import streamlit as st
import pandas as pd

from database import get_connection
from detector import detect_revenue_leaks
from root_cause import get_main_root_cause
from opportunity_ranker import rank_opportunities
from recovery_executor import execute_recovery_batch


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Revenue Leak Detective",
    page_icon="💰",
    layout="wide"
)


# ---------------------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------------------

def get_latest_batch():
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            created_at,
            opportunities_processed,
            executed,
            escalated,
            stopped,
            revenue_at_risk,
            predicted_recovery,
            actual_recovery,
            actual_recovery_rate,
            prediction_error,
            prediction_accuracy
        FROM recovery_batch_results
        ORDER BY created_at DESC
        LIMIT 1;
    """

    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result


def get_audit_logs():
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            created_at,
            payment_method,
            device,
            hour,
            failure_reason,
            recommended_action,
            recovery_rate,
            estimated_recovery,
            guard_decision,
            execution_status
        FROM recovery_audit_log
        ORDER BY created_at DESC
        LIMIT 20;
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("💰 Revenue Leak Detective")

st.subheader(
    "AI-powered revenue recovery investigation system"
)

st.caption(
    "Detect → Diagnose → Predict → Guard → Recover"
)

st.info(
    "Synthetic/test-mode environment. Recovery outcomes are simulated "
    "and are not real payment actions or causal intervention results."
)


# ---------------------------------------------------------
# RECOVERY EXECUTION
# ---------------------------------------------------------

st.divider()

if st.button(
    "🚀 Run Recovery Execution",
    type="primary",
    use_container_width=True
):

    with st.spinner("Running recovery decision engine..."):

        execution_results = execute_recovery_batch()

    st.success(
        f"Recovery batch completed — "
        f"{len(execution_results)} opportunities processed."
    )

    st.rerun()


# ---------------------------------------------------------
# LATEST BATCH OVERVIEW
# ---------------------------------------------------------

st.divider()

st.header("📊 Latest Recovery Batch")

latest_batch = get_latest_batch()

if latest_batch:

    (
        created_at,
        opportunities,
        executed,
        escalated,
        stopped,
        revenue_at_risk,
        predicted_recovery,
        actual_recovery,
        actual_recovery_rate,
        prediction_error,
        prediction_accuracy
    ) = latest_batch

    # -----------------------------------------------------
    # TOP METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Opportunities",
            opportunities
        )

    with col2:
        st.metric(
            "Revenue at Risk",
            f"₹{float(revenue_at_risk):,.0f}"
        )

    with col3:
        st.metric(
            "Predicted Recovery",
            f"₹{float(predicted_recovery):,.0f}"
        )

    with col4:
        st.metric(
            "Simulated Intervention Recovery",
            f"₹{float(actual_recovery):,.0f}"
        )

    st.caption(
        "Revenue at risk represents the value associated with the "
        "identified root causes in the recovery batch."
    )

    # -----------------------------------------------------
    # DECISION SUMMARY
    # -----------------------------------------------------

    st.subheader("Decision Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "EXECUTE",
            executed
        )

    with col2:
        st.metric(
            "ESCALATE",
            escalated
        )

    with col3:
        st.metric(
            "STOP",
            stopped
        )

    # -----------------------------------------------------
    # PREDICTION PERFORMANCE
    # -----------------------------------------------------

    st.subheader("Prediction Performance")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Simulated Recovery Rate",
            f"{float(actual_recovery_rate) * 100:.2f}%"
        )

    with col2:
        st.metric(
            "Prediction Error",
            f"₹{float(prediction_error):,.0f}"
        )

    with col3:
        st.metric(
            "Prediction Accuracy",
            f"{float(prediction_accuracy) * 100:.2f}%"
        )

    st.caption(
        "These metrics are based on the synthetic/test-mode recovery "
        "simulation. Prediction accuracy is an evaluation metric for "
        "this simulation, not ML model accuracy."
    )

else:

    st.warning(
        "No recovery batch has been recorded yet. "
        "Run the recovery execution engine first."
    )


# ---------------------------------------------------------
# TOP REVENUE LEAK
# ---------------------------------------------------------

st.divider()

st.header("🚨 Top Revenue Leak")

leaks = detect_revenue_leaks(return_all=True)

if leaks:

    top_leak = leaks[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Payment Method",
            top_leak["payment_method"]
        )

    with col2:
        st.metric(
            "Device",
            top_leak["device"]
        )

    with col3:
        st.metric(
            "Failure Rate",
            f"{top_leak['failure_rate']:.2f}%"
        )

    with col4:
        st.metric(
            "Segment Revenue at Risk",
            f"₹{top_leak['failed_revenue']:,.0f}"
        )

    root_cause = get_main_root_cause(
        top_leak["payment_method"],
        top_leak["device"],
        top_leak["hour"]
    )

    if root_cause:

        st.subheader("Root Cause Investigation")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Primary Root Cause",
                root_cause["failure_reason"]
            )

        with col2:
            st.metric(
                "Root Cause Failures",
                root_cause["failed_transactions"]
            )

        with col3:
            st.metric(
                "Root Cause Value",
                f"₹{root_cause['failed_revenue']:,.0f}"
            )

        st.caption(
            "The primary root cause is selected from the failure reason "
            "with the highest failed revenue inside the detected segment."
        )

else:

    st.success("No revenue leaks detected.")


# ---------------------------------------------------------
# RECOVERY OPPORTUNITIES
# ---------------------------------------------------------

st.divider()

st.header("🎯 Recovery Opportunities")

opportunities = rank_opportunities()

if opportunities:

    table_data = []

    for opportunity in opportunities:

        table_data.append({
            "Rank": len(table_data) + 1,

            "Segment": (
                f"{opportunity['payment_method']} | "
                f"{opportunity['device']} | "
                f"{opportunity['hour']}:00"
            ),

            "Root Cause": opportunity["failure_reason"],

            "Historical Recovery Signal": (
                f"{opportunity['historical_recovery_rate'] * 100:.2f}%"
            ),

            "Predicted Recovery": (
                f"₹{opportunity['predicted_recovery']:,.0f}"
            ),

            "Evidence": opportunity["evidence_source"],

            "Action": opportunity["recommended_action"],

            "Decision": opportunity["final_decision"]
        })

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Historical Recovery Signal = observed subsequent-success rate "
        "from historical data. It is observational evidence, not proof "
        "that the recommended intervention caused recovery."
    )

else:

    st.info(
        "No recovery opportunities available."
    )


# ---------------------------------------------------------
# AUDIT TRAIL
# ---------------------------------------------------------

st.divider()

st.header("📝 Recovery Audit Trail")

audit_logs = get_audit_logs()

if audit_logs:

    audit_data = []

    for row in audit_logs:

        (
            created_at,
            payment_method,
            device,
            hour,
            failure_reason,
            recommended_action,
            recovery_rate,
            estimated_recovery,
            guard_decision,
            execution_status
        ) = row

        audit_data.append({
            "Time": created_at,

            "Segment": (
                f"{payment_method} | "
                f"{device} | "
                f"{hour}:00"
            ),

            "Root Cause": failure_reason,

            "Action": recommended_action,

            "Historical Signal": (
                f"{float(recovery_rate) * 100:.2f}%"
            ),

            "Predicted Recovery": (
                f"₹{float(estimated_recovery):,.0f}"
            ),

            "Guard Decision": guard_decision,

            "Execution Status": execution_status
        })

    audit_df = pd.DataFrame(audit_data)

    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "The audit trail records the recovery decision, safety-guard "
        "result, and simulated execution status."
    )

else:

    st.info(
        "No audit records found."
    )


# ---------------------------------------------------------
# METHODOLOGY
# ---------------------------------------------------------

st.divider()

st.header("🧠 How Revenue Leak Detective Works")

st.markdown(
    """
### 1. Detect revenue leakage

Finds payment-method, device, and time segments whose failure rate
is significantly above the historical baseline.

### 2. Diagnose the root cause

Identifies the failure reason responsible for the largest amount of
failed revenue inside the suspicious segment.

### 3. Estimate recoverability

Uses historical subsequent-success behavior as an observational
recovery signal.

### 4. Predict recovery value

Combines the historical signal with root-cause revenue to estimate
potential recovery.

### 5. Apply eligibility rules

Only opportunities with sufficient evidence and expected value can
proceed.

### 6. Apply the safety guard

The action guard enforces stopping rules such as retry limits.

### 7. Execute in test mode

The system simulates the intervention rather than performing a real
payment action.

### 8. Record everything

Every decision is written to the PostgreSQL audit trail.
"""
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Revenue Leak Detective — synthetic data / test mode only"
)