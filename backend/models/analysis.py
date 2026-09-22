from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TopicTaught(BaseModel):
    """Represents a curriculum topic verified as taught with transcript evidence."""
    model_config = ConfigDict(extra="ignore")

    curriculum_topic: str = Field(
        ...,
        description="Exact topic name from the active curriculum",
        min_length=1
    )
    evidence: str = Field(
        ...,
        description="Transcript excerpt or quote demonstrating this topic was taught",
        min_length=1
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score for this topic coverage (0.0 - 1.0)"
    )


class ClassworkPerformed(BaseModel):
    """Represents in-class activity, exercise, or problem solving performed during the lecture."""
    model_config = ConfigDict(extra="ignore")

    description: str = Field(
        ...,
        description="Description of the in-class activity performed",
        min_length=1
    )
    evidence: str = Field(
        ...,
        description="Transcript excerpt evidencing that this classwork took place",
        min_length=1
    )
    confidence: Optional[float] = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 - 1.0)"
    )


class HomeworkAssigned(BaseModel):
    """Represents homework, reading assignment, or deliverables assigned during the lecture."""
    model_config = ConfigDict(extra="ignore")

    description: str = Field(
        ...,
        description="Description of the assigned homework",
        min_length=1
    )
    evidence: str = Field(
        ...,
        description="Transcript excerpt evidencing that this homework was assigned",
        min_length=1
    )
    confidence: Optional[float] = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 - 1.0)"
    )


class MatchedLecture(BaseModel):
    """Represents the curriculum lecture code that most closely matches the lecture transcript."""
    model_config = ConfigDict(extra="ignore")

    lecture_name: str = Field(
        ...,
        description="Matched lecture code from curriculum (e.g., 'LEC-1') or 'NO_MATCH'",
        min_length=1
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score of the lecture match (0.0 - 1.0)"
    )


class LectureAnalysisResult(BaseModel):
    """
    Standardized, structured output of the Day 3 AI Lecture Analysis.
    Authoritative, course-agnostic, and grounded in transcript evidence.
    """
    model_config = ConfigDict(extra="ignore")

    analysis_status: str = Field(
        default="SUCCESS",
        description="Status of analysis: 'SUCCESS', 'NO_MATCH', 'PARTIAL_MATCH', or 'ERROR'"
    )
    matched_lecture: MatchedLecture = Field(
        ...,
        description="Curriculum lecture that best corresponds to the transcript"
    )
    topics_taught: List[TopicTaught] = Field(
        default_factory=list,
        description="Curriculum topics verified with evidence in the transcript"
    )
    topics_not_evidenced: List[str] = Field(
        default_factory=list,
        description="Topics present in curriculum/supporting materials but not evidenced as taught in transcript"
    )
    subtopics: List[str] = Field(
        default_factory=list,
        description="Specific subtopics or detailed concepts discussed during class"
    )
    classwork: List[ClassworkPerformed] = Field(
        default_factory=list,
        description="Classwork and exercises actually conducted during the lecture"
    )
    homework: List[HomeworkAssigned] = Field(
        default_factory=list,
        description="Homework, problem sets, or readings actually assigned by the instructor"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Illustrations, code walkthroughs, or practical examples given"
    )
    problems_discussed: List[str] = Field(
        default_factory=list,
        description="Specific questions, exercises, or exam problems discussed in class"
    )
    important_explanations: List[str] = Field(
        default_factory=list,
        description="Concise explanations of core concepts delivered by the instructor"
    )
    unmatched_content: List[str] = Field(
        default_factory=list,
        description="Significant lecture content taught that does not exist in the active curriculum"
    )
    analysis_warnings: List[str] = Field(
        default_factory=list,
        description="Warnings regarding missing evidence, unparsed files, or low confidence"
    )
    provider: str = Field(
        default="gemini",
        description="AI Analysis engine used (e.g., 'gemini', 'mock')"
    )
