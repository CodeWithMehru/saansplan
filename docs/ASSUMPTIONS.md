# Assumptions and sources

Every factor is a planning assumption, not a medical fact.

| Key | Unit / value | Status | Source to verify before final claim |
|---|---|---|---|
| VENTILATION_L_MIN | Rest 6, light 8, moderate 20, heavy 40 L/min | Assumption | US EPA Exposure Factors Handbook, Agency Factors and Ingestion/Exposure |
| CHILD_INHALATION_SCALE | 0.55 | Assumption | UK/US paediatric ventilation evidence; verify publisher-specific values |
| ELDERLY_INHALATION_SCALE | 0.70 | Assumption | Assumption pending a cited older-adult ventilation source |
| CPCB_PM25_BREAKPOINTS | Breakpoints in app/core/constants.py | Planning implementation pending official CPCB verification | Central Pollution Control Board India AQI documentation |
| PM2.5 forecast | Hourly forecast, not a 24-hour CPCB average | Limitation | Open-Meteo terms and air-quality documentation |

No claim in this file should be presented as a clinical dose estimate until the named source is fetched and the value is checked.
