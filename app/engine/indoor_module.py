"""Indoor air quality module facade (re-exports from indoor_guidance)."""

from app.engine.indoor_guidance import (
    CFM_PER_M3H,
    SQFT_PER_SQM,
    calculate_purifier_cadr,
    get_diy_box_fan_guide,
    get_room_checklists,
)

__all__ = [
    "CFM_PER_M3H",
    "SQFT_PER_SQM",
    "calculate_purifier_cadr",
    "get_diy_box_fan_guide",
    "get_room_checklists",
]
