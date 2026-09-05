from opportunity_ranker import rank_opportunities
from database import get_connection


def simulate_actual_recovery(
    expected_recovery,
    decision
):
    """
    Simulate the actual amount recovered.

    Test-mode only.
    No real payment action is performed.
    """

    if decision == "EXECUTE":
        return expected_recovery * 0.80

    elif decision == "ESCALATE":
        return 0

    else:
        return 0


def save_batch_result(result):

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO recovery_batch_results (
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
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s
        );
    """

    cursor.execute(
        query,
        (
            result["opportunities"],
            result["executed"],
            result["escalated"],
            result["stopped"],
            result["revenue_at_risk"],
            result["predicted_recovery"],
            result["actual_recovery"],
            result["actual_recovery_rate"],
            result["prediction_error"],
            result["prediction_accuracy"]
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def measure_batch_recovery():

    opportunities = rank_opportunities()

    total_revenue_at_risk = 0
    total_predicted_recovery = 0
    total_actual_recovery = 0

    executed = 0
    escalated = 0
    stopped = 0

    print("\n📦 BATCH RECOVERY MEASUREMENT")
    print("=" * 75)

    for opportunity in opportunities:

        revenue_at_risk = (
            opportunity["root_cause_revenue"]
        )

        predicted_recovery = (
            opportunity["expected_recovery"]
        )

        decision = (
            opportunity["final_decision"]
        )

        actual_recovery = simulate_actual_recovery(
            predicted_recovery,
            decision
        )

        total_revenue_at_risk += revenue_at_risk
        total_predicted_recovery += predicted_recovery
        total_actual_recovery += actual_recovery

        if decision == "EXECUTE":
            executed += 1

        elif decision == "ESCALATE":
            escalated += 1

        else:
            stopped += 1

    if total_revenue_at_risk > 0:
        actual_recovery_rate = (
            total_actual_recovery
            / total_revenue_at_risk
        )
    else:
        actual_recovery_rate = 0

    # Difference between actual and predicted recovery
    prediction_error = (
        total_actual_recovery
        - total_predicted_recovery
    )

    # How accurate was the prediction?
    if total_predicted_recovery > 0:
        prediction_accuracy = (
            total_actual_recovery
            / total_predicted_recovery
        )
    else:
        prediction_accuracy = 0

    result = {
        "opportunities": len(opportunities),
        "executed": executed,
        "escalated": escalated,
        "stopped": stopped,
        "revenue_at_risk": total_revenue_at_risk,
        "predicted_recovery": total_predicted_recovery,
        "actual_recovery": total_actual_recovery,
        "actual_recovery_rate": actual_recovery_rate,
        "prediction_error": prediction_error,
        "prediction_accuracy": prediction_accuracy
    }

    save_batch_result(result)

    print(
        f"\nOpportunities processed : "
        f"{result['opportunities']}"
    )

    print(
        f"EXECUTE                : "
        f"{result['executed']}"
    )

    print(
        f"ESCALATE               : "
        f"{result['escalated']}"
    )

    print(
        f"STOP                   : "
        f"{result['stopped']}"
    )

    print(
        f"\nRevenue at risk        : "
        f"₹{result['revenue_at_risk']:,.2f}"
    )

    print(
        f"Predicted recovery     : "
        f"₹{result['predicted_recovery']:,.2f}"
    )

    print(
        f"Simulated actual       : "
        f"₹{result['actual_recovery']:,.2f}"
    )

    print(
        f"Actual recovery rate   : "
        f"{result['actual_recovery_rate'] * 100:.2f}%"
    )

    print(
        f"Prediction error       : "
        f"₹{result['prediction_error']:,.2f}"
    )

    print(
        f"Prediction accuracy    : "
        f"{result['prediction_accuracy'] * 100:.2f}%"
    )

    print(
        "\n📝 Batch result saved to PostgreSQL."
    )

    print(
        "⚠️ Actual recovery is simulated "
        "for test-mode evaluation."
    )

    return result


if __name__ == "__main__":

    measure_batch_recovery()