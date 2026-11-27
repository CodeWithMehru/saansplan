"""Unit tests for app.engine.base_model protocol methods and container semantics."""

from __future__ import annotations

import pytest

from app.engine.exposure_models import HourlyExposureRow
from app.engine.indoor_models import IndoorModulePayload, PurifierCadr
from app.engine.persona_models import PersonaMember


def test_domain_model_mapping_protocol_methods() -> None:
    """Verify FrozenDomainModel implements mapping subscript, get, contains, keys, and iter."""
    row = HourlyExposureRow(
        hour=8,
        pm25=45.0,
        aqi=100,
        exposure=30.0,
        interpolated=False,
        indian_aqi=110,
        indian_category="Moderate",
    )
    with pytest.raises(KeyError):
        _ = row["nonexistent_field"]

    assert row.get("nonexistent_field", "default_val") == "default_val"
    assert row.get("hour") == 8
    assert 123 not in row
    assert "nonexistent_field" not in row
    assert "hour" in row
    assert "hour" in set(row.keys())
    assert "hour" in list(row)
    assert len(row) == 7


def test_nested_domain_model_subscript_and_get() -> None:
    """Verify nested domain model instances convert to dictionaries on mapping access."""
    cadr = PurifierCadr(
        room_area_m2=18.5,
        room_area_sqft=200.0,
        ceiling_height_m=2.7,
        volume_m3=50.0,
        recommended_smoke_cadr_cfm=150,
        recommended_smoke_cadr_m3h=255,
        target_ach=4,
        rule_basis="AHAM 2/3 rule",
    )
    payload = IndoorModulePayload(
        room_checklists={},
        purifier_sizing_default=cadr,
        diy_box_fan_guide={},
    )
    cadr_dict = payload["purifier_sizing_default"]
    assert isinstance(cadr_dict, dict)
    assert cadr_dict["recommended_smoke_cadr_cfm"] == 150

    cadr_get = payload.get("purifier_sizing_default")
    assert isinstance(cadr_get, dict)
    assert cadr_get["recommended_smoke_cadr_cfm"] == 150


def test_persona_member_attribute_access() -> None:
    """Verify PersonaMember dictionary-like subscript and fallback retrieval."""
    m = PersonaMember(name="Test", age_group="adult", sensitive=False)
    assert m["ageGroup"] == "adult"
    assert m["name"] == "Test"
    assert m.get("ageGroup") == "adult"
    assert m.get("missing", "default") == "default"
