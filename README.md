# GenAI-Powered Automated Course Progression Tracker

A modular, course-agnostic system designed to automatically track, verify, and document curriculum progression from classroom lectures into an official Course Progression record.

---

## 📌 Development Plan Overview

This project is built incrementally over 7 distinct stages:

* **Day 1: Project Foundation + Curriculum Ingestion** *(Current)*
* **Day 2: Audio Ingestion + Speech-to-Text**
* **Day 3: AI Lecture Analysis**
* **Day 4: Curriculum Mapping + Progress Engine**
* **Day 5: Excel Generation / Update**
* **Day 6: Teacher Review UI (React)**
* **Day 7: Full Integration + Testing + Demo**

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
