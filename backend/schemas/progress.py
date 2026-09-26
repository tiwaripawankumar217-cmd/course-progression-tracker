from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
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


class ExportProgressionRequest(BaseModel):
    """Request schema for exporting Day 4 progression into an Excel spreadsheet."""
    model_config = ConfigDict(extra="allow")

    progression: Optional[Union[LectureProgression, Dict[str, Any]]] = Field(
        default=None,
        description="Day 4 progression result or progression dictionary"
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Optional custom file name for the downloaded XLSX file"
    )


class TeacherReviewApprovalRequest(BaseModel):
    """Request schema for teacher review and approval of lecture progression."""
    model_config = ConfigDict(extra="ignore")

    progression: LectureProgression = Field(
        ...,
        description="The reviewed LectureProgression record"
    )
    instructor_name: str = Field(
        ...,
        min_length=1,
        description="Name of the instructor approving the progression"
    )
    comments: Optional[str] = Field(
        default=None,
        description="Optional teacher review notes or comments"
    )
    commit_to_excel: bool = Field(
        default=True,
        description="Whether to commit this approved progression directly into course_progression.xlsx"
    )


class TeacherReviewApprovalResponse(BaseModel):
    """Response schema returned after instructor approval."""
    success: bool = Field(default=True)
    message: str = Field(..., description="Approval status message")
    approved_progression: LectureProgression = Field(..., description="Approved progression record")
    instructor_name: str = Field(...)
    approval_timestamp: str = Field(...)
    excel_updated: bool = Field(default=False)
