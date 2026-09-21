import json
from typing import Any, Dict, List, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, status

from backend.models.curriculum import LecturePlan
from backend.schemas.curriculum import (
    CurriculumResponse,
    CurriculumLoadResponse,
)
from backend.services.curriculum_service import curriculum_service, DEFAULT_CURRICULUM_PATH

# Fallback-safe HTTP 422 status
HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])


@router.get(
    "",
    response_model=CurriculumResponse,
    summary="Get active curriculum",
    description="Returns the currently loaded curriculum and summary statistics."
)
async def get_curriculum():
    """Retrieve the currently active loaded course curriculum."""
    try:
        curriculum = curriculum_service.get_curriculum()
        summary = curriculum_service.get_summary()
        return CurriculumResponse(
            course_id=curriculum.course_id,
            course_name=curriculum.course_name,
            lectures=curriculum.lectures,
            summary=summary,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@router.get(
    "/lectures/{lecture_id}",
    response_model=LecturePlan,
    summary="Get single lecture plan",
    description="Fetch details of a specific planned lecture by its identifier (e.g., 'LEC-1')."
)
async def get_lecture(lecture_id: str):
    """Retrieve a single lecture plan by its unique identifier."""
    try:
        lecture = curriculum_service.get_lecture(lecture_id)
        if not lecture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture with identifier '{lecture_id}' not found in the loaded curriculum."
            )
        return lecture
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/load",
    response_model=CurriculumLoadResponse,
    summary="Load curriculum from JSON body",
    description="Validate and load curriculum from a JSON object or array of lectures."
)
async def load_curriculum(payload: Union[Dict[str, Any], List[Dict[str, Any]]]):
    """Set the active curriculum by passing raw JSON payload."""
    try:
        curriculum_service.load_from_data(payload)
        summary = curriculum_service.get_summary()
        return CurriculumLoadResponse(
            status="success",
            message=f"Curriculum successfully validated and loaded with {summary.total_lectures} lectures.",
            summary=summary,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_422,
            detail=str(exc)
        )


@router.post(
    "/upload",
    response_model=CurriculumLoadResponse,
    summary="Upload curriculum JSON file",
    description="Upload a JSON file containing curriculum definitions. Validates structure and replaces active curriculum."
)
async def upload_curriculum_file(file: UploadFile = File(...)):
    """Upload and activate curriculum from an uploaded .json file."""
    if not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid JSON file with .json extension"
        )

    try:
        raw_bytes = await file.read()
        raw_str = raw_bytes.decode("utf-8")
        parsed_json = json.loads(raw_str)
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File could not be decoded as UTF-8 text.")
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON syntax in uploaded file: {exc.msg} (line {exc.lineno}, col {exc.colno})"
        )

    try:
        curriculum_service.load_from_data(parsed_json)
        summary = curriculum_service.get_summary()
        return CurriculumLoadResponse(
            status="success",
            message=f"Uploaded curriculum '{file.filename}' successfully validated and loaded.",
            summary=summary,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_422,
            detail=str(exc)
        )


@router.post(
    "/reset",
    response_model=CurriculumLoadResponse,
    summary="Reset to default curriculum",
    description="Reloads the default sample curriculum from backend/data/curriculum.json."
)
async def reset_curriculum():
    """Reset curriculum to default sample file."""
    try:
        curriculum_service.load_from_file(DEFAULT_CURRICULUM_PATH)
        summary = curriculum_service.get_summary()
        return CurriculumLoadResponse(
            status="success",
            message="Curriculum reset to default sample dataset.",
            summary=summary,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset default curriculum: {str(exc)}"
        )
