def generate_decision_trace(negotiation_result: dict) -> dict:
    """
    Converts the raw negotiation result (decision_trace + verification_log +
    winning_action) into a clean, human-readable reasoning chain — the
    "Decision Trace" format the project's research plan calls for, instead
    of a generic "AI recommends X" black box.

    Example output:
      {
        "recommendation": "Convert Ward Beds (Ward-C)",
        "chain": [
          "[emergency_assessment] Emergency Agent: Incoming 5 patients but only 2 free ICU beds. Short by 3 beds.",
          "[bed_overflow_search] Bed Agent: Ward-C has 1 free bed. Offering 1 to cover ICU shortfall of 3.",
          "[staff_coverage_check] Staff Agent: No available staff in Ward-C to support extra beds.",
          "[equipment_check] Equipment Agent: 1 ventilator(s) available for Ward-C.",
          "Verification: passed all constraint checks.",
          "Selected action: convert_ward_beds on Ward-C",
          "Confidence: 75.0%"
        ],
        "confidence_percent": 75.0
      }
    """
    winner = negotiation_result.get("winning_action")

    if not winner:
        return {
            "recommendation": "No feasible action found",
            "chain": ["Every candidate proposal failed verification or no proposals were made."],
            "confidence_percent": 0,
        }

    chain: list[str] = []

    # Step-by-step reasoning from each agent that participated
    for stage in negotiation_result.get("decision_trace", []):
        for p in stage["proposals"]:
            agent_label = p["agent"].replace("_", " ").title()
            chain.append(f"[{stage['stage']}] {agent_label} Agent: {p['reason']}")

    # Verification outcome for the winning candidate
    verification_log = negotiation_result.get("verification_log", [])
    winner_verification = next(
        (
            v for v in verification_log
            if v["candidate"]["agent"] == winner["agent"] and v["candidate"]["action"] == winner["action"]
        ),
        None,
    )
    if winner_verification:
        if winner_verification["passed"]:
            chain.append("Verification: passed all constraint checks.")
        else:
            reasons = "; ".join(v["detail"] for v in winner_verification["violations"])
            chain.append(f"Verification: flagged issues ({reasons}) — fell back to next best option.")

    # Final decision + confidence
    action_label = winner["action"].replace("_", " ").title()
    target = winner.get("target_id", "N/A")
    chain.append(f"Selected action: {winner['action']} on {target}")

    confidence_percent = round(winner["confidence"] * 100, 1)
    chain.append(f"Confidence: {confidence_percent}%")

    return {
        "recommendation": f"{action_label} ({target})",
        "chain": chain,
        "confidence_percent": confidence_percent,
    }