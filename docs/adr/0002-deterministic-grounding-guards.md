# ADR 0002: Deterministic Grounding Guards and Safety Interception

## Status
Accepted

## Context
Generative AI models are prone to hallucinating numbers, conflating hypothetical reductions with historical occurrences, and failing to provide clinical boundary warnings when users query medical symptoms. In an air-quality context, ungrounded exposure claims or delayed medical interventions can mislead vulnerable populations (children, elderly, asthma patients).

## Decision
We mandate a three-tier deterministic guard system that wraps all LLM interactions:
1. **Number Guard (`app/services/guard_numbers.py`)**: All numerals extracted from the LLM output are checked against an explicit numerical whitelist supplied by the deterministic engine. If any ungrounded digit or unknown value is detected, the LLM response is rejected immediately.
2. **Wording Guard (`app/services/guard_wording.py`)**: All past-tense claims ("dropped", "kam hua", "reduced by") are forbidden for hypothetical routines. The guard enforces future/hypothetical phrasing ("could reduce by ~27% (estimate)").
3. **Safety Guard (`app/services/guard_safety.py`)**: High-risk clinical symptoms (e.g., chest pain, severe breathlessness, hemoptysis) deterministically bypass the LLM and return an immediate doctor referral notice with emergency guidance.
4. **Instant Template Fallback**: Any rejection by the guards or upstream failure from Groq triggers a 0 ms fallback to deterministic, pre-computed template guidance (`app/services/llm.py`), ensuring high availability (`ai_available=False`).

## Consequences
- Hallucinated dosages or ungrounded statistics cannot reach the end user.
- Clinical symptoms receive immediate, safe, deterministic triage guidance.
- System availability remains 100% even during Groq outages, rate limits (HTTP 429), or network partitions.
