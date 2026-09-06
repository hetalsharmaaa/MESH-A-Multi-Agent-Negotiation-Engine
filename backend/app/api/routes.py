from fastapi import APIRouter

from app.config import settings
from app.core.digital_twin import digital_twin, Bed, StaffMember, Equipment, MedicineStock
from app.core.event_bus import event_bus
from app.models.schemas import ScenarioRequest
from app.negotiation.negotiation_engine import NegotiationEngine
from app.negotiation.trust import trust_engine

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
def seed_twin():
    """Seed the digital twin with sample hospital data — for testing only."""
    digital_twin.add_bed(Bed(bed_id="ICU-1", ward="ICU"))
    digital_twin.add_bed(Bed(bed_id="ICU-2", ward="ICU"))
    digital_twin.add_bed(Bed(bed_id="WARD-C-1", ward="Ward-C"))
    digital_twin.add_bed(Bed(bed_id="OT-1", ward="OT"))
    digital_twin.add_staff(StaffMember(staff_id="N1", role="nurse", ward="ICU"))
    digital_twin.add_equipment(Equipment(equipment_id="VENT-1", type="ventilator", ward="ICU"))
    digital_twin.add_medicine(MedicineStock(name="Paracetamol", quantity=100))

    event_bus.publish("twin_seeded", {"message": "sample data loaded"}, source="system")
    return digital_twin.snapshot()


@router.post("/twin/break-equipment/{equipment_id}")
def break_equipment(equipment_id: str):
    digital_twin.mark_equipment_faulty(equipment_id)
    return {"status": "marked faulty", "equipment_id": equipment_id}


# ---------- Negotiation scenarios ----------
@router.post("/negotiate/patient-surge")
def negotiate_patient_surge(request: ScenarioRequest):
    engine = NegotiationEngine(twin=digital_twin, bus=event_bus)
    return engine.run_patient_surge(
        ward=request.ward or "ICU",
        patient_count=request.patient_count or 0,
    )


@router.post("/negotiate/equipment-failure")
def negotiate_equipment_failure(request: ScenarioRequest):
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