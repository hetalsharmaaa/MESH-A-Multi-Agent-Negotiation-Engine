from app.models.schemas import Proposal


# Weights from the project's own research plan (PDF): 
# 0.45 Patient Survival | 0.30 Waiting Time | 0.15 Staff Load | 0.10 Cost
WEIGHTS = {
    "patient_survival": 0.45,
    "waiting_time": 0.30,
    "staff_load": 0.15,
    "cost": 0.10,
}


def score_proposal(proposal: Proposal, agent_reliability: float = 1.0) -> float:
    """
    Converts a Proposal into a single utility score (higher = better).

    We don't have real clinical outcome data (this is a simulation), so each
    factor is proxied from the fields agents already fill in:
      - patient_survival  <- proposal.urgency (higher urgency actions addressed = more lives protected)
      - waiting_time       <- inverse of urgency delay risk (approximated via confidence)
      - staff_load         <- inverse of cost (rough proxy: higher cost implies more staff strain)
      - cost               <- inverse of proposal.cost, normalized
    Shortage/failure actions (no_capacity_available, staff_shortage, etc.)
    are automatically penalized so they never "win" a negotiation.
    """
    is_failure_action = proposal.action in {
        "no_capacity_available",
        "staff_shortage",
        "equipment_shortage",
        "medicine_shortage",
        "ot_shortage",
    }

    # Normalize cost into a 0-1 "goodness" score (lower cost = higher score)
    # Cap at 200 as a rough max expected cost in this simulation.
    cost_goodness = max(0.0, 1 - (proposal.cost / 200))

    patient_survival = proposal.urgency
    waiting_time = proposal.confidence
    staff_load = cost_goodness  # proxy: cheaper actions assumed lighter on staff
    cost = cost_goodness

    raw_score = (
        WEIGHTS["patient_survival"] * patient_survival
        + WEIGHTS["waiting_time"] * waiting_time
        + WEIGHTS["staff_load"] * staff_load
        + WEIGHTS["cost"] * cost
    )

    # Weight by the proposing agent's trust/reliability score (Step 6 wires this properly)
    final_score = raw_score * agent_reliability

    if is_failure_action:
        final_score *= 0.1  # heavily deprioritize "we can't do it" proposals

    return round(final_score, 4)