import React from 'react';

export default function WarningMessage({ warnings }) {
  const hasWarnings = warnings && warnings.length > 0;

  return (
    <section className="academic-card" aria-label="System Warnings and Notes">
      <h3 className="card-title" style={{ fontSize: '1rem', marginBottom: '0.4rem' }}>
        <span>⚠️</span> System Warnings & Pedagogical Notes
      </h3>

      {!hasWarnings ? (
        <p style={{
          color: 'var(--success)',
          fontSize: '0.875rem',
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}>
          <span>✓</span> No major issues detected. All analyzed items mapped cleanly.
        </p>
      ) : (
        <div style={{
          backgroundColor: 'var(--warning-bg)',
          border: '1px solid var(--warning-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.75rem 1rem',
        }}>
          <ul style={{ paddingLeft: '1.25rem', margin: 0 }}>
            {warnings.map((warn, idx) => (
              <li
                key={idx}
                style={{
                  fontSize: '0.85rem',
                  color: 'var(--warning)',
                  marginBottom: idx < warnings.length - 1 ? '0.35rem' : 0,
                }}
              >
                {warn}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
