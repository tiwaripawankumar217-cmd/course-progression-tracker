import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import HowToUseModal from '../components/HowToUseModal';
import LectureIngestionCard from '../components/LectureIngestionCard';
import ProgressSummary from '../components/ProgressSummary';
import TopicList from '../components/TopicList';
import ClassworkSection from '../components/ClassworkSection';
import HomeworkSection from '../components/HomeworkSection';
import MaterialList from '../components/MaterialList';
import WarningMessage from '../components/WarningMessage';
import LoadingState from '../components/LoadingState';
import ExportSection from '../components/ExportSection';
import TeacherReviewPanel from '../components/TeacherReviewPanel';
import { calculateProgress, getDemoScenarios } from '../services/api';

export default function Dashboard() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('scenario-2');
  const [curriculum, setCurriculum] = useState(null);
  const [progression, setProgression] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isGuideOpen, setIsGuideOpen] = useState(false);

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

  function handleScenarioSelect(scId) {
    setSelectedScenarioId(scId);
    const target = scenarios.find(s => s.id === scId);
    if (target) {
      runCalculation(target);
    }
  }

  async function handleAnalysisCalculated(analysis, lectureCode, dateTaught) {
    setLoading(true);
    setError(null);
    try {
      const response = await calculateProgress({
        analysis,
        curriculum,
        lecture_code: lectureCode,
        date_taught: dateTaught,
        config: { completed_threshold: 100.0, confidence_threshold: 0.65, spillover_enabled: true, is_finalized: false },
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

  return (
    <div className="app-container">
      <Header onOpenGuide={() => setIsGuideOpen(true)} />

      {/* Faculty Quick-Start Guide Modal */}
      <HowToUseModal isOpen={isGuideOpen} onClose={() => setIsGuideOpen(false)} />

      {/* Unified Ingestion & Analysis Workflow Card */}
      <LectureIngestionCard
        curriculum={curriculum}
        scenarios={scenarios}
        selectedScenarioId={selectedScenarioId}
        onSelectScenario={handleScenarioSelect}
        onAnalysisCalculated={handleAnalysisCalculated}
        loading={loading}
      />

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

          {/* Day 6 Teacher Review & Verification Workspace */}
          <TeacherReviewPanel
            progression={progression}
            onProgressionUpdated={setProgression}
          />

          {/* Day 5 Excel Progression Export */}
          <ExportSection progression={progression} />
        </main>
      )}
    </div>
  );
}
