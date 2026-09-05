from app.core.digital_twin import DigitalTwin
from app.core.event_bus import EventBus
from app.models.schemas import Proposal
from app.negotiation.utility import score_proposal

from app.agents.emergency_agent import EmergencyAgent
from app.agents.bed_agent import BedAgent
from app.agents.staff_agent import StaffAgent
from app.agents.equipment_agent import EquipmentAgent
from app.agents.pharmacy_agent import PharmacyAgent
from app.agents.ot_agent import OTAgent
from app.negotiation.trust import trust_engine


class NegotiationEngine:
    """
    Orchestrates multi-agent negotiation for a given scenario.

    Flow (matches the PDF's architecture):
      Hospital -> Digital Twin -> Multi-Agent System -> Negotiation
      -> Constraint Verification -> Explainable Decision

    This class handles the "Negotiation" stage: it runs the relevant
    agents in sequence, collects every proposal made along the chain,
    scores them all with the utility function, and returns the winner
    plus a full decision trace.
    """

    def __init__(self, twin: DigitalTwin, bus: EventBus):
        self.twin = twin
        self.bus = bus
        self.agents = {
            "emergency": EmergencyAgent(twin, bus),
            "bed": BedAgent(twin, bus),
            "staff": StaffAgent(twin, bus),
            "equipment": EquipmentAgent(twin, bus),
            "pharmacy": PharmacyAgent(twin, bus),
            "ot": OTAgent(twin, bus),
        }

    def run_patient_surge(self, ward: str, patient_count: int) -> dict:
        """
        Handles the 'patient_surge' scenario end-to-end:
        Emergency reports shortfall -> Bed offers overflow -> Staff confirms ->
        Equipment confirms -> all proposals scored -> best plan selected.
        """
        trace: list[dict] = []
        all_proposals: list[Proposal] = []

        # Step 1: Emergency Agent evaluates the surge
        emergency_event = self.bus.publish(
            "patient_surge",
            payload={"target_id": ward, "patient_count": patient_count},
            source="simulation",
        )
        emergency_proposals = self.agents["emergency"].propose(emergency_event)
        all_proposals.extend(emergency_proposals)
        trace.append({
            "stage": "emergency_assessment",
            "agent": "emergency",
            "proposals": [p.model_dump() for p in emergency_proposals],
        })

        # If ICU capacity was sufficient, negotiation ends here — no shortfall to resolve
        top_emergency = emergency_proposals[0]
        if top_emergency.action == "admit_to_icu":
            return self._finalize(trace, all_proposals, winner=top_emergency)

        # Step 2: There's a shortfall — Bed Agent looks for overflow capacity
        shortfall = patient_count - self.agents["emergency"].observe()["free_icu_beds"]
        bed_event = {
            "type": "request_overflow_capacity",
            "payload": {"target_id": ward, "shortfall": shortfall},
        }
        bed_proposals = self.agents["bed"].propose(bed_event)
        all_proposals.extend(bed_proposals)
        trace.append({
            "stage": "bed_overflow_search",
            "agent": "bed",
            "proposals": [p.model_dump() for p in bed_proposals],
        })

        best_bed_proposal = max(bed_proposals, key=lambda p: p.confidence, default=None)

        if not best_bed_proposal or best_bed_proposal.action == "no_capacity_available":
            return self._finalize(trace, all_proposals, winner=best_bed_proposal)

        overflow_ward = best_bed_proposal.target_id

        # Step 3: Staff Agent checks coverage for the overflow ward
        staff_event = {
            "type": "convert_ward_beds",
            "payload": {"target_id": overflow_ward},
        }
        staff_proposals = self.agents["staff"].propose(staff_event)
        all_proposals.extend(staff_proposals)
        trace.append({
            "stage": "staff_coverage_check",
            "agent": "staff",
            "proposals": [p.model_dump() for p in staff_proposals],
        })

        # Step 4: Equipment Agent checks critical gear for the overflow ward
        equipment_event = {
            "type": "convert_ward_beds",
            "payload": {"target_id": overflow_ward, "equipment_type": "ventilator"},
        }
        equipment_proposals = self.agents["equipment"].propose(equipment_event)
        all_proposals.extend(equipment_proposals)
        trace.append({
            "stage": "equipment_check",
            "agent": "equipment",
            "proposals": [p.model_dump() for p in equipment_proposals],
        })

        # Step 5: Score everything and pick the winning plan
        return self._finalize(trace, all_proposals)

    def _finalize(self, trace: list[dict], proposals: list[Proposal], winner: Proposal = None) -> dict:
        scored = [
            {
                "proposal": p.model_dump(),
                "score": score_proposal(p, trust_engine.get_score(p.agent)),
            }
            for p in proposals
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)

        if winner is None and scored:
            winner = Proposal(**scored[0]["proposal"])

        # Record outcomes: the winning agent's proposal "succeeded",
        # shortage/failure proposals count as a miss for that agent.
        for p in proposals:
            if winner and p.agent == winner.agent and p.action == winner.action:
                trust_engine.record_outcome(p.agent, success=True, note="Proposal selected as winning action")
            elif p.action in {
                "no_capacity_available", "staff_shortage",
                "equipment_shortage", "medicine_shortage", "ot_shortage",
            }:
                trust_engine.record_outcome(p.agent, success=False, note=p.reason)

        return {
            "decision_trace": trace,
            "scored_proposals": scored,
            "winning_action": winner.model_dump() if winner else None,
            "trust_snapshot": trust_engine.snapshot(),
        }