import os
import io
import wave
import struct
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status
from fastapi.responses import Response

from backend.schemas.lecture import AudioTranscriptionResponse
from backend.services.transcription import get_transcription_service

router = APIRouter(prefix="/lecture", tags=["Lecture Audio"])

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".ogg", ".flac", ".webm", ".aac"}
MAX_AUDIO_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


@router.post(
    "/audio",
    response_model=AudioTranscriptionResponse,
    summary="Upload and transcribe lecture audio",
    description=(
        "Accepts a recorded classroom lecture audio file (.mp3, .wav, .m4a, etc.), "
        "streams it to the transcription service, and returns the transcript and duration metrics. "
        "Temporary audio files are immediately deleted upon completion to ensure privacy."
    ),
)
async def upload_lecture_audio(
    file: UploadFile = File(..., description="Lecture audio recording"),
    provider: Optional[str] = Query(
        default=None,
        description="Optional provider override ('assemblyai' or 'mock')"
    ),
):
    """
    Ingests lecture audio, validates constraints, and executes Speech-to-Text transcription.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename."
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported audio file extension '{ext}'. "
                f"Allowed formats: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
            )
        )

    # Temporary storage with immediate deletion guarantee (Rule 7: Privacy)
    temp_dir = tempfile.gettempdir()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=temp_dir) as temp_file:
        temp_path = Path(temp_file.name)

    total_bytes = 0
    try:
        # Write chunks to disk and guard file size limits
        CHUNK_SIZE = 64 * 1024
        with open(temp_path, "wb") as f_out:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_AUDIO_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Audio file exceeds maximum allowed size of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB."
                    )
                f_out.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio file is empty (0 bytes)."
            )

        # Transcribe using selected or configured provider
        service = get_transcription_service(provider)
        result = await service.transcribe(temp_path)

        return AudioTranscriptionResponse(
            transcript=result.transcript,
            duration=result.duration,
            words_count=result.words_count,
            provider=result.provider,
            file_name=file.filename,
            confidence=result.confidence,
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc))
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription processing error: {str(exc)}"
        )
    finally:
        # Always remove temporary audio file
        if temp_path.exists():
            try:
                os.unlink(temp_path)
            except OSError:
                pass


@router.get(
    "/sample-audio",
    summary="Generate sample test audio (WAV)",
    description="Generates and returns a minimal valid 1-second sine wave WAV file for testing uploads."
)
async def get_sample_audio():
    """Generates a minimal valid 1-second 440Hz PCM mono audio file in memory."""
    sample_rate = 8000
    num_samples = sample_rate * 1  # 1 second
    
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Generate simple silence / tone data
        frames = bytearray()
        for i in range(num_samples):
            # Gentle tone
            val = int(3000 * (i % 20) / 20)
            frames.extend(struct.pack("<h", val))
        wav_file.writeframes(frames)

    buffer.seek(0)
    return Response(
        content=buffer.read(),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=sample_lecture.wav"}
    )
