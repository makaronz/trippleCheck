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
    VERIFICATION_SYNTHESIS_PROMPT # Zmieniono import
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
ANALYSIS_MODEL = "anthropic/claude-3-haiku" # Bardziej niezawodny model do analizy JSON
PERSPECTIVE_MODEL_1 = "google/gemini-2.0-flash-001" # Model 1 z dostępem do internetu (Gemini 2)
PERSPECTIVE_MODEL_2 = "anthropic/claude-3-sonnet" # Model 2 z dostępem do internetu (inny model)
VERIFICATION_SYNTHESIS_MODEL = "openai/gpt-4o" # Model do weryfikacji i syntezy
MAX_PERSPECTIVES = 2 # Przywrócono 2 perspektywy

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
        current_app.logger.info(f"Krok 1/4: Analiza zapytania (model: {ANALYSIS_MODEL})...")
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
            # Próba znalezienia JSON w odpowiedzi
            json_start = analysis_raw.find("```json")
            json_end = analysis_raw.rfind("```")
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                # Wytnij JSON z odpowiedzi
                analysis_cleaned = analysis_raw[json_start + 7:json_end].strip()
            else:
                # Jeśli nie ma znaczników, spróbuj całą odpowiedź
                analysis_cleaned = analysis_raw.strip()
            
            # Próba znalezienia obiektu JSON w tekście
            start_brace = analysis_cleaned.find('{')
            end_brace = analysis_cleaned.rfind('}')
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                analysis_cleaned = analysis_cleaned[start_brace:end_brace+1]
            
            if analysis_cleaned:
                analysis_json = json.loads(analysis_cleaned)
                current_app.logger.info(f"Pomyślnie sparsowano JSON z analizy: {analysis_json}")
            else:
                current_app.logger.warning("Pusta odpowiedź analizy po czyszczeniu.")
        except Exception as e:
            current_app.logger.warning(f"Nie udało się sparsować JSON z analizy: {e}. Surowa odpowiedź: '{analysis_raw[:200]}...'")
            # Utwórz domyślny JSON w przypadku błędu
            analysis_json = {
                "main_topics": ["unknown"],
                "user_intent": "unknown",
                "complexity": "medium",
                "analysis_summary": "Nie udało się przeprowadzić analizy."
            }
        # --- Koniec Parsowania ---


        # --- Krok 2: Generowanie Perspektyw ---
        current_app.logger.info(f"Krok 2/4: Generowanie perspektyw (modele: {PERSPECTIVE_MODEL_1}, {PERSPECTIVE_MODEL_2})...")
        perspectives_results = []
        
        # Generowanie pierwszej perspektywy
        current_app.logger.info(f"  - Generowanie perspektywy 1 (model: {PERSPECTIVE_MODEL_1})...")
        specialization_1 = "Zaawansowane rozumowanie i wyszukiwanie informacji" # Dostosowano
        perspective_prompt_1 = None # Reset
        try:
            perspective_prompt_1 = RESPONSE_GENERATION_PROMPT_V2.format(
                model_name=PERSPECTIVE_MODEL_1,
                specialization=specialization_1,
                query=query,
                analysis=analysis_raw, # Przekaż surową analizę
                documents_content=documents_content
            )
            # Używamy klucza OpenRouter z UI
            response_1 = call_openrouter_api(
                api_key=openrouter_api_key,
                model=PERSPECTIVE_MODEL_1,
                prompt_content=perspective_prompt_1
            )
            perspectives_results.append({
                "model": PERSPECTIVE_MODEL_1,
                "specialization": specialization_1,
                "response": response_1,
                "prompt": perspective_prompt_1
            })
            current_app.logger.info(f"  - Generowanie perspektywy 1 (model: {PERSPECTIVE_MODEL_1}) zakończone.")
        except Exception as e:
             current_app.logger.error(f"  - Błąd generowania przez {PERSPECTIVE_MODEL_1}: {e}", exc_info=True)
             perspectives_results.append({
                "model": PERSPECTIVE_MODEL_1,
                "specialization": specialization_1,
                "response": f"BŁĄD: Nie udało się wygenerować odpowiedzi przez model {PERSPECTIVE_MODEL_1}.\nSzczegóły: {e}",
                "prompt": perspective_prompt_1 if perspective_prompt_1 else "Błąd przed formatowaniem promptu"
             })
        
        # Generowanie drugiej perspektywy
        current_app.logger.info(f"  - Generowanie perspektywy 2 (model: {PERSPECTIVE_MODEL_2})...")
        specialization_2 = "Dogłębna analiza i krytyczne myślenie" # Dostosowano
        perspective_prompt_2 = None # Reset
        try:
            perspective_prompt_2 = RESPONSE_GENERATION_PROMPT_V2.format(
                model_name=PERSPECTIVE_MODEL_2,
                specialization=specialization_2,
                query=query,
                analysis=analysis_raw, # Przekaż surową analizę
                documents_content=documents_content
            )
            # Używamy klucza OpenRouter z UI
            response_2 = call_openrouter_api(
                api_key=openrouter_api_key,
                model=PERSPECTIVE_MODEL_2,
                prompt_content=perspective_prompt_2
            )
            perspectives_results.append({
                "model": PERSPECTIVE_MODEL_2,
                "specialization": specialization_2,
                "response": response_2,
                "prompt": perspective_prompt_2
            })
            current_app.logger.info(f"  - Generowanie perspektywy 2 (model: {PERSPECTIVE_MODEL_2}) zakończone.")
        except Exception as e:
             current_app.logger.error(f"  - Błąd generowania przez {PERSPECTIVE_MODEL_2}: {e}", exc_info=True)
             perspectives_results.append({
                "model": PERSPECTIVE_MODEL_2,
                "specialization": specialization_2,
                "response": f"BŁĄD: Nie udało się wygenerować odpowiedzi przez model {PERSPECTIVE_MODEL_2}.\nSzczegóły: {e}",
                "prompt": perspective_prompt_2 if perspective_prompt_2 else "Błąd przed formatowaniem promptu"
             })
        
        current_app.logger.info(f"Generowanie perspektyw zakończone. Uzyskano {len(perspectives_results)} perspektyw.")
        # --- Koniec Generowania Perspektyw ---


        # --- Krok 3: Weryfikacja i Synteza ---
        current_app.logger.info(f"Krok 3/3: Weryfikacja i Synteza (model: {VERIFICATION_SYNTHESIS_MODEL})...")
        verification_synthesis_prompt = None # Reset
        verification_synthesis_response = f"BŁĄD: Nie udało się przeprowadzić weryfikacji i syntezy." # Domyślny błąd

        # Sprawdzamy, czy mamy obie perspektywy
        if len(perspectives_results) == 2:
            p1 = perspectives_results[0]
            p2 = perspectives_results[1]
            try:
                verification_synthesis_args = {
                    'query': query,
                    'model_1_name': p1.get('model', 'N/A'),
                    'model_1_spec': p1.get('specialization', 'N/A'),
                    'perspective_1_response': p1.get('response', 'Brak'),
                    'model_2_name': p2.get('model', 'N/A'),
                    'model_2_spec': p2.get('specialization', 'N/A'),
                    'perspective_2_response': p2.get('response', 'Brak')
                }
                verification_synthesis_prompt = VERIFICATION_SYNTHESIS_PROMPT.format(**verification_synthesis_args)

                # Używamy klucza OpenRouter z UI
                verification_synthesis_response = call_openrouter_api(
                    api_key=openrouter_api_key,
                    model=VERIFICATION_SYNTHESIS_MODEL,
                    prompt_content=verification_synthesis_prompt
                )
                current_app.logger.info("Weryfikacja i Synteza zakończona.")
            except Exception as e:
                 current_app.logger.error(f"Błąd podczas kroku Weryfikacji i Syntezy (model: {VERIFICATION_SYNTHESIS_MODEL}): {e}", exc_info=True)
                 verification_synthesis_prompt = verification_synthesis_prompt if verification_synthesis_prompt else "Błąd formatowania promptu weryfikacji i syntezy"
                 verification_synthesis_response = f"BŁĄD: Nie udało się przeprowadzić weryfikacji i syntezy.\nSzczegóły: {e}"
        elif len(perspectives_results) < 2:
             current_app.logger.warning("Krok 3: Pominięto Weryfikację i Syntezę - nie wygenerowano obu perspektyw.")
             verification_synthesis_response = "Pominięto - nie wygenerowano obu perspektyw."
             verification_synthesis_prompt = "Pominięto - nie wygenerowano obu perspektyw."
        # --- Koniec Weryfikacji i Syntezy ---


        # --- Zwrócenie Wyników ---
        return jsonify({
            # Analiza
            "analysis_raw": analysis_raw,
            "analysis_json": analysis_json,
            "analysis_model": ANALYSIS_MODEL,
            "analysis_prompt": analysis_prompt,

            # Perspektywy
            "perspectives": perspectives_results,

            # Weryfikacja i Synteza
            "verification_synthesis_response": verification_synthesis_response,
            "verification_synthesis_model": VERIFICATION_SYNTHESIS_MODEL,
            "verification_synthesis_prompt": verification_synthesis_prompt
        })
        # --- Koniec Zwracania Wyników ---

    except (ValueError, RuntimeError) as e:
         current_app.logger.error(f"Kontrolowany błąd przetwarzania zapytania: {e}", exc_info=True)
         return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Nieoczekiwany błąd w /process_query: {traceback.format_exc()}")
        return jsonify({"error": "Wystąpił krytyczny, nieoczekiwany błąd serwera podczas przetwarzania zapytania."}), 500
