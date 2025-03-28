# -*- coding: utf-8 -*-
import os
import base64
import tempfile
import traceback
import io
import time
import markdown
import requests
import json

# Usunięto import PyPDF2
from PIL import Image
import pytesseract
import markdownify
from bs4 import BeautifulSoup

# --- Stałe ---
# Przeniesiono do __init__.py lub konfiguracji, ale MAX_DOCUMENT_CHARS może tu zostać
MAX_DOCUMENT_CHARS = 4000
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") # Wczytane w __init__.py

# --- Przetwarzanie Plików ---

# Usunięto funkcję safe_extract_text_from_pdf

def safe_extract_text_from_image(image_data):
    """Bezpieczna ekstrakcja tekstu z obrazu (OCR). Rzuca wyjątek."""
    text = ""
    suffix = '.png'
    try:
        img_check = Image.open(io.BytesIO(image_data))
        if img_check.format:
             suffix = f'.{img_check.format.lower()}'
    except Exception:
        pass

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(image_data)
        temp_path = temp_file.name

    try:
        image = Image.open(temp_path)
        # Upewnij się, że Tesseract jest skonfigurowany (można to zrobić globalnie w __init__.py)
        # np. if os.getenv('TESSERACT_CMD'): pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD')
        text = pytesseract.image_to_string(image, lang='eng+pol') # Dodano polski
    except pytesseract.TesseractNotFoundError:
         raise RuntimeError("Tesseract OCR nie jest zainstalowany lub nie znajduje się w ścieżce systemowej (PATH).")
    except Exception as e:
        raise ValueError(f"Błąd podczas przetwarzania obrazu przez OCR: {e}") from e
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            print(f"Ostrzeżenie: Nie udało się usunąć pliku tymczasowego: {temp_path}")
    return text

def safe_extract_text_from_markdown(md_data):
    """Konwertuje Markdown na czysty tekst. Rzuca wyjątek."""
    try:
        if isinstance(md_data, bytes):
            md_text = md_data.decode('utf-8')
        else:
            md_text = md_data
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        raise ValueError(f"Błąd podczas przetwarzania pliku Markdown: {e}") from e

def safe_extract_text_from_txt(txt_data):
    """Bezpieczne odczytanie tekstu z danych TXT. Rzuca wyjątek."""
    try:
        if isinstance(txt_data, bytes):
            # Próba dekodowania jako UTF-8, potem latin-1, potem cp1250
            try:
                return txt_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return txt_data.decode('latin-1')
                except UnicodeDecodeError:
                    try:
                        return txt_data.decode('cp1250') # Częste w Windows PL
                    except Exception as inner_e:
                         raise ValueError(f"Nie udało się zdekodować pliku tekstowego (próbowano UTF-8, Latin-1, CP1250): {inner_e}") from inner_e
        return str(txt_data) # Jeśli już jest stringiem
    except Exception as e:
        raise ValueError(f"Błąd podczas odczytu pliku tekstowego: {e}") from e

def process_uploaded_file(filename, file_data_base64):
    """Przetwarza przesłany plik na podstawie jego typu."""
    try:
        file_data = base64.b64decode(file_data_base64)
        filename_lower = filename.lower()

        if filename_lower.endswith('.pdf'):
            # Zgłoś błąd zamiast przetwarzać PDF
            raise ValueError("Przesyłanie plików PDF nie jest obsługiwane.")
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png')):
            content = safe_extract_text_from_image(file_data)
        elif filename_lower.endswith('.md'):
            content = safe_extract_text_from_markdown(file_data)
        elif filename_lower.endswith('.txt'):
            content = safe_extract_text_from_txt(file_data)
        else:
            raise ValueError("Nieobsługiwany typ pliku.")

        # Ogranicz długość zwracanego contentu
        return content[:MAX_DOCUMENT_CHARS * 2]

    except (ValueError, RuntimeError, pytesseract.TesseractNotFoundError) as e:
        print(f"Błąd przetwarzania pliku {filename}: {e}")
        # Rzucamy wyjątek dalej, aby obsłużyć go w trasie
        raise e
    except Exception as e:
        print(f"Nieoczekiwany błąd w process_uploaded_file dla {filename}: {traceback.format_exc()}")
        raise RuntimeError("Wystąpił nieoczekiwany błąd serwera podczas przetwarzania pliku.") from e


# --- Logika API OpenRouter ---

