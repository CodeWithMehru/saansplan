import { translations } from './i18n.js';

let language = 'en';
let family = JSON.parse(localStorage.getItem('saansplan-family') || 'null') || [{ name: '', ageGroup: 'adult', sensitive: false }];

const $ = (selector) => document.querySelector(selector);

function textContent(element, value) {
  if (element) element.textContent = String(value);
}

function applyTranslations() {
  document.documentElement.lang = language === 'en' ? 'en' : 'hi';
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
    nameLabel.textContent = 'Name (optional)';
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
  if (aqi <= 100) return { level: 'good', text: 'Good to moderate', icon: '●' };
  if (aqi <= 200) return { level: 'moderate', text: 'Unhealthy for sensitive groups', icon: '◆' };
  return { level: 'bad', text: 'Unhealthy / severe', icon: '▲' };
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
    for (const value of [`${row.hour}:00`, row.pm25, row.aqi, row.exposure, row.interpolated ? 'Yes' : 'No']) {
      const td = document.createElement('td'); td.textContent = String(value); tr.append(td);
    }
    tbody.append(tr);
  }
}

function cardGrid(container, items) {
  container.replaceChildren();
  container.className = 'card-grid';
  for (const item of items) {
    const card = document.createElement('article'); card.className = 'card';
    const title = document.createElement('strong'); title.textContent = item.description_key || item.key;
    const body = document.createElement('p');
    if ('percent_reduction' in item) body.textContent = `Before ${item.exposure_before} → after ${item.exposure_after}; estimated ${item.percent_reduction}% lower. ${item.emissions_note}`;
    else body.textContent = `${item.estimate || item.exposure_note || ''} ${item.emissions_note || ''}`;
    card.append(title, body); container.append(card);
  }
}

function shareText(data) {
  const top = data.top_swaps?.[0];
  const swapText = top ? `Top estimate: ${top.percent_reduction}% lower exposure (${top.exposure_before} to ${top.exposure_after}).` : 'No positive swap found.';
  return `SaansPlan family summary\nPeak exposure: about ${data.exposure.peak_hour}:00, AQI ${data.exposure.peak_aqi}.\n${swapText}\n${data.explanation.explanation}\nAll numbers are estimates, not medical advice.`;
}

async function submitPlan(event) {
  event.preventDefault();
  const status = $('#status'); const error = $('#error');
  error.textContent = ''; status.textContent = translations[language].loading;
  document.querySelector('.results').setAttribute('aria-busy', 'true');
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

    $('#timeline-section').hidden = false; renderTimeline(data.hourly);
    $('#swaps-section').hidden = false; cardGrid($('#swaps'), data.top_swaps);
    $('#indoor-section').hidden = false; cardGrid($('#indoor'), data.indoor_hacks);
    $('#alternatives-section').hidden = false; cardGrid($('#alternatives'), data.sustainable_alternatives);
    $('#share-section').hidden = false;
    const summary = shareText(data); textContent($('#family-summary'), summary); $('#family-summary').dataset.value = summary;
  } catch (cause) {
    status.textContent = ''; textContent(error, cause.message);
  } finally {
    document.querySelector('.results').setAttribute('aria-busy', 'false');
  }
}

$('#plan-form').addEventListener('submit', submitPlan);
$('#add-member').addEventListener('click', () => { if (family.length < 12) { family.push({ name: '', ageGroup: 'adult', sensitive: false }); renderMembers(); saveFamily(); } });
$('#language-toggle').addEventListener('click', () => { language = language === 'en' ? 'hinglish' : 'en'; applyTranslations(); renderMembers(); });
$('#geo-button').addEventListener('click', () => {
  if (!navigator.geolocation) { textContent($('#error'), 'Geolocation is not available in this browser'); return; }
  navigator.geolocation.getCurrentPosition((position) => { $('#latitude').value = position.coords.latitude.toFixed(4); $('#longitude').value = position.coords.longitude.toFixed(4); }, () => textContent($('#error'), 'Location permission was not granted'));
});
$('#copy-summary').addEventListener('click', async () => { try { await navigator.clipboard.writeText($('#family-summary').dataset.value || ''); } catch { textContent($('#error'), 'Copy failed. Select the summary text manually.'); } });

renderMembers(); applyTranslations();
