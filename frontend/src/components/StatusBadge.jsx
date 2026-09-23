import React from 'react';

export default function StatusBadge({ status }) {
  const normalized = (status || 'UNKNOWN').toUpperCase();

  let badgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.35rem',
    fontSize: '0.8rem',
    fontWeight: '600',
    padding: '0.2rem 0.65rem',
    borderRadius: '9999px',
    letterSpacing: '0.025em',
  };

  let icon = '•';

  if (normalized === 'COMPLETED') {
    badgeStyle.backgroundColor = 'var(--success-bg)';
    badgeStyle.color = 'var(--success)';
    badgeStyle.border = '1px solid var(--success-border)';
    icon = '✓';
  } else if (normalized === 'ONGOING') {
    badgeStyle.backgroundColor = 'var(--primary-subtle)';
    badgeStyle.color = 'var(--primary)';
    badgeStyle.border = '1px solid var(--primary-border)';
    icon = '⏳';
  } else if (normalized === 'SPILLED OVER') {
    badgeStyle.backgroundColor = 'var(--warning-bg)';
    badgeStyle.color = 'var(--warning)';
    badgeStyle.border = '1px solid var(--warning-border)';
    icon = '↷';
  } else if (normalized === 'UNCERTAIN' || normalized === 'NEEDS REVIEW') {
    badgeStyle.backgroundColor = 'var(--warning-bg)';
    badgeStyle.color = 'var(--warning)';
    badgeStyle.border = '1px solid var(--warning-border)';
    icon = '⚠';
  } else {
    badgeStyle.backgroundColor = 'var(--bg-subtle)';
    badgeStyle.color = 'var(--text-muted)';
    badgeStyle.border = '1px solid var(--border-color)';
    icon = '○';
  }

  return (
    <span style={badgeStyle} aria-label={`Status: ${normalized}`}>
      <span aria-hidden="true">{icon}</span>
      {normalized}
    </span>
  );
}
