# Security Architecture & Threat Model

SaansPlan processes urban air quality data and sensitive household routines. Our defense-in-depth security model ensures user privacy, zero credential exposure, strict sandboxing against prompt injections, and resilient defense against abuse.

---

## 1. Threat Model Matrix

| Asset | Threat | Mitigation | Proving Test / Verification |
|---|---|---|---|
| **`GROQ_API_KEY`** | Secret leakage in logs, git, or client response | Pinned in server `.env` (gitignored); never sent to client; redacted from logging; verified in pre-commit and CI | `tests/test_security.py::test_api_key_not_exposed`, `git status`, `bandit -q -r app` |
| **User Routine Text** | Privacy leak / PII persistence | Zero server persistence (stateless FastAPI); routine text is never written to disk or logs; logged payloads contain only request IDs and lat/lon rounded to 2 decimal places | `tests/security/test_prompt_injection.py`, `app/core/logging.py` |
| **User Location (Coordinates)** | Exact home location tracking | Coordinates are rounded to 2 decimal places for cache keys (~1.1 km resolution); IP addresses are hashed for rate limiting | `tests/security/test_real_client_ip.py`, `app/services/air_quality.py` |
| **LLM Output & Medical Advice** | Hallucinations, dangerous medical guidance, or ungrounded claims | Deterministic guard (`app/services/guard.py`) intercepts medical symptoms and triggers safe doctor redirect; all physical numbers computed by verified deterministic engines | `tests/security/test_prompt_injection.py::test_medical_advice_redirect`, `tests/test_guard.py` |
| **Prompt Injection Attacks** | Jailbreaks, prompt leaking, or system prompt overrides | XML data demarcation (`<user_routine>`), system prompt locking, and strict Pydantic JSON schema output enforcement | `tests/security/test_prompt_injection.py` (25 multi-lingual attacks in EN, Hinglish, HI) |
| **API Endpoints (DoS / Abuse)** | Endpoint spamming, brute-force requests | SlowAPI rate limiting (30 req/min); proxy-aware real client IP extraction (`X-Forwarded-For` with trusted proxy validation) | `tests/security/test_real_client_ip.py`, `tests/api/test_plan_endpoint.py` |
| **Browser Execution (XSS)** | Cross-Site Scripting, DOM injection | Zero `innerHTML` for user content; all DOM insertions use `textContent` or `createElement`; strict Content Security Policy | `tests/a11y/test_static_markup.py`, `tests/test_geocode_and_csp.py`, `scripts/a11y.py` |
| **Server-Side Request Forgery (SSRF)** | Arbitrary outbound network requests | Outbound client restricted strictly to verified endpoints (`api.open-meteo.com`, `geocoding-api.open-meteo.com`, `api.groq.com`); no redirects allowed; 10s strict timeout | `app/services/air_quality.py`, `app/routers/geocode.py`, `tests/test_air_quality.py` |
| **Dependencies & Supply Chain** | Known CVEs in Python packages | Pinned versions, automated Dependabot alerts, regular `pip-audit` scans, and Bandit static AST analysis in CI | `make security` (`pip-audit -r requirements.txt`, `bandit -q -r app`) |

---

## 2. Production HTTP Security Headers

Every HTTP response dispatched by `app/main.py` enforces modern defensive headers:

```http
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(self), camera=(), microphone=()
Strict-Transport-Security: max-age=31536000; includeSubDomains
Cross-Origin-Opener-Policy: same-origin
Cache-Control: no-store (for API responses)
```

- **Strict CSP:** Scripts and styles are restricted strictly to `'self'`. No `unsafe-inline`, no `unsafe-eval`, and no external third-party CDN scripts.
- **Request Size Guard:** Payloads exceeding 64 KB (`MAX_REQUEST_BYTES`) are terminated immediately with HTTP 413.

---

## 3. Vulnerability Reporting

Please report security issues responsibly via GitHub Security Advisories or by creating a private report with the project maintainer. Do not publish reproducible exploit code or private credentials in public issues.
