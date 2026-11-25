/**
 * Utility functions: DOM helpers, CPCB AQI categories, and F10 human titles in 3 languages.
 */

export const $ = (selector) => document.querySelector(selector);
export const $$ = (selector) => document.querySelectorAll(selector);

export function textContent(element, value) {
  if (element) element.textContent = String(value);
}

const AQI_THRESHOLDS = [
  { max: 50, level: "good", text: "Good (CPCB)", icon: "●", slug: "good" },
  { max: 100, level: "satisfactory", text: "Satisfactory (CPCB)", icon: "●", slug: "satisfactory" },
  { max: 200, level: "moderate", text: "Moderate (CPCB)", icon: "◆", slug: "moderate" },
  { max: 300, level: "poor", text: "Poor (CPCB)", icon: "▲", slug: "poor" },
  { max: 400, level: "very-poor", text: "Very Poor (CPCB)", icon: "▲", slug: "very-poor" },
];

export function aqiLevel(aqi, _language = "en") {
  const num = Number(aqi) || 0;
  for (const t of AQI_THRESHOLDS) {
    if (num <= t.max) return t;
  }
  return { level: "severe", text: "Severe (CPCB)", icon: "■", slug: "severe" };
}

// F10: Comprehensive Human Titles in English, Hinglish, and Hindi
const HUMAN_TITLES = {
  swap_shift: {
    en: "Shift outdoor activity to a cleaner hour",
    hinglish: "Outdoor walk/activity ko saaf ghante me shift karein",
    hi: "बाहरी गतिविधि को स्वच्छ समय पर स्थानांतरित करें",
  },
  shift_activity: {
    en: "Shift outdoor activity to a cleaner hour",
    hinglish: "Outdoor walk/activity ko saaf ghante me shift karein",
    hi: "बाहरी गतिविधि को स्वच्छ समय पर स्थानांतरित करें",
  },
  swap_windows: {
    en: "Keep windows closed during smog peaks",
    hinglish: "Pradooshan ke peak ghanton me khidkiyan band rakhein",
    hi: "प्रदूषण के चरम समय खिड़कियां बंद रखें",
  },
  close_windows: {
    en: "Keep windows closed during smog peaks",
    hinglish: "Pradooshan ke peak ghanton me khidkiyan band rakhein",
    hi: "प्रदूषण के चरम समय खिड़कियां बंद रखें",
  },
  swap_purifier: {
    en: "Run a certified HEPA air purifier",
    hinglish: "Ghar par certified HEPA purifier chalayein",
    hi: "प्रमाणित HEPA एयर प्यूरीफायर चलाएं",
  },
  run_purifier: {
    en: "Run a certified HEPA air purifier",
    hinglish: "Ghar par certified HEPA purifier chalayein",
    hi: "प्रमाणित HEPA एयर प्यूरीफायर चलाएं",
  },
  swap_cooking: {
    en: "Switch from smoky fuel to induction cooking",
    hinglish: "Dhuwen wale indhan ki jagah induction use karein",
    hi: "धुएं वाले ईंधन के स्थान पर इंडक्शन अपनाएं",
  },
  cook_induction: {
    en: "Switch from smoky fuel to induction cooking",
    hinglish: "Dhuwen wale indhan ki jagah induction use karein",
    hi: "धुएं वाले ईंधन के स्थान पर इंडक्शन अपनाएं",
  },
  purifier: {
    en: "HEPA Air Purifier in Main Rooms",
    hinglish: "Mukhya kamron me HEPA Air Purifier",
    hi: "मुख्य कमरों में HEPA एयर प्यूरीफायर",
  },
  closed_windows: {
    en: "Seal gaps and close windows during smog",
    hinglish: "Smog ke dauran khidkiyan band rakhein",
    hi: "स्मॉग के समय खिड़कियां बंद रखें",
  },
  box_fan_filter: {
    en: "DIY Box-Fan Filter with MERV 13",
    hinglish: "MERV 13 filter ke sath DIY Box-Fan",
    hi: "MERV 13 फिल्टर के साथ DIY बॉक्स-फैन",
  },
  chimney: {
    en: "Exhaust Fan & Chimney Ventilation",
    hinglish: "Exhaust fan aur chimney chalayein",
    hi: "रसोई में एग्जॉस्ट फैन और चिमनी चलाएं",
  },
  mask: {
    en: "Tight-fitting certified N95/FFP2 respirator",
    hinglish: "Acche se fit N95/FFP2 mask pehnein",
    hi: "चेहरे पर सही बैठने वाला N95/FFP2 मास्क पहनें",
  },
  metro_bus: {
    en: "Electric Metro or Shared Public Bus",
    hinglish: "Electric Metro ya Public Bus se safar karein",
    hi: "इलेक्ट्रिक मेट्रो या साझा सार्वजनिक बस",
  },
  walk_cycle: {
    en: "Walking or cycling in cleaner midday hours",
    hinglish: "Saaf dopahar ke samay walk ya cycle karein",
    hi: "स्वच्छ दोपहर के समय पैदल या साइकिल यात्रा",
  },
  induction: {
    en: "Electric induction cooktop",
    hinglish: "Electric induction cooktop",
    hi: "इलेक्ट्रिक इंडक्शन चूल्हा",
  },
  insulation: {
    en: "Thermal curtains and gap sealing",
    hinglish: "Thermal curtains aur darwazon ki sealing",
    hi: "थर्मल पर्दे और दरवाजों की सीलिंग",
  },
};

export function getHumanLabel(key, language = "en") {
  if (!key) return "Cleaner daily action";
  const cleanKey = String(key).toLowerCase().trim();
  const entry = HUMAN_TITLES[cleanKey];
  if (entry && entry[language]) {
    return entry[language];
  }
  if (entry && entry.en) {
    return entry.en;
  }
  // Safe human-readable fallback: NEVER return a raw snake_case identifier
  return cleanKey
    .replace(/^swap_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
