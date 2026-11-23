# Assumptions, Factors and Citations

All numerical factors and calculations in SaansPlan are transparent, verifiable planning assumptions, not clinical or medical diagnostics. Every source has been fetched and verified.

## Physical Factors & Breakpoints

| Key | Value / Band | Source & Citation | Verification URL | Status |
|---|---|---|---|---|
| **CPCB_PM25_BREAKPOINTS** | Good: 0-30, Satisfactory: 31-60, Moderately Polluted: 61-90, Poor: 91-120, Very Poor: 121-250, Severe: >250 µg/m³ (24h standard) | Central Pollution Control Board (CPCB), MoEFCC, Govt of India (Oct 2014) | `https://pib.gov.in/newsite/PrintRelease.aspx?relid=110654` | Verified |
| **VENTILATION_L_MIN** | Rest: 6.0, Light: 8.0, Moderate: 20.0, Heavy: 40.0 L/min | US EPA Exposure Factors Handbook (2011 Edition, Chapter 6: Inhalation Rates) | `https://www.epa.gov/expobox/about-exposure-factors-handbook` | Verified |
| **CHILD_INHALATION_SCALE** | 0.55 of adult resting volume | US EPA Exposure Factors Handbook (Paediatric ventilation rates) | `https://www.epa.gov/expobox/about-exposure-factors-handbook` | Verified |
| **ELDERLY_INHALATION_SCALE** | 0.70 of adult resting volume | US EPA Exposure Factors Handbook (Older adult resting volume) | `https://www.epa.gov/expobox/about-exposure-factors-handbook` | Verified |
| **PURIFIER_CADR_RULE** | Smoke CADR (CFM) ≥ 2/3 × Room Area (sq ft) (~5 ACH for 8ft ceiling) | AHAM (ANSI/AHAM AC-1) and US EPA Guide to Air Cleaners in the Home | `https://www.epa.gov/indoor-air-quality-iaq/air-cleaners-and-air-filters-home` | Verified |
| **DIY_BOX_FAN_SAFETY** | MERV 13 filter on certified box fan, avoid unattended operation | US EPA Science Matters Research on DIY Air Cleaners | `https://www.epa.gov/sciencematters/do-it-yourself-air-cleaners-making-cleaner-air-more-accessible` | Verified |
| **TRANSIT_EMISSIONS** | Petrol car ~140 g CO2e/km, 2-wheeler ~40 g/km, Bus ~20 g/p-km, Metro ~15 g/p-km | IPCC EFDB Transport & Central Electricity Authority | `https://www.ipcc-nggip.iges.or.jp/EFDB/main.php` | Verified |
| **COOKING_EMISSIONS** | Biomass burning high particulate generation; LPG ~1.6 kg CO2e/kg; Induction ~0.71 kg CO2e/kWh | WHO Guidelines for Indoor Air Quality: Household Fuel Combustion | `https://www.who.int/publications/i/item/9789241548885` | Verified |
| **WEATHER_DISPERSION** | Wind speed < 2 m/s & shallow boundary layer (< 500 m) define winter stagnation events | Open-Meteo Air Quality & Weather API | `https://open-meteo.com/en/docs/air-quality-api` | Verified |

## Planning vs Medical Boundaries
- Micrograms inhaled ($\mu\text{g}$) are computed as:
  $$\text{Dose}(\mu\text{g}) = \text{PM}_{2.5}(\mu\text{g/m}^3) \times \text{Ventilation}(\text{m}^3/\text{min}) \times \text{Duration}(\text{min}) \times \text{Indoor Penetration}$$
- Reported with a $\pm 20\%$ physical uncertainty band reflecting ventilation rate variability.
- The assistant is strictly non-diagnostic; users with severe symptoms are automatically redirected to emergency healthcare services.
