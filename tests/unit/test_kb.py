"""Knowledge base retrieval and threshold unit tests."""

from app.services.kb import KnowledgeBase


def test_kb_retrieve_purifier_sizing() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("What air purifier CADR for bedroom?")
    assert len(res) > 0
    assert res[0]["id"] == "purifier-sizing"


def test_kb_retrieve_mask() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("How to wear N95 mask outdoors?")
    assert len(res) > 0
    assert any(e["id"] == "mask-fit" for e in res)


def test_kb_retrieve_box_fan() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("How to make a DIY box fan filter?")
    assert len(res) > 0
    assert any(e["id"] == "box-fan-safety" for e in res)


def test_kb_retrieve_wet_mop() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("Should I sweep or wet mop dust?")
    assert len(res) > 0
    assert any(e["id"] == "wet-mop" for e in res)


def test_kb_retrieve_cooking() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("Cooking smoke from chulha LPG kitchen")
    assert len(res) > 0
    assert any(e["id"] in ("cleaner-cooking", "cooking-vent") for e in res)


def test_kb_retrieve_transit() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("Is taking metro or electric bus better for commute emissions?")
    assert len(res) > 0
    assert any(e["id"] == "transit-emissions" for e in res)


def test_kb_retrieve_incense() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("Does agarbatti dhoop incense cause indoor smoke?")
    assert len(res) > 0
    assert any(e["id"] == "incense-avoidance" for e in res)


def test_kb_retrieve_no_match() -> None:
    kb = KnowledgeBase()
    res = kb.retrieve("xyz completely unrelated query 1234567")
    assert res == []

