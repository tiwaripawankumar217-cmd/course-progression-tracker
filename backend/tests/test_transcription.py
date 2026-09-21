import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.transcription import (
    MockTranscriptionService,
    AssemblyAITranscriptionService,
    get_transcription_service,
)

client = TestClient(app)


def test_get_sample_audio():
    """Verify GET /lecture/sample-audio generates a valid WAV file."""
    response = client.get("/lecture/sample-audio")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 100


def test_get_mic_dictation_page():
    """Verify GET /lecture/record serves the in-browser dictation UI."""
    response = client.get("/lecture/record")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Lecture Dictation Studio" in response.text


def test_upload_audio_mock_provider_success():
    """Test audio upload using mock provider returns valid transcript response."""
    # Obtain sample WAV audio
    sample_res = client.get("/lecture/sample-audio")
    audio_bytes = sample_res.content

    response = client.post(
        "/lecture/audio?provider=mock",
        files={"file": ("lecture_sample.wav", io.BytesIO(audio_bytes), "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert len(data["transcript"]) > 0
    assert data["duration"] > 0
    assert data["words_count"] > 0
    assert data["provider"] == "mock"
    assert data["file_name"] == "lecture_sample.wav"


def test_upload_audio_reject_non_audio_extension():
    """Test uploading unsupported file format (.txt) is rejected with 400."""
    fake_file = io.BytesIO(b"Hello world transcript")
    response = client.post(
        "/lecture/audio?provider=mock",
        files={"file": ("lecture_notes.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported audio file extension" in response.json()["detail"]


def test_upload_audio_reject_empty_file():
    """Test uploading 0-byte audio file is rejected with 400."""
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/lecture/audio?provider=mock",
        files={"file": ("empty.mp3", empty_file, "audio/mpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_mock_transcription_service_direct():
    """Unit test for MockTranscriptionService directly."""
    import asyncio
    service = MockTranscriptionService(custom_transcript="Test transcript", duration=45.0)
    health = asyncio.run(service.health_check())
    assert health is True

    result = asyncio.run(service.transcribe(Path("fake_path.wav")))
    assert result.transcript == "Test transcript"
    assert result.duration == 45.0
    assert result.words_count == 2
    assert result.provider == "mock"


def test_assemblyai_service_missing_key_error():
    """Unit test: AssemblyAI service raises clear error if API key is missing."""
    service = AssemblyAITranscriptionService(api_key="")
    with pytest.raises(ValueError) as excinfo:
        service._get_headers()
    assert "AssemblyAI API key is not configured" in str(excinfo.value)


def test_get_transcription_service_factory():
    """Verify factory returns appropriate service instance."""
    mock_svc = get_transcription_service(provider_override="mock")
    assert isinstance(mock_svc, MockTranscriptionService)

    assembly_svc = get_transcription_service(provider_override="assemblyai")
    assert isinstance(assembly_svc, AssemblyAITranscriptionService)
