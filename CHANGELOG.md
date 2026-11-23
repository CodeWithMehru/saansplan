# Changelog

All notable changes to the SaansPlan project are documented here.

## [2.0.0] - 2026-11-23

### Added
- **5-Day Winter Smog Forecast (`app/engine/forecast.py`):** Multi-day hourly analysis identifying daily best/worst outdoor windows, safest midday airing time (11:00–15:00), surface wind stagnation alerts (< 2 m/s), and CPCB severity banners.
- **Your Cleaner Day Optimizer (`app/engine/cleaner_day.py`):** 24-hour routine comparison that shifts flexible tasks to cleaner afternoon hours while strictly preserving fixed work/school commitments, displaying estimated $\mu\text{g}$ saved with $\pm 25\%$ uncertainty bands, an accessible SVG comparison chart, and table alternative.
- **Emissions & Cost Calculator (`app/engine/emissions.py`):** Weekly carbon footprint ($\text{kg CO}_2\text{e}$), particle output ($\text{g PM}$), and cost ($\text{INR}$) for commute, cooking, and heating, with budget tiers (`free`, `< ₹500`, `< ₹5000`, `any`).
- **Indoor Air Quality Module (`app/engine/indoor_module.py`):** Interactive AHAM CADR 2/3 room-sizing calculator, verified DIY box-fan filter guide (Corsi-Rosenthal principle), and room-by-room intervention checklists (kitchen, bedroom, living room, children's room).
- **Household Persona Presets (`app/engine/personas.py`, `app/static/js/state.js`):** 4 realistic urban Indian presets (Working Parents, Senior Citizen, Student/Hostel, Delivery Rider) for one-click form prefilling.
- **Community Action Kit (`app/engine/community.py`):** WhatsApp direct-share link generator, morning school advisory, and Resident Welfare Association (RWA) winter smog checklist.
- **Frontend ES-Module Architecture (`app/static/js/`):** Refactored monolith into clean ES-modules (`api.js`, `state.js`, `render.js`, `utils.js`, `speech.js`, `a11y/focus.js`) with zero inline style violations and zero inline handlers.
- **Accessibility & Axe 0 Violations (`scripts/a11y.py`):** Full WCAG 2.2 AA validation with 0 violations across English, Hinglish, and Hindi views; 360px mobile reflow (WCAG 1.4.10); keyboard skip link; A-/A/A+ text scaling; and polite/assertive live announcers.
- **Performance Optimizations:** In-memory `BoundedTTLCache` with TTL expiration, LRU eviction, and single-flight request coalescing; FastAPI lifespan with shared `httpx.AsyncClient`; HTTP GZip compression; weak ETags; 2.8ms 6-member plan calculation; and 30.7 KB gzipped static bundle.

### Changed
- Upgraded dependencies to resolve all pip-audit vulnerabilities (`fastapi>=0.115.12`, `python-dotenv>=1.2.4`, `starlette>=0.46.2`).
- Fixed health check routes to support both `/health` and `/api/health`.
- Formatted and enforced 100% ruff linting and strict mypy type coverage across all 32 modules.

## [1.1.0] - 2026-11-22

- Added property, golden, API, security, and a11y test structure with 90% coverage enforcement.
- Separated runtime (`requirements.txt`) and development dependencies (`requirements-dev.txt`).
- Added physical-unit planning, CPCB NAQI category helpers, and separate exposure/AQI peaks.
- Added human-readable swap labels (F10), Hindi locale, and grounded assistant fallback with medical redirection.
- Added proxy-aware rate limiting, strict Content Security Policy, and prompt injection test suite.
