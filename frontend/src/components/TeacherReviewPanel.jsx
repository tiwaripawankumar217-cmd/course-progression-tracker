import React, { useState } from 'react';
import { approveTeacherReview } from '../services/api';

export default function TeacherReviewPanel({
  progression,
  onProgressionUpdated,
}) {
  const [instructorName, setInstructorName] = useState('Prof. Sharma');
  const [comments, setComments] = useState('');
  const [commitToExcel, setCommitToExcel] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [approvalResult, setApprovalResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!progression) return null;

  // Find uncertain topics that need urgent inspection
  const uncertainTopics = (progression.topics || []).filter(t => t.status === 'uncertain');
  const allTopics = progression.topics || [];

  // Deterministic live recalculation helper
  function updateTopicStatus(topicName, newStatus) {
    const updatedTopics = allTopics.map(t => {
      if (t.name === topicName) {
        return {
          ...t,
          status: newStatus,
          // If manually marked covered, ensure confidence is evidenced
          confidence: newStatus === 'covered' ? Math.max(t.confidence || 0.9, 0.9) : t.confidence,
        };
      }
      return t;
    });

    const total = updatedTopics.length;
    const coveredCount = updatedTopics.filter(t => t.status === 'covered').length;
    const uncertainCount = updatedTopics.filter(t => t.status === 'uncertain').length;

    const newCoveredPct = total > 0 ? Number((((coveredCount + uncertainCount) / total) * 100).toFixed(2)) : 0;
    const newCompletedPct = total > 0 ? Number(((coveredCount / total) * 100).toFixed(2)) : 0;

    let newStatusVal = 'NOT_STARTED';
    if (newCompletedPct >= 100) {
      newStatusVal = 'COMPLETED';
    } else if (newCoveredPct > 0) {
      newStatusVal = 'ONGOING';
    }

    const updatedProgression = {
      ...progression,
      topics: updatedTopics,
      percent_covered: newCoveredPct,
      percent_completed: newCompletedPct,
      status: newStatusVal,
    };

    onProgressionUpdated(updatedProgression);
  }

  async function handleApprove() {
    if (!instructorName || !instructorName.trim()) {
      setErrorMsg('Please enter the Instructor Name before approving.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await approveTeacherReview({
        progression,
        instructorName: instructorName.trim(),
        comments: comments.trim() || null,
        commitToExcel,
      });

      setApprovalResult(res);
      if (res.approved_progression) {
        onProgressionUpdated(res.approved_progression);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to submit instructor approval.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section
      className="academic-card"
      aria-label="Teacher Review and Override Panel"
      style={{
        marginTop: '1.75rem',
        border: '2px solid #3B82F6',
        backgroundColor: '#F8FAFC',
        boxShadow: 'var(--shadow-md)',
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1rem',
        borderBottom: '1px solid #E2E8F0',
        paddingBottom: '0.75rem',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.25rem' }}>👩‍🏫</span>
            <h2 className="card-title" style={{ fontSize: '1.1rem', margin: 0, color: '#1E3A8A' }}>
              Instructor Review & Verification (Day 6)
            </h2>
          </div>
          <p className="card-subtitle" style={{ margin: '0.25rem 0 0 0', color: '#475569' }}>
            Verify AI-extracted lecture findings, resolve low-confidence topics, and approve the official record.
          </p>
        </div>

        {/* Approval Badge */}
        <div>
          {approvalResult ? (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              backgroundColor: '#ECFDF5',
              border: '1px solid #10B981',
              color: '#065F46',
              padding: '0.35rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.85rem',
              fontWeight: '700',
            }}>
              ✓ APPROVED by {approvalResult.instructor_name}
            </span>
          ) : (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              backgroundColor: '#FEF3C7',
              border: '1px solid #F59E0B',
              color: '#92400E',
              padding: '0.35rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.85rem',
              fontWeight: '600',
            }}>
              ● Awaiting Instructor Verification
            </span>
          )}
        </div>
      </div>

      {/* Success Banner */}
      {approvalResult && (
        <div style={{
          backgroundColor: '#ECFDF5',
          border: '1px solid #A7F3D0',
          borderRadius: 'var(--radius-sm)',
          padding: '0.85rem 1rem',
          marginBottom: '1.25rem',
          color: '#065F46',
          fontSize: '0.9rem',
        }}>
          <div style={{ fontWeight: '700', marginBottom: '0.25rem' }}>
            ✓ {approvalResult.message}
          </div>
          <div style={{ fontSize: '0.825rem', color: '#047857' }}>
            Timestamp: {approvalResult.approval_timestamp} • Excel Status:{' '}
            {approvalResult.excel_updated ? 'Directly committed to course_progression.xlsx' : 'Not committed'}
          </div>
        </div>
      )}

      {/* Error Alert */}
      {errorMsg && (
        <div style={{
          backgroundColor: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          color: 'var(--danger)',
          fontSize: '0.875rem',
        }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Step 1: Uncertain Topics for Review */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{
          fontSize: '0.95rem',
          fontWeight: '700',
          color: '#1E293B',
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}>
          <span>🔍</span> Topic Verification & Manual Overrides
          {uncertainTopics.length > 0 && (
            <span style={{
              fontSize: '0.75rem',
              fontWeight: '600',
              backgroundColor: '#FEF2F2',
              color: '#B91C1C',
              padding: '0.1rem 0.5rem',
              borderRadius: '4px',
              border: '1px solid #F87171',
            }}>
              {uncertainTopics.length} needs inspection
            </span>
          )}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {allTopics.map((topic, idx) => {
            const isUncertain = topic.status === 'uncertain';
            const isCovered = topic.status === 'covered';
            const isNotCovered = topic.status === 'not_covered';

            return (
              <div
                key={`${topic.name}-${idx}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: isUncertain ? '#FFFBEB' : '#FFFFFF',
                  border: isUncertain ? '1px solid #FCD34D' : '1px solid #E2E8F0',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', maxWidth: '65%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: '600', fontSize: '0.9rem', color: '#1E293B' }}>
                      {topic.name}
                    </span>
                    {topic.confidence !== undefined && topic.confidence !== null && (
                      <span style={{
                        fontSize: '0.75rem',
                        color: isUncertain ? '#B45309' : '#059669',
                        fontWeight: '600',
                      }}>
                        ({Math.round(topic.confidence * 100)}% AI confidence)
                      </span>
                    )}
                  </div>
                  {topic.evidence && (
                    <div style={{
                      fontSize: '0.8rem',
                      color: '#475569',
                      fontStyle: 'italic',
                      lineHeight: 1.3,
                    }}>
                      "{topic.evidence}"
                    </div>
                  )}
                </div>

                {/* Override Buttons */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <button
                    onClick={() => updateTopicStatus(topic.name, 'covered')}
                    style={{
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      padding: '0.35rem 0.7rem',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: isCovered ? '#047857' : '#FFFFFF',
                      color: isCovered ? '#FFFFFF' : '#047857',
                      border: '1px solid #047857',
                      cursor: 'pointer',
                    }}
                  >
                    ✓ Covered
                  </button>

                  <button
                    onClick={() => updateTopicStatus(topic.name, 'not_covered')}
                    style={{
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      padding: '0.35rem 0.7rem',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: isNotCovered ? '#DC2626' : '#FFFFFF',
                      color: isNotCovered ? '#FFFFFF' : '#DC2626',
                      border: '1px solid #DC2626',
                      cursor: 'pointer',
                    }}
                  >
                    ✗ Not Covered
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step 2: Instructor Credentials & Approval Submission */}
      <div style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #CBD5E1',
        borderRadius: 'var(--radius-sm)',
        padding: '1rem',
      }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#1E293B', marginBottom: '0.75rem' }}>
          ✍️ Instructor Sign-Off
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: '#475569', marginBottom: '0.3rem' }}>
              Instructor / Reviewer Name:
            </label>
            <input
              type="text"
              value={instructorName}
              onChange={(e) => setInstructorName(e.target.value)}
              placeholder="e.g. Prof. Pawan Sharma"
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                fontSize: '0.875rem',
                border: '1px solid #CBD5E1',
                borderRadius: 'var(--radius-sm)',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: '#475569', marginBottom: '0.3rem' }}>
              Review Comments / Pedagogical Notes:
            </label>
            <input
              type="text"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="e.g. Verified topics; practice set assigned in lab."
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                fontSize: '0.875rem',
                border: '1px solid #CBD5E1',
                borderRadius: 'var(--radius-sm)',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.85rem', color: '#334155', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={commitToExcel}
              onChange={(e) => setCommitToExcel(e.target.checked)}
            />
            <span>Auto-commit approved progression directly to <code>course_progression.xlsx</code></span>
          </label>

          <button
            onClick={handleApprove}
            disabled={submitting}
            style={{
              backgroundColor: '#1E40AF',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.9rem',
              padding: '0.65rem 1.5rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: submitting ? 'not-allowed' : 'pointer',
              boxShadow: 'var(--shadow-sm)',
              opacity: submitting ? 0.7 : 1,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span>✍️</span>
            {submitting ? 'Submitting Approval...' : 'Approve & Finalize Progression'}
          </button>
        </div>
      </div>
    </section>
  );
}
