# AI Agent - Pixel Pasta (trippleCheck)

Prosta aplikacja webowa Flask, która wykorzystuje potok modeli AI (analiza, generowanie perspektywy, weryfikacja, synteza) do odpowiadania na zapytania użytkownika, z możliwością dodania plików tekstowych lub obrazów jako kontekstu.

## Funkcjonalności

*   Przetwarzanie zapytań w języku naturalnym.
*   Obsługa przesyłania plików `.txt`, `.md`, `.jpg`, `.png` jako dodatkowego kontekstu (OCR dla obrazów).
*   Wykorzystanie modeli AI z OpenRouter i Google Gemini API.
*   4-etapowy potok przetwarzania:
    1.  **Analiza:** Zrozumienie zapytania i kontekstu.
    2.  **Generowanie Perspektywy:** Stworzenie odpowiedzi przez wybrany model.
    3.  **Weryfikacja:** Ocena wygenerowanej perspektywy.
    4.  **Synteza:** Stworzenie finalnej, spójnej odpowiedzi.
*   Interfejs użytkownika w stylu pixel art.

## Konfiguracja Lokalna

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/makaronz/trippleCheck.git
    cd trippleCheck
    ```
2.  **Utwórz i aktywuj środowisko wirtualne (zalecane):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Skonfiguruj zmienne środowiskowe:**
    *   Utwórz plik `.env` w głównym katalogu projektu.
    *   Dodaj do niego następujące klucze API:
        ```dotenv
        SECRET_KEY=wygeneruj_losowy_sekretny_klucz
        OPENAI_API_KEY=twoj_klucz_openai_api
        GOOGLE_API_KEY=twoj_klucz_google_gemini_api
        ```
    *   Zastąp wartości swoimi kluczami. `SECRET_KEY` może być dowolnym losowym ciągiem znaków.
5.  **(Opcjonalnie) Zainstaluj Tesseract OCR:**
    *   Jeśli chcesz przetwarzać pliki obrazów (`.jpg`, `.png`), musisz zainstalować Tesseract OCR: [Instrukcje instalacji Tesseract](https://github.com/tesseract-ocr/tesseract#installing-tesseract).
    *   Upewnij się, że Tesseract jest dodany do zmiennej środowiskowej `PATH` Twojego systemu, lub ustaw zmienną `TESSERACT_CMD` w pliku `.env`, wskazującą na plik wykonywalny Tesseracta.
6.  **Uruchom aplikację:**
    ```bash
    python run.py
    ```
    Aplikacja będzie dostępna pod adresem `http://127.0.0.1:5000`.

## Wdrożenie

Aplikacja jest skonfigurowana do wdrożenia na platformie [Render](https://render.com/).

*   **Serwer produkcyjny:** Gunicorn
*   **Plik konfiguracyjny:** `Procfile` (`web: gunicorn "app:create_app()"`)
*   **Zależności:** `requirements.txt`
*   **Zmienne środowiskowe na Render:** Należy ustawić `SECRET_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` (oraz opcjonalnie `PYTHON_VERSION` i `TESSERACT_CMD`, jeśli jest potrzebny).

Po wypchnięciu zmian do gałęzi `main` na GitHubie, Render powinien automatycznie (jeśli tak skonfigurowano) lub manualnie (przez "Deploy latest commit") rozpocząć proces wdrażania.
