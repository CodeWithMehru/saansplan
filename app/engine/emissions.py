"""Emissions and household cost calculator."""

from __future__ import annotations

from app.engine.domain_models import EmissionsCurrent, EmissionsOption, EmissionsResult

EMISSION_FACTORS_TRANSPORT = {
    "car": 140.0,
    "bike": 40.0,
    "carpool": 70.0,
    "bus": 20.0,
    "metro": 15.0,
    "walk": 0.0,
    "cycle": 0.0,
    "none": 0.0,
}

EMISSION_FACTORS_COOKING = {
    "wood_coal": {"co2e_kg": 18.0, "pm_g": 350.0, "cost_inr": 250},
    "lpg": {"co2e_kg": 7.5, "pm_g": 1.5, "cost_inr": 220},
    "induction": {"co2e_kg": 5.8, "pm_g": 0.0, "cost_inr": 180},
    "other": {"co2e_kg": 12.0, "pm_g": 150.0, "cost_inr": 200},
}

EMISSION_FACTORS_HEATING = {
    "wood_coal": {"co2e_kg": 25.0, "pm_g": 500.0, "cost_inr": 350},
    "gas": {"co2e_kg": 14.0, "pm_g": 5.0, "cost_inr": 300},
    "electric": {"co2e_kg": 10.5, "pm_g": 0.0, "cost_inr": 450},
    "insulation": {"co2e_kg": 0.0, "pm_g": 0.0, "cost_inr": 50},
    "none": {"co2e_kg": 0.0, "pm_g": 0.0, "cost_inr": 0},
    "other": {"co2e_kg": 15.0, "pm_g": 100.0, "cost_inr": 250},
}

WEEKLY_COMMUTE_KM = 75.0

COST_PER_KM = {
    "car": 6.7,
    "bike": 2.2,
    "carpool": 3.4,
    "bus": 1.2,
    "metro": 2.0,
    "walk": 0.0,
    "cycle": 0.2,
    "none": 0.0,
}

UPFRONT_THRESHOLD_FREE = 0
UPFRONT_THRESHOLD_LOW = 500
UPFRONT_THRESHOLD_MID = 5000


def _build_commute_options(
    commute_mode: str, current_commute_co2: float, current_commute_cost: float
) -> list[EmissionsOption]:
    """Build list of commute alternatives with carbon and cost savings."""
    options = []
    candidates = [
        ("metro", "Electric Metro Rail", 0),
        ("bus", "Public Bus Transit", 0),
        ("carpool", "Ride-sharing / Carpool", 0),
        ("cycle", "Bicycle Commute", 3500),
        ("walk", "Walking (clean hours)", 0),
    ]
    for mode, label, upfront_inr in candidates:
        if mode != commute_mode:
            c_co2 = (EMISSION_FACTORS_TRANSPORT[mode] * WEEKLY_COMMUTE_KM) / 1000.0
            c_cost = COST_PER_KM[mode] * WEEKLY_COMMUTE_KM
            co2_saving = round(max(0.0, current_commute_co2 - c_co2), 1)
            cost_saving = round(current_commute_cost - c_cost)
            tier = "free" if upfront_inr == 0 else "under_5000"
            options.append(
                EmissionsOption(
                    mode=mode,
                    title=label,
                    category="commute",
                    weekly_co2e_kg=round(c_co2, 1),
                    weekly_cost_inr=round(c_cost),
                    co2e_saved_kg=co2_saving,
                    inr_saved_weekly=cost_saving,
                    upfront_cost_inr=upfront_inr,
                    is_free=upfront_inr == 0 and cost_saving >= 0,
                    budget_tier=tier,
                    pm_saved_g=None,
                )
            )
    return options


def _build_cooking_options(
    cooking_fuel: str, current_co2: float, current_pm: float, current_cost: float
) -> list[EmissionsOption]:
    """Build alternative options for residential cooking."""
    options = []
    if cooking_fuel != "induction":
        ind_data = EMISSION_FACTORS_COOKING["induction"]
        co2_saved = round(max(0.0, current_co2 - ind_data["co2e_kg"]), 1)
        pm_saved = round(max(0.0, current_pm - ind_data["pm_g"]), 1)
        options.append(
            EmissionsOption(
                mode="induction",
                title="Electric Induction Cooktop",
                category="cooking",
                weekly_co2e_kg=ind_data["co2e_kg"],
                weekly_cost_inr=int(ind_data["cost_inr"]),
                co2e_saved_kg=co2_saved,
                pm_saved_g=pm_saved,
                inr_saved_weekly=round(current_cost - ind_data["cost_inr"]),
                upfront_cost_inr=2200,
                budget_tier="under_5000",
            )
        )
    return options


def _build_heating_options(
    heating_fuel: str, current_co2: float, current_pm: float, current_cost: float
) -> list[EmissionsOption]:
    """Build alternative options for residential space heating."""
    options = []
    if heating_fuel in ("wood_coal", "other"):
        options.append(
            EmissionsOption(
                mode="insulation",
                title="Thermal Layering & Draft Stoppers",
                category="heating",
                weekly_co2e_kg=0.0,
                weekly_cost_inr=0,
                co2e_saved_kg=round(current_co2, 1),
                pm_saved_g=round(current_pm, 1),
                inr_saved_weekly=round(current_cost),
                upfront_cost_inr=350,
                budget_tier="under_500",
            )
        )
    return options


def _filter_by_budget(
    all_options: list[EmissionsOption], budget_filter: str
) -> list[EmissionsOption]:
    """Filter sustainable alternative options by user upfront budget tier."""
    thresholds = {
        "free": 0,
        "under_500": UPFRONT_THRESHOLD_LOW,
        "under_5000": UPFRONT_THRESHOLD_MID,
    }
    max_cost = thresholds.get(budget_filter)
    if max_cost is None:
        return all_options
    return [opt for opt in all_options if opt.upfront_cost_inr <= max_cost]


def calculate_emissions_and_cost(
    commute_mode: str = "car",
    cooking_fuel: str = "lpg",
    heating_fuel: str = "none",
    budget_filter: str = "any",
) -> EmissionsResult:
    """Calculate current and alternative weekly carbon emissions, particles, and cost."""
    commute_factor = EMISSION_FACTORS_TRANSPORT.get(commute_mode, 0.0)
    current_commute_co2 = (commute_factor * WEEKLY_COMMUTE_KM) / 1000.0
    current_commute_cost = COST_PER_KM.get(commute_mode, 0.0) * WEEKLY_COMMUTE_KM

    cooking_data = EMISSION_FACTORS_COOKING.get(cooking_fuel, EMISSION_FACTORS_COOKING["lpg"])
    current_cooking_co2 = cooking_data["co2e_kg"]
    current_cooking_pm = cooking_data["pm_g"]
    current_cooking_cost = cooking_data["cost_inr"]

    heating_data = EMISSION_FACTORS_HEATING.get(heating_fuel, EMISSION_FACTORS_HEATING["none"])
    current_heating_co2 = heating_data["co2e_kg"]
    current_heating_pm = heating_data["pm_g"]
    current_heating_cost = heating_data["cost_inr"]

    total_current_co2 = round(current_commute_co2 + current_cooking_co2 + current_heating_co2, 1)
    total_current_pm = round(current_cooking_pm + current_heating_pm, 1)
    total_current_cost = round(current_commute_cost + current_cooking_cost + current_heating_cost)

    commute_options = _build_commute_options(
        commute_mode, current_commute_co2, current_commute_cost
    )
    cooking_options = _build_cooking_options(
        cooking_fuel, current_cooking_co2, current_cooking_pm, current_cooking_cost
    )
    heating_options = _build_heating_options(
        heating_fuel, current_heating_co2, current_heating_pm, current_heating_cost
    )

    all_options = commute_options + cooking_options + heating_options
    filtered = _filter_by_budget(all_options, budget_filter)

    return EmissionsResult(
        current=EmissionsCurrent(
            commute_mode=commute_mode,
            weekly_co2e_kg=total_current_co2,
            weekly_pm_g=total_current_pm,
            weekly_cost_inr=round(total_current_cost),
        ),
        alternatives=filtered,
        all_alternatives=all_options,
        budget_filter=budget_filter,
    )