def call_openrouter_api(api_key, model, prompt_content, max_retries=10, retry_delay=1):
    """Ulepszona funkcja API z obsługą błędów i ponowieniami."""
    if not api_key: # Sprawdź przekazany klucz
        raise ValueError("Klucz API OpenRouter nie został podany.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}", # Użyj przekazanego klucza
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:5000"), # Użyj zmiennej środowiskowej lub domyślnej
        "X-Title": os.getenv("APP_TITLE", "MultiModuleAgentApp")      # Użyj zmiennej środowiskowej lub domyślnej
    }
    data = {"model": model, "messages": [{"role": "user", "content": prompt_content}]}

    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # Zmniejszony timeout do 30 sekund
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0 and "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Nieoczekiwana struktura odpowiedzi API dla modelu {model}: {result}")

        except requests.exceptions.Timeout as e:
             last_exception = e
             print(f"Timeout API (próba {attempt+1}/{max_retries+1}) dla modelu {model}: {e}")
             # Można ponowić przy timeout
             if attempt < max_retries:
                 time.sleep(retry_delay * (attempt + 1))
             else:
                 raise RuntimeError(f"Przekroczono limit czasu połączenia z API OpenRouter dla modelu {model} po {max_retries+1} próbach.") from e
        except requests.exceptions.RequestException as e:
            last_exception = e
            print(f"Błąd sieciowy API (próba {attempt+1}/{max_retries+1}) dla modelu {model}: {e}")
            # Ponów przy błędach sieciowych
            if attempt < max_retries:
                time.sleep(retry_delay * (attempt + 1))
            else:
                raise RuntimeError(f"Nie udało się połączyć z API OpenRouter dla modelu {model} po {max_retries+1} próbach: {e}") from e
        except Exception as e: # Inne błędy (np. ValueError z parsowania)
             last_exception = e
             print(f"Nieoczekiwany błąd podczas wywołania API dla modelu {model} (próba {attempt+1}): {e}")
             # Nie ponawiaj przy błędach logicznych/struktury
             raise RuntimeError(f"Wystąpił nieoczekiwany błąd podczas komunikacji z API dla modelu {model}: {e}") from e

    # Ten kod nie powinien być osiągnięty
    raise RuntimeError(f"Nie udało się uzyskać odpowiedzi z API dla modelu {model} po wszystkich próbach. Ostatni błąd: {last_exception}")


# --- Logika API Google Gemini ---

def call_google_gemini_api(api_key, model, prompt_content, max_retries=5, retry_delay=2):
    """Funkcja do wywoływania API Google Gemini."""
    if not api_key:
        raise ValueError("Klucz API Google Gemini nie został podany.")

    # Endpoint API Gemini (może się różnić w zależności od modelu i regionu)
    # Używamy v1beta dla modeli Gemini Pro
    api_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }
    # Struktura danych dla Gemini API
    data = {
        "contents": [{
            "parts": [{
                "text": prompt_content
            }]
        }],
        # Można dodać konfigurację generowania, np. temperature, maxOutputTokens
        # "generationConfig": {
        #     "temperature": 0.7,
        #     "maxOutputTokens": 2048,
        # }
    }

    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=data,
                timeout=60 # Zmniejszony timeout do 60 sekund
            )
            response.raise_for_status() # Rzuci wyjątkiem dla błędów 4xx/5xx

            result = response.json()

            # Sprawdzenie struktury odpowiedzi Gemini
            if "candidates" in result and len(result["candidates"]) > 0 and \
               "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"] and \
               len(result["candidates"][0]["content"]["parts"]) > 0 and "text" in result["candidates"][0]["content"]["parts"][0]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            elif "promptFeedback" in result and "blockReason" in result["promptFeedback"]:
                 # Obsługa zablokowania przez filtry bezpieczeństwa
                 block_reason = result["promptFeedback"]["blockReason"]
                 details = result["promptFeedback"].get("safetyRatings", [])
                 raise ValueError(f"Zapytanie zablokowane przez Google Gemini z powodu: {block_reason}. Szczegóły: {details}")
            else:
                # Jeśli struktura jest inna lub brak tekstu
                raise ValueError(f"Nieoczekiwana struktura odpowiedzi API Google Gemini dla modelu {model}: {result}")

        except requests.exceptions.Timeout as e:
             last_exception = e
             print(f"Timeout API Google Gemini (próba {attempt+1}/{max_retries+1}) dla modelu {model}: {e}")
             if attempt < max_retries:
                 time.sleep(retry_delay * (attempt + 1))
             else:
                 raise RuntimeError(f"Przekroczono limit czasu połączenia z API Google Gemini dla modelu {model} po {max_retries+1} próbach.") from e
        except requests.exceptions.RequestException as e:
            last_exception = e
            print(f"Błąd sieciowy API Google Gemini (próba {attempt+1}/{max_retries+1}) dla modelu {model}: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay * (attempt + 1))
            else:
                raise RuntimeError(f"Nie udało się połączyć z API Google Gemini dla modelu {model} po {max_retries+1} próbach: {e}") from e
        except Exception as e: # Inne błędy (np. ValueError)
             last_exception = e
             print(f"Nieoczekiwany błąd podczas wywołania API Google Gemini dla modelu {model} (próba {attempt+1}): {e}")
             raise RuntimeError(f"Wystąpił nieoczekiwany błąd podczas komunikacji z API Google Gemini dla modelu {model}: {e}") from e

    raise RuntimeError(f"Nie udało się uzyskać odpowiedzi z API Google Gemini dla modelu {model} po wszystkich próbach. Ostatni błąd: {last_exception}")
