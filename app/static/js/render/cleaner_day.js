/**
 * Cleaner Day alternative routine, SVG comparison chart, and table rendering.
 */

import { translations } from "../../i18n.js";
import { $ } from "../utils.js";

function _createSummaryCard(cleanerDay, t) {
  const card = document.createElement("div");
  card.className = "cleaner-day-summary";
  const savedIntake = cleanerDay.inhaled_saved_ug || 0;
  const [lowRange, highRange] = cleanerDay.inhaled_saved_range_ug || [0, 0];
  card.innerHTML = `
    <h3>${t.cleanerDayTitle}</h3>
    <p>${t.cleanerDayDesc}</p>
    <div class="metrics-banner">
      <div class="metric"><strong>${cleanerDay.percent_reduction}%</strong><span>Lower daily exposure</span></div>
      <div class="metric"><strong>~${savedIntake} µg</strong><span>PM2.5 saved (${lowRange}–${highRange} µg physical range)</span></div>
    </div>
  `;
  return card;
}

function _createChangesSection(changes) {
  if (!changes || changes.length === 0) return null;
  const sec = document.createElement("div");
  sec.className = "cleaner-changes";
  const title = document.createElement("h4");
  title.textContent = "Optimized Daily Timing & In-Home Actions";
  const ul = document.createElement("ul");
  changes.forEach((chg) => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${chg.activity}:</strong> ${chg.reason}`;
    ul.append(li);
  });
  sec.append(title, ul);
  return sec;
}

function _renderBarsSvg(comparison, maxExp, chartHeight, barWidth, barGap) {
  let barsSvg = "";
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
  return barsSvg;
}

function _createSvgChart(comparison, t) {
  const svgWrap = document.createElement("div");
  svgWrap.className = "chart-wrap";
  const maxExp = Math.max(
    ...comparison.map((r) => Math.max(r.exposure_before, r.exposure_after)),
    50.0
  );
  const chartHeight = 160;
  const chartWidth = 560;
  const barWidth = 8;
  const barGap = 23;
  const barsSvg = _renderBarsSvg(comparison, maxExp, chartHeight, barWidth, barGap);

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
  return svgWrap;
}

function _createTableDetails(comparison, t) {
  const details = document.createElement("details");
  details.open = true;
  details.className = "comparison-details";
  details.innerHTML = `
    <summary>${t.tableAlternative}</summary>
    <div class="table-wrap" role="region" tabindex="0" aria-label="Cleaner day comparison data table">
      <table class="comparison-table">
        <caption>Hour-by-hour exposure: Current vs Cleaner Day</caption>
        <thead>
          <tr><th scope="col">Hour</th><th scope="col">PM2.5 µg/m³</th><th scope="col">${t.originalRoutine}</th><th scope="col">${t.optimizedRoutine}</th><th scope="col">Reduction</th></tr>
        </thead>
        <tbody>
          ${comparison
            .map(
              (r) => `
            <tr>
              <th scope="row">${r.hour}:00</th>
              <td>${r.pm25}</td>
              <td>${r.exposure_before}</td>
              <td>${r.exposure_after}</td>
              <td>${r.difference > 0 ? `−${r.difference}` : "0"}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
  return details;
}

export function renderCleanerDay(cleanerDay, language) {
  const container = $("#cleaner-day-content");
  if (!container || !cleanerDay) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;
  const comparison = cleanerDay.hourly_comparison || [];

  container.append(_createSummaryCard(cleanerDay, t));
  const changes = _createChangesSection(cleanerDay.changes);
  if (changes) container.append(changes);
  container.append(_createSvgChart(comparison, t));
  container.append(_createTableDetails(comparison, t));
}
