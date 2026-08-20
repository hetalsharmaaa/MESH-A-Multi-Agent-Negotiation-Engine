from app.agents.base_agent import BaseAgent
from app.models.schemas import Proposal, AgentType


class StaffAgent(BaseAgent):
    agent_type = AgentType.STAFF

    def observe(self) -> dict:
        by_ward: dict[str, dict] = {}
        for member in self.twin.staff.values():
            w = by_ward.setdefault(member.ward, {"available": 0, "avg_fatigue": 0.0, "count": 0})
            w["count"] += 1
            w["avg_fatigue"] += member.fatigue_score
            if member.available:
                w["available"] += 1
        for w in by_ward.values():
            if w["count"] > 0:
                w["avg_fatigue"] = round(w["avg_fatigue"] / w["count"], 2)
        return by_ward

    def propose(self, event: dict) -> list[Proposal]:
        """
        Reacts to 'convert_ward_beds' — checks whether enough staff
        are available in the target ward to actually run the extra beds.
        """
        proposals: list[Proposal] = []
        payload = event.get("payload", {})
        target_ward = payload.get("target_id")

        if not target_ward:
            return proposals

        state = self.observe()
        ward_info = state.get(target_ward, {"available": 0, "avg_fatigue": 0.0})

        if ward_info["available"] > 0:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="assign_staff",
                    target_id=target_ward,
                    reason=(
                        f"{ward_info['available']} staff available in {target_ward} "
                        f"(avg fatigue {ward_info['avg_fatigue']})."
                    ),
                    confidence=0.85 if ward_info["avg_fatigue"] < 0.7 else 0.5,
                    cost=ward_info["available"] * 5,
                    urgency=0.5,
                )
            )
        else:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="staff_shortage",
                    target_id=target_ward,
                    reason=f"No available staff in {target_ward} to support extra beds.",
                    confidence=0.9,
                    cost=0,
                    urgency=0.85,
                )
            )

        for p in proposals:
            self.announce(p)

        return proposals