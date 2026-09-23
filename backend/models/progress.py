from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TopicStatus(str, Enum):
    """Status classification for a curriculum topic."""
    COVERED = "covered"
    NOT_COVERED = "not_covered"
    UNCERTAIN = "uncertain"


class TopicProgress(BaseModel):
    """
    Status of an individual curriculum topic within a lecture.
    Maintains strict reference to the authoritative curriculum.
    """
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Curriculum topic name", min_length=1)
    status: TopicStatus = Field(
        default=TopicStatus.NOT_COVERED,
        description="Coverage status: 'covered', 'not_covered', or 'uncertain'"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score from AI extraction (0.0 - 1.0), or None if not covered"
    )
    evidence: Optional[str] = Field(
        default=None,
        description="Verifiable transcript excerpt proving coverage, or None"
    )


class ClassworkItem(BaseModel):
    """Classwork or in-class exercise evidenced from the lecture."""
    model_config = ConfigDict(extra="ignore")

    description: str = Field(..., description="Classwork activity description", min_length=1)
    evidence: Optional[str] = Field(default=None, description="Transcript quote")
    confidence: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)


class HomeworkItem(BaseModel):
    """Homework or assignment explicitly evidenced as given to students."""
    model_config = ConfigDict(extra="ignore")

    description: str = Field(..., description="Homework task description", min_length=1)
    evidence: Optional[str] = Field(default=None, description="Transcript quote")
    confidence: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)


class MaterialItem(BaseModel):
    """Supporting academic document processed alongside the lecture."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="File name (e.g. slides.pptx)")
    type: str = Field(default="document", description="Material type (pdf, pptx, docx, txt)")
    status: str = Field(default="processed", description="Status: 'processed', 'warning', 'failed'")
    error: Optional[str] = Field(default=None, description="Warning or error details if processing failed")


class ProgressThresholdConfig(BaseModel):
    """
    Configurable thresholds for deterministic progress and status calculation.
    Never hardcoded into AI prompts.
    """
    model_config = ConfigDict(extra="ignore")

    completed_threshold: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Minimum % covered required to mark lecture COMPLETED (default 100%)"
    )
    ongoing_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Minimum % covered to mark lecture ONGOING (default 0%)"
    )
    confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Confidence score below which a topic is classified as 'uncertain' (needs review)"
    )
    spillover_enabled: bool = Field(
        default=True,
        description="Whether incomplete lectures can trigger SPILLED OVER status"
    )
    is_finalized: bool = Field(
        default=False,
        description="Set to true if the lecture session has concluded (enables SPILLED OVER if incomplete)"
    )


class LectureProgression(BaseModel):
    """
    Standard Day 4 progression object.
    Deterministic, course-agnostic, and formatted for Excel progression export in Day 5.
    """
    model_config = ConfigDict(extra="ignore")

    lecture: str = Field(..., description="Curriculum lecture identifier, e.g. 'LEC-1'")
    date_taught: str = Field(..., description="Date lecture was taught (YYYY-MM-DD)")
    status: str = Field(
        ...,
        description="Deterministic status: 'COMPLETED', 'ONGOING', 'SPILLED OVER', or 'NOT_STARTED'"
    )
    percent_completed: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of confirmed, fully evidenced topics completed"
    )
    percent_covered: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of planned topics covered (including uncertain topics awaiting review)"
    )
    topics: List[TopicProgress] = Field(
        default_factory=list,
        description="Curriculum topics mapped to status and transcript evidence"
    )
    classwork: List[ClassworkItem] = Field(
        default_factory=list,
        description="Verified in-class activities performed"
    )
    homework: List[HomeworkItem] = Field(
        default_factory=list,
        description="Verified homework assigned"
    )
    supporting_materials: List[MaterialItem] = Field(
        default_factory=list,
        description="Supporting materials referenced"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Pedagogical, confidence, or processing warnings"
    )
