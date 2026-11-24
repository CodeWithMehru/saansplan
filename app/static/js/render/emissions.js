/**
 * Carbon emissions, budget tier filtering, and sustainable alternatives rendering.
 */

import { translations } from '../../i18n.js';
import { $ } from '../utils.js';

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
