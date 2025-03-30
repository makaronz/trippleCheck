from fastapi import APIRouter, HTTPException, Body, status
import logging

from ..models import schemas
from ..utils import file_processor

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["File Processing"], # Tag dla dokumentacji Swagger
)

@router.post(
    "/process_file",
    response_model=schemas.FileProcessingResponse,
    summary="Przetwarza pojedynczy przesłany plik",
    description="Przyjmuje nazwę pliku i jego zawartość zakodowaną w base64, ekstrahuje tekst (TXT, PDF, MD) lub wykonuje OCR (obrazy).",
    responses={
        400: {"model": schemas.ErrorResponse, "description": "Błąd w danych wejściowych lub nieobsługiwany typ pliku"},
        500: {"model": schemas.ErrorResponse, "description": "Wewnętrzny błąd serwera podczas przetwarzania pliku"}
    }
)
async def process_single_file(
    request_body: schemas.FileProcessingRequest = Body(...)
):
    """
    Endpoint do przetwarzania pojedynczego pliku.
    """
    logger.info(f"Otrzymano żądanie /process_file dla pliku: {request_body.filename}")

    try:
        # Wywołaj funkcję przetwarzającą z utils
        extracted_content = file_processor.process_uploaded_file_data(
            filename=request_body.filename,
            file_data_base64=request_body.file_data_base64
        )
        logger.info(f"Pomyślnie przetworzono plik: {request_body.filename}")
        return schemas.FileProcessingResponse(content=extracted_content)

    except ValueError as ve:
        # Błędy walidacji lub nieobsługiwany typ pliku
        logger.error(f"Błąd przetwarzania pliku {request_body.filename}: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        # Błędy wykonania (np. brak Tesseracta, PyPDF2)
        logger.error(f"Błąd wykonania podczas przetwarzania pliku {request_body.filename}: {re}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        # Inne, nieoczekiwane błędy
        logger.critical(f"Nieoczekiwany błąd serwera podczas przetwarzania pliku {request_body.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Wystąpił wewnętrzny błąd serwera: {e}")
