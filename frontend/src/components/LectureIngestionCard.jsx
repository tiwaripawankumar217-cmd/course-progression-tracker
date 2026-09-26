import React, { useState } from 'react';
import { uploadLectureAudio, fetchSampleAudio, analyzeLectureWithUpload } from '../services/api';

export default function LectureIngestionCard({
  curriculum,
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  onAnalysisCalculated,
  loading,
}) {
  const [activeTab, setActiveTab] = useState('scenarios'); // 'scenarios' | 'audio' | 'transcript'
  const [audioFile, setAudioFile] = useState(null);
  const [audioUploading, setAudioUploading] = useState(false);
  const [transcriptText, setTranscriptText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [selectedLectureCode, setSelectedLectureCode] = useState('LEC-1');
  const [dateTaught, setDateTaught] = useState(new Date().toISOString().split('T')[0]);
  const [statusNotice, setStatusNotice] = useState(null);
  const [errorNotice, setErrorNotice] = useState(null);

  // Available lectures from loaded curriculum
  const lectures = curriculum?.lectures || [
    { lecture: 'LEC-1', content: ['Topic A: Core Principles', 'Topic B: Conceptual Framework'] },
    { lecture: 'LEC-2', content: ['Topic D: Analysis Techniques', 'Topic E: Quantitative Application'] },
    { lecture: 'LEC-3', content: ['Topic G: Advanced Synthesis', 'Topic H: Diagnostics'] },
  ];

  // Helper to load sample test audio from backend
  async function handleLoadSampleAudio() {
    setAudioUploading(true);
    setStatusNotice(null);
    setErrorNotice(null);
    try {
      const sampleFile = await fetchSampleAudio();
      setAudioFile(sampleFile);
      setStatusNotice('Sample classroom audio recording loaded (sample_lecture.wav, 8kHz PCM). Click "Transcribe Audio" below.');
    } catch (err) {
      setErrorNotice(`Failed to load sample audio: ${err.message}`);
    } finally {
      setAudioUploading(false);
    }
  }

  // Transcribe uploaded or sample audio
  async function handleTranscribeAudio() {
    if (!audioFile) {
      setErrorNotice('Please select or load an audio file first.');
      return;
    }
    setAudioUploading(true);
    setStatusNotice('Transcribing audio via Speech-to-Text service...');
    setErrorNotice(null);
    try {
      const res = await uploadLectureAudio(audioFile, 'mock');
      setTranscriptText(res.transcript || '');
      setStatusNotice(`Transcription complete! Duration: ${res.duration || 1}s. Review or edit transcript below.`);
      setActiveTab('transcript');
    } catch (err) {
      setErrorNotice(`Transcription failed: ${err.message}`);
    } finally {
      setAudioUploading(false);
    }
  }

  // Preset transcript samples
  function loadPresetTranscript(type) {
    if (type === 'arrays') {
      setSelectedLectureCode('LEC-1');
      setTranscriptText(
        "Welcome class. Today we covered Core Principles of data organization and contiguous memory allocation. " +
        "We also reviewed the Conceptual Framework and Terminology for static arrays. " +
        "For classwork, students completed Activity 1: Guided Concept Review. " +
        "Homework assigned is Homework 1: Practice Exercises due next week."
      );
      setStatusNotice("Loaded preset transcript for Lecture 1 (Arrays & Principles).");
    } else if (type === 'complexity') {
      setSelectedLectureCode('LEC-2');
      setTranscriptText(
        "Today we started Analysis and Decomposition Techniques. " +
        "We analyzed single loops and nested iterations. " +
        "Classwork was Activity 3: Collaborative Case Exploration. " +
        "Homework 2: Structured Problem Formulation was assigned."
      );
      setStatusNotice("Loaded preset transcript for Lecture 2 (Decomposition & Analysis).");
    }
  }

  // Execute full analysis & progress mapping
  async function handleRunLiveAnalysis() {
    if (!transcriptText || !transcriptText.trim()) {
      setErrorNotice('Please enter or transcribe lecture text before running analysis.');
      return;
    }

    setStatusNotice('Analyzing lecture delivery against active curriculum...');
    setErrorNotice(null);

    try {
      const res = await analyzeLectureWithUpload({
        transcript: transcriptText.trim(),
        files: attachedFiles,
        provider: 'mock',
        confidenceThreshold: 0.65,
      });

      if (res && res.success && res.analysis) {
        setStatusNotice('AI analysis complete! Calculating deterministic progression...');
        onAnalysisCalculated(res.analysis, selectedLectureCode, dateTaught);
      } else {
        throw new Error(res?.warnings?.join(' ') || 'Analysis failed to return a valid result.');
      }
    } catch (err) {
      setErrorNotice(`Analysis failed: ${err.message}`);
    }
  }

  function handleFileAttach(e) {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setAttachedFiles((prev) => [...prev, ...newFiles]);
    }
  }

  function handleRemoveFile(indexToRemove) {
    setAttachedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  }

  return (
    <section className="academic-card" aria-label="Lecture Ingestion Workflow">
      {/* Workflow Stepper Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1rem',
        borderBottom: '1px solid var(--border-color)',
        paddingBottom: '0.75rem',
      }}>
        <div>
          <h2 className="card-title" style={{ fontSize: '1.1rem', margin: 0 }}>
            <span>🧭</span> Workflow Steps 1 – 4: Ingestion & Analysis
          </h2>
          <p className="card-subtitle" style={{ margin: '0.2rem 0 0 0' }}>
            Course: <strong>{curriculum?.course_name || 'Foundational Course'}</strong> ({curriculum?.course_id || 'GEN-101'})
          </p>
        </div>

        {/* Tab Switcher */}
        <div style={{
          display: 'inline-flex',
          backgroundColor: 'var(--bg-subtle)',
          padding: '0.25rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-color)',
          gap: '0.25rem',
        }}>
          <button
            onClick={() => setActiveTab('scenarios')}
            style={{
              padding: '0.4rem 0.85rem',
              fontSize: '0.85rem',
              fontWeight: '600',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: activeTab === 'scenarios' ? 'var(--bg-card)' : 'transparent',
              color: activeTab === 'scenarios' ? 'var(--primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'scenarios' ? 'var(--shadow-sm)' : 'none',
            }}
          >
            ⚡ Pre-loaded Scenarios
          </button>

          <button
            onClick={() => setActiveTab('audio')}
            style={{
              padding: '0.4rem 0.85rem',
              fontSize: '0.85rem',
              fontWeight: '600',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: activeTab === 'audio' ? 'var(--bg-card)' : 'transparent',
              color: activeTab === 'audio' ? 'var(--primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'audio' ? 'var(--shadow-sm)' : 'none',
            }}
          >
            🎙️ Audio Ingestion
          </button>

          <button
            onClick={() => setActiveTab('transcript')}
            style={{
              padding: '0.4rem 0.85rem',
              fontSize: '0.85rem',
              fontWeight: '600',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: activeTab === 'transcript' ? 'var(--bg-card)' : 'transparent',
              color: activeTab === 'transcript' ? 'var(--primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'transcript' ? 'var(--shadow-sm)' : 'none',
            }}
          >
            📝 Transcript & Materials
          </button>
        </div>
      </div>

      {/* Notifications */}
      {statusNotice && (
        <div style={{
          backgroundColor: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: 'var(--radius-sm)',
          padding: '0.65rem 0.9rem',
          marginBottom: '1rem',
          color: '#1E40AF',
          fontSize: '0.85rem',
        }}>
          ℹ️ {statusNotice}
        </div>
      )}

      {errorNotice && (
        <div style={{
          backgroundColor: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.65rem 0.9rem',
          marginBottom: '1rem',
          color: 'var(--danger)',
          fontSize: '0.85rem',
        }}>
          ⚠️ {errorNotice}
        </div>
      )}

      {/* Tab 1: Pre-loaded Demo Scenarios */}
      {activeTab === 'scenarios' && (
        <div>
          <label
            htmlFor="scenario-select"
            style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}
          >
            Choose Demonstration Scenario:
          </label>
          <select
            id="scenario-select"
            value={selectedScenarioId}
            onChange={(e) => onSelectScenario(e.target.value)}
            style={{
              width: '100%',
              padding: '0.65rem 0.85rem',
              fontSize: '0.9rem',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--bg-card)',
              color: 'var(--text-primary)',
              marginBottom: '0.75rem',
            }}
          >
            {scenarios.map(sc => (
              <option key={sc.id} value={sc.id}>
                {sc.title} — {sc.description}
              </option>
            ))}
          </select>
          <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            💡 Pre-loaded scenarios allow instant verification of complete, partial, spilled-over, and low-confidence review flows.
          </p>
        </div>
      )}

      {/* Tab 2: Audio Upload & Transcription */}
      {activeTab === 'audio' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Upload Classroom Audio Recording (.mp3, .wav, .m4a):
            </label>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="file"
                accept="audio/*,.mp3,.wav,.m4a,.aac,.webm,.ogg"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setAudioFile(e.target.files[0]);
                    setStatusNotice(`Selected audio file: ${e.target.files[0].name} (${(e.target.files[0].size / 1024).toFixed(1)} KB)`);
                  }
                }}
                disabled={audioUploading}
                style={{ fontSize: '0.85rem' }}
              />

              <button
                type="button"
                onClick={handleLoadSampleAudio}
                disabled={audioUploading}
                style={{
                  padding: '0.45rem 0.85rem',
                  fontSize: '0.8rem',
                  fontWeight: '600',
                  color: 'var(--primary)',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                }}
              >
                ⚡ Load Sample Audio (WAV)
              </button>
            </div>
          </div>

          <div>
            <button
              onClick={handleTranscribeAudio}
              disabled={audioUploading || !audioFile}
              style={{
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                fontWeight: '600',
                fontSize: '0.875rem',
                padding: '0.6rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                cursor: audioUploading || !audioFile ? 'not-allowed' : 'pointer',
                opacity: audioUploading || !audioFile ? 0.6 : 1,
              }}
            >
              {audioUploading ? 'Transcribing...' : '🎙️ Transcribe Audio to Text'}
            </button>
          </div>
        </div>
      )}

      {/* Tab 3: Transcript & Supporting Materials */}
      {activeTab === 'transcript' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Preset Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Presets:</span>
            <button
              type="button"
              onClick={() => loadPresetTranscript('arrays')}
              style={{
                padding: '0.35rem 0.75rem',
                fontSize: '0.8rem',
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
              }}
            >
              Sample: Lecture 1 (Arrays)
            </button>
            <button
              type="button"
              onClick={() => loadPresetTranscript('complexity')}
              style={{
                padding: '0.35rem 0.75rem',
                fontSize: '0.8rem',
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
              }}
            >
              Sample: Lecture 2 (Analysis)
            </button>
          </div>

          {/* Target Lecture Code and Date */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                Target Lecture:
              </label>
              <select
                value={selectedLectureCode}
                onChange={(e) => setSelectedLectureCode(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.85rem',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                {lectures.map((l, i) => (
                  <option key={i} value={l.lecture}>
                    {l.lecture} ({l.content ? l.content.slice(0, 2).join(', ') : ''}...)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                Date Taught:
              </label>
              <input
                type="date"
                value={dateTaught}
                onChange={(e) => setDateTaught(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.85rem',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                }}
              />
            </div>
          </div>

          {/* Transcript Textarea */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Lecture Spoken Transcript:
            </label>
            <textarea
              rows={4}
              value={transcriptText}
              onChange={(e) => setTranscriptText(e.target.value)}
              placeholder="Paste or type what was taught in the lecture, or transcribe from audio above..."
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                fontSize: '0.85rem',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'inherit',
                lineHeight: 1.4,
              }}
            />
          </div>

          {/* Supporting Materials Upload */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              Attach Supporting Documents (PDF, PPTX, DOCX, TXT):
            </label>
            <input
              type="file"
              multiple
              accept=".pdf,.pptx,.docx,.txt,.md"
              onChange={handleFileAttach}
              style={{ fontSize: '0.85rem' }}
            />
            {attachedFiles.length > 0 && (
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                {attachedFiles.map((f, idx) => (
                  <span
                    key={idx}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      fontSize: '0.75rem',
                      backgroundColor: 'var(--bg-subtle)',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    📄 {f.name}
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: 0 }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Submit Live Analysis Button */}
          <div>
            <button
              onClick={handleRunLiveAnalysis}
              disabled={loading || !transcriptText.trim()}
              style={{
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                fontWeight: '600',
                fontSize: '0.9rem',
                padding: '0.65rem 1.4rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                cursor: loading || !transcriptText.trim() ? 'not-allowed' : 'pointer',
                opacity: loading || !transcriptText.trim() ? 0.6 : 1,
                boxShadow: 'var(--shadow-sm)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <span>🚀</span>
              {loading ? 'Processing...' : 'Run Lecture Analysis & Map Progress'}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
