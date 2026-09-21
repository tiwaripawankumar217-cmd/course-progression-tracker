from typing import Optional
from pydantic import BaseModel, Field


class AudioTranscriptionResponse(BaseModel):
    """
    Standard response schema for lecture audio transcription.
    Course-agnostic and provider-agnostic.
    """
    transcript: str = Field(..., description="Transcribed lecture text")
    duration: float = Field(..., description="Audio duration in seconds")
    words_count: int = Field(..., description="Total word count in the transcript")
    provider: str = Field(..., description="Transcription provider used (e.g., assemblyai, mock)")
    file_name: str = Field(..., description="Original name of the uploaded audio file")
    confidence: Optional[float] = Field(default=None, description="Average confidence score if provided")
