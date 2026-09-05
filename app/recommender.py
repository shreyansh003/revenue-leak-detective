from root_cause import get_main_root_cause
from detector import detect_revenue_leaks
from recovery_model import get_recovery_rate


def recommend_action(failure_reason):

    if failure_reason == "TIMEOUT":
        return {
            "action": "RETRY_PAYMENT",
            "reason": "Timeouts may be temporary, so a controlled retry can be attempted."
        }

    elif failure_reason == "BANK_ERROR":
        return {
            "action": "RETRY_LATER",
            "reason": "Bank errors may be temporary, so retrying later is safer than retrying immediately."
        }

    elif failure_reason == "INSUFFICIENT_FUNDS":
        return {
            "action": "OFFER_ALTERNATIVE_PAYMENT",
            "reason": "Retrying may not help unless the customer's available balance changes."
        }

    elif failure_reason == "CARD_DECLINED":
        return {
            "action": "OFFER_ALTERNATIVE_PAYMENT",
            "reason": "The customer can try another card or payment method."
        }

    else:
        return {
            "action": "MANUAL_REVIEW",
            "reason": "Unknown failure reason requires further investigation."
        }


def calculate_recovery(failed_revenue, recovery_rate):

    return failed_revenue * recovery_rate


if __name__ == "__main__":

    # 1. Detect the biggest revenue leak
    top_leak = detect_revenue_leaks()

    if top_leak is None:
        print("No revenue leak found.")
        exit()

    # 2. Find the main root cause
    root_cause = get_main_root_cause(
        top_leak["payment_method"],
        top_leak["device"],
        top_leak["hour"]
    )

    if root_cause is None:
        print("No root cause found.")
        exit()

    failure_reason = root_cause["failure_reason"]
    failed_transactions = root_cause["failed_transactions"]
    failed_revenue = root_cause["failed_revenue"]

    # 3. Decide what action should be taken
    recommendation = recommend_action(failure_reason)

    # 4. Get segment-aware recovery rate
    recovery = get_recovery_rate(
        top_leak["payment_method"],
        top_leak["device"],
        top_leak["hour"],
        failure_reason
    )

    recovery_rate = recovery["recovery_rate"]

    # 5. Estimate recoverable revenue
    estimated_recovery = calculate_recovery(
        failed_revenue,
        recovery_rate
    )

    print("\n🤖 DATA-DRIVEN RECOVERY DECISION")
    print("=" * 70)

    print(
        f"\nSegment           : "
        f"{top_leak['payment_method']} | "
        f"{top_leak['device']} | "
        f"{top_leak['hour']}:00"
    )

    print(f"Failure reason    : {failure_reason}")
    print(f"Failed payments   : {failed_transactions}")
    print(f"Revenue at risk   : ₹{failed_revenue:,.2f}")

    print(
        f"\nRecommended action: "
        f"{recommendation['action']}"
    )

    print(
        f"Historical recovery: "
        f"{recovery_rate * 100:.2f}%"
    )

    print(
        f"Recovery evidence : "
        f"{recovery['source']}"
    )

    print(
        f"Sample size       : "
        f"{recovery['sample_size']}"
    )

    print(
        f"Expected recovery : "
        f"₹{estimated_recovery:,.2f}"
    )

    print(
        f"\nWhy               : "
        f"{recommendation['reason']}"
    )