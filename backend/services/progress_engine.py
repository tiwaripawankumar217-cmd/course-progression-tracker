from datetime import date
from typing import List, Optional, Tuple
import re

from backend.models.curriculum import Curriculum, LecturePlan
from backend.models.analysis import LectureAnalysisResult, TopicTaught
from backend.models.progress import (
    TopicStatus,
    TopicProgress,
    ClassworkItem,
    HomeworkItem,
    MaterialItem,
    ProgressThresholdConfig,
    LectureProgression,
)
from backend.services.curriculum_service import curriculum_service


class ProgressEngine:
    """
    Deterministic Curriculum Mapping & Progress Engine for Day 4.
    Reconciles planned curriculum with actual AI lecture delivery.
    Performs deterministic arithmetic in Python with zero LLM hallucinations.
    """

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalizes text for robust curriculum topic matching."""
        cleaned = re.sub(r"^(topic\s+[a-z0-9]+[:\-\.]?\s*|\d+[\.:\-\)]\s*)", "", text.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return " ".join(cleaned.lower().split())

    def _find_matching_topic(
        self,
        planned_topic: str,
        topics_taught: List[TopicTaught]
    ) -> Optional[TopicTaught]:
        """Finds if a planned topic was taught in the lecture delivery."""
        norm_planned = self._normalize_text(planned_topic)
        exact_planned_lower = planned_topic.strip().lower()

        # 1. Exact or normalized matching
        for item in topics_taught:
            curr_topic = item.curriculum_topic.strip().lower()
            if curr_topic == exact_planned_lower or self._normalize_text(item.curriculum_topic) == norm_planned:
                return item

        # 2. Substring containment matching
        for item in topics_taught:
            norm_taught = self._normalize_text(item.curriculum_topic)
            if (norm_planned and norm_taught) and (norm_planned in norm_taught or norm_taught in norm_planned):
                return item

        return None

    def calculate_progress(
        self,
        analysis: LectureAnalysisResult,
        curriculum: Optional[Curriculum] = None,
        lecture_code: Optional[str] = None,
        date_taught: Optional[str] = None,
        config: Optional[ProgressThresholdConfig] = None,
    ) -> LectureProgression:
        """
        Calculates deterministic course progression by mapping lecture analysis to planned curriculum.

        Formulas:
          % Covered = (covered_topics + uncertain_topics) / total_planned_topics * 100
          % Completed = confirmed_covered_topics / total_planned_topics * 100
        """
        cfg = config or ProgressThresholdConfig()
        resolved_date = date_taught or date.today().isoformat()
        active_curriculum = curriculum or curriculum_service.get_curriculum()

        # Determine target lecture code
        target_code = (
            lecture_code.strip()
            if lecture_code and lecture_code.strip()
            else analysis.matched_lecture.lecture_name.strip()
        )

        warnings: List[str] = list(analysis.analysis_warnings or [])

        # Handle 'NO_MATCH' or empty target code
        if not target_code or target_code.upper() == "NO_MATCH":
            warnings.append("No reliable curriculum match was found for lecture delivery.")
            return LectureProgression(
                lecture=target_code or "NO_MATCH",
                date_taught=resolved_date,
                status="NOT_STARTED",
                percent_completed=0.0,
                percent_covered=0.0,
                topics=[],
                classwork=[],
                homework=[],
                supporting_materials=[],
                warnings=warnings,
            )

        # Locate planned lecture in curriculum
        target_plan: Optional[LecturePlan] = None
        for plan in active_curriculum.lectures:
            if plan.lecture.strip().lower() == target_code.lower():
                target_plan = plan
                break

        if not target_plan:
            warnings.append(f"Lecture '{target_code}' does not exist in the active curriculum.")
            return LectureProgression(
                lecture=target_code,
                date_taught=resolved_date,
                status="NOT_STARTED",
                percent_completed=0.0,
                percent_covered=0.0,
                topics=[],
                classwork=[],
                homework=[],
                supporting_materials=[],
                warnings=warnings,
            )

        # Reconcile topics
        planned_topics = target_plan.content
        topic_progress_list: List[TopicProgress] = []
        covered_count = 0
        uncertain_count = 0

        for planned in planned_topics:
            matched_taught = self._find_matching_topic(planned, analysis.topics_taught)
            if matched_taught:
                conf = float(matched_taught.confidence)
                if conf < cfg.confidence_threshold:
                    # Low-confidence evidence -> flagged as uncertain
                    status = TopicStatus.UNCERTAIN
                    uncertain_count += 1
                    warnings.append(
                        f"Topic '{planned}' has low confidence ({conf:.2f}) and requires review."
                    )
                else:
                    status = TopicStatus.COVERED
                    covered_count += 1

                topic_progress_list.append(
                    TopicProgress(
                        name=planned,
                        status=status,
                        confidence=conf,
                        evidence=matched_taught.evidence,
                    )
                )
            else:
                topic_progress_list.append(
                    TopicProgress(
                        name=planned,
                        status=TopicStatus.NOT_COVERED,
                        confidence=None,
                        evidence=None,
                    )
                )

        # Record unmatched content as informational warnings
        if analysis.unmatched_content:
            for extra in analysis.unmatched_content:
                warnings.append(f"Extra topic taught outside curriculum: {extra}")

        # Deterministic Progress Calculation
        total_planned = len(planned_topics)
        if total_planned > 0:
            percent_covered = round(((covered_count + uncertain_count) / total_planned) * 100.0, 2)
            percent_completed = round((covered_count / total_planned) * 100.0, 2)
        else:
            percent_covered = 0.0
            percent_completed = 0.0

        # Deterministic Status Engine
        if total_planned == 0 or (covered_count == 0 and uncertain_count == 0):
            computed_status = "NOT_STARTED"
        elif percent_completed >= cfg.completed_threshold:
            computed_status = "COMPLETED"
        elif cfg.spillover_enabled and cfg.is_finalized and percent_completed < cfg.completed_threshold:
            computed_status = "SPILLED OVER"
        elif percent_covered > cfg.ongoing_threshold:
            computed_status = "ONGOING"
        else:
            computed_status = "NOT_STARTED"

        # Map Classwork and Homework
        classwork_items: List[ClassworkItem] = [
            ClassworkItem(
                description=cw.description,
                evidence=cw.evidence,
                confidence=cw.confidence,
            )
            for cw in analysis.classwork
        ]

        homework_items: List[HomeworkItem] = [
            HomeworkItem(
                description=hw.description,
                evidence=hw.evidence,
                confidence=hw.confidence,
            )
            for hw in analysis.homework
        ]

        # Supporting Materials (default list derived from active curriculum and analyzed content)
        materials: List[MaterialItem] = [
            MaterialItem(name="curriculum.json", type="json", status="processed")
        ]

        return LectureProgression(
            lecture=target_plan.lecture,
            date_taught=resolved_date,
            status=computed_status,
            percent_completed=percent_completed,
            percent_covered=percent_covered,
            topics=topic_progress_list,
            classwork=classwork_items,
            homework=homework_items,
            supporting_materials=materials,
            warnings=warnings,
        )

    @staticmethod
    def recalculate_from_topics(
        topics: List[TopicProgress],
        config: Optional[ProgressThresholdConfig] = None
    ) -> Tuple[float, float, str]:
        """
        Deterministically recalculates % Covered, % Completed, and status
        from a list of TopicProgress items (e.g. after teacher overrides).
        """
        cfg = config or ProgressThresholdConfig()
        total = len(topics)
        if total == 0:
            return 0.0, 0.0, "NOT_STARTED"

        covered_count = sum(1 for t in topics if t.status == TopicStatus.COVERED)
        uncertain_count = sum(1 for t in topics if t.status == TopicStatus.UNCERTAIN)

        percent_covered = round(((covered_count + uncertain_count) / total) * 100.0, 2)
        percent_completed = round((covered_count / total) * 100.0, 2)

        if covered_count == 0 and uncertain_count == 0:
            status_val = "NOT_STARTED"
        elif percent_completed >= cfg.completed_threshold:
            status_val = "COMPLETED"
        elif cfg.spillover_enabled and cfg.is_finalized and percent_completed < cfg.completed_threshold:
            status_val = "SPILLED OVER"
        elif percent_covered > cfg.ongoing_threshold:
            status_val = "ONGOING"
        else:
            status_val = "NOT_STARTED"

        return percent_covered, percent_completed, status_val


progress_engine = ProgressEngine()
