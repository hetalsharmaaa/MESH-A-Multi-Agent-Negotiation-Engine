from collections import defaultdict
from typing import Callable, List
from datetime import datetime


class EventBus:
    """
    Simple synchronous pub/sub bus.
    Agents subscribe to event types (e.g. 'icu_capacity_critical')
    and publish events for others to react to.
    """

    def __init__(self):
        self._subscribers: dict[str, List[Callable]] = defaultdict(list)
        self.history: List[dict] = []

    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, payload: dict, source: str = "system"):
        event = {
            "type": event_type,
            "source": source,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.history.append(event)

        for handler in self._subscribers.get(event_type, []):
            handler(event)

        return event


# Shared bus instance
event_bus = EventBus()