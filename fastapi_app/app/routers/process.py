from fastapi import APIRouter, HTTPException, Body, Depends
import logging
import httpx # Dodano import httpx
from typing import Dict, Any

from ..models import schemas
from ..services import pipeline_service
from ..utils.dependencies import get_openrouter_api_key # Zależność do pobierania klucza API

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1", # Prefix dla wszystkich tras w tym routerze
    tags=["AI Pipeline"], # Tag dla dokumentacji Swagger
)

@router.post(
    "/process_query",
    response_model=schemas.ProcessQueryResponse, # Model odpowiedzi Pydantic
    summary="Przetwarza zapytanie użytkownika przez potok AI",
    description="Przyjmuje zapytanie i opcjonalne dokumenty, przeprowadza analizę, generuje 3 perspektywy (równolegle), weryfikuje je i syntetyzuje finalną odpowiedź.",
    responses={
        400: {"model": schemas.ErrorResponse, "description": "Błąd w danych wejściowych"},
        500: {"model": schemas.ErrorResponse, "description": "Wewnętrzny błąd serwera"}
    }
)
async def process_query_endpoint(
    request_body: schemas.ProcessQueryRequest = Body(...), # Pobierz ciało żądania i zwaliduj
    api_key: str = Depends(get_openrouter_api_key) # Użyj zależności do pobrania klucza API ze zmiennej środowiskowej
):
    """
    Endpoint do przetwarzania zapytania przez przeprojektowany potok AI.
    """
    logger.info(f"Otrzymano żądanie /process_query dla zapytania: {request_body.query[:50]}...")

    # Usunięto sprawdzanie klucza API z ciała żądania

    try:
        # Uruchomienie potoku AI z serwisu, przekazując klucz API jako argument
        result = await pipeline_service.run_ai_pipeline(request_body, api_key)
        logger.info("Pomyślnie zakończono przetwarzanie zapytania.")
        return result

    except ValueError as ve:
        logger.error(f"Błąd walidacji danych: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except httpx.HTTPStatusError as http_err: # Błąd z API OpenRouter
         logger.error(f"Błąd HTTP podczas komunikacji z OpenRouter: {http_err}", exc_info=True)
         # Zwróć bardziej szczegółowy błąd, jeśli to możliwe
         error_detail = f"Błąd komunikacji z modelem AI ({http_err.response.status_code})."
         try:
              # Spróbuj odczytać treść błędu z odpowiedzi API
              api_error = http_err.response.json()
              error_detail += f" Szczegóły: {api_error.get('error', {}).get('message', http_err.response.text)}"
         except Exception:
              error_detail += f" Szczegóły: {http_err.response.text}"
         raise HTTPException(status_code=502, detail=error_detail) # 502 Bad Gateway
    except Exception as e:
        logger.critical(f"Nieoczekiwany krytyczny błąd serwera podczas przetwarzania zapytania: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Wystąpił wewnętrzny błąd serwera: {e}")

# Można dodać tutaj endpoint /process_file, jeśli przenosimy tę logikę
# @router.post("/process_file", ...)
# async def process_file_endpoint(...): ...
