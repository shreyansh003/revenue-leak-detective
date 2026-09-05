from recommender import recommend_action
from recovery_model import get_recovery_rate
from action_guard import check_action
from audit_log import log_recovery_decision


def simulate_recovery(
    payment_method,
    device,
    hour,
    failure_reason,
    failed_revenue,
    failed_transactions,
    retry_count=0
):
    # Get recommended action
    recommendation = recommend_action(failure_reason)

    action = recommendation["action"]

    # Get historical recovery evidence
    recovery = get_recovery_rate(
        payment_method,
        device,
        hour,
        failure_reason
    )

    recovery_rate = recovery["recovery_rate"]

    # Estimate recoverable revenue
    estimated_recovery = (
        failed_revenue * recovery_rate
    )

    remaining_at_risk = (
        failed_revenue - estimated_recovery
    )

    # Apply safety guard
    guard = check_action(
        action,
        retry_count,
        failed_revenue
    )

    # Simulate execution
    if guard["allowed"]:
        execution_status = "SIMULATED_SUCCESS"
    else:
        execution_status = "BLOCKED"

    # Record the decision
    log_recovery_decision(
        payment_method,
        device,
        hour,
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

    return {
        "action": action,
        "recovery_rate": recovery_rate,
        "recovery_source": recovery["source"],
        "sample_size": recovery["sample_size"],
        "estimated_recovery": estimated_recovery,
        "remaining_at_risk": remaining_at_risk,
        "guard_allowed": guard["allowed"],
        "guard_decision": guard["decision"],
        "guard_reason": guard["reason"],
        "execution_status": execution_status
    }


if __name__ == "__main__":

    result = simulate_recovery(
        payment_method="UPI",
        device="mobile",
        hour=21,
        failure_reason="BANK_ERROR",
        failed_revenue=72071.82,
        failed_transactions=44,
        retry_count=0
    )

    print("\n💰 RECOVERY EXECUTION SIMULATOR")
    print("=" * 70)

    print(
        f"\nRecommended action : "
        f"{result['action']}"
    )

    print(
        f"Recovery rate      : "
        f"{result['recovery_rate'] * 100:.2f}%"
    )

    print(
        f"Evidence source    : "
        f"{result['recovery_source']}"
    )

    print(
        f"Sample size        : "
        f"{result['sample_size']}"
    )

    print(
        f"Estimated recovery : "
        f"₹{result['estimated_recovery']:,.2f}"
    )

    print(
        f"Remaining at risk  : "
        f"₹{result['remaining_at_risk']:,.2f}"
    )

    print(
        f"\nGuard allowed      : "
        f"{result['guard_allowed']}"
    )

    print(
        f"Guard decision     : "
        f"{result['guard_decision']}"
    )

    print(
        f"Guard reason       : "
        f"{result['guard_reason']}"
    )

    print(
        f"\nExecution status   : "
        f"{result['execution_status']}"
    )

    print(
        "\n📝 Audit log updated."
    )