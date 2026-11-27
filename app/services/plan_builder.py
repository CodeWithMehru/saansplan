"""Formatting, series extraction, and payload assembly helpers for the plan service."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.core.constants import DEFAULT_FORECAST_DAYS
from app.engine.assistant_models import AirQualityData
from app.engine.community import (
    generate_whatsapp_share_url,
    get_rwa_checklist,
    get_school_day_advisory,
)
from app.engine.exposure_models import ExposureResult
from app.engine.forecast import analyze_forecast
from app.engine.forecast_models import ForecastDay
from app.engine.indoor_guidance import (
    calculate_purifier_cadr,
    get_diy_box_fan_guide,
    get_room_checklists,
)
from app.engine.personas import get_personas
from app.schemas.plan import PlanRequest
from app.schemas.routine import HomeSetup, Routine

DEFAULT_ROOM_AREA_SQM = 15.0


@dataclass(frozen=True)
class PlanExecutionArtifacts:
    """Artifacts produced by the multi-engine calculation pipeline."""

    payload: PlanRequest
    air: AirQualityData | Mapping[str, object]
    engine: ExposureResult
    swaps_dicts: list[dict[str, object]]
    forecast_days: Sequence[ForecastDay]
    cleaner_day_dict: dict[str, object]
    emissions_dict: dict[str, object]
    community: dict[str, object]
    explanation: dict[str, object]


@dataclass(frozen=True)
class PipelineOutputs:
    """Intermediate computation artifacts from exposure, cleaner day, and emissions engines."""

    swaps_dicts: list[dict[str, object]]
    cleaner_day_dict: dict[str, object]
    emissions_dict: dict[str, object]
    explanation: dict[str, object]


def build_plan_artifacts(
    payload: PlanRequest,
    air: AirQualityData | Mapping[str, object],
    engine: ExposureResult,
    outputs: PipelineOutputs,
) -> PlanExecutionArtifacts:
    """Package calculation artifacts into response container."""
    pm25_list = extract_pm25_series(air)
    wind_list = extract_wind_series(air)
    forecast_days = analyze_forecast(pm25_list, wind_list, forecast_days=DEFAULT_FORECAST_DAYS)

    peak_aqi_raw = engine.get("peak_aqi", 250)
    peak_aqi = int(peak_aqi_raw) if isinstance(peak_aqi_raw, int | float | str) else 250
    category = str(engine.hourly[0].indian_category) if engine.hourly else "Poor"
    community = build_community_payload(
        payload.city, peak_aqi, category, outputs.swaps_dicts, outputs.cleaner_day_dict
    )
    return PlanExecutionArtifacts(
        payload=payload,
        air=air,
        engine=engine,
        swaps_dicts=outputs.swaps_dicts,
        forecast_days=forecast_days,
        cleaner_day_dict=outputs.cleaner_day_dict,
        emissions_dict=outputs.emissions_dict,
        community=community,
        explanation=outputs.explanation,
    )


def default_routine(request: PlanRequest) -> Routine:
    """Build a safe form-only fallback routine if no text or routine is supplied."""
    activities = request.routine.activities if request.routine else []
    if request.routine:
        return request.routine
    return Routine(
        activities=activities,
        home=HomeSetup(
            heating="none",
            cooking="lpg",
            windows="mostly_closed",
            purifier=False,
            has_chimney=False,
        ),
    )


def extract_primary_commute(routine: Routine) -> str:
    """Extract primary commute mode from active routine activities."""
    for act in routine.activities:
        if act.mode.value != "none":
            return act.mode.value
    return "none"


def extract_pm25_series(air: AirQualityData | Mapping[str, object]) -> list[float | None]:
    """Extract PM2.5 float values from AirQualityData or mapping."""
    raw = air.pm25 if isinstance(air, AirQualityData) else air.get("pm25")
    if isinstance(raw, Sequence):
        return [float(v) if isinstance(v, int | float) else None for v in raw]
    return []


def extract_aqi_series(air: AirQualityData | Mapping[str, object]) -> list[float | None]:
    """Extract AQI integer values from AirQualityData or mapping."""
    raw = air.aqi if isinstance(air, AirQualityData) else air.get("aqi")
    if isinstance(raw, Sequence):
        return [float(v) if isinstance(v, int | float) else None for v in raw]
    return []


def extract_wind_series(air: AirQualityData | Mapping[str, object]) -> list[float | None] | None:
    """Extract optional wind speed series from AirQualityData or mapping."""
    raw = air.wind_speed if isinstance(air, AirQualityData) else air.get("wind_speed")
    if isinstance(raw, Sequence):
        return [float(v) if isinstance(v, int | float) else None for v in raw]
    return None


def extract_metadata(air: AirQualityData | Mapping[str, object]) -> tuple[str, str]:
    """Extract timezone and data source from AirQualityData or mapping."""
    tz = str(air.timezone if isinstance(air, AirQualityData) else air.get("timezone", "UTC"))
    src = str(air.source if isinstance(air, AirQualityData) else air.get("source", "Open-Meteo"))
    return tz, src


def build_indoor_module() -> dict[str, object]:
    """Assemble default indoor room checklists and purification guidance."""
    return {
        "room_checklists": get_room_checklists(),
        "purifier_sizing_default": calculate_purifier_cadr(
            area_sq_meters=DEFAULT_ROOM_AREA_SQM
        ).to_dict(),
        "diy_box_fan_guide": get_diy_box_fan_guide().to_dict(),
    }


def build_community_payload(
    city: str | None,
    peak_aqi: int,
    category: str,
    swaps: Sequence[dict[str, object]],
    cleaner_day: Mapping[str, object],
) -> dict[str, object]:
    """Generate shareable community advisory texts and links."""
    top_swap_desc = (
        str(swaps[0].get("description_key", "Keep windows closed"))
        if swaps
        else "Keep windows closed"
    )
    reduction = cleaner_day.get("percent_reduction", 0)
    summary = (
        f"SaansPlan Family Summary:\n"
        f"Location: {city or 'My City'} (AQI {peak_aqi} - {category})\n"
        f"Top swap: {top_swap_desc}\n"
        f"Dose reduction: {reduction}% cleaner routine.\n"
        f"Check full low-emission day plan on SaansPlan."
    )
    return {
        "school_advisory": get_school_day_advisory(
            max_aqi=peak_aqi, indian_category=category
        ).to_dict(),
        "rwa_checklist": get_rwa_checklist().to_dict(),
        "whatsapp_url": generate_whatsapp_share_url(summary),
        "shareable_text": summary,
    }


def format_plan_response(artifacts: PlanExecutionArtifacts) -> dict[str, object]:
    """Package calculation engines and guidance into stable JSON response envelope."""
    peak = max(artifacts.engine.hourly, key=lambda row: row.pm25)
    personas_dict = {k: v.to_dict() for k, v in get_personas().items()}
    tz, src = extract_metadata(artifacts.air)
    return {
        "location": {
            "latitude": artifacts.payload.latitude,
            "longitude": artifacts.payload.longitude,
            "city": artifacts.payload.city,
            "timezone": tz,
            "source": src,
        },
        "exposure": artifacts.engine.to_dict(),
        "top_swaps": artifacts.swaps_dicts,
        "hourly": [h.to_dict() for h in artifacts.engine.hourly],
        "indoor_hacks": artifacts.engine["indoor_hacks"],
        "sustainable_alternatives": artifacts.engine["sustainable_alternatives"],
        "peak_pm25_hour": peak.hour,
        "forecast": [f.to_dict() for f in artifacts.forecast_days],
        "cleaner_day": artifacts.cleaner_day_dict,
        "emissions": artifacts.emissions_dict,
        "indoor_module": build_indoor_module(),
        "personas": personas_dict,
        "community": artifacts.community,
        "explanation": artifacts.explanation,
        "estimate_label": "All values are estimates",
    }
