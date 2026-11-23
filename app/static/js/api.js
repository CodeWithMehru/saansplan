/**
 * API client module: handles network requests, timeouts, and structured error responses.
 */

export async function fetchPlan(payload) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 14000);
  try {
    const response = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data.error?.message || data.detail || 'Unable to generate plan';
      throw new Error(msg);
    }
    return data;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function fetchGeocode(city) {
  const response = await fetch(`/api/geocode?name=${encodeURIComponent(city)}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'City search failed');
  }
  return data.results || [];
}

export async function askAssistant(question) {
  const response = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Could not answer this question.');
  }
  return data.answer;
}

