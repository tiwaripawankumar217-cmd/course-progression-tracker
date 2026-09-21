from fastapi import APIRouter
from backend.utils.config import get_safe_config_status

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get(
    "/status",
    summary="Safe API key configuration check",
    description="Reports whether required external provider API keys are configured in .env without revealing values."
)
async def check_config_status():
    """Returns safe verification status for configured API keys."""
    return get_safe_config_status()
