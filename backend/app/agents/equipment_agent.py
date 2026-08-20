from app.agents.base_agent import BaseAgent
from app.models.schemas import Proposal, AgentType


class EquipmentAgent(BaseAgent):
    agent_type = AgentType.EQUIPMENT

    def observe(self) -> dict:
        by_type: dict[str, dict] = {}
        for item in self.twin.equipment.values():
            t = by_type.setdefault(item.type, {"total": 0, "available": 0, "faulty": 0})
            t["total"] += 1
            if item.status.value == "available":
                t["available"] += 1
            elif item.status.value == "faulty":
                t["faulty"] += 1
        return by_type

    def propose(self, event: dict) -> list[Proposal]:
        """
        Reacts to 'convert_ward_beds' or direct equipment checks —
        confirms critical equipment (e.g. ventilators) is available
        for the ward taking on overflow patients.
        """
        proposals: list[Proposal] = []
        payload = event.get("payload", {})
        target_ward = payload.get("target_id")
        equipment_type = payload.get("equipment_type", "ventilator")

        state = self.observe()
        info = state.get(equipment_type, {"available": 0, "faulty": 0, "total": 0})

        if info["available"] > 0:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="allocate_equipment",
                    target_id=target_ward,
                    reason=f"{info['available']} {equipment_type}(s) available for {target_ward}.",
                    confidence=0.9,
                    cost=info["available"] * 8,
                    urgency=0.5,
                )
            )
        else:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="equipment_shortage",
                    target_id=target_ward,
                    reason=(
                        f"No available {equipment_type}s "
                        f"({info['faulty']} faulty out of {info['total']})."
                    ),
                    confidence=0.9,
                    cost=0,
                    urgency=0.8,
                )
            )

        for p in proposals:
            self.announce(p)

        return proposals