import streamlit as st
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASELINE_FAILURE_RATE = 5.46
MIN_TRANSACTIONS = 50
MAX_RETRIES = 1

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "transactions.csv"


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_transactions():
    df = pd.read_csv(DATA_PATH)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["status"] = df["status"].str.lower()

    return df


# ============================================================
# REVENUE LEAK DETECTION
# ============================================================

def detect_revenue_leaks(df):

    grouped = (
        df.groupby(
            [
                "payment_method",
                "device",
                df["timestamp"].dt.hour.rename("hour")
            ]
        )
        .agg(
            total_transactions=("transaction_id", "count"),
            failed_transactions=("status", lambda x: (x == "failed").sum()),
            failed_revenue=("amount", lambda x: x[df.loc[x.index, "status"] == "failed"].sum())
        )
        .reset_index()
    )

    grouped = grouped[
        grouped["total_transactions"] >= MIN_TRANSACTIONS
    ].copy()

    grouped["failure_rate"] = (
        grouped["failed_transactions"]
        / grouped["total_transactions"]
        * 100
    )

    grouped = grouped[
        grouped["failure_rate"] > BASELINE_FAILURE_RATE
    ].copy()

    grouped["expected_failures"] = (
        grouped["total_transactions"]
        * BASELINE_FAILURE_RATE
        / 100
    )

    grouped["excess_failures"] = (
        grouped["failed_transactions"]
        - grouped["expected_failures"]
    )

    grouped["rate_deviation"] = (
        grouped["failure_rate"]
        - BASELINE_FAILURE_RATE
    )

    grouped["leak_score"] = (
        grouped["rate_deviation"] * 10
        + grouped["excess_failures"] * 0.5
        + grouped["failed_revenue"] / 10000
    )

    grouped = grouped.sort_values(
        "leak_score",
        ascending=False
    ).reset_index(drop=True)

    return grouped


# ============================================================
# ROOT CAUSE ANALYSIS
# ============================================================

def get_root_causes(df, payment_method, device, hour):

    segment = df[
        (df["payment_method"] == payment_method)
        & (df["device"] == device)
        & (df["timestamp"].dt.hour == hour)
        & (df["status"] == "failed")
    ]

    if segment.empty:
        return pd.DataFrame()

    causes = (
        segment.groupby("failure_reason")
        .agg(
            failed_transactions=("transaction_id", "count"),
            failed_revenue=("amount", "sum")
        )
        .reset_index()
        .sort_values(
            "failed_revenue",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return causes


# ============================================================
# HISTORICAL RECOVERY SIGNAL
# ============================================================

def calculate_historical_recovery(df, payment_method, device, hour, failure_reason):

    failures = df[
        (df["payment_method"] == payment_method)
        & (df["device"] == device)
        & (df["timestamp"].dt.hour == hour)
        & (df["failure_reason"] == failure_reason)
        & (df["status"] == "failed")
    ].copy()

    if failures.empty:
        return {
            "rate": 0,
            "sample_size": 0,
            "successes": 0,
            "source": "NO_EVIDENCE"
        }

    successes = 0

    for _, failure in failures.iterrows():

        later_transactions = df[
            (df["customer_id"] == failure["customer_id"])
            & (df["timestamp"] > failure["timestamp"])
            & (df["timestamp"] <= failure["timestamp"] + pd.Timedelta(hours=24))
            & (df["status"] == "success")
        ]

        if not later_transactions.empty:
            successes += 1

    rate = successes / len(failures)

    return {
        "rate": rate,
        "sample_size": len(failures),
        "successes": successes,
        "source": "CSV_DERIVED_HISTORICAL_SIGNAL"
    }


# ============================================================
# ACTION RECOMMENDATION
# ============================================================

def recommend_action(failure_reason):

    if failure_reason == "TIMEOUT":
        return (
            "RETRY_PAYMENT",
            "Timeouts may be temporary, so a controlled retry can be attempted."
        )

    if failure_reason == "BANK_ERROR":
        return (
            "RETRY_LATER",
            "Bank errors may be temporary, so retrying later is safer than retrying immediately."
        )

    if failure_reason == "INSUFFICIENT_FUNDS":
        return (
            "OFFER_ALTERNATIVE_PAYMENT",
            "Retrying may not help unless the customer's available balance changes."
        )

    if failure_reason == "CARD_DECLINED":
        return (
            "OFFER_ALTERNATIVE_PAYMENT",
            "The customer can try another card or payment method."
        )

    return (
        "MANUAL_REVIEW",
        "Unknown failure reason requires further investigation."
    )


# ============================================================
# SAFETY / ELIGIBILITY GUARD
# ============================================================

def check_action(action, retry_count, predicted_recovery):

    if action in ["RETRY_PAYMENT", "RETRY_LATER"]:

        if retry_count >= MAX_RETRIES:
            return {
                "allowed": False,
                "decision": "STOP",
                "reason": "Maximum retry limit reached."
            }

        if predicted_recovery <= 0:
            return {
                "allowed": False,
                "decision": "STOP",
                "reason": "No positive recovery evidence."
            }

        return {
            "allowed": True,
            "decision": "EXECUTE",
            "reason": "Retry is within the allowed limit and has positive historical evidence."
        }

    if action == "OFFER_ALTERNATIVE_PAYMENT":

        if predicted_recovery <= 0:
            return {
                "allowed": False,
                "decision": "STOP",
                "reason": "No positive recovery evidence."
            }

        return {
            "allowed": True,
            "decision": "ESCALATE",
            "reason": "Alternative payment requires customer/manual intervention."
        }

    return {
        "allowed": False,
        "decision": "STOP",
        "reason": "Unknown action blocked by safety guard."
    }


# ============================================================
# OPPORTUNITY RANKING
# ============================================================

def build_opportunities(df):

    leaks = detect_revenue_leaks(df)

    opportunities = []

    for _, leak in leaks.iterrows():

        causes = get_root_causes(
            df,
            leak["payment_method"],
            leak["device"],
            int(leak["hour"])
        )

        if causes.empty:
            continue

        root_cause = causes.iloc[0]

        payment_method = leak["payment_method"]
        device = leak["device"]
        hour = int(leak["hour"])
        failure_reason = root_cause["failure_reason"]

        recovery = calculate_historical_recovery(
            df,
            payment_method,
            device,
            hour,
            failure_reason
        )

        failed_revenue = float(root_cause["failed_revenue"])

        predicted_recovery = (
            failed_revenue * recovery["rate"]
        )

        action, action_reason = recommend_action(
            failure_reason
        )

        guard = check_action(
            action,
            0,
            predicted_recovery
        )

        opportunities.append({
            "payment_method": payment_method,
            "device": device,
            "hour": hour,
            "failure_reason": failure_reason,
            "root_cause_transactions": int(
                root_cause["failed_transactions"]
            ),
            "root_cause_revenue": failed_revenue,
            "failure_rate": float(leak["failure_rate"]),
            "leak_score": float(leak["leak_score"]),
            "historical_recovery_rate": recovery["rate"],
            "historical_sample_size": recovery["sample_size"],
            "historical_successes": recovery["successes"],
            "predicted_recovery": predicted_recovery,
            "recommended_action": action,
            "action_reason": action_reason,
            "final_decision": guard["decision"],
            "guard_reason": guard["reason"],
            "evidence_source": recovery["source"]
        })

    opportunities.sort(
        key=lambda x: x["predicted_recovery"],
        reverse=True
    )

    return opportunities


# ============================================================
# EXECUTION SIMULATION
# ============================================================

def simulate_execution(opportunity):

    decision = opportunity["final_decision"]

    if decision == "EXECUTE":
        actual_recovery = (
            opportunity["predicted_recovery"] * 0.80
        )
        status = "SIMULATED_SUCCESS"

    elif decision == "ESCALATE":
        actual_recovery = 0
        status = "ESCALATED"

    else:
        actual_recovery = 0
        status = "BLOCKED"

    return actual_recovery, status


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Revenue Leak Detective",
    page_icon="🔎",
    layout="wide"
)


# ============================================================
# LOAD DATA
# ============================================================

try:
    transactions = load_transactions()
except Exception as error:

    st.error("Unable to load synthetic transaction data.")

    st.exception(error)

    st.stop()


opportunities = build_opportunities(transactions)


# ============================================================
# HEADER
# ============================================================

st.title("🔎 Revenue Leak Detective")

st.subheader(
    "AI-powered revenue recovery investigation and decision system"
)

st.info(
    "🧪 TEST MODE — This public demo uses synthetic transaction data "
    "from CSV. No real payment or recovery action is executed."
)


st.caption(
    "Pipeline: Detect → Diagnose → Estimate → Prioritize → Guard → Recover"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("System Controls")

st.sidebar.metric(
    "Transactions",
    f"{len(transactions):,}"
)

st.sidebar.metric(
    "Detected Leak Segments",
    f"{len(detect_revenue_leaks(transactions)):,}"
)

st.sidebar.metric(
    "Recovery Opportunities",
    f"{len(opportunities):,}"
)

st.sidebar.divider()

st.sidebar.write(
    "**Safety limits**"
)

st.sidebar.write(
    f"Maximum retries: {MAX_RETRIES}"
)

st.sidebar.write(
    "Unknown actions: STOP"
)

st.sidebar.write(
    "Alternative payment: ESCALATE"
)


# ============================================================
# RUN RECOVERY BUTTON
# ============================================================

if "execution_results" not in st.session_state:
    st.session_state.execution_results = None


if st.button(
    "🚀 Run Recovery Execution",
    type="primary"
):

    execution_results = []

    for opportunity in opportunities:

        actual_recovery, status = simulate_execution(
            opportunity
        )

        execution_results.append({
            "Segment": (
                f"{opportunity['payment_method']} | "
                f"{opportunity['device']} | "
                f"{opportunity['hour']}:00"
            ),
            "Failure Reason": opportunity["failure_reason"],
            "Decision": opportunity["final_decision"],
            "Action": opportunity["recommended_action"],
            "Predicted Recovery": opportunity["predicted_recovery"],
            "Actual Recovery": actual_recovery,
            "Execution Status": status
        })

    st.session_state.execution_results = execution_results


# ============================================================
# TOP OVERVIEW
# ============================================================

total_risk = sum(
    opportunity["root_cause_revenue"]
    for opportunity in opportunities
)

total_predicted = sum(
    opportunity["predicted_recovery"]
    for opportunity in opportunities
)

if opportunities:

    top_opportunity = opportunities[0]

else:

    top_opportunity = None


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Revenue at Risk",
    f"₹{total_risk:,.0f}"
)

col2.metric(
    "Predicted Recovery",
    f"₹{total_predicted:,.0f}"
)

col3.metric(
    "Leak Segments",
    f"{len(detect_revenue_leaks(transactions)):,}"
)

col4.metric(
    "Recovery Opportunities",
    f"{len(opportunities):,}"
)


# ============================================================
# TOP REVENUE LEAK
# ============================================================

st.header("🚨 Top Revenue Leak")

if top_opportunity:

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Segment:** "
            f"{top_opportunity['payment_method']} | "
            f"{top_opportunity['device']} | "
            f"{top_opportunity['hour']}:00"
        )

        st.write(
            f"**Failure rate:** "
            f"{top_opportunity['failure_rate']:.2f}% "
            f"vs baseline {BASELINE_FAILURE_RATE}%"
        )

        st.write(
            f"**Leak score:** "
            f"{top_opportunity['leak_score']:.2f}"
        )

    with col2:

        st.write(
            f"**Root cause:** "
            f"{top_opportunity['failure_reason']}"
        )

        st.write(
            f"**Root-cause revenue:** "
            f"₹{top_opportunity['root_cause_revenue']:,.2f}"
        )

        st.write(
            f"**Predicted recovery:** "
            f"₹{top_opportunity['predicted_recovery']:,.2f}"
        )


# ============================================================
# ROOT CAUSE BREAKDOWN
# ============================================================

st.header("🔬 Root Cause Investigation")

if top_opportunity:

    causes = get_root_causes(
        transactions,
        top_opportunity["payment_method"],
        top_opportunity["device"],
        top_opportunity["hour"]
    )

    display_causes = causes.copy()

    display_causes["failed_revenue"] = (
        display_causes["failed_revenue"]
        .map(lambda x: f"₹{x:,.2f}")
    )

    display_causes = display_causes.rename(
        columns={
            "failure_reason": "Failure Reason",
            "failed_transactions": "Failed Transactions",
            "failed_revenue": "Revenue at Risk"
        }
    )

    st.dataframe(
        display_causes,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# OPPORTUNITY TABLE
# ============================================================

st.header("🎯 Recovery Opportunities")

table_data = []

for rank, opportunity in enumerate(
    opportunities[:10],
    start=1
):

    table_data.append({
        "Rank": rank,
        "Segment": (
            f"{opportunity['payment_method']} | "
            f"{opportunity['device']} | "
            f"{opportunity['hour']}:00"
        ),
        "Root Cause": opportunity["failure_reason"],
        "Revenue at Risk": (
            f"₹{opportunity['root_cause_revenue']:,.0f}"
        ),
        "Historical Signal": (
            f"{opportunity['historical_recovery_rate'] * 100:.2f}%"
        ),
        "Predicted Recovery": (
            f"₹{opportunity['predicted_recovery']:,.0f}"
        ),
        "Action": opportunity["recommended_action"],
        "Decision": opportunity["final_decision"]
    })


if table_data:

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# SELECTED OPPORTUNITY DETAILS
# ============================================================

st.header("🧠 Decision Evidence")

if top_opportunity:

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Historical Recovery Signal",
        f"{top_opportunity['historical_recovery_rate'] * 100:.2f}%"
    )

    col2.metric(
        "Historical Sample",
        f"{top_opportunity['historical_sample_size']:,}"
    )

    col3.metric(
        "Predicted Recovery",
        f"₹{top_opportunity['predicted_recovery']:,.2f}"
    )

    st.write(
        f"**Evidence source:** "
        f"{top_opportunity['evidence_source']}"
    )

    st.write(
        f"**Historical successes:** "
        f"{top_opportunity['historical_successes']:,}"
    )

    st.write(
        f"**Recommended action:** "
        f"{top_opportunity['recommended_action']}"
    )

    st.write(
        f"**Why:** "
        f"{top_opportunity['action_reason']}"
    )

    st.warning(
        "Historical recovery is an observational signal, "
        "not proof that the intervention caused recovery."
    )


# ============================================================
# EXECUTION RESULTS
# ============================================================

if st.session_state.execution_results:

    st.header("🚀 Recovery Execution")

    execution_df = pd.DataFrame(
        st.session_state.execution_results
    )

    executed = len(
        execution_df[
            execution_df["Decision"] == "EXECUTE"
        ]
    )

    escalated = len(
        execution_df[
            execution_df["Decision"] == "ESCALATE"
        ]
    )

    stopped = len(
        execution_df[
            execution_df["Decision"] == "STOP"
        ]
    )

    predicted = execution_df[
        "Predicted Recovery"
    ].sum()

    actual = execution_df[
        "Actual Recovery"
    ].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "EXECUTE",
        executed
    )

    col2.metric(
        "ESCALATE",
        escalated
    )

    col3.metric(
        "STOP",
        stopped
    )

    col4.metric(
        "Simulated Recovery",
        f"₹{actual:,.0f}"
    )

    st.dataframe(
        execution_df.style.format({
            "Predicted Recovery": "₹{:,.2f}",
            "Actual Recovery": "₹{:,.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Actual recovery is simulated for test-mode evaluation."
    )


# ============================================================
# AUDIT TRAIL
# ============================================================

st.header("📝 Audit Trail")

if st.session_state.execution_results:

    audit_df = pd.DataFrame(
        st.session_state.execution_results
    )

    audit_df["Audit Status"] = audit_df[
        "Execution Status"
    ]

    st.dataframe(
        audit_df[
            [
                "Segment",
                "Failure Reason",
                "Action",
                "Decision",
                "Audit Status"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "Run the recovery execution to generate the demo audit trail."
    )


# ============================================================
# METHODOLOGY
# ============================================================

with st.expander("📚 Methodology"):

    st.markdown(
        """
### 1. Detect

Transaction segments are grouped by:

- Payment method
- Device
- Hour of day

Segments with a failure rate above the historical baseline are flagged.

### 2. Diagnose

The system investigates the failure reasons inside each suspicious segment.

### 3. Estimate

A historical recovery signal is calculated from subsequent successful
transactions observed for the same customer.

### 4. Prioritize

Recovery opportunities are ranked using predicted recoverable revenue.

### 5. Guard

Every action passes through bounded decision rules:

- **EXECUTE** — controlled retry with positive evidence
- **ESCALATE** — customer/manual intervention
- **STOP** — insufficient evidence or unsafe action

### 6. Measure

The dashboard reports predicted recovery and simulated intervention
recovery.

### Safety

This deployment uses synthetic data only.

No real payment is initiated, retried, refunded, or modified.
"""
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Revenue Leak Detective • Synthetic/Test Mode • "
    "AI Revenue Recovery Investigation System"
)