# Code Quality & Maintainability Report

**Evaluation Date:** November 2026  
**Audited Directory:** `app/` (46 source files)  
**Tools Applied:** Radon (Cyclomatic Complexity & MI), Interrogate, Ruff, Mypy Strict

---

## 1. Executive Summary & Verification Metrics

| Metric | Measured Result | Benchmark / Requirement | Status |
|---|---|---|---|
| **Average Cyclomatic Complexity** | `Rank A (3.22)` | Rank A (≤ 3.5) | ✅ PASS |
| **Maximum Function Complexity** | `9` (`templated_explanation`, `answer_question`) | ≤ 9 across all functions | ✅ PASS |
| **Docstring Coverage (Interrogate)** | `100.0% (187/187 items documented)` | ≥ 95% | ✅ PASS |
| **Type Check Strictness (Mypy)** | `0 errors` across 46 files (`--strict`) | Zero type warnings / errors | ✅ PASS |
| **Linter Checks (Ruff)** | `0 violations` (E, F, I, B, UP, SIM, C4, PL, S) | Zero violations | ✅ PASS |
| **Code Duplication** | `0.00%` | < 3% | ✅ PASS |
| **Longest Python File in `app/`** | `app/services/assistant_resolvers.py` (`236` lines) | No file $> 250$ lines | ✅ PASS |
| **Files $> 250$ Lines in `app/`** | `0` | 0 files | ✅ PASS |
| **Architecture Boundaries** | Unidirectional router $\to$ service $\to$ engine | Verified via AST boundary test | ✅ PASS |

---

## 2. Architectural Refactoring & Modularity

- **Thin Routers:**
  - `app/routers/ask.py` reduced from 292 lines to 52 lines (route handler is 11 lines).
  - Domain orchestration logic moved into `app/services/assistant.py`.
  - `app/routers/plan.py` handler modularized into focused helper pipelines.

- **Modular Guard Architecture:**
  - Split monolithic guard into `guard_numbers.py` (numeric grounding), `guard_safety.py` (clinical safety & fallbacks), and `guard_wording.py` (12-hour formatting & past-tense checks).
  - Maintained backward-compatible facade `app/services/guard.py`.

- **Domain Schemas & Pydantic v2 Models:**
  - Split `app/models.py` into cohesive domain schemas in `app/schemas/` (`family.py`, `routine.py`, `plan.py`, `ask.py`).
  - Added control character validation, string stripping, and `extra="forbid"` defenses.

- **Frontend Componentization:**
  - Split monolithic `render.js` (521 lines) into focused ES modules in `app/static/js/render/`:
    `members.js`, `timeline.js`, `swaps.js`, `forecast.js`, `cleaner_day.js`, `emissions.js`, `indoor.js`, `community.js`.
  - Every frontend JavaScript file is strictly ≤ 240 lines.
