import test from 'node:test';
import assert from 'node:assert/strict';
import { translations } from '../i18n.js';

test('all locales share the same i18n keys', () => {
  const base = Object.keys(translations.en).sort();
  for (const locale of ['hinglish', 'hi']) {
    assert.deepEqual(Object.keys(translations[locale]).sort(), base);
  }
});

test('Hindi locale contains Devanagari text', () => {
  assert.match(translations.hi.location, /[अ-ह]/);
});
