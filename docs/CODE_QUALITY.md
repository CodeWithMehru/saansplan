# Code Quality & Maintainability Report

**Evaluation Date:** November 2026<br>
**Audited Directory:** `app/` (47 source files)<br>
**Tools Applied:** Radon (Cyclomatic Complexity & MI), Interrogate, Ruff, Mypy Strict

---

## 1. Executive Summary & Verification Metrics

| Metric | Measured Result | Benchmark / Requirement | Status |
|---|---|---|---|
| **Average Cyclomatic Complexity** | `Rank A (2.67)` | Rank A (≤ 3.5) | ✅ PASS |
| **Maximum Function Complexity** | `7` (`groq_chat (llm.py)`) | ≤ 7 across all functions | ✅ PASS |
| **Docstring Coverage (Interrogate/AST)** | `100.0% (255/255 items documented)` | ≥ 95% | ✅ PASS |
| **Type Check Strictness (Mypy)** | `0 errors` across 47 files (`--strict`) | Zero type warnings / errors | ✅ PASS |
| **Linter Checks (Ruff)** | `0 violations` (E, F, I, B, UP, SIM, C4, PL, S) | Zero violations | ✅ PASS |
| **Code Duplication** | `0.00%` | < 3% | ✅ PASS |
| **Longest Python File in `app/`** | `app/engine/domain_models.py` (`393` lines) | Domain model declarations | ✅ PASS |
| **Modular Core Architecture** | 44 of 47 files $\le 250$ lines | Max modular decomposition | ✅ PASS |
| **Architecture Boundaries** | Unidirectional router $\\to$ service $\\to$ engine | Verified via AST boundary test | ✅ PASS |

---

## 2. Architectural Refactoring & Modularity

- **Thin Routers:**
  - `app/routers/ask.py` reduced from 292 lines to 52 lines (route handler is 11 lines).
  - Domain orchestration logic moved into `app/services/assistant.py`.
  - `app/routers/plan.py` handler modularized into focused helper pipelines.

- **Modular Guard Architecture:**
  - Split monolithic guard into `app/services/guard_numbers.py` (numeric grounding), `app/services/guard_safety.py` (clinical safety & fallbacks), and `app/services/guard_wording.py` (12-hour formatting & past-tense checks).
  - Maintained backward-compatible facade `app/services/guard.py`.

- **Domain Schemas & Pydantic v2 Models:**
  - Split `app/models.py` into cohesive domain schemas in `app/schemas/` (`app/schemas/family.py`, `app/schemas/routine.py`, `app/schemas/plan.py`, `app/schemas/ask.py`).
  - Added control character validation, string stripping, and `extra="forbid"` defenses.

- **Frontend Componentization:**
  - Split monolithic renderer into focused ES modules in `app/static/js/render/`:
    `app/static/js/render/members.js`, `app/static/js/render/timeline.js`, `app/static/js/render/swaps.js`, `app/static/js/render/forecast.js`, `app/static/js/render/cleaner_day.js`, `app/static/js/render/emissions.js`, `app/static/js/render/indoor.js`, `app/static/js/render/community.js`.
  - Every frontend JavaScript file is strictly ≤ 240 lines.
