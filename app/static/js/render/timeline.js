/**
 * 24-hour timeline and accessible data table rendering.
 */

import { translations } from "../i18n.js";
import { $, aqiLevel } from "../utils.js";

export function renderTimeline(hourly, language) {
  const timeline = $("#timeline");
  const tbody = $("#timeline-table tbody");
  if (!timeline || !tbody) return;
  timeline.replaceChildren();
  tbody.replaceChildren();
  const t = translations[language] || translations.en;

  for (const row of hourly) {
    const level = aqiLevel(row.aqi, language);
    const hourDiv = document.createElement("div");
    hourDiv.className = "timeline-hour";
    hourDiv.dataset.level = level.slug;

    const hourText = document.createElement("strong");
    hourText.textContent = `${row.hour}:00`;
    const aqiSpan = document.createElement("span");
    aqiSpan.textContent = `${level.icon} AQI ${row.aqi}`;

    hourDiv.append(hourText, document.createElement("br"), aqiSpan);
    timeline.append(hourDiv);

    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = `${row.hour}:00`;
    tr.append(th);

    const cols = [row.pm25, row.aqi, row.exposure, row.interpolated ? t.interpolated : t.forecast];
    for (const val of cols) {
      const td = document.createElement("td");
      td.textContent = String(val);
      tr.append(td);
    }
    tbody.append(tr);
  }
}
