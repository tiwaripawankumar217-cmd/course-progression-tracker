import React from 'react';

export default function Header({ onOpenGuide }) {
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
            AI COURSE PROGRESSION TRACKER • DAY 7
          </span>
          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: '700',
            color: 'var(--text-primary)',
            lineHeight: 1.2
          }}>
            Automated Classroom Course Progression Tracker
          </h1>
          <p style={{
            fontSize: '0.95rem',
            color: 'var(--text-secondary)',
            marginTop: '0.35rem'
          }}>
            Track delivery, review uncertain topics with pedagogical overrides, and maintain official Excel progression records.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
          {onOpenGuide && (
            <button
              onClick={onOpenGuide}
              style={{
                fontSize: '0.825rem',
                fontWeight: '600',
                color: '#1E40AF',
                backgroundColor: '#EFF6FF',
                border: '1px solid #BFDBFE',
                padding: '0.45rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
            >
              <span>📘</span> How to Use / Guide
            </button>
          )}
          <a
            href="/progress/download"
            download="course_progression.xlsx"
            style={{
              fontSize: '0.825rem',
              fontWeight: '600',
              color: '#ffffff',
              backgroundColor: '#047857',
              padding: '0.45rem 0.85rem',
              borderRadius: 'var(--radius-sm)',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <span>📥</span> Download Excel (.xlsx)
          </a>
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
      </div>
    </header>
  );
}
