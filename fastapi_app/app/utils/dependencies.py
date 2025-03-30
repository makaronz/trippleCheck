import os
from fastapi import HTTPException, status
from dotenv import load_dotenv
import logging

# Load environment variables from .env file (mainly for local development)
# In production, variables will be set directly in the Render environment
load_dotenv()

# Logger configuration
logger = logging.getLogger(__name__)

def get_openrouter_api_key() -> str:
    """
    FastAPI dependency to retrieve the OpenRouter API key from environment variables.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("Missing OPENROUTER_API_KEY environment variable.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Missing OpenRouter API key."
        )
    return api_key

# Other dependencies can be added here, e.g., for managing database sessions if needed.
