import React from 'react';
import StatusBadge from './StatusBadge';

export default function ProgressSummary({ progression }) {
  if (!progression) return null;

  const {
    lecture,
    date_taught,
    status,
    percent_covered,
    percent_completed,
  } = progression;

  return (
    <section className="academic-card" aria-label="Progress Overview">
      {/* Current Lecture & Date Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        paddingBottom: '1rem',
        marginBottom: '1.25rem',
        borderBottom: '1px solid var(--border-color)',
      }}>
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            Current Lecture
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.1rem' }}>
            {lecture}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
              Date Taught
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: '500', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
              {date_taught}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
              Lecture Status
            </div>
            <StatusBadge status={status} />
          </div>
        </div>
      </div>

      {/* Progress Bars */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        {/* % Covered */}
        <div style={{
          background: 'var(--bg-page)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          padding: '1rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
              Topics Covered
            </span>
            <span style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--primary)' }}>
              {percent_covered.toFixed(1)}%
            </span>
          </div>
          {/* Visual progress bar */}
          <div
            role="progressbar"
            aria-valuenow={percent_covered}
            aria-valuemin="0"
            aria-valuemax="100"
            aria-label={`${percent_covered.toFixed(1)}% Topics Covered`}
            style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--border-color)',
              borderRadius: '9999px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${Math.min(100, Math.max(0, percent_covered))}%`,
                height: '100%',
                backgroundColor: 'var(--primary)',
                borderRadius: '9999px',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            Curriculum content evidenced in transcript
          </div>
        </div>

        {/* % Completed */}
        <div style={{
          background: 'var(--bg-page)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          padding: '1rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
              Topics Completed
            </span>
            <span style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--success)' }}>
              {percent_completed.toFixed(1)}%
            </span>
          </div>
          {/* Visual progress bar */}
          <div
            role="progressbar"
            aria-valuenow={percent_completed}
            aria-valuemin="0"
            aria-valuemax="100"
            aria-label={`${percent_completed.toFixed(1)}% Topics Completed`}
            style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--border-color)',
              borderRadius: '9999px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${Math.min(100, Math.max(0, percent_completed))}%`,
                height: '100%',
                backgroundColor: 'var(--success)',
                borderRadius: '9999px',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            Strictly confirmed topics (excluding low-confidence/uncertain)
          </div>
        </div>
      </div>
    </section>
  );
}
