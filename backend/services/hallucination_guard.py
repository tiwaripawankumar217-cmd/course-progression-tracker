from typing import List, Set, Tuple
from backend.models.curriculum import Curriculum
from backend.models.analysis import LectureAnalysisResult, TopicTaught, MatchedLecture


class HallucinationGuard:
    """
    Deterministic programmatic safeguard that intercepts and corrects any
    hallucinations produced by the LLM.
    
    Guarantees:
    1. Every topic in 'topics_taught' must strictly exist in the supplied curriculum.
    2. Any non-curriculum topic is intercepted and safely rerouted to 'unmatched_content'.
    3. Matched lecture codes must exist in the curriculum; otherwise forced to 'NO_MATCH'.
    4. Topics with confidence below the threshold are flagged in 'analysis_warnings'.
    """

    @classmethod
    def sanitize_and_verify(
        cls,
        result: LectureAnalysisResult,
        curriculum: Curriculum,
        confidence_threshold: float = 0.70
    ) -> LectureAnalysisResult:
        """
        Validates analysis output against authoritative curriculum data.
        Modifies and returns the validated result with updated warnings.
        """
        valid_lecture_codes = {lec.lecture.strip().upper() for lec in curriculum.lectures}
        
        # Build mapping of canonical topics (case-insensitive)
        valid_topics_map = {}
        for lec in curriculum.lectures:
            for topic in lec.content:
                valid_topics_map[topic.strip().lower()] = topic.strip()

        sanitized_topics_taught: List[TopicTaught] = []
        unmatched_topics_found: List[str] = list(result.unmatched_content)
        warnings: List[str] = list(result.analysis_warnings)

        # 1. Validate Matched Lecture Code
        matched_code = result.matched_lecture.lecture_name.strip().upper()
        if matched_code != "NO_MATCH" and matched_code not in valid_lecture_codes:
            warnings.append(
                f"Hallucination Guard: Lecture '{result.matched_lecture.lecture_name}' "
                "does not exist in active curriculum; reclassified to 'NO_MATCH'."
            )
            result.matched_lecture = MatchedLecture(
                lecture_name="NO_MATCH",
                confidence=0.0
            )
            result.analysis_status = "NO_MATCH"

        # 2. Validate Topics Taught against Curriculum
        for item in result.topics_taught:
            norm_topic = item.curriculum_topic.strip().lower()
            
            # Check for exact or normalized match
            matched_canonical = None
            if norm_topic in valid_topics_map:
                matched_canonical = valid_topics_map[norm_topic]
            else:
                # Substring match if LLM slightly altered the title
                for valid_norm, canonical in valid_topics_map.items():
                    if norm_topic == valid_norm or norm_topic in valid_norm or valid_norm in norm_topic:
                        matched_canonical = canonical
                        break

            if matched_canonical:
                # Update with exact canonical topic name from curriculum
                item.curriculum_topic = matched_canonical
                
                # Check confidence threshold
                if item.confidence < confidence_threshold:
                    warnings.append(
                        f"Low confidence ({item.confidence:.2f}) for topic '{item.curriculum_topic}'; "
                        f"flagged for manual review (threshold: {confidence_threshold:.2f})."
                    )
                sanitized_topics_taught.append(item)
            else:
                # Hallucination detected! Reroute to unmatched_content
                unmatched_desc = (
                    f"Taught concept '{item.curriculum_topic}' (Evidence: '{item.evidence}') "
                    "does not exist in the active curriculum."
                )
                unmatched_topics_found.append(unmatched_desc)
                warnings.append(
                    f"Hallucination Guard: Rerouted non-curriculum topic '{item.curriculum_topic}' "
                    "from 'topics_taught' to 'unmatched_content'."
                )

        result.topics_taught = sanitized_topics_taught
        result.unmatched_content = unmatched_topics_found

        # 3. Check Overall Status
        if result.matched_lecture.lecture_name == "NO_MATCH" or (not result.topics_taught and not result.classwork):
            if result.analysis_status != "ERROR":
                result.analysis_status = "NO_MATCH"
                if not any("No curriculum match" in w for w in warnings):
                    warnings.append("No curriculum lecture or topics adequately matched the provided transcript.")
        elif result.unmatched_content and not result.topics_taught:
            result.analysis_status = "NO_MATCH"

        result.analysis_warnings = warnings
        return result
