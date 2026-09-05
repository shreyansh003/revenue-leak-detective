from database import get_connection


BASELINE_FAILURE_RATE = 5.46
MIN_TRANSACTIONS = 50


def detect_revenue_leaks(return_all=False):

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            payment_method,
            device,
            EXTRACT(HOUR FROM timestamp)::int AS hour,

            COUNT(*) AS total_transactions,

            COUNT(*) FILTER (
                WHERE status = 'failed'
            ) AS failed_transactions,

            ROUND(
                COUNT(*) FILTER (
                    WHERE status = 'failed'
                ) * 100.0 / COUNT(*),
                2
            ) AS failure_rate,

            ROUND(
                SUM(amount) FILTER (
                    WHERE status = 'failed'
                ),
                2
            ) AS failed_revenue

        FROM transactions

        GROUP BY
            payment_method,
            device,
            EXTRACT(HOUR FROM timestamp)

        HAVING COUNT(*) >= %s;
    """

    cursor.execute(query, (MIN_TRANSACTIONS,))

    results = cursor.fetchall()

    leaks = []

    for row in results:

        payment_method = row[0]
        device = row[1]
        hour = row[2]
        total_transactions = row[3]
        failed_transactions = row[4]
        failure_rate = float(row[5])
        failed_revenue = float(row[6] or 0)

        # Ignore segments that are not worse than baseline
        if failure_rate <= BASELINE_FAILURE_RATE:
            continue

        # Calculate expected failures
        expected_failures = (
            total_transactions * BASELINE_FAILURE_RATE / 100
        )

        # Calculate excess failures
        excess_failures = (
            failed_transactions - expected_failures
        )

        # How much worse is this segment?
        rate_deviation = (
            failure_rate - BASELINE_FAILURE_RATE
        )

        # Leak score
        leak_score = (
            rate_deviation * 10
            + excess_failures * 0.5
            + failed_revenue / 10000
        )

        leaks.append({
            "payment_method": payment_method,
            "device": device,
            "hour": hour,
            "total_transactions": total_transactions,
            "failed_transactions": failed_transactions,
            "failure_rate": failure_rate,
            "expected_failures": expected_failures,
            "excess_failures": excess_failures,
            "failed_revenue": failed_revenue,
            "leak_score": leak_score
        })

    # Highest leak score first
    leaks.sort(
        key=lambda x: x["leak_score"],
        reverse=True
    )
    top_leak = leaks[0] if leaks else None

    print("\n🚨 REVENUE LEAK DETECTIVE")
    print("=" * 75)

    print(
        f"Baseline failure rate: {BASELINE_FAILURE_RATE}%"
    )

    print(
        f"Minimum transactions: {MIN_TRANSACTIONS}"
    )

    print("\n🔎 TOP REVENUE LEAKS")
    print("=" * 75)

    for i, leak in enumerate(leaks[:10], start=1):

        print(
            f"\n#{i} "
            f"{leak['payment_method']} | "
            f"{leak['device']} | "
            f"{leak['hour']}:00"
        )

        print(
            f"Leak Score       : "
            f"{leak['leak_score']:.2f}"
        )

        print(
            f"Failure rate     : "
            f"{leak['failure_rate']}%"
        )

        print(
            f"Expected failures: "
            f"{leak['expected_failures']:.0f}"
        )

        print(
            f"Actual failures  : "
            f"{leak['failed_transactions']}"
        )

        print(
            f"Excess failures  : "
            f"{leak['excess_failures']:.0f}"
        )

        print(
            f"Revenue at risk  : "
            f"₹{leak['failed_revenue']:,.2f}"
        )

    cursor.close()
    connection.close()

    if return_all:
        return leaks

    return top_leak


if __name__ == "__main__":
    detect_revenue_leaks()