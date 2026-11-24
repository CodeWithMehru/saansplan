"""Application constants and documented assumptions."""

from app.core.settings import get_settings

_settings = get_settings()

GROQ_MODEL = _settings.groq_model
GROQ_ENDPOINT = _settings.groq_endpoint
AIR_QUALITY_ENDPOINT = _settings.air_quality_endpoint

# ASSUMPTION - approximate, see README Assumptions
CACHE_TTL_SECONDS = _settings.cache_ttl_seconds
# ASSUMPTION - approximate, see README Assumptions
OUTBOUND_TIMEOUT_SECONDS = _settings.outbound_timeout_seconds
# ASSUMPTION - approximate, see README Assumptions
OUTBOUND_RETRIES = _settings.outbound_retries
# ASSUMPTION - approximate, see README Assumptions
RATE_LIMIT = _settings.rate_limit
# ASSUMPTION - approximate, see README Assumptions
MAX_REQUEST_BYTES = _settings.max_request_bytes

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
