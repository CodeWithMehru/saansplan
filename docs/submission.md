# SaansPlan submission notes

## Changes / updates made in the deployed version

SaansPlan provides an Indian urban family exposure-budget plan using hourly Open-Meteo PM2.5/AQI data, a transparent deterministic engine and ranked low-emission swaps. It supports child/adult/elderly profiles, Hinglish/English routines, location or manual coordinates, indoor hacks, sustainable alternatives and a copyable WhatsApp summary. Groq can parse routine text and explain engine numbers, while a strict number guard and local template preserve full fallback if AI is unavailable.

## Gen AI services utilized and where

Groq is the only GenAI service. Call 1 uses the Groq OpenAI-compatible chat-completions endpoint with `openai/gpt-oss-20b` to parse untrusted Hinglish/English routine text into a strict Pydantic routine JSON. Call 2 uses only deterministic engine numbers to generate a short Hinglish/English explanation. Fixed system prompts, JSON mode, no tools, extra-field rejection, an engine-number guard, one retry and a template fallback keep AI output bounded and safe.

## 90-second demo script

**0:00–0:08 — Setup:** Open SaansPlan on the mobile-sized browser. Say that it is for an Indian urban family in winter smog.

**0:08–0:18 — Location:** Enter Delhi or use geolocation. Show the permission prompt and manual latitude/longitude fallback.

**0:18–0:28 — Family:** Add one child and one elderly member. Toggle the sensitive option.

**0:28–0:40 — Hinglish routine:** Enter the few-shot style text: “Subah 7…” and include a wood/coal heater and mostly closed windows.

**0:40–0:50 — Timeline:** Submit and show the AQI summary, peak hour and scrollable timeline/table alternative.

**0:50–1:02 — Swaps and impact:** Read the top swap before/after estimate and percentage. Scroll through indoor hacks and alternatives.

**1:02–1:12 — Fallback and sharing:** Disable or remove the Groq key, submit again and show “AI explanation unavailable” plus a useful template and full engine plan. Copy the family summary.

**1:12–1:30 — Accessibility:** Tab from the skip link through controls, switch language toggle, show visible focus and mobile/dark/reduced-motion behavior.

## LinkedIn post draft

Built SaansPlan for Hack2skill Challenge 6: an urban air-quality assistant for Indian families facing winter smog. It combines hourly Open-Meteo PM2.5/AQI data with a transparent exposure engine, child/adult/elderly profiles, Hinglish/English, indoor hacks and ranked low-emission swaps. Groq helps parse routines and explain only validated engine numbers; if Groq is unavailable, deterministic results and a template remain usable. Proud to finish with accessible vanilla UI, strict Pydantic validation, security headers, tests and a fallback-first design.

## Character counts

- Changes/updates field: **489 characters**.
- Gen AI services field: **461 characters**.
