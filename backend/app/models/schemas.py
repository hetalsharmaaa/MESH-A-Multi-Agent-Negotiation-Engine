from pydantic import BaseModel
from enum import Enum
from typing import Optional


class AgentType(str, Enum):
    EMERGENCY = "emergency"
    BED = "bed"
    OT = "ot"
    PHARMACY = "pharmacy"
    STAFF = "staff"
    EQUIPMENT = "equipment"


class Proposal(BaseModel):
    """
    A single agent's proposed action in response to an event.
    This is what agents exchange during negotiation.
    """
    agent: AgentType
    action: str                     # e.g. "open_bed", "reassign_staff"
    target_id: Optional[str] = None  # e.g. bed_id, staff_id
    reason: str                     # human-readable justification
    confidence: float = 1.0         # 0.0 - 1.0
    cost: float = 0.0               # rough resource/financial cost estimate
    urgency: float = 0.5            # 0.0 - 1.0, how time-critical this is


class ScenarioRequest(BaseModel):
    """Input used to trigger a simulated hospital event."""
    scenario_type: str              # e.g. "patient_surge"
    ward: Optional[str] = None
    patient_count: Optional[int] = None
    details: Optional[dict] = None