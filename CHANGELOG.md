# Changelog

All notable changes to the SaansPlan project are documented here.

## [2.3.0] - 2026-11-27

### Refactored
- **Code Quality & Architecture Refactor:**
  - Consolidated duplicate script layout under canonical `scripts/reports/` and `scripts/verify/` directories, removing legacy root redirects.
  - Eliminated legacy backward-compatibility shims (legacy config, models, limiting, guard, and indoor shims).
  - Reorganized test suite into domain hierarchies (`tests/unit/engine/`, `tests/unit/services/`, `tests/api/`, `tests/security/`, `tests/a11y/`) with behavior-based test naming.
  - Enhanced type safety: defined `AssistantResult` and `SafetyResult` TypedDicts, cleaned Starlette exception signatures, replaced broad `except Exception` with specific tuples, and added dictionary support to `PersonaMember`.
  - Decomposed long functions: extracted static room checklists in `indoor_guidance.py`, persona presets in `personas.py`, swap helpers in `swaps.py`, and emission calculation helpers in `emissions.py`.
  - Single source of truth for configuration: deferred `load_dotenv` to runtime setting initialization, exported clean `__all__` in `app/core/settings.py`.
  - Frontend modularization: moved `i18n.js` to `app/static/js/i18n.js`, modularized `styles.css` into `app/static/css/{tokens,base,layout,components,utilities}.css`, formatted static assets with Prettier, and verified WCAG 2.2 reflow and target size.
  - Tooling hygiene: aligned `mutmut` 3.x configuration, deleted obsolete `setup.cfg`, and integrated Prettier into `.pre-commit-config.yaml`.
  - Streamlined `README.md` to a concise $\le 10$ KB structure, extracting detailed upgrade history into `docs/UPGRADES.md`.

## [2.2.0] - 2026-11-26

### Refactored
- **Cyclomatic Complexity Reduction (Radon & Xenon Rank A):**
  - Average cyclomatic complexity reduced to 2.37 across 247 blocks; every single function in the core domain capped at CC $\le 5$ (Rank A).
  - 100% of modules achieve Xenon Rank A (`xenon --max-absolute B --max-modules A --max-average A app/` clean).
- **Backend Architecture & Service Decoupling:**
  - Extracted `app/api/router.py` aggregating API routes into centralized `api_router`.
  - Extracted `app/core/middleware.py` (security headers, caching headers, payload limit inspection) and `app/core/error_handlers.py` (RFC 6585 rate limiting, 404, validation error envelope).
  - Extracted orchestration pipeline from `app/routers/plan.py` into dedicated `app/services/plan_service.py` (shrunk route handler to 11 lines).
  - Renamed assistant resolvers to `app/services/assistant_grounding.py`.
  - Defined centralized domain enumerations in `app/schemas/enums.py` (`CPCBCategory`, `BudgetTier`) and `app/schemas/routine.py` (`HeatingFuel`, `CookingFuel`, `WindowHabit`).
- **Frontend Architecture & Tooling Consolidation:**
  - Extracted `app/static/js/constants.js` centralizing API endpoints, localStorage keys, CPCB breakpoints, and defaults.
  - Added full JSDoc typing across ES modules; verified with `tsc --noEmit`.
  - Relocated frontend unit tests from the public static mount to dedicated `tests/js/`.
  - Removed duplicate config files (`.eslintrc.json`, `.prettierrc`) in favor of canonical `eslint.config.mjs` and `.prettierrc.json`.
  - Added `.htmlvalidate.json` and resolved HTML validation issues in `app/static/index.html` and `app/static/accessibility.html`.
- **Test & Script Hygiene:**
  - Reorganized script entries with clean forwarders across `scripts/reports/` and `scripts/verify/`.
  - Automated venv detection in `scripts/verify/a11y.py` and dynamic metric generation in `scripts/reports/quality_report.py` and `scripts/reports/report.py`.
  - All 280 automated tests (269 pytest + 11 node.js) pass hermetically with 99.32% statement coverage.


## [2.1.0] - 2026-11-25

