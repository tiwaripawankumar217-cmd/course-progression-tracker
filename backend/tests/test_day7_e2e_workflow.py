import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import openpyxl

from backend.main import app
from backend.services.excel_service import PRIMARY_SHEET_NAME, REQUIRED_COLUMNS


@pytest.fixture
def client():
    return TestClient(app)


def test_complete_day7_end_to_end_faculty_workflow(client, tmp_path, monkeypatch):
    """
    Day 7 Complete End-to-End Pipeline Verification:
    Curriculum -> Audio -> Transcript -> AI Analysis -> Progress Mapping -> Teacher Review -> Excel Export
    """
    # Isolate filesystem for test
    monkeypatch.chdir(tmp_path)

    # -------------------------------------------------------------
    # Step 1: Curriculum Ingestion & Verification
    # -------------------------------------------------------------
    curriculum_res = client.get("/curriculum")
    assert curriculum_res.status_code == 200
    curriculum_data = curriculum_res.json()
    assert curriculum_data["course_id"] == "GEN-101"
    assert len(curriculum_data["lectures"]) >= 1

    # -------------------------------------------------------------
    # Step 2: Audio Ingestion & Transcription (Speech-to-Text)
    # -------------------------------------------------------------
    sample_audio_res = client.get("/lecture/sample-audio")
    assert sample_audio_res.status_code == 200
    audio_bytes = sample_audio_res.content
    assert len(audio_bytes) > 0

    # Upload audio to Speech-to-Text endpoint
    audio_upload_res = client.post(
        "/lecture/audio?provider=mock",
        files={"file": ("lecture_recording.wav", audio_bytes, "audio/wav")},
    )
    assert audio_upload_res.status_code == 200
    transcript_data = audio_upload_res.json()
    assert "transcript" in transcript_data
    assert transcript_data["duration"] > 0
    transcript_text = (
        "Welcome class. Today we covered Core Principles and Foundations of curriculum structure. "
        "We also reviewed Conceptual Framework and Terminology. "
        "For classwork, students completed Activity 1: Guided Concept Review. "
        "Homework assigned is Homework 1: Practice Exercises due Friday."
    )

    # -------------------------------------------------------------
    # Step 3 & 4: Multi-Material Context + AI Lecture Analysis
    # -------------------------------------------------------------
    slide_text = "[Slide 1]\nCore Principles and Foundations\n[Slide 2]\nConceptual Framework and Terminology"
    analysis_res = client.post(
        "/analyze/upload?provider=mock&confidence_threshold=0.65",
        data={"transcript": transcript_text},
        files={"files": ("lecture_slides.txt", io.BytesIO(slide_text.encode("utf-8")), "text/plain")},
    )
    assert analysis_res.status_code == 200
    analysis_payload = analysis_res.json()
    assert analysis_payload["success"] is True
    analysis_result = analysis_payload["analysis"]
    assert analysis_result["matched_lecture"]["lecture_name"] == "LEC-1"
    assert len(analysis_result["topics_taught"]) >= 1

    # -------------------------------------------------------------
    # Step 5: Deterministic Curriculum Mapping & Progress Engine
    # -------------------------------------------------------------
    progress_res = client.post(
        "/progress/calculate",
        json={
            "analysis": analysis_result,
            "lecture_code": "LEC-1",
            "date_taught": "2026-09-26",
            "config": {
                "completed_threshold": 100.0,
                "confidence_threshold": 0.65,
                "spillover_enabled": True,
                "is_finalized": False,
            },
        },
    )
    assert progress_res.status_code == 200
    calc_data = progress_res.json()
    assert calc_data["success"] is True
    progression = calc_data["progression"]
    assert progression["lecture"] == "LEC-1"
    assert progression["percent_covered"] > 0
    assert progression["status"] in ("ONGOING", "COMPLETED")

    # -------------------------------------------------------------
    # Step 6: Teacher Review, Pedagogical Overrides & Approval
    # -------------------------------------------------------------
    # Teacher reviews and marks all 3 planned topics as confirmed covered
    for topic in progression["topics"]:
        topic["status"] = "covered"
        topic["confidence"] = 0.95
    progression["percent_completed"] = 100.0
    progression["percent_covered"] = 100.0
    progression["status"] = "COMPLETED"

    approval_res = client.post(
        "/progress/review/approve",
        json={
            "progression": progression,
            "instructor_name": "Prof. Pawan Sharma",
            "comments": "Audited in class; student comprehension verified.",
            "commit_to_excel": True,
        },
    )
    assert approval_res.status_code == 200
    approval_data = approval_res.json()
    assert approval_data["success"] is True
    assert approval_data["excel_updated"] is True
    assert approval_data["instructor_name"] == "Prof. Pawan Sharma"

    # -------------------------------------------------------------
    # Step 7: Official Excel Progression Export & File Verification
    # -------------------------------------------------------------
    download_res = client.get("/progress/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    wb = openpyxl.load_workbook(io.BytesIO(download_res.content))
    assert PRIMARY_SHEET_NAME in wb.sheetnames
    ws = wb[PRIMARY_SHEET_NAME]

    # Verify standard columns
    headers = [ws.cell(row=1, column=c).value for c in range(1, 7)]
    assert headers == REQUIRED_COLUMNS

    # Verify data row
    assert ws.cell(row=2, column=1).value == "2026-09-26"
    assert ws.cell(row=2, column=2).value == "Completed"
    assert float(ws.cell(row=2, column=3).value) == 100.0
    assert float(ws.cell(row=2, column=4).value) == 100.0
    assert "Activity 1" in str(ws.cell(row=2, column=5).value)
    assert "Homework 1" in str(ws.cell(row=2, column=6).value)
