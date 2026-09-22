import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.curriculum import Curriculum, LecturePlan
from backend.services.curriculum_service import curriculum_service
from backend.services.material_processor import ProcessedMaterial, MaterialProcessor
from backend.services.analysis_service import (
    MockLectureAnalysisService,
    GeminiLectureAnalysisService,
    get_analysis_service,
    GEMINI_API_KEY_ERROR_MESSAGE,
)
from backend.services.hallucination_guard import HallucinationGuard
from backend.tests.test_material_processor import create_mock_pptx_bytes

client = TestClient(app)


@pytest.fixture
def sample_curriculum() -> Curriculum:
    """Provides a clean, standard 2-lecture test curriculum."""
    return Curriculum(
        course_id="CS-101",
        course_name="Data Structures and Algorithms",
        lectures=[
            LecturePlan(
                week=1,
                day=1,
                lecture="LEC-1",
                content=[
                    "Topic A: Core Principles",
                    "Topic B: Conceptual Framework",
                ],
                classwork=["Activity 1: Guided Concept Review"],
                homework=["Homework 1: Practice Exercises"],
            ),
            LecturePlan(
                week=1,
                day=2,
                lecture="LEC-2",
                content=[
                    "Topic C: Primary Methodologies",
                    "Topic D: Systematic Implementation",
                ],
                classwork=["Activity 2: Pair Programming"],
                homework=["Homework 2: Lab Submission"],
            ),
        ],
    )


# ==============================================================================
# 1. Test 1 — Transcript + Curriculum
# ==============================================================================
def test_transcript_plus_curriculum_matches_topic_with_evidence(sample_curriculum):
    """
    Test 1: Verify AI analysis identifies a curriculum topic and includes
    transcript evidence without inventing topics.
    """
    service = MockLectureAnalysisService()
    transcript = (
        "Welcome everyone to class. Today we will thoroughly cover Topic A: Core Principles. "
        "The core principles govern all architectural decisions in our software stack. "
        "Let's conduct Activity 1: Guided Concept Review as our classwork. "
        "For homework, please work on Homework 1: Practice Exercises."
    )

    result = service.analyze_lecture(
        transcript=transcript,
        curriculum=sample_curriculum,
    )

    assert result.analysis_status == "SUCCESS"
    assert result.matched_lecture.lecture_name == "LEC-1"
    assert result.matched_lecture.confidence >= 0.70

    # Verify topics taught contains curriculum topic and evidence
    taught_topics = [t.curriculum_topic for t in result.topics_taught]
    assert "Topic A: Core Principles" in taught_topics

    topic_entry = next(t for t in result.topics_taught if t.curriculum_topic == "Topic A: Core Principles")
    assert len(topic_entry.evidence) > 0
    assert "Topic A" in topic_entry.evidence

    # Verify classwork & homework detected
    assert len(result.classwork) > 0
    assert len(result.homework) > 0


# ==============================================================================
# 2. Test 2 — Transcript + Curriculum + PDF
# ==============================================================================
def test_transcript_plus_curriculum_plus_pdf(sample_curriculum):
    """
    Test 2: Verify PDF supporting context is accepted, parsed, and incorporated
    into the analysis without overriding the transcript.
    """
    service = MockLectureAnalysisService()
    transcript = (
        "In this session, we study Topic A: Core Principles. "
        "We reviewed the foundational concepts and discussed the main definitions."
    )
    pdf_material = ProcessedMaterial(
        name="lecture1_notes.pdf",
        material_type="pdf",
        content="[Page 1]\nLecture 1 Supplementary Notes on Core Principles and Systemic Axioms.",
        page_or_slide_count=1,
    )

    result = service.analyze_lecture(
        transcript=transcript,
        curriculum=sample_curriculum,
        materials=[pdf_material],
    )

    assert result.analysis_status == "SUCCESS"
    assert result.matched_lecture.lecture_name == "LEC-1"
    assert any(t.curriculum_topic == "Topic A: Core Principles" for t in result.topics_taught)


# ==============================================================================
# 3. Test 3 — Transcript + Curriculum + PPT
# ==============================================================================
def test_transcript_plus_curriculum_plus_ppt_identifies_unevidenced_topics(sample_curriculum):
    """
    Test 3: Verify PPT context is accepted. If a topic is present in slides but
    NOT taught in the transcript, it must be marked in 'topics_not_evidenced'.
    """
    service = MockLectureAnalysisService()
    transcript = (
        "Today we only had time to discuss Topic A: Core Principles. "
        "We walked through the architectural definitions."
    )
    ppt_material = ProcessedMaterial(
        name="lecture1_deck.pptx",
        material_type="pptx",
        content=(
            "[Slide 1]\nCore Principles\n"
            "[Slide 2]\nTopic A: Core Principles\n"
            "[Slide 3]\nTime Complexity and Big-O Notation"
        ),
        page_or_slide_count=3,
    )

    result = service.analyze_lecture(
        transcript=transcript,
        curriculum=sample_curriculum,
        materials=[ppt_material],
    )

    assert result.analysis_status == "SUCCESS"
    # Time Complexity was in slides but teacher did not teach it
    assert any("Time Complexity" in t for t in result.topics_not_evidenced)


# ==============================================================================
# 4. Test 4 — Unsupported Material Handled Gracefully
# ==============================================================================
def test_unsupported_material_handling():
    """
    Test 4: Verify unsupported or corrupted material is handled gracefully with
    a warning, without crashing the pipeline.
    """
    material = MaterialProcessor.process_material("bad_archive.bin", b"\x00\xff\xfe", file_type="bin")
    assert material.success is False
    assert len(material.warnings) > 0
    assert "unsupported" in material.warnings[0].lower()


# ==============================================================================
# 5. Test 5 — Off-Topic Lecture (NO_MATCH)
# ==============================================================================
def test_off_topic_lecture_returns_no_match(sample_curriculum):
    """
    Test 5: Verify that an off-topic transcript (e.g. baking cake) returns
    matched_lecture = 'NO_MATCH' and appropriate warnings.
    """
    service = MockLectureAnalysisService()
    transcript = (
        "Today we will learn how to bake a moist chocolate cake. "
        "Preheat your oven to 350 degrees, sift two cups of flour, add sugar and cocoa powder."
    )

    result = service.analyze_lecture(
        transcript=transcript,
        curriculum=sample_curriculum,
    )

    assert result.analysis_status == "NO_MATCH"
    assert result.matched_lecture.lecture_name == "NO_MATCH"
    assert result.matched_lecture.confidence == 0.0
    assert len(result.topics_taught) == 0
    assert len(result.analysis_warnings) > 0


# ==============================================================================
# 6. Test 6 — Hallucination Protection
# ==============================================================================
def test_hallucination_protection_blocks_invented_curriculum_topics(sample_curriculum):
    """
    Test 6: If the transcript contains a topic that does not exist in the curriculum
    (e.g., Recursion), the system must NOT add it to 'topics_taught'.
    It must safely route it to 'unmatched_content'.
    """
    service = MockLectureAnalysisService()
    # Transcript discusses Recursion, which is NOT in sample_curriculum (only Topic A, B, C, D)
    transcript = (
        "Today in class we studied Recursion and divide-and-conquer paradigms. "
        "Recursion involves a recursive step and a base case. We solved Fibonacci recursively."
    )

    result = service.analyze_lecture(
        transcript=transcript,
        curriculum=sample_curriculum,
    )

    # 1. Topics taught must not contain Recursion
    taught_names = [t.curriculum_topic.lower() for t in result.topics_taught]
    assert not any("recursion" in name for name in taught_names)

    # 2. Recursion must be logged in unmatched_content
    unmatched_text = " ".join(result.unmatched_content).lower()
    assert "recursion" in unmatched_text


# ==============================================================================
# 7. Test 7 — Missing API Key Error Handling
# ==============================================================================
def test_missing_gemini_api_key_raises_explicit_error(sample_curriculum):
    """
    Test 7: Verify clear configuration error message when GEMINI_API_KEY is missing.
    """
    service = GeminiLectureAnalysisService()
    transcript = "Introduction to core principles."

    # Simulate environment without key
    with patch("backend.services.analysis_service.get_gemini_api_key", return_value=""):
        with pytest.raises(ValueError) as exc_info:
            service.analyze_lecture(
                transcript=transcript,
                curriculum=sample_curriculum,
            )

        err_msg = str(exc_info.value)
        assert "API KEY REQUIRED: YES" in err_msg
        assert "Google Gemini" in err_msg
        assert "GEMINI_API_KEY" in err_msg
        assert "backend/.env" in err_msg


# ==============================================================================
# 8. REST API Endpoints Verification
# ==============================================================================
def test_api_analyze_json_endpoint():
    """Verify POST /analyze returns 200 and structured response."""
    payload = {
        "transcript": (
            "In today's lecture on Topic A: Core Principles, we explained the foundational "
            "architecture and conducted Activity 1: Guided Concept Review."
        ),
        "provider": "mock",
        "materials": [
            {
                "name": "slides.pptx",
                "type": "pptx",
                "content": "[Slide 1]\nCore Principles\n[Slide 2]\nTime Complexity Analysis",
            }
        ],
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "analysis" in data
    assert data["analysis"]["matched_lecture"]["lecture_name"] == "LEC-1"
    assert len(data["analysis"]["topics_taught"]) > 0


def test_api_analyze_upload_endpoint():
    """Verify POST /analyze/upload with multipart file upload."""
    pptx_bytes = create_mock_pptx_bytes(["Slide 1: Core Principles", "Slide 2: Algorithms"])
    transcript_text = "Today we covered Topic A: Core Principles in detail."

    response = client.post(
        "/analyze/upload?provider=mock",
        data={"transcript": transcript_text},
        files=[("files", ("lecture_slides.pptx", io.BytesIO(pptx_bytes), "application/vnd.openxmlformats-officedocument.presentationml.presentation"))],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["analysis"]["matched_lecture"]["lecture_name"] == "LEC-1"


def test_api_analyze_ui_page():
    """Verify GET /analyze/ui renders the testing dashboard."""
    response = client.get("/analyze/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI Lecture Analysis Studio" in response.text
