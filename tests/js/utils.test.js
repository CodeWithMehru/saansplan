import test from "node:test";
import assert from "node:assert/strict";
import { aqiLevel, getHumanLabel } from "../../app/static/js/utils.js";

test("aqiLevel categorizes standard CPCB breakpoints correctly", () => {
  assert.equal(aqiLevel(30).level, "good");
  assert.equal(aqiLevel(50).level, "good");
  assert.equal(aqiLevel(75).level, "satisfactory");
  assert.equal(aqiLevel(100).level, "satisfactory");
  assert.equal(aqiLevel(150).level, "moderate");
  assert.equal(aqiLevel(200).level, "moderate");
  assert.equal(aqiLevel(250).level, "poor");
  assert.equal(aqiLevel(300).level, "poor");
  assert.equal(aqiLevel(350).level, "very-poor");
  assert.equal(aqiLevel(400).level, "very-poor");
  assert.equal(aqiLevel(450).level, "severe");
  assert.equal(aqiLevel(999).level, "severe");
});

test("aqiLevel handles zero, negative, and invalid numeric values", () => {
  assert.equal(aqiLevel(0).level, "good");
  assert.equal(aqiLevel(-10).level, "good");
  assert.equal(aqiLevel("invalid").level, "good");
});

test("getHumanLabel returns localized text across all 3 languages", () => {
  const key = "swap_purifier";
  assert.match(getHumanLabel(key, "en"), /HEPA/i);
  assert.match(getHumanLabel(key, "hinglish"), /purifier chalayein/i);
  assert.match(getHumanLabel(key, "hi"), /प्यूरीफायर/);
});

test("getHumanLabel provides clean human fallback for unknown keys", () => {
  assert.equal(getHumanLabel(""), "Cleaner daily action");
  assert.equal(getHumanLabel(null), "Cleaner daily action");
  assert.equal(getHumanLabel("custom_indoor_action", "en"), "Custom Indoor Action");
});
