import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.curriculum import Curriculum, LecturePlan
from backend.models.analysis import (
    LectureAnalysisResult,
    MatchedLecture,
    TopicTaught,
    ClassworkPerformed,
    HomeworkAssigned,
)
from backend.models.progress import (
    TopicStatus,
    ProgressThresholdConfig,
)
from backend.services.progress_engine import ProgressEngine

client = TestClient(app)


@pytest.fixture
def sample_curriculum():
    """Provides a deterministic test curriculum."""
    return Curriculum(
        course_id="CS-101",
        course_name="Data Structures & Algorithms",
        lectures=[
            LecturePlan(
                week=1,
                day=1,
                lecture="LEC-1",
                content=["Arrays", "Array Traversal", "Time Complexity"],
                classwork=["Find Maximum Element in Array"],
                homework=["Solve 5 Array Practice Problems"],
            ),
            LecturePlan(
                week=1,
                day=2,
                lecture="LEC-2",
                content=["Dynamic Arrays", "Amortized Analysis", "Two Pointers Technique"],
                classwork=["Implement Custom Vector"],
                homework=["Two Sum Problem"],
            ),
        ],
    )


def test_100_percent_topic_coverage(sample_curriculum):
    """Test 1: 100% topic coverage marks lecture COMPLETED with 100% covered and completed."""
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="SUCCESS",
        matched_lecture=MatchedLecture(lecture_name="LEC-1", confidence=0.95),
        topics_taught=[
            TopicTaught(curriculum_topic="Arrays", evidence="Discussed array memory allocation.", confidence=0.95),
            TopicTaught(curriculum_topic="Array Traversal", evidence="Showed for-loop scan.", confidence=0.92),
            TopicTaught(curriculum_topic="Time Complexity", evidence="Explained O(1) vs O(N).", confidence=0.90),
        ],
        classwork=[ClassworkPerformed(description="Find Maximum Element", evidence="Students coded max.", confidence=0.9)],
        homework=[HomeworkAssigned(description="Solve 5 problems", evidence="Assigned on portal.", confidence=0.9)],
    )

    prog = engine.calculate_progress(analysis=analysis, curriculum=sample_curriculum, lecture_code="LEC-1")

    assert prog.lecture == "LEC-1"
    assert prog.percent_covered == 100.0
    assert prog.percent_completed == 100.0
    assert prog.status == "COMPLETED"
    assert len(prog.topics) == 3
    assert all(t.status == TopicStatus.COVERED for t in prog.topics)
    assert len(prog.classwork) == 1
    assert len(prog.homework) == 1


def test_partial_coverage(sample_curriculum):
    """Test 2: Partial coverage (2 of 3 topics) yields 66.67% and ONGOING status."""
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="SUCCESS",
        matched_lecture=MatchedLecture(lecture_name="LEC-1", confidence=0.95),
        topics_taught=[
            TopicTaught(curriculum_topic="Arrays", evidence="Defined contiguous array.", confidence=0.95),
            TopicTaught(curriculum_topic="Array Traversal", evidence="Loop iteration.", confidence=0.91),
        ],
        topics_not_evidenced=["Time Complexity"],
    )

    prog = engine.calculate_progress(analysis=analysis, curriculum=sample_curriculum, lecture_code="LEC-1")

    assert prog.percent_covered == 66.67
    assert prog.percent_completed == 66.67
    assert prog.status == "ONGOING"
    assert prog.topics[0].status == TopicStatus.COVERED
    assert prog.topics[1].status == TopicStatus.COVERED
    assert prog.topics[2].status == TopicStatus.NOT_COVERED
    assert prog.topics[2].evidence is None
    assert prog.topics[2].confidence is None


def test_zero_coverage(sample_curriculum):
    """Test 3: Zero topics taught yields 0% and NOT_STARTED status."""
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="SUCCESS",
        matched_lecture=MatchedLecture(lecture_name="LEC-1", confidence=0.8),
        topics_taught=[],
        topics_not_evidenced=["Arrays", "Array Traversal", "Time Complexity"],
    )

    prog = engine.calculate_progress(analysis=analysis, curriculum=sample_curriculum, lecture_code="LEC-1")

    assert prog.percent_covered == 0.0
    assert prog.percent_completed == 0.0
    assert prog.status == "NOT_STARTED"
    assert all(t.status == TopicStatus.NOT_COVERED for t in prog.topics)


def test_low_confidence_uncertain_topic(sample_curriculum):
    """
    Test 4: Low-confidence topic (e.g. 0.42 < 0.65 threshold) is marked 'uncertain'.
    % Covered includes uncertain topic (66.67%), while % Completed strictly excludes it (33.33%).
    """
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="SUCCESS",
        matched_lecture=MatchedLecture(lecture_name="LEC-1", confidence=0.9),
        topics_taught=[
            TopicTaught(curriculum_topic="Arrays", evidence="Defined arrays thoroughly.", confidence=0.95),
            TopicTaught(curriculum_topic="Array Traversal", evidence="Mentioned traversal in passing.", confidence=0.42),
        ],
        topics_not_evidenced=["Time Complexity"],
    )

    cfg = ProgressThresholdConfig(confidence_threshold=0.65)
    prog = engine.calculate_progress(
        analysis=analysis,
        curriculum=sample_curriculum,
        lecture_code="LEC-1",
        config=cfg,
    )

    assert prog.topics[0].status == TopicStatus.COVERED
    assert prog.topics[1].status == TopicStatus.UNCERTAIN
    assert prog.topics[1].confidence == 0.42
    assert prog.topics[2].status == TopicStatus.NOT_COVERED

    # % Covered counts covered + uncertain = 2/3 = 66.67%
    assert prog.percent_covered == 66.67
    # % Completed counts confirmed covered = 1/3 = 33.33%
    assert prog.percent_completed == 33.33

    # Low-confidence warning should be surfaced
    assert any("requires review" in w for w in prog.warnings)


def test_spilled_over_status(sample_curriculum):
    """Test 5: When lecture is finalized with incomplete topics, status is 'SPILLED OVER'."""
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="SUCCESS",
        matched_lecture=MatchedLecture(lecture_name="LEC-1", confidence=0.95),
        topics_taught=[
            TopicTaught(curriculum_topic="Arrays", evidence="Defined arrays.", confidence=0.95),
            TopicTaught(curriculum_topic="Array Traversal", evidence="Loops.", confidence=0.90),
        ],
        topics_not_evidenced=["Time Complexity"],
    )

    cfg = ProgressThresholdConfig(
        completed_threshold=100.0,
        spillover_enabled=True,
        is_finalized=True,  # Session concluded
    )
    prog = engine.calculate_progress(
        analysis=analysis,
        curriculum=sample_curriculum,
        lecture_code="LEC-1",
        config=cfg,
    )

    assert prog.status == "SPILLED OVER"
    assert prog.percent_completed == 66.67


def test_no_curriculum_match(sample_curriculum):
    """Test 6: NO_MATCH or non-existent lecture code returns NOT_STARTED with clear warning."""
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="NO_MATCH",
        matched_lecture=MatchedLecture(lecture_name="NO_MATCH", confidence=0.0),
        topics_taught=[],
    )

    prog = engine.calculate_progress(analysis=analysis, curriculum=sample_curriculum)

    assert prog.status == "NOT_STARTED"
    assert prog.percent_covered == 0.0
    assert prog.percent_completed == 0.0
    assert any("No reliable curriculum match" in w for w in prog.warnings)


def test_classwork_and_homework_evidence(sample_curriculum):
    """Test 7: Classwork and homework only included when evidenced."""
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="SUCCESS",
        matched_lecture=MatchedLecture(lecture_name="LEC-1", confidence=0.9),
        topics_taught=[TopicTaught(curriculum_topic="Arrays", evidence="Defined arrays.", confidence=0.9)],
        classwork=[
            ClassworkPerformed(
                description="Find Maximum Element",
                evidence="Students wrote loop to find maximum integer in array.",
                confidence=0.95,
            )
        ],
        homework=[],  # No homework assigned in this lecture
    )

    prog = engine.calculate_progress(analysis=analysis, curriculum=sample_curriculum, lecture_code="LEC-1")

    assert len(prog.classwork) == 1
    assert prog.classwork[0].description == "Find Maximum Element"
    assert "wrote loop" in prog.classwork[0].evidence
    assert len(prog.homework) == 0  # Should be empty when none assigned


def test_unmatched_content_in_warnings(sample_curriculum):
    """Test 8: Topics taught outside the curriculum are captured as warnings, not curriculum topics."""
    engine = ProgressEngine()
    analysis = LectureAnalysisResult(
        analysis_status="SUCCESS",
        matched_lecture=MatchedLecture(lecture_name="LEC-1", confidence=0.9),
        topics_taught=[TopicTaught(curriculum_topic="Arrays", evidence="Defined arrays.", confidence=0.9)],
        unmatched_content=["Introduction to Quantum Computing"],
    )

    prog = engine.calculate_progress(analysis=analysis, curriculum=sample_curriculum, lecture_code="LEC-1")

    # Curriculum topics must only be the planned 3
    topic_names = [t.name for t in prog.topics]
    assert "Introduction to Quantum Computing" not in topic_names
    assert any("Quantum Computing" in w for w in prog.warnings)


def test_api_calculate_endpoint(sample_curriculum):
    """Test 9: POST /progress/calculate returns valid response."""
    payload = {
        "analysis": {
            "analysis_status": "SUCCESS",
            "matched_lecture": {"lecture_name": "LEC-1", "confidence": 0.95},
            "topics_taught": [
                {"curriculum_topic": "Arrays", "evidence": "Arrays discussed.", "confidence": 0.95},
                {"curriculum_topic": "Array Traversal", "evidence": "Scan discussed.", "confidence": 0.91},
            ],
            "classwork": [{"description": "Find Maximum", "evidence": "Loop coded.", "confidence": 0.9}],
            "homework": [{"description": "Solve 5 Problems", "evidence": "Assigned.", "confidence": 0.9}],
        },
        "curriculum": sample_curriculum.model_dump(),
        "lecture_code": "LEC-1",
        "config": {"completed_threshold": 100.0, "spillover_enabled": True, "is_finalized": False},
    }

    response = client.post("/progress/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    prog = data["progression"]
    assert prog["lecture"] == "LEC-1"
    assert prog["status"] == "ONGOING"
    assert prog["percent_covered"] == 66.67
    assert prog["percent_completed"] == 66.67
    assert len(prog["topics"]) == 3
    assert len(prog["classwork"]) == 1
    assert len(prog["homework"]) == 1


def test_api_demo_endpoint():
    """Test 10: GET /progress/demo returns all 4 pre-configured demonstration scenarios."""
    response = client.get("/progress/demo")
    assert response.status_code == 200
    data = response.json()
    assert "curriculum" in data
    assert "scenarios" in data
    assert len(data["scenarios"]) == 4


def test_progress_ui_endpoint():
    """Test 11: GET /progress/ui serves the compiled React application bundle."""
    response = client.get("/progress/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Course Progression Tracker" in response.text
    assert '<div id="root"></div>' in response.text

