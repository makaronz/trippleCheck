from fastapi import Header, HTTPException, status
from typing import Optional

async def get_openrouter_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> str:
    """
    Zależność FastAPI do pobierania klucza API OpenRouter z nagłówka X-API-Key.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nagłówek X-API-Key z kluczem OpenRouter jest wymagany."
        )
    return x_api_key

# Można dodać inne zależności, np. do zarządzania sesją bazy danych, itp.
