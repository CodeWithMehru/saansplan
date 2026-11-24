/**
 * DOM event handlers for personas, geolocation, text scaling, speech, and assistant Q&A.
 */

import { translations } from '../i18n.js';
import { announce, initTextScale } from './a11y/focus.js';
import { askAssistant, fetchGeocode } from './api.js';
import { isSpeechRecognitionSupported, isSpeechSynthesisSupported, speakText, startVoiceRecognition } from './speech.js';
import { applyPersona, DEFAULT_PERSONAS, getState, setLanguage, setTextScale } from './state.js';
import { $, $$, textContent } from './utils.js';

export function initLanguageToggle(applyTranslations, refreshMembers, renderResults) {
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
}

export function initPersonaHandlers(refreshMembers) {
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
}

export function initLocationHandlers() {
  $('#city-search').addEventListener('click', async () => {
    const city = $('#city').value.trim();
    const results = $('#city-results');
    const { language } = getState();
    const t = translations[language] || translations.en;
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

  $('#geo-button').addEventListener('click', () => {
    const { language } = getState();
    const t = translations[language] || translations.en;
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
}

export function initTextScaleHandlers() {
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

  const contrastBtn = $('#contrast-toggle');
  if (contrastBtn) {
    if (localStorage.getItem('saansplan_contrast') === 'high') {
      document.documentElement.setAttribute('data-contrast', 'high');
    }
    contrastBtn.addEventListener('click', () => {
      const isHigh = document.documentElement.getAttribute('data-contrast') === 'high';
      if (isHigh) {
        document.documentElement.removeAttribute('data-contrast');
        localStorage.removeItem('saansplan_contrast');
        announce('High contrast disabled');
      } else {
        document.documentElement.setAttribute('data-contrast', 'high');
        localStorage.setItem('saansplan_contrast', 'high');
        announce('High contrast enabled');
      }
    });
  }

  const spacingBtn = $('#spacing-toggle');
  if (spacingBtn) {
    if (localStorage.getItem('saansplan_spacing') === 'enhanced') {
      document.documentElement.setAttribute('data-spacing', 'enhanced');
    }
    spacingBtn.addEventListener('click', () => {
      const isEnhanced = document.documentElement.getAttribute('data-spacing') === 'enhanced';
      if (isEnhanced) {
        document.documentElement.removeAttribute('data-spacing');
        localStorage.removeItem('saansplan_spacing');
        announce('Enhanced text spacing disabled');
      } else {
        document.documentElement.setAttribute('data-spacing', 'enhanced');
        localStorage.setItem('saansplan_spacing', 'enhanced');
        announce('Enhanced text spacing enabled');
      }
    });
  }
}

export function initSpeechAndAssistantHandlers() {
  $('#copy-summary').addEventListener('click', async () => {
    const { language } = getState();
    const t = translations[language] || translations.en;
    try {
      await navigator.clipboard.writeText($('#family-summary').dataset.value || '');
      textContent($('#status'), t.copied);
      announce(t.copied);
    } catch {
      textContent($('#error'), t.copyFailed);
    }
  });

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

  $('#ask-button').addEventListener('click', async () => {
    const question = $('#ask-question').value.trim();
    const answer = $('#ask-answer');
    const { language } = getState();
    const t = translations[language] || translations.en;
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
