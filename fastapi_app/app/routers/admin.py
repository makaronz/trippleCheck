from fastapi import APIRouter, HTTPException, Body
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any
import httpx

from ..models import schemas

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Admin"], # Tag for Swagger documentation
)

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent.parent / "admin_settings.json"

# Default admin settings (Updated with latest models January 2025)
DEFAULT_SETTINGS = {
    "api_key": "",
    "models": {
        "analysis": "qwen/qwen3-coder:free",  # Fast, free model for analysis
        "perspective_informative": "google/gemini-2.5-flash",  # Fast, capable model for informative content
        "perspective_contrarian": "deepseek/deepseek-r1-0528:free",  # Free reasoning model for contrarian views
        "perspective_complementary": "mistralai/mistral-small-3.2-24b-instruct:free",  # Free, balanced model
        "verification": "anthropic/claude-sonnet-4",  # High-quality verification
        "synthesis": "qwen/qwen3-235b-a22b-thinking-2507"  # Advanced reasoning for synthesis
    }
}

def load_admin_settings() -> Dict[str, Any]:
    """Load admin settings from JSON file."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_settings = DEFAULT_SETTINGS.copy()
                merged_settings.update(settings)
                return merged_settings
        else:
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        logger.error(f"Error loading admin settings: {e}")
        return DEFAULT_SETTINGS.copy()

def save_admin_settings(settings: Dict[str, Any]) -> bool:
    """Save admin settings to JSON file."""
    try:
        # Ensure parent directory exists
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info(f"Admin settings saved to {SETTINGS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving admin settings: {e}")
        return False

@router.get(
    "/admin/settings",
    summary="Get current admin settings",
    description="Retrieve the current admin configuration including API key and model selections.",
    responses={
        200: {"description": "Admin settings retrieved successfully"},
        500: {"model": schemas.ErrorResponse, "description": "Internal server error"}
    }
)
async def get_admin_settings():
    """Get current admin settings."""
    try:
        settings = load_admin_settings()
        
        # Handle API key display
        api_key = settings.get("api_key", "")
        if api_key == "${API_KEY_FROM_ENV}":
            # Check if environment variable exists
            env_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("API_KEY")
            if env_key:
                settings["api_key"] = env_key[:8] + "..." + env_key[-4:] if len(env_key) > 12 else "***"
            else:
                settings["api_key"] = "${API_KEY_FROM_ENV} (not found in environment)"
        elif api_key:
            # Don't expose the full API key in the response for security
            settings["api_key"] = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        
        return settings
    except Exception as e:
        logger.error(f"Error retrieving admin settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin settings")

@router.post(
    "/admin/settings",
    summary="Save admin settings",
    description="Save new admin configuration including API key and model selections.",
    responses={
        200: {"description": "Settings saved successfully"},
        400: {"model": schemas.ErrorResponse, "description": "Invalid settings data"},
        500: {"model": schemas.ErrorResponse, "description": "Internal server error"}
    }
)
async def save_admin_settings_endpoint(
    settings: Dict[str, Any] = Body(...)
):
    """Save admin settings."""
    try:
        # Validate required structure
        if "models" not in settings:
            raise HTTPException(status_code=400, detail="Missing 'models' configuration")
        
        required_model_keys = [
            "analysis", "perspective_informative", "perspective_contrarian", 
            "perspective_complementary", "verification", "synthesis"
        ]
        
        for key in required_model_keys:
            if key not in settings["models"]:
                raise HTTPException(status_code=400, detail=f"Missing model configuration for '{key}'")
        
        # Validate API key format (basic check)
        api_key = settings.get("api_key", "")
        if api_key and len(api_key) < 40:
            raise HTTPException(status_code=400, detail="API key appears to be too short - OpenRouter API keys are typically 40+ characters")
        
        # Save settings
        success = save_admin_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save settings")
        
        logger.info("Admin settings updated successfully")
        return {"success": True, "message": "Settings saved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving admin settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save admin settings")

@router.post(
    "/admin/test-api-key",
    summary="Test OpenRouter API key",
    description="Test if the provided API key is valid by making a test call to OpenRouter.",
    responses={
        200: {"description": "API key is valid"},
        400: {"model": schemas.ErrorResponse, "description": "Invalid API key"},
        500: {"model": schemas.ErrorResponse, "description": "Internal server error"}
    }
)
async def test_api_key(
    request_data: Dict[str, str] = Body(...)
):
    """Test if an OpenRouter API key is valid."""
    api_key = request_data.get("api_key", "").strip()
    
    # Handle environment variable substitution
    if api_key == "${API_KEY_FROM_ENV}":
        env_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("API_KEY")
        if not env_key:
            raise HTTPException(status_code=400, detail="Environment variable OPENROUTER_API_KEY or API_KEY not found")
        api_key = env_key
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Validate API key length
    if len(api_key) < 40:
        raise HTTPException(status_code=400, detail="API key appears to be too short - OpenRouter API keys are typically 40+ characters")
    
    try:
        # Make a test call to OpenRouter to validate the API key
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen/qwen3-coder:free",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10.0
            )
            
            if response.status_code == 401:
                raise HTTPException(status_code=400, detail="Invalid API key - authentication failed")
            elif response.status_code == 403:
                raise HTTPException(status_code=400, detail="API key doesn't have required permissions")
            elif 200 <= response.status_code < 300:
                return {"valid": True, "message": "API key is valid"}
            else:
                # For other status codes, the key might still be valid but there could be other issues
                logger.warning(f"API key test returned status {response.status_code}")
                return {"valid": True, "message": "API key appears to be valid (could not complete full test)"}
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=400, detail="API key test timed out - please try again")
    except httpx.RequestError as e:
        logger.error(f"Network error during API key test: {e}")
        raise HTTPException(status_code=500, detail="Network error during API key validation")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to test API key")

# Function to get current admin settings for use by other services
def get_current_admin_settings() -> Dict[str, Any]:
    """Get current admin settings for use by other services."""
    return load_admin_settings()

# Function to get current API key
def get_current_api_key() -> str:
    """Get the current API key from admin settings or environment variables."""
    settings = load_admin_settings()
    api_key = settings.get("api_key", "")
    
    # Handle environment variable substitution
    if api_key == "${API_KEY_FROM_ENV}":
        env_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("API_KEY")
        return env_key if env_key else ""
    
    return api_key

# Function to get current model configuration
def get_current_models() -> Dict[str, str]:
    """Get the current model configuration from admin settings."""
    settings = load_admin_settings()
    return settings.get("models", DEFAULT_SETTINGS["models"])