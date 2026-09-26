import json
from pathlib import Path
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Response, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import ValidationError

from backend.schemas.progress import (
    CalculateProgressRequest,
    CalculateProgressResponse,
    ExportProgressionRequest,
    TeacherReviewApprovalRequest,
    TeacherReviewApprovalResponse,
)
from backend.services.progress_engine import progress_engine
from backend.services.excel_service import excel_service
from backend.models.curriculum import Curriculum
from backend.models.analysis import (
    LectureAnalysisResult,
    TopicTaught,
    ClassworkPerformed,
    HomeworkAssigned,
    MatchedLecture,
)
from backend.models.progress import ProgressThresholdConfig

router = APIRouter(prefix="/progress", tags=["Progress Engine"])


@router.post(
    "/calculate",
    response_model=CalculateProgressResponse,
    summary="Calculate deterministic curriculum progression",
    description=(
        "Reconciles Day 3 AI lecture analysis with planned curriculum to calculate "
        "% Covered, % Completed, and lecture status deterministically."
    ),
)
async def calculate_progress_endpoint(request: CalculateProgressRequest) -> CalculateProgressResponse:
    """Calculates progression metrics deterministically using Python logic."""
    try:
        progression = progress_engine.calculate_progress(
            analysis=request.analysis,
            curriculum=request.curriculum,
            lecture_code=request.lecture_code,
            date_taught=request.date_taught,
            config=request.config,
        )
        return CalculateProgressResponse(
            success=True,
            progression=progression,
            message="Progression calculated successfully",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating progress: {str(exc)}",
        )


@router.get(
    "/demo",
    summary="Get pre-configured Day 4 demonstration scenarios",
    description="Provides clean, pre-built scenarios for UI visualization and instant review.",
)
async def get_demo_scenarios() -> Dict[str, Any]:
    """Returns safe demonstration scenarios covering standard, partial, spilled-over, and uncertain flows."""
    demo_curriculum = {
        "course_id": "CS-101",
        "course_name": "Data Structures & Algorithms",
        "lectures": [
            {
                "week": 1,
                "day": 1,
                "lecture": "LEC-1",
                "content": ["Arrays", "Array Traversal", "Time Complexity"],
                "classwork": ["Find Maximum Element in Array"],
                "homework": ["Solve 5 Array Practice Problems"],
            },
            {
                "week": 1,
                "day": 2,
                "lecture": "LEC-2",
                "content": ["Dynamic Arrays", "Amortized Analysis", "Two Pointers Technique"],
                "classwork": ["Implement Custom Vector"],
                "homework": ["Two Sum Problem"],
            },
        ],
    }

    # Scenario 1: Standard Complete Delivery (100% Covered)
    s1_analysis = {
        "analysis_status": "SUCCESS",
        "matched_lecture": {"lecture_name": "LEC-1", "confidence": 0.98},
        "topics_taught": [
            {
                "curriculum_topic": "Arrays",
                "evidence": "Instructor opened by defining contiguous memory allocation and zero-indexed arrays.",
                "confidence": 0.96,
            },
            {
                "curriculum_topic": "Array Traversal",
                "evidence": "Demonstrated linear scan using for-loop with index pointer.",
                "confidence": 0.94,
            },
            {
                "curriculum_topic": "Time Complexity",
                "evidence": "Walked through Big-O notation explaining O(1) random access vs O(N) linear iteration.",
                "confidence": 0.92,
            },
        ],
        "classwork": [
            {
                "description": "Find Maximum Element in Array",
                "evidence": "Students coded linear scan algorithm to track current max value.",
                "confidence": 0.95,
            }
        ],
        "homework": [
            {
                "description": "Solve 5 Array Practice Problems",
                "evidence": "Assigned problems 1 through 5 on course portal due Friday.",
                "confidence": 0.91,
            }
        ],
        "analysis_warnings": [],
        "unmatched_content": [],
    }

    # Scenario 2: Partial Delivery (66.7% Covered, Ongoing)
    s2_analysis = {
        "analysis_status": "SUCCESS",
        "matched_lecture": {"lecture_name": "LEC-1", "confidence": 0.95},
        "topics_taught": [
            {
                "curriculum_topic": "Arrays",
                "evidence": "Explained memory layouts and static array definitions.",
                "confidence": 0.95,
            },
            {
                "curriculum_topic": "Array Traversal",
                "evidence": "Coded forward and backward loops across integer array.",
                "confidence": 0.93,
            },
        ],
        "topics_not_evidenced": ["Time Complexity"],
        "classwork": [
            {
                "description": "Find Maximum Element in Array",
                "evidence": "Students worked on finding maximum value in an array.",
                "confidence": 0.92,
            }
        ],
        "homework": [],
        "analysis_warnings": ["Time Complexity was not evidenced in lecture transcript."],
        "unmatched_content": [],
    }

    # Scenario 3: Spilled Over (Partial delivery finalized with spillover enabled)
    s3_analysis = dict(s2_analysis)

    # Scenario 4: Uncertain / Low-Confidence Review
    s4_analysis = {
        "analysis_status": "SUCCESS",
        "matched_lecture": {"lecture_name": "LEC-1", "confidence": 0.91},
        "topics_taught": [
            {
                "curriculum_topic": "Arrays",
                "evidence": "Detailed explanation of array memory structures and indexing.",
                "confidence": 0.95,
            },
            {
                "curriculum_topic": "Array Traversal",
                "evidence": "Mentioned traversal briefly in passing during discussion of pointer arithmetic.",
                "confidence": 0.42,
            },
        ],
        "topics_not_evidenced": ["Time Complexity"],
        "classwork": [],
        "homework": [
            {
                "description": "Solve 5 Array Practice Problems",
                "evidence": "Assigned reading and exercises on array fundamentals.",
                "confidence": 0.88,
            }
        ],
        "analysis_warnings": [],
        "unmatched_content": [],
    }

    return {
        "curriculum": demo_curriculum,
        "scenarios": [
            {
                "id": "scenario-1",
                "title": "Scenario 1: Complete Delivery (100% Covered)",
                "description": "All 3 planned topics taught with high confidence. Result: COMPLETED (100%).",
                "lecture_code": "LEC-1",
                "analysis": s1_analysis,
                "config": {"completed_threshold": 100.0, "spillover_enabled": True, "is_finalized": False},
            },
            {
                "id": "scenario-2",
                "title": "Scenario 2: Partial Delivery (66.7% Ongoing)",
                "description": "2 of 3 topics covered. Time Complexity remaining. Result: ONGOING (66.7%).",
                "lecture_code": "LEC-1",
                "analysis": s2_analysis,
                "config": {"completed_threshold": 100.0, "spillover_enabled": True, "is_finalized": False},
            },
            {
                "id": "scenario-3",
                "title": "Scenario 3: Finalized Incomplete (Spilled Over)",
                "description": "Session ended with incomplete curriculum. Result: SPILLED OVER (66.7%).",
                "lecture_code": "LEC-1",
                "analysis": s3_analysis,
                "config": {"completed_threshold": 100.0, "spillover_enabled": True, "is_finalized": True},
            },
            {
                "id": "scenario-4",
                "title": "Scenario 4: Low-Confidence / Uncertain Topic",
                "description": "Array Traversal has 0.42 confidence. Result: Marked UNCERTAIN, requires teacher review.",
                "lecture_code": "LEC-1",
                "analysis": s4_analysis,
                "config": {"completed_threshold": 100.0, "confidence_threshold": 0.65, "is_finalized": False},
            },
        ],
    }


@router.post(
    "/export",
    summary="Export Day 4 progression to Course Progression Excel workbook",
    description="Generates an official .xlsx spreadsheet containing the validated progression record.",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Returns generated Course Progression Excel file.",
        }
    },
)
async def export_progress_excel(request: Request) -> Response:
    """Exports validated Day 4 progress result into a formatted .xlsx workbook."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid JSON payload for Excel export.",
        )

    if not body or not isinstance(body, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing progression data for Excel export.",
        )

    # Extract progression and optional custom filename
    prog_payload = body.get("progression", body)
    if not isinstance(prog_payload, dict) or not prog_payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Progression payload must be a non-empty object.",
        )

    # Validate essential fields
    has_metrics = any(
        k in prog_payload
        for k in ("percent_completed", "percent_covered", "status", "lecture", "date_taught")
    )
    if not has_metrics:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Progression payload missing required progression fields.",
        )

    try:
        xlsx_bytes = excel_service.generate_progression_workbook(prog_payload)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel workbook: {str(exc)}",
        )

    # Determine filename
    custom_name = body.get("file_name") if isinstance(body, dict) else None
    if custom_name and str(custom_name).strip():
        filename = str(custom_name).strip()
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
    else:
        date_str = str(prog_payload.get("date_taught", "")).strip() or date.today().isoformat()
        filename = f"course_progression_{date_str}.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post(
    "/export/update",
    summary="Update existing Course Progression Excel workbook with new lecture",
    description="Updates existing .xlsx workbook preserving previous records, with duplicate protection.",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Returns updated Course Progression Excel file.",
        }
    },
)
async def update_progress_excel(
    file: UploadFile = File(..., description="Existing .xlsx progression workbook"),
    progression_json: str = Form(..., description="JSON string of validated LectureProgression"),
) -> Response:
    """Updates an existing Excel workbook with new validated lecture progression record."""
    try:
        prog_data = json.loads(progression_json)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid progression JSON string: {str(exc)}",
        )

    if not isinstance(prog_data, dict) or not prog_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Progression data must be a non-empty JSON object.",
        )

    prog_payload = prog_data.get("progression", prog_data)

    try:
        file_bytes = await file.read()
        updated_bytes = excel_service.update_progression_workbook(file_bytes, prog_payload)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Excel workbook: {str(exc)}",
        )

    filename = file.filename or f"course_progression_{date.today().isoformat()}.xlsx"
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    return Response(
        content=updated_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    "/download",
    summary="Download the current course_progression.xlsx file",
    description="Downloads the saved course progression spreadsheet.",
    response_class=FileResponse,
)
async def download_progression_file():
    target_path = Path("course_progression.xlsx")
    if not target_path.exists():
        target_path = Path("backend/output/course_progression.xlsx")
    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No course_progression.xlsx file found. Please export a progression first.",
        )
    return FileResponse(
        path=str(target_path),
        filename="course_progression.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="course_progression.xlsx"'},
    )


@router.post(
    "/review/approve",
    response_model=TeacherReviewApprovalResponse,
    summary="Approve and finalize reviewed lecture progression",
    description="Allows instructor to officially verify and approve progression, syncing directly to Excel.",
)
async def approve_teacher_review(request: TeacherReviewApprovalRequest) -> TeacherReviewApprovalResponse:
    """Approves reviewed lecture progression and optionally commits directly into course_progression.xlsx."""
    if not request.instructor_name or not request.instructor_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Instructor name is required for formal review approval.",
        )

    progression = request.progression
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add approval note to warnings
    approval_stamp = f"Approved by Instructor: {request.instructor_name.strip()} on {timestamp}."
    if approval_stamp not in progression.warnings:
        progression.warnings.append(approval_stamp)

    if request.comments and request.comments.strip():
        comment_stamp = f"Instructor Note: {request.comments.strip()}"
        if comment_stamp not in progression.warnings:
            progression.warnings.append(comment_stamp)

    excel_updated = False
    if request.commit_to_excel:
        target_path = Path("course_progression.xlsx")
        backup_path = Path("backend/output/course_progression.xlsx")

        existing_bytes = None
        if target_path.exists():
            try:
                with open(target_path, "rb") as f:
                    existing_bytes = f.read()
            except Exception:
                existing_bytes = None

        try:
            if existing_bytes:
                updated_bytes = excel_service.update_progression_workbook(existing_bytes, progression)
            else:
                updated_bytes = excel_service.generate_progression_workbook(progression)

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(updated_bytes)
            try:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                with open(backup_path, "wb") as f:
                    f.write(updated_bytes)
            except Exception:
                pass
            excel_updated = True
        except Exception as exc:
            progression.warnings.append(f"Warning: Could not automatically commit to Excel: {str(exc)}")

    return TeacherReviewApprovalResponse(
        success=True,
        message=f"Lecture progression for {progression.lecture} approved successfully by {request.instructor_name.strip()}.",
        approved_progression=progression,
        instructor_name=request.instructor_name.strip(),
        approval_timestamp=timestamp,
        excel_updated=excel_updated,
    )
