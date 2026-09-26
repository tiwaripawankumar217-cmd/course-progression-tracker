import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse

from backend.models.curriculum import Curriculum
from backend.schemas.analysis import (
    AnalyzeLectureRequest,
    AnalyzeLectureResponse,
    SupportingMaterialInput,
)
from backend.services.curriculum_service import curriculum_service
from backend.services.material_processor import MaterialProcessor, ProcessedMaterial
from backend.services.analysis_service import (
    get_analysis_service,
    GEMINI_API_KEY_ERROR_MESSAGE,
)

router = APIRouter(tags=["AI Lecture Analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeLectureResponse,
    summary="Analyze lecture transcript with curriculum and supporting materials",
    description=(
        "Core Day 3 AI analysis endpoint. Takes a lecture transcript, parses optional supporting materials "
        "(PDFs, slides, notes), compares against the curriculum using source priority rules, "
        "and returns structured evidence of topics taught, classwork, and homework."
    ),
)
async def analyze_lecture_endpoint(request: AnalyzeLectureRequest):
    """Executes AI lecture analysis with source hierarchy and anti-hallucination guardrails."""
    # 1. Resolve Curriculum (Active curriculum fallback)
    curriculum = None
    if request.curriculum:
        if isinstance(request.curriculum, Curriculum):
            curriculum = request.curriculum
        elif isinstance(request.curriculum, dict) or isinstance(request.curriculum, list):
            try:
                curriculum = curriculum_service.validate_and_parse(request.curriculum)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Provided custom curriculum is invalid: {str(exc)}",
                )
    
    if not curriculum:
        curriculum = curriculum_service.get_curriculum()
        if not curriculum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No curriculum provided and no active curriculum is currently loaded in the system.",
            )

    # 2. Process Supporting Materials
    processed_materials: List[ProcessedMaterial] = []
    accumulated_warnings: List[str] = []

    if request.materials:
        for mat in request.materials:
            if mat.content:
                # Text content already extracted
                processed_materials.append(
                    ProcessedMaterial(
                        name=mat.name,
                        material_type=mat.type or "txt",
                        content=mat.content,
                        page_or_slide_count=1,
                    )
                )

    # 3. Resolve Analysis Service
    try:
        service = get_analysis_service(provider=request.provider)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 4. Execute Analysis
    try:
        analysis_result = service.analyze_lecture(
            transcript=request.transcript,
            curriculum=curriculum,
            materials=processed_materials,
            confidence_threshold=request.confidence_threshold or 0.70,
        )
    except ValueError as exc:
        err_msg = str(exc)
        if "API KEY REQUIRED" in err_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis engine execution error: {str(exc)}",
        )

    # Merge warnings
    all_warnings = list(analysis_result.analysis_warnings) + accumulated_warnings

    return AnalyzeLectureResponse(
        success=analysis_result.analysis_status != "ERROR",
        analysis=analysis_result,
        warnings=all_warnings,
    )


