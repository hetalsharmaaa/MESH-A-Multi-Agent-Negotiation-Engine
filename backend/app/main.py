from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.agents.bed_agent import BedAgent
from app.agents.staff_agent import StaffAgent
from app.agents.equipment_agent import EquipmentAgent
from app.agents.pharmacy_agent import PharmacyAgent
from app.agents.ot_agent import OTAgent
from app.config import settings
from app.core.digital_twin import digital_twin, Bed, StaffMember, Equipment, MedicineStock
from app.core.event_bus import event_bus
from app.agents.emergency_agent import EmergencyAgent
from app.models.schemas import ScenarioRequest
from app.negotiation.negotiation_engine import NegotiationEngine
from app.negotiation.trust import trust_engine

app = FastAPI(
    title="MESH - Multi-Agent Negotiation Engine",
    description="AI-Driven Multi-Agent Decision Intelligence Engine for Hospital Digital Twin",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.post("/scenario/trigger")
def trigger_scenario(request: ScenarioRequest):
    """
    Trigger a simulated hospital event and see what the Emergency Agent proposes.
    This will later route through negotiation + verification too.
    """
    event = event_bus.publish(
        request.scenario_type,
        payload=request.model_dump(),
        source="simulation",
    )

    emergency_agent = EmergencyAgent(twin=digital_twin, bus=event_bus)
    proposals = emergency_agent.propose(event)

    return {
        "event": event,
        "agent_observation": emergency_agent.observe(),
        "proposals": [p.model_dump() for p in proposals],
    }


@app.get("/agents/observe")
def observe_all_agents():
    """Debug endpoint: see what every agent currently sees in the twin."""
    return {
        "emergency": EmergencyAgent(digital_twin, event_bus).observe(),
        "bed": BedAgent(digital_twin, event_bus).observe(),
        "staff": StaffAgent(digital_twin, event_bus).observe(),
        "equipment": EquipmentAgent(digital_twin, event_bus).observe(),
        "pharmacy": PharmacyAgent(digital_twin, event_bus).observe(),
        "ot": OTAgent(digital_twin, event_bus).observe(),
    }

@app.post("/negotiate/patient-surge")
def negotiate_patient_surge(request: ScenarioRequest):
    """
    Runs the full negotiation flow for a patient surge scenario:
    Emergency -> Bed -> Staff -> Equipment, all proposals scored,
    best plan selected with a full decision trace.
    """
    engine = NegotiationEngine(twin=digital_twin, bus=event_bus)
    result = engine.run_patient_surge(
        ward=request.ward or "ICU",
        patient_count=request.patient_count or 0,
    )
    return result

@app.get("/trust/snapshot")
def get_trust_snapshot():
    """See every agent's current reliability score."""
    return trust_engine.snapshot()