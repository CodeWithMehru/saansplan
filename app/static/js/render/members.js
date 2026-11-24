/**
 * Family member profile configuration rendering.
 */

import { translations } from '../../i18n.js';
import { $ } from '../utils.js';

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
