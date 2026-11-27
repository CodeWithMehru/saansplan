"""Persona presets for urban Indian households navigating winter smog."""

from __future__ import annotations

from app.engine.domain_models import PersonaMember, PersonaPreset


def get_personas() -> dict[str, PersonaPreset]:
    """Return 4 realistic lifestyle presets for quick form prefilling."""
    return {
        "working_parents": PersonaPreset(
            id="working_parents",
            name="Working Parents & School Children",
            description="Busy family with morning school drop-off and daily office transit.",
            members=[
                PersonaMember(name="Parent 1", age_group="adult", sensitive=False),
                PersonaMember(name="Child", age_group="child", sensitive=True),
            ],
            routine_text=(
                "Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, "
                "shaam 6 baje park walk."
            ),
            commute="metro",
            outdoor_minutes=60,
            cooking="lpg",
            heating="none",
            windows="mostly_closed",
            purifier=False,
            budget="under_5000",
        ),
        "elderly_home": PersonaPreset(
            id="elderly_home",
            name="Senior Citizen / Elderly at Home",
            description="Retired grandparents with respiratory sensitivity and high indoor hours.",
            members=[
                PersonaMember(name="Grandparent", age_group="elderly", sensitive=True),
                PersonaMember(name="Caregiver", age_group="adult", sensitive=False),
            ],
            routine_text=(
                "Dada ji din bhar ghar pe rehte hain, subah balcony me baithte hain, "
                "thand me heating zaroori hai."
            ),
            commute="none",
            outdoor_minutes=30,
            cooking="induction",
            heating="electric",
            windows="mostly_closed",
            purifier=True,
            budget="under_5000",
        ),
        "student_hostel": PersonaPreset(
            id="student_hostel",
            name="Student / Hostel Resident",
            description="University student walking between hostel, library, and campus mess.",
            members=[
                PersonaMember(name="Student", age_group="adult", sensitive=False),
            ],
            routine_text=(
                "College campus me subah 8 baje class ke liye walk karta hoon, "
                "shaam ko library se hostel."
            ),
            commute="walk",
            outdoor_minutes=60,
            cooking="induction",
            heating="none",
            windows="mostly_closed",
            purifier=False,
            budget="under_500",
        ),
        "outdoor_worker": PersonaPreset(
            id="outdoor_worker",
            name="Outdoor Worker / Delivery Rider",
            description="Gig delivery partner or outdoor worker with 6+ hours street exposure.",
            members=[
                PersonaMember(name="Rider", age_group="adult", sensitive=False),
            ],
            routine_text=(
                "Subah 10 baje se shaam 6 baje tak bike pe deliveries karta hoon busy roads pe."
            ),
            commute="bike",
            outdoor_minutes=120,
            cooking="lpg",
            heating="none",
            windows="mostly_closed",
            purifier=False,
            budget="under_500",
        ),
    }
