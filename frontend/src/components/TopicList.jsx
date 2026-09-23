import React from 'react';
import TopicItem from './TopicItem';

export default function TopicList({ topics }) {
  if (!topics || topics.length === 0) {
    return (
      <section className="academic-card">
        <h2 className="card-title">Curriculum Topics</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
          No curriculum topics mapped for this lecture.
        </p>
      </section>
    );
  }

  const coveredCount = topics.filter(t => t.status === 'covered').length;
  const uncertainCount = topics.filter(t => t.status === 'uncertain').length;

  return (
    <section className="academic-card" aria-label="Curriculum Topics Mapping">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div>
          <h2 className="card-title" style={{ marginBottom: '0.1rem' }}>
            Curriculum Topics
          </h2>
          <p className="card-subtitle" style={{ marginBottom: 0 }}>
            Click any topic to review AI evidence quotes and confidence scores.
          </p>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          <strong>{coveredCount}</strong> of <strong>{topics.length}</strong> covered
          {uncertainCount > 0 && (
            <span style={{ color: 'var(--warning)', marginLeft: '0.5rem', fontWeight: '600' }}>
              ({uncertainCount} review needed)
            </span>
          )}
        </div>
      </div>

      <div style={{ marginTop: '1rem' }}>
        {topics.map((topic, idx) => (
          <TopicItem key={`${topic.name}-${idx}`} topic={topic} />
        ))}
      </div>
    </section>
  );
}
