"""Unit tests for indoor module: purifier sizing, DIY fan guide, and room checklists."""

from app.engine.indoor_guidance import (
    calculate_purifier_cadr,
    get_diy_box_fan_guide,
    get_room_checklists,
)


def test_purifier_cadr_sizing_rule():
    # 15 sqm room with 2.4m height = 36 m3
    res = calculate_purifier_cadr(area_sq_meters=15.0, ceiling_height_meters=2.4)
    assert res["volume_m3"] == 36.0
    # 5 ACH = 180 m3/h
    assert res["recommended_smoke_cadr_m3h"] == 180
    assert res["recommended_smoke_cadr_cfm"] > 100
    assert res["target_ach"] == 5


def test_diy_box_fan_guide():
    guide = get_diy_box_fan_guide()
    assert "Corsi-Rosenthal" in guide["title"]
    assert len(guide["materials"]) >= 4
    assert len(guide["assembly_steps"]) >= 4
    assert len(guide["safety_warnings"]) >= 4
    # Must explicitly warn against unattended operation
    assert any("unattended" in w.lower() for w in guide["safety_warnings"])


def test_room_checklists():
    lists = get_room_checklists()
    assert "kitchen" in lists
    assert "bedroom" in lists
    assert "living_room" in lists
    assert "children_room" in lists

    # Kitchen must mention exhaust ventilation
    assert any(
        "exhaust" in item["action"].lower() or "ventilate" in item["action"].lower()
        for item in lists["kitchen"]
    )
    # Bedroom must mention wet mopping and zero incense
    assert any("mopping" in item["action"].lower() for item in lists["bedroom"])
    assert any("incense" in item["action"].lower() for item in lists["bedroom"])
