# SaansPlan submission notes

## Changes / updates made in the deployed version

SaansPlan provides an Indian urban family exposure-budget plan using hourly Open-Meteo PM2.5/AQI data, physical-unit planning estimates and ranked low-emission swaps. It supports child/adult/elderly profiles, English/Hinglish/Hindi, location search or manual coordinates, indoor/commute alternatives, a rich shareable family summary and a grounded Ask SaansPlan fallback. Groq can parse routines and explain engine numbers, while strict validation and templates preserve a useful plan if AI is unavailable. The app includes text-size controls, accessible tables, proxy-aware rate limits and a 90% overall coverage gate.

## Gen AI services utilized and where

Groq is the only GenAI service. Call 1 parses untrusted English/Hinglish/Hindi routine text into strict Pydantic JSON through the Groq OpenAI-compatible endpoint using `openai/gpt-oss-20b`. Call 2 explains only a compact whitelist of engine facts with one retry and deterministic fallback. The grounded Ask SaansPlan route uses a verified-source knowledge base plus fixed safety prompts and refusals; it has no tools, cannot reveal keys or diagnose, and falls back to KB text when Groq is unavailable. Strict JSON, number/KB guards and template fallbacks keep output bounded.

## 90-second demo script

**0:00–0:08 — Setup:** Open SaansPlan on the mobile-sized browser. Say that it is for an Indian urban family in winter smog.

**0:08–0:18 — Location:** Enter Delhi or use geolocation. Show the permission prompt and manual latitude/longitude fallback.

**0:18–0:28 — Family:** Add one child and one elderly member. Toggle the sensitive option.

**0:28–0:40 — Hinglish routine:** Enter the few-shot style text: “Subah 7…” and include a wood/coal heater and mostly closed windows.

**0:40–0:50 — Timeline:** Submit and show the hourly table, Indian AQI interpretation caveat and separate highest-AQI/hour and exposure/hour details.

**0:50–1:02 — Actions and Ask:** Read top human-readable swaps and indoor options, then ask a short grounded air-quality question.

**1:02–1:12 — Fallback and sharing:** Disable Groq or use the template fallback, copy the richer family/WhatsApp summary and switch languages.

**1:12–1:30 — Accessibility:** Tab through controls, switch Hindi/Hinglish/English, use text-size controls and show mobile/reduced-motion behavior.

## LinkedIn post draft

Built SaansPlan for Hack2skill Challenge 6: an urban air-quality assistant for Indian families facing winter smog. It combines hourly Open-Meteo PM2.5/AQI data with a transparent exposure engine, child/adult/elderly profiles, Hinglish/English, indoor hacks and ranked low-emission swaps. Groq helps parse routines and explain only validated engine numbers; if Groq is unavailable, deterministic results and a template remain usable. Proud to finish with accessible vanilla UI, strict Pydantic validation, security headers, tests and a fallback-first design.

## Character counts

- Changes/updates field: **619 characters**.
- Gen AI services field: **575 characters**.
