from fastapi import APIRouter, HTTPException, Body, status
import logging

from ..models import schemas
from ..utils import file_processor

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["File Processing"], # Tag for Swagger documentation
)

@router.post(
    "/process_file",
    response_model=schemas.FileProcessingResponse,
    summary="Processes a single uploaded file",
    description="Accepts a filename and its base64 encoded content, extracts text (TXT, PDF, MD) or performs OCR (images).",
    responses={
        400: {"model": schemas.ErrorResponse, "description": "Input data error or unsupported file type"},
        500: {"model": schemas.ErrorResponse, "description": "Internal server error during file processing"}
    }
)
async def process_single_file(
    request_body: schemas.FileProcessingRequest = Body(...)
):
    """
    Endpoint for processing a single file.
    """
    logger.info(f"Received /process_file request for file: {request_body.filename}")

    try:
        # Call the processing function from utils
        extracted_content = file_processor.process_uploaded_file_data(
            filename=request_body.filename,
            file_data_base64=request_body.file_data_base64
        )
        logger.info(f"Successfully processed file: {request_body.filename}")
        return schemas.FileProcessingResponse(content=extracted_content)

    except ValueError as ve:
        # Validation errors or unsupported file type
        logger.error(f"Error processing file {request_body.filename}: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        # Runtime errors (e.g., missing Tesseract, PyPDF2)
        logger.error(f"Runtime error processing file {request_body.filename}: {re}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        # Other unexpected errors
        logger.critical(f"Unexpected server error processing file {request_body.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An internal server error occurred: {e}")
