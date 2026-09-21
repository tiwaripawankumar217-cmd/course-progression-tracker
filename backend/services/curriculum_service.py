import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError

from backend.models.curriculum import Curriculum, LecturePlan
from backend.schemas.curriculum import CurriculumSummary

DEFAULT_CURRICULUM_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum.json"


class CurriculumService:
    """
    Service responsible for loading, parsing, validating, and serving course curricula.
    Course-agnostic: strictly operates on schema rules and data integrity.
    """

    def __init__(self, default_path: Optional[Path] = None):
        self.curriculum_path = default_path or DEFAULT_CURRICULUM_PATH
        self._curriculum: Optional[Curriculum] = None
        # Attempt auto-load if default curriculum file exists
        if self.curriculum_path.exists():
            try:
                self.load_from_file(self.curriculum_path)
            except Exception:
                # If default file is missing or invalid during startup, keep as None
                self._curriculum = None

    def validate_and_parse(self, raw_data: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> Curriculum:
        """
        Parses and strictly validates raw curriculum data.
        Supports both raw list of lecture objects and full curriculum container object.
        """
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON format: {exc.msg} at line {exc.lineno}, column {exc.colno}")

        if not isinstance(raw_data, (dict, list)):
            raise ValueError("Curriculum payload must be a JSON object or a JSON array of lectures")

        if isinstance(raw_data, list):
            # Wrapped into standard container
            if len(raw_data) == 0:
                raise ValueError("Curriculum list cannot be empty. At least one lecture is required.")
            raw_data = {
                "course_id": "COURSE-AUTO",
                "course_name": "Course Curriculum",
                "lectures": raw_data,
            }

        try:
            curriculum = Curriculum(**raw_data)
            return curriculum
        except ValidationError as exc:
            # Build human-friendly validation error summary
            error_details = []
            for err in exc.errors():
                loc = " -> ".join(str(p) for p in err.get("loc", []))
                msg = err.get("msg", "Invalid value")
                error_details.append(f"Field '{loc}': {msg}")
            raise ValueError(f"Curriculum validation failed: {'; '.join(error_details)}")

    def load_from_file(self, file_path: Union[str, Path]) -> Curriculum:
        """Loads and validates a curriculum from a JSON file path."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Curriculum file not found at: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse JSON file {path.name}: {exc}")
        except Exception as exc:
            raise ValueError(f"Could not read curriculum file {path.name}: {exc}")

        curriculum = self.validate_and_parse(content)
        self._curriculum = curriculum
        self.curriculum_path = path
        return curriculum

    def load_from_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> Curriculum:
        """Loads and sets the active curriculum from in-memory dictionary or string."""
        curriculum = self.validate_and_parse(data)
        self._curriculum = curriculum
        return curriculum

    def get_curriculum(self) -> Curriculum:
        """Returns the currently active curriculum or raises an error if not loaded."""
        if self._curriculum is None:
            if self.curriculum_path.exists():
                return self.load_from_file(self.curriculum_path)
            raise ValueError("No curriculum loaded. Please upload or load a curriculum file first.")
        return self._curriculum

    def get_lecture(self, lecture_id: str) -> Optional[LecturePlan]:
        """Finds a lecture by its unique identifier (case-insensitive)."""
        curriculum = self.get_curriculum()
        target = lecture_id.strip().lower()
        for lec in curriculum.lectures:
            if lec.lecture.lower() == target:
                return lec
        return None

    def get_summary(self) -> CurriculumSummary:
        """Generates statistical summary of the currently loaded curriculum."""
        curr = self.get_curriculum()
        total_topics = sum(len(l.content) for l in curr.lectures)
        total_cw = sum(len(l.classwork) for l in curr.lectures)
        total_hw = sum(len(l.homework) for l in curr.lectures)

        return CurriculumSummary(
            course_id=curr.course_id,
            course_name=curr.course_name,
            total_lectures=len(curr.lectures),
            total_topics=total_topics,
            total_classwork=total_cw,
            total_homework=total_hw,
        )


# Singleton instance for the application lifecycle
curriculum_service = CurriculumService()
