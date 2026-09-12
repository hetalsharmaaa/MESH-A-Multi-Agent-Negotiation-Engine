from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from datetime import datetime

from app.db.database import Base


class BedRecord(Base):
    __tablename__ = "beds"

    bed_id = Column(String(50), primary_key=True)
    ward = Column(String(50), nullable=False)
    status = Column(String(20), default="free")
    patient_id = Column(String(50), nullable=True)


class StaffRecord(Base):
    __tablename__ = "staff"

    staff_id = Column(String(50), primary_key=True)
    role = Column(String(50), nullable=False)
    ward = Column(String(50), nullable=False)
    available = Column(Boolean, default=True)
    fatigue_score = Column(Float, default=0.0)


class EquipmentRecord(Base):
    __tablename__ = "equipment"

    equipment_id = Column(String(50), primary_key=True)
    type = Column(String(50), nullable=False)
    ward = Column(String(50), nullable=False)
    status = Column(String(20), default="available")


class MedicineRecord(Base):
    __tablename__ = "medicine"

    name = Column(String(100), primary_key=True)
    quantity = Column(Integer, default=0)
    reorder_threshold = Column(Integer, default=20)


class NegotiationLog(Base):
    __tablename__ = "negotiation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_type = Column(String(50), nullable=False)
    input_payload = Column(Text)
    winning_action = Column(Text)
    decision_summary = Column(Text)
    verification_passed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrustHistoryRecord(Base):
    __tablename__ = "trust_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent = Column(String(50), nullable=False)
    reliability_score = Column(Float, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)