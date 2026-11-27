"""Sustainable alternatives and indoor hacks."""

from __future__ import annotations

from app.engine.swaps_models import IndoorHack, SustainableAlternative


def indoor_hacks() -> list[IndoorHack]:
    """Return practical indoor actions with qualitative estimated impact."""
    return [
        IndoorHack(
            key="purifier",
            impact="high",
            estimate="May reduce indoor PM2.5 substantially when correctly sized.",
        ),
        IndoorHack(
            key="closed_windows",
            impact="medium",
            estimate="May reduce outdoor infiltration during high-AQI hours.",
        ),
        IndoorHack(
            key="box_fan_filter",
            impact="medium",
            estimate=(
                "A properly built filter may reduce particles; use only as a supplemental setup."
            ),
        ),
        IndoorHack(
            key="chimney",
            impact="high",
            estimate="May reduce cooking and heating smoke when vented outdoors.",
        ),
        IndoorHack(
            key="mask",
            impact="medium",
            estimate=(
                "A well-fitted certified respirator may reduce unavoidable "
                "outdoor particle inhalation."
            ),
        ),
    ]


def sustainable_alternatives() -> list[SustainableAlternative]:
    """Return commute, fuel and heating alternatives."""
    return [
        SustainableAlternative(
            key="metro_bus",
            exposure_note="May reduce outdoor duration; verify AQ inside vehicle.",
            emissions_note="May lower emissions versus a private car when shared.",
        ),
        SustainableAlternative(
            key="walk_cycle",
            exposure_note="Only choose quieter, lower-AQI hours and avoid heavy traffic.",
            emissions_note="Near-zero direct fuel emissions.",
        ),
        SustainableAlternative(
            key="induction",
            exposure_note="May lower indoor combustion particles.",
            emissions_note="Avoids on-site combustion; grid impact varies.",
        ),
        SustainableAlternative(
            key="insulation",
            exposure_note="May reduce need for smoky supplemental heating.",
            emissions_note="May lower heating energy use.",
        ),
    ]
