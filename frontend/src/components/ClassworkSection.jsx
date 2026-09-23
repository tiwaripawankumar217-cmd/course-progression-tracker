import React from 'react';

export default function ClassworkSection({ classwork }) {
  const hasItems = classwork && classwork.length > 0;

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
        <span>📝</span> Classwork Conducted
      </h3>

      {!hasItems ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontStyle: 'italic', margin: 0 }}>
          No classwork detected
        </p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {classwork.map((item, idx) => (
            <li
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.5rem',
                fontSize: '0.875rem',
                marginBottom: idx < classwork.length - 1 ? '0.6rem' : 0,
                color: 'var(--text-primary)',
              }}
            >
              <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span>
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
