from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from backend.models.curriculum import Curriculum
from backend.models.analysis import LectureAnalysisResult


class SupportingMaterialInput(BaseModel):
    """Input structure for supporting academic materials provided to the analysis layer."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(
        ...,
        description="Filename or title of the supporting material (e.g., 'lecture_slides.pptx')",
        min_length=1
    )
    type: Optional[str] = Field(
        default=None,
        description="Format type: 'pdf', 'pptx', 'ppt', 'docx', 'txt', 'markdown', etc."
    )
    content: str = Field(
        default="",
        description="Extracted or raw text representation of the material"
    )
    source_info: Optional[str] = Field(
        default=None,
        description="Optional metadata such as page/slide count or source reference"
    )


class AnalyzeLectureRequest(BaseModel):
    """
    Request payload for lecture analysis.
    Accepts the lecture transcript, optional curriculum (defaults to active curriculum),
    and an optional list of supporting materials.
    """
    model_config = ConfigDict(extra="ignore")

    transcript: str = Field(
        ...,
        description="Raw lecture transcript text from Day 2 STT or uploaded text",
        min_length=1
    )
    curriculum: Optional[Union[Curriculum, List[Dict[str, Any]]]] = Field(
        default=None,
        description="Optional curriculum specification. If omitted, the currently active curriculum is used."
    )
    materials: Optional[List[SupportingMaterialInput]] = Field(
        default_factory=list,
        description="Optional list of supporting materials (PDFs, PPTs, notes, etc.)"
    )
    provider: Optional[str] = Field(
        default=None,
        description="Override AI provider: 'gemini' or 'mock'"
    )
    confidence_threshold: Optional[float] = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Configurable confidence threshold for evidence confirmation"
    )


class AnalyzeLectureResponse(BaseModel):
    """Standardized API response for the /analyze endpoint."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(
        default=True,
        description="Whether the analysis request executed successfully"
    )
    analysis: LectureAnalysisResult = Field(
        ...,
        description="Structured, evidence-grounded lecture analysis"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings encountered during analysis or material processing"
    )