### Added
- **Architecture & Modularity:** Thin routers (`app/routers/ask.py` reduced to 52 lines, domain orchestration moved to `app/services/assistant.py` and `app/services/assistant_grounding.py`); decomposed guard architecture (`app/services/guard_numbers.py`, `app/services/guard_safety.py`, `app/services/guard_wording.py`); domain schemas in `app/schemas/` (`family.py`, `routine.py`, `plan.py`, `ask.py`); componentized frontend ES modules in `app/static/js/render/` (`members.js`, `timeline.js`, `swaps.js`, `forecast.js`, `cleaner_day.js`, `emissions.js`, `indoor.js`, `community.js` and `handlers.js`). All files in `app/` are strictly $\le 240$ lines (zero files $> 250$ lines).
- **Code Quality & Typing:** Radon cyclomatic complexity reduced to Rank A (3.22 average, max 9); 187/187 items documented via `interrogate` (100.0% docstring coverage); Mypy `--strict` clean across 46 source files; AST architectural boundary enforcement in `tests/unit/test_architecture_boundaries.py`.
- **Testing Boost (178 passed, 96.07% coverage):** Coverage threshold raised to `--cov-fail-under=95` in `pyproject.toml`; added unit service suites (`tests/unit/services/test_plan_service.py`), fault injection tests (`tests/security/test_fault_injection.py` covering upstream 500s, Groq 429s, and IP spoofing), Hypothesis property-based invariants (`tests/unit/engine/test_property_invariants.py`), and 7 regression characterization snapshots (`tests/api/test_characterization_snapshots.py`).
- **Security Hardening:** Enforced `Content-Type: application/json` on POST with 415 rejection; added `Cross-Origin-Resource-Policy: same-origin` and `X-Request-ID` headers; published RFC 9116 `app/static/.well-known/security.txt`; SHA-pinned GitHub Actions in `.github/workflows/ci.yml` with weekly scheduled security audit; expanded multi-lingual prompt-injection test corpus to 48 vectors in `tests/security/test_prompt_injection.py`.
- **Accessibility Enhancements:** Added dedicated `/accessibility` statement page (`app/static/accessibility.html`); Reading Comfort panel in `app/static/index.html` with High Contrast and Text Spacing (WCAG 1.4.12) controls persisting in localStorage; visible skip links for `#main-content`, `#results`, and `#ask-section`; Google Lighthouse accessibility verified at 100/100; zero Axe-Core violations across 56 rules and 5 application states in `scripts/verify/a11y.py`.
- **Grounded Assistant Grounding:** Grounded `/api/ask` with verified knowledge base snippets, deterministic AHAM 2/3 CADR calculation (150 sq ft → 100 CFM), live plan facts, and immediate medical emergency redirects for acute respiratory symptoms.

## [2.0.0] - 2026-11-23

### Added
- **5-Day Winter Smog Forecast (`app/engine/forecast.py`):** Multi-day hourly analysis identifying daily best/worst outdoor windows, safest midday airing time (11:00–15:00), surface wind stagnation alerts (< 2 m/s), and CPCB severity banners.
- **Your Cleaner Day Optimizer (`app/engine/cleaner_day.py`):** 24-hour routine comparison that shifts flexible tasks to cleaner afternoon hours while strictly preserving fixed work/school commitments, displaying estimated $\mu\text{g}$ saved with $\pm 25\%$ uncertainty bands, an accessible SVG comparison chart, and table alternative.
- **Emissions & Cost Calculator (`app/engine/emissions.py`):** Weekly carbon footprint ($\text{kg CO}_2\text{e}$), particle output ($\text{g PM}$), and cost ($\text{INR}$) for commute, cooking, and heating, with budget tiers (`free`, `< ₹500`, `< ₹5000`, `any`).
- **Indoor Air Quality Module (`app/engine/indoor_guidance.py`):** Interactive AHAM CADR 2/3 room-sizing calculator, verified DIY box-fan filter guide (Corsi-Rosenthal principle), and room-by-room intervention checklists (kitchen, bedroom, living room, children's room).
- **Household Persona Presets (`app/engine/personas.py`, `app/static/js/state.js`):** 4 realistic urban Indian presets (Working Parents, Senior Citizen, Student/Hostel, Delivery Rider) for one-click form prefilling.
- **Community Action Kit (`app/engine/community.py`):** WhatsApp direct-share link generator, morning school advisory, and Resident Welfare Association (RWA) winter smog checklist.
- **Frontend ES-Module Architecture (`app/static/js/`):** Refactored monolith into clean ES-modules (`app/static/js/api.js`, `app/static/js/state.js`, `app/static/js/utils.js`, `app/static/js/speech.js`, `app/static/js/a11y/focus.js`) with zero inline style violations and zero inline handlers.
- **Accessibility & Axe 0 Violations (`scripts/verify/a11y.py`):** Full WCAG 2.2 AA validation with 0 violations across English, Hinglish, and Hindi views; 360px mobile reflow (WCAG 1.4.10); keyboard skip link; A-/A/A+ text scaling; and polite/assertive live announcers.
- **Performance Optimizations:** In-memory `BoundedTTLCache` with TTL expiration, LRU eviction, and single-flight request coalescing; FastAPI lifespan with shared `httpx.AsyncClient`; HTTP GZip compression; weak ETags; sub-2ms 6-member plan calculation; and 32.7 KB gzipped static bundle.

### Changed
- Upgraded dependencies to resolve all pip-audit vulnerabilities (`fastapi>=0.115.12`, `python-dotenv>=1.2.4`, `starlette>=0.46.2`).
- Fixed health check routes to support both `/health` and `/api/health`.
- Formatted and enforced ruff linting and strict mypy type coverage across all source modules.

## [1.1.0] - 2026-11-22

- Added property, golden, API, security, and a11y test structure with 90% coverage enforcement.
- Separated runtime (`requirements.txt`) and development dependencies (`requirements-dev.txt`).
- Added physical-unit planning, CPCB NAQI category helpers, and separate exposure/AQI peaks.
- Added human-readable swap labels (F10), Hindi locale, and grounded assistant fallback with medical redirection.
- Added proxy-aware rate limiting, strict Content Security Policy, and prompt injection test suite.
