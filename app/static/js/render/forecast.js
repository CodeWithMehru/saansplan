/**
 * Multi-day winter smog forecast cards rendering.
 */

import { translations } from "../../i18n.js";
import { $ } from "../utils.js";

export function renderForecast(forecastDays, language) {
  const container = $("#forecast-cards");
  if (!container || !forecastDays) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  forecastDays.forEach((day) => {
    const card = document.createElement("article");
    card.className = `card forecast-card ${day.is_severe ? "severe-border" : ""}`;

    const head = document.createElement("div");
    head.className = "forecast-head";
    const dayName = document.createElement("strong");
    dayName.textContent =
      day.day_index === 0 ? "Today" : day.day_index === 1 ? "Tomorrow" : `Day ${day.day_index + 1}`;
    const aqiBadge = document.createElement("span");
    aqiBadge.className = `badge ${day.category_slug}`;
    aqiBadge.textContent = `AQI ${day.peak_aqi} (${day.indian_category})`;
    head.append(dayName, aqiBadge);

    const worstP = document.createElement("p");
    worstP.innerHTML = `<strong>${t.worstWindow}:</strong> ${day.worst_window.start_hour}:00 – ${day.worst_window.end_hour}:00`;

    const bestP = document.createElement("p");
    bestP.innerHTML = `<strong>${t.bestWindow}:</strong> ${day.best_window.start_hour}:00 – ${day.best_window.end_hour}:00`;

    const airingP = document.createElement("p");
    airingP.innerHTML = `<strong>${t.safestAiring}:</strong> ${day.safest_airing_hour}:00 – ${day.safest_airing_hour + 1}:00`;

    card.append(head, worstP, bestP, airingP);

    if (day.is_stagnant) {
      const stagP = document.createElement("p");
      stagP.className = "alert-notice stagnation";
      stagP.textContent = `⚠️ ${t.stagnationAlert} (${day.avg_wind_speed_mps} m/s)`;
      card.append(stagP);
    }

    if (day.is_severe) {
      const severeP = document.createElement("p");
      severeP.className = "alert-notice severe";
      severeP.textContent = `🚨 ${t.severeSmogAlert}`;
      card.append(severeP);
    }

    container.append(card);
  });
}
