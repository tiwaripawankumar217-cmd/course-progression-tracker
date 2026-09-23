import React from 'react';

export default function HomeworkSection({ homework }) {
  const hasItems = homework && homework.length > 0;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      padding: '1.25rem',
      flex: '1 1 300px',
    }}>
      <h3 style={{
        fontSize: '1rem',
        fontWeight: '600',
        color: 'var(--text-primary)',
        marginBottom: '0.75rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.4rem',
      }}>
        <span>📚</span> Homework Assigned
      </h3>

      {!hasItems ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontStyle: 'italic', margin: 0 }}>
          No homework detected
        </p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {homework.map((item, idx) => (
            <li
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.5rem',
                fontSize: '0.875rem',
                marginBottom: idx < homework.length - 1 ? '0.6rem' : 0,
                color: 'var(--text-primary)',
              }}
            >
              <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>✓</span>
              <div>
                <div>{item.description}</div>
                {item.evidence && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '0.15rem' }}>
                    "{item.evidence}"
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
