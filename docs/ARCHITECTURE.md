# System Architecture

## Overview

SaansPlan is an urban air quality assistant built with FastAPI, vanilla ECMAScript modules, and a pure deterministic mathematical engine. It provides family-tailored low-emission daily routines, indoor air quality hacks, and sustainable alternatives with clear impact explanations.

```mermaid
flowchart TD
    subgraph Client["Client Tier (Vanilla ES / HTML5)"]
        UI["app/static/index.html"]
        APP["app/static/js/app.js"]
        HANDLERS["app/static/js/handlers.js"]
        RENDER["app/static/js/render/*.js"]
    end

    subgraph API["API & Routing Tier (FastAPI)"]
        MAIN["app/main.py"]
        R_PLAN["app/routers/plan.py"]
        R_ASK["app/routers/ask.py"]
        R_GEO["app/routers/geocode.py"]
        R_HEALTH["app/routers/health.py"]
    end

    subgraph Services["Service Tier"]
        SVC_ASSIST["app/services/assistant.py"]
        SVC_RESOLV["app/services/assistant_resolvers.py"]
        SVC_AQ["app/services/air_quality.py"]
        SVC_GUARD["app/services/guard*.py"]
        SVC_LLM["app/services/llm.py"]
        SVC_KB["app/services/kb.py"]
    end

    subgraph Engine["Deterministic Engine (Zero I/O)"]
        ENG_EXP["app/engine/exposure.py"]
        ENG_CLN["app/engine/cleaner_day.py"]
        ENG_SWP["app/engine/swaps.py"]
        ENG_EMI["app/engine/emissions.py"]
        ENG_FC["app/engine/forecast.py"]
        ENG_IND["app/engine/indoor_*.py"]
        ENG_INH["app/engine/inhaled.py"]
    end

    subgraph Schemas["Domain Schemas (Pydantic v2)"]
        SCH_FAM["app/schemas/family.py"]
        SCH_ROU["app/schemas/routine.py"]
        SCH_PLN["app/schemas/plan.py"]
        SCH_ASK["app/schemas/ask.py"]
    end

    subgraph External["External Services"]
        OPEN_METEO["Open-Meteo Air Quality & Geocoding API"]
        GROQ["Groq LLM (openai/gpt-oss-20b)"]
    end

    UI --> APP
    APP --> HANDLERS
    HANDLERS --> RENDER
    APP -- "JSON REST" --> MAIN
    MAIN --> R_PLAN & R_ASK & R_GEO & R_HEALTH

    R_PLAN --> SVC_AQ & SVC_GUARD & SVC_LLM & Engine
    R_ASK --> SVC_ASSIST
    SVC_ASSIST --> SVC_AQ & SVC_KB & SVC_LLM & Engine

    R_PLAN & R_ASK & SVC_ASSIST --> Schemas
    Engine --> Schemas

    SVC_AQ --> OPEN_METEO
    SVC_LLM --> GROQ
```

## Architectural Principles & Boundaries

1. **Unidirectional Dependency Invariant:**
   - Routers depend on Services, Schemas, and the Engine.
   - Services orchestrate I/O and external clients.
   - Engine modules are **strictly pure and deterministic**: zero network calls, zero file system I/O, zero random numbers, and zero imports from routers or external clients.
   - Schemas are self-contained data models with input sanitization.
   - Verified continuously via AST analysis in `tests/unit/test_architecture_boundaries.py`.

2. **Thin Routers & Modular Services:**
   - Routers perform request validation, route dispatching, and HTTP response mapping.
   - Business orchestration logic resides in specialized services (`app/services/assistant.py`, `app/services/guard_numbers.py`, `app/services/guard_safety.py`, `app/services/guard_wording.py`).

3. **Deterministic Fallbacks:**
   - LLM generation is strictly guarded. If Groq is unavailable, rate-limited, returns malformed text, violates clinical safety criteria, uses prohibited past-tense wording, or invents numeric values, the system seamlessly returns verified deterministic templates with zero downtime (`ai_available=false`).

4. **Hermetic & Offline-Capable Testing:**
   - The entire core test suite executes hermetically without requiring external network access or API secrets.
