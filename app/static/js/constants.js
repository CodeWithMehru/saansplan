/**
 * Application constants: centralized API endpoints, storage keys,
 * supported locales, CPCB thresholds, and default values.
 *
 * @module constants
 */

/**
 * REST API Endpoints used by the frontend.
 * @readonly
 * @enum {string}
 */
export const API_ENDPOINTS = Object.freeze({
  PLAN: "/api/plan",
  GEOCODE: "/api/geocode",
  ASK: "/api/ask",
  HEALTH: "/health",
});

/**
 * LocalStorage keys for persisting user preferences and session data.
 * @readonly
 * @enum {string}
 */
export const STORAGE_KEYS = Object.freeze({
  LANGUAGE: "saansplan-language",
  FAMILY: "saansplan-family",
  TEXT_SCALE: "saansplan-text-scale",
  BUDGET: "saansplan-budget",
});

/**
 * Supported UI language codes.
 * @readonly
 */
export const SUPPORTED_LANGUAGES = Object.freeze(["en", "hinglish", "hi"]);

/**
 * Default fallback language.
 * @type {string}
 */
export const DEFAULT_LANGUAGE = "en";

/**
 * CPCB Indian Air Quality Index category thresholds and display metadata.
 * @readonly
 */
export const AQI_THRESHOLDS = Object.freeze([
  { max: 50, level: "good", text: "Good (CPCB)", icon: "●", slug: "good" },
  { max: 100, level: "satisfactory", text: "Satisfactory (CPCB)", icon: "●", slug: "satisfactory" },
  { max: 200, level: "moderate", text: "Moderate (CPCB)", icon: "◆", slug: "moderate" },
  { max: 300, level: "poor", text: "Poor (CPCB)", icon: "▲", slug: "poor" },
  { max: 400, level: "very-poor", text: "Very Poor (CPCB)", icon: "▲", slug: "very-poor" },
]);

/**
 * Fallback severe level for AQI exceeding 400.
 * @readonly
 */
export const SEVERE_AQI_LEVEL = Object.freeze({
  level: "severe",
  text: "Severe (CPCB)",
  icon: "■",
  slug: "severe",
});

/**
 * Default geographic coordinates (New Delhi, India).
 * @readonly
 */
export const DEFAULT_COORDINATES = Object.freeze({
  CITY: "New Delhi",
  LATITUDE: 28.6139,
  LONGITUDE: 77.209,
});

/**
 * Network timeout for API requests in milliseconds.
 * @type {number}
 */
export const API_TIMEOUT_MS = 14000;
