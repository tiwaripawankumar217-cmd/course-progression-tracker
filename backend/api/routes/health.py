from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Returns application status.
    Expected response: {"status": "ok"}
    """
    return {"status": "ok"}
