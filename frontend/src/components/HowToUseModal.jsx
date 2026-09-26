import React from 'react';

export default function HowToUseModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="guide-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: 'var(--radius-md)',
          maxWidth: '780px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '1px solid var(--border-color)',
          padding: '1.75rem',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '1rem',
          marginBottom: '1.25rem',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.5rem' }}>📘</span>
              <h2 id="guide-title" style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                Faculty Quick-Start Guide
              </h2>
            </div>
            <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              How the Automated Course Progression Tracker works in 6 simple steps.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              lineHeight: 1,
              padding: '0.25rem',
            }}
            aria-label="Close Guide"
          >
            ×
          </button>
        </div>

        {/* Overview Box */}
        <div style={{
          backgroundColor: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: 'var(--radius-sm)',
          padding: '0.85rem 1rem',
          marginBottom: '1.5rem',
          fontSize: '0.875rem',
          color: '#1E40AF',
          lineHeight: 1.5,
        }}>
          <strong>Purpose:</strong> This system automatically turns classroom recordings or transcripts into verified course progression entries, ensuring your official faculty progression spreadsheet is always accurate without manual data entry.
        </div>

        {/* 6 Step Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
          {/* Step 1 */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <span style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.8rem',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              1
            </span>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.925rem', color: 'var(--text-primary)' }}>
                Select Course & Curriculum
              </div>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                The curriculum is the authoritative source of truth. The system uses your course syllabus (e.g. <code>GEN-101</code>) to know which topics, classwork activities, and homework problems are planned.
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <span style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.8rem',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              2
            </span>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.925rem', color: 'var(--text-primary)' }}>
                Upload Lecture Audio or Transcript
              </div>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Provide classroom delivery data either by uploading your audio recording (<code>.mp3</code>, <code>.wav</code>, <code>.m4a</code>) for speech-to-text transcription, or typing/pasting a transcript directly.
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <span style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.8rem',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              3
            </span>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.925rem', color: 'var(--text-primary)' }}>
                Attach Supporting Materials (Optional)
              </div>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Attach lecture slides (<code>.pptx</code>), handouts (<code>.pdf</code>), or notes (<code>.docx</code>). The parser extracts slide text to cross-reference with spoken words.
              </p>
            </div>
          </div>

          {/* Step 4 */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <span style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.8rem',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              4
            </span>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.925rem', color: 'var(--text-primary)' }}>
                AI Analysis & Deterministic Progress Engine
              </div>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                The AI compares what was taught against the syllabus. Then Python arithmetic calculates:
                <br />
                <code>% Covered = (Covered + Uncertain Topics) / Total Planned × 100</code>
                <br />
                <code>% Completed = Confirmed Covered Topics / Total Planned × 100</code>
              </p>
            </div>
          </div>

          {/* Step 5 */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <span style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.8rem',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              5
            </span>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.925rem', color: 'var(--text-primary)' }}>
                Instructor Review & Pedagogical Overrides
              </div>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Inspect topics highlighted in amber (low AI confidence &lt; 65%). Use <strong>[✓ Covered]</strong> or <strong>[✗ Not Covered]</strong> buttons to override the AI based on your judgment, then sign off with your name.
              </p>
            </div>
          </div>

          {/* Step 6 */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <span style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.8rem',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              6
            </span>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.925rem', color: 'var(--text-primary)' }}>
                Excel Spreadsheet Sync & Download
              </div>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Download your official <code>course_progression.xlsx</code> file containing the required schema:
                <br />
                <code>Date Taught | Status | % Completed | % Covered | CW | HW</code>.
              </p>
            </div>
          </div>
        </div>

        {/* Common Questions */}
        <div style={{
          backgroundColor: '#F8FAFC',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid #E2E8F0',
          padding: '1rem',
          fontSize: '0.825rem',
          color: '#334155',
        }}>
          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: '700', color: '#1E293B' }}>
            💡 Frequently Asked Questions
          </h4>
          <ul style={{ margin: 0, paddingLeft: '1.25rem', lineHeight: 1.6 }}>
            <li><strong>Will the AI invent homework?</strong> No. If homework wasn't mentioned in the lecture, the HW cell is left blank.</li>
            <li><strong>Will updating an existing sheet overwrite my old lectures?</strong> No. It searches by date/lecture and either updates that row or appends a new one, keeping historical entries intact.</li>
            <li><strong>Can I run a quick test without audio?</strong> Yes! Select any of the pre-configured scenarios in the dropdown to test the workflow instantly.</li>
          </ul>
        </div>

        {/* Modal Footer */}
        <div style={{ marginTop: '1.25rem', textAlign: 'right' }}>
          <button
            onClick={onClose}
            style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '600',
              fontSize: '0.875rem',
              padding: '0.55rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Got it, let's start!
          </button>
        </div>
      </div>
    </div>
  );
}
