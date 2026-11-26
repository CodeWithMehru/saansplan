/**
 * State management module: tracks user preferences, family members, and last API results.
 *
 * @module state
 */

import { DEFAULT_LANGUAGE, STORAGE_KEYS } from "./constants.js";

/**
 * Application state store.
 * @type {{
 *   language: string,
 *   family: Array<{name: string, ageGroup: string, sensitive: boolean}>,
 *   textScale: number,
 *   budgetFilter: string,
 *   lastResult: object | null
 * }}
 */
const state = {
  language: localStorage.getItem(STORAGE_KEYS.LANGUAGE) || DEFAULT_LANGUAGE,
  family: JSON.parse(localStorage.getItem(STORAGE_KEYS.FAMILY) || "null") || [
    { name: "", ageGroup: "adult", sensitive: false },
  ],
  textScale: Number(localStorage.getItem(STORAGE_KEYS.TEXT_SCALE) || 100),
  budgetFilter: localStorage.getItem(STORAGE_KEYS.BUDGET) || "any",
  lastResult: null,
};

/**
 * Get current application state snapshot.
 * @returns {typeof state} Current state object.
 */
export function getState() {
  return state;
}

/**
 * Set and persist active language code.
 * @param {string} lang - Language code ('en', 'hinglish', 'hi').
 */
export function setLanguage(lang) {
  state.language = lang;
  localStorage.setItem(STORAGE_KEYS.LANGUAGE, lang);
}

/**
 * Set and persist user text display scale percentage.
 * @param {number} scale - Text scale percentage (e.g. 90, 100, 110).
 */
export function setTextScale(scale) {
  state.textScale = scale;
  localStorage.setItem(STORAGE_KEYS.TEXT_SCALE, String(scale));
}

/**
 * Set and persist active budget filter tier.
 * @param {string} filter - Budget tier identifier ('any', 'zero_cost', 'under_500', 'under_5000').
 */
export function setBudgetFilter(filter) {
  state.budgetFilter = filter;
  localStorage.setItem(STORAGE_KEYS.BUDGET, filter);
}

/**
 * Store the most recent plan API response.
 * @param {object | null} result - Plan result object or null.
 */
export function setLastResult(result) {
  state.lastResult = result;
}

/**
 * Persist current family members array to LocalStorage.
 */
export function saveFamily() {
  localStorage.setItem(STORAGE_KEYS.FAMILY, JSON.stringify(state.family));
}

/**
 * Add a new family member to state (up to 12 members).
 * @param {string} [name=""] - Optional member name or label.
 * @param {string} [ageGroup="adult"] - Age category ('child', 'adult', 'elderly').
 * @param {boolean} [sensitive=false] - Whether member has respiratory sensitivity.
 */
export function addMember(name = "", ageGroup = "adult", sensitive = false) {
  if (state.family.length < 12) {
    state.family.push({ name, ageGroup, sensitive });
    saveFamily();
  }
}

/**
 * Remove family member at specified index (minimum 1 member retained).
 * @param {number} index - Array index to remove.
 */
export function removeMember(index) {
  if (state.family.length > 1) {
    state.family.splice(index, 1);
    saveFamily();
  }
}

/**
 * Update attributes of family member at specified index.
 * @param {number} index - Array index to update.
 * @param {Partial<{name: string, ageGroup: string, sensitive: boolean}>} updates - Property updates.
 */
export function updateMember(index, updates) {
  if (state.family[index]) {
    Object.assign(state.family[index], updates);
    saveFamily();
  }
}

/**
 * Pre-defined demographic household personas for 1-click loading.
 * @readonly
 */
export const DEFAULT_PERSONAS = {
  working_parents: {
    id: "working_parents",
    name: "Working Parents & School Children",
    description: "Busy family with morning school drop-off and daily office transit.",
    members: [
      { name: "Parent 1", ageGroup: "adult", sensitive: false },
      { name: "Child", ageGroup: "child", sensitive: true },
    ],
    routine_text:
      "Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, shaam 6 baje park walk.",
    commute: "metro",
    outdoor_minutes: 60,
    cooking: "lpg",
    heating: "none",
    windows: "mostly_closed",
    purifier: false,
    budget: "under_5000",
  },
  elderly_home: {
    id: "elderly_home",
    name: "Senior Citizen / Elderly at Home",
    description: "Retired grandparents with respiratory sensitivity and high indoor hours.",
    members: [
      { name: "Grandparent", ageGroup: "elderly", sensitive: true },
      { name: "Caregiver", ageGroup: "adult", sensitive: false },
    ],
    routine_text:
      "Dada ji din bhar ghar pe rehte hain, subah balcony me baithte hain, thand me heating zaroori hai.",
    commute: "none",
    outdoor_minutes: 30,
    cooking: "induction",
    heating: "electric",
    windows: "mostly_closed",
    purifier: true,
    budget: "under_5000",
  },
  student_hostel: {
    id: "student_hostel",
    name: "Student / Hostel Resident",
    description: "University student walking between hostel, library, and campus mess.",
    members: [{ name: "Student", ageGroup: "adult", sensitive: false }],
    routine_text:
      "College campus me subah 8 baje class ke liye walk karta hoon, shaam ko library se hostel.",
    commute: "walk",
    outdoor_minutes: 60,
    cooking: "induction",
    heating: "none",
    windows: "mostly_closed",
    purifier: false,
    budget: "under_500",
  },
  outdoor_worker: {
    id: "outdoor_worker",
    name: "Outdoor Worker / Delivery Rider",
    description: "Gig delivery partner or outdoor worker with 6+ hours street exposure.",
    members: [{ name: "Rider", ageGroup: "adult", sensitive: false }],
    routine_text: "Subah 10 baje se shaam 6 baje tak bike pe deliveries karta hoon busy roads pe.",
    commute: "bike",
    outdoor_minutes: 120,
    cooking: "lpg",
    heating: "none",
    windows: "mostly_closed",
    purifier: false,
    budget: "under_500",
  },
};

/**
 * Apply persona preset to family members state.
 * @param {{members: Array<{name?: string, ageGroup?: string, sensitive?: boolean}>} | null} preset - Selected persona.
 */
export function applyPersona(preset) {
  if (!preset) return;
  state.family = preset.members.map((m) => ({
    name: m.name || "",
    ageGroup: m.ageGroup || "adult",
    sensitive: Boolean(m.sensitive),
  }));
  saveFamily();
}
