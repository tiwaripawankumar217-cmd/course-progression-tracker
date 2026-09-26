# GenAI-Powered Automated Course Progression Tracker

A modular, course-agnostic system designed to automatically track, verify, and document curriculum progression from classroom lectures into an official Course Progression record.

---

## 📌 Development Plan Overview

This project is built incrementally over 7 distinct stages:

* **Day 1: Project Foundation + Curriculum Ingestion** *(Completed)*
* **Day 2: Audio Ingestion + Speech-to-Text** *(Completed)*
* **Day 3: AI Lecture Analysis + Multi-Material Context** *(Completed)*
* **Day 4: Curriculum Mapping + Progress Engine + Clean UI** *(Completed)*
* **Day 5: Excel Generation / Update** *(Completed)*
* **Day 6: Teacher Review UI (React)** *(Completed)*
* **Day 7: Full Integration + Testing + Demo** *(Completed)*

---

## 🚀 Day 1: Project Foundation + Curriculum Ingestion

Day 1 establishes a modular backend foundation, course-agnostic curriculum schemas, in-memory/file-based loading services, strict validation with hallucination safeguards, FastAPI REST endpoints, and a comprehensive test suite.

### Key Architectural Principles
1. **Strictly Course-Agnostic**: No domain-specific (DSA, CS, etc.) concepts or hardcoded topics are baked into logic. The curriculum is the single source of truth.
2. **Deterministic Validation**: Pydantic models validate structure, types, non-empty topic lists, positive day/week indexing, and detect duplicate lecture codes before data enters the system.
3. **Fail-Fast Error Reporting**: Clear, descriptive errors pin-point exact fields and reasons when an invalid curriculum is supplied.

---

## 📂 Project Structure

```
.
├── backend/
│   ├── main.py                     # FastAPI application entry point, middleware & lifespan
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py           # GET /health
│   │       └── curriculum.py       # GET/POST /curriculum endpoints
│   ├── data/
│   │   ├── curriculum.json         # Generic, course-agnostic sample curriculum
│   │   └── sample_invalid_curriculum.json # Demonstration invalid curriculum
│   ├── models/
│   │   ├── __init__.py
│   │   └── curriculum.py           # Pydantic domain models (LecturePlan, Curriculum)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── curriculum.py           # API request/response DTOs & summaries
│   ├── services/
│   │   ├── __init__.py
│   │   └── curriculum_service.py   # Ingestion, parsing, and validation service
│   ├── utils/
│   │   └── __init__.py
│   ├── output/                     # Directory reserved for progression spreadsheets
│   │   └── .gitkeep
│   └── tests/
│       ├── __init__.py
│       ├── test_health.py          # Tests for /health and root
│       └── test_curriculum.py      # Comprehensive curriculum validation tests
├── requirements.txt                # Backend dependencies
├── .env.example                    # Environment configuration template
├── .gitignore
└── README.md
```

---

## 📋 Curriculum Format Specification

Every lecture plan within a curriculum adheres strictly to this structure:

```json
{
  "week": 1,
  "day": 1,
  "lecture": "LEC-1",
  "content": [
    "Topic A: Core Principles",
    "Topic B: Conceptual Framework",
    "Topic C: Primary Methodologies"
  ],
  "classwork": [
    "Activity 1: Guided Concept Review"
  ],
  "homework": [
    "Homework 1: Practice Exercises"
  ]
}
```

The system accepts either:
- A standard curriculum container: `{"course_id": "...", "course_name": "...", "lectures": [...]}`
- Or directly a JSON array of lecture objects: `[{...}, {...}]`

---

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- `pip`

### 2. Create and Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

---

## ▶️ How to Run the Backend

Start the development server with auto-reload:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The server will start at `http://127.0.0.1:8000`.

Interactive Swagger API documentation will be available at:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

---

## 🧪 Testing

Run the automated test suite with `pytest`:

```bash
pytest backend/tests -v
```

### Manual Verification via `curl`

#### 1. Health Check
```bash
curl -s http://127.0.0.1:8000/health
```
Response:
```json
{"status": "ok"}
```

#### 2. Get Active Curriculum
```bash
curl -s http://127.0.0.1:8000/curriculum
```

#### 3. Query Specific Lecture Plan
```bash
curl -s http://127.0.0.1:8000/curriculum/lectures/LEC-1
```

#### 4. Load Custom Curriculum (Valid)
```bash
curl -s -X POST http://127.0.0.1:8000/curriculum/load \
  -H "Content-Type: application/json" \
  -d '[
    {
      "week": 1,
      "day": 1,
      "lecture": "DEMO-1",
      "content": ["Orientation", "Introduction"],
      "classwork": ["Setup IDE"],
      "homework": ["Read Syllabus"]
    }
  ]'
```

#### 5. Verify Invalid Curriculum Rejection
```bash
curl -s -X POST http://127.0.0.1:8000/curriculum/load \
  -H "Content-Type: application/json" \
  -d @backend/data/sample_invalid_curriculum.json
```
Response:
```json
{
  "detail": "Curriculum validation failed: Field 'lectures -> 0 -> week': Input should be greater than or equal to 1; Field 'lectures -> 0 -> lecture': String should have at least 1 character; Field 'lectures -> 0 -> content': List should have at least 1 item after validation, not 0"
}
```

#### 6. Reset Curriculum Back to Default Sample
```bash
curl -s -X POST http://127.0.0.1:8000/curriculum/reset
```

#### 7. Verify API Key Status (Safe Check)
```bash
curl -s http://127.0.0.1:8000/config/status
```

#### 8. Upload Lecture Audio (Mock Provider)
```bash
curl -s -X POST "http://127.0.0.1:8000/lecture/audio?provider=mock" \
  -F "file=@/path/to/lecture.mp3"
```

#### 9. Upload Lecture Audio (AssemblyAI Provider)
```bash
curl -s -X POST http://127.0.0.1:8000/lecture/audio \
  -F "file=@/path/to/lecture.mp3"
```

---

## 🧠 Day 3: AI Lecture Analysis + Multi-Material Context

Day 3 builds the AI analysis layer that understands classroom lecture delivery and maps it against the curriculum with optional supporting academic documents.

### Strict Source Hierarchy
1. **SOURCE 1 — CURRICULUM (Authoritative Source of Truth)**: The AI can ONLY map to lectures, topics, classwork, and homework that actually exist in the active curriculum. Programmatic safeguards prevent inventing new curriculum topics.
2. **SOURCE 2 — LECTURE TRANSCRIPT (Primary Evidence)**: What the instructor actually explained and taught in class. Every mapped topic, classwork, and homework requires explicit transcript evidence quotes.
3. **SOURCE 3 — SUPPORTING MATERIALS (Contextual Academic Support)**: Slides (PPTX), notes (PDF/TXT), or readings (DOCX). Materials must **NEVER** override the transcript: if a concept appears in a slide deck but is never taught in the transcript, it is classified as `topics_not_evidenced`.

### Multi-Material Extraction Layer
- **PDF**: Page-by-page text extraction with `[Page X]` markers.
- **PPT / PPTX**: Slide-by-slide text extraction with `[Slide Y]` markers (native OpenXML parser).
- **DOCX**: Document text extraction preserving paragraph structures.
- **TXT / Markdown**: Multi-encoding text parsing with context window budget limits.
- **Resilience**: Corrupt or unsupported files produce warnings in `analysis_warnings` rather than crashing the pipeline.

### Anti-Hallucination Guardrails
Any topic generated by the LLM that is not in the active curriculum is automatically intercepted, removed from `topics_taught`, and routed to `unmatched_content`.

### Dual Provider Architecture
- **Gemini Engine**: Live inference using Gemini Flash (`GEMINI_API_KEY`).
- **Mock Engine**: Deterministic offline rule-based analyzer for zero-cost automated testing, CI/CD, and local verification without external network access.

### Endpoints
- `POST /analyze`: JSON payload with `transcript`, optional `curriculum`, and `materials`.
- `POST /analyze/upload`: Multipart endpoint for file uploads.
- `GET /analyze/ui`: Interactive browser studio for testing scenarios in real time (`http://127.0.0.1:8000/analyze/ui`).

#### Example API Request
```bash
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Today we cover Topic A: Core Principles. Let us do Activity 1 together.",
    "provider": "mock",
    "materials": [
      {
        "name": "slides.pptx",
        "type": "pptx",
        "content": "[Slide 1]\nCore Principles\n[Slide 2]\nTime Complexity"
      }
    ]
  }'
```

---

## 📊 Day 4: Curriculum Mapping, Progress Engine + Clean UI

Day 4 reconciles the structured Day 3 AI lecture extraction against the planned Day 1 curriculum to compute reliable, deterministic course progression results and visualize them in a clean academic React interface.

### Deterministic Formulas
All progression mathematics are calculated strictly in Python backend logic with zero LLM arithmetic:

1. **% Covered**:
   $$\text{\% Covered} = \frac{\text{covered curriculum items} + \text{uncertain items}}{\text{total planned curriculum items}} \times 100$$
   *Measures the portion of the planned curriculum evidenced or touched in the lecture.*

2. **% Completed**:
   $$\text{\% Completed} = \frac{\text{confirmed covered curriculum items (confidence} \ge \text{threshold)}}{\text{total planned curriculum items}} \times 100$$
   *Strict metric excluding tentative or low-confidence topics awaiting human teacher review.*

3. **Deterministic Status Engine**:
   - **`COMPLETED`**: Reached when $\text{\% Completed} \ge \text{completed\_threshold}$ (default: $100\%$).
   - **`ONGOING`**: When $0\% < \text{\% Covered} < \text{completed\_threshold}$ and lecture session continues.
   - **`SPILLED OVER`**: Triggered when a finalized lecture session concludes with uncompleted planned topics.
   - **`NOT_STARTED`**: $0\%$ coverage or unmapped lecture delivery.

### Anti-Hallucination & Low-Confidence Guardrails
- **Curriculum Boundaries**: Topics outside the active curriculum are never added as new curriculum topics; they are routed to `warnings` as informational notes.
- **Uncertain / Needs Review**: Topics with confidence $< 0.65$ (e.g. $0.42$) are classified as `uncertain` and surfaced in amber for human teacher inspection.
- **Classwork & Homework**: Only displayed when verified with transcript evidence; otherwise falls back to `"No classwork detected"` / `"No homework detected"`.

### Endpoints
- `POST /progress/calculate`: Accepts `analysis`, optional `curriculum`, and `config` to return deterministic `LectureProgression`.
- `GET /progress/demo`: Returns safe pre-configured demonstration scenarios.
- `GET /progress/ui`: Serves the compiled React productivity dashboard (`http://127.0.0.1:8000/progress/ui`).

#### Example Progress Calculation Request
```bash
curl -s -X POST http://127.0.0.1:8000/progress/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_code": "LEC-1",
    "analysis": {
      "analysis_status": "SUCCESS",
      "matched_lecture": {"lecture_name": "LEC-1", "confidence": 0.95},
      "topics_taught": [
        {"curriculum_topic": "Arrays", "evidence": "Contiguous memory layout explained.", "confidence": 0.95},
        {"curriculum_topic": "Array Traversal", "evidence": "Linear scan loop demonstrated.", "confidence": 0.92}
      ],
      "topics_not_evidenced": ["Time Complexity"],
      "classwork": [{"description": "Find Maximum Element", "evidence": "Coded max value scan.", "confidence": 0.95}],
      "homework": []
    }
  }'
```

---

## 📊 Day 5: Excel Progression Sheet Generation & Update

Day 5 converts validated Day 4 progression outputs into an official faculty Course Progression spreadsheet (`.xlsx`), with support for updating existing workbooks without losing prior records.

### Required Output Schema (Strictly Enforced)

| Column Name | Type | Description |
| :--- | :--- | :--- |
| **`Date Taught`** | Text / Date | ISO format (YYYY-MM-DD) date of lecture delivery |
| **`Status`** | Text | Normalized progression status (`Completed`, `Ongoing`, `Spilled Over`) |
| **`% Completed`** | Numeric (2 dec) | Deterministic completed percentage from Day 4 engine (e.g. `66.67`) |
| **`% Covered`** | Numeric (2 dec) | Deterministic covered percentage from Day 4 engine (e.g. `66.67`) |
| **`CW`** | Text | Classwork activities evidenced from lecture transcript |
| **`HW`** | Text | Homework assignments explicitly assigned (never hallucinated) |

### Key Capabilities
1. **New Workbook Generation**: Generates clean, professional `.xlsx` file with frozen header row, Calibri typography, autofilter, and auto-adjusted column widths.
2. **Deterministic Duplicate Protection**: When re-exporting the same date and lecture, updates the existing row in place instead of creating duplicate records.
3. **Existing Workbook Update**: Preserves all prior rows while appending or updating the current lecture record.
4. **Secondary Evidence Sheet**: Includes an optional `Evidence` sheet with topic confidence and transcript excerpts for review.

