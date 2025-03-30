# -*- coding: utf-8 -*-
import os
import base64
import tempfile
import traceback
import io
import logging

# Zależności do przetwarzania plików
try:
    import fitz  # type: ignore # PyMuPDF
except ImportError:
    fitz = None

try:
    import ocrmypdf # type: ignore
    # Sprawdzenie, czy Tesseract jest dostępny dla ocrmypdf
    # ocrmypdf.check() # Może rzucić wyjątek, jeśli Tesseracta brakuje
except ImportError:
    ocrmypdf = None
except Exception as ocr_check_e:
     logging.warning(f"ocrmypdf jest zainstalowany, ale wystąpił problem ze sprawdzeniem zależności (np. Tesseract): {ocr_check_e}")
     ocrmypdf = None # Traktuj jako niedostępny, jeśli zależności systemowe nie są spełnione

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None # Obsłuż brak bibliotek

try:
    import markdown
    from bs4 import BeautifulSoup
except ImportError:
    markdown = None
    BeautifulSoup = None # Obsłuż brak bibliotek

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stałe (można przenieść do konfiguracji)
MAX_DOCUMENT_CHARS = 4000 # Maksymalna liczba znaków zwracana z pliku
MAX_PDF_SIZE_MB = 10  # Maksymalny rozmiar pliku PDF w MB

# --- Funkcje Przetwarzania Plików ---

def _run_ocr_on_pdf(input_pdf_path: str, output_pdf_path: str) -> bool:
    """Uruchamia OCR na pliku PDF za pomocą ocrmypdf."""
    if not ocrmypdf:
        logger.warning("Biblioteka ocrmypdf nie jest dostępna. Pomijanie OCR dla PDF.")
        return False
    try:
        logger.info(f"Uruchamianie OCR na pliku PDF: {input_pdf_path}")
        # Używamy języków angielskiego i polskiego, wymuszamy OCR
        result = ocrmypdf.ocr(input_pdf_path, output_pdf_path, language='eng+pol', force_ocr=True, progress_bar=False)
        if result == 0: # ocrmypdf zwraca 0 przy sukcesie
             logger.info(f"OCR zakończony pomyślnie dla: {input_pdf_path}")
             return True
        else:
             logger.error(f"ocrmypdf zakończył działanie z kodem błędu {result} dla pliku {input_pdf_path}")
             return False
    except ocrmypdf.exceptions.TesseractNotFoundError:
         logger.error("Tesseract OCR nie znaleziony przez ocrmypdf. Upewnij się, że jest zainstalowany i w PATH.")
         raise RuntimeError("Tesseract OCR nie znaleziony przez ocrmypdf.")
    except Exception as ocr_e:
        logger.error(f"Błąd podczas wykonywania OCR na PDF {input_pdf_path}: {ocr_e}", exc_info=True)
        return False # Zwróć False, aby spróbować ekstrakcji bez OCR

def safe_extract_text_from_pdf(pdf_data: bytes) -> str:
    """Bezpieczna ekstrakcja tekstu z pliku PDF używając PyMuPDF, z fallbackiem do OCR."""
    if not fitz:
        raise RuntimeError("Biblioteka PyMuPDF (fitz) nie jest zainstalowana. Uruchom 'pip install PyMuPDF'.")

    text = ""
    temp_input_path = None
    temp_output_path = None

    try:
        # Sprawdź rozmiar pliku
        file_size_mb = len(pdf_data) / (1024 * 1024)
        if file_size_mb > MAX_PDF_SIZE_MB:
            raise ValueError(f"Plik PDF jest zbyt duży. Maksymalny rozmiar to {MAX_PDF_SIZE_MB} MB.")

        # 1. Spróbuj ekstrakcji tekstu za pomocą PyMuPDF
        try:
            with fitz.open(stream=pdf_data, filetype="pdf") as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text") # Ekstrahuj czysty tekst
                    if page_text:
                        text += page_text + "\n\n"
            logger.info(f"PyMuPDF: Wyekstrahowano {len(text)} znaków tekstu.")
        except Exception as fitz_e:
             logger.warning(f"Błąd podczas ekstrakcji tekstu przez PyMuPDF: {fitz_e}. Próba OCR...")
             text = "" # Zresetuj tekst, jeśli PyMuPDF zawiódł

        # 2. Jeśli tekst jest pusty lub niewystarczający, spróbuj OCR z ocrmypdf
        if not text.strip() and ocrmypdf:
            logger.warning("Tekst z PyMuPDF jest pusty/niewystarczający. Próba OCR z ocrmypdf...")
            try:
                # Zapisz dane do tymczasowego pliku wejściowego
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_in:
                    temp_in.write(pdf_data)
                    temp_input_path = temp_in.name

                # Utwórz ścieżkę dla tymczasowego pliku wyjściowego
                temp_output_fd, temp_output_path = tempfile.mkstemp(suffix=".pdf")
                os.close(temp_output_fd) # Zamknij deskryptor pliku

                # Uruchom OCR
                ocr_success = _run_ocr_on_pdf(temp_input_path, temp_output_path)

                if ocr_success and os.path.exists(temp_output_path):
                    # Odczytaj tekst z pliku przetworzonego przez OCR za pomocą PyMuPDF
                    text = "" # Zresetuj tekst
                    with fitz.open(temp_output_path) as doc_ocr:
                        for page_num in range(len(doc_ocr)):
                            page = doc_ocr.load_page(page_num)
                            page_text = page.get_text("text")
                            if page_text:
                                text += page_text + "\n\n"
                    logger.info(f"OCR: Wyekstrahowano {len(text)} znaków tekstu po OCR.")
                else:
                     logger.error(f"OCR nie powiodło się lub plik wyjściowy nie istnieje: {temp_output_path}")
                     # Jeśli OCR zawiedzie, nadal możemy zwrócić pusty tekst lub rzucić błąd
                     # Na razie zwrócimy pusty tekst
                     text = ""

            except Exception as ocr_pipeline_e:
                 logger.error(f"Błąd w potoku OCR dla PDF: {ocr_pipeline_e}", exc_info=True)
                 text = "" # Zwróć pusty tekst w razie błędu OCR
            finally:
                 # Posprzątaj pliki tymczasowe
                 if temp_input_path and os.path.exists(temp_input_path):
                     try: os.unlink(temp_input_path)
                     except OSError: logger.warning(f"Nie udało się usunąć pliku tymczasowego: {temp_input_path}")
                 if temp_output_path and os.path.exists(temp_output_path):
                     try: os.unlink(temp_output_path)
                     except OSError: logger.warning(f"Nie udało się usunąć pliku tymczasowego: {temp_output_path}")

        # Ostateczne sprawdzenie, czy mamy jakiś tekst
        if not text.strip():
            logger.warning("Nie udało się wyekstrahować tekstu z PDF ani za pomocą PyMuPDF, ani OCR.")
            # Można rzucić błąd, jeśli brak tekstu jest niedopuszczalny
            # raise ValueError("Nie udało się wyekstrahować tekstu z pliku PDF.")

        return text.strip()

    except Exception as e:
        logger.error(f"Nieoczekiwany błąd podczas przetwarzania PDF: {e}", exc_info=True)
        raise ValueError(f"Błąd podczas przetwarzania pliku PDF: {e}") from e

def safe_extract_text_from_image(image_data: bytes) -> str:
    """Bezpieczna ekstrakcja tekstu z obrazu (OCR). Rzuca wyjątek."""
    if not Image or not pytesseract:
        raise RuntimeError("Biblioteki Pillow i/lub pytesseract nie są zainstalowane. Uruchom 'pip install Pillow pytesseract'.")

    text = ""
    suffix = '.png' # Domyślny
    temp_path = None

    try:
        # Sprawdź format obrazu, aby użyć poprawnego rozszerzenia dla pliku tymczasowego
        try:
            img_check = Image.open(io.BytesIO(image_data))
            if img_check.format:
                suffix = f'.{img_check.format.lower()}'
        except Exception:
            logger.warning("Nie udało się określić formatu obrazu, używam domyślnego .png")

        # Zapisz dane do pliku tymczasowego
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name

        # Wykonaj OCR
        image = Image.open(temp_path)
        # Upewnij się, że ścieżka do Tesseract jest ustawiona (można to zrobić globalnie)
        # if os.getenv('TESSERACT_CMD'): pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD')
        text = pytesseract.image_to_string(image, lang='eng+pol') # Dodano polski
        logger.info(f"Pomyślnie wykonano OCR dla obrazu (rozmiar: {len(image_data)} B).")

    except pytesseract.TesseractNotFoundError:
         logger.error("Tesseract OCR nie jest zainstalowany lub nie znajduje się w ścieżce systemowej (PATH).")
         raise RuntimeError("Tesseract OCR nie jest zainstalowany lub nie znajduje się w ścieżce systemowej (PATH).")
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania obrazu przez OCR: {e}", exc_info=True)
        raise ValueError(f"Błąd podczas przetwarzania obrazu przez OCR: {e}") from e
    finally:
        # Usuń plik tymczasowy
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError as unlink_e:
                logger.warning(f"Nie udało się usunąć pliku tymczasowego OCR: {temp_path}. Błąd: {unlink_e}")
    return text

def safe_extract_text_from_markdown(md_data: bytes) -> str:
    """Konwertuje Markdown na czysty tekst. Rzuca wyjątek."""
    if not markdown or not BeautifulSoup:
         raise RuntimeError("Biblioteki Markdown i/lub beautifulsoup4 nie są zainstalowane.")
    try:
        md_text = md_data.decode('utf-8') # Zakładamy UTF-8 dla Markdown
        html = markdown.markdown(md_text)
        # Użyj html.parser jako parsera, jest wbudowany
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        logger.error(f"Błąd przetwarzania pliku Markdown: {e}", exc_info=True)
        raise ValueError(f"Błąd podczas przetwarzania pliku Markdown: {e}") from e

def safe_extract_text_from_txt(txt_data: bytes) -> str:
    """Bezpieczne odczytanie tekstu z danych TXT. Rzuca wyjątek."""
    encodings_to_try = ['utf-8', 'latin-1', 'cp1250', 'cp1252'] # Lista kodowań do sprawdzenia
    for encoding in encodings_to_try:
        try:
            return txt_data.decode(encoding)
        except UnicodeDecodeError:
            continue # Spróbuj następnego kodowania
        except Exception as e:
             logger.error(f"Nieoczekiwany błąd podczas dekodowania TXT jako {encoding}: {e}", exc_info=True)
             raise ValueError(f"Błąd podczas odczytu pliku tekstowego: {e}") from e # Rzuć błąd, jeśli nie jest to UnicodeDecodeError

    # Jeśli żadne kodowanie nie zadziałało
    logger.error("Nie udało się zdekodować pliku tekstowego przy użyciu standardowych kodowań.")
    raise ValueError(f"Nie udało się zdekodować pliku tekstowego (próbowano: {', '.join(encodings_to_try)}).")


def process_uploaded_file_data(filename: str, file_data_base64: str) -> str:
    """
    Przetwarza przesłany plik (zakodowany w base64) na podstawie jego typu.
    Zwraca wyekstrahowany tekst lub rzuca wyjątek.
    """
    try:
        file_data = base64.b64decode(file_data_base64)
        filename_lower = filename.lower()
        logger.info(f"Przetwarzanie pliku: {filename} (rozmiar: {len(file_data)} B)")

        content = ""
        if filename_lower.endswith('.pdf'):
            content = safe_extract_text_from_pdf(file_data)
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')): # Rozszerzono listę obrazów
            content = safe_extract_text_from_image(file_data)
        elif filename_lower.endswith('.md'):
            content = safe_extract_text_from_markdown(file_data)
        elif filename_lower.endswith('.txt'):
            content = safe_extract_text_from_txt(file_data)
        # Można dodać obsługę innych typów, np. .html, .docx, .pptx (wymaga dodatkowych bibliotek)
        else:
            logger.warning(f"Nieobsługiwany typ pliku: {filename}")
            raise ValueError(f"Nieobsługiwany typ pliku: {os.path.splitext(filename)[1]}")

        # Ogranicz długość zwracanego contentu
        if len(content) > MAX_DOCUMENT_CHARS:
             logger.info(f"Skrócono zawartość pliku {filename} do {MAX_DOCUMENT_CHARS} znaków.")
             return content[:MAX_DOCUMENT_CHARS] + "... (skrócono)"
        else:
             return content

    except (ValueError, RuntimeError) as e:
        logger.error(f"Błąd przetwarzania pliku {filename}: {e}")
        # Rzucamy wyjątek dalej, aby obsłużyć go w routerze
        raise e
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd w process_uploaded_file_data dla {filename}: {e}", exc_info=True)
        # Rzucamy ogólny błąd
        raise RuntimeError("Wystąpił nieoczekiwany błąd serwera podczas przetwarzania pliku.") from e
