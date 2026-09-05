from app.agents.base_agent import BaseAgent
from app.models.schemas import Proposal, AgentType


class BedAgent(BaseAgent):
    agent_type = AgentType.BED

    def observe(self) -> dict:
        by_ward: dict[str, dict] = {}
        for bed in self.twin.beds.values():
            w = by_ward.setdefault(bed.ward, {"total": 0, "free": 0})
            w["total"] += 1
            if bed.status.value == "free":
                w["free"] += 1
        return by_ward

    def propose(self, event: dict) -> list[Proposal]:
        """
        Reacts to 'request_overflow_capacity' — checks whether beds
        in other wards can be converted/reassigned to cover the shortfall.
        """
        proposals: list[Proposal] = []
        payload = event.get("payload", {})

        shortfall = payload.get("shortfall")
        requesting_ward = payload.get("target_id", "ICU")

        if shortfall is None:
            return proposals

        state = self.observe()
        for ward, info in state.items():
            if ward == requesting_ward:
                continue
            if info["free"] > 0:
                offer = min(info["free"], shortfall)
                proposals.append(
                    Proposal(
                        agent=self.agent_type,
                        action="convert_ward_beds",
                        target_id=ward,
                        reason=(
                            f"{ward} has {info['free']} free beds. Offering {offer} "
                            f"to cover {requesting_ward} shortfall of {shortfall}."
                        ),
                        confidence=0.75,
                        cost=offer * 15,
                        urgency=0.6,
                    )
                )
                shortfall -= offer
            if shortfall <= 0:
                break

        if not proposals:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="no_capacity_available",
                    target_id=requesting_ward,
                    reason="No free beds in any other ward to offer as overflow.",
                    confidence=0.9,
                    cost=0,
                    urgency=0.9,
                )
            )

        for p in proposals:
            self.announce(p)

        return proposals