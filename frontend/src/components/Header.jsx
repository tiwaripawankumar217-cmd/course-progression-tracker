import React from 'react';

export default function Header() {
  return (
    <header style={{
      marginBottom: '2rem',
      borderBottom: '1px solid var(--border-color)',
      paddingBottom: '1.25rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: '700',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: 'var(--primary)',
            display: 'block',
            marginBottom: '0.25rem'
          }}>
            AI COURSE PROGRESSION • DAY 4
          </span>
          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: '700',
            color: 'var(--text-primary)',
            lineHeight: 1.2
          }}>
            Lecture Analysis & Curriculum Mapping
          </h1>
          <p style={{
            fontSize: '0.95rem',
            color: 'var(--text-secondary)',
            marginTop: '0.35rem'
          }}>
            Track what was actually taught and map it to the curriculum with deterministic verification.
          </p>
        </div>
        <div style={{
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          background: 'var(--bg-card)',
          padding: '0.4rem 0.75rem',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)'
        }}>
          Deterministic Engine • Zero LLM Math
        </div>
      </div>
    </header>
  );
}
