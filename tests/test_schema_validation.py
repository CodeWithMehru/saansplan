from pydantic import ValidationError

from app.schemas.plan import PlanRequest
from app.schemas.routine import Routine


def test_extra_fields_rejected():
    try:
        Routine.model_validate(
            {
                "activities": [],
                "home": {
                    "heating": "none",
                    "cooking": "lpg",
                    "windows": "mostly_closed",
                    "purifier": False,
                    "has_chimney": False,
                },
                "extra": True,
            }
        )
    except ValidationError:
        return
    raise AssertionError("Extra field should be rejected")


def test_bad_enum_rejected():
    try:
        PlanRequest.model_validate(
            {"latitude": 28.6, "longitude": 77.2, "members": [{"age_group": "infant"}]}
        )
    except ValidationError:
        return
    raise AssertionError("Bad enum should be rejected")
