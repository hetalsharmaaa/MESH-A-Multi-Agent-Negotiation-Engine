from app.core.digital_twin import DigitalTwin
from app.models.schemas import Proposal


class ConstraintViolation:
    def __init__(self, rule: str, detail: str):
        self.rule = rule
        self.detail = detail

    def to_dict(self) -> dict:
        return {"rule": self.rule, "detail": self.detail}


class ConstraintChecker:
    """
    Validates a winning proposal against real operational constraints
    before it's shown to the administrator. This is what turns a
    "suggestion" into something actually safe to act on.

    Each check function returns None if fine, or a ConstraintViolation if not.
    """

    def __init__(self, twin: DigitalTwin):
        self.twin = twin

    def check(self, proposal: Proposal) -> list[ConstraintViolation]:
        violations: list[ConstraintViolation] = []

        checks = [
            self._check_ward_exists,
            self._check_not_negative_cost,
            self._check_capacity_still_valid,
            self._check_equipment_not_faulty,
        ]

        for check_fn in checks:
            result = check_fn(proposal)
            if result:
                violations.append(result)

        return violations

    def _check_ward_exists(self, proposal: Proposal) -> ConstraintViolation | None:
        if proposal.action in {"convert_ward_beds", "admit_to_icu", "schedule_surgery"}:
            wards = {b.ward for b in self.twin.beds.values()}
            if proposal.target_id and proposal.target_id not in wards and proposal.target_id != "OT":
                return ConstraintViolation(
                    rule="ward_must_exist",
                    detail=f"Target ward '{proposal.target_id}' does not exist in the Digital Twin.",
                )
        return None

    def _check_not_negative_cost(self, proposal: Proposal) -> ConstraintViolation | None:
        if proposal.cost < 0:
            return ConstraintViolation(
                rule="cost_must_be_non_negative",
                detail=f"Proposal cost is negative ({proposal.cost}), which is invalid.",
            )
        return None

    def _check_capacity_still_valid(self, proposal: Proposal) -> ConstraintViolation | None:
        """
        Re-checks live twin state at verification time — protects against
        race conditions where beds/capacity changed between proposal and verification.
        """
        if proposal.action == "convert_ward_beds" and proposal.target_id:
            free_beds = [
                b for b in self.twin.beds.values()
                if b.ward == proposal.target_id and b.status.value == "free"
            ]
            if not free_beds:
                return ConstraintViolation(
                    rule="capacity_must_still_be_available",
                    detail=f"No free beds remain in {proposal.target_id} at verification time.",
                )
        return None

    def _check_equipment_not_faulty(self, proposal: Proposal) -> ConstraintViolation | None:
        if proposal.action == "allocate_equipment" and proposal.target_id:
            faulty = [
                e for e in self.twin.equipment.values()
                if e.ward == proposal.target_id and e.status.value == "faulty"
            ]
            available = [
                e for e in self.twin.equipment.values()
                if e.ward == proposal.target_id and e.status.value == "available"
            ]
            if faulty and not available:
                return ConstraintViolation(
                    rule="equipment_must_not_be_faulty",
                    detail=f"All equipment in {proposal.target_id} is currently faulty.",
                )
        return None