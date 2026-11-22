import { translations } from './i18n.js';

let language = localStorage.getItem('saansplan-language') || 'en';
let family = JSON.parse(localStorage.getItem('saansplan-family') || 'null') || [{ name: '', ageGroup: 'adult', sensitive: false }];
let lastResult = null;
let textScale = Number(localStorage.getItem('saansplan-text-scale') || 100);

const $ = (selector) => document.querySelector(selector);

function textContent(element, value) {
  if (element) element.textContent = String(value);
}

function applyTranslations() {
  document.documentElement.lang = language === 'hi' ? 'hi' : language === 'hinglish' ? 'hi-Latn' : 'en';
  for (const [key, value] of Object.entries(translations[language])) {
    for (const element of document.querySelectorAll(`[data-i18n="${key}"]`)) textContent(element, value);
  }
  for (const element of document.querySelectorAll('[data-i18n-placeholder]')) {
    element.placeholder = translations[language][element.dataset.i18nPlaceholder];
  }
}

function renderMembers() {
  const container = $('#members');
  container.replaceChildren();
  family.forEach((member, index) => {
    const row = document.createElement('div');
    row.className = 'member-row';
    const nameWrap = document.createElement('div');
    const nameLabel = document.createElement('label');
    nameLabel.htmlFor = `member-name-${index}`;
    nameLabel.textContent = translations[language].nameOptional;
    const nameInput = document.createElement('input');
    nameInput.id = `member-name-${index}`;
    nameInput.value = member.name;
    nameInput.maxLength = 40;
    nameInput.addEventListener('input', () => { family[index].name = nameInput.value; saveFamily(); });
    nameWrap.append(nameLabel, nameInput);

    const ageWrap = document.createElement('div');
    const ageLabel = document.createElement('label');
    ageLabel.htmlFor = `member-age-${index}`;
    ageLabel.textContent = translations[language].age;
    const age = document.createElement('select');
    age.id = `member-age-${index}`;
    for (const value of ['child', 'adult', 'elderly']) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = translations[language][value];
      option.selected = member.ageGroup === value;
      age.append(option);
    }
    age.addEventListener('change', () => { family[index].ageGroup = age.value; saveFamily(); });
    ageWrap.append(ageLabel, age);

    const sensitiveWrap = document.createElement('div');
    const sensitiveLabel = document.createElement('label');
    sensitiveLabel.htmlFor = `member-sensitive-${index}`;
    sensitiveLabel.textContent = translations[language].sensitive;
    const sensitive = document.createElement('input');
    sensitive.type = 'checkbox';
    sensitive.id = `member-sensitive-${index}`;
    sensitive.checked = member.sensitive;
    sensitive.addEventListener('change', () => { family[index].sensitive = sensitive.checked; saveFamily(); });
    sensitiveWrap.append(sensitiveLabel, sensitive);

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'secondary';
    remove.textContent = translations[language].remove;
    remove.disabled = family.length === 1;
    remove.addEventListener('click', () => { family.splice(index, 1); renderMembers(); saveFamily(); });
    row.append(nameWrap, ageWrap, sensitiveWrap, remove);
    container.append(row);
  });
}

function saveFamily() {
  localStorage.setItem('saansplan-family', JSON.stringify(family));
}

function aqiLevel(aqi) {
  const t = translations[language];
  if (aqi <= 100) return { level: 'good', text: t.categoryGood, icon: '●' };
  if (aqi <= 200) return { level: 'moderate', text: t.categorySensitive, icon: '◆' };
  return { level: 'bad', text: t.categoryBad, icon: '▲' };
}

function buildRoutinePayload() {
  const commute = $('#commute').value;
  const outdoorMinutes = Number($('#outdoor').value);
  const routineText = $('#routine-text').value.trim();
  const activities = [];
  if (outdoorMinutes > 0) {
    activities.push({ label: 'Outdoor activity', start_hour: 18, duration_min: outdoorMinutes, place: 'outdoor', mode: commute === 'none' ? 'walk' : commute, intensity: 'light', member_refs: family.map((_, i) => i) });
  }
  return {
    latitude: Number($('#latitude').value), longitude: Number($('#longitude').value),
    city: $('#city').value.trim() || null,
    members: family.map((member) => ({ name: member.name || null, age_group: member.ageGroup, sensitive: member.sensitive })),
    routine_text: routineText,
    routine: routineText ? null : {
      activities,
      home: { heating: $('#heating').value, cooking: $('#cooking').value, windows: $('#windows').value, purifier: $('#purifier').value === 'true', has_chimney: false },
      unclear: []
    },
    language
  };
}

function renderTimeline(hourly) {
  const timeline = $('#timeline');
  const tbody = $('#timeline-table tbody');
  timeline.replaceChildren(); tbody.replaceChildren();
  for (const row of hourly) {
    const level = aqiLevel(row.aqi);
    const hour = document.createElement('div');
    hour.className = 'timeline-hour'; hour.dataset.level = level.level;
    const hourText = document.createElement('strong'); hourText.textContent = `${row.hour}:00`;
    const aqiText = document.createElement('span'); aqiText.textContent = `${level.icon} AQI ${row.aqi}`;
    hour.append(hourText, document.createElement('br'), aqiText); timeline.append(hour);

    const tr = document.createElement('tr');
    const values = [
      `${row.hour}:00`,
      row.pm25,
      row.indian_category || 'Estimate unavailable',
      row.indian_aqi ?? row.aqi,
      row.exposure,
      row.interpolated ? translations[language].interpolatedYes : translations[language].interpolatedNo,
    ];
    values.forEach((value, index) => {
      if (index === 0) {
        const th = document.createElement('th');
        th.scope = 'row'; th.textContent = String(value); tr.append(th);
      } else {
        const td = document.createElement('td'); td.textContent = String(value); tr.append(td);
      }
    });
    tbody.append(tr);
  }
}

function cardGrid(container, items) {
  container.replaceChildren();
  container.className = 'card-grid';
  for (const item of items) {
    const card = document.createElement('article'); card.className = 'card';
    const title = document.createElement('strong');
    title.textContent = readableLabels[item.description_key || item.key] || 'Safer home or travel action';
    const body = document.createElement('p');
    if ('percent_reduction' in item) {
      const t = translations[language];
      body.textContent = `${t.before} ${item.exposure_before} → ${t.after} ${item.exposure_after}; ${t.estimated} ${item.percent_reduction}% ${t.lower}. ${item.emissions_note}`;
    }
    else body.textContent = `${item.estimate || item.exposure_note || ''} ${item.emissions_note || ''}`;
    card.append(title, body); container.append(card);
  }
}

function shareText(data) {
  const t = translations[language];
  const topThree = (data.top_swaps || []).slice(0, 3);
  const actions = topThree.map((item, index) => {
    const title = readableLabels[item.description_key || item.key] || 'Safer home or travel action';
    return `${index + 1}. ${title}: about ${item.percent_reduction}% less exposure (estimate).`;
  }).join('\n');
  const highestAqi = data.exposure.highest_aqi_hour;
  const peakExposure = data.exposure.peak_hour;
  return `SaansPlan family summary\nHighest exposure hour: ${peakExposure}:00.\nHighest AQI hour: ${highestAqi}:00, AQI ${data.exposure.highest_aqi ?? data.exposure.peak_aqi}.\nTop actions:\n${actions || 'No positive swap found.'}\n${data.explanation.explanation}\n${t.estimates}`;
}

async function submitPlan(event) {
  event.preventDefault();
  const status = $('#status'); const error = $('#error');
  error.textContent = ''; status.textContent = translations[language].loading;
  document.querySelector('.results').setAttribute('aria-busy', 'true');
  const empty = $('#empty-state');
  if (empty) empty.hidden = true;
  try {
    const response = await fetch('/api/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(buildRoutinePayload()) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Unable to create plan');
    status.textContent = '';
    $('#summary-card').hidden = false;
    textContent($('#peak-aqi'), data.exposure.peak_aqi);
    const level = aqiLevel(data.exposure.peak_aqi);
    textContent($('#aqi-category'), `${level.icon} ${level.text}`);
    textContent($('#explanation'), data.explanation.explanation);

    const aiNotice = $('#ai-notice');
    aiNotice.hidden = data.explanation.ai_available !== false;

    $('#timeline-section').hidden = false; renderTimeline(data.hourly);
    $('#swaps-section').hidden = false; cardGrid($('#swaps'), data.top_swaps);
    $('#indoor-section').hidden = false; cardGrid($('#indoor'), data.indoor_hacks);
    $('#alternatives-section').hidden = false; cardGrid($('#alternatives'), data.sustainable_alternatives);
    $('#share-section').hidden = false;
    const summary = shareText(data); textContent($('#family-summary'), summary); $('#family-summary').dataset.value = summary;
    textContent($('#peak-exposure-text'), `Highest exposure hour: ${data.exposure.peak_hour}:00 (estimate)`);
    textContent($('#highest-aqi-text'), `Highest AQI hour: ${data.exposure.highest_aqi_hour}:00, Indian AQI band ${data.exposure.highest_aqi}`);
    lastResult = data;
  } catch (cause) {
    status.textContent = ''; textContent(error, cause.message);
  } finally {
    document.querySelector('.results').setAttribute('aria-busy', 'false');
  }
}

$('#plan-form').addEventListener('submit', submitPlan);
$('#add-member').addEventListener('click', () => {
  if (family.length < 12) {
    family.push({ name: '', ageGroup: 'adult', sensitive: false });
    renderMembers(); saveFamily();
  }
});
$('#language-toggle').addEventListener('click', () => {
  const nextLanguage = language === 'en' ? 'hinglish' : language === 'hinglish' ? 'hi' : 'en';
  language = nextLanguage;
  localStorage.setItem('saansplan-language', language);
  applyTranslations(); renderMembers();
  if (lastResult) {
    textContent($('#peak-aqi'), lastResult.exposure.peak_aqi);
    const level = aqiLevel(lastResult.exposure.peak_aqi);
    textContent($('#aqi-category'), `${level.icon} ${level.text}`);
    textContent($('#explanation'), lastResult.explanation.explanation);
    renderTimeline(lastResult.hourly); cardGrid($('#swaps'), lastResult.top_swaps);
    cardGrid($('#indoor'), lastResult.indoor_hacks);
    cardGrid($('#alternatives'), lastResult.sustainable_alternatives);
    textContent($('#family-summary'), shareText(lastResult));
  }
});

$('#city-search').addEventListener('click', async () => {
  const city = $('#city').value.trim();
  const results = $('#city-results');
  results.replaceChildren();
  if (city.length < 2) { textContent(results, translations[language].cityNotFound); return; }
  textContent(results, translations[language].citySearching);
  try {
    const response = await fetch(`/api/geocode?name=${encodeURIComponent(city)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || translations[language].cityFailed);
    results.replaceChildren();
    if (!data.results?.length) { textContent(results, translations[language].cityNotFound); return; }
    data.results.forEach((item) => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'secondary';
      button.textContent = `${item.name}, ${item.admin1 || ''} ${item.country}`.trim();
      button.addEventListener('click', () => {
        $('#latitude').value = item.latitude.toFixed(4);
        $('#longitude').value = item.longitude.toFixed(4);
        results.replaceChildren(); textContent(results, button.textContent);
      });
      results.append(button);
    });
  } catch (cause) {
    results.replaceChildren(); textContent(results, cause.message || translations[language].cityFailed);
  }
});

$('#geo-button').addEventListener('click', () => {
  if (!navigator.geolocation) {
    textContent($('#error'), translations[language].geolocationUnavailable); return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      $('#latitude').value = position.coords.latitude.toFixed(4);
      $('#longitude').value = position.coords.longitude.toFixed(4);
      textContent($('#error'), '');
    },
    () => textContent($('#error'), translations[language].locationDenied)
  );
});

$('#copy-summary').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText($('#family-summary').dataset.value || '');
    textContent($('#status'), translations[language].copied);
  } catch {
    textContent($('#error'), translations[language].copyFailed);
  }
});

$('#routine-text').setAttribute('aria-label', translations[language].routine);
$('.skip-link').textContent = translations[language].skip;

const readableLabels = {
  swap_shift: 'Shift the outdoor activity to a cleaner hour',
  shift_activity: 'Shift the outdoor activity to a cleaner hour',
  swap_windows: 'Close windows during high-AQI hours',
  close_windows: 'Close windows during high-AQI hours',
  swap_purifier: 'Run a clean, correctly sized purifier',
  run_purifier: 'Run a clean, correctly sized purifier',
  swap_cooking: 'Cook with induction instead of smoky fuel',
  cook_induction: 'Cook with induction instead of smoky fuel',
  purifier: 'Run a purifier',
  closed_windows: 'Close windows in severe hours',
  box_fan_filter: 'Use a safer supplemental box-fan filter',
  chimney: 'Vent cooking and heating smoke outdoors',
  mask: 'Use a well-fitted certified respirator outdoors',
  metro_bus: 'Choose metro or bus for shared travel',
  walk_cycle: 'Walk or cycle in quieter, cleaner hours',
  induction: 'Use induction for lower indoor combustion',
  insulation: 'Improve insulation and layering'
};

function applyTextScale() {
  document.documentElement.style.fontSize = `${textScale}%`;
  localStorage.setItem('saansplan-text-scale', String(textScale));
}

renderMembers(); applyTranslations(); applyTextScale();
$('#text-smaller').addEventListener('click', () => { textScale = Math.max(75, textScale - 10); applyTextScale(); });
$('#text-reset').addEventListener('click', () => { textScale = 100; applyTextScale(); });
$('#text-larger').addEventListener('click', () => { textScale = Math.min(200, textScale + 10); applyTextScale(); });
applyTextScale();
$('#ask-button').addEventListener('click', async () => {
  const question = $('#ask-question').value.trim();
  const answer = $('#ask-answer');
  if (!question) { textContent(answer, 'Enter a short air-quality question.'); return; }
  textContent(answer, 'Finding a grounded answer…');
  try {
    const response = await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) });
    const data = await response.json();
    if (!response.ok) throw new Error('Could not answer this question.');
    textContent(answer, data.answer);
  } catch (cause) {
    textContent(answer, cause.message);
  }
});
