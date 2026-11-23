/**
 * Render module: renders all accessible UI components, accessible SVG charts, and tables.
 */

import { translations } from '../i18n.js';
import { $, aqiLevel, getHumanLabel, textContent } from './utils.js';

export function renderMembers(family, language, onUpdate, onRemove) {
  const container = $('#members');
  if (!container) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  family.forEach((member, index) => {
    const row = document.createElement('div');
    row.className = 'member-row';

    const nameWrap = document.createElement('div');
    const nameLabel = document.createElement('label');
    nameLabel.htmlFor = `member-name-${index}`;
    nameLabel.textContent = `${t.nameOptional} (${index + 1})`;
    const nameInput = document.createElement('input');
    nameInput.id = `member-name-${index}`;
    nameInput.value = member.name || '';
    nameInput.maxLength = 40;
    nameInput.autocomplete = 'given-name';
    nameInput.addEventListener('input', () => onUpdate(index, { name: nameInput.value }));
    nameWrap.append(nameLabel, nameInput);

    const ageWrap = document.createElement('div');
    const ageLabel = document.createElement('label');
    ageLabel.htmlFor = `member-age-${index}`;
    ageLabel.textContent = `${t.age} (${index + 1})`;
    const ageSelect = document.createElement('select');
    ageSelect.id = `member-age-${index}`;
    ['child', 'adult', 'elderly'].forEach((val) => {
      const opt = document.createElement('option');
      opt.value = val;
      opt.textContent = t[val];
      opt.selected = member.ageGroup === val;
      ageSelect.append(opt);
    });
    ageSelect.addEventListener('change', () => onUpdate(index, { ageGroup: ageSelect.value }));
    ageWrap.append(ageLabel, ageSelect);

    const sensWrap = document.createElement('div');
    sensWrap.className = 'checkbox-wrap';
    const sensInput = document.createElement('input');
    sensInput.type = 'checkbox';
    sensInput.id = `member-sens-${index}`;
    sensInput.checked = Boolean(member.sensitive);
    sensInput.addEventListener('change', () => onUpdate(index, { sensitive: sensInput.checked }));
    const sensLabel = document.createElement('label');
    sensLabel.htmlFor = `member-sens-${index}`;
    sensLabel.textContent = t.sensitive;
    sensWrap.append(sensInput, sensLabel);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'secondary remove-btn';
    removeBtn.textContent = t.remove;
    removeBtn.setAttribute('aria-label', `${t.remove} ${member.name || `Member ${index + 1}`}`);
    removeBtn.disabled = family.length <= 1;
    removeBtn.addEventListener('click', () => onRemove(index));

    row.append(nameWrap, ageWrap, sensWrap, removeBtn);
    container.append(row);
  });
}

export function renderTimeline(hourly, language) {
  const timeline = $('#timeline');
  const tbody = $('#timeline-table tbody');
  if (!timeline || !tbody) return;
  timeline.replaceChildren();
  tbody.replaceChildren();
  const t = translations[language] || translations.en;

  for (const row of hourly) {
    const level = aqiLevel(row.aqi, language);
    const hourDiv = document.createElement('div');
    hourDiv.className = 'timeline-hour';
    hourDiv.dataset.level = level.slug;

    const hourText = document.createElement('strong');
    hourText.textContent = `${row.hour}:00`;
    const aqiSpan = document.createElement('span');
    aqiSpan.textContent = `${level.icon} AQI ${row.aqi}`;

    hourDiv.append(hourText, document.createElement('br'), aqiSpan);
    timeline.append(hourDiv);

    const tr = document.createElement('tr');
    const th = document.createElement('th');
    th.scope = 'row';
    th.textContent = `${row.hour}:00`;
    tr.append(th);

    const cols = [
      row.pm25,
      row.indian_category || level.text,
      row.indian_aqi ?? row.aqi,
      row.exposure,
      row.interpolated ? t.interpolatedYes : t.interpolatedNo,
    ];
    cols.forEach((val) => {
      const td = document.createElement('td');
      td.textContent = String(val);
      tr.append(td);
    });
    tbody.append(tr);
  }
}

export function renderSwaps(swaps, language) {
  const container = $('#swaps');
  if (!container) return;
  container.replaceChildren();
  container.className = 'card-grid';
  const t = translations[language] || translations.en;

  swaps.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'card swap-card';

    const title = document.createElement('strong');
    title.textContent = getHumanLabel(item.description_key || item.key, language);

    const body = document.createElement('p');
    const reduction = item.percent_reduction || 0;
    body.textContent = `Could reduce your family's PM2.5 intake by about ${reduction}% (estimate). ${item.emissions_note || ''}`;

    card.append(title, body);
    container.append(card);
  });
}

export function renderForecast(forecastDays, language) {
  const container = $('#forecast-cards');
  if (!container || !forecastDays) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  forecastDays.forEach((day) => {
    const card = document.createElement('article');
    card.className = `card forecast-card ${day.is_severe ? 'severe-border' : ''}`;

    const head = document.createElement('div');
    head.className = 'forecast-head';
    const dayName = document.createElement('strong');
    dayName.textContent = day.day_index === 0 ? 'Today' : day.day_index === 1 ? 'Tomorrow' : `Day ${day.day_index + 1}`;
    const aqiBadge = document.createElement('span');
    aqiBadge.className = `badge ${day.category_slug}`;
    aqiBadge.textContent = `AQI ${day.peak_aqi} (${day.indian_category})`;
    head.append(dayName, aqiBadge);

    const worstP = document.createElement('p');
    worstP.innerHTML = `<strong>${t.worstWindow}:</strong> ${day.worst_window.start_hour}:00 – ${day.worst_window.end_hour}:00`;

    const bestP = document.createElement('p');
    bestP.innerHTML = `<strong>${t.bestWindow}:</strong> ${day.best_window.start_hour}:00 – ${day.best_window.end_hour}:00`;

    const airingP = document.createElement('p');
    airingP.innerHTML = `<strong>${t.safestAiring}:</strong> ${day.safest_airing_hour}:00 – ${day.safest_airing_hour + 1}:00`;

    card.append(head, worstP, bestP, airingP);

    if (day.is_stagnant) {
      const stagP = document.createElement('p');
      stagP.className = 'alert-notice stagnation';
      stagP.textContent = `⚠️ ${t.stagnationAlert} (${day.avg_wind_speed_mps} m/s)`;
      card.append(stagP);
    }

    if (day.is_severe) {
      const severeP = document.createElement('p');
      severeP.className = 'alert-notice severe';
      severeP.textContent = `🚨 ${t.severeSmogAlert}`;
      card.append(severeP);
    }

    container.append(card);
  });
}

export function renderCleanerDay(cleanerDay, language) {
  const container = $('#cleaner-day-content');
  if (!container || !cleanerDay) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  const summaryCard = document.createElement('div');
  summaryCard.className = 'cleaner-day-summary';
  const savedIntake = cleanerDay.inhaled_saved_ug || 0;
  const [lowRange, highRange] = cleanerDay.inhaled_saved_range_ug || [0, 0];
  summaryCard.innerHTML = `
    <h3>${t.cleanerDayTitle}</h3>
    <p>${t.cleanerDayDesc}</p>
    <div class="metrics-banner">
      <div class="metric"><strong>${cleanerDay.percent_reduction}%</strong><span>Lower daily exposure</span></div>
      <div class="metric"><strong>~${savedIntake} µg</strong><span>PM2.5 saved (${lowRange}–${highRange} µg physical range)</span></div>
    </div>
  `;
  container.append(summaryCard);

  // Changes list
  if (cleanerDay.changes && cleanerDay.changes.length > 0) {
    const changesSec = document.createElement('div');
    changesSec.className = 'cleaner-changes';
    const changesTitle = document.createElement('h4');
    changesTitle.textContent = 'Optimized Daily Timing & In-Home Actions';
    const ul = document.createElement('ul');
    cleanerDay.changes.forEach((chg) => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${chg.activity}:</strong> ${chg.reason}`;
      ul.append(li);
    });
    changesSec.append(changesTitle, ul);
    container.append(changesSec);
  }

  // SVG Before vs After Comparison Chart
  const svgWrap = document.createElement('div');
  svgWrap.className = 'chart-wrap';
  const comparison = cleanerDay.hourly_comparison || [];

  const maxExp = Math.max(...comparison.map((r) => Math.max(r.exposure_before, r.exposure_after)), 50.0);
  const chartHeight = 160;
  const chartWidth = 560;
  const barWidth = 8;
  const barGap = 23;

  let barsSvg = '';
  comparison.forEach((r, idx) => {
    const x = 20 + idx * barGap;
    const hBefore = Math.round((r.exposure_before / maxExp) * (chartHeight - 40));
    const hAfter = Math.round((r.exposure_after / maxExp) * (chartHeight - 40));
    const yBefore = chartHeight - 20 - hBefore;
    const yAfter = chartHeight - 20 - hAfter;

    barsSvg += `
      <rect x="${x}" y="${yBefore}" width="${barWidth}" height="${hBefore}" fill="#9e2d23" opacity="0.8" rx="2"><title>${r.hour}:00 Before: ${r.exposure_before}</title></rect>
      <rect x="${x + barWidth + 1}" y="${yAfter}" width="${barWidth}" height="${hAfter}" fill="#146b43" opacity="0.9" rx="2"><title>${r.hour}:00 Cleaner Day: ${r.exposure_after}</title></rect>
      <text x="${x + barWidth}" y="${chartHeight - 5}" font-size="9" text-anchor="middle" fill="#666">${r.hour}</text>
    `;
  });

  svgWrap.innerHTML = `
    <svg viewBox="0 0 ${chartWidth} ${chartHeight}" class="cleaner-chart" role="img" aria-labelledby="chart-title chart-desc">
      <title id="chart-title">Hour-by-hour exposure comparison chart</title>
      <desc id="chart-desc">Bar chart comparing hourly pollution exposure between original routine (red) and cleaner day alternative (green).</desc>
      <line x1="20" y1="${chartHeight - 20}" x2="${chartWidth - 10}" y2="${chartHeight - 20}" stroke="#b9c9bf" stroke-width="1"/>
      ${barsSvg}
    </svg>
    <div class="chart-legend" aria-hidden="true">
      <span class="legend-item"><span class="legend-color before"></span> ${t.originalRoutine}</span>
      <span class="legend-item"><span class="legend-color after"></span> ${t.optimizedRoutine}</span>
    </div>
  `;
  container.append(svgWrap);

  // Table alternative
  const details = document.createElement('details');
  details.open = true;
  details.className = 'comparison-details';
  details.innerHTML = `
    <summary>${t.tableAlternative}</summary>
    <div class="table-wrap" role="region" tabindex="0" aria-label="Cleaner day comparison data table">
      <table class="comparison-table">
        <caption>Hour-by-hour exposure: Current vs Cleaner Day</caption>
        <thead>
          <tr><th scope="col">Hour</th><th scope="col">PM2.5 µg/m³</th><th scope="col">${t.originalRoutine}</th><th scope="col">${t.optimizedRoutine}</th><th scope="col">Reduction</th></tr>
        </thead>
        <tbody>
          ${comparison.map((r) => `
            <tr>
              <th scope="row">${r.hour}:00</th>
              <td>${r.pm25}</td>
              <td>${r.exposure_before}</td>
              <td>${r.exposure_after}</td>
              <td>${r.difference > 0 ? `−${r.difference}` : '0'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
  container.append(details);
}

export function renderEmissions(emissionsData, language, onFilterChange) {
  const container = $('#emissions-content');
  if (!container || !emissionsData) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  const current = emissionsData.current;
  const currentBanner = document.createElement('div');
  currentBanner.className = 'emissions-current-card';
  currentBanner.innerHTML = `
    <h3>${t.emissionsTitle}</h3>
    <p>${t.emissionsDesc}</p>
    <div class="metrics-banner">
      <div class="metric"><strong>${current.weekly_co2e_kg} kg</strong><span>${t.weeklyCo2e}</span></div>
      <div class="metric"><strong>₹${current.weekly_cost_inr}</strong><span>${t.weeklyCost}</span></div>
      <div class="metric"><strong>${current.weekly_pm_g} g</strong><span>Indoor/Tailpipe PM</span></div>
    </div>
  `;
  container.append(currentBanner);

  // Budget filter controls
  const filterWrap = document.createElement('div');
  filterWrap.className = 'budget-filters';
  filterWrap.setAttribute('role', 'group');
  filterWrap.setAttribute('aria-label', 'Budget filter options');

  const filters = [
    { id: 'any', label: t.budgetFilterAll },
    { id: 'free', label: t.budgetFilterFree },
    { id: 'under_500', label: t.budgetFilterLow },
    { id: 'under_5000', label: t.budgetFilterMid },
  ];

  filters.forEach((f) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `budget-pill ${emissionsData.budget_filter === f.id ? 'active' : ''}`;
    btn.textContent = f.label;
    btn.setAttribute('aria-pressed', emissionsData.budget_filter === f.id ? 'true' : 'false');
    btn.addEventListener('click', () => onFilterChange(f.id));
    filterWrap.append(btn);
  });
  container.append(filterWrap);

  // Alternatives cards
  const grid = document.createElement('div');
  grid.className = 'card-grid';
  emissionsData.alternatives.forEach((alt) => {
    const card = document.createElement('article');
    card.className = 'card alt-card';
    card.innerHTML = `
      <strong>${alt.title}</strong>
      <p>Avoids <strong>${alt.co2e_saved_kg} kg CO2e</strong> per week. Saves <strong>₹${alt.inr_saved_weekly}</strong>/week in fuel & expenses.</p>
      <div class="alt-footer">
        <span class="badge ${alt.upfront_cost_inr === 0 ? 'good' : 'moderate'}">${alt.upfront_cost_inr === 0 ? 'Free to adopt' : `Upfront: ~₹${alt.upfront_cost_inr}`}</span>
      </div>
    `;
    grid.append(card);
  });
  container.append(grid);
}

export function renderIndoorModule(indoorModule, language) {
  const container = $('#indoor-module-content');
  if (!container || !indoorModule) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  // CADR Calculator
  const calcCard = document.createElement('div');
  calcCard.className = 'card cadr-calc-card';
  calcCard.innerHTML = `
    <h3>${t.purifierSizingTitle}</h3>
    <p>Using the ANSI/AHAM 2/3 Rule to achieve 5 clean air changes per hour for fine smog particulate removal.</p>
    <div class="row">
      <div>
        <label for="cadr-room-area">${t.roomAreaLabel}</label>
        <input id="cadr-room-area" type="number" min="5" max="150" step="1" value="15">
      </div>
      <div>
        <label for="cadr-ceiling-height">Ceiling height (meters)</label>
        <input id="cadr-ceiling-height" type="number" min="2" max="5" step="0.1" value="2.4">
      </div>
    </div>
    <div id="cadr-output" class="metrics-banner cadr-output-metrics">
      <div class="metric"><strong id="cadr-val-m3h">180 m³/h</strong><span>Required CADR</span></div>
      <div class="metric"><strong id="cadr-val-cfm">~106 CFM</strong><span>Smoke CADR rating</span></div>
    </div>
  `;
  container.append(calcCard);

  const areaInput = calcCard.querySelector('#cadr-room-area');
  const heightInput = calcCard.querySelector('#cadr-ceiling-height');
  const updateCadr = () => {
    const a = parseFloat(areaInput.value) || 15.0;
    const h = parseFloat(heightInput.value) || 2.4;
    const vol = a * h;
    const m3h = Math.round(vol * 5);
    const cfm = Math.round(m3h / 1.699);
    calcCard.querySelector('#cadr-val-m3h').textContent = `${m3h} m³/h`;
    calcCard.querySelector('#cadr-val-cfm').textContent = `~${cfm} CFM`;
  };
  areaInput.addEventListener('input', updateCadr);
  heightInput.addEventListener('input', updateCadr);

  // DIY Fan Guide
  const diy = indoorModule.diy_box_fan_guide;
  if (diy) {
    const diyCard = document.createElement('div');
    diyCard.className = 'card diy-fan-card';
    diyCard.innerHTML = `
      <h3>${t.diyBoxFanTitle}</h3>
      <p><strong>Estimated cost:</strong> ${diy.estimated_cost_inr}. Certified efficiency: ${diy.filter_efficiency}</p>
      <h4>Materials</h4>
      <ul>${diy.materials.map((m) => `<li>${m}</li>`).join('')}</ul>
      <h4>Assembly Steps</h4>
      <ol>${diy.assembly_steps.map((s) => `<li>${s}</li>`).join('')}</ol>
      <p class="alert-notice severe">⚠️ ${t.fanWarning}</p>
    `;
    container.append(diyCard);
  }

  // Room Checklists
  const checklists = indoorModule.room_checklists;
  if (checklists) {
    const roomSec = document.createElement('div');
    roomSec.className = 'room-checklists-sec';
    roomSec.innerHTML = `<h3>Room-by-Room Air Quality Guide</h3>`;

    const tabsNav = document.createElement('div');
    tabsNav.className = 'tabs-nav';
    tabsNav.setAttribute('role', 'tablist');

    const rooms = [
      { id: 'kitchen', label: t.kitchenTab },
      { id: 'bedroom', label: t.bedroomTab },
      { id: 'living_room', label: t.livingRoomTab },
      { id: 'children_room', label: t.childrenTab },
    ];

    const tabPanels = document.createElement('div');

    rooms.forEach((r, idx) => {
      const tabBtn = document.createElement('button');
      tabBtn.type = 'button';
      tabBtn.id = `tab-${r.id}`;
      tabBtn.className = `tab-button ${idx === 0 ? 'active' : ''}`;
      tabBtn.setAttribute('role', 'tab');
      tabBtn.setAttribute('aria-selected', idx === 0 ? 'true' : 'false');
      tabBtn.setAttribute('aria-controls', `panel-${r.id}`);
      tabBtn.textContent = r.label;

      const panel = document.createElement('div');
      panel.id = `panel-${r.id}`;
      panel.className = 'tab-panel';
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', `tab-${r.id}`);
      panel.hidden = idx !== 0;

      const items = checklists[r.id] || [];
      panel.innerHTML = `
        <ul class="checklist">
          ${items.map((it) => `
            <li>
              <strong>${it.action}</strong>
              <p>${it.details}</p>
              <span class="badge good">${it.reduction_estimate}</span>
            </li>
          `).join('')}
        </ul>
      `;

      tabBtn.addEventListener('click', () => {
        tabsNav.querySelectorAll('.tab-button').forEach((b) => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        tabPanels.querySelectorAll('.tab-panel').forEach((p) => {
          p.hidden = true;
        });
        tabBtn.classList.add('active');
        tabBtn.setAttribute('aria-selected', 'true');
        panel.hidden = false;
      });

      tabsNav.append(tabBtn);
      tabPanels.append(panel);
    });

    roomSec.append(tabsNav, tabPanels);
    container.append(roomSec);
  }
}

export function renderCommunity(communityData, language) {
  const container = $('#community-content');
  if (!container || !communityData) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  const school = communityData.school_advisory;
  if (school) {
    const schoolCard = document.createElement('div');
    schoolCard.className = 'card community-card';
    schoolCard.innerHTML = `
      <h3>${school.title}</h3>
      <ul>${school.actions.map((a) => `<li>${a}</li>`).join('')}</ul>
      <a href="${communityData.whatsapp_url}" target="_blank" rel="noopener noreferrer" class="primary wa-btn">
        💬 ${t.whatsappShare}
      </a>
    `;
    container.append(schoolCard);
  }

  const rwa = communityData.rwa_checklist;
  if (rwa) {
    const rwaCard = document.createElement('div');
    rwaCard.className = 'card community-card';
    rwaCard.innerHTML = `
      <h3>${rwa.title}</h3>
      <p><em>${rwa.disclaimer}</em></p>
      <ul>
        ${rwa.items.map((it) => `<li><strong>${it.action} (${it.category}):</strong> ${it.guidance}</li>`).join('')}
      </ul>
      <button type="button" class="secondary print-btn" onclick="window.print()">
        🖨️ ${t.printPlan}
      </button>
    `;
    container.append(rwaCard);
  }
}
