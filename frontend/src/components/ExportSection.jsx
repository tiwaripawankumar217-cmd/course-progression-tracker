import React, { useState, useRef } from 'react';
import { exportProgressionExcel, updateProgressionExcel } from '../services/api';

export default function ExportSection({ progression }) {
  const [exporting, setExporting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  if (!progression) return null;

  async function handleDownloadNew() {
    setExporting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await exportProgressionExcel(progression);
      setSuccessMsg(`Spreadsheet '${res.filename}' generated and downloaded successfully.`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to generate Excel progression file.');
    } finally {
      setExporting(false);
    }
  }

  async function handleUpdateExisting() {
    if (!selectedFile) {
      setErrorMsg('Please select an existing .xlsx workbook to update.');
      return;
    }

    setExporting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await updateProgressionExcel(selectedFile, progression);
      setSuccessMsg(`Workbook '${res.filename}' updated with ${progression.lecture} and downloaded.`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setErrorMsg(err.message || 'Failed to update existing workbook.');
    } finally {
      setExporting(false);
    }
  }

  function handleFileChange(e) {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMsg(null);
    }
  }

  return (
    <section
      className="academic-card"
      aria-label="Excel Progression Export"
      style={{
        marginTop: '1.75rem',
        borderTop: '2px solid var(--border-color)',
        paddingTop: '1.5rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <h2 className="card-title" style={{ fontSize: '1.05rem', margin: 0 }}>
          <span>📊</span> Export Course Progression (Day 5)
        </h2>
        <span style={{
          fontSize: '0.75rem',
          padding: '0.2rem 0.6rem',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'var(--bg-subtle)',
          color: 'var(--text-secondary)',
          border: '1px solid var(--border-color)'
        }}>
          Required Schema: Date Taught • Status • % Completed • % Covered • CW • HW
        </span>
      </div>

      <p className="card-subtitle" style={{ marginBottom: '1.25rem' }}>
        Export the validated progression for <strong>{progression.lecture}</strong> ({progression.date_taught}) into an official faculty Excel spreadsheet, or update an existing course workbook.
      </p>

      {/* Success Notification */}
      {successMsg && (
        <div style={{
          backgroundColor: '#ECFDF5',
          border: '1px solid #A7F3D0',
          borderRadius: 'var(--radius-sm)',
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          color: '#065F46',
          fontSize: '0.875rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <span>✓</span>
          <span>{successMsg}</span>
        </div>
      )}

      {/* Error Notification */}
      {errorMsg && (
        <div style={{
          backgroundColor: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          color: 'var(--danger)',
          fontSize: '0.875rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <span>⚠️</span>
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Action Buttons & Update Controls */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
      }}>
        {/* Button 1: Download Direct Saved Progression */}
        <a
          href="/progress/download"
          download="course_progression.xlsx"
          style={{
            backgroundColor: '#1E40AF',
            color: '#ffffff',
            fontWeight: '600',
            fontSize: '0.9rem',
            padding: '0.65rem 1.3rem',
            borderRadius: 'var(--radius-sm)',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <span>📁</span>
          Download course_progression.xlsx
        </a>

        {/* Button 2: Export Current Selected Scenario */}
        <button
          onClick={handleDownloadNew}
          disabled={exporting}
          style={{
            backgroundColor: '#047857',
            color: '#ffffff',
            fontWeight: '600',
            fontSize: '0.9rem',
            padding: '0.65rem 1.3rem',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            cursor: exporting ? 'not-allowed' : 'pointer',
            boxShadow: 'var(--shadow-sm)',
            opacity: exporting ? 0.7 : 1,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span>📥</span>
          {exporting && !selectedFile ? 'Generating...' : `Export ${progression.lecture} to Excel`}
        </button>

        {/* Separator */}
        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>or</span>

        {/* Option 2: Update Existing Workbook */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.6rem',
          flexWrap: 'wrap',
        }}>
          <input
            type="file"
            accept=".xlsx"
            ref={fileInputRef}
            onChange={handleFileChange}
            disabled={exporting}
            style={{
              fontSize: '0.85rem',
              color: 'var(--text-secondary)',
            }}
          />

          <button
            onClick={handleUpdateExisting}
            disabled={exporting || !selectedFile}
            style={{
              backgroundColor: selectedFile ? 'var(--primary)' : 'var(--bg-subtle)',
              color: selectedFile ? '#ffffff' : 'var(--text-muted)',
              fontWeight: '600',
              fontSize: '0.85rem',
              padding: '0.65rem 1.1rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              cursor: exporting || !selectedFile ? 'not-allowed' : 'pointer',
              opacity: exporting ? 0.7 : 1,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <span>🔄</span>
            {exporting && selectedFile ? 'Updating...' : 'Update Existing Workbook'}
          </button>
        </div>
      </div>
    </section>
  );
}
