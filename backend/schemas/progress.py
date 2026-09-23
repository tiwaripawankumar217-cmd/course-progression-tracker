from typing import Optional
from pydantic import BaseModel, Field
from backend.models.curriculum import Curriculum
from backend.models.analysis import LectureAnalysisResult
from backend.models.progress import LectureProgression, ProgressThresholdConfig


class CalculateProgressRequest(BaseModel):
    """Request schema for calculating course lecture progression."""
    analysis: LectureAnalysisResult = Field(
        ...,
        description="Structured AI lecture analysis output from Day 3"
    )
    curriculum: Optional[Curriculum] = Field(
        default=None,
        description="Optional curriculum override. If omitted, the active system curriculum is used."
    )
    lecture_code: Optional[str] = Field(
        default=None,
        description="Optional lecture code override (e.g. 'LEC-1'). Defaults to analysis matched_lecture."
    )
    date_taught: Optional[str] = Field(
        default=None,
        description="Date lecture was taught (YYYY-MM-DD). Defaults to current date if omitted."
    )
    config: Optional[ProgressThresholdConfig] = Field(
        default_factory=ProgressThresholdConfig,
        description="Configurable threshold parameters for progress and status logic"
    )


class CalculateProgressResponse(BaseModel):
    """Response schema containing deterministic progression evaluation."""
    success: bool = Field(default=True, description="Indicates if progression calculation succeeded")
    progression: LectureProgression = Field(..., description="The calculated progression record")
    message: Optional[str] = Field(default=None, description="Optional informational message")
