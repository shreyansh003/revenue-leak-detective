from detector import detect_revenue_leaks
from root_cause import get_main_root_cause
from recovery_model import get_recovery_rate
from eligibility import check_eligibility
from action_guard import check_action


MAX_OPPORTUNITIES = 10


def calculate_opportunity(failed_revenue, historical_recovery_rate):
    return failed_revenue * historical_recovery_rate


def get_recommended_action(failure_reason):

    if failure_reason == "TIMEOUT":
        return "RETRY_PAYMENT"

    elif failure_reason == "BANK_ERROR":
        return "RETRY_LATER"

    elif failure_reason == "INSUFFICIENT_FUNDS":
        return "OFFER_ALTERNATIVE_PAYMENT"

    elif failure_reason == "CARD_DECLINED":
        return "OFFER_ALTERNATIVE_PAYMENT"

    else:
        return "MANUAL_REVIEW"


def rank_opportunities():

    print("\n⚙️ BUILDING RECOVERY OPPORTUNITIES...")

    leaks = detect_revenue_leaks(return_all=True)

    leaks = leaks[:MAX_OPPORTUNITIES]

    opportunities = []

    for index, leak in enumerate(leaks, start=1):

        print(
            f"Processing opportunity "
            f"{index}/{len(leaks)}..."
        )

        root_cause = get_main_root_cause(
            leak["payment_method"],
            leak["device"],
            leak["hour"]
        )

        if root_cause is None:
            continue

        failure_reason = root_cause["failure_reason"]

        recovery = get_recovery_rate(
            leak["payment_method"],
            leak["device"],
            leak["hour"],
            failure_reason
        )

        # -------------------------------------------------
        # HISTORICAL RECOVERY SIGNAL
        # -------------------------------------------------

        historical_recovery_rate = (
            recovery["historical_recovery_rate"]
        )

        predicted_recovery = calculate_opportunity(
            root_cause["failed_revenue"],
            historical_recovery_rate
        )

        # -------------------------------------------------
        # ELIGIBILITY
        # -------------------------------------------------

        eligibility = check_eligibility(
            historical_recovery_rate,
            recovery["sample_size"],
            predicted_recovery,
            recovery["source"]
        )

        # -------------------------------------------------
        # ACTION RECOMMENDATION
        # -------------------------------------------------

        action = get_recommended_action(
            failure_reason
        )

        # -------------------------------------------------
        # SAFETY GUARD
        # -------------------------------------------------

        guard = check_action(
            action,
            retry_count=0,
            failed_revenue=root_cause["failed_revenue"]
        )

        # -------------------------------------------------
        # FINAL DECISION
        # -------------------------------------------------

        if eligibility["decision"] == "STOP":

            final_decision = "STOP"
            final_reason = eligibility["reason"]

        elif guard["decision"] == "STOP":

            final_decision = "STOP"
            final_reason = guard["reason"]

        elif eligibility["decision"] == "ESCALATE":

            final_decision = "ESCALATE"
            final_reason = eligibility["reason"]

        else:

            final_decision = guard["decision"]
            final_reason = guard["reason"]

        # -------------------------------------------------
        # OPPORTUNITY OBJECT
        # -------------------------------------------------

        opportunities.append({

            "payment_method":
                leak["payment_method"],

            "device":
                leak["device"],

            "hour":
                leak["hour"],

            "failure_reason":
                failure_reason,

            # Detection information
            "leak_score":
                leak["leak_score"],

            "segment_total_transactions":
                leak["total_transactions"],

            "segment_failed_transactions":
                leak["failed_transactions"],

            "segment_failure_rate":
                leak["failure_rate"],

            "segment_revenue_at_risk":
                leak["failed_revenue"],

            # Root cause information
            "root_cause_failed_transactions":
                root_cause["failed_transactions"],

            "root_cause_revenue":
                root_cause["failed_revenue"],

            # Historical evidence
            "historical_recovery_rate":
                historical_recovery_rate,

            "historical_sample_size":
                recovery["sample_size"],

            "historical_subsequent_successes":
                recovery["subsequent_successes"],

            "evidence_source":
                recovery["source"],

            "evidence_interpretation":
                recovery["interpretation"],

            # Predicted recovery
            "predicted_recovery":
                predicted_recovery,

            # Keep old key for compatibility
            "recovery_rate":
                historical_recovery_rate,

            "expected_recovery":
                predicted_recovery,

            "evidence":
                recovery["source"],

            "recovery_source":
                recovery["source"],

            "sample_size":
                recovery["sample_size"],

            # Action
            "recommended_action":
                action,

            # Eligibility
            "eligibility":
                eligibility["decision"],

            "eligibility_decision":
                eligibility["decision"],

            "eligibility_reason":
                eligibility["reason"],

            # Guard
            "guard_decision":
                guard["decision"],

            "guard_allowed":
                guard["allowed"],

            "guard_reason":
                guard["reason"],

            # Final decision
            "final_decision":
                final_decision,

            "final_reason":
                final_reason
        })

    # Highest predicted recovery first

    opportunities.sort(
        key=lambda x: x["predicted_recovery"],
        reverse=True
    )

    return opportunities


if __name__ == "__main__":

    opportunities = rank_opportunities()

    print("\n💰 RECOVERY OPPORTUNITY RANKING")
    print("=" * 75)

    for i, opportunity in enumerate(
        opportunities,
        start=1
    ):

        print(
            f"\n#{i} "
            f"{opportunity['payment_method']} | "
            f"{opportunity['device']} | "
            f"{opportunity['hour']}:00"
        )

        print(
            f"Root cause              : "
            f"{opportunity['failure_reason']}"
        )

        print(
            f"Segment failures        : "
            f"{opportunity['segment_failed_transactions']}"
        )

        print(
            f"Root cause failures     : "
            f"{opportunity['root_cause_failed_transactions']}"
        )

        print(
            f"Root cause value        : "
            f"₹{opportunity['root_cause_revenue']:,.2f}"
        )

        print(
            f"Historical recovery     : "
            f"{opportunity['historical_recovery_rate'] * 100:.2f}%"
        )

        print(
            f"Historical sample       : "
            f"{opportunity['historical_sample_size']}"
        )

        print(
            f"Subsequent successes    : "
            f"{opportunity['historical_subsequent_successes']}"
        )

        print(
            f"Predicted recovery      : "
            f"₹{opportunity['predicted_recovery']:,.2f}"
        )

        print(
            f"Evidence source         : "
            f"{opportunity['evidence_source']}"
        )

        print(
            f"Evidence interpretation : "
            f"{opportunity['evidence_interpretation']}"
        )

        print(
            f"Recommended action      : "
            f"{opportunity['recommended_action']}"
        )

        print(
            f"Eligibility             : "
            f"{opportunity['eligibility_decision']}"
        )

        print(
            f"Eligibility reason      : "
            f"{opportunity['eligibility_reason']}"
        )

        print(
            f"Guard decision          : "
            f"{opportunity['guard_decision']}"
        )

        print(
            f"Guard allowed           : "
            f"{opportunity['guard_allowed']}"
        )

        print(
            f"FINAL DECISION          : "
            f"{opportunity['final_decision']}"
        )

        print(
            f"Reason                  : "
            f"{opportunity['final_reason']}"
        )

    print(
        "\n⚠️ Historical recovery is an observational "
        "signal, not causal intervention evidence."
    )