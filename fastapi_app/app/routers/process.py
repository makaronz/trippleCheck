from fastapi import APIRouter, HTTPException, Body, Depends
import logging
import httpx # Added httpx import
from typing import Dict, Any

from ..models import schemas
from ..services import pipeline_service
from ..utils.dependencies import get_openrouter_api_key # Dependency to get the API key

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1", # Prefix for all routes in this router
    tags=["AI Pipeline"], # Tag for Swagger documentation
)

@router.post(
    "/process_query",
    response_model=schemas.ProcessQueryResponse, # Pydantic response model
    summary="Processes a user query through the AI pipeline",
    description="Accepts a query and optional documents, performs analysis, generates 3 perspectives (in parallel), verifies them, and synthesizes a final answer.",
    responses={
        400: {"model": schemas.ErrorResponse, "description": "Input data error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal server error"}
    }
)
async def process_query_endpoint(
    request_body: schemas.ProcessQueryRequest = Body(...), # Get the request body and validate
    api_key: str = Depends(get_openrouter_api_key) # Use dependency to get API key from environment variable
):
    """
    Endpoint for processing a query through the redesigned AI pipeline.
    """
    logger.info(f"Received /process_query request for query: {request_body.query[:50]}...")

    # Removed API key check from the request body

    try:
        # Run the AI pipeline from the service, passing the API key as an argument
        result = await pipeline_service.run_ai_pipeline(request_body, api_key)
        logger.info("Successfully finished processing the query.")
        return result

    except ValueError as ve:
        logger.error(f"Data validation error: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except httpx.HTTPStatusError as http_err: # Error from OpenRouter API
         logger.error(f"HTTP error during communication with OpenRouter: {http_err}", exc_info=True)
         # Return a more detailed error if possible
         error_detail = f"Error communicating with the AI model ({http_err.response.status_code})."
         try:
              # Try to read the error content from the API response
              api_error = http_err.response.json()
              error_detail += f" Details: {api_error.get('error', {}).get('message', http_err.response.text)}"
         except Exception:
              error_detail += f" Details: {http_err.response.text}"
         raise HTTPException(status_code=502, detail=error_detail) # 502 Bad Gateway
    except Exception as e:
        logger.critical(f"Unexpected critical server error during query processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# The /process_file endpoint could be added here if we move the logic
# @router.post("/process_file", ...)
# async def process_file_endpoint(...): ...
