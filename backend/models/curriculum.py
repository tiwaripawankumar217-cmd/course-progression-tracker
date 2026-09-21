from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class LecturePlan(BaseModel):
    """
    Represents a single lecture's planned curriculum.
    Course-agnostic: strictly adheres to week, day, lecture name, content topics,
    classwork, and homework activities.
    """
    week: int = Field(..., description="Week number (must be >= 1)", ge=1)
    day: int = Field(..., description="Day number (must be >= 1)", ge=1)
    lecture: str = Field(..., min_length=1, description="Unique lecture code or name, e.g. LEC-1")
    content: List[str] = Field(..., min_length=1, description="List of planned topics/subtopics")
    classwork: List[str] = Field(default_factory=list, description="Planned classwork activities")
    homework: List[str] = Field(default_factory=list, description="Assigned homework tasks")

    @field_validator("lecture")
    @classmethod
    def validate_lecture_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Lecture name/identifier cannot be blank or whitespace only")
        return trimmed

    @field_validator("content")
    @classmethod
    def validate_content_items(cls, v: List[str]) -> List[str]:
        cleaned = [item.strip() for item in v if item and item.strip()]
        if not cleaned:
            raise ValueError("Lecture must contain at least one valid non-empty content/topic item")
        return cleaned

    @field_validator("classwork", "homework")
    @classmethod
    def clean_string_list(cls, v: List[str]) -> List[str]:
        return [item.strip() for item in v if item and item.strip()]


class Curriculum(BaseModel):
    """
    Container representing the entire planned course curriculum.
    Agnostic to specific subject domains.
    """
    course_id: Optional[str] = Field(default="COURSE-001", description="Optional course identifier")
    course_name: Optional[str] = Field(default="Course Curriculum", description="Course or subject title")
    lectures: List[LecturePlan] = Field(..., min_length=1, description="List of scheduled lectures")

    @model_validator(mode="after")
    def check_duplicate_lectures(self) -> "Curriculum":
        seen = set()
        duplicates = []
        for lec in self.lectures:
            lec_key = lec.lecture.lower()
            if lec_key in seen:
                duplicates.append(lec.lecture)
            else:
                seen.add(lec_key)
        if duplicates:
            raise ValueError(f"Duplicate lecture identifiers found in curriculum: {', '.join(duplicates)}")
        return self
