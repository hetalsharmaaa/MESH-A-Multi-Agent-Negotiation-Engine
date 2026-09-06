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
from app.verification.constraint_checker import ConstraintChecker
from app.explainability.decision_trace import generate_decision_trace


class NegotiationEngine:
    """
    Orchestrates multi-agent negotiation for a given scenario.

    Flow (matches the PDF's architecture):
      Hospital -> Digital Twin -> Multi-Agent System -> Negotiation
      -> Constraint Verification -> Explainable Decision
    """

    def __init__(self, twin: DigitalTwin, bus: EventBus):
        self.twin = twin
        self.bus = bus
        self.verifier = ConstraintChecker(twin)
        self.agents = {
            "emergency": EmergencyAgent(twin, bus),
            "bed": BedAgent(twin, bus),
            "staff": StaffAgent(twin, bus),
            "equipment": EquipmentAgent(twin, bus),
            "pharmacy": PharmacyAgent(twin, bus),
            "ot": OTAgent(twin, bus),
        }

    def run_patient_surge(self, ward: str, patient_count: int) -> dict:
        trace: list[dict] = []
        all_proposals: list[Proposal] = []

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

        top_emergency = emergency_proposals[0]
        if top_emergency.action == "admit_to_icu":
            return self._finalize(trace, all_proposals, winner=top_emergency)

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

        return self._finalize(trace, all_proposals)

    def run_equipment_failure(self, ward: str, equipment_type: str = "ventilator") -> dict:
        """
        Handles an equipment failure scenario: Equipment Agent reports the
        failure, then checks if the same ward (or reallocation) has a working
        replacement available.
        """
        trace: list[dict] = []
        all_proposals: list[Proposal] = []

        equipment_event = {
            "type": "equipment_check",
            "payload": {"target_id": ward, "equipment_type": equipment_type},
        }
        equipment_proposals = self.agents["equipment"].propose(equipment_event)
        all_proposals.extend(equipment_proposals)
        trace.append({
            "stage": "equipment_assessment",
            "agent": "equipment",
            "proposals": [p.model_dump() for p in equipment_proposals],
        })

        top = equipment_proposals[0]
        if top.action == "allocate_equipment":
            return self._finalize(trace, all_proposals, winner=top)

        staff_event = {
            "type": "convert_ward_beds",
            "payload": {"target_id": ward},
        }
        staff_proposals = self.agents["staff"].propose(staff_event)
        all_proposals.extend(staff_proposals)
        trace.append({
            "stage": "staff_fallback_check",
            "agent": "staff",
            "proposals": [p.model_dump() for p in staff_proposals],
        })

        return self._finalize(trace, all_proposals)

    def run_medicine_shortage(self, medicine: str, amount_needed: int) -> dict:
        """
        Handles a medicine shortage scenario: Pharmacy Agent checks stock,
        and if insufficient, this is flagged directly (no substitute agent
        exists yet — a good future-work item to mention in your report).
        """
        trace: list[dict] = []
        all_proposals: list[Proposal] = []

        pharmacy_event = {
            "type": "medicine_demand",
            "payload": {"medicine": medicine, "amount": amount_needed},
        }
        pharmacy_proposals = self.agents["pharmacy"].propose(pharmacy_event)
        all_proposals.extend(pharmacy_proposals)
        trace.append({
            "stage": "pharmacy_assessment",
            "agent": "pharmacy",
            "proposals": [p.model_dump() for p in pharmacy_proposals],
        })

        return self._finalize(trace, all_proposals)

    def run_ot_overload(self, surgery_count: int) -> dict:
        """
        Handles an OT overload scenario: OT Agent checks slot availability,
        and if insufficient, Staff Agent checks if extending hours / adding
        a shift is feasible.
        """
        trace: list[dict] = []
        all_proposals: list[Proposal] = []

        ot_event = {
            "type": "surgery_request",
            "payload": {"surgery_count": surgery_count},
        }
        ot_proposals = self.agents["ot"].propose(ot_event)
        all_proposals.extend(ot_proposals)
        trace.append({
            "stage": "ot_assessment",
            "agent": "ot",
            "proposals": [p.model_dump() for p in ot_proposals],
        })

        top = ot_proposals[0]
        if top.action == "schedule_surgery":
            return self._finalize(trace, all_proposals, winner=top)

        staff_event = {
            "type": "convert_ward_beds",
            "payload": {"target_id": "OT"},
        }
        staff_proposals = self.agents["staff"].propose(staff_event)
        all_proposals.extend(staff_proposals)
        trace.append({
            "stage": "staff_extension_check",
            "agent": "staff",
            "proposals": [p.model_dump() for p in staff_proposals],
        })

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

        verification_log = []
        verified_winner = None

        if winner:
            candidates = [winner] + [Proposal(**s["proposal"]) for s in scored if Proposal(**s["proposal"]) != winner]
            seen = set()
            ordered_candidates = []
            for c in candidates:
                key = (c.agent, c.action, c.target_id)
                if key not in seen:
                    seen.add(key)
                    ordered_candidates.append(c)

            for candidate in ordered_candidates:
                violations = self.verifier.check(candidate)
                verification_log.append({
                    "candidate": candidate.model_dump(),
                    "violations": [v.to_dict() for v in violations],
                    "passed": len(violations) == 0,
                })
                if not violations:
                    verified_winner = candidate
                    break

        for p in proposals:
            if verified_winner and p.agent == verified_winner.agent and p.action == verified_winner.action:
                trust_engine.record_outcome(p.agent, success=True, note="Proposal passed verification and was selected")
            elif p.action in {
                "no_capacity_available", "staff_shortage",
                "equipment_shortage", "medicine_shortage", "ot_shortage",
            }:
                trust_engine.record_outcome(p.agent, success=False, note=p.reason)

        result = {
            "decision_trace": trace,
            "scored_proposals": scored,
            "verification_log": verification_log,
            "winning_action": verified_winner.model_dump() if verified_winner else None,
            "verification_failed_completely": verified_winner is None and winner is not None,
            "trust_snapshot": trust_engine.snapshot(),
        }
        result["decision_summary"] = generate_decision_trace(result)
        return result