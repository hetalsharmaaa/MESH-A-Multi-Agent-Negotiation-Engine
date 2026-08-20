from app.agents.base_agent import BaseAgent
from app.models.schemas import Proposal, AgentType


class PharmacyAgent(BaseAgent):
    agent_type = AgentType.PHARMACY

    def observe(self) -> dict:
        return {
            name: {"quantity": stock.quantity, "threshold": stock.reorder_threshold}
            for name, stock in self.twin.pharmacy.items()
        }

    def propose(self, event: dict) -> list[Proposal]:
        """
        Reacts to 'medicine_demand' events — checks stock levels
        against the requested amount.
        """
        proposals: list[Proposal] = []
        payload = event.get("payload", {})
        medicine = payload.get("medicine")
        amount_needed = payload.get("amount", 0)

        if not medicine:
            return proposals

        stock = self.twin.pharmacy.get(medicine)

        if stock and stock.quantity >= amount_needed:
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="dispense_medicine",
                    target_id=medicine,
                    reason=f"{stock.quantity} units of {medicine} in stock, {amount_needed} requested.",
                    confidence=0.95,
                    cost=amount_needed * 1,
                    urgency=0.4,
                )
            )
        else:
            available = stock.quantity if stock else 0
            proposals.append(
                Proposal(
                    agent=self.agent_type,
                    action="medicine_shortage",
                    target_id=medicine,
                    reason=f"Only {available} units of {medicine} available, {amount_needed} needed.",
                    confidence=0.9,
                    cost=0,
                    urgency=0.85,
                )
            )

        for p in proposals:
            self.announce(p)

        return proposals