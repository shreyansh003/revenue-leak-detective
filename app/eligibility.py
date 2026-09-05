MIN_RECOVERY_RATE = 0.10
MIN_SAMPLE_SIZE = 30
MIN_EXPECTED_RECOVERY = 1000


def check_eligibility(
    recovery_rate,
    sample_size,
    expected_recovery,
    evidence
):

    # 1. Not enough historical evidence
    if sample_size < MIN_SAMPLE_SIZE:
        return {
            "decision": "STOP",
            "reason": "Not enough historical recovery evidence."
        }

    # 2. Recovery probability is too low
    if recovery_rate < MIN_RECOVERY_RATE:
        return {
            "decision": "STOP",
            "reason": "Historical recovery rate is too low."
        }

    # 3. Opportunity is too small
    if expected_recovery < MIN_EXPECTED_RECOVERY:
        return {
            "decision": "STOP",
            "reason": "Expected recovery is below the action threshold."
        }

    # 4. Weak evidence
    if evidence == "NO_DATA":
        return {
            "decision": "STOP",
            "reason": "No historical recovery evidence available."
        }

    # 5. Strong segment-specific evidence
    if evidence == "SEGMENT":
        return {
            "decision": "EXECUTE",
            "reason": "Strong segment-specific recovery evidence."
        }

    # 6. Failure-reason evidence is useful but less specific
    if evidence == "FAILURE_REASON":
        return {
            "decision": "ESCALATE",
            "reason": "Recovery evidence exists, but it is not segment-specific."
        }

    return {
        "decision": "STOP",
        "reason": "Unknown evidence type."
    }


if __name__ == "__main__":

    print("\n🛡️ ACTION ELIGIBILITY ENGINE")
    print("=" * 65)

    result = check_eligibility(
        recovery_rate=0.1591,
        sample_size=44,
        expected_recovery=11465.97,
        evidence="SEGMENT"
    )

    print("\nTest:")
    print(f"Decision : {result['decision']}")
    print(f"Reason   : {result['reason']}")