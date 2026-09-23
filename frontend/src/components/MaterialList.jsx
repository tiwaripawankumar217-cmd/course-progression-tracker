import React from 'react';

export default function MaterialList({ materials }) {
  if (!materials || materials.length === 0) return null;

  return (
    <section className="academic-card" aria-label="Supporting Materials">
      <h3 className="card-title" style={{ fontSize: '1rem', marginBottom: '0.4rem' }}>
        <span>📎</span> Supporting Materials Used
      </h3>
      <p className="card-subtitle" style={{ marginBottom: '0.75rem' }}>
        Curriculum, slide decks, readings, and lecture notes processed as academic context.
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
        {materials.map((mat, idx) => {
          const isFailed = mat.status === 'failed' || Boolean(mat.error);
          return (
            <div
              key={idx}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontSize: '0.825rem',
                padding: '0.35rem 0.65rem',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: isFailed ? 'var(--warning-bg)' : 'var(--bg-subtle)',
                border: `1px solid ${isFailed ? 'var(--warning-border)' : 'var(--border-color)'}`,
                color: isFailed ? 'var(--warning)' : 'var(--text-secondary)',
              }}
            >
              <span>{isFailed ? '⚠' : '✓'}</span>
              <span style={{ fontWeight: '500' }}>{mat.name}</span>
              {isFailed && (
                <span style={{ fontSize: '0.75rem', fontStyle: 'italic', marginLeft: '0.2rem' }}>
                  ({mat.error || 'Could not be processed'})
                </span>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
