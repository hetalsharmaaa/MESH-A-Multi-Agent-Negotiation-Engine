from app.agents.base_agent import BaseAgent
from app.models.schemas import Proposal, AgentType


class EmergencyAgent(BaseAgent):
    agent_type = AgentType.EMERGENCY

    def observe(self) -> dict:
        icu_beds = [b for b in self.twin.beds.values() if b.ward == "ICU"]
        free_icu = [b for b in icu_beds if b.status.value == "free"]
        return {
            "total_icu_beds": len(icu_beds),
            "free_icu_beds": len(free_icu),
            "occupancy_rate": (
                1 - (len(free_icu) / len(icu_beds)) if icu_beds else None
            ),
        }

    def propose(self, event: dict) -> list[Proposal]:
        """
        Handles events like:
        { "type": "patient_surge", "payload": { "ward": "ICU", "patient_count": 8 } }
        """
        proposals: list[Proposal] = []
        payload = event.get("payload", {})
        patient_count = payload.get("patient_count", 0)

        state = self.observe()
        free = state["free_icu_beds"]
        shortfall = patient_count - free

        if shortfall > 0:
            # Not enough ICU capacity — ask other wards to free up space.
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="request_overflow_capacity",
                    target_id="ICU",
                    reason=(
                        f"Incoming {patient_count} patients but only {free} free ICU "
                        f"beds available. Short by {shortfall} beds."
                    ),
                    confidence=0.95,
                    cost=shortfall * 10,   # placeholder cost model
                    urgency=min(1.0, 0.5 + 0.1 * shortfall),
                )
            )
        else:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="admit_to_icu",
                    target_id="ICU",
                    reason=f"{free} free ICU beds are sufficient for {patient_count} incoming patients.",
                    confidence=0.98,
                    cost=patient_count * 5,
                    urgency=0.4,
                )
            )

        for p in proposals:
            self.announce(p)

        return proposals