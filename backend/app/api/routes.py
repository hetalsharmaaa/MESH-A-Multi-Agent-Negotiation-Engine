from fastapi import APIRouter

from app.config import settings
from app.core.digital_twin import digital_twin, Bed, StaffMember, Equipment, MedicineStock
from app.core.event_bus import event_bus
from app.models.schemas import ScenarioRequest
from app.negotiation.negotiation_engine import NegotiationEngine
from app.negotiation.trust import trust_engine
from fastapi import Depends
from sqlalchemy.orm import Session
import json

from app.db.database import get_db
from app.db.models import BedRecord, StaffRecord, EquipmentRecord, MedicineRecord, NegotiationLog, TrustHistoryRecord
from app.core.digital_twin import BedStatus, EquipmentStatus

router = APIRouter()


# ---------- System ----------
@router.get("/")
def root():
    return {"app": settings.app_name, "status": "running", "env": settings.env}


@router.get("/health")
def health_check():
    return {"status": "ok"}


# ---------- Digital Twin ----------
@router.get("/twin/seed")
def seed_twin(db: Session = Depends(get_db)):
    """Seed the digital twin (in-memory) AND persist it to the database."""
    digital_twin.add_bed(Bed(bed_id="ICU-1", ward="ICU"))
    digital_twin.add_bed(Bed(bed_id="ICU-2", ward="ICU"))
    digital_twin.add_bed(Bed(bed_id="WARD-C-1", ward="Ward-C"))
    digital_twin.add_bed(Bed(bed_id="OT-1", ward="OT"))
    digital_twin.add_staff(StaffMember(staff_id="N1", role="nurse", ward="ICU"))
    digital_twin.add_equipment(Equipment(equipment_id="VENT-1", type="ventilator", ward="ICU"))
    digital_twin.add_medicine(MedicineStock(name="Paracetamol", quantity=100))

    # Persist to DB (clear old rows first so re-seeding doesn't duplicate)
    db.query(BedRecord).delete()
    db.query(StaffRecord).delete()
    db.query(EquipmentRecord).delete()
    db.query(MedicineRecord).delete()

    for bed in digital_twin.beds.values():
        db.add(BedRecord(bed_id=bed.bed_id, ward=bed.ward, status=bed.status.value, patient_id=bed.patient_id))
    for staff in digital_twin.staff.values():
        db.add(StaffRecord(staff_id=staff.staff_id, role=staff.role, ward=staff.ward,
                            available=staff.available, fatigue_score=staff.fatigue_score))
    for eq in digital_twin.equipment.values():
        db.add(EquipmentRecord(equipment_id=eq.equipment_id, type=eq.type, ward=eq.ward, status=eq.status.value))
    for med in digital_twin.pharmacy.values():
        db.add(MedicineRecord(name=med.name, quantity=med.quantity, reorder_threshold=med.reorder_threshold))

    db.commit()
    event_bus.publish("twin_seeded", {"message": "sample data loaded"}, source="system")
    return digital_twin.snapshot()


@router.get("/twin/load")
def load_twin_from_db(db: Session = Depends(get_db)):
    """
    Restores the in-memory Digital Twin from the database.
    Call this after a server restart instead of re-seeding, to
    resume from whatever state was last saved.
    """
    digital_twin.beds.clear()
    digital_twin.staff.clear()
    digital_twin.equipment.clear()
    digital_twin.pharmacy.clear()

    for row in db.query(BedRecord).all():
        digital_twin.add_bed(Bed(bed_id=row.bed_id, ward=row.ward, status=BedStatus(row.status), patient_id=row.patient_id))
    for row in db.query(StaffRecord).all():
        digital_twin.add_staff(StaffMember(staff_id=row.staff_id, role=row.role, ward=row.ward,
                                            available=row.available, fatigue_score=row.fatigue_score))
    for row in db.query(EquipmentRecord).all():
        digital_twin.add_equipment(Equipment(equipment_id=row.equipment_id, type=row.type, ward=row.ward,
                                              status=EquipmentStatus(row.status)))
    for row in db.query(MedicineRecord).all():
        digital_twin.add_medicine(MedicineStock(name=row.name, quantity=row.quantity, reorder_threshold=row.reorder_threshold))

    return digital_twin.snapshot()


@router.post("/twin/break-equipment/{equipment_id}")
def break_equipment(equipment_id: str):
    digital_twin.mark_equipment_faulty(equipment_id)
    return {"status": "marked faulty", "equipment_id": equipment_id}


# ---------- Negotiation scenarios ----------
@router.post("/negotiate/patient-surge")
def negotiate_patient_surge(request: ScenarioRequest, db: Session = Depends(get_db)):
    engine = NegotiationEngine(twin=digital_twin, bus=event_bus)
    result = engine.run_patient_surge(
        ward=request.ward or "ICU",
        patient_count=request.patient_count or 0,
    )

    db.add(NegotiationLog(
        scenario_type="patient_surge",
        input_payload=json.dumps(request.model_dump()),
        winning_action=json.dumps(result.get("winning_action")),
        decision_summary=json.dumps(result.get("decision_summary")),
        verification_passed=not result.get("verification_failed_completely", False),
    ))
    for agent, data in result.get("trust_snapshot", {}).items():
        db.add(TrustHistoryRecord(agent=agent, reliability_score=data["reliability_score"]))
    db.commit()

    return result

@router.post("/negotiate/equipment-failure")
def negotiate_equipment_failure(request: ScenarioRequest, db: Session = Depends(get_db)):
    engine = NegotiationEngine(twin=digital_twin, bus=event_bus)
    equipment_type = (request.details or {}).get("equipment_type", "ventilator")
    return engine.run_equipment_failure(
        ward=request.ward or "ICU",
        equipment_type=equipment_type,
    )


@router.post("/negotiate/medicine-shortage")
def negotiate_medicine_shortage(request: ScenarioRequest):
    engine = NegotiationEngine(twin=digital_twin, bus=event_bus)
    details = request.details or {}
    return engine.run_medicine_shortage(
        medicine=details.get("medicine", "Paracetamol"),
        amount_needed=details.get("amount", 0),
    )


@router.post("/negotiate/ot-overload")
def negotiate_ot_overload(request: ScenarioRequest):
    engine = NegotiationEngine(twin=digital_twin, bus=event_bus)
    details = request.details or {}
    return engine.run_ot_overload(surgery_count=details.get("surgery_count", 0))


# ---------- Trust ----------
@router.get("/trust/snapshot")
def get_trust_snapshot():
    return trust_engine.snapshot()

@router.get("/history/negotiations")
def get_negotiation_history(db: Session = Depends(get_db)):
    """Returns all past negotiation results — useful for your evaluation charts."""
    logs = db.query(NegotiationLog).order_by(NegotiationLog.created_at.desc()).all()
    return [
        {
            "id": log.id,
            "scenario_type": log.scenario_type,
            "winning_action": json.loads(log.winning_action) if log.winning_action else None,
            "verification_passed": log.verification_passed,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]