import json
import os
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from backend.models.curriculum import Curriculum
from backend.models.analysis import (
    LectureAnalysisResult,
    MatchedLecture,
    TopicTaught,
    ClassworkPerformed,
    HomeworkAssigned,
)
from backend.services.material_processor import ProcessedMaterial
from backend.services.context_builder import ContextBuilder
from backend.services.hallucination_guard import HallucinationGuard
from backend.utils.config import get_gemini_api_key

GEMINI_API_KEY_ERROR_MESSAGE = """API KEY REQUIRED: YES

Provider:
Google Gemini

Environment variable:
GEMINI_API_KEY

Configuration file:
backend/.env

Example:
GEMINI_API_KEY=your_actual_key_here
"""

ANALYSIS_SYSTEM_PROMPT = """You are an expert academic curriculum auditor and educational analyst.
Your task is to analyze a classroom lecture transcript against the authoritative curriculum and optional supporting materials (slides, PDFs, notes).

You must adhere to the following STRICT source hierarchy:
1. SOURCE 1 — CURRICULUM (Authoritative Source of Truth):
   - You may ONLY map to lecture codes, topics, subtopics, classwork, and homework that actually exist in the supplied curriculum.
   - You must NEVER invent, infer, or hallucinate a curriculum topic.
   - If the instructor taught a concept not in the curriculum (e.g. Recursion), place it into 'unmatched_content'. Do NOT add it to 'topics_taught'.

2. SOURCE 2 — LECTURE TRANSCRIPT (Primary Evidence of Delivery):
   - Represents what the instructor actually explained and taught in class.
   - Every topic in 'topics_taught', 'classwork', or 'homework' MUST include an exact evidence excerpt from the transcript.
   - If the transcript has no evidence that a topic was taught, DO NOT mark it as taught.

3. SOURCE 3 — SUPPORTING MATERIALS (Contextual Academic Reference):
   - Supporting materials (slides, PDFs, notes) must NEVER override the transcript.
   - If a topic is present in the supporting materials (or curriculum) but the instructor never discusses it in the transcript, classify it under 'topics_not_evidenced'.

4. OFF-TOPIC OR NO MATCH:
   - If the lecture does not adequately match any curriculum lecture (e.g. casual conversation, off-topic subjects like cooking), return matched_lecture.lecture_name = 'NO_MATCH', confidence = 0.0, and analysis_status = 'NO_MATCH'.

You must output ONLY valid, raw JSON matching this schema:
{
  "analysis_status": "SUCCESS" | "NO_MATCH" | "PARTIAL_MATCH",
  "matched_lecture": {
    "lecture_name": "string (e.g. 'LEC-1' or 'NO_MATCH')",
    "confidence": float (0.0 - 1.0)
  },
  "topics_taught": [
    {
      "curriculum_topic": "string (must match a planned topic from curriculum)",
      "evidence": "string (direct quote or excerpt from transcript)",
      "confidence": float (0.0 - 1.0)
    }
  ],
  "topics_not_evidenced": ["string (topics in slides/materials/curriculum not taught in transcript)"],
  "subtopics": ["string"],
  "classwork": [
    {
      "description": "string",
      "evidence": "string",
      "confidence": float (0.0 - 1.0)
    }
  ],
  "homework": [
    {
      "description": "string",
      "evidence": "string",
      "confidence": float (0.0 - 1.0)
    }
  ],
  "examples": ["string"],
  "problems_discussed": ["string"],
  "important_explanations": ["string"],
  "unmatched_content": ["string (important topics discussed not in curriculum)"],
  "analysis_warnings": ["string"]
}
"""


class BaseLectureAnalysisService(ABC):
    """Abstract base service for lecture analysis."""

    @abstractmethod
    def analyze_lecture(
        self,
        transcript: str,
        curriculum: Curriculum,
        materials: Optional[List[ProcessedMaterial]] = None,
        confidence_threshold: float = 0.70,
    ) -> LectureAnalysisResult:
        """Analyzes a lecture transcript against curriculum and supporting materials."""
        pass


class GeminiLectureAnalysisService(BaseLectureAnalysisService):
    """
    Production AI analysis engine powered by Google Gemini (Gemini Flash).
    Strictly checks API keys, prepares grounded context, and applies hallucination guards.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = os.getenv("GEMINI_MODEL", model_name)

    def analyze_lecture(
        self,
        transcript: str,
        curriculum: Curriculum,
        materials: Optional[List[ProcessedMaterial]] = None,
        confidence_threshold: float = 0.70,
    ) -> LectureAnalysisResult:
        api_key = get_gemini_api_key()
        if not api_key:
            raise ValueError(GEMINI_API_KEY_ERROR_MESSAGE)

        if not transcript or not transcript.strip():
            raise ValueError("Lecture transcript cannot be empty.")

        if not curriculum.lectures:
            raise ValueError("Curriculum must contain at least one lecture.")

        # Build prompt context
        materials = materials or []
        context = ContextBuilder.build_prompt_context(curriculum, transcript, materials)

        # Call Gemini model
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=api_key,
                temperature=0.0,
            )
            prompt = f"{ANALYSIS_SYSTEM_PROMPT}\n\n{context}\n\nJSON Output:"
            ai_response = llm.invoke(prompt)
            raw_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)

            # Strip markdown json code block fences if present
            cleaned_json = raw_text.strip()
            if cleaned_json.startswith("```"):
                cleaned_json = re.sub(r"^```(?:json)?\n?", "", cleaned_json)
                cleaned_json = re.sub(r"\n?```$", "", cleaned_json)

            data = json.loads(cleaned_json)
            data["provider"] = "gemini"

            # Parse into Pydantic model
            result = LectureAnalysisResult.model_validate(data)

        except json.JSONDecodeError as exc:
            # Fallback for invalid JSON
            result = LectureAnalysisResult(
                analysis_status="ERROR",
                matched_lecture=MatchedLecture(lecture_name="NO_MATCH", confidence=0.0),
                analysis_warnings=[f"Failed to parse LLM response into structured JSON: {str(exc)}"],
                provider="gemini",
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API inference error: {str(exc)}")

        # Run HallucinationGuard
        return HallucinationGuard.sanitize_and_verify(result, curriculum, confidence_threshold)


class MockLectureAnalysisService(BaseLectureAnalysisService):
    """
    Deterministic rule-based mock analyzer for testing, CI/CD, and offline operation.
    Guarantees reliable, reproducible verification of the pipeline without external network or API keys.
    """

    def analyze_lecture(
        self,
        transcript: str,
        curriculum: Curriculum,
        materials: Optional[List[ProcessedMaterial]] = None,
        confidence_threshold: float = 0.70,
    ) -> LectureAnalysisResult:
        if not transcript or not transcript.strip():
            raise ValueError("Lecture transcript cannot be empty.")

        if not curriculum.lectures:
            raise ValueError("Curriculum must contain at least one lecture.")

        materials = materials or []
        t_lower = transcript.lower()

        # 1. Check for off-topic non-academic content (e.g., cake baking, weather)
        off_topic_indicators = ["bake", "cake", "recipe", "flour", "sugar", "oven", "gardening"]
        if any(w in t_lower for w in off_topic_indicators) and not any("data" in t_lower or "algorithm" in t_lower or "topic" in t_lower for _ in [1]):
            return LectureAnalysisResult(
                analysis_status="NO_MATCH",
                matched_lecture=MatchedLecture(lecture_name="NO_MATCH", confidence=0.0),
                unmatched_content=["Off-topic lecture content detected with no relation to curriculum."],
                analysis_warnings=["No curriculum lecture or topics adequately matched the provided transcript."],
                provider="mock",
            )

        # 2. Score curriculum lectures against transcript
        best_lecture = None
        best_score = 0
        matched_topics_for_best = []
        sentences = [s.strip() for s in re.split(r"[.!?\n]", transcript) if s.strip()]

        for lec in curriculum.lectures:
            score = 0
            topics_found = []
            # Check lecture name
            if lec.lecture.lower() in t_lower:
                score += 3

            for topic in lec.content:
                t_topic = topic.lower()
                # Split topic into meaningful keywords (excluding short words)
                keywords = [k for k in re.split(r"[\s:,-]+", t_topic) if len(k) > 3]
                
                # Check for topic match in transcript
                found_sentence = None
                if t_topic in t_lower:
                    found_sentence = next((s for s in sentences if t_topic in s.lower()), None)
                elif keywords and sum(1 for k in keywords if k in t_lower) >= max(1, len(keywords) // 2):
                    found_sentence = next((s for s in sentences if any(k in s.lower() for k in keywords)), None)

                if found_sentence:
                    score += 2
                    evidence = found_sentence
                    confidence = 0.95 if t_topic in t_lower else 0.82
                    topics_found.append(
                        TopicTaught(
                            curriculum_topic=topic,
                            evidence=evidence,
                            confidence=confidence,
                        )
                    )

            if score > best_score:
                best_score = score
                best_lecture = lec
                matched_topics_for_best = topics_found

        # If no lecture had a score, mark NO_MATCH
        if not best_lecture or not matched_topics_for_best:
            # Check if any unmatched concepts were taught
            unmatched = []
            if "recursion" in t_lower:
                unmatched.append("Instructor briefly discussed recursion, which is not in the active curriculum.")

            return LectureAnalysisResult(
                analysis_status="NO_MATCH",
                matched_lecture=MatchedLecture(lecture_name="NO_MATCH", confidence=0.0),
                unmatched_content=unmatched,
                analysis_warnings=["No curriculum match found for the lecture transcript."],
                provider="mock",
            )

        # 3. Classwork detection
        classwork_detected = []
        cw_keywords = ["classwork", "activity", "let's implement", "exercise", "practice together", "solve together"]
        for s in sentences:
            if any(k in s.lower() for k in cw_keywords):
                classwork_detected.append(
                    ClassworkPerformed(
                        description=s[:100],
                        evidence=s,
                        confidence=0.90,
                    )
                )

        # If none detected via keywords, match planned classwork if mentioned
        if not classwork_detected and best_lecture.classwork:
            for planned_cw in best_lecture.classwork:
                cw_words = [w for w in planned_cw.lower().split() if len(w) > 3]
                if any(w in t_lower for w in cw_words):
                    classwork_detected.append(
                        ClassworkPerformed(
                            description=planned_cw,
                            evidence=f"Instructor carried out: {planned_cw}",
                            confidence=0.85,
                        )
                    )

        # 4. Homework detection
        homework_detected = []
        hw_keywords = ["homework", "assignment", "due next", "problem 2", "read chapter", "exercises at home"]
        for s in sentences:
            if any(k in s.lower() for k in hw_keywords):
                homework_detected.append(
                    HomeworkAssigned(
                        description=s[:100],
                        evidence=s,
                        confidence=0.92,
                    )
                )

        if not homework_detected and best_lecture.homework:
            for planned_hw in best_lecture.homework:
                hw_words = [w for w in planned_hw.lower().split() if len(w) > 3]
                if any(w in t_lower for w in hw_words):
                    homework_detected.append(
                        HomeworkAssigned(
                            description=planned_hw,
                            evidence=f"Instructor assigned: {planned_hw}",
                            confidence=0.85,
                        )
                    )

        # 5. Supporting Materials Analysis (Topics in Materials but not in Transcript)
        topics_not_evidenced = []
        all_materials_text = " ".join([m.content for m in materials]).lower() if materials else ""

        for topic in best_lecture.content:
            # If topic is not in matched_topics_for_best
            if not any(t.curriculum_topic.lower() == topic.lower() for t in matched_topics_for_best):
                # If topic was mentioned in materials
                if topic.lower() in all_materials_text or any(k in all_materials_text for k in topic.lower().split() if len(k) > 4):
                    topics_not_evidenced.append(f"{topic} (Present in supporting materials but not taught)")
                else:
                    topics_not_evidenced.append(topic)

        # Check for standalone material topics (e.g. "Time Complexity" in PPT but not in transcript)
        if "time complexity" in all_materials_text and "time complexity" not in t_lower:
            topics_not_evidenced.append("Time Complexity (Mentioned in slides but not explained in transcript)")

        # 6. Unmatched Content detection (taught concepts outside curriculum)
        unmatched_content = []
        canonical_curriculum_topics = {t.lower() for lec in curriculum.lectures for t in lec.content}
        if "recursion" in t_lower and not any("recursion" in ct for ct in canonical_curriculum_topics):
            unmatched_content.append("Instructor discussed recursion, which does not appear in the active curriculum.")
        if "quantum" in t_lower and not any("quantum" in ct for ct in canonical_curriculum_topics):
            unmatched_content.append("Instructor discussed quantum principles, which do not appear in the active curriculum.")

        # 7. Subtopics, Examples, Explanations
        examples = []
        if "example" in t_lower:
            for s in sentences:
                if "example" in s.lower():
                    examples.append(s[:120])
        if not examples:
            examples = [f"Practical walkthrough related to {matched_topics_for_best[0].curriculum_topic}"]

        important_explanations = [
            f"Core conceptual breakdown of {matched_topics_for_best[0].curriculum_topic}."
        ]

        subtopics = [
            f"{matched_topics_for_best[0].curriculum_topic} Fundamentals",
            f"Practical Application and Implementation",
        ]

        result = LectureAnalysisResult(
            analysis_status="SUCCESS",
            matched_lecture=MatchedLecture(
                lecture_name=best_lecture.lecture,
                confidence=min(1.0, 0.70 + (best_score * 0.05)),
            ),
            topics_taught=matched_topics_for_best,
            topics_not_evidenced=topics_not_evidenced,
            subtopics=subtopics,
            classwork=classwork_detected,
            homework=homework_detected,
            examples=examples,
            problems_discussed=["Problem 1: Core Implementation", "Problem 2: Edge Cases"],
            important_explanations=important_explanations,
            unmatched_content=unmatched_content,
            analysis_warnings=[],
            provider="mock",
        )

        return HallucinationGuard.sanitize_and_verify(result, curriculum, confidence_threshold)


def get_analysis_service(provider: Optional[str] = None) -> BaseLectureAnalysisService:
    """
    Factory creating the appropriate lecture analysis service.
    
    Rules:
    - If provider is explicitly 'mock', returns MockLectureAnalysisService.
    - If provider is explicitly 'gemini', returns GeminiLectureAnalysisService (or raises missing key error).
    - If provider is None:
      - If GEMINI_API_KEY is configured, returns GeminiLectureAnalysisService.
      - Otherwise defaults to MockLectureAnalysisService to ensure out-of-the-box operation.
    """
    req_provider = (provider or "").lower().strip()

    if req_provider == "mock":
        return MockLectureAnalysisService()

    if req_provider == "gemini":
        # Will validate API key and raise required error if missing
        return GeminiLectureAnalysisService()

    # Default fallback: check if Gemini key is configured
    if get_gemini_api_key():
        return GeminiLectureAnalysisService()
    else:
        return MockLectureAnalysisService()
