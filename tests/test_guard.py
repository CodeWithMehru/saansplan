from app.services.guard import (
    extract_numbers,
    format_hour_12h,
    has_past_tense,
    has_raw_hour_zero,
    has_raw_units,
    templated_explanation,
    validate_number_guard,
)


def test_number_guard_accepts_engine_numbers():
    engine = {
        "top_swap": {"percent_reduction": 29},
        "peak_hour": 18,
        "peak_aqi": 312,
    }
    assert validate_number_guard(
        "Peak pollution is at 6 pm with AQI 312. Could reduce about 29% (estimate).", engine
    )


def test_number_guard_rejects_unknown_number():
    engine = {
        "top_swap": {"percent_reduction": 29},
        "peak_hour": 18,
        "peak_aqi": 312,
    }
    assert not validate_number_guard("Could reduce about 45% (estimate)", engine)


def test_number_guard_rejects_past_tense_wording():
    engine = {
        "top_swap": {"percent_reduction": 29},
        "peak_hour": 18,
        "peak_aqi": 312,
    }
    # English past tense claims
    assert not validate_number_guard("Exposure dropped from 100 to 71, a 29% reduction.", engine)
    assert not validate_number_guard("The routine reduced exposure by 29%.", engine)
    assert not validate_number_guard("Total exposure was reduced to 71.", engine)
    assert not validate_number_guard("We lowered exposure by 29%.", engine)
    # Hinglish past tense claims
    assert not validate_number_guard("Routine se exposure 29% kam ho gaya.", engine)
    assert not validate_number_guard("Exposure 29% kam hua.", engine)
    assert not validate_number_guard("Pradushan ghat gaya.", engine)


def test_number_guard_rejects_raw_units():
    engine = {
        "total_before": 47872.35,
        "total_after": 29828.99,
        "top_swap": {"percent_reduction": 29},
        "peak_hour": 18,
        "peak_aqi": 312,
    }
    assert not validate_number_guard(
        "Exposure before 47872 and after 29828, could reduce 29% (estimate).", engine
    )
    assert has_raw_units("Exposure before 47872")


def test_number_guard_rejects_raw_hour_zero():
    engine = {
        "peak_hour": 0,
        "peak_aqi": 206,
        "top_swap": {"percent_reduction": 25},
    }
    assert not validate_number_guard(
        "Peak hour 0 has AQI 206, could reduce about 25% (estimate).", engine
    )
    assert not validate_number_guard(
        "At 0:00 AQI is 206, could reduce about 25% (estimate).", engine
    )
    assert has_raw_hour_zero("Peak hour 0")
    assert has_raw_hour_zero("At 0:00")


def test_format_hour_12h():
    assert format_hour_12h(0, "en") == "12 am"
    assert format_hour_12h(9, "en") == "9 am"
    assert format_hour_12h(12, "en") == "12 pm"
    assert format_hour_12h(18, "en") == "6 pm"

    assert format_hour_12h(0, "hinglish") == "raat 12 baje"
    assert format_hour_12h(3, "hinglish") == "raat 3 baje"
    assert format_hour_12h(8, "hinglish") == "subah 8 baje"
    assert format_hour_12h(12, "hinglish") == "dopahar 12 baje"
    assert format_hour_12h(15, "hinglish") == "dopahar 3 baje"
    assert format_hour_12h(18, "hinglish") == "shaam 6 baje"
    assert format_hour_12h(22, "hinglish") == "raat 10 baje"


def test_extract_numbers():
    assert extract_numbers("AQI 312 and 29%") == {312.0, 29.0}


def test_template_fallback():
    engine = {
        "peak_hour": 18,
        "peak_aqi": 312,
        "top_swap": {"percent_reduction": 29},
        "cleaner_day": {"inhaled_saved_ug": 24.5, "inhaled_saved_range_ug": (18.4, 30.6)},
    }
    text_en = templated_explanation(engine, "en")
    assert "312" in text_en and "29" in text_en
    assert "6 pm" in text_en
    assert "could reduce about" in text_en
    assert not has_past_tense(text_en)

    text_hi = templated_explanation(engine, "hinglish")
    assert "312" in text_hi and "29" in text_hi
    assert "shaam 6 baje" in text_hi
    assert "kam ho sakta hai" in text_hi
    assert not has_past_tense(text_hi)
