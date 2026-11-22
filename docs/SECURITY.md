# Security model

| Asset | Threat | Mitigation | Test |
|---|---|---|---|
| GROQ_API_KEY | Secret exposure | Server env only, .gitignore, secret scan | `make security` / secret grep |
| Family text | Privacy leak | No server persistence or text logging | `tests/security/*` |
| Coordinates | Personal location disclosure | Rounded cache key, no coordinate logging | `app/core/logging.py` |
| LLM output | Prompt injection or false numbers | Delimited data, strict Pydantic, number guard, retry/fallback | `tests/security/test_prompt_injection.py` |
| Public API | Abuse or proxy bypass | SlowAPI and trustable forwarded-IP configuration | `tests/security/test_real_client_ip.py` |
| Browser | Script injection | textContent, CSP, no innerHTML | `tests/a11y/test_static_markup.py` |
| Outbound hosts | SSRF/egress misuse | Fixed Open-Meteo and Groq hosts, short timeout, no redirects | service code review |

## Production headers

Responses include CSP, HSTS, no-sniff, Referrer-Policy, Permissions-Policy and Cross-Origin-Opener-Policy. API responses use `no-store`; static responses are cached.

## Reporting

Use GitHub Security Advisories or open a private report with the maintainer. Do not include secrets or real family health details.
