from detector import detect_revenue_leaks
from root_cause import get_main_root_cause
from recommender import recommend_action, calculate_recovery
from recovery_model import get_recovery_rate
from action_guard import check_action
from audit_log import log_recovery_decision


def run_pipeline():

    print("\n" + "=" * 75)
    print("🚀 REVENUE LEAK DETECTIVE — FULL INVESTIGATION")
    print("=" * 75)

    # --------------------------------------------------
    # STEP 1: Detect revenue leak
    # --------------------------------------------------

    top_leak = detect_revenue_leaks()

    if top_leak is None:
        print("\nNo revenue leak found.")
        return

    # --------------------------------------------------
    # STEP 2: Find root cause
    # --------------------------------------------------

    root_cause = get_main_root_cause(
        top_leak["payment_method"],
        top_leak["device"],
        top_leak["hour"]
    )

    if root_cause is None:
        print("\nNo root cause found.")
        return

    failure_reason = root_cause["failure_reason"]
    failed_transactions = root_cause["failed_transactions"]
    failed_revenue = root_cause["failed_revenue"]

    # --------------------------------------------------
    # STEP 3: Recommend recovery action
    # --------------------------------------------------

    recommendation = recommend_action(
        failure_reason
    )

    action = recommendation["action"]

    # --------------------------------------------------
    # STEP 4: Get recovery evidence
    # --------------------------------------------------

    recovery = get_recovery_rate(
        top_leak["payment_method"],
        top_leak["device"],
        top_leak["hour"],
        failure_reason
    )

    recovery_rate = recovery["recovery_rate"]

    # --------------------------------------------------
    # STEP 5: Estimate recovery
    # --------------------------------------------------

    estimated_recovery = calculate_recovery(
        failed_revenue,
        recovery_rate
    )

    remaining_at_risk = (
        failed_revenue - estimated_recovery
    )

    # --------------------------------------------------
    # STEP 6: Safety check
    # --------------------------------------------------

    # Current retry count for the segment.
    # We use 0 here because this is a simulated
    # recovery action, not a real payment action.
    retry_count = 0

    guard = check_action(
        action,
        retry_count,
        failed_revenue
    )
        # --------------------------------------------------
    # STEP 7: Record decision in audit trail
    # --------------------------------------------------

    execution_status = "SIMULATED"

    log_recovery_decision(
        top_leak["payment_method"],
        top_leak["device"],
        top_leak["hour"],
        failure_reason,
        failed_transactions,
        failed_revenue,
        action,
        recovery_rate,
        estimated_recovery,
        guard["allowed"],
        guard["decision"],
        execution_status
    )

    # --------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------

    print("\n")
    print("=" * 75)
    print("🔎 INVESTIGATION RESULT")
    print("=" * 75)

    print(
        f"\nLeak segment       : "
        f"{top_leak['payment_method']} | "
        f"{top_leak['device']} | "
        f"{top_leak['hour']}:00"
    )

    print(
        f"Failure rate      : "
        f"{top_leak['failure_rate']:.2f}%"
    )

    print(
        f"Excess failures   : "
        f"{top_leak['excess_failures']:.0f}"
    )

    print(
        f"Revenue at risk   : "
        f"₹{top_leak['failed_revenue']:,.2f}"
    )

    print("\n" + "-" * 75)
    print("🧠 ROOT CAUSE")
    print("-" * 75)

    print(f"Primary cause     : {failure_reason}")
    print(f"Failed payments   : {failed_transactions}")
    print(f"Cause revenue     : ₹{failed_revenue:,.2f}")

    print("\n" + "-" * 75)
    print("🤖 RECOVERY DECISION")
    print("-" * 75)

    print(f"Recommended action: {action}")

    print(
        f"Recovery evidence : "
        f"{recovery['source']}"
    )

    print(
        f"Evidence sample   : "
        f"{recovery['sample_size']}"
    )

    print(
        f"Historical rate   : "
        f"{recovery_rate * 100:.2f}%"
    )

    print(
        f"Expected recovery : "
        f"₹{estimated_recovery:,.2f}"
    )

    print(
        f"Remaining risk    : "
        f"₹{remaining_at_risk:,.2f}"
    )

    print("\n" + "-" * 75)
    print("🛡️ ACTION GUARD")
    print("-" * 75)

    print(
        f"Action allowed    : "
        f"{guard['allowed']}"
    )

    print(
        f"Guard decision    : "
        f"{guard['decision']}"
    )

    print(
        f"Guard reason      : "
        f"{guard['reason']}"
    )

    print(
        f"\nReason            : "
        f"{recommendation['reason']}"
    )

    print("\n" + "=" * 75)
    print("✅ INVESTIGATION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    run_pipeline()