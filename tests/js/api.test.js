import test from "node:test";
import assert from "node:assert/strict";
import { fetchGeocode, askAssistant, fetchPlan } from "../../app/static/js/api.js";

test("fetchGeocode returns results array on success", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      results: [{ name: "Delhi", latitude: 28.6, longitude: 77.2 }],
    }),
  });

  try {
    const results = await fetchGeocode("Delhi");
    assert.equal(results.length, 1);
    assert.equal(results[0].name, "Delhi");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchGeocode throws Error on server error", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    json: async () => ({ detail: "Geocode upstream timeout" }),
  });

  try {
    await assert.rejects(fetchGeocode("Unknown"), /Geocode upstream timeout/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("askAssistant returns answer string on success", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({ answer: "Keep windows closed during morning smog." }),
  });

  try {
    const ans = await askAssistant("Should I open windows?");
    assert.equal(ans, "Keep windows closed during morning smog.");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("askAssistant throws Error on failure", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    json: async () => ({ detail: "Rate limit exceeded" }),
  });

  try {
    await assert.rejects(askAssistant("test"), /Rate limit exceeded/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchPlan returns full plan payload on success", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      ai_available: true,
      exposure: { total_before: 100 },
    }),
  });

  try {
    const plan = await fetchPlan({ latitude: 28.6, longitude: 77.2, members: [] });
    assert.equal(plan.ai_available, true);
    assert.equal(plan.exposure.total_before, 100);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
