/**
 * Accessibility and focus management: WCAG 2.2 AA compliant focus routing, error summary, and announcer.
 */

import { $, textContent } from '../utils.js';

export function announce(message, priority = 'polite') {
  let announcer = $(`#a11y-announcer-${priority}`);
  if (!announcer) {
    announcer = document.createElement('div');
    announcer.id = `a11y-announcer-${priority}`;
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);
  }
  // Clear and update to ensure screen reader triggers
  announcer.textContent = '';
  setTimeout(() => {
    announcer.textContent = message;
  }, 50);
}

export function moveToResults() {
  const heading = $('#results-heading');
  if (heading) {
    heading.setAttribute('tabindex', '-1');
    heading.focus();
    announce('Your customized air-quality plan is ready.', 'assertive');
  }
}

export function showErrorSummary(errors) {
  const container = $('#error-summary');
  if (!container) return;

  if (!errors || errors.length === 0) {
    container.hidden = true;
    container.replaceChildren();
    return;
  }

  container.replaceChildren();
  container.hidden = false;

  const title = document.createElement('h2');
  title.id = 'error-summary-title';
  title.textContent = 'Please fix the errors below:';
  container.appendChild(title);

  const list = document.createElement('ul');
  errors.forEach((err) => {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = `#${err.fieldId}`;
    link.textContent = err.message;
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = $(`#${err.fieldId}`);
      if (target) {
        target.focus();
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
    item.appendChild(link);
    list.appendChild(item);
  });
  container.appendChild(list);

  container.setAttribute('tabindex', '-1');
  container.focus();
  announce('Form submission error. Check the error summary.', 'assertive');
}

export function initTextScale(currentScale = 100) {
  document.documentElement.style.fontSize = `${currentScale}%`;
}

