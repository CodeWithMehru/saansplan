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

# ASSUMPTION - approximate, see README Assumptions
CACHE_TTL_SECONDS = 30 * 60
# ASSUMPTION - approximate, see README Assumptions
OUTBOUND_TIMEOUT_SECONDS = 10.0
# ASSUMPTION - approximate, see README Assumptions
OUTBOUND_RETRIES = 2
# ASSUMPTION - approximate, see README Assumptions
RATE_LIMIT = "30/minute"
# ASSUMPTION - approximate, see README Assumptions
MAX_REQUEST_BYTES = 64 * 1024

# ASSUMPTION - approximate, see README Assumptions
BREATHING_FACTORS = {"rest": 1.0, "light": 1.2, "moderate": 1.7, "heavy": 2.2}
# ASSUMPTION - approximate, see README Assumptions
MEMBER_SENSITIVITY = {"child": 1.25, "adult": 1.0, "elderly": 1.35}
# ASSUMPTION - approximate, see README Assumptions
INFILTRATION_OPEN = 0.70
# ASSUMPTION - approximate, see README Assumptions
INFILTRATION_CLOSED = 0.35
# ASSUMPTION - approximate, see README Assumptions
PURIFIER_FACTOR = 0.55
# ASSUMPTION - approximate, see README Assumptions
MASK_EFFICIENCY = 0.30

# ASSUMPTION - approximate, see README Assumptions
INDOOR_SOURCE_INCREMENTS = {
    "wood_coal": 55.0,
    "biomass": 45.0,
    "gas_cooking": 12.0,
    "lpg_cooking": 6.0,
    "induction": 1.0,
    "incense": 8.0,
}
# ASSUMPTION - approximate, see README Assumptions
VEHICLE_FACTOR = 0.75
# ASSUMPTION - approximate, see README Assumptions
AQI_UNHEALTHY_THRESHOLD = 150
# ASSUMPTION - approximate, see README Assumptions
TOP_SWAP_LIMIT = 3
