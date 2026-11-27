/**
 * Main application coordinator: orchestrates state, API communication, accessibility, and UI rendering.
 */

import { translations } from "./i18n.js";
import { announce, initTextScale, moveToResults, showErrorSummary } from "./a11y/focus.js";
import { fetchPlan } from "./api.js";
import {
  initLanguageToggle,
  initLocationHandlers,
  initPersonaHandlers,
  initSpeechAndAssistantHandlers,
  initTextScaleHandlers,
} from "./handlers.js";
import {
  renderCleanerDay,
  renderCommunity,
  renderEmissions,
  renderForecast,
  renderIndoorModule,
  renderMembers,
  renderSwaps,
  renderTimeline,
} from "./render.js";
import {
  addMember,
  getState,
  removeMember,
  setBudgetFilter,
  setLastResult,
  updateMember,
} from "./state.js";
import { $, $$, aqiLevel, textContent } from "./utils.js";

function applyTranslations() {
  const { language } = getState();
  const t = translations[language] || translations.en;
  document.documentElement.lang =
    language === "hi" ? "hi" : language === "hinglish" ? "hi-Latn" : "en";

  $$("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (t[key]) textContent(el, t[key]);
  });

  $$("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    if (t[key]) el.placeholder = t[key];
  });

  const nextLang = language === "hi" ? "English" : language === "hinglish" ? "हिंदी" : "Hinglish";
  const toggleBtn = $("#language-toggle");
  toggleBtn.textContent = nextLang;
  toggleBtn.setAttribute("aria-label", `${nextLang} - Switch language`);
}

function refreshMembers() {
  const { family, language } = getState();
  renderMembers(
    family,
    language,
    (idx, up) => updateMember(idx, up),
    (idx) => {
      removeMember(idx);
      refreshMembers();
    }
  );
}

function buildPayload() {
  const { family, language } = getState();
  const commute = $("#commute").value;
  const outdoorMinutes = Number($("#outdoor").value);
  const routineText = $("#routine-text").value.trim();

  const activities =
    outdoorMinutes > 0
      ? [
          {
            label: "Outdoor activity",
            start_hour: 18,
            duration_min: outdoorMinutes,
            place: "outdoor",
            mode: commute === "none" ? "walk" : commute,
            intensity: "moderate",
            member_refs: family.map((_, i) => i),
          },
        ]
      : [];

  return {
    latitude: Number($("#latitude").value),
    longitude: Number($("#longitude").value),
    city: $("#city").value.trim() || null,
    members: family.map((m) => ({
      name: m.name || null,
      age_group: m.ageGroup,
      sensitive: Boolean(m.sensitive),
    })),
    routine_text: routineText,
    routine: routineText
      ? null
      : {
          activities,
          home: {
            heating: $("#heating").value,
            cooking: $("#cooking").value,
            windows: $("#windows").value,
            purifier: $("#purifier").value === "true",
            has_chimney: false,
          },
          unclear: [],
        },
    language,
  };
}

function _renderSummaryHeader(data, language) {
  $("#summary-card").hidden = false;
  textContent($("#peak-aqi"), data.exposure.peak_aqi);
  const level = aqiLevel(data.exposure.peak_aqi, language);
  textContent($("#aqi-category"), `${level.icon} ${level.text}`);
  textContent($("#explanation"), data.explanation.explanation);

  const aiNotice = $("#ai-notice");
  if (aiNotice) aiNotice.hidden = data.explanation.ai_available !== false;
}

function _filterEmissions(all, filter) {
  if (filter === "any") return all;
  return all.filter((alt) => {
    if (filter === "free") return alt.upfront_cost_inr === 0;
    if (filter === "under_500") return alt.upfront_cost_inr <= 500;
    if (filter === "under_5000") return alt.upfront_cost_inr <= 5000;
    return true;
  });
}

function _renderEmissionsSection(emissions, language) {
  if (!emissions) return;
  $("#emissions-section").hidden = false;
  renderEmissions(emissions, language, (newFilter) => {
    setBudgetFilter(newFilter);
    const filtered = _filterEmissions(emissions.all_alternatives, newFilter);
    renderEmissions(
      { ...emissions, alternatives: filtered, budget_filter: newFilter },
      language,
      () => {}
    );
  });
}

function _renderModules(data, language) {
  $("#timeline-section").hidden = false;
  renderTimeline(data.hourly, language);

  $("#swaps-section").hidden = false;
  renderSwaps(data.top_swaps || [], language);

  if (data.forecast) {
    $("#forecast-section").hidden = false;
    renderForecast(data.forecast, language);
  }
  if (data.cleaner_day) {
    $("#cleaner-day-section").hidden = false;
    renderCleanerDay(data.cleaner_day, language);
  }
  _renderEmissionsSection(data.emissions, language);
  if (data.indoor_module) {
    $("#indoor-module-section").hidden = false;
    renderIndoorModule(data.indoor_module, language);
  }
  if (data.community) {
    $("#community-section").hidden = false;
    renderCommunity(data.community, language);
  }
}

function renderResults(data) {
  const { language } = getState();
  _renderSummaryHeader(data, language);
  _renderModules(data, language);

  $("#share-section").hidden = false;
  const summary = data.community?.shareable_text || "Plan summary generated.";
  textContent($("#family-summary"), summary);
  $("#family-summary").dataset.value = summary;

  textContent(
    $("#peak-exposure-text"),
    `Highest exposure hour: ${data.exposure.peak_hour}:00 (estimate)`
  );
  textContent(
    $("#highest-aqi-text"),
    `Highest AQI hour: ${data.exposure.highest_aqi_hour}:00, Indian AQI band ${data.exposure.highest_aqi}`
  );

  moveToResults();
}

function _validateCoordinates(lat, lon) {
  const errors = [];
  if (isNaN(lat) || lat < -90 || lat > 90) {
    errors.push({ fieldId: "latitude", message: "Latitude must be between -90 and 90." });
  }
  if (isNaN(lon) || lon < -180 || lon > 180) {
    errors.push({ fieldId: "longitude", message: "Longitude must be between -180 and 180." });
  }
  return errors;
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const lat = parseFloat($("#latitude").value);
  const lon = parseFloat($("#longitude").value);
  const errors = _validateCoordinates(lat, lon);

  if (errors.length > 0) {
    showErrorSummary(errors);
    return;
  }
  showErrorSummary([]);

  const status = $("#status");
  const error = $("#error");
  textContent(error, "");
  const { language } = getState();
  textContent(status, translations[language].loading);
  $(".results").setAttribute("aria-busy", "true");
  const empty = $("#empty-state");
  if (empty) empty.hidden = true;

  try {
    const payload = buildPayload();
    const data = await fetchPlan(payload);
    textContent(status, "");
    setLastResult(data);
    renderResults(data);
  } catch (err) {
    textContent(status, "");
    textContent(error, err.message || "Unable to create plan");
    announce(`Error: ${err.message}`, "assertive");
  } finally {
    $(".results").setAttribute("aria-busy", "false");
  }
}

function initEventHandlers() {
  $(".skip-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    const main = $("#main-content");
    if (main) {
      main.focus();
      main.scrollIntoView();
    }
  });

  $("#plan-form").addEventListener("submit", handleFormSubmit);

  $("#add-member").addEventListener("click", () => {
    addMember();
    refreshMembers();
  });

  initLanguageToggle(applyTranslations, refreshMembers, renderResults);
  initPersonaHandlers(refreshMembers);
  initLocationHandlers();
  initTextScaleHandlers();
  initSpeechAndAssistantHandlers();
}

document.addEventListener("DOMContentLoaded", () => {
  const { textScale } = getState();
  initTextScale(textScale);
  applyTranslations();
  refreshMembers();
  initEventHandlers();
});
