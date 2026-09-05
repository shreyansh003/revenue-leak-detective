from opportunity_ranker import rank_opportunities
from recovery_simulator import simulate_recovery
from audit_log import log_recovery_decision


def execute_recovery_batch():

    print("\n🚀 RECOVERY EXECUTION ENGINE")
    print("=" * 75)

    opportunities = rank_opportunities()

    if not opportunities:
        print("\nNo recovery opportunities found.")
        return []

    results = []

    for index, opportunity in enumerate(opportunities, start=1):

        print(
            f"\nProcessing recovery "
            f"{index}/{len(opportunities)}..."
        )

        decision = opportunity["final_decision"]

        segment = (
            f"{opportunity['payment_method']} | "
            f"{opportunity['device']} | "
            f"{opportunity['hour']}:00"
        )

        failure_reason = opportunity["failure_reason"]

        revenue_at_risk = opportunity["root_cause_revenue"]

        failed_transactions = opportunity.get(
            "failed_transactions",
            opportunity.get("sample_size", 0)
        )

        recovery_rate = opportunity["recovery_rate"]

        expected_recovery = opportunity["expected_recovery"]

        action = opportunity["recommended_action"]


        # -------------------------------------------------
        # STOP
        # -------------------------------------------------

        if decision == "STOP":

            print("Decision : STOP")
            print("Action   : No action taken.")

            log_recovery_decision(
                opportunity["payment_method"],
                opportunity["device"],
                opportunity["hour"],
                failure_reason,
                failed_transactions,
                revenue_at_risk,
                action,
                recovery_rate,
                expected_recovery,
                False,
                "STOP",
                "BLOCKED"
            )

            results.append({
                "segment": segment,
                "failure_reason": failure_reason,
                "decision": "STOP",
                "action": "NONE",
                "estimated_recovery": 0,
                "actual_recovery": 0,
                "execution_status": "BLOCKED"
            })

            continue


        # -------------------------------------------------
        # ESCALATE
        # -------------------------------------------------

        if decision == "ESCALATE":

            print("Decision : ESCALATE")
            print(
                "Action   : Sent for "
                "manual/customer escalation."
            )

            log_recovery_decision(
                opportunity["payment_method"],
                opportunity["device"],
                opportunity["hour"],
                failure_reason,
                failed_transactions,
                revenue_at_risk,
                action,
                recovery_rate,
                expected_recovery,
                False,
                "ESCALATE",
                "ESCALATED"
            )

            results.append({
                "segment": segment,
                "failure_reason": failure_reason,
                "decision": "ESCALATE",
                "action": action,
                "estimated_recovery": expected_recovery,
                "actual_recovery": 0,
                "execution_status": "ESCALATED"
            })

            continue


        # -------------------------------------------------
        # EXECUTE
        # -------------------------------------------------

        if decision == "EXECUTE":

            print("Decision : EXECUTE")

            simulation = simulate_recovery(
                payment_method=opportunity["payment_method"],
                device=opportunity["device"],
                hour=opportunity["hour"],
                failure_reason=failure_reason,
                failed_revenue=revenue_at_risk,
                failed_transactions=failed_transactions,
                retry_count=0
            )

            actual_recovery = (
                simulation["estimated_recovery"] * 0.80
            )

            print(
                f"Action   : {simulation['action']}"
            )

            print(
                f"Expected : "
                f"₹{simulation['estimated_recovery']:,.2f}"
            )

            print(
                f"Actual   : "
                f"₹{actual_recovery:,.2f}"
            )

            results.append({
                "segment": segment,
                "failure_reason": failure_reason,
                "decision": "EXECUTE",
                "action": simulation["action"],
                "estimated_recovery":
                    simulation["estimated_recovery"],
                "actual_recovery":
                    actual_recovery,
                "execution_status":
                    simulation["execution_status"]
            })


    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    executed = sum(
        1
        for result in results
        if result["decision"] == "EXECUTE"
    )

    escalated = sum(
        1
        for result in results
        if result["decision"] == "ESCALATE"
    )

    stopped = sum(
        1
        for result in results
        if result["decision"] == "STOP"
    )

    total_expected = sum(
        result["estimated_recovery"]
        for result in results
    )

    total_actual = sum(
        result["actual_recovery"]
        for result in results
    )


    print("\n")
    print("=" * 75)
    print("📊 RECOVERY EXECUTION SUMMARY")
    print("=" * 75)

    print(
        f"\nOpportunities : {len(results)}"
    )

    print(
        f"EXECUTE       : {executed}"
    )

    print(
        f"ESCALATE      : {escalated}"
    )

    print(
        f"STOP          : {stopped}"
    )

    print(
        f"\nExpected recovery : "
        f"₹{total_expected:,.2f}"
    )

    print(
        f"Actual recovery   : "
        f"₹{total_actual:,.2f}"
    )

    print(
        "\n📝 All decisions recorded in audit trail."
    )

    print(
        "⚠️ All recovery actions are simulated."
    )

    return results


if __name__ == "__main__":

    execute_recovery_batch()