# Maximum number of automated retries allowed
MAX_RETRIES = 1


def check_action(
    action,
    retry_count,
    failed_revenue
):

    # --------------------------------------------------
    # RULE 1: Never retry more than the allowed limit
    # --------------------------------------------------

    if action in ["RETRY_PAYMENT", "RETRY_LATER"]:

        if retry_count >= MAX_RETRIES:

            return {
                "allowed": False,
                "decision": "STOP",
                "reason": "Maximum retry limit reached."
            }

        return {
            "allowed": True,
            "decision": "EXECUTE",
            "reason": "Retry is within the allowed limit."
        }

    # --------------------------------------------------
    # RULE 2: Alternative payment does not need retry
    # --------------------------------------------------

    if action == "OFFER_ALTERNATIVE_PAYMENT":

        return {
            "allowed": True,
            "decision": "ESCALATE",
            "reason": "Customer should be offered an alternative payment method."
        }

    # --------------------------------------------------
    # RULE 3: Unknown actions require human review
    # --------------------------------------------------

    if action == "MANUAL_REVIEW":

        return {
            "allowed": False,
            "decision": "MANUAL_REVIEW",
            "reason": "Action requires human review."
        }

    # --------------------------------------------------
    # Safety fallback
    # --------------------------------------------------

    return {
        "allowed": False,
        "decision": "STOP",
        "reason": "Unknown action blocked by safety guard."
    }


if __name__ == "__main__":

    print("\n🛡️ ACTION GUARD TEST")
    print("=" * 65)

    # Test 1: Retry allowed
    result = check_action(
        "RETRY_LATER",
        0,
        72071.82
    )

    print("\nTest 1")
    print(f"Allowed  : {result['allowed']}")
    print(f"Decision : {result['decision']}")
    print(f"Reason   : {result['reason']}")

    # Test 2: Retry blocked
    result = check_action(
        "RETRY_LATER",
        1,
        72071.82
    )

    print("\nTest 2")
    print(f"Allowed  : {result['allowed']}")
    print(f"Decision : {result['decision']}")
    print(f"Reason   : {result['reason']}")

    # Test 3: Alternative payment
    result = check_action(
        "OFFER_ALTERNATIVE_PAYMENT",
        0,
        72071.82
    )

    print("\nTest 3")
    print(f"Allowed  : {result['allowed']}")
    print(f"Decision : {result['decision']}")
    print(f"Reason   : {result['reason']}")