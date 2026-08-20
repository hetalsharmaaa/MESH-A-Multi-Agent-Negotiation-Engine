from abc import ABC, abstractmethod
from app.core.digital_twin import DigitalTwin
from app.core.event_bus import EventBus
from app.models.schemas import Proposal, AgentType


class BaseAgent(ABC):
    """
    Base class every department agent inherits from.
    Each agent:
      - observes the Digital Twin (its domain's live state)
      - listens for events on the Event Bus
      - proposes actions when asked to respond to a scenario
    """

    agent_type: AgentType

    def __init__(self, twin: DigitalTwin, bus: EventBus):
        self.twin = twin
        self.bus = bus
        self.reliability_score: float = 0.9  # starting trust score, used later in Step 6

    @abstractmethod
    def observe(self) -> dict:
        """Return this agent's current view of its domain (subset of twin state)."""
        raise NotImplementedError

    @abstractmethod
    def propose(self, event: dict) -> list[Proposal]:
        """
        Given an event (e.g. a patient surge), return one or more
        candidate actions this agent could take.
        """
        raise NotImplementedError

    def announce(self, proposal: Proposal):
        """Publish this agent's proposal onto the event bus for others to see."""
        self.bus.publish(
            "proposal_made",
            payload=proposal.model_dump(),
            source=self.agent_type.value,
        )