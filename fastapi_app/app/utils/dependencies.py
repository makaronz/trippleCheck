import os
from fastapi import HTTPException, status
from dotenv import load_dotenv
import logging

# Załaduj zmienne środowiskowe z pliku .env (głównie dla lokalnego rozwoju)
# W produkcji zmienne będą ustawione bezpośrednio w środowisku Render
load_dotenv()

# Konfiguracja loggera
logger = logging.getLogger(__name__)

def get_openrouter_api_key() -> str:
    """
    Zależność FastAPI do pobierania klucza API OpenRouter ze zmiennych środowiskowych.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("Missing OPENROUTER_API_KEY environment variable.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Missing OpenRouter API key."
        )
    return api_key

# Można tu dodać inne zależności, np. do zarządzania sesją bazy danych, jeśli będzie potrzebna.
