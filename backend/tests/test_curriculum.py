import io
import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.curriculum_service import curriculum_service, DEFAULT_CURRICULUM_PATH
from backend.models.curriculum import LecturePlan, Curriculum

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_default_curriculum():
    """Ensure every test starts with the default curriculum loaded."""
    curriculum_service.load_from_file(DEFAULT_CURRICULUM_PATH)
    yield
    curriculum_service.load_from_file(DEFAULT_CURRICULUM_PATH)


def test_get_curriculum_success():
    """Test retrieving active curriculum returns correct data and summary."""
    response = client.get("/curriculum")
    assert response.status_code == 200
    data = response.json()

    assert "lectures" in data
    assert "summary" in data
    assert len(data["lectures"]) >= 1

    first_lecture = data["lectures"][0]
    assert "week" in first_lecture
    assert "day" in first_lecture
    assert "lecture" in first_lecture
    assert "content" in first_lecture
    assert "classwork" in first_lecture
    assert "homework" in first_lecture
    assert isinstance(first_lecture["content"], list)
    assert isinstance(first_lecture["classwork"], list)
    assert isinstance(first_lecture["homework"], list)

    summary = data["summary"]
    assert summary["total_lectures"] == len(data["lectures"])
    assert summary["total_topics"] > 0


def test_get_lecture_by_id_success():
    """Test retrieving a specific lecture plan by identifier."""
    response = client.get("/curriculum/lectures/LEC-1")
    assert response.status_code == 200
    data = response.json()
    assert data["lecture"] == "LEC-1"
    assert data["week"] == 1
    assert data["day"] == 1
    assert len(data["content"]) > 0


def test_get_lecture_by_id_case_insensitive():
    """Test retrieving lecture is case-insensitive (lec-1 vs LEC-1)."""
    response = client.get("/curriculum/lectures/lec-1")
    assert response.status_code == 200
    data = response.json()
    assert data["lecture"] == "LEC-1"


def test_get_lecture_by_id_not_found():
    """Test querying a non-existent lecture returns 404."""
    response = client.get("/curriculum/lectures/NON_EXISTENT_LEC")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not found" in detail.lower()


def test_load_curriculum_valid_container():
    """Test loading a custom full curriculum container via POST /curriculum/load."""
    payload = {
        "course_id": "TEST-COURSE",
        "course_name": "Test Course Name",
        "lectures": [
            {
                "week": 1,
                "day": 1,
                "lecture": "T-LEC-01",
                "content": ["Topic 1", "Topic 2"],
                "classwork": ["Activity 1"],
                "homework": ["HW 1"],
            }
        ],
    }
    response = client.post("/curriculum/load", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"]["total_lectures"] == 1
    assert data["summary"]["course_id"] == "TEST-COURSE"

    # Confirm it is now active
    get_res = client.get("/curriculum")
    assert get_res.json()["course_id"] == "TEST-COURSE"


def test_load_curriculum_valid_raw_list():
    """Test loading curriculum as a raw JSON list of lectures."""
    payload = [
        {
            "week": 1,
            "day": 1,
            "lecture": "LIST-LEC-1",
            "content": ["Concept Alpha", "Concept Beta"],
            "classwork": [],
            "homework": [],
        },
        {
            "week": 1,
            "day": 2,
            "lecture": "LIST-LEC-2",
            "content": ["Concept Gamma"],
            "classwork": ["CW 1"],
            "homework": ["HW 1"],
        },
    ]
    response = client.post("/curriculum/load", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"]["total_lectures"] == 2


def test_load_curriculum_empty_list_rejected():
    """Test loading an empty list of lectures is rejected with 422."""
    response = client.post("/curriculum/load", json=[])
    assert response.status_code == 422
    assert "at least one lecture" in response.json()["detail"].lower()


def test_load_curriculum_invalid_week_number():
    """Test invalid week (< 1) is rejected."""
    payload = [
        {
            "week": 0,
            "day": 1,
            "lecture": "LEC-BAD",
            "content": ["Topic A"],
        }
    ]
    response = client.post("/curriculum/load", json=payload)
    assert response.status_code == 422
    assert "week" in response.json()["detail"].lower()


def test_load_curriculum_missing_content():
    """Test lecture with empty content list is rejected."""
    payload = [
        {
            "week": 1,
            "day": 1,
            "lecture": "LEC-EMPTY",
            "content": [],
        }
    ]
    response = client.post("/curriculum/load", json=payload)
    assert response.status_code == 422
    assert "content" in response.json()["detail"].lower()


def test_load_curriculum_blank_lecture_name():
    """Test lecture with empty/whitespace name is rejected."""
    payload = [
        {
            "week": 1,
            "day": 1,
            "lecture": "   ",
            "content": ["Topic A"],
        }
    ]
    response = client.post("/curriculum/load", json=payload)
    assert response.status_code == 422
    assert "lecture" in response.json()["detail"].lower()


def test_load_curriculum_duplicate_lecture_codes():
    """Test curriculum with duplicate lecture IDs is rejected."""
    payload = [
        {
            "week": 1,
            "day": 1,
            "lecture": "LEC-DUP",
            "content": ["Topic A"],
        },
        {
            "week": 1,
            "day": 2,
            "lecture": "LEC-DUP",
            "content": ["Topic B"],
        },
    ]
    response = client.post("/curriculum/load", json=payload)
    assert response.status_code == 422
    assert "duplicate" in response.json()["detail"].lower()


def test_upload_curriculum_file_valid():
    """Test uploading a valid JSON curriculum file via multipart/form-data."""
    valid_data = {
        "course_id": "UPLOAD-101",
        "course_name": "Uploaded Course",
        "lectures": [
            {
                "week": 1,
                "day": 1,
                "lecture": "UP-LEC-1",
                "content": ["Uploaded Topic 1"],
                "classwork": [],
                "homework": [],
            }
        ],
    }
    file_bytes = io.BytesIO(json.dumps(valid_data).encode("utf-8"))
    response = client.post(
        "/curriculum/upload",
        files={"file": ("curriculum.json", file_bytes, "application/json")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_upload_curriculum_file_invalid_extension():
    """Test uploading a non-json file is rejected with 400."""
    file_bytes = io.BytesIO(b"random content")
    response = client.post(
        "/curriculum/upload",
        files={"file": ("curriculum.txt", file_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert ".json" in response.json()["detail"]


def test_upload_curriculum_file_malformed_json():
    """Test uploading malformed JSON is rejected with 400."""
    file_bytes = io.BytesIO(b"{ invalid json syntax: ")
    response = client.post(
        "/curriculum/upload",
        files={"file": ("curriculum.json", file_bytes, "application/json")},
    )
    assert response.status_code == 400
    assert "syntax" in response.json()["detail"].lower()


def test_reset_curriculum():
    """Test POST /curriculum/reset restores the default dataset."""
    # First alter it
    client.post(
        "/curriculum/load",
        json=[
            {
                "week": 1,
                "day": 1,
                "lecture": "TEMP-LEC",
                "content": ["Temporary Topic"],
            }
        ],
    )
    # Verify altered
    res = client.get("/curriculum/lectures/TEMP-LEC")
    assert res.status_code == 200

    # Reset
    reset_res = client.post("/curriculum/reset")
    assert reset_res.status_code == 200

    # Verify temp lecture is gone and default LEC-1 exists
    res_gone = client.get("/curriculum/lectures/TEMP-LEC")
    assert res_gone.status_code == 404
    res_default = client.get("/curriculum/lectures/LEC-1")
    assert res_default.status_code == 200
