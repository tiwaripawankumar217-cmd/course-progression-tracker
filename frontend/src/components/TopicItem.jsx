import React, { useState } from 'react';

export default function TopicItem({ topic }) {
  const [isOpen, setIsOpen] = useState(false);

  const { name, status, confidence, evidence } = topic;
  const isCovered = status === 'covered';
  const isUncertain = status === 'uncertain';
  const isNotCovered = status === 'not_covered';

  let iconText = '○';
  let iconColor = 'var(--text-muted)';
  let borderColor = 'var(--border-color)';
  let bgColor = 'var(--bg-card)';
  let badgeLabel = 'Not Covered';

  if (isCovered) {
    iconText = '✓';
    iconColor = 'var(--success)';
    borderColor = 'var(--success-border)';
    bgColor = 'var(--bg-card)';
    badgeLabel = 'Covered';
  } else if (isUncertain) {
    iconText = '⚠';
    iconColor = 'var(--warning)';
    borderColor = 'var(--warning-border)';
    bgColor = 'var(--warning-bg)';
    badgeLabel = 'Needs Review';
  }

  return (
    <div style={{
      border: `1px solid ${borderColor}`,
      borderRadius: 'var(--radius-sm)',
      marginBottom: '0.6rem',
      backgroundColor: bgColor,
      transition: 'border-color 0.15s ease',
      overflow: 'hidden',
    }}>
      {/* Header Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.75rem 1rem',
          textAlign: 'left',
          fontSize: '0.95rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '22px',
            height: '22px',
            borderRadius: '4px',
            fontWeight: 'bold',
            fontSize: '0.85rem',
            color: iconColor,
            backgroundColor: isCovered ? 'var(--success-bg)' : (isUncertain ? 'var(--bg-card)' : 'var(--bg-subtle)'),
          }}>
            {iconText}
          </span>
          <span style={{
            fontWeight: isCovered ? '600' : '500',
            color: isNotCovered ? 'var(--text-muted)' : 'var(--text-primary)',
          }}>
            {name}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: '600',
            padding: '0.15rem 0.5rem',
            borderRadius: '9999px',
            color: isCovered ? 'var(--success)' : (isUncertain ? 'var(--warning)' : 'var(--text-muted)'),
            backgroundColor: isCovered ? 'var(--success-bg)' : (isUncertain ? 'var(--warning-bg)' : 'var(--bg-subtle)'),
            border: `1px solid ${borderColor}`,
          }}>
            {badgeLabel}
          </span>
          <span style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            transition: 'transform 0.2s ease',
            transform: isOpen ? 'rotate(180deg)' : 'none',
          }}>
            ▼
          </span>
        </div>
      </button>

      {/* Expandable Evidence Drawer */}
      {isOpen && (
        <div style={{
          padding: '0.75rem 1rem 1rem 1rem',
          borderTop: `1px solid ${borderColor}`,
          backgroundColor: isUncertain ? 'var(--bg-card)' : 'var(--bg-subtle)',
          fontSize: '0.85rem',
        }}>
          <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
            <div>
              <span style={{ color: 'var(--text-muted)', fontWeight: '500' }}>Status: </span>
              <strong style={{ color: isCovered ? 'var(--success)' : (isUncertain ? 'var(--warning)' : 'var(--text-secondary)') }}>
                {badgeLabel}
              </strong>
            </div>
            {confidence !== null && confidence !== undefined && (
              <div>
                <span style={{ color: 'var(--text-muted)', fontWeight: '500' }}>AI Confidence: </span>
                <strong style={{ color: confidence < 0.65 ? 'var(--warning)' : 'var(--text-primary)' }}>
                  {Math.round(confidence * 100)}%
                </strong>
              </div>
            )}
          </div>

          <div>
            <span style={{ color: 'var(--text-muted)', fontWeight: '500', display: 'block', marginBottom: '0.2rem' }}>
              Transcript Evidence Quote:
            </span>
            {evidence ? (
              <blockquote style={{
                margin: 0,
                padding: '0.5rem 0.75rem',
                backgroundColor: 'var(--bg-card)',
                borderLeft: `3px solid ${isUncertain ? 'var(--warning)' : 'var(--primary)'}`,
                borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                color: 'var(--text-secondary)',
                fontStyle: 'italic',
                lineHeight: 1.4,
              }}>
                "{evidence}"
              </blockquote>
            ) : (
              <p style={{ margin: 0, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                No transcript evidence recorded. This topic was not detected in the classroom lecture.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
