from dataclasses import dataclass, field
from datetime import datetime
from app.models.schemas import AgentType


@dataclass
class TrustRecord:
    agent: AgentType
    reliability_score: float = 0.9  # starts optimistic, adjusts over time
    total_proposals: int = 0
    successful_proposals: int = 0
    failed_proposals: int = 0
    history: list = field(default_factory=list)


class TrustEngine:
    """
    Tracks each agent's reliability over time.

    Example from the PDF:
      Emergency Agent suggests opening ICU Bed 14.
      Equipment Agent later reports Bed 14's ventilator is faulty.
      -> Emergency Agent's reliability drops (bad information).
      -> Equipment Agent's reliability rises (caught the issue).

    This score is then used to weight proposals during negotiation
    (see utility.py's agent_reliability multiplier), so agents that
    are repeatedly wrong get automatically down-weighted.
    """

    def __init__(self):
        self.records: dict[AgentType, TrustRecord] = {
            agent_type: TrustRecord(agent=agent_type) for agent_type in AgentType
        }

    def get_score(self, agent: AgentType) -> float:
        return self.records[agent].reliability_score

    def record_outcome(self, agent: AgentType, success: bool, note: str = ""):
        """
        Call this whenever a proposal's real-world (or simulated) outcome
        becomes known — e.g. the bed the Bed Agent offered actually worked out,
        or the equipment the Equipment Agent flagged as available was faulty.
        """
        record = self.records[agent]
        record.total_proposals += 1

        if success:
            record.successful_proposals += 1
        else:
            record.failed_proposals += 1

        # Exponential moving average: recent outcomes matter more than old ones,
        # but score never swings wildly from a single event.
        alpha = 0.2
        target = 1.0 if success else 0.0
        record.reliability_score = round(
            (1 - alpha) * record.reliability_score + alpha * target, 4
        )

        record.history.append({
            "success": success,
            "note": note,
            "new_score": record.reliability_score,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def snapshot(self) -> dict:
        return {
            agent.value: {
                "reliability_score": r.reliability_score,
                "total_proposals": r.total_proposals,
                "successful_proposals": r.successful_proposals,
                "failed_proposals": r.failed_proposals,
            }
            for agent, r in self.records.items()
        }


# Shared instance — persists reliability scores across negotiations in this run
trust_engine = TrustEngine()