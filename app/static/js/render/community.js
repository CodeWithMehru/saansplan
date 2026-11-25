/**
 * School day advisories and RWA community checklist rendering.
 */

import { translations } from "../../i18n.js";
import { $ } from "../utils.js";

export function renderCommunity(communityData, language) {
  const container = $("#community-content");
  if (!container || !communityData) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  const school = communityData.school_advisory;
  if (school) {
    const schoolCard = document.createElement("div");
    schoolCard.className = "card community-card";
    schoolCard.innerHTML = `
      <h3>${school.title}</h3>
      <ul>${school.actions.map((a) => `<li>${a}</li>`).join("")}</ul>
      <a href="${communityData.whatsapp_url}" target="_blank" rel="noopener noreferrer" class="primary wa-btn">
        💬 ${t.whatsappShare}
      </a>
    `;
    container.append(schoolCard);
  }

  const rwa = communityData.rwa_checklist;
  if (rwa) {
    const rwaCard = document.createElement("div");
    rwaCard.className = "card community-card";
    rwaCard.innerHTML = `
      <h3>${rwa.title}</h3>
      <p><em>${rwa.disclaimer}</em></p>
      <ul>
        ${rwa.items.map((it) => `<li><strong>${it.action} (${it.category}):</strong> ${it.guidance}</li>`).join("")}
      </ul>
      <button type="button" class="secondary print-btn" onclick="window.print()">
        🖨️ ${t.printPlan}
      </button>
    `;
    container.append(rwaCard);
  }
}
