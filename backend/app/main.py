from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.digital_twin import digital_twin, Bed, StaffMember, Equipment, MedicineStock
from app.core.event_bus import event_bus
from app.config import settings

app = FastAPI(
    title="MESH - Multi-Agent Negotiation Engine",
    description="AI-Driven Multi-Agent Decision Intelligence Engine for Hospital Digital Twin",
    version="0.1.0",
)

# Allow frontend (React/etc) to call this API later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "env": settings.env,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
@app.get("/twin/seed")
def seed_twin():
    """Seed the digital twin with sample hospital data — for testing only."""
    digital_twin.add_bed(Bed(bed_id="ICU-1", ward="ICU"))
    digital_twin.add_bed(Bed(bed_id="ICU-2", ward="ICU"))
    digital_twin.add_bed(Bed(bed_id="WARD-C-1", ward="Ward-C"))
    digital_twin.add_staff(StaffMember(staff_id="N1", role="nurse", ward="ICU"))
    digital_twin.add_equipment(Equipment(equipment_id="VENT-1", type="ventilator", ward="ICU"))
    digital_twin.add_medicine(MedicineStock(name="Paracetamol", quantity=100))

    event_bus.publish("twin_seeded", {"message": "sample data loaded"}, source="system")

    return digital_twin.snapshot()