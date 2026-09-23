import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import ProgressSummary from '../components/ProgressSummary';
import TopicList from '../components/TopicList';
import ClassworkSection from '../components/ClassworkSection';
import HomeworkSection from '../components/HomeworkSection';
import MaterialList from '../components/MaterialList';
import WarningMessage from '../components/WarningMessage';
import LoadingState from '../components/LoadingState';
import { calculateProgress, getDemoScenarios } from '../services/api';

export default function Dashboard() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('scenario-2');
  const [curriculum, setCurriculum] = useState(null);
  const [progression, setProgression] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load demonstration scenarios on mount
  useEffect(() => {
    async function loadInitialData() {
      setLoading(true);
      setError(null);
      try {
        const demoData = await getDemoScenarios();
        setScenarios(demoData.scenarios || []);
        setCurriculum(demoData.curriculum || null);

        // Select Scenario 2 (Partial 66.7% Ongoing) by default as typical demonstration
        const defaultScenario = (demoData.scenarios || []).find(s => s.id === 'scenario-2') || demoData.scenarios[0];
        if (defaultScenario) {
          setSelectedScenarioId(defaultScenario.id);
          await runCalculation(defaultScenario, demoData.curriculum);
        }
      } catch (err) {
        setError(`Failed to load lecture scenarios: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  async function runCalculation(scenario, curr = curriculum) {
    if (!scenario) return;
    setLoading(true);
    setError(null);
    try {
      const response = await calculateProgress({
        analysis: scenario.analysis,
        curriculum: curr,
        lecture_code: scenario.lecture_code,
        date_taught: '2026-09-22',
        config: scenario.config,
      });

      if (response && response.success) {
        setProgression(response.progression);
      } else {
        throw new Error(response.message || 'Calculation was not successful.');
      }
    } catch (err) {
      setError(`Error calculating progress: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleScenarioSelect(e) {
    const scId = e.target.value;
    setSelectedScenarioId(scId);
    const target = scenarios.find(s => s.id === scId);
    if (target) {
      runCalculation(target);
    }
  }

  const currentScenario = scenarios.find(s => s.id === selectedScenarioId);

  return (
    <div className="app-container">
      <Header />

      {/* Input / Scenario Selection Card */}
      <section className="academic-card" aria-label="Lecture Selection & Analysis Input">
        <h2 className="card-title" style={{ fontSize: '1rem' }}>
          <span>⚙️</span> Lecture Selection & Verification Flow
        </h2>
        <p className="card-subtitle" style={{ marginBottom: '1rem' }}>
          Select a lecture scenario to verify deterministic curriculum mapping, % coverage arithmetic, and status detection.
        </p>

        {/* Step 1: Scenario Select */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label
              htmlFor="scenario-select"
              style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}
            >
              Choose Lecture Delivery Scenario:
            </label>
            <select
              id="scenario-select"
              value={selectedScenarioId}
              onChange={handleScenarioSelect}
              style={{
                width: '100%',
                padding: '0.6rem 0.85rem',
                fontSize: '0.9rem',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-card)',
                color: 'var(--text-primary)',
              }}
            >
              {scenarios.map(sc => (
                <option key={sc.id} value={sc.id}>
                  {sc.title} — {sc.description}
                </option>
              ))}
            </select>
          </div>

          {/* Steps Status Indicators */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1rem',
            padding: '0.75rem 1rem',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.825rem',
            color: 'var(--text-secondary)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ color: 'var(--success)' }}>✓</span>
              <span><strong>Step 1:</strong> Lecture Data Selected ({currentScenario?.lecture_code || 'LEC-1'})</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ color: 'var(--success)' }}>✓</span>
              <span><strong>Step 2:</strong> Transcript Ready</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ color: 'var(--success)' }}>✓</span>
              <span><strong>Step 3:</strong> Supporting Materials Linked</span>
            </div>
          </div>

          {/* Action Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '0.25rem' }}>
            <button
              onClick={() => runCalculation(currentScenario)}
              disabled={loading}
              style={{
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                fontWeight: '600',
                fontSize: '0.9rem',
                padding: '0.6rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                boxShadow: 'var(--shadow-sm)',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'Calculating...' : 'Recalculate Progress'}
            </button>
          </div>
        </div>
      </section>

      {/* Loading Indicator */}
      {loading && <LoadingState message="Analyzing lecture and calculating progression..." />}

      {/* Error State */}
      {error && !loading && (
        <div style={{
          backgroundColor: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          color: 'var(--danger)',
          fontSize: '0.9rem',
        }}>
          <strong>Error: </strong> {error}
        </div>
      )}

      {/* Main Results Display */}
      {!loading && progression && (
        <main>
          {/* Progress Overview (% Covered, % Completed, Status) */}
          <ProgressSummary progression={progression} />

          {/* Interactive Topics List */}
          <TopicList topics={progression.topics} />

          {/* Classwork and Homework in 2-column responsive layout */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1.25rem',
            marginBottom: '1.5rem',
          }}>
            <ClassworkSection classwork={progression.classwork} />
            <HomeworkSection homework={progression.homework} />
          </div>

          {/* Supporting Materials Used */}
          <MaterialList materials={progression.supporting_materials} />

          {/* System Warnings & Notes */}
          <WarningMessage warnings={progression.warnings} />
        </main>
      )}
    </div>
  );
}
