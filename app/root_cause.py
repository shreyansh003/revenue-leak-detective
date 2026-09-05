from database import get_connection


def get_root_causes(payment_method, device, hour):

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            failure_reason,
            COUNT(*) AS failed_transactions,
            SUM(amount) AS failed_revenue
        FROM transactions
        WHERE payment_method = %s
          AND device = %s
          AND EXTRACT(HOUR FROM timestamp) = %s
          AND status = 'failed'
        GROUP BY failure_reason
        ORDER BY failed_revenue DESC;
    """

    cursor.execute(
        query,
        (payment_method, device, hour)
    )

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    return results


def get_main_root_cause(payment_method, device, hour):

    causes = get_root_causes(
        payment_method,
        device,
        hour
    )

    if not causes:
        return None

    main_cause = causes[0]

    return {
        "failure_reason": main_cause[0],
        "failed_transactions": main_cause[1],
        "failed_revenue": float(main_cause[2])
    }


if __name__ == "__main__":

    result = get_main_root_cause(
        "UPI",
        "mobile",
        21
    )

    print("\n🔍 MAIN ROOT CAUSE")
    print("=" * 60)

    if result:

        print(
            f"Failure reason     : "
            f"{result['failure_reason']}"
        )

        print(
            f"Failed payments    : "
            f"{result['failed_transactions']}"
        )

        print(
            f"Revenue at risk    : "
            f"₹{result['failed_revenue']:,.2f}"
        )

    else:
        print("No failure data found.")