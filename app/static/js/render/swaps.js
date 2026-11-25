/**
 * Recommended routine swap cards rendering.
 */

import { $, getHumanLabel } from "../utils.js";

export function renderSwaps(swaps, language) {
  const container = $("#swaps");
  if (!container) return;
  container.replaceChildren();
  container.className = "card-grid";

  swaps.forEach((item) => {
    const card = document.createElement("article");
    card.className = "card swap-card";

    const title = document.createElement("strong");
    title.textContent = getHumanLabel(item.description_key || item.key, language);

    const body = document.createElement("p");
    const reduction = item.percent_reduction || 0;
    body.textContent = `Could reduce your family's PM2.5 intake by about ${reduction}% (estimate). ${item.emissions_note || ""}`;

    card.append(title, body);
    container.append(card);
  });
}
