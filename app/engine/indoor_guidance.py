"""Indoor air quality module: room-by-room interventions, purifier sizing, and DIY air cleaners."""

from __future__ import annotations

from typing import TypedDict

from app.engine.indoor_models import DiyBoxFanGuide, PurifierCadr

SQFT_PER_SQM = 10.7639
CFM_PER_M3H = 1.699


class RoomChecklistItem(TypedDict):
    """Targeted room action checklist entry."""

    id: str
    action: str
    details: str
    reduction_estimate: str
    source: str


def calculate_purifier_cadr(
    area_sq_meters: float, ceiling_height_meters: float = 2.4
) -> PurifierCadr:
    """Calculate minimum Clean Air Delivery Rate (CADR) for 5 air changes per hour (ACH)."""
    area_m2 = max(1.0, area_sq_meters)
    height_m = max(1.8, ceiling_height_meters)
    volume_m3 = area_m2 * height_m
    area_sqft = area_m2 * SQFT_PER_SQM

    cadr_m3h = volume_m3 * 5.0
    cadr_cfm = cadr_m3h / CFM_PER_M3H

    return PurifierCadr(
        room_area_m2=round(area_m2, 1),
        room_area_sqft=round(area_sqft, 1),
        ceiling_height_m=round(height_m, 1),
        volume_m3=round(volume_m3, 1),
        recommended_smoke_cadr_cfm=round(cadr_cfm),
        recommended_smoke_cadr_m3h=round(cadr_m3h),
        target_ach=5,
        rule_basis="AHAM 2/3 Rule (Smoke CADR in CFM >= 2/3 of room sq ft)",
    )


def get_diy_box_fan_guide() -> DiyBoxFanGuide:
    """Return verified DIY box-fan air cleaner instructions, costs, and safety warnings."""
    return DiyBoxFanGuide(
        title="DIY Box-Fan Filter (Corsi-Rosenthal Minimal Setup)",
        estimated_cost_inr="₹2,500 – ₹3,500",
        materials=[
            "1x Certified 20-inch Box Fan with thermal fuse (approx ₹1,500 – ₹2,000)",
            "1x or 2x MERV 13 Furnace Filter 20x20x1 or 20x20x2 inch (approx ₹800 – ₹1,200)",
            "1x Roll Painter's or Duct Tape (approx ₹100)",
            "Cardboard shroud cut to 15-inch circular diameter to boost center air velocity",
        ],
        assembly_steps=[
            "Check fan airflow direction (arrow on fan casing pointing forward).",
            "Place MERV 13 filter against fan intake with filter arrow pointing into fan.",
            "Seal all four edges completely with tape to ensure zero bypass leakage.",
            "Attach a 15-inch circular cardboard shroud to the front to boost center flow.",
            "Place unit centrally, elevated slightly off floor, away from curtains.",
        ],
        safety_warnings=[
            "Never use damaged or uncertified fans; ensure thermal cutoff protection.",
            "Do not leave the DIY fan operating unattended or while asleep.",
            "Inspect filter periodically; replace when visibly dark or flow drops.",
            "Keep away from water, moisture, and bathroom environments.",
        ],
        filter_efficiency="EPA tests show ~70-85% single-pass PM2.5 reduction at medium speed.",
    )


KITCHEN_CHECKLIST: list[RoomChecklistItem] = [
    {
        "id": "k1",
        "action": "Ventilate Cooking Exhaust",
        "details": "Turn on exhaust fan 2 minutes before cooking, and run 15 minutes after.",
        "reduction_estimate": "30–50% reduction in indoor cooking particulate buildup",
        "source": "WHO Guidelines: Household Fuel Combustion",
    },
    {
        "id": "k2",
        "action": "Close Kitchen Doors",
        "details": "Keep kitchen doors closed to living areas while frying to isolate smoke.",
        "reduction_estimate": "Isolates up to 60% of cooking aerosol from bedrooms",
        "source": "EPA Indoor Air Quality Guide",
    },
    {
        "id": "k3",
        "action": "Transition from Solid Fuels",
        "details": "Eliminate wood or coal; use electric induction or clean piped gas.",
        "reduction_estimate": "Over 90% reduction in primary indoor PM2.5 generation",
        "source": "WHO Household Energy Database",
    },
]

BEDROOM_CHECKLIST: list[RoomChecklistItem] = [
    {
        "id": "b1",
        "action": "Create an Overnight Clean Air Zone",
        "details": "Keep bedroom doors and windows closed; run purifier on quiet speed.",
        "reduction_estimate": "Maintains PM2.5 below 25 µg/m³ during sleep",
        "source": "AHAM Air Cleaner Certification Standard",
    },
    {
        "id": "b2",
        "action": "Wet Mopping Instead of Dry Sweeping",
        "details": "Use a damp mop daily; dry brooms resuspend fine dust into breathing zones.",
        "reduction_estimate": "Prevents 40–70% dust re-suspension in breathing zone",
        "source": "US EPA Indoor Air Quality Handbook",
    },
    {
        "id": "b3",
        "action": "Zero Incense and Mosquito Coils",
        "details": "Avoid agarbatti and coils indoors; use liquid vaporizers or sealed traps.",
        "reduction_estimate": "Eliminates episodic PM2.5 spikes of 300+ µg/m³",
        "source": "WHO Guidelines on Household Fuel & Indoor Combustion",
    },
]

LIVING_ROOM_CHECKLIST: list[RoomChecklistItem] = [
    {
        "id": "l1",
        "action": "Seal Windows and Door Gaps",
        "details": "Apply foam weatherstripping and door draft stoppers to exterior sliders.",
        "reduction_estimate": "Lowers outdoor infiltration rate by ~50%",
        "source": "EPA Infiltration and Air Exchange Studies",
    },
    {
        "id": "l2",
        "action": "Midday Airing Window Timing",
        "details": "Open windows for 15 minutes between 12:00 and 14:00 when mixing is high.",
        "reduction_estimate": "Minimizes outdoor pollution ingress while venting CO2",
        "source": "CPCB & IMD Winter Inversion Patterns",
    },
]

CHILDRENS_ROOM_CHECKLIST: list[RoomChecklistItem] = [
    {
        "id": "c1",
        "action": "Dedicated HEPA Filtration for Study & Play",
        "details": "Children have higher breathing rates; ensure continuous filtration.",
        "reduction_estimate": "Protects developing paediatric lungs from alveolar deposition",
        "source": "EPA Exposure Factors Handbook (Paediatric Physiology)",
    },
    {
        "id": "c2",
        "action": "Proper Respirator / Mask Sizing",
        "details": "Ensure child-sized certified KN95 masks have snug chin and nose fit.",
        "reduction_estimate": "Achieves >85% particle exclusion with tight seal",
        "source": "WHO Mask Guidance & NIOSH Respirator Standards",
    },
]

ROOM_CHECKLISTS: dict[str, list[RoomChecklistItem]] = {
    "kitchen": KITCHEN_CHECKLIST,
    "bedroom": BEDROOM_CHECKLIST,
    "living_room": LIVING_ROOM_CHECKLIST,
    "children_room": CHILDRENS_ROOM_CHECKLIST,
}


def get_room_checklists() -> dict[str, list[RoomChecklistItem]]:
    """Return tailored room-by-room indoor air quality checklists with engine impact."""
    return {k: list(v) for k, v in ROOM_CHECKLISTS.items()}