### Endpoints
- `POST /progress/export`: Accepts `ExportProgressionRequest` or Day 4 `LectureProgression` payload; returns downloadable binary `.xlsx` workbook.
- `POST /progress/export/update`: Accepts multipart form (`file`: existing `.xlsx`, `progression_json`: JSON string); returns updated `.xlsx` workbook.

#### Example Excel Export Request
```bash
curl -s -X POST http://127.0.0.1:8000/progress/export \
  -H "Content-Type: application/json" \
  -d '{
    "lecture": "LEC-1",
    "date_taught": "2026-09-26",
    "status": "Ongoing",
    "percent_completed": 66.67,
    "percent_covered": 66.67,
    "classwork": "Find Maximum Element in Array",
    "homework": "Solve 5 Array Practice Problems"
  }' \
  --output course_progression.xlsx
```

---

## 👩‍🏫 Day 6: Teacher Review UI (React) & Approval Workflow

Day 6 implements the Human-in-the-Loop (HITL) interface empowering educators to verify AI findings, apply pedagogical overrides to low-confidence topics, and approve the official progression records.

### Key Capabilities
1. **Uncertain Topic Inspection**: Highlights topics with low AI confidence ($< 0.65$) with full transcript evidence quotes for rapid teacher evaluation.
2. **Pedagogical Overrides**: One-click actions (`✓ Covered` / `✗ Not Covered`) that trigger deterministic real-time recalculation of `% Completed`, `% Covered`, and status.
3. **Formal Instructor Sign-Off**: Captures instructor name, verification timestamp, and pedagogical notes.
4. **Direct Excel Sync**: Automatically commits the approved lecture record directly into `course_progression.xlsx`.

### Endpoints
- `POST /progress/review/approve`: Submits instructor verification and commits approved progression into `course_progression.xlsx`.
- `GET /progress/download`: Directly downloads the current `course_progression.xlsx` file.

#### Example Teacher Approval Request
```bash
curl -s -X POST http://127.0.0.1:8000/progress/review/approve \
  -H "Content-Type: application/json" \
  -d '{
    "progression": { ...LectureProgression... },
    "instructor_name": "Prof. Sharma",
    "comments": "Verified and approved.",
    "commit_to_excel": true
  }'
```

---

## 🎯 Day 7: Product Usability, User Guide & End-to-End Demo

Day 7 elevates the system from an engineering MVP into a **faculty-ready product** that any professor or instructor can open and immediately operate without technical assistance.

### Key Usability Enhancements

1. **Self-Explanatory Interface**:
   - Academic terminology with visual cues explaining *what this product does*, *what to upload*, and *how progress is calculated*.
   - Clear input sections: Audio recording upload (`.mp3`, `.wav`), spoken transcript text, and supporting slide/notes files (`.pdf`, `.pptx`, `.docx`).
   - One-click sample test audio for instant evaluation without recording live lectures.

2. **Unified 6-Step Faculty Workflow**:
   ```text
   Step 1: Select / Verify Course Curriculum
             ↓
   Step 2: Upload Lecture Audio (or enter transcript)
             ↓
   Step 3: Attach Optional Supporting Materials (Slides, Notes)
             ↓
   Step 4: AI Lecture Delivery Analysis & Curriculum Mapping
             ↓
   Step 5: Human-in-the-Loop Review & Pedagogical Overrides
             ↓
   Step 6: Sync to Official Excel Progression Spreadsheet
   ```

3. **Interactive "How to Use" Faculty Guide**:
   - Accessible via the **📘 How to Use / Guide** button in the header.
   - Comprehensive walk-through of the 6-step workflow, explanation of progression formulas (`% Completed` vs `% Covered`), status rules (`Completed`, `Ongoing`, `Spilled Over`), and faculty FAQs.

4. **Automated End-to-End Pipeline Verification**:
   - `test_day7_e2e_workflow.py` validates the complete pipeline from Audio Ingestion $\rightarrow$ Transcription $\rightarrow$ Multi-Material AI Extraction $\rightarrow$ Curriculum Reconciler $\rightarrow$ Teacher Override $\rightarrow$ Excel Workbook persistence.

### End-to-End Workflow Verification Command
```bash
pytest backend/tests/test_day7_e2e_workflow.py -v
```

### Complete Test Suite
```bash
pytest backend/tests/ -v
```
*(68 passed, 0 failed)*


