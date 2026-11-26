/**
 * API client module: handles network requests, timeouts, and structured error responses.
 *
 * @module api
 */

import { API_ENDPOINTS, API_TIMEOUT_MS } from "./constants.js";

/**
 * Submit plan parameters to generate air quality routines and swap recommendations.
 *
 * @param {object} payload - Plan request payload (coordinates, members, routine, language).
 * @returns {Promise<any>} Parsed response data containing plan results.
 * @throws {Error} When request fails or server returns error status.
 */
export async function fetchPlan(payload) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    const response = await fetch(API_ENDPOINTS.PLAN, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data.error?.message || data.detail || "Unable to generate plan";
      throw new Error(msg);
    }
    return data;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Search geocoding database for Indian city coordinates.
 *
 * @param {string} city - City name or partial query.
 * @returns {Promise<Array<{name: string, latitude: number, longitude: number, state?: string, admin1?: string, country?: string}>>} List of matching locations.
 * @throws {Error} When network request fails.
 */
export async function fetchGeocode(city) {
  const response = await fetch(`${API_ENDPOINTS.GEOCODE}?name=${encodeURIComponent(city)}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "City search failed");
  }
  return data.results || [];
}

/**
 * Ask assistant grounded air quality and health guidance question.
 *
 * @param {string} question - Free-form user query.
 * @returns {Promise<string>} Grounded answer text.
 * @throws {Error} When request fails.
 */
export async function askAssistant(question) {
  const response = await fetch(API_ENDPOINTS.ASK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Could not answer this question.");
  }
  return data.answer;
}
