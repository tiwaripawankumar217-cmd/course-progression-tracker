from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from backend.models.curriculum import LecturePlan, Curriculum


class CurriculumSummary(BaseModel):
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    total_lectures: int
    total_topics: int
    total_classwork: int
    total_homework: int


class CurriculumResponse(BaseModel):
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    lectures: List[LecturePlan]
    summary: CurriculumSummary


class CurriculumLoadResponse(BaseModel):
    status: str
    message: str
    summary: CurriculumSummary


class ErrorResponse(BaseModel):
    error: str
    detail: Any
