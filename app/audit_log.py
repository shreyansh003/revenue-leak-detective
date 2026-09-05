from database import get_connection


def log_recovery_decision(
    payment_method,
    device,
    hour,
    failure_reason,
    failed_transactions,
    revenue_at_risk,
    recommended_action,
    recovery_rate,
    estimated_recovery,
    guard_allowed,
    guard_decision,
    execution_status
):

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO recovery_audit_log (
            payment_method,
            device,
            hour,
            failure_reason,
            failed_transactions,
            revenue_at_risk,
            recommended_action,
            recovery_rate,
            estimated_recovery,
            guard_allowed,
            guard_decision,
            execution_status
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        );
    """

    cursor.execute(
        query,
        (
            payment_method,
            device,
            hour,
            failure_reason,
            failed_transactions,
            revenue_at_risk,
            recommended_action,
            recovery_rate,
            estimated_recovery,
            guard_allowed,
            guard_decision,
            execution_status
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


if __name__ == "__main__":

    log_recovery_decision(
        "UPI",
        "mobile",
        21,
        "BANK_ERROR",
        44,
        72071.82,
        "RETRY_LATER",
        0.1591,
        11465.97,
        True,
        "EXECUTE",
        "SIMULATED"
    )

    print("\n📝 AUDIT LOG")
    print("=" * 60)
    print("Recovery decision successfully recorded.")