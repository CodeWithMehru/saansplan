"""Indoor concentration tests for various heating, cooking, and purifier configurations."""

from __future__ import annotations

import pytest

from app.engine.indoor_penetration import indoor_concentration
from app.schemas.routine import HomeSetup


@pytest.mark.parametrize(
    ("heating", "cooking", "purifier", "expected_min"),
    [
        ("wood_coal", "wood_coal", True, 50.0),
        ("electric", "induction", False, 0.0),
        ("gas", "lpg", True, 0.0),
    ],
)
def test_indoor_source_increments(
    heating: str, cooking: str, purifier: bool, expected_min: float
) -> None:
    """Verify indoor concentration increment bounds under different sources."""
    home = HomeSetup(
        heating=heating, cooking=cooking, windows="mostly_open", purifier=purifier, has_chimney=True
    )
    value = indoor_concentration(100.0, home)
    assert value >= expected_min
