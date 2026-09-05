from database import get_connection


MIN_SEGMENT_FAILURES = 30


def get_recovery_rate(
    payment_method,
    device,
    hour,
    failure_reason
):

    connection = get_connection()
    cursor = connection.cursor()


    # -----------------------------------------------------
    # SEGMENT-SPECIFIC HISTORICAL SIGNAL
    # -----------------------------------------------------

    segment_query = """
        SELECT
            COUNT(*) AS failed_payments,

            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1
                    FROM transactions t2
                    WHERE t2.customer_id = t1.customer_id
                      AND t2.status = 'success'
                      AND t2.timestamp > t1.timestamp
                      AND t2.timestamp <=
                          t1.timestamp + INTERVAL '24 hours'
                )
            ) AS subsequent_successes

        FROM transactions t1

        WHERE t1.status = 'failed'
          AND t1.payment_method = %s
          AND t1.device = %s
          AND EXTRACT(HOUR FROM t1.timestamp) = %s
          AND t1.failure_reason = %s;
    """


    cursor.execute(
        segment_query,
        (
            payment_method,
            device,
            hour,
            failure_reason
        )
    )


    segment_result = cursor.fetchone()

    segment_failed = segment_result[0]
    segment_successes = segment_result[1]


    if segment_failed >= MIN_SEGMENT_FAILURES:

        historical_rate = (
            segment_successes / segment_failed
        )

        cursor.close()
        connection.close()

        return {

            "historical_recovery_rate":
                historical_rate,

            "recovery_rate":
                historical_rate,

            "source":
                "SEGMENT",

            "sample_size":
                segment_failed,

            "subsequent_successes":
                segment_successes,

            "recovered":
                segment_successes,

            "interpretation":
                "Historical subsequent-success signal"
        }


    # -----------------------------------------------------
    # FAILURE-REASON FALLBACK
    # -----------------------------------------------------

    fallback_query = """
        SELECT
            COUNT(*) AS failed_payments,

            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1
                    FROM transactions t2
                    WHERE t2.customer_id = t1.customer_id
                      AND t2.status = 'success'
                      AND t2.timestamp > t1.timestamp
                      AND t2.timestamp <=
                          t1.timestamp + INTERVAL '24 hours'
                )
            ) AS subsequent_successes

        FROM transactions t1

        WHERE t1.status = 'failed'
          AND t1.failure_reason = %s;
    """


    cursor.execute(
        fallback_query,
        (failure_reason,)
    )


    fallback_result = cursor.fetchone()

    failed = fallback_result[0]
    successes = fallback_result[1]


    cursor.close()
    connection.close()


    if failed == 0:

        return {

            "historical_recovery_rate": 0,

            "recovery_rate": 0,

            "source": "NO_DATA",

            "sample_size": 0,

            "subsequent_successes": 0,

            "recovered": 0,

            "interpretation":
                "No historical recovery signal available"
        }


    historical_rate = successes / failed


    return {

        "historical_recovery_rate":
            historical_rate,

        "recovery_rate":
            historical_rate,

        "source":
            "FAILURE_REASON",

        "sample_size":
            failed,

        "subsequent_successes":
            successes,

        "recovered":
            successes,

        "interpretation":
            "Historical subsequent-success signal"
    }


if __name__ == "__main__":

    result = get_recovery_rate(
        "UPI",
        "mobile",
        21,
        "BANK_ERROR"
    )


    print("\n📈 HISTORICAL RECOVERY SIGNAL")
    print("=" * 70)

    print(
        f"\nHistorical recovery signal : "
        f"{result['historical_recovery_rate'] * 100:.2f}%"
    )

    print(
        f"Evidence source            : "
        f"{result['source']}"
    )

    print(
        f"Historical sample          : "
        f"{result['sample_size']}"
    )

    print(
        f"Subsequent successes       : "
        f"{result['subsequent_successes']}"
    )

    print(
        f"\nInterpretation             : "
        f"{result['interpretation']}"
    )

    print(
        "\n⚠️ This is observational historical evidence, "
        "not causal proof of intervention impact."
    )