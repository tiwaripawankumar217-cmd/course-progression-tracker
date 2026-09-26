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

/**
 * Upload lecture audio recording (.mp3, .wav, .m4a) for speech-to-text transcription.
 */
export async function uploadLectureAudio(audioFile, provider = 'mock') {
  const formData = new FormData();
  formData.append('file', audioFile);
  const response = await fetch(`${API_BASE_URL}/lecture/audio?provider=${provider}`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

/**
 * Fetch sample test audio (WAV) directly from the backend.
 */
export async function fetchSampleAudio() {
  const response = await fetch(`${API_BASE_URL}/lecture/sample-audio`);
  if (!response.ok) throw new Error('Failed to generate sample audio');
  const blob = await response.blob();
  return new File([blob], 'sample_lecture.wav', { type: 'audio/wav' });
}

/**
 * Analyze lecture delivery with transcript and optional supporting documents (PDF, PPTX, DOCX, TXT).
 */
export async function analyzeLectureWithUpload({ transcript, files = [], provider = 'mock', confidenceThreshold = 0.65 }) {
  const formData = new FormData();
  formData.append('transcript', transcript);
  if (files && files.length > 0) {
    for (const f of files) {
      formData.append('files', f);
    }
  }
  const providerParam = provider ? `provider=${provider}&` : '';
  const response = await fetch(`${API_BASE_URL}/analyze/upload?${providerParam}confidence_threshold=${confidenceThreshold}`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

/**
 * Export Day 4 progression to Excel (.xlsx) file and trigger browser download.
 */
export async function exportProgressionExcel(progression, customFilename = null) {
  const response = await fetch(`${API_BASE_URL}/progress/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      progression,
      file_name: customFilename,
    }),
  });

  if (!response.ok) {
    let errorDetail = 'Excel export failed';
    try {
      const errData = await response.json();
      errorDetail = errData.detail || errData.message || JSON.stringify(errData);
    } catch {
      errorDetail = `HTTP ${response.status} ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;

  let filename = customFilename;
  const disposition = response.headers.get('Content-Disposition');
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename=["']?([^"';]+)["']?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }
  if (!filename) {
    const dateStr = progression?.date_taught || 'export';
    filename = `course_progression_${dateStr}.xlsx`;
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
  return { success: true, filename };
}

/**
 * Update an existing progression workbook (.xlsx) with new lecture progression.
 */
export async function updateProgressionExcel(existingFile, progression) {
  const formData = new FormData();
  formData.append('file', existingFile);
  formData.append('progression_json', JSON.stringify(progression));

  const response = await fetch(`${API_BASE_URL}/progress/export/update`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'Updating Excel workbook failed';
    try {
      const errData = await response.json();
      errorDetail = errData.detail || errData.message || JSON.stringify(errData);
    } catch {
      errorDetail = `HTTP ${response.status} ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;

  let filename = existingFile.name || 'course_progression_updated.xlsx';
  const disposition = response.headers.get('Content-Disposition');
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename=["']?([^"';]+)["']?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
  return { success: true, filename };
}

/**
 * Approve reviewed lecture progression and commit to official records.
 */
export async function approveTeacherReview({ progression, instructorName, comments, commitToExcel = true }) {
  const response = await fetch(`${API_BASE_URL}/progress/review/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      progression,
      instructor_name: instructorName,
      comments,
      commit_to_excel: commitToExcel,
    }),
  });
  return handleResponse(response);
}