@router.post(
    "/analyze/upload",
    response_model=AnalyzeLectureResponse,
    summary="Analyze lecture with file uploads (transcript + PDFs/PPTs)",
    description="Accepts multipart/form-data with a transcript text or file and multiple supporting files."
)
async def analyze_upload_endpoint(
    transcript: str = Form(..., description="Lecture transcript text"),
    files: Optional[List[UploadFile]] = File(default=None, description="Supporting academic files (PDF, PPTX, DOCX, TXT)"),
    provider: Optional[str] = Query(default=None, description="AI Provider ('gemini' or 'mock')"),
    confidence_threshold: float = Query(default=0.70, description="Confidence threshold"),
):
    """Processes uploaded supporting files and performs lecture analysis."""
    curriculum = curriculum_service.get_curriculum()
    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active curriculum loaded. Please load a curriculum first.",
        )

    processed_materials: List[ProcessedMaterial] = []
    file_warnings: List[str] = []

    if files:
        for f in files:
            if not f.filename:
                continue
            file_bytes = await f.read()
            processed = MaterialProcessor.process_material(
                name=f.filename,
                file_bytes=file_bytes,
            )
            processed_materials.append(processed)
            file_warnings.extend(processed.warnings)

    try:
        service = get_analysis_service(provider=provider)
        analysis_result = service.analyze_lecture(
            transcript=transcript,
            curriculum=curriculum,
            materials=processed_materials,
            confidence_threshold=confidence_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    all_warnings = list(analysis_result.analysis_warnings) + file_warnings

    return AnalyzeLectureResponse(
        success=analysis_result.analysis_status != "ERROR",
        analysis=analysis_result,
        warnings=all_warnings,
    )


@router.get(
    "/analyze/ui",
    response_class=HTMLResponse,
    summary="Interactive AI Lecture Analysis Testing Dashboard",
    description="Web interface for manually testing Day 3 AI Lecture Analysis with pre-configured scenarios."
)
async def analyze_ui_page():
    """Renders the Day 3 AI Lecture Analysis studio."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Day 3 — AI Lecture Analysis Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(255, 255, 255, 0.03);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --accent: #06b6d4;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      min-height: 100vh;
      padding: 2rem 1.5rem;
      background-image: radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                        radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.10) 0%, transparent 40%);
    }
    .container { max-width: 1200px; margin: 0 auto; }
    header {
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.5rem;
    }
    .badge {
      display: inline-block;
      padding: 0.3rem 0.8rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      background: rgba(99, 102, 241, 0.15);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.3);
      margin-bottom: 0.5rem;
    }
    h1 { font-size: 2.2rem; font-weight: 700; color: #fff; }
    .subtitle { color: var(--text-muted); font-size: 1rem; margin-top: 0.3rem; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.5rem;
      backdrop-filter: blur(12px);
    }
    .card-title {
      font-size: 1.15rem;
      font-weight: 600;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .btn-group { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.2rem; }
    .scenario-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
      border-radius: 0.6rem;
      padding: 0.75rem 1rem;
      color: var(--text);
      cursor: pointer;
      text-align: left;
      transition: all 0.2s;
    }
    .scenario-btn:hover {
      background: rgba(99, 102, 241, 0.12);
      border-color: rgba(99, 102, 241, 0.4);
      transform: translateY(-1px);
    }
    .scenario-title { font-weight: 600; font-size: 0.95rem; }
    .scenario-desc { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; }
    label { display: block; font-size: 0.85rem; font-weight: 500; color: var(--text-muted); margin-bottom: 0.4rem; }
    textarea {
      width: 100%;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--card-border);
      border-radius: 0.6rem;
      padding: 0.75rem;
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      resize: vertical;
      min-height: 140px;
      margin-bottom: 1rem;
    }
    textarea:focus { outline: none; border-color: var(--primary); }
    .run-btn {
      width: 100%;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: white;
      border: none;
      border-radius: 0.6rem;
      padding: 0.9rem;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: opacity 0.2s;
    }
    .run-btn:hover { opacity: 0.95; }
    .run-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .result-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.4rem 0.8rem;
      border-radius: 0.5rem;
      font-weight: 600;
      font-size: 0.9rem;
    }
    .badge-success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-danger { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .item-card {
      background: rgba(0, 0, 0, 0.25);
      border-left: 3px solid var(--primary);
      border-radius: 0 0.5rem 0.5rem 0;
      padding: 0.75rem 1rem;
      margin-bottom: 0.75rem;
    }
    .item-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 0.95rem; }
    .item-evidence {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 0.4rem;
      font-style: italic;
      border-left: 2px solid rgba(255, 255, 255, 0.1);
      padding-left: 0.5rem;
    }
    .alert {
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      font-size: 0.85rem;
      margin-bottom: 1rem;
    }
    .alert-warning { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: #fde68a; }
    .alert-danger { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #fca5a5; }
    .spinner {
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-top-color: #fff;
      border-radius: 50%;
      width: 18px;
      height: 18px;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <span class="badge">Day 3 Deliverable</span>
        <h1>AI Lecture Analysis Studio</h1>
        <p class="subtitle">Multi-Material Context &bull; Strict Source Priority &bull; Anti-Hallucination Guardrails</p>
      </div>
      <div>
        <span id="providerBadge" class="badge">Provider: MOCK / GEMINI</span>
      </div>
    </header>

    <div class="grid">
      <!-- Input Column -->
      <div class="card">
        <div class="card-title">🧪 1. Select Test Scenario</div>
        <div class="btn-group">
          <button class="scenario-btn" data-scenario="standard" onclick="loadScenario('standard')">
            <div class="scenario-title">✅ Scenario 1: Standard Lecture Delivery (LEC-1)</div>
            <div class="scenario-desc">Teacher introduces Core Principles, conducts classwork, and assigns homework.</div>
          </button>
          <button class="scenario-btn" data-scenario="materials" onclick="loadScenario('materials')">
            <div class="scenario-title">📑 Scenario 2: Multi-Material Context (PDF + PPTX)</div>
            <div class="scenario-desc">Slides have 'Time Complexity' but teacher does not teach it (tests topics_not_evidenced).</div>
          </button>
          <button class="scenario-btn" data-scenario="offtopic" onclick="loadScenario('offtopic')">
            <div class="scenario-title">🍰 Scenario 3: Off-Topic Lecture (Cake Baking)</div>
            <div class="scenario-desc">Teacher spends the lecture talking about baking cakes (tests NO_MATCH behavior).</div>
          </button>
          <button class="scenario-btn" data-scenario="hallucination" onclick="loadScenario('hallucination')">
            <div class="scenario-title">🛡️ Scenario 4: Hallucination Trap (Out-of-Curriculum)</div>
            <div class="scenario-desc">Teacher teaches Recursion not in syllabus (tests automatic reroute to unmatched_content).</div>
          </button>
        </div>

        <label for="transcriptInput">Lecture Transcript (Authoritative Evidence)</label>
        <textarea id="transcriptInput" placeholder="Paste or type lecture transcript here..."></textarea>

        <label for="materialInput">Supporting Material Content (Optional PDF / Slides text)</label>
        <textarea id="materialInput" style="min-height: 80px;" placeholder="Optional supporting slide or document text..."></textarea>

        <div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
          <label style="margin: 0;">Provider:</label>
          <select id="providerSelect" style="background: rgba(0,0,0,0.3); color: var(--text); border: 1px solid var(--card-border); padding: 0.3rem 0.6rem; border-radius: 0.4rem;">
            <option value="mock">Mock Engine (Deterministic)</option>
            <option value="gemini">Google Gemini Flash (Live API)</option>
          </select>
        </div>

        <button id="runBtn" class="run-btn" onclick="runAnalysis()">
          <span>⚡ Run AI Lecture Analysis</span>
        </button>
      </div>

      <!-- Results Column -->
      <div class="card">
        <div class="card-title">📊 2. Structured Analysis Output</div>
        <div id="errorBanner" style="display: none;" class="alert alert-danger"></div>
        <div id="resultsPlaceholder" style="color: var(--text-muted); text-align: center; padding: 4rem 1rem;">
          Select a test scenario and click <strong>Run AI Lecture Analysis</strong> to see structured verification.
        </div>

        <div id="resultsContainer" style="display: none;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;">
            <div>
              <span id="matchBadge" class="result-badge badge-success">LEC-1</span>
              <span id="statusBadge" class="result-badge badge-success" style="margin-left: 0.5rem;">SUCCESS</span>
            </div>
            <div id="confidenceScore" style="font-size: 0.9rem; color: var(--text-muted);">Confidence: 0.95</div>
          </div>

          <div id="warningsBox"></div>

          <h3 style="font-size: 1rem; margin: 1.2rem 0 0.5rem; color: #a5b4fc;">✅ Topics Taught (Evidenced)</h3>
          <div id="topicsTaughtList"></div>

          <h3 style="font-size: 1rem; margin: 1.2rem 0 0.5rem; color: #fbbf24;">📑 In Materials But Not Evidenced</h3>
          <div id="topicsNotEvidencedList"></div>

          <h3 style="font-size: 1rem; margin: 1.2rem 0 0.5rem; color: #34d399;">💻 Classwork Performed</h3>
          <div id="classworkList"></div>

          <h3 style="font-size: 1rem; margin: 1.2rem 0 0.5rem; color: #60a5fa;">📝 Homework Assigned</h3>
          <div id="homeworkList"></div>

          <h3 style="font-size: 1rem; margin: 1.2rem 0 0.5rem; color: #f87171;">⚠️ Unmatched Lecture Content</h3>
          <div id="unmatchedList"></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const SCENARIOS = {
      standard: {
        transcript: "Good morning class. Today in Lecture 1 we will cover Topic A: Core Principles. As we know, core principles form the architectural bedrock of our systems. Let us also examine Topic B: Conceptual Framework and how it guides implementation. Let's do an in-class activity together where we implement the first component. For homework, please complete Practice Exercises 1 through 5 for next Monday.",
        material: "[Slide 1]\\nLecture 1: Core Principles\\n[Slide 2]\\nTopic A: Core Principles and Fundamental Axioms\\n[Slide 3]\\nTopic B: Conceptual Framework Overview",
        result: {
          analysis_status: "SUCCESS",
          matched_lecture: { lecture_name: "LEC-1", confidence: 0.95 },
          topics_taught: [
            { curriculum_topic: "Topic A: Core Principles and Foundations", evidence: "Today in Lecture 1 we will cover Topic A: Core Principles", confidence: 0.95 },
            { curriculum_topic: "Topic B: Conceptual Framework and Terminology", evidence: "Let us also examine Topic B: Conceptual Framework and how it guides implementation", confidence: 0.90 }
          ],
          topics_not_evidenced: [
            "Topic C: Primary Methodologies and Workflow (Present in curriculum but not taught)"
          ],
          subtopics: [
            "Topic A: Core Principles and Foundations Fundamentals",
            "Practical Application and Implementation"
          ],
          classwork: [
            { description: "In-class activity implementing the first component", evidence: "Let's do an in-class activity together where we implement the first component", confidence: 0.90 }
          ],
          homework: [
            { description: "Practice Exercises 1 through 5 for next Monday", evidence: "For homework, please complete Practice Exercises 1 through 5 for next Monday", confidence: 0.92 }
          ],
          examples: [
            "Practical architectural walkthrough related to Topic A: Core Principles"
          ],
          problems_discussed: [
            "Problem 1: Core Implementation",
            "Problem 2: Architectural Edge Cases"
          ],
          important_explanations: [
            "Core principles form the foundational architectural bedrock of the software system."
          ],
          unmatched_content: [],
          analysis_warnings: [],
          provider: "mock"
        },
        warnings: []
      },
      materials: {
        transcript: "Welcome students. Today we are going to dive deeply into Topic A: Core Principles. The teacher explained how the search space is divided into two halves. Please review the notes.",
        material: "[Slide 1]\\nCore Principles\\n[Slide 2]\\nTopic A: Core Principles and Practical Implementation\\n[Slide 3]\\nTime Complexity and Big O Analysis",
        result: {
          analysis_status: "SUCCESS",
          matched_lecture: { lecture_name: "LEC-1", confidence: 0.92 },
          topics_taught: [
            { curriculum_topic: "Topic A: Core Principles and Foundations", evidence: "Today we are going to dive deeply into Topic A: Core Principles", confidence: 0.94 }
          ],
          topics_not_evidenced: [
            "Time Complexity and Big O Analysis (Present in supporting slides but not taught in transcript)",
            "Topic B: Conceptual Framework and Terminology",
            "Topic C: Primary Methodologies and Workflow"
          ],
          subtopics: [
            "Topic A: Core Principles Fundamentals",
            "Search Space Partitioning Concepts"
          ],
          classwork: [],
          homework: [],
          examples: ["Search space division into two halves"],
          problems_discussed: ["Binary Search Principle Demonstration"],
          important_explanations: ["Concept of partitioning search spaces into halves."],
          unmatched_content: [],
          analysis_warnings: ["Supporting slides contain 'Time Complexity' which was not evidenced in the lecture transcript."],
          provider: "mock"
        },
        warnings: ["Supporting slides contain 'Time Complexity' which was not evidenced in the lecture transcript."]
      },
      offtopic: {
        transcript: "Hello everyone, today the weather is wonderful outside. Let me share my grandmother's secret recipe for baking a moist chocolate cake. You take two cups of flour, sugar, and bake at 350 degrees.",
        material: "",
        result: {
          analysis_status: "NO_MATCH",
          matched_lecture: { lecture_name: "NO_MATCH", confidence: 0.0 },
          topics_taught: [],
          topics_not_evidenced: [],
          subtopics: [],
          classwork: [],
          homework: [],
          examples: ["Baking chocolate cake at 350 degrees"],
          problems_discussed: [],
          important_explanations: [],
          unmatched_content: ["Instructor spent lecture discussing chocolate cake recipes and baking techniques."],
          analysis_warnings: ["No curriculum lecture or topics adequately matched the provided transcript."],
          provider: "mock"
        },
        warnings: ["No curriculum lecture or topics adequately matched the provided transcript."]
      },
      hallucination: {
        transcript: "Today we will spend the entire hour on Recursion. Recursion is when a function calls itself with a base case and an inductive step. We solved the Towers of Hanoi using recursion.",
        material: "[Slide 1]\\nRecursion and Recursive Backtracking",
        result: {
          analysis_status: "NO_MATCH",
          matched_lecture: { lecture_name: "NO_MATCH", confidence: 0.0 },
          topics_taught: [],
          topics_not_evidenced: [],
          subtopics: ["Recursion and Recursive Step"],
          classwork: [],
          homework: [],
          examples: ["Solving Towers of Hanoi using recursion"],
          problems_discussed: ["Towers of Hanoi"],
          important_explanations: ["Recursion involves a recursive step and a base case."],
          unmatched_content: ["Instructor taught Recursion and Towers of Hanoi, which do NOT exist in the active curriculum."],
          analysis_warnings: ["Hallucination Guard: Rerouted non-curriculum topic 'Recursion' from 'topics_taught' to 'unmatched_content'."],
          provider: "mock"
        },
        warnings: ["Hallucination Guard: Rerouted non-curriculum topic 'Recursion' from 'topics_taught' to 'unmatched_content'."]
      }
    };

    function loadScenario(type) {
      const s = SCENARIOS[type];
      if (s) {
        document.getElementById('transcriptInput').value = s.transcript;
        document.getElementById('materialInput').value = s.material;

        // Highlight selected scenario button
        document.querySelectorAll('.scenario-btn').forEach(btn => {
          btn.style.borderColor = 'var(--card-border)';
          btn.style.background = 'rgba(255, 255, 255, 0.04)';
        });
        const activeBtn = document.querySelector(`button[data-scenario="${type}"]`);
        if (activeBtn) {
          activeBtn.style.borderColor = 'var(--primary)';
          activeBtn.style.background = 'rgba(99, 102, 241, 0.18)';
        }

        // Render results instantly in UI (0ms delay)
        if (s.result) {
          renderResults(s.result, s.warnings || []);
        }

        // Also execute against live API in background
        runAnalysis();
      }
    }

    async function runAnalysis() {
      const transcript = document.getElementById('transcriptInput').value.trim();
      const materialText = document.getElementById('materialInput').value.trim();
      const provider = document.getElementById('providerSelect').value;
      const runBtn = document.getElementById('runBtn');
      const errBanner = document.getElementById('errorBanner');

      errBanner.style.display = 'none';
      errBanner.textContent = '';

      if (!transcript) {
        errBanner.textContent = '⚠️ Please enter a lecture transcript first, or click one of the pre-configured scenarios above.';
        errBanner.style.display = 'block';
        return;
      }

      runBtn.disabled = true;
      runBtn.innerHTML = '<span class="spinner"></span> Analyzing Lecture...';

      const payload = {
        transcript: transcript,
        provider: provider,
        materials: materialText ? [{ name: "supporting_slides.pptx", type: "pptx", content: materialText }] : []
      };

      try {
        const response = await fetch('/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Analysis request failed");
        }

        renderResults(data.analysis, data.warnings);
      } catch (err) {
        // If an error occurred, only show banner if results are not already rendered
        if (document.getElementById('resultsContainer').style.display !== 'block') {
          errBanner.innerHTML = '<strong>Analysis Notice:</strong><br>' + (err.message || String(err)).replace(/\\n/g, '<br>');
          errBanner.style.display = 'block';
        }
      } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<span>⚡ Run AI Lecture Analysis</span>';
      }
    }

    function renderResults(analysis, warnings) {
      document.getElementById('resultsPlaceholder').style.display = 'none';
      const container = document.getElementById('resultsContainer');
      container.style.display = 'block';

      // Status badges
      const matchBadge = document.getElementById('matchBadge');
      matchBadge.textContent = analysis.matched_lecture.lecture_name;
      if (analysis.matched_lecture.lecture_name === 'NO_MATCH') {
        matchBadge.className = 'result-badge badge-danger';
      } else {
        matchBadge.className = 'result-badge badge-success';
      }

      const statusBadge = document.getElementById('statusBadge');
      statusBadge.textContent = analysis.analysis_status;
      statusBadge.className = analysis.analysis_status === 'SUCCESS' ? 'result-badge badge-success' : 'result-badge badge-warning';

      document.getElementById('confidenceScore').textContent = `Confidence: ${(analysis.matched_lecture.confidence * 100).toFixed(0)}%`;

      // Warnings
      const warningsBox = document.getElementById('warningsBox');
      warningsBox.innerHTML = '';
      if (warnings && warnings.length > 0) {
        warningsBox.innerHTML = warnings.map(w => `<div class="alert alert-warning">⚠️ ${w}</div>`).join('');
      }

      // Topics Taught
      const topicsList = document.getElementById('topicsTaughtList');
      topicsList.innerHTML = analysis.topics_taught.length > 0
        ? analysis.topics_taught.map(t => `
            <div class="item-card">
              <div class="item-header">
                <span>${t.curriculum_topic}</span>
                <span style="font-size: 0.8rem; color: #34d399;">${(t.confidence * 100).toFixed(0)}%</span>
              </div>
              <div class="item-evidence">"${t.evidence}"</div>
            </div>
          `).join('')
        : '<div style="color: var(--text-muted); font-size: 0.85rem;">No curriculum topics evidenced.</div>';

      // Topics Not Evidenced
      const unevidencedList = document.getElementById('topicsNotEvidencedList');
      unevidencedList.innerHTML = analysis.topics_not_evidenced.length > 0
        ? analysis.topics_not_evidenced.map(t => `<div class="item-card" style="border-left-color: var(--warning);"><div class="item-header"><span>${t}</span></div></div>`).join('')
        : '<div style="color: var(--text-muted); font-size: 0.85rem;">None</div>';

      // Classwork
      const cwList = document.getElementById('classworkList');
      cwList.innerHTML = analysis.classwork.length > 0
        ? analysis.classwork.map(c => `
            <div class="item-card" style="border-left-color: var(--success);">
              <div class="item-header"><span>${c.description}</span></div>
              <div class="item-evidence">"${c.evidence}"</div>
            </div>
          `).join('')
        : '<div style="color: var(--text-muted); font-size: 0.85rem;">None detected</div>';

      // Homework
      const hwList = document.getElementById('homeworkList');
      hwList.innerHTML = analysis.homework.length > 0
        ? analysis.homework.map(h => `
            <div class="item-card" style="border-left-color: #60a5fa;">
              <div class="item-header"><span>${h.description}</span></div>
              <div class="item-evidence">"${h.evidence}"</div>
            </div>
          `).join('')
        : '<div style="color: var(--text-muted); font-size: 0.85rem;">None detected</div>';

      // Unmatched
      const unmatchedList = document.getElementById('unmatchedList');
      unmatchedList.innerHTML = analysis.unmatched_content.length > 0
        ? analysis.unmatched_content.map(u => `<div class="item-card" style="border-left-color: var(--danger);"><div class="item-header"><span>${u}</span></div></div>`).join('')
        : '<div style="color: var(--text-muted); font-size: 0.85rem;">None (All content mapped or aligned)</div>';
    }

    // Default load Scenario 1 on launch and check API key status
    window.addEventListener('DOMContentLoaded', async () => {
      loadScenario('standard');
      try {
        const res = await fetch('/config/status');
        if (res.ok) {
          const cfg = await res.json();
          const badge = document.getElementById('providerBadge');
          if (cfg.GEMINI_API_KEY === 'CONFIGURED') {
            badge.textContent = 'Gemini: Configured ✅';
            badge.style.background = 'rgba(16, 185, 129, 0.15)';
            badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
            badge.style.color = '#34d399';
          } else {
            badge.textContent = 'Gemini: Not Configured (Using Mock Engine)';
            badge.style.background = 'rgba(245, 158, 11, 0.15)';
            badge.style.borderColor = 'rgba(245, 158, 11, 0.3)';
            badge.style.color = '#fbbf24';
          }
        }
      } catch (_) {}

      // Auto-load transcript if provided from Dictation Studio
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const urlTranscript = urlParams.get('transcript');
        const sessionTranscript = sessionStorage.getItem('analysis_transcript');
        const textToLoad = urlTranscript || sessionTranscript;
        if (textToLoad && textToLoad.trim().length > 0) {
          document.getElementById('transcriptInput').value = textToLoad;
          sessionStorage.removeItem('analysis_transcript');
          runAnalysis();
        }
      } catch (_) {}
    });
  </script>
</body>
</html>
"""
    return HTMLResponse(
        content=html_content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
