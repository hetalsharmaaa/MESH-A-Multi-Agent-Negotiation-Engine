from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


# ---------- Enums (keep state values consistent everywhere) ----------
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"


class CasePriority(str, enum.Enum):
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ConflictStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class NegotiationStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    UNRESOLVED = "unresolved"
    ESCALATED = "escalated"


class MessageType(str, enum.Enum):
    REQUEST = "request"
    RESPONSE = "response"
    PROPOSAL = "proposal"
    COUNTERPROPOSAL = "counterproposal"
    CONSTRAINT_CHECK = "constraint_check"
    CONSENSUS = "consensus"


class ProposalStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class DecisionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"


# ---------- Users & Auth ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MANAGER)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- Agent registry (metadata, not logic) ----------
class AgentRecord(Base):
    """
    Static registry of the 7 department agents — used for the /agents
    page in the UI. Agent BEHAVIOR still lives in Python classes;
    this table just tracks identity/status/objective for display.
    """
    __tablename__ = "agents"

    agent_id = Column(String(50), primary_key=True)   # e.g. "emergency"
    agent_name = Column(String(100), nullable=False)   # e.g. "Emergency Agent"
    agent_type = Column(String(50), nullable=False)    # e.g. "emergency"
    status = Column(String(20), default="active")
    objective = Column(Text)


# ---------- Resource tables ----------
class BedRecord(Base):
    __tablename__ = "beds"

    bed_id = Column(String(50), primary_key=True)
    bed_code = Column(String(50), nullable=False)
    ward = Column(String(50), nullable=False)
    bed_type = Column(String(50), default="general")   # e.g. "ICU", "general"
    status = Column(String(20), default="free")
    patient_case = Column(String(50), ForeignKey("cases.case_number"), nullable=True)


class OperatingTheatreRecord(Base):
    __tablename__ = "operating_theatres"

    ot_id = Column(String(50), primary_key=True)
    ot_code = Column(String(50), nullable=False)
    status = Column(String(20), default="available")   # available, occupied, maintenance
    current_case = Column(String(50), ForeignKey("cases.case_number"), nullable=True)
    available_from = Column(DateTime, nullable=True)


class StaffRecord(Base):
    __tablename__ = "staff"

    staff_id = Column(String(50), primary_key=True)
    staff_code = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)          # surgeon, nurse, anaesthetist
    department = Column(String(50), nullable=False)
    ward = Column(String(50), nullable=True)
    status = Column(String(20), default="available")   # available, busy
    available_from = Column(DateTime, nullable=True)
    fatigue_score = Column(Float, default=0.0)


class LabResourceRecord(Base):
    __tablename__ = "lab_resources"

    lab_id = Column(String(50), primary_key=True)
    resource_code = Column(String(50), nullable=False)
    status = Column(String(20), default="available")
    capacity = Column(Integer, default=1)
    available_from = Column(DateTime, nullable=True)


class RadiologyResourceRecord(Base):
    __tablename__ = "radiology_resources"

    radiology_id = Column(String(50), primary_key=True)
    resource_code = Column(String(50), nullable=False)
    status = Column(String(20), default="available")
    available_from = Column(DateTime, nullable=True)


class MedicineRecord(Base):
    __tablename__ = "medicine"

    name = Column(String(100), primary_key=True)
    quantity = Column(Integer, default=0)
    reorder_threshold = Column(Integer, default=20)

class EquipmentRecord(Base):
    __tablename__ = "equipment"

    equipment_id = Column(String(50), primary_key=True)
    type = Column(String(50), nullable=False)
    ward = Column(String(50), nullable=False)
    status = Column(String(20), default="available")
    
# ---------- Core operational chain: Case -> Conflict -> Negotiation -> Decision ----------
class Case(Base):
    """
    A patient case with an operational requirement (e.g. P205 needing surgery).
    This is the starting point of the whole MESH pipeline.
    """
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(50), unique=True, nullable=False)  # e.g. "P205"
    priority = Column(Enum(CasePriority), default=CasePriority.NORMAL)
    department = Column(String(50), nullable=False)
    status = Column(Enum(CaseStatus), default=CaseStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

    conflicts = relationship("Conflict", back_populates="case")


class Conflict(Base):
    """
    A detected resource conflict tied to a case (e.g. C-001: OT-02 is
    occupied but Case P205 needs it urgently).
    """
    __tablename__ = "conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conflict_code = Column(String(50), unique=True, nullable=False)  # e.g. "C-001"
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    description = Column(Text, nullable=False)
    involved_agents = Column(Text)   # JSON string list, e.g. '["emergency","ot","staff","bed"]'
    status = Column(Enum(ConflictStatus), default=ConflictStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    case = relationship("Case", back_populates="conflicts")
    negotiations = relationship("Negotiation", back_populates="conflict")


class Negotiation(Base):
    """
    A negotiation session between agents to resolve one Conflict.
    Holds many Messages and Proposals, and produces one Decision.
    """
    __tablename__ = "negotiations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conflict_id = Column(Integer, ForeignKey("conflicts.id"), nullable=False)
    status = Column(Enum(NegotiationStatus), default=NegotiationStatus.IN_PROGRESS)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    conflict = relationship("Conflict", back_populates="negotiations")
    messages = relationship("Message", back_populates="negotiation")
    proposals = relationship("Proposal", back_populates="negotiation")
    decision = relationship("Decision", back_populates="negotiation", uselist=False)


class Message(Base):
    """
    A single communication turn in a negotiation — this is what powers
    the "Live Negotiation" page's chat-like feed.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    negotiation_id = Column(Integer, ForeignKey("negotiations.id"), nullable=False)
    agent = Column(String(50), nullable=False)          # e.g. "emergency", "ot"
    message_type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False)               # human-readable text
    created_at = Column(DateTime, default=datetime.utcnow)

    negotiation = relationship("Negotiation", back_populates="messages")


class Proposal(Base):
    """
    A structured proposal (or counterproposal) made during negotiation.
    parent_proposal_id links a counterproposal back to what it's countering.
    """
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    negotiation_id = Column(Integer, ForeignKey("negotiations.id"), nullable=False)
    agent = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    target_id = Column(String(50), nullable=True)
    reason = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    cost = Column(Float, default=0.0)
    urgency = Column(Float, default=0.5)
    score = Column(Float, nullable=True)
    is_counterproposal = Column(Boolean, default=False)
    parent_proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)
    status = Column(Enum(ProposalStatus), default=ProposalStatus.PROPOSED)
    created_at = Column(DateTime, default=datetime.utcnow)

    negotiation = relationship("Negotiation", back_populates="proposals")


class Decision(Base):
    """
    The final recommendation from a negotiation, awaiting human approval.
    This is what the "Decision & Approval" page reads and writes.
    """
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    negotiation_id = Column(Integer, ForeignKey("negotiations.id"), unique=True, nullable=False)
    recommendation = Column(Text, nullable=False)
    decision_factors = Column(Text)      # JSON string, e.g. '["Emergency priority","OT availability"]'
    confidence_percent = Column(Float, default=0.0)
    status = Column(Enum(DecisionStatus), default=DecisionStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    negotiation = relationship("Negotiation", back_populates="decision")


class AuditLog(Base):
    """
    Human-readable trail of every significant action — matches masterprompt
    section 26's example log format exactly.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(100), nullable=False)     # e.g. "System" or a user's name
    action = Column(Text, nullable=False)            # e.g. "Decision D-001 approved by Hospital Manager"
    entity_type = Column(String(50), nullable=True)  # e.g. "conflict", "decision"
    entity_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)