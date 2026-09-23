from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from backend.schemas.progress import (
    CalculateProgressRequest,
    CalculateProgressResponse,
)
from backend.services.progress_engine import progress_engine
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
