/**
 * State management module: tracks user preferences, family members, and last API results.
 */

const STORAGE_KEYS = {
  LANGUAGE: 'saansplan-language',
  FAMILY: 'saansplan-family',
  TEXT_SCALE: 'saansplan-text-scale',
  BUDGET: 'saansplan-budget',
};

const state = {
  language: localStorage.getItem(STORAGE_KEYS.LANGUAGE) || 'en',
  family: JSON.parse(localStorage.getItem(STORAGE_KEYS.FAMILY) || 'null') || [
    { name: '', ageGroup: 'adult', sensitive: false },
  ],
  textScale: Number(localStorage.getItem(STORAGE_KEYS.TEXT_SCALE) || 100),
  budgetFilter: localStorage.getItem(STORAGE_KEYS.BUDGET) || 'any',
  lastResult: null,
};

export function getState() {
  return state;
}

export function setLanguage(lang) {
  state.language = lang;
  localStorage.setItem(STORAGE_KEYS.LANGUAGE, lang);
}

export function setTextScale(scale) {
  state.textScale = scale;
  localStorage.setItem(STORAGE_KEYS.TEXT_SCALE, String(scale));
}

export function setBudgetFilter(filter) {
  state.budgetFilter = filter;
  localStorage.setItem(STORAGE_KEYS.BUDGET, filter);
}

export function setLastResult(result) {
  state.lastResult = result;
}

export function saveFamily() {
  localStorage.setItem(STORAGE_KEYS.FAMILY, JSON.stringify(state.family));
}

export function addMember(name = '', ageGroup = 'adult', sensitive = false) {
  if (state.family.length < 12) {
    state.family.push({ name, ageGroup, sensitive });
    saveFamily();
  }
}

export function removeMember(index) {
  if (state.family.length > 1) {
    state.family.splice(index, 1);
    saveFamily();
  }
}

export function updateMember(index, updates) {
  if (state.family[index]) {
    Object.assign(state.family[index], updates);
    saveFamily();
  }
}

export const DEFAULT_PERSONAS = {
  working_parents: {
    id: 'working_parents',
    name: 'Working Parents & School Children',
    description: 'Busy family with morning school drop-off and daily office transit.',
    members: [
      { name: 'Parent 1', ageGroup: 'adult', sensitive: false },
      { name: 'Child', ageGroup: 'child', sensitive: true },
    ],
    routine_text:
      'Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, shaam 6 baje park walk.',
    commute: 'metro',
    outdoor_minutes: 60,
    cooking: 'lpg',
    heating: 'none',
    windows: 'mostly_closed',
    purifier: false,
    budget: 'under_5000',
  },
  elderly_home: {
    id: 'elderly_home',
    name: 'Senior Citizen / Elderly at Home',
    description: 'Retired grandparents with respiratory sensitivity and high indoor hours.',
    members: [
      { name: 'Grandparent', ageGroup: 'elderly', sensitive: true },
      { name: 'Caregiver', ageGroup: 'adult', sensitive: false },
    ],
    routine_text:
      'Dada ji din bhar ghar pe rehte hain, subah balcony me baithte hain, thand me heating zaroori hai.',
    commute: 'none',
    outdoor_minutes: 30,
    cooking: 'induction',
    heating: 'electric',
    windows: 'mostly_closed',
    purifier: true,
    budget: 'under_5000',
  },
  student_hostel: {
    id: 'student_hostel',
    name: 'Student / Hostel Resident',
    description: 'University student walking between hostel, library, and campus mess.',
    members: [{ name: 'Student', ageGroup: 'adult', sensitive: false }],
    routine_text:
      'College campus me subah 8 baje class ke liye walk karta hoon, shaam ko library se hostel.',
    commute: 'walk',
    outdoor_minutes: 60,
    cooking: 'induction',
    heating: 'none',
    windows: 'mostly_closed',
    purifier: false,
    budget: 'under_500',
  },
  outdoor_worker: {
    id: 'outdoor_worker',
    name: 'Outdoor Worker / Delivery Rider',
    description: 'Gig delivery partner or outdoor worker with 6+ hours street exposure.',
    members: [{ name: 'Rider', ageGroup: 'adult', sensitive: false }],
    routine_text:
      'Subah 10 baje se shaam 6 baje tak bike pe deliveries karta hoon busy roads pe.',
    commute: 'bike',
    outdoor_minutes: 120,
    cooking: 'lpg',
    heating: 'none',
    windows: 'mostly_closed',
    purifier: false,
    budget: 'under_500',
  },
};

export function applyPersona(preset) {
  if (!preset) return;
  state.family = preset.members.map((m) => ({
    name: m.name || '',
    ageGroup: m.ageGroup || 'adult',
    sensitive: Boolean(m.sensitive),
  }));
  saveFamily();
}
