/**
 * Centralized API Service for Course Progression Tracker.
 * Communicates ONLY with the FastAPI backend.
 * NO external API keys or secrets are stored in or sent by the frontend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errData = await response.json();
      errorDetail = errData.detail || errData.message || JSON.stringify(errData);
    } catch {
      errorDetail = `HTTP ${response.status} ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

/**
 * Fetch the active curriculum.
 */
export async function getCurriculum() {
  const response = await fetch(`${API_BASE_URL}/curriculum`);
  return handleResponse(response);
}

/**
 * Calculate deterministic course progression from curriculum and lecture analysis.
 */
export async function calculateProgress({ analysis, curriculum, lecture_code, date_taught, config }) {
  const response = await fetch(`${API_BASE_URL}/progress/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      analysis,
      curriculum,
      lecture_code,
      date_taught,
      config,
    }),
  });
  return handleResponse(response);
}

/**
 * Fetch Day 4 pre-configured demo scenarios for instant testing and review.
 */
export async function getDemoScenarios() {
  const response = await fetch(`${API_BASE_URL}/progress/demo`);
  return handleResponse(response);
}

/**
 * Safe backend configuration status (verifies API key status without exposing secrets).
 */
export async function getConfigStatus() {
  const response = await fetch(`${API_BASE_URL}/config/status`);
  return handleResponse(response);
}
