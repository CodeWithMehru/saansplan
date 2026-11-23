/**
 * Main application coordinator: orchestrates state, API communication, accessibility, and UI rendering.
 */

import { translations } from '../i18n.js';
import { announce, initTextScale, moveToResults, showErrorSummary } from './a11y/focus.js';
import { askAssistant, fetchGeocode, fetchPlan } from './api.js';
import {
  renderCleanerDay,
  renderCommunity,
  renderEmissions,
  renderForecast,
  renderIndoorModule,
  renderMembers,
  renderSwaps,
  renderTimeline,
} from './render.js';
import { isSpeechRecognitionSupported, isSpeechSynthesisSupported, speakText, startVoiceRecognition } from './speech.js';
import {
  DEFAULT_PERSONAS,
  addMember,
  applyPersona,
  getState,
  removeMember,
  setBudgetFilter,
  setLanguage,
  setLastResult,
  setTextScale,
  updateMember,
} from './state.js';
import { $, $$, aqiLevel, textContent } from './utils.js';

function applyTranslations() {
  const { language } = getState();
  const t = translations[language] || translations.en;
  document.documentElement.lang = language === 'hi' ? 'hi' : language === 'hinglish' ? 'hi-Latn' : 'en';

  $$('[data-i18n]').forEach((el) => {
    const key = el.dataset.i18n;
    if (t[key]) textContent(el, t[key]);
  });

  $$('[data-i18n-placeholder]').forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    if (t[key]) el.placeholder = t[key];
  });

  const nextLang = language === 'hi' ? 'English' : language === 'hinglish' ? 'हिंदी' : 'Hinglish';
  const toggleBtn = $('#language-toggle');
  toggleBtn.textContent = nextLang;
  toggleBtn.setAttribute('aria-label', `${nextLang} - Switch language`);
}

function refreshMembers() {
  const { family, language } = getState();
  renderMembers(
    family,
    language,
    (index, updates) => {
      updateMember(index, updates);
    },
    (index) => {
      removeMember(index);
      refreshMembers();
    }
  );
}

function buildPayload() {
  const { family, language } = getState();
  const commute = $('#commute').value;
  const outdoorMinutes = Number($('#outdoor').value);
  const routineText = $('#routine-text').value.trim();

  const activities = [];
  if (outdoorMinutes > 0) {
    activities.push({
      label: 'Outdoor activity',
      start_hour: 18,
      duration_min: outdoorMinutes,
      place: 'outdoor',
      mode: commute === 'none' ? 'walk' : commute,
      intensity: 'moderate',
      member_refs: family.map((_, i) => i),
    });
  }

  return {
    latitude: Number($('#latitude').value),
    longitude: Number($('#longitude').value),
    city: $('#city').value.trim() || null,
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
            heating: $('#heating').value,
            cooking: $('#cooking').value,
            windows: $('#windows').value,
            purifier: $('#purifier').value === 'true',
            has_chimney: false,
          },
          unclear: [],
        },
    language,
  };
}

function renderResults(data) {
  const { language, budgetFilter } = getState();
  const t = translations[language] || translations.en;

  $('#summary-card').hidden = false;
  textContent($('#peak-aqi'), data.exposure.peak_aqi);
  const level = aqiLevel(data.exposure.peak_aqi, language);
  textContent($('#aqi-category'), `${level.icon} ${level.text}`);
  textContent($('#explanation'), data.explanation.explanation);

  const aiNotice = $('#ai-notice');
  if (aiNotice) aiNotice.hidden = data.explanation.ai_available !== false;

  $('#timeline-section').hidden = false;
  renderTimeline(data.hourly, language);

  $('#swaps-section').hidden = false;
  renderSwaps(data.top_swaps || [], language);

  if (data.forecast) {
    $('#forecast-section').hidden = false;
    renderForecast(data.forecast, language);
  }

  if (data.cleaner_day) {
    $('#cleaner-day-section').hidden = false;
    renderCleanerDay(data.cleaner_day, language);
  }

  if (data.emissions) {
    $('#emissions-section').hidden = false;
    renderEmissions(data.emissions, language, (newFilter) => {
      setBudgetFilter(newFilter);
      // Re-filter locally
      const filtered = newFilter === 'any'
        ? data.emissions.all_alternatives
        : data.emissions.all_alternatives.filter((alt) => {
            if (newFilter === 'free') return alt.upfront_cost_inr === 0;
            if (newFilter === 'under_500') return alt.upfront_cost_inr <= 500;
            if (newFilter === 'under_5000') return alt.upfront_cost_inr <= 5000;
            return true;
          });
      renderEmissions({ ...data.emissions, alternatives: filtered, budget_filter: newFilter }, language, () => {});
    });
  }

  if (data.indoor_module) {
    $('#indoor-module-section').hidden = false;
    renderIndoorModule(data.indoor_module, language);
  }

  if (data.community) {
    $('#community-section').hidden = false;
    renderCommunity(data.community, language);
  }

  $('#share-section').hidden = false;
  const summary = data.community?.shareable_text || 'Plan summary generated.';
  textContent($('#family-summary'), summary);
  $('#family-summary').dataset.value = summary;

  textContent($('#peak-exposure-text'), `Highest exposure hour: ${data.exposure.peak_hour}:00 (estimate)`);
  textContent($('#highest-aqi-text'), `Highest AQI hour: ${data.exposure.highest_aqi_hour}:00, Indian AQI band ${data.exposure.highest_aqi}`);

  moveToResults();
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const errors = [];
  const lat = parseFloat($('#latitude').value);
  const lon = parseFloat($('#longitude').value);

  if (isNaN(lat) || lat < -90 || lat > 90) {
    errors.push({ fieldId: 'latitude', message: 'Latitude must be between -90 and 90.' });
  }
  if (isNaN(lon) || lon < -180 || lon > 180) {
    errors.push({ fieldId: 'longitude', message: 'Longitude must be between -180 and 180.' });
  }

  if (errors.length > 0) {
    showErrorSummary(errors);
    return;
  }
  showErrorSummary([]);

  const status = $('#status');
  const error = $('#error');
  textContent(error, '');
  const { language } = getState();
  textContent(status, translations[language].loading);
  $('.results').setAttribute('aria-busy', 'true');
  const empty = $('#empty-state');
  if (empty) empty.hidden = true;

  try {
    const payload = buildPayload();
    const data = await fetchPlan(payload);
    textContent(status, '');
    setLastResult(data);
    renderResults(data);
  } catch (err) {
    textContent(status, '');
    textContent(error, err.message || 'Unable to create plan');
    announce(`Error: ${err.message}`, 'assertive');
  } finally {
    $('.results').setAttribute('aria-busy', 'false');
  }
}

function initEventHandlers() {
  $('.skip-link')?.addEventListener('click', (e) => {
    e.preventDefault();
    const main = $('#main-content');
    if (main) {
      main.focus();
      main.scrollIntoView();
    }
  });

  $('#plan-form').addEventListener('submit', handleFormSubmit);

  $('#add-member').addEventListener('click', () => {
    addMember();
    refreshMembers();
  });

  $('#language-toggle').addEventListener('click', () => {
    const { language, lastResult } = getState();
    const nextLang = language === 'en' ? 'hinglish' : language === 'hinglish' ? 'hi' : 'en';
    setLanguage(nextLang);
    applyTranslations();
    refreshMembers();
    if (lastResult) {
      renderResults(lastResult);
    }
  });

  // Persona Presets
  $$('.persona-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const personaKey = btn.dataset.persona;
      const { lastResult } = getState();
      const presets = lastResult?.personas || DEFAULT_PERSONAS;
      const preset = presets[personaKey];
      if (preset) {
        applyPersona(preset);
        refreshMembers();
        if (preset.routine_text) $('#routine-text').value = preset.routine_text;
        if (preset.commute) $('#commute').value = preset.commute;
        if (preset.outdoor_minutes) $('#outdoor').value = String(preset.outdoor_minutes);
        if (preset.cooking) $('#cooking').value = preset.cooking;
        if (preset.heating) $('#heating').value = preset.heating;
        if (preset.windows) $('#windows').value = preset.windows;
        if (preset.purifier !== undefined) $('#purifier').value = String(preset.purifier);
        announce(`Loaded preset: ${preset.name}`);
      }
    });
  });

  // City Search
  $('#city-search').addEventListener('click', async () => {
    const city = $('#city').value.trim();
    const results = $('#city-results');
    const { language } = getState();
    const t = translations[language];
    results.replaceChildren();

    if (city.length < 2) {
      textContent(results, t.cityNotFound);
      return;
    }
    textContent(results, t.citySearching);

    try {
      const items = await fetchGeocode(city);
      results.replaceChildren();
      if (!items || items.length === 0) {
        textContent(results, t.cityNotFound);
        return;
      }
      announce(`Found ${items.length} city matches.`);
      items.forEach((item) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'secondary city-match-btn';
        btn.textContent = `${item.name}, ${item.admin1 || ''} ${item.country}`.trim();
        btn.addEventListener('click', () => {
          $('#latitude').value = item.latitude.toFixed(4);
          $('#longitude').value = item.longitude.toFixed(4);
          $('#city').value = item.name;
          results.replaceChildren();
          announce(`Selected location: ${btn.textContent}`);
        });
        results.append(btn);
      });
    } catch (err) {
      results.replaceChildren();
      textContent(results, err.message || t.cityFailed);
    }
  });

  // Geolocation
  $('#geo-button').addEventListener('click', () => {
    const { language } = getState();
    const t = translations[language];
    if (!navigator.geolocation) {
      textContent($('#error'), t.geolocationUnavailable);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        $('#latitude').value = pos.coords.latitude.toFixed(4);
        $('#longitude').value = pos.coords.longitude.toFixed(4);
        textContent($('#error'), '');
        announce('Location updated from device GPS.');
      },
      () => {
        textContent($('#error'), t.locationDenied);
      }
    );
  });

  // Text Scaling (A-, A, A+)
  $('#text-smaller').addEventListener('click', () => {
    const { textScale } = getState();
    const next = Math.max(75, textScale - 10);
    setTextScale(next);
    initTextScale(next);
  });
  $('#text-reset').addEventListener('click', () => {
    setTextScale(100);
    initTextScale(100);
  });
  $('#text-larger').addEventListener('click', () => {
    const { textScale } = getState();
    const next = Math.min(200, textScale + 10);
    setTextScale(next);
    initTextScale(next);
  });

  // Copy Summary
  $('#copy-summary').addEventListener('click', async () => {
    const { language } = getState();
    const t = translations[language];
    try {
      await navigator.clipboard.writeText($('#family-summary').dataset.value || '');
      textContent($('#status'), t.copied);
      announce(t.copied);
    } catch {
      textContent($('#error'), t.copyFailed);
    }
  });

  // Speech: Read Aloud
  const readBtn = $('#read-aloud-btn');
  if (readBtn) {
    if (!isSpeechSynthesisSupported()) {
      readBtn.hidden = true;
    } else {
      readBtn.addEventListener('click', () => {
        const text = $('#family-summary').dataset.value || $('#explanation').textContent;
        const { language } = getState();
        speakText(text, language);
      });
    }
  }

  // Speech: Voice Input
  const voiceBtn = $('#voice-input-btn');
  if (voiceBtn) {
    if (!isSpeechRecognitionSupported()) {
      voiceBtn.hidden = true;
    } else {
      voiceBtn.addEventListener('click', () => {
        const { language } = getState();
        startVoiceRecognition({
          lang: language,
          onStart: () => {
            voiceBtn.classList.add('listening');
            textContent(voiceBtn, '🎙️ Listening…');
          },
          onResult: (transcript) => {
            const current = $('#routine-text').value;
            $('#routine-text').value = current ? `${current} ${transcript}` : transcript;
          },
          onError: (err) => {
            announce(`Speech recognition error: ${err}`);
          },
          onEnd: () => {
            voiceBtn.classList.remove('listening');
            textContent(voiceBtn, '🎤 Speak routine');
          },
        });
      });
    }
  }

  // Ask Assistant
  $('#ask-button').addEventListener('click', async () => {
    const question = $('#ask-question').value.trim();
    const answer = $('#ask-answer');
    const { language } = getState();
    const t = translations[language];
    if (!question) {
      textContent(answer, 'Please enter an air-quality question.');
      return;
    }
    textContent(answer, t.askThinking);
    try {
      const reply = await askAssistant(question);
      textContent(answer, reply);
      announce('Answer received from grounded assistant.');
    } catch (err) {
      textContent(answer, err.message || 'Could not retrieve answer.');
    }
  });
}

// Bootstrap
document.addEventListener('DOMContentLoaded', () => {
  const { textScale } = getState();
  initTextScale(textScale);
  applyTranslations();
  refreshMembers();
  initEventHandlers();
});
