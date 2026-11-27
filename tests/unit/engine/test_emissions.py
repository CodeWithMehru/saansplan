"""Unit tests for emissions and household cost calculator."""

from app.engine.emissions import calculate_emissions_and_cost


def test_emissions_car_commute():
    res = calculate_emissions_and_cost(
        commute_mode="car",
        cooking_fuel="lpg",
        heating_fuel="none",
        budget_filter="any",
    )
    assert res["current"]["weekly_co2e_kg"] > 0
    assert res["current"]["weekly_cost_inr"] > 0
    assert len(res["alternatives"]) > 0

    # Ensure metro or bus offers CO2 savings over private car
    metro_alt = next((a for a in res["alternatives"] if a["mode"] == "metro"), None)
    assert metro_alt is not None
    assert metro_alt["co2e_saved_kg"] > 0
    assert metro_alt["inr_saved_weekly"] > 0


def test_emissions_budget_filtering():
    free_res = calculate_emissions_and_cost(commute_mode="car", budget_filter="free")
    for alt in free_res["alternatives"]:
        assert alt["upfront_cost_inr"] == 0

    low_res = calculate_emissions_and_cost(commute_mode="car", budget_filter="under_500")
    for alt in low_res["alternatives"]:
        assert alt["upfront_cost_inr"] <= 500


def test_emissions_cooking_induction_option() -> None:
    """Verify _build_cooking_options when fuel is already induction."""
    from app.engine import emissions

    opts = emissions._build_cooking_options("induction", 10.0, 5.0, 500.0)
    assert opts == []
