import os
import io
import wave
import struct
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status
from fastapi.responses import Response, HTMLResponse

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


@router.get(
    "/record",
    response_class=HTMLResponse,
    summary="In-Browser Microphone Dictation Test Page",
    description="Interactive web interface for testing voice dictation and Speech-to-Text directly in the browser."
)
async def mic_dictation_page():
    """Renders a modern, responsive web application for mic recording and instant transcription."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Course Progression Tracker - Lecture Dictation Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(22, 30, 49, 0.75);
      --border: rgba(255, 255, 255, 0.08);
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --danger: #ef4444;
      --danger-hover: #dc2626;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --accent-green: #10b981;
      --glass: backdrop-filter: blur(16px);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
    body {
      background: radial-gradient(circle at top, #1e1b4b 0%, #0b0f19 70%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .container {
      width: 100%;
      max-width: 680px;
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 36px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    header { text-align: center; margin-bottom: 28px; }
    header h1 { font-size: 26px; font-weight: 700; margin-bottom: 8px; background: linear-gradient(to right, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    header p { color: var(--text-muted); font-size: 14px; }
    
    .provider-selector {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-bottom: 24px;
    }
    .radio-pill {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 8px 16px;
      border-radius: 9999px;
      cursor: pointer;
      font-size: 13px;
      color: var(--text-muted);
      transition: all 0.2s;
    }
    .radio-pill.active {
      background: rgba(99, 102, 241, 0.2);
      border-color: var(--primary);
      color: #a5b4fc;
      font-weight: 600;
    }

    .record-box {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 0;
    }
    .mic-button {
      width: 90px;
      height: 90px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--primary), #4338ca);
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5);
      position: relative;
    }
    .mic-button:hover { transform: scale(1.05); box-shadow: 0 15px 30px -5px rgba(99, 102, 241, 0.7); }
    .mic-button.recording {
      background: linear-gradient(135deg, var(--danger), #b91c1c);
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
      70% { box-shadow: 0 0 0 24px rgba(239, 68, 68, 0); }
      100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .mic-icon { width: 36px; height: 36px; fill: white; }

    .timer {
      font-size: 28px;
      font-weight: 700;
      letter-spacing: 2px;
      margin-top: 18px;
      font-variant-numeric: tabular-nums;
      color: #e0e7ff;
    }
    .status-hint {
      margin-top: 8px;
      font-size: 13px;
      color: var(--text-muted);
    }

    .audio-player-container {
      margin-top: 16px;
      width: 100%;
      display: none;
    }
    audio { width: 100%; height: 38px; border-radius: 8px; }

    /* Results */
    .result-section {
      margin-top: 24px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
      display: none;
    }
    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .result-title { font-size: 14px; font-weight: 600; color: #c7d2fe; text-transform: uppercase; letter-spacing: 0.5px; }
    .copy-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .copy-btn:hover { background: rgba(255, 255, 255, 0.15); color: #fff; }
    
    .badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }
    .badge {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      color: #d1d5db;
    }
    .badge span { font-weight: 600; color: #a5b4fc; }

    .transcript-box {
      background: rgba(11, 15, 25, 0.6);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      font-size: 15px;
      line-height: 1.6;
      color: #f3f4f6;
      max-height: 220px;
      overflow-y: auto;
      white-space: pre-wrap;
    }

    .loader {
      display: none;
      align-items: center;
      gap: 10px;
      margin-top: 16px;
      color: #a5b4fc;
      font-size: 14px;
    }
    .spinner {
      width: 18px;
      height: 18px;
      border: 2px solid rgba(165, 180, 252, 0.2);
      border-top-color: #818cf8;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    .error-box {
      display: none;
      margin-top: 16px;
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
      padding: 12px 16px;
      border-radius: 10px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🎙️ Lecture Dictation Studio</h1>
      <p>Test Speech-to-Text with your live microphone</p>
    </header>

    <div class="provider-selector">
      <div class="radio-pill active" id="btn-assemblyai" onclick="setProvider('assemblyai')">
        ⚡ AssemblyAI (Real STT)
      </div>
      <div class="radio-pill" id="btn-mock" onclick="setProvider('mock')">
        🧪 Mock Provider (Simulated)
      </div>
    </div>

    <div class="record-box">
      <button class="mic-button" id="micBtn" onclick="toggleRecording()">
        <svg class="mic-icon" id="micIcon" viewBox="0 0 24 24">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
      </button>

      <div class="timer" id="timer">00:00</div>
      <div class="status-hint" id="statusHint">Click the microphone to start dictating</div>

      <div class="loader" id="loader">
        <div class="spinner"></div>
        <span id="loaderText">Processing audio with AssemblyAI...</span>
      </div>

      <div class="audio-player-container" id="playerContainer">
        <audio id="audioPlayer" controls></audio>
      </div>

      <div class="error-box" id="errorBox"></div>
    </div>

    <div class="result-section" id="resultSection">
      <div class="result-header">
        <div class="result-title">Transcribed Lecture Text</div>
        <button class="copy-btn" id="copyBtn" onclick="copyTranscript()">Copy</button>
      </div>

      <div class="badges" id="badges">
        <div class="badge">⏱️ Duration: <span id="badgeDuration">0s</span></div>
        <div class="badge">📝 Words: <span id="badgeWords">0</span></div>
        <div class="badge">⚙️ Provider: <span id="badgeProvider">assemblyai</span></div>
      </div>

      <div class="transcript-box" id="transcriptBox"></div>
    </div>
  </div>

  <script>
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;
    let timerInterval = null;
    let startTime = null;
    let selectedProvider = 'assemblyai';

    const micBtn = document.getElementById('micBtn');
    const timer = document.getElementById('timer');
    const statusHint = document.getElementById('statusHint');
    const loader = document.getElementById('loader');
    const loaderText = document.getElementById('loaderText');
    const errorBox = document.getElementById('errorBox');
    const resultSection = document.getElementById('resultSection');
    const transcriptBox = document.getElementById('transcriptBox');
    const playerContainer = document.getElementById('playerContainer');
    const audioPlayer = document.getElementById('audioPlayer');

    function setProvider(prov) {
      selectedProvider = prov;
      document.getElementById('btn-assemblyai').classList.toggle('active', prov === 'assemblyai');
      document.getElementById('btn-mock').classList.toggle('active', prov === 'mock');
    }

    function formatTime(ms) {
      const totalSec = Math.floor(ms / 1000);
      const mins = String(Math.floor(totalSec / 60)).padStart(2, '0');
      const secs = String(totalSec % 60).padStart(2, '0');
      return `${mins}:${secs}`;
    }

    async function toggleRecording() {
      if (isRecording) {
        stopRecording();
      } else {
        await startRecording();
      }
    }

    async function startRecording() {
      errorBox.style.display = 'none';
      resultSection.style.display = 'none';
      playerContainer.style.display = 'none';

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        let mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported('audio/webm')) {
          if (MediaRecorder.isTypeSupported('audio/mp4')) mimeType = 'audio/mp4';
          else if (MediaRecorder.isTypeSupported('audio/ogg')) mimeType = 'audio/ogg';
        }

        mediaRecorder = new MediaRecorder(stream, { mimeType });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
          const mime = mediaRecorder.mimeType || 'audio/webm';
          const audioBlob = new Blob(audioChunks, { type: mime });
          const audioUrl = URL.createObjectURL(audioBlob);
          audioPlayer.src = audioUrl;
          playerContainer.style.display = 'block';

          // Stop all stream tracks to release microphone
          stream.getTracks().forEach(track => track.stop());

          // Upload and transcribe
          uploadAudio(audioBlob, mime);
        };

        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add('recording');
        statusHint.textContent = 'Recording in progress... Click again to stop & transcribe';

        startTime = Date.now();
        timerInterval = setInterval(() => {
          timer.textContent = formatTime(Date.now() - startTime);
        }, 200);

      } catch (err) {
        showError('Microphone access denied or not available: ' + err.message);
      }
    }

    function stopRecording() {
      if (!mediaRecorder || !isRecording) return;
      isRecording = false;
      micBtn.classList.remove('recording');
      clearInterval(timerInterval);
      statusHint.textContent = 'Finalizing recording...';
      mediaRecorder.stop();
    }

    async function uploadAudio(audioBlob, mimeType) {
      loader.style.display = 'flex';
      loaderText.textContent = selectedProvider === 'assemblyai'
        ? 'Uploading to AssemblyAI & transcribing (may take 5-15s)...'
        : 'Generating simulated transcript...';
      statusHint.textContent = 'Processing transcription...';

      let ext = 'webm';
      if (mimeType.includes('mp4')) ext = 'm4a';
      else if (mimeType.includes('ogg')) ext = 'ogg';
      else if (mimeType.includes('wav')) ext = 'wav';

      const formData = new FormData();
      formData.append('file', audioBlob, `lecture_dictation.${ext}`);

      try {
        const response = await fetch(`/lecture/audio?provider=${selectedProvider}`, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Transcription failed');
        }

        displayResult(data);
      } catch (err) {
        showError(err.message);
      } finally {
        loader.style.display = 'none';
        statusHint.textContent = 'Ready to record again';
      }
    }

    function displayResult(data) {
      document.getElementById('badgeDuration').textContent = `${data.duration}s`;
      document.getElementById('badgeWords').textContent = data.words_count;
      document.getElementById('badgeProvider').textContent = data.provider;
      
      transcriptBox.textContent = data.transcript || '(No speech detected in recording)';
      resultSection.style.display = 'block';
    }

    function showError(msg) {
      errorBox.textContent = '⚠️ Error: ' + msg;
      errorBox.style.display = 'block';
    }

    function copyTranscript() {
      const text = transcriptBox.textContent;
      navigator.clipboard.writeText(text);
      const copyBtn = document.getElementById('copyBtn');
      copyBtn.textContent = 'Copied!';
      setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
    }
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
