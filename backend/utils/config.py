import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Locate project root and load .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()


def get_assemblyai_api_key() -> str:
    """Retrieve AssemblyAI API key from environment, checking latest .env file."""
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=True)
    return os.getenv("ASSEMBLYAI_API_KEY", "").strip()


def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from environment, checking latest .env file."""
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=True)
    return os.getenv("GEMINI_API_KEY", "").strip()


def get_safe_config_status() -> Dict[str, str]:
    """
    Returns a safe status dictionary showing whether required API keys are configured.
    NEVER returns or logs the secret key values.
    """
    assembly_key = get_assemblyai_api_key()
    gemini_key = get_gemini_api_key()

    return {
        "ASSEMBLYAI_API_KEY": "CONFIGURED" if bool(assembly_key) else "NOT CONFIGURED",
        "GEMINI_API_KEY": "CONFIGURED" if bool(gemini_key) else "NOT CONFIGURED",
    }
