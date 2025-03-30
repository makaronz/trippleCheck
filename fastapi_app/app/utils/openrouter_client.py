import httpx
import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stałe
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 60  # Sekundy
MAX_RETRIES = 3
RETRY_DELAY = 2  # Sekundy

async def call_openrouter_api_async(
    api_key: str,
    model: str,
    prompt_content: str,
    max_retries: int = MAX_RETRIES,
    retry_delay: int = RETRY_DELAY,
    timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    Asynchronicznie wywołuje API OpenRouter z obsługą błędów i ponowień.

    Args:
        api_key: Klucz API OpenRouter.
        model: Nazwa modelu do użycia.
        prompt_content: Treść promptu dla modelu.
        max_retries: Maksymalna liczba ponowień w przypadku błędów sieciowych/timeoutów.
        retry_delay: Początkowe opóźnienie między ponowieniami (rośnie wykładniczo).
        timeout: Timeout dla pojedynczego zapytania HTTP.

    Returns:
        Odpowiedź tekstowa z modelu.

    Raises:
        ValueError: Jeśli brakuje klucza API lub odpowiedź ma nieprawidłową strukturę.
        RuntimeError: Jeśli nie uda się uzyskać odpowiedzi po wszystkich ponowieniach.
        httpx.HTTPStatusError: Jeśli API zwróci błąd HTTP (np. 4xx, 5xx) po ostatniej próbie.
    """
    if not api_key:
        logger.error("Brak klucza API OpenRouter.")
        raise ValueError("Klucz API OpenRouter nie został podany.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"), # Pobierz z .env lub użyj domyślnego
        "X-Title": os.getenv("APP_TITLE", "AI Agent - FastAPI")      # Pobierz z .env lub użyj domyślnego
    }
    # Używamy standardowego formatu wiadomości OpenAI API
    data = {"model": model, "messages": [{"role": "user", "content": prompt_content}]}

    last_exception = None

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Wywołanie API OpenRouter dla modelu {model} (próba {attempt + 1}/{max_retries + 1})...")
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=data
                )
                response.raise_for_status()  # Rzuci wyjątkiem dla błędów 4xx/5xx

                result = response.json()
                logger.info(f"Otrzymano odpowiedź od modelu {model}.")

                # Sprawdzenie struktury odpowiedzi
                if (choices := result.get("choices")) and isinstance(choices, list) and len(choices) > 0:
                    if (message := choices[0].get("message")) and isinstance(message, dict):
                        if (content := message.get("content")) is not None:
                            logger.debug(f"Model {model} zwrócił treść: {content[:100]}...")
                            return str(content) # Zwracamy treść jako string

                # Jeśli struktura jest nieprawidłowa
                logger.error(f"Nieoczekiwana struktura odpowiedzi API dla modelu {model}: {result}")
                raise ValueError(f"Nieoczekiwana struktura odpowiedzi API dla modelu {model}")

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                logger.warning(f"Błąd sieciowy/timeout API (próba {attempt + 1}/{max_retries + 1}) dla modelu {model}: {e}")
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt) # Backoff wykładniczy
                    logger.info(f"Ponowienie za {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Nie udało się połączyć z API OpenRouter dla modelu {model} po {max_retries + 1} próbach.")
                    raise RuntimeError(f"Nie udało się połączyć z API OpenRouter dla modelu {model} po {max_retries + 1} próbach: {e}") from e
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.error(f"Błąd HTTP {e.response.status_code} API (próba {attempt + 1}/{max_retries + 1}) dla modelu {model}: {e.response.text}")
                # Zazwyczaj nie ponawiamy przy błędach 4xx, ale możemy przy 5xx
                if attempt < max_retries and e.response.status_code >= 500:
                    delay = retry_delay * (2 ** attempt)
                    logger.info(f"Ponowienie za {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # Rzucamy oryginalny błąd HTTP po ostatniej próbie lub przy błędzie 4xx
                    raise e
            except Exception as e: # Inne błędy (np. ValueError z parsowania)
                last_exception = e
                logger.error(f"Nieoczekiwany błąd podczas wywołania API dla modelu {model} (próba {attempt + 1}): {e}", exc_info=True)
                # Nie ponawiaj przy błędach logicznych/struktury
                raise RuntimeError(f"Wystąpił nieoczekiwany błąd podczas komunikacji z API dla modelu {model}: {e}") from e

    # Ten kod nie powinien być osiągnięty, ale dla pewności:
    logger.critical(f"Nie udało się uzyskać odpowiedzi z API dla modelu {model} po wszystkich próbach. Ostatni błąd: {last_exception}")
    raise RuntimeError(f"Nie udało się uzyskać odpowiedzi z API dla modelu {model} po wszystkich próbach. Ostatni błąd: {last_exception}")

# Przykład użycia (do testów)
async def main_test():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Ustaw zmienną środowiskową OPENROUTER_API_KEY w pliku .env")
        return

    try:
        # Test analizy
        analysis_response = await call_openrouter_api_async(
            api_key=api_key,
            model="openchat/openchat-3.5-0106",
            prompt_content="Analyze the query: 'What are the pros and cons of FastAPI vs Flask?'"
        )
        print("--- Analiza ---")
        print(analysis_response)

        # Test perspektywy
        perspective_response = await call_openrouter_api_async(
            api_key=api_key,
            model="mistralai/mistral-7b-instruct",
            prompt_content="Provide an informative perspective on FastAPI vs Flask."
        )
        print("\n--- Perspektywa ---")
        print(perspective_response)

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    # Aby uruchomić test: python -m fastapi_app.app.utils.openrouter_client
    # Upewnij się, że masz plik .env w katalogu fastapi_app z kluczem API
    # i zainstalowane zależności (pip install -r fastapi_app/requirements.txt)
    load_dotenv(dotenv_path="../../.env") # Wczytaj .env z katalogu głównego fastapi_app
    asyncio.run(main_test())
