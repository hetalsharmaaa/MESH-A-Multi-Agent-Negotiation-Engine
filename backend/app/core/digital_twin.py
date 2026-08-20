from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
from threading import Lock


class BedStatus(Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    OUT_OF_SERVICE = "out_of_service"


class EquipmentStatus(Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    FAULTY = "faulty"
    MAINTENANCE = "maintenance"


@dataclass
class Bed:
    bed_id: str
    ward: str  # e.g. "ICU", "General", "Ward-C"
    status: BedStatus = BedStatus.FREE
    patient_id: str | None = None


@dataclass
class StaffMember:
    staff_id: str
    role: str  # "nurse", "doctor", "technician"
    ward: str
    available: bool = True
    fatigue_score: float = 0.0  # 0 = fresh, 1 = exhausted


@dataclass
class Equipment:
    equipment_id: str
    type: str  # "ventilator", "monitor", "defibrillator"
    ward: str
    status: EquipmentStatus = EquipmentStatus.AVAILABLE


@dataclass
class MedicineStock:
    name: str
    quantity: int
    reorder_threshold: int = 20


class DigitalTwin:
    """
    Live virtual replica of hospital state.
    Agents read from this to make decisions, and write to it
    to simulate the effect of actions (without touching real systems).
    """

    def __init__(self):
        self._lock = Lock()
        self.beds: Dict[str, Bed] = {}
        self.staff: Dict[str, StaffMember] = {}
        self.equipment: Dict[str, Equipment] = {}
        self.pharmacy: Dict[str, MedicineStock] = {}
        self.event_log: List[dict] = []

    # ---------- Bed operations ----------
    def add_bed(self, bed: Bed):
        with self._lock:
            self.beds[bed.bed_id] = bed

    def free_beds(self, ward: str | None = None) -> List[Bed]:
        with self._lock:
            return [
                b for b in self.beds.values()
                if b.status == BedStatus.FREE and (ward is None or b.ward == ward)
            ]

    def occupy_bed(self, bed_id: str, patient_id: str):
        with self._lock:
            bed = self.beds.get(bed_id)
            if bed and bed.status == BedStatus.FREE:
                bed.status = BedStatus.OCCUPIED
                bed.patient_id = patient_id
                return True
            return False

    # ---------- Staff operations ----------
    def add_staff(self, member: StaffMember):
        with self._lock:
            self.staff[member.staff_id] = member

    def available_staff(self, ward: str | None = None, role: str | None = None) -> List[StaffMember]:
        with self._lock:
            return [
                s for s in self.staff.values()
                if s.available
                and (ward is None or s.ward == ward)
                and (role is None or s.role == role)
            ]

    # ---------- Equipment operations ----------
    def add_equipment(self, item: Equipment):
        with self._lock:
            self.equipment[item.equipment_id] = item

    def available_equipment(self, type_: str | None = None, ward: str | None = None) -> List[Equipment]:
        with self._lock:
            return [
                e for e in self.equipment.values()
                if e.status == EquipmentStatus.AVAILABLE
                and (type_ is None or e.type == type_)
                and (ward is None or e.ward == ward)
            ]

    def mark_equipment_faulty(self, equipment_id: str):
        with self._lock:
            item = self.equipment.get(equipment_id)
            if item:
                item.status = EquipmentStatus.FAULTY

    # ---------- Pharmacy operations ----------
    def add_medicine(self, stock: MedicineStock):
        with self._lock:
            self.pharmacy[stock.name] = stock

    def consume_medicine(self, name: str, amount: int) -> bool:
        with self._lock:
            stock = self.pharmacy.get(name)
            if stock and stock.quantity >= amount:
                stock.quantity -= amount
                return True
            return False

    # ---------- Snapshot for agents / API ----------
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "beds": {k: v.__dict__ | {"status": v.status.value} for k, v in self.beds.items()},
                "staff": {k: v.__dict__ for k, v in self.staff.items()},
                "equipment": {k: v.__dict__ | {"status": v.status.value} for k, v in self.equipment.items()},
                "pharmacy": {k: v.__dict__ for k, v in self.pharmacy.items()},
            }


# Single shared instance used across the whole app (simulation state)
digital_twin = DigitalTwin()