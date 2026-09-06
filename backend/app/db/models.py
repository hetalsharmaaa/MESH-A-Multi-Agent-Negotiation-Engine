from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from datetime import datetime

from app.db.database import Base


class BedRecord(Base):
    __tablename__ = "beds"

    bed_id = Column(String, primary_key=True)
    ward = Column(String, nullable=False)
    status = Column(String, default="free")
    patient_id = Column(String, nullable=True)


class StaffRecord(Base):
    __tablename__ = "staff"

    staff_id = Column(String, primary_key=True)
    role = Column(String, nullable=False)
    ward = Column(String, nullable=False)
    available = Column(Boolean, default=True)
    fatigue_score = Column(Float, default=0.0)


class EquipmentRecord(Base):
    __tablename__ = "equipment"

    equipment_id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    ward = Column(String, nullable=False)
    status = Column(String, default="available")


class MedicineRecord(Base):
    __tablename__ = "medicine"

    name = Column(String, primary_key=True)
    quantity = Column(Integer, default=0)
    reorder_threshold = Column(Integer, default=20)


class NegotiationLog(Base):
    """
    Every negotiation run gets stored here — this is what your evaluation
    section (Scenario A/B/C waiting-time comparisons) will query from.
    """
    __tablename__ = "negotiation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_type = Column(String, nullable=False)
    input_payload = Column(Text)          # JSON string of the request
    winning_action = Column(Text)         # JSON string of winning proposal
    decision_summary = Column(Text)       # JSON string of the readable trace
    verification_passed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrustHistoryRecord(Base):
    """Snapshot of trust scores after each negotiation, for tracking drift over time."""
    __tablename__ = "trust_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent = Column(String, nullable=False)
    reliability_score = Column(Float, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)