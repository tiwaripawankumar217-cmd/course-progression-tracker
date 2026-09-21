import abc
import asyncio
import os
from pathlib import Path
from typing import Optional
import httpx
from pydantic import BaseModel

from backend.utils.config import get_assemblyai_api_key


class TranscriptionResult(BaseModel):
    """Normalized transcription output returned by any STT provider."""
    transcript: str
    duration: float
    words_count: int
    provider: str
    confidence: Optional[float] = None


class BaseTranscriptionService(abc.ABC):
    """Abstract base class for all Speech-to-Text providers."""

    @abc.abstractmethod
    async def transcribe(self, audio_file_path: Path) -> TranscriptionResult:
        """Transcribe an audio file and return normalized transcript results."""
        pass

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Verify API connectivity and key validity."""
        pass


class AssemblyAITranscriptionService(BaseTranscriptionService):
    """
    Speech-to-Text implementation using AssemblyAI REST API.
    Uploads audio, initiates transcription, and polls until complete.
    """

    BASE_URL = "https://api.assemblyai.com/v2"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key if api_key is not None else get_assemblyai_api_key()

    def _get_headers(self) -> dict:
        key = self._api_key if self._api_key is not None else get_assemblyai_api_key()
        if not key:
            raise ValueError(
                "AssemblyAI API key is not configured. "
                "Please add ASSEMBLYAI_API_KEY to the backend .env file."
            )
        return {
            "authorization": key,
            "content-type": "application/json",
        }

    async def health_check(self) -> bool:
        """Verify AssemblyAI API token by querying account or transcript list."""
        try:
            headers = self._get_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Query transcript list with limit 1 as a lightweight credential verification
                res = await client.get(
                    f"{self.BASE_URL}/transcript?limit=1",
                    headers={"authorization": headers["authorization"]}
                )
                return res.status_code == 200
        except Exception:
            return False

    async def _upload_audio(self, client: httpx.AsyncClient, audio_file_path: Path) -> str:
        """Streams audio file to AssemblyAI upload endpoint and returns upload_url."""
        headers = {"authorization": self._get_headers()["authorization"]}
        
        with open(audio_file_path, "rb") as f:
            file_bytes = f.read()

        response = await client.post(
            f"{self.BASE_URL}/upload",
            headers=headers,
            content=file_bytes,
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to upload audio to AssemblyAI (status {response.status_code}): {response.text}"
            )

        data = response.json()
        upload_url = data.get("upload_url")
        if not upload_url:
            raise ValueError("AssemblyAI did not return a valid upload_url.")
        return upload_url

    async def transcribe(self, audio_file_path: Path) -> TranscriptionResult:
        """
        Uploads audio to AssemblyAI and waits for transcription completion.
        """
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=15.0)) as client:
            # 1. Upload audio
            upload_url = await self._upload_audio(client, audio_file_path)

            # 2. Submit transcription job
            job_res = await client.post(
                f"{self.BASE_URL}/transcript",
                headers=headers,
                json={"audio_url": upload_url}
            )

            if job_res.status_code not in (200, 201):
                raise ValueError(
                    f"AssemblyAI transcription request failed (status {job_res.status_code}): {job_res.text}"
                )

            job_data = job_res.json()
            transcript_id = job_data.get("id")
            if not transcript_id:
                raise ValueError("No transcript ID received from AssemblyAI.")

            # 3. Poll for completion
            polling_url = f"{self.BASE_URL}/transcript/{transcript_id}"
            max_attempts = 120  # up to ~4 minutes polling
            delay = 2.5

            for _ in range(max_attempts):
                await asyncio.sleep(delay)
                poll_res = await client.get(polling_url, headers={"authorization": headers["authorization"]})
                
                if poll_res.status_code != 200:
                    continue

                poll_data = poll_res.json()
                current_status = poll_data.get("status")

                if current_status == "completed":
                    text = poll_data.get("text") or ""
                    audio_duration = float(poll_data.get("audio_duration") or 0.0)
                    confidence = poll_data.get("confidence")
                    words_count = len(text.split()) if text else 0

                    return TranscriptionResult(
                        transcript=text,
                        duration=round(audio_duration, 2),
                        words_count=words_count,
                        provider="assemblyai",
                        confidence=confidence,
                    )

                if current_status == "error":
                    error_msg = poll_data.get("error", "Unknown AssemblyAI error")
                    raise ValueError(f"AssemblyAI transcription failed: {error_msg}")

            raise TimeoutError("AssemblyAI transcription timed out waiting for audio processing.")


class MockTranscriptionService(BaseTranscriptionService):
    """
    Mock speech-to-text service for local testing, offline demo, and unit tests.
    Course-agnostic: returns a structured simulated classroom lecture transcript.
    """

    SAMPLE_TRANSCRIPT = (
        "Good morning everyone, welcome to today's lecture. "
        "Today we are covering Topic A: Core Principles and Foundations, "
        "and Topic B: Conceptual Framework and Terminology. "
        "Please open your textbooks to review Activity 1: Guided Concept Review. "
        "For homework, please complete Homework 1: Formative Assessment and Practice Exercises "
        "by next lecture. We will proceed with Topic C in our upcoming class."
    )

    def __init__(self, custom_transcript: Optional[str] = None, duration: float = 125.0):
        self.custom_transcript = custom_transcript or self.SAMPLE_TRANSCRIPT
        self.duration = duration

    async def health_check(self) -> bool:
        return True

    async def transcribe(self, audio_file_path: Path) -> TranscriptionResult:
        # Simulate quick processing
        await asyncio.sleep(0.05)
        text = self.custom_transcript
        return TranscriptionResult(
            transcript=text,
            duration=self.duration,
            words_count=len(text.split()),
            provider="mock",
            confidence=0.98,
        )


def get_transcription_service(provider_override: Optional[str] = None) -> BaseTranscriptionService:
    """
    Factory function to obtain the appropriate transcription service.
    Defaults to AssemblyAI if configured, otherwise falls back safely to Mock.
    """
    provider = provider_override or os.getenv("STT_PROVIDER", "").strip().lower()

    if provider == "mock":
        return MockTranscriptionService()

    if provider == "assemblyai":
        return AssemblyAITranscriptionService()

    # Automatic selection based on key availability
    key = get_assemblyai_api_key()
    if key:
        return AssemblyAITranscriptionService()
    return MockTranscriptionService()
