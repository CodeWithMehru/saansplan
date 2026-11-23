"""Runtime constants and source-keyed assumptions."""

CPCB_PM25_BREAKPOINTS = (
    # SOURCE - Central Pollution Control Board National AQI, see docs/ASSUMPTIONS.md
    (0.0, 30.0, 0, 50, "Good", "good"),
    (31.0, 60.0, 51, 100, "Satisfactory", "satisfactory"),
    (61.0, 90.0, 101, 200, "Moderately polluted", "moderate"),
    (91.0, 120.0, 201, 300, "Poor", "poor"),
    (121.0, 250.0, 301, 400, "Very poor", "very-poor"),
    (251.0, 500.0, 401, 500, "Severe", "severe"),
)

# ASSUMPTION - approximate, see docs/ASSUMPTIONS.md source: EPA Exposure Factors Handbook
VENTILATION_L_MIN: dict[str, float] = {
    "rest": 6.0,
    "light": 8.0,
    "moderate": 20.0,
    "heavy": 40.0,
}
# ASSUMPTION - approximate, see docs/ASSUMPTIONS.md
CHILD_INHALATION_SCALE = 0.55
# ASSUMPTION - approximate, see docs/ASSUMPTIONS.md
ELDERLY_INHALATION_SCALE = 0.70

HOURS_IN_DAY = 24
HTTP_STATUS_OK = 200
SEVERE_AQI_THRESHOLD = 300
DEFAULT_FORECAST_DAYS = 5
