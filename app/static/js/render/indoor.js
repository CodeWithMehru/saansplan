/**
 * Indoor air quality interventions: CADR calculator, DIY fan guide, and room checklists.
 */

import { translations } from "../../i18n.js";
import { $ } from "../utils.js";

function _buildCadrCard(t) {
  const card = document.createElement("div");
  card.className = "card cadr-calc-card";
  card.innerHTML = `
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
  const areaInput = card.querySelector("#cadr-room-area");
  const heightInput = card.querySelector("#cadr-ceiling-height");
  const updateCadr = () => {
    const a = areaInput instanceof HTMLInputElement ? parseFloat(areaInput.value) || 15.0 : 15.0;
    const h = heightInput instanceof HTMLInputElement ? parseFloat(heightInput.value) || 2.4 : 2.4;
    const vol = a * h;
    const m3h = Math.round(vol * 5);
    const cfm = Math.round(m3h / 1.699);
    card.querySelector("#cadr-val-m3h").textContent = `${m3h} m³/h`;
    card.querySelector("#cadr-val-cfm").textContent = `~${cfm} CFM`;
  };
  areaInput.addEventListener("input", updateCadr);
  heightInput.addEventListener("input", updateCadr);
  return card;
}

function _buildDiyGuide(diy, t) {
  if (!diy) return null;
  const card = document.createElement("div");
  card.className = "card diy-fan-card";
  card.innerHTML = `
    <h3>${t.diyBoxFanTitle}</h3>
    <p><strong>Estimated cost:</strong> ${diy.estimated_cost_inr}. Certified efficiency: ${diy.filter_efficiency}</p>
    <h4>Materials</h4>
    <ul>${diy.materials.map((m) => `<li>${m}</li>`).join("")}</ul>
    <h4>Assembly Steps</h4>
    <ol>${diy.assembly_steps.map((s) => `<li>${s}</li>`).join("")}</ol>
    <p class="alert-notice severe">⚠️ ${t.fanWarning}</p>
  `;
  return card;
}

function _createRoomPanel(r, items, isActive) {
  const panel = document.createElement("div");
  panel.id = `panel-${r.id}`;
  panel.className = "tab-panel";
  panel.setAttribute("role", "tabpanel");
  panel.setAttribute("aria-labelledby", `tab-${r.id}`);
  panel.hidden = !isActive;
  panel.innerHTML = `
    <ul class="checklist">
      ${items
        .map(
          (it) => `
        <li>
          <strong>${it.action}</strong>
          <p>${it.details}</p>
          <span class="badge good">${it.reduction_estimate}</span>
        </li>
      `
        )
        .join("")}
    </ul>
  `;
  return panel;
}

function _buildRoomChecklists(checklists, t) {
  if (!checklists) return null;
  const roomSec = document.createElement("div");
  roomSec.className = "room-checklists-sec";
  roomSec.innerHTML = `<h3>Room-by-Room Air Quality Guide</h3>`;

  const tabsNav = document.createElement("div");
  tabsNav.className = "tabs-nav";
  tabsNav.setAttribute("role", "tablist");
  const tabPanels = document.createElement("div");

  const rooms = [
    { id: "kitchen", label: t.kitchenTab },
    { id: "bedroom", label: t.bedroomTab },
    { id: "living_room", label: t.livingRoomTab },
    { id: "children_room", label: t.childrenTab },
  ];

  rooms.forEach((r, idx) => {
    const isActive = idx === 0;
    const tabBtn = document.createElement("button");
    tabBtn.type = "button";
    tabBtn.id = `tab-${r.id}`;
    tabBtn.className = `tab-button ${isActive ? "active" : ""}`;
    tabBtn.setAttribute("role", "tab");
    tabBtn.setAttribute("aria-selected", isActive ? "true" : "false");
    tabBtn.setAttribute("aria-controls", `panel-${r.id}`);
    tabBtn.textContent = r.label;

    const panel = _createRoomPanel(r, checklists[r.id] || [], isActive);

    tabBtn.addEventListener("click", () => {
      tabsNav.querySelectorAll(".tab-button").forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      tabPanels.querySelectorAll(".tab-panel").forEach((p) => {
        if (p instanceof HTMLElement) {
          p.hidden = true;
        }
      });
      tabBtn.classList.add("active");
      tabBtn.setAttribute("aria-selected", "true");
      panel.hidden = false;
    });

    tabsNav.append(tabBtn);
    tabPanels.append(panel);
  });

  roomSec.append(tabsNav, tabPanels);
  return roomSec;
}

export function renderIndoorModule(indoorModule, language) {
  const container = $("#indoor-module-content");
  if (!container || !indoorModule) return;
  container.replaceChildren();
  const t = translations[language] || translations.en;

  container.append(_buildCadrCard(t));
  const diy = _buildDiyGuide(indoorModule.diy_box_fan_guide, t);
  if (diy) container.append(diy);
  const checklists = _buildRoomChecklists(indoorModule.room_checklists, t);
  if (checklists) container.append(checklists);
}
