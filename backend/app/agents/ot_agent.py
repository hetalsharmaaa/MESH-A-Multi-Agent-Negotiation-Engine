from app.agents.base_agent import BaseAgent
from app.models.schemas import Proposal, AgentType


class OTAgent(BaseAgent):
    """
    Operation Theatre agent. Reuses bed logic scoped to OT-type wards
    since OTs are modeled as a special ward in the Digital Twin.
    """
    agent_type = AgentType.OT

    def observe(self) -> dict:
        ot_beds = [b for b in self.twin.beds.values() if b.ward == "OT"]
        free = [b for b in ot_beds if b.status.value == "free"]
        return {"total_ot_slots": len(ot_beds), "free_ot_slots": len(free)}

    def propose(self, event: dict) -> list[Proposal]:
        """
        Reacts to 'surgery_request' events.
        """
        proposals: list[Proposal] = []
        payload = event.get("payload", {})
        surgery_count = payload.get("surgery_count", 0)

        state = self.observe()
        free = state["free_ot_slots"]

        if free >= surgery_count:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="schedule_surgery",
                    target_id="OT",
                    reason=f"{free} free OT slots available for {surgery_count} surgeries.",
                    confidence=0.9,
                    cost=surgery_count * 20,
                    urgency=0.5,
                )
            )
        else:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="ot_shortage",
                    target_id="OT",
                    reason=f"Only {free} free OT slots for {surgery_count} requested surgeries.",
                    confidence=0.9,
                    cost=0,
                    urgency=0.7,
                )
            )

        for p in proposals:
            self.announce(p)

        return proposals