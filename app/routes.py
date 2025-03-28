# -*- coding: utf-8 -*-
import traceback
import json
import os  # Do obsługi zmiennych środowiskowych
from flask import request, render_template, jsonify, current_app, Blueprint
import pytesseract

# Importy z lokalnych modułów
from .utils import process_uploaded_file, call_openrouter_api, call_google_gemini_api, MAX_DOCUMENT_CHARS
from .prompts import (
    QUERY_ANALYSIS_PROMPT_V2,
    RESPONSE_GENERATION_PROMPT_V2,
    VERIFICATION_PROMPT_V2,
    SYNTHESIS_PROMPT_V2
)

# Tworzymy Blueprint
main_bp = Blueprint('main', __name__, template_folder='templates', static_folder='static')

# --- STAŁE KONFIGURACYJNE (Lepsze niż w środku funkcji) ---
# Domyślne modele, jeśli analiza zawiedzie lub nie zwróci sugestii
# Zaktualizowano zgodnie z nowymi wytycznymi
DEFAULT_PERSPECTIVE_MODELS = [
    {"model_id": "google/gemini-flash-1.5", "reason": "Szybki i wszechstronny model domyślny."},
    {"model_id": "anthropic/claude-3-haiku", "reason": "Alternatywny, szybki model domyślny."},
    {"model_id": "mistralai/mistral-7b-instruct", "reason": "Lekki model open-source jako trzecia opcja."},
]
MAX_PERSPECTIVES = 1 # Zmieniono na 1 zgodnie z nowymi wytycznymi

# Modele używane w stałych krokach - ZAKTUALIZOWANO
ANALYSIS_MODEL = "openai/gpt-4o" # Model do analizy
PERSPECTIVE_MODEL = "google/gemini-2.5-pro-exp-03-25:free" # Model do generowania perspektyw
VERIFICATION_MODEL = "deepseek/deepseek-chat:free" # Model do weryfikacji
SYNTHESIS_MODEL_ID = "gemini-pro" # Model do syntezy (używamy Gemini Pro 1.0 przez API Google)

# Klucze API - Pobierane ze zmiennych środowiskowych
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Usunięto - niepotrzebne przy użyciu OpenRouter
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Upewnij się, że ten klucz jest w .env

@main_bp.route('/')
def index():
    """Serwuje główną stronę aplikacji."""
    return render_template('index.html')

@main_bp.route('/process_file', methods=['POST'])
def process_file_endpoint():
    """Endpoint do przetwarzania pojedynczego pliku."""
    data = None
    try:
        data = request.json
        if not data or 'filename' not in data or 'file_data_base64' not in data:
             return jsonify({"error": "Nieprawidłowe dane wejściowe."}), 400
        filename = data['filename']
        file_data_base64 = data['file_data_base64']
        content = process_uploaded_file(filename, file_data_base64)
        return jsonify({"content": content})
    except (ValueError, RuntimeError, pytesseract.TesseractNotFoundError) as e:
        filename_log = data.get('filename', 'N/A') if data else 'N/A'
        current_app.logger.error(f"Błąd przetwarzania pliku {filename_log}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Nieoczekiwany błąd w /process_file: {traceback.format_exc()}")
        return jsonify({"error": "Wystąpił nieoczekiwany błąd serwera podczas przetwarzania pliku."}), 500

@main_bp.route('/process_query', methods=['POST'])
def process_query_endpoint():
    """Główny endpoint przetwarzania zapytania przez pipeline AI."""
    try:
        # Pobranie klucza OpenRouter z żądania
        data = request.json
        if not data or 'query' not in data or 'api_key' not in data:
             current_app.logger.warning("Otrzymano niekompletne żądanie do /process_query")
             return jsonify({"error": "Brak zapytania lub klucza API (OpenRouter) w żądaniu."}), 400

        query = data['query']
        openrouter_api_key = data['api_key'] # Klucz OpenRouter od użytkownika
        documents = data.get('documents', [])

        if not openrouter_api_key:
             return jsonify({"error": "Klucz API (OpenRouter) nie może być pusty."}), 400
        # --- Koniec walidacji i pobierania kluczy ---


        # --- Przygotowanie Danych dla Modeli ---
        documents_summary = "Brak dodatkowych dokumentów."
        documents_content = "Brak dodatkowych dokumentów."
        if documents:
            summaries = [f"Dokument {i+1}: {doc.get('name', 'N/A')} (początek: {doc.get('content', '')[:100]}...)"
                         for i, doc in enumerate(documents) if isinstance(doc, dict)]
            if summaries: documents_summary = "\n".join(summaries)

            contents = []
            for i, doc in enumerate(documents):
                 if isinstance(doc, dict):
                    doc_content = doc.get('content', '')
                    limited_content = doc_content[:MAX_DOCUMENT_CHARS]
                    if len(doc_content) > MAX_DOCUMENT_CHARS: limited_content += "... (dokument skrócony)"
                    contents.append(f"--- START Document {i+1}: {doc.get('name', 'N/A')} ---\n{limited_content}\n--- END Document {i+1} ---")
            if contents: documents_content = "\n\n".join(contents)
        # --- Koniec Przygotowania Danych ---


        # --- Krok 1: Analiza Zapytania ---
        current_app.logger.info(f"Krok 1: Analiza zapytania (model: {ANALYSIS_MODEL})...")
        analysis_prompt = QUERY_ANALYSIS_PROMPT_V2.format(
            query=query,
            documents_summary=documents_summary
        )
        analysis_raw = "{}" # Domyślna pusta odpowiedź
        try:
            # Używamy klucza OpenRouter podanego przez użytkownika w UI
            analysis_raw = call_openrouter_api(
                api_key=openrouter_api_key, # Poprawiono: Użyj klucza OpenRouter z UI
                model=ANALYSIS_MODEL,
                prompt_content=analysis_prompt
            )
            current_app.logger.info("Analiza zakończona.")
        except Exception as e:
            current_app.logger.error(f"Błąd podczas kroku analizy (model: {ANALYSIS_MODEL}): {e}", exc_info=True)
            analysis_raw = f'{{"error": "Błąd podczas analizy: {e}"}}' # Zwróć błąd jako JSON string


        # --- Parsowanie Wyników Analizy (niepotrzebne do wyboru modeli perspektyw) ---
        analysis_json = None
        try:
            analysis_cleaned = analysis_raw.strip().removeprefix("```json").removesuffix("```").strip()
            if analysis_cleaned:
                analysis_json = json.loads(analysis_cleaned)
        except Exception as e:
            current_app.logger.warning(f"Nie udało się sparsować JSON z analizy: {e}. Surowa odpowiedź: '{analysis_raw[:200]}...'")
        # --- Koniec Parsowania ---


        # --- Krok 2: Generowanie Perspektywy ---
        current_app.logger.info(f"Krok 2: Generowanie perspektywy (model: {PERSPECTIVE_MODEL})...")
        perspectives_results = []
        specialization = "Zaawansowane rozumowanie i generowanie" # Można dostosować
        perspective_prompt = None # Reset
        try:
            perspective_prompt = RESPONSE_GENERATION_PROMPT_V2.format(
                model_name=PERSPECTIVE_MODEL,
                specialization=specialization,
                query=query,
                analysis=analysis_raw, # Przekaż surową analizę
                documents_content=documents_content
            )
            # Używamy klucza OpenRouter z UI dla Gemini Free
            response = call_openrouter_api(
                api_key=openrouter_api_key,
                model=PERSPECTIVE_MODEL,
                prompt_content=perspective_prompt
            )
            perspectives_results.append({
                "model": PERSPECTIVE_MODEL,
                "specialization": specialization,
                "response": response,
                "prompt": perspective_prompt
            })
            current_app.logger.info(f"  - Generowanie perspektywy (model: {PERSPECTIVE_MODEL}) zakończone.")
        except Exception as e:
             current_app.logger.error(f"  - Błąd generowania przez {PERSPECTIVE_MODEL}: {e}", exc_info=True)
             perspectives_results.append({
                "model": PERSPECTIVE_MODEL,
                "specialization": specialization,
                "response": f"BŁĄD: Nie udało się wygenerować odpowiedzi przez model {PERSPECTIVE_MODEL}.\nSzczegóły: {e}",
                "prompt": perspective_prompt if perspective_prompt else "Błąd przed formatowaniem promptu"
             })
        current_app.logger.info("Generowanie perspektywy zakończone.")
        # --- Koniec Generowania Perspektywy ---


        # --- Krok 3: Weryfikacja Odpowiedzi ---
        current_app.logger.info(f"Krok 3: Weryfikacja odpowiedzi (model: {VERIFICATION_MODEL})...")
        verification_prompt = None # Reset
        verification_report = f"BŁĄD: Nie udało się przeprowadzić weryfikacji." # Domyślny błąd

        # Sprawdzamy, czy mamy perspektywę do weryfikacji
        if perspectives_results:
            perspective_to_verify = perspectives_results[0] # Bierzemy pierwszą (i jedyną) perspektywę
            try:
                verification_args = {
                    'query': query,
                    'model_name': perspective_to_verify.get('model', 'N/A'),
                    'model_spec': perspective_to_verify.get('specialization', 'N/A'),
                    'perspective_response': perspective_to_verify.get('response', 'Brak')
                }
                verification_prompt = VERIFICATION_PROMPT_V2.format(**verification_args)

                # Używamy klucza OpenRouter z UI dla Deepseek Free
                verification_report = call_openrouter_api(
                    api_key=openrouter_api_key,
                    model=VERIFICATION_MODEL,
                    prompt_content=verification_prompt
                )
                current_app.logger.info("Weryfikacja zakończona.")
            except Exception as e:
                 current_app.logger.error(f"Błąd podczas kroku weryfikacji (model: {VERIFICATION_MODEL}): {e}", exc_info=True)
                 verification_prompt = verification_prompt if verification_prompt else "Błąd formatowania promptu weryfikacji"
                 verification_report = f"BŁĄD: Nie udało się przeprowadzić weryfikacji.\nSzczegóły: {e}"
        else:
            current_app.logger.warning("Krok 3: Pominięto weryfikację - brak perspektyw do weryfikacji.")
            verification_report = "Pominięto - brak perspektywy do weryfikacji."
            verification_prompt = "Pominięto - brak perspektywy do weryfikacji."
        # --- Koniec Weryfikacji ---


        # --- Krok 4: Synteza i Konkluzja ---
        current_app.logger.info(f"Krok 4: Synteza odpowiedzi końcowej (model: {SYNTHESIS_MODEL_ID})...")
        synthesis_prompt = None # Reset
        final_response = f"BŁĄD: Nie udało się przeprowadzić syntezy odpowiedzi." # Domyślny błąd
        try:
            # Przygotuj podsumowanie perspektyw (teraz tylko jednej)
            perspectives_summary_for_prompt = "Brak perspektyw do podsumowania."
            if perspectives_results:
                 p = perspectives_results[0]
                 perspectives_summary_for_prompt = f"--- START PERSPECTIVE ({p.get('model', 'N/A')} - {p.get('specialization', 'N/A')}) ---\n{p.get('response', 'Brak')}\n--- END PERSPECTIVE ---"

            synthesis_prompt = SYNTHESIS_PROMPT_V2.format(
                    query=query,
                    perspectives_summary=perspectives_summary_for_prompt,
                    verification_report=verification_report
                )
            # Używamy dedykowanej funkcji dla API Google z kluczem z env
            if not GOOGLE_API_KEY:
                 raise ValueError("Brak klucza GOOGLE_API_KEY w konfiguracji środowiska.")
            final_response = call_google_gemini_api(
                api_key=GOOGLE_API_KEY, # Używamy klucza Google z env
                model=SYNTHESIS_MODEL_ID,
                prompt_content=synthesis_prompt
            )
            current_app.logger.info("Synteza zakończona.")
        except Exception as e:
            current_app.logger.error(f"Błąd podczas kroku syntezy (model: {SYNTHESIS_MODEL_ID}): {e}", exc_info=True)
            synthesis_prompt = synthesis_prompt if synthesis_prompt else "Błąd formatowania promptu syntezy"
            final_response = f"BŁĄD: Nie udało się przeprowadzić syntezy odpowiedzi.\nSzczegóły: {e}"
        # --- Koniec Syntezy ---


        # --- Zwrócenie Wyników ---
        return jsonify({
            # Analiza
            "analysis_raw": analysis_raw, # Surowa odpowiedź
            "analysis_json": analysis_json, # Sparsowana odpowiedź (może być None)
            "analysis_model": ANALYSIS_MODEL,
            "analysis_prompt": analysis_prompt,
            # Usunięto selected_perspective_models, bo jest stały

            # Perspektywy (rzeczywiste wyniki, bez późniejszego paddingu)
            "perspectives": perspectives_results, # Zwracamy listę (nawet jeśli 1 element)

            # Weryfikacja
            "verification": verification_report,
            "verification_model": VERIFICATION_MODEL,
            "verification_prompt": verification_prompt,

            # Synteza
            "final_response": final_response,
            "synthesis_model": SYNTHESIS_MODEL_ID,
            "synthesis_prompt": synthesis_prompt
        })
        # --- Koniec Zwracania Wyników ---

    except (ValueError, RuntimeError) as e:
         current_app.logger.error(f"Kontrolowany błąd przetwarzania zapytania: {e}", exc_info=True)
         return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Nieoczekiwany błąd w /process_query: {traceback.format_exc()}")
        return jsonify({"error": "Wystąpił krytyczny, nieoczekiwany błąd serwera podczas przetwarzania zapytania."}), 500
