from fastapi import APIRouter, HTTPException, Body, status
import logging

from ..models import schemas
from ..utils import file_processor
from ..models.file_models import FileProcessingRequest, FileProcessingResponse
from ..utils.logger import get_logger

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
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
async def process_single_file(file_data: FileProcessingRequest) -> FileProcessingResponse:
    """
    Process a single uploaded file.
    
    Args:
        file_data (FileProcessingRequest): Request containing filename and base64 encoded content
        
    Returns:
        FileProcessingResponse: Response containing processing results
        
    Raises:
        HTTPException: If file processing fails
    """
    try:
        # First validate and scan the file
        is_valid, mime_type, error_message = validate_file_type_and_scan(file_data.content)
        if not is_valid:
            raise ValueError(error_message)
            
        # Process the file if validation passes
        result = process_uploaded_file_data(file_data.filename, file_data.content)
        return FileProcessingResponse(
            success=True,
            filename=file_data.filename,
            mime_type=mime_type,
            processed_content=result
        )
        
    except ValueError as ve:
        logger.error(f"Validation error processing file {file_data.filename}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
        
    except RuntimeError as re:
        logger.error(f"Runtime error processing file {file_data.filename}: {str(re)}")
        raise HTTPException(status_code=500, detail=str(re))
        
    except Exception as e:
        logger.error(f"Unexpected error processing file {file_data.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
