"""Golden engine fixture tests."""

import json
from pathlib import Path

from app.engine.exposure import simulate_exposure
from app.schemas.family import FamilyMember
from app.schemas.routine import Activity, HomeSetup, Routine


def test_golden_moderate_fixture_is_deterministic() -> None:
    fixture = json.loads(Path("tests/fixtures/golden.json").read_text(encoding="utf-8"))
    member = FamilyMember(age_group="adult")
    routine = Routine(
        activities=[
            Activity(
                label="Walk",
                start_hour=18,
                duration_min=40,
                place="outdoor",
                mode="walk",
                intensity="moderate",
                member_refs=[0],
            )
        ],
        home=HomeSetup(
            heating="none",
            cooking="lpg",
            windows="mostly_closed",
            purifier=False,
            has_chimney=False,
        ),
    )
    first = simulate_exposure(fixture["pm25"], fixture["aqi"], [member], routine)
    second = simulate_exposure(fixture["pm25"], fixture["aqi"], [member], routine)
    assert first == second
    assert first["hourly"][18]["pm25"] == 100.0
