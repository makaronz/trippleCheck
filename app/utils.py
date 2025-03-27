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

import PyPDF2
from PIL import Image
import pytesseract
import markdownify
from bs4 import BeautifulSoup

# --- Stałe ---
# Przeniesiono do __init__.py lub konfiguracji, ale MAX_DOCUMENT_CHARS może tu zostać
MAX_DOCUMENT_CHARS = 4000
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") # Wczytane w __init__.py

# --- Przetwarzanie Plików ---

def safe_extract_text_from_pdf(pdf_data):
    """Bezpieczna ekstrakcja tekstu z PDF. Rzuca wyjątek w razie błędu."""
    text = ""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(pdf_data)
        temp_path = temp_file.name
    try:
        with open(temp_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # Sprawdzenie czy plik jest zaszyfrowany
            if reader.is_encrypted:
                 try:
                     # Próba odszyfrowania pustym hasłem (częsty przypadek)
                     reader.decrypt('')
                 except Exception as decrypt_error:
                      raise ValueError(f"Plik PDF jest zaszyfrowany i nie można go odszyfrować: {decrypt_error}") from decrypt_error

            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_error:
                    print(f"Ostrzeżenie: Błąd podczas ekstrakcji tekstu ze strony PDF: {page_error}")
                    continue # Przejdź do następnej strony
    except PyPDF2.errors.PdfReadError as pdf_error:
         raise ValueError(f"Błąd odczytu pliku PDF (może być uszkodzony): {pdf_error}") from pdf_error
    except Exception as e:
        raise ValueError(f"Nieoczekiwany błąd podczas przetwarzania PDF: {e}") from e
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
             print(f"Ostrzeżenie: Nie udało się usunąć pliku tymczasowego: {temp_path}")
    return text

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
            content = safe_extract_text_from_pdf(file_data)
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

def call_openrouter_api(model, prompt_content, max_retries=2, retry_delay=5):
    """Ulepszona funkcja API z obsługą błędów i ponowieniami."""
    if not OPENROUTER_API_KEY:
        raise ValueError("Klucz API OpenRouter nie został skonfigurowany.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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
                timeout=180
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
