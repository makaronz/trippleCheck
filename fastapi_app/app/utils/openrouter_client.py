import httpx
import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 60  # Seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # Seconds

async def call_openrouter_api_async(
    api_key: str,
    model: str,
    prompt_content: str,
    max_retries: int = MAX_RETRIES,
    retry_delay: int = RETRY_DELAY,
    timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    Asynchronously calls the OpenRouter API with error handling and retries.

    Args:
        api_key: OpenRouter API key.
        model: Name of the model to use.
        prompt_content: Content of the prompt for the model.
        max_retries: Maximum number of retries for network errors/timeouts.
        retry_delay: Initial delay between retries (increases exponentially).
        timeout: Timeout for a single HTTP request.

    Returns:
        Text response from the model.

    Raises:
        ValueError: If the API key is missing or the response has an invalid structure.
        RuntimeError: If unable to get a response after all retries.
        httpx.HTTPStatusError: If the API returns an HTTP error (e.g., 4xx, 5xx) after the last attempt.
    """
    if not api_key:
        logger.error("OpenRouter API key is missing.")
        raise ValueError("OpenRouter API key was not provided.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"), # Get from .env or use default
        "X-Title": os.getenv("APP_TITLE", "trippleCheck")      # Get from .env or use default
    }
    # Use the standard OpenAI API message format
    data = {"model": model, "messages": [{"role": "user", "content": prompt_content}]}

    last_exception = None

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Calling OpenRouter API for model {model} (attempt {attempt + 1}/{max_retries + 1})...")
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=data
                )
                response.raise_for_status()  # Will raise an exception for 4xx/5xx errors

                result = response.json()
                logger.info(f"Received response from model {model}.")

                # Check the response structure
                if (choices := result.get("choices")) and isinstance(choices, list) and len(choices) > 0:
                    if (message := choices[0].get("message")) and isinstance(message, dict):
                        if (content := message.get("content")) is not None:
                            logger.debug(f"Model {model} returned content: {content[:100]}...")
                            return str(content) # Return the content as a string

                # If the structure is invalid
                logger.error(f"Unexpected API response structure for model {model}: {result}")
                raise ValueError(f"Unexpected API response structure for model {model}")

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                logger.warning(f"Network error/timeout API (attempt {attempt + 1}/{max_retries + 1}) for model {model}: {e}")
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt) # Exponential backoff
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to connect to OpenRouter API for model {model} after {max_retries + 1} attempts.")
                    raise RuntimeError(f"Failed to connect to OpenRouter API for model {model} after {max_retries + 1} attempts: {e}") from e
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.error(f"HTTP error {e.response.status_code} API (attempt {attempt + 1}/{max_retries + 1}) for model {model}: {e.response.text}")
                # Usually, we don't retry on 4xx errors, but we might on 5xx
                if attempt < max_retries and e.response.status_code >= 500:
                    delay = retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # Raise the original HTTP error after the last attempt or on a 4xx error
                    raise e
            except Exception as e: # Other errors (e.g., ValueError from parsing)
                last_exception = e
                logger.error(f"Unexpected error during API call for model {model} (attempt {attempt + 1}): {e}", exc_info=True)
                # Do not retry on logical/structure errors
                raise RuntimeError(f"An unexpected error occurred during API communication for model {model}: {e}") from e

    # This code should not be reachable, but just in case:
    logger.critical(f"Failed to get a response from the API for model {model} after all attempts. Last error: {last_exception}")
    raise RuntimeError(f"Failed to get a response from the API for model {model} after all attempts. Last error: {last_exception}")

# Example usage (for testing)
async def main_test():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Set the OPENROUTER_API_KEY environment variable in a .env file")
        return

    try:
        # Test analysis
        analysis_response = await call_openrouter_api_async(
            api_key=api_key,
            model="openchat/openchat-3.5-0106",
            prompt_content="Analyze the query: 'What are the pros and cons of FastAPI vs Flask?'"
        )
        print("--- Analysis ---")
        print(analysis_response)

        # Test perspective
        perspective_response = await call_openrouter_api_async(
            api_key=api_key,
            model="mistralai/mistral-7b-instruct",
            prompt_content="Provide an informative perspective on FastAPI vs Flask."
        )
        print("\n--- Perspective ---")
        print(perspective_response)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # To run the test: python -m fastapi_app.app.utils.openrouter_client
    # Make sure you have a .env file in the fastapi_app directory with the API key
    # and dependencies installed (pip install -r fastapi_app/requirements.txt)
    load_dotenv(dotenv_path="../../.env") # Load .env from the main fastapi_app directory
    asyncio.run(main_test())
