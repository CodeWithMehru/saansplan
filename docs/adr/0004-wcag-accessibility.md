# ADR 0004: WCAG 2.2 AA Accessibility and Multilingual Inclusion

## Status
Accepted

## Context
Severe air pollution affects diverse communities across northern India, including individuals with low vision, cognitive differences, motor impairments, and language preferences across Hindi, Hinglish, and English. A public health tool must be accessible to everyone, compliant with modern accessibility standards, and usable across slow mobile devices.

## Decision
We enforce WCAG 2.2 AA compliance natively without heavy client-side frameworks:
1. **Accessible Foundations**: Semantic HTML5 elements (`<main>`, `<nav>`, `<aside>`, `<section>`, `<article>`), explicit ARIA attributes (`aria-live="polite"`, `aria-atomic="true"`), and high-contrast color palettes (contrast ratios > 7:1 for text).
2. **Reading Comfort Controls**: Built-in user preferences for font sizing, enhanced line spacing (WCAG 1.4.12), high contrast mode, and reduced motion (prefers-reduced-motion).
3. **Multilingual Inclusivity**: First-class support for English, Hinglish, and Hindi, with dynamic ARIA announcements matching the active language.
4. **Continuous Verification**: Multi-engine automated testing with Axe-core, Lighthouse, Playwright keyboard navigation audits, and static HTML linters in CI.

## Consequences
- Zero Axe-core and Lighthouse accessibility violations.
- Full keyboard operability and screen-reader compatibility across all interactive controls.
- Plain vanilla JavaScript and CSS keep the gzipped bundle under 35 KB, ensuring fast access on low-bandwidth networks.
