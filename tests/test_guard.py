from app.services.guard import (
    extract_numbers,
    templated_explanation,
    validate_number_guard,
)


def test_number_guard_accepts_engine_numbers():
    engine = {
        "total_before": 100,
        "total_after": 58,
        "top_swap": {"percent_reduction": 29},
        "peak_hour": 18,
        "peak_aqi": 312,
    }
    assert validate_number_guard("29% kam ho sakta hai at 18:00", engine)


def test_number_guard_rejects_unknown_number():
    engine = {
        "total_before": 100,
        "top_swap": {"percent_reduction": 29},
        "peak_hour": 18,
        "peak_aqi": 312,
    }
    assert not validate_number_guard("45% kam hoga", engine)


def test_extract_numbers():
    assert extract_numbers("AQI 312 and 29%") == {312.0, 29.0}


def test_template_fallback():
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}}
    text = templated_explanation(engine)
    assert "312" in text and "29" in text
