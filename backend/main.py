from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes.health import router as health_router
from backend.api.routes.curriculum import router as curriculum_router
from backend.services.curriculum_service import curriculum_service, DEFAULT_CURRICULUM_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown events."""
    # Ensure default curriculum is loaded on startup if available
    try:
        if DEFAULT_CURRICULUM_PATH.exists():
            curriculum_service.load_from_file(DEFAULT_CURRICULUM_PATH)
            print(f"[INFO] Default curriculum loaded from {DEFAULT_CURRICULUM_PATH.name}")
    except Exception as exc:
        print(f"[WARN] Startup could not load default curriculum: {exc}")
    yield


app = FastAPI(
    title="GenAI Automated Course Progression Tracker API",
    description=(
        "Course-agnostic progression tracking system that automates curriculum mapping, "
        "lecture content progression, and verification."
    ),
    version="1.0.0-day1",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Translate ValueError into HTTP 422 Unprocessable Content with clear error details."""
    http_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
    return JSONResponse(
        status_code=http_422,
        content={"error": "Validation Error", "detail": str(exc)},
    )


@app.get("/", tags=["Root"], summary="API Root / Overview")
async def root():
    """Returns basic service metadata and links to documentation."""
    return {
        "service": "GenAI-Powered Automated Course Progression Tracker",
        "day": 1,
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
        "curriculum_url": "/curriculum",
    }


# Include Modular Routers
app.include_router(health_router)
app.include_router(curriculum_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
