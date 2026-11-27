"""Community kit: WhatsApp share links, class parent group advisories, and RWA action checklists."""

from __future__ import annotations

import urllib.parse

from app.core.constants import SEVERE_AQI_THRESHOLD
from app.engine.community_models import RwaChecklist, RwaChecklistItem, SchoolAdvisory


def generate_whatsapp_share_url(summary_text: str) -> str:
    """Generate a direct WhatsApp click-to-chat URL with URL-encoded message text."""
    encoded_text = urllib.parse.quote(summary_text)
    return f"https://wa.me/?text={encoded_text}"


def get_school_day_advisory(max_aqi: int, indian_category: str) -> SchoolAdvisory:
    """Generate school morning air quality advisory for class parent WhatsApp groups."""
    is_severe = max_aqi > SEVERE_AQI_THRESHOLD or indian_category in ("Very Poor", "Severe")
    advisory_actions = [
        "Ensure children wear well-fitted certified N95 / KN95 masks during morning transit.",
        "Recommend moving sports and morning assembly indoors during peak pollution hours.",
        "Advise keeping school bus windows closed on congested traffic corridors.",
        "Keep emergency inhalers and medications accessible with school medical staff.",
    ]
    if is_severe:
        advisory_actions.insert(
            0,
            "SEVERE SMOG ALERT: Request suspension of strenuous outdoor sports and recess.",
        )

    share_text = (
        f"📢 *SaansPlan School Day Advisory*\n"
        f"Today's peak outdoor AQI is {max_aqi} ({indian_category}).\n"
        f"Key recommendations for parents & teachers:\n"
        + "\n".join(f"• {act}" for act in advisory_actions)
        + "\n\n_Generated via SaansPlan. Planning suggestions, not legal/medical orders._"
    )

    return SchoolAdvisory(
        title=f"Morning School Commute Advisory — AQI {max_aqi} ({indian_category})",
        severity="high" if is_severe else "moderate",
        category=indian_category,
        actions=advisory_actions,
        shareable_text=share_text,
    )


def get_rwa_checklist() -> RwaChecklist:
    """Return Resident Welfare Association (RWA) and neighbourhood clean air checklist."""
    return RwaChecklist(
        title="RWA & Neighbourhood Clean Air Action Plan",
        disclaimer="Community suggestions for citizen action, not legal advice.",
        items=[
            RwaChecklistItem(
                category="Dust Control",
                action="Water Sprinkling on Unpaved Surfaces",
                guidance=(
                    "Sprinkle recycled water twice daily on construction and dirt perimeters."
                ),
            ),
            RwaChecklistItem(
                category="Waste Burning",
                action="Zero Open Waste & Leaf Burning",
                guidance=("Compost fallen leaves; report open garbage burning to green helplines."),
            ),
            RwaChecklistItem(
                category="Power & Emissions",
                action="Regulate Diesel Generator (DG) Sets",
                guidance="Restrict non-emergency DG sets in smog; switch to battery/PNG backup.",
            ),
            RwaChecklistItem(
                category="Transport",
                action="Neighbourhood School & Office Carpooling",
                guidance="Coordinate shared vans or group carpools to reduce gate traffic.",
            ),
            RwaChecklistItem(
                category="Green Cover",
                action="Dust-Trapping Vertical Greenery",
                guidance=(
                    "Plant native dense canopy hedges (Neem, Bougainvillea) as dust filters."
                ),
            ),
        ],
    )
