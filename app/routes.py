# -*- coding: utf-8 -*-
import traceback
import json
from flask import request, render_template, jsonify, current_app, Blueprint # Dodano Blueprint
import pytesseract # Import potrzebny do łapania wyjątku

# Usunięto import create_app - nie będzie już potrzebny w tym pliku
from .utils import process_uploaded_file, call_openrouter_api, MAX_DOCUMENT_CHARS
from .prompts import (
    QUERY_ANALYSIS_PROMPT_V2,
    RESPONSE_GENERATION_PROMPT_V2,
    VERIFICATION_PROMPT_V2,
    SYNTHESIS_PROMPT_V2
)

# Tworzymy Blueprint
main_bp = Blueprint('main', __name__, template_folder='templates', static_folder='static')


@main_bp.route('/') # Zmieniono dekorator na Blueprint
def index():
    """Serwuje główną stronę aplikacji."""
    # Używamy render_template zamiast render_template_string
    return render_template('index.html')

@main_bp.route('/process_file', methods=['POST']) # Zmieniono dekorator na Blueprint
def process_file_endpoint():
    """Endpoint do przetwarzania pojedynczego pliku przesłanego z frontendu."""
    data = None # Zdefiniuj data przed blokiem try
    try:
        data = request.json
        if not data or 'filename' not in data or 'file_data_base64' not in data:
             return jsonify({"error": "Nieprawidłowe dane wejściowe."}), 400

        filename = data['filename']
        file_data_base64 = data['file_data_base64']

        # Używamy funkcji z utils.py
        content = process_uploaded_file(filename, file_data_base64)

        return jsonify({"content": content})

    # Łapiemy konkretne wyjątki z utils.py
    except (ValueError, RuntimeError, pytesseract.TesseractNotFoundError) as e:
        # Logowanie błędu może być bardziej rozbudowane
        current_app.logger.error(f"Błąd przetwarzania pliku {data.get('filename', 'N/A') if data else 'N/A'}: {e}")
        return jsonify({"error": str(e)}), 400 # Bad Request lub inny odpowiedni kod
    except Exception as e:
        current_app.logger.error(f"Nieoczekiwany błąd w /process_file: {traceback.format_exc()}")
        return jsonify({"error": "Wystąpił nieoczekiwany błąd serwera podczas przetwarzania pliku."}), 500

@main_bp.route('/process_query', methods=['POST']) # Zmieniono dekorator na Blueprint
def process_query_endpoint():
    """Główny endpoint przetwarzania zapytania przez pipeline AI."""
    # Usunięto sprawdzanie klucza z konfiguracji serwera
    # if not current_app.config['OPENROUTER_API_KEY']:
    #     current_app.logger.error("Klucz API OpenRouter nie jest skonfigurowany na serwerze.")
    #     return jsonify({"error": "Klucz API OpenRouter nie jest skonfigurowany na serwerze."}), 500

    try:
        data = request.json
        if not data or 'query' not in data or 'api_key' not in data: # Sprawdź, czy klucz API jest w żądaniu
             return jsonify({"error": "Brak zapytania lub klucza API w żądaniu."}), 400

        query = data['query']
        api_key = data['api_key'] # Odczytaj klucz API z żądania
        documents = data.get('documents', []) # Oczekujemy listy {name: string, content: string}

        if not api_key:
             return jsonify({"error": "Klucz API nie może być pusty."}), 400

        # --- Przygotowanie danych dla modeli ---
        documents_summary = "Brak dodatkowych dokumentów."
        if documents:
            summaries = [
                f"Dokument {i+1}: {doc.get('name', 'N/A')} (początek: {doc.get('content', '')[:100]}...)"
                for i, doc in enumerate(documents) if isinstance(doc, dict)
            ]
            if summaries:
                documents_summary = "\n".join(summaries)

        documents_content = "Brak dodatkowych dokumentów."
        if documents:
            contents = []
            for i, doc in enumerate(documents):
                 if isinstance(doc, dict):
                    doc_content = doc.get('content', '')
                    limited_content = doc_content[:MAX_DOCUMENT_CHARS]
                    if len(doc_content) > MAX_DOCUMENT_CHARS:
                        limited_content += "... (dokument skrócony)"
                    contents.append(f"--- START Document {i+1}: {doc.get('name', 'N/A')} ---\n{limited_content}\n--- END Document {i+1} ---")
            if contents:
                documents_content = "\n\n".join(contents)

        # --- Krok 1: Analiza zapytania ---
        current_app.logger.info("Krok 1: Analiza zapytania...")
        analysis_raw = call_openrouter_api(
            api_key=api_key, # Przekaż klucz API
            model="mistralai/mistral-7b-instruct", # Darmowy model
            prompt_content=QUERY_ANALYSIS_PROMPT_V2.format(query=query, documents_summary=documents_summary)
        )
        current_app.logger.info("Analiza zakończona.")

        # Parsowanie JSON z analizy
        suggested_models_list = []
        try:
            analysis_cleaned = analysis_raw.strip()
            if analysis_cleaned.startswith("```json"):
                analysis_cleaned = analysis_cleaned[7:-3].strip()
            analysis_json = json.loads(analysis_cleaned)
            if isinstance(analysis_json.get('suggested_models'), list):
                 suggested_models_list = [m for m in analysis_json['suggested_models'] if isinstance(m, dict) and 'model_id' in m]
            else:
                 current_app.logger.warning("Klucz 'suggested_models' nie jest listą w odpowiedzi analizy.")
        except json.JSONDecodeError as e:
            current_app.logger.warning(f"Nie udało się sparsować JSON z analizy: {e}. Używam modeli domyślnych.")
        except Exception as e:
             current_app.logger.error(f"Nieoczekiwany błąd przy przetwarzaniu analizy JSON: {e}")

        # Domyślne darmowe modele, jeśli brak sugestii
        if not suggested_models_list:
            current_app.logger.info("Używanie domyślnych (darmowych) modeli do generowania perspektyw.")
            suggested_models_list = [
                {"model_id": "mistralai/mistral-7b-instruct", "reason": "Szybki, darmowy (domyślny)"},
                {"model_id": "google/gemma-7b-it", "reason": "Darmowy model Google (domyślny)"},
                {"model_id": "nousresearch/nous-hermes-2-mixtral-8x7b-dpo", "reason": "Zaawansowany darmowy model (domyślny)"}
            ]

        # --- Krok 2: Generowanie Wieloperspektywiczne ---
        models_to_use = suggested_models_list[:3]
        current_app.logger.info(f"Krok 2: Generowanie perspektyw (modele: {[m.get('model_id', 'N/A') for m in models_to_use]})...")
        perspectives_results = []

        # Uzupełnienie do 3 modeli, jeśli potrzeba
        if len(models_to_use) < 3:
            default_models_fallback = [
                {"model_id": "mistralai/mistral-7b-instruct", "reason": "Domyślny darmowy fallback"},
                {"model_id": "google/gemma-7b-it", "reason": "Domyślny darmowy fallback"},
                {"model_id": "nousresearch/nous-hermes-2-mixtral-8x7b-dpo", "reason": "Domyślny darmowy fallback"}
            ]
            needed = 3 - len(models_to_use)
            for dm in default_models_fallback:
                if needed == 0: break
                if not any(m.get('model_id') == dm['model_id'] for m in models_to_use):
                    models_to_use.append(dm)
                    needed -= 1

        for model_info in models_to_use:
            model_id = model_info.get('model_id', 'unknown-model')
            specialization = model_info.get('reason', 'N/A')
            current_app.logger.info(f"  - Generowanie przez: {model_id}")
            try:
                response = call_openrouter_api(
                    api_key=api_key, # Przekaż klucz API
                    model=model_id,
                    prompt_content=RESPONSE_GENERATION_PROMPT_V2.format(
                        model_name=model_id,
                        specialization=specialization,
                        query=query,
                        analysis=analysis_raw,
                        documents_content=documents_content
                    )
                )
                perspectives_results.append({"model": model_id, "specialization": specialization, "response": response})
            except Exception as e:
                 current_app.logger.error(f"  - Błąd generowania przez {model_id}: {e}")
                 perspectives_results.append({
                    "model": model_id,
                    "specialization": specialization,
                    "response": f"BŁĄD: Nie udało się wygenerować odpowiedzi przez ten model.\nSzczegóły: {e}"
                 })
        current_app.logger.info("Generowanie perspektyw zakończone.")

        # Uzupełnienie do 3 wyników, jeśli były błędy
        while len(perspectives_results) < 3:
            perspectives_results.append({"model": "N/A", "specialization": "N/A", "response": "Brak odpowiedzi."})

        perspectives_summary_for_prompt = "\n\n".join([
            f"--- START PERSPECTIVE {i+1} ({p['model']} - {p['specialization']}) ---\n{p['response']}\n--- END PERSPECTIVE {i+1} ---"
            for i, p in enumerate(perspectives_results[:3])
        ])

        # --- Krok 3: Weryfikacja Odpowiedzi ---
        current_app.logger.info("Krok 3: Weryfikacja odpowiedzi...")
        verification_report = call_openrouter_api(
            api_key=api_key, # Przekaż klucz API
            model="nousresearch/nous-hermes-2-mixtral-8x7b-dpo", # Darmowy model
            prompt_content=VERIFICATION_PROMPT_V2.format(
                query=query,
                model_1_name=perspectives_results[0]['model'],
                model_1_spec=perspectives_results[0]['specialization'],
                perspective_1_response=perspectives_results[0]['response'],
                model_2_name=perspectives_results[1]['model'],
                model_2_spec=perspectives_results[1]['specialization'],
                perspective_2_response=perspectives_results[1]['response'],
                model_3_name=perspectives_results[2]['model'],
                model_3_spec=perspectives_results[2]['specialization'],
                perspective_3_response=perspectives_results[2]['response']
            )
        )
        current_app.logger.info("Weryfikacja zakończona.")

        # --- Krok 4: Synteza i Konkluzja ---
        current_app.logger.info("Krok 4: Synteza odpowiedzi końcowej...")
        final_response = call_openrouter_api(
            api_key=api_key, # Przekaż klucz API
            model="nousresearch/nous-hermes-2-mixtral-8x7b-dpo", # Najlepszy darmowy
            prompt_content=SYNTHESIS_PROMPT_V2.format(
                query=query,
                perspectives_summary=perspectives_summary_for_prompt,
                verification_report=verification_report
            )
        )
        current_app.logger.info("Synteza zakończona.")

        # Zwróć wszystkie wyniki
        return jsonify({
            "analysis": analysis_raw,
            "perspectives": perspectives_results[:3],
            "verification": verification_report,
            "final_response": final_response
        })

    except (ValueError, RuntimeError) as e:
         current_app.logger.error(f"Błąd przetwarzania zapytania (kontrolowany): {e}")
         return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Nieoczekiwany błąd w /process_query: {traceback.format_exc()}")
        return jsonify({"error": "Wystąpił nieoczekiwany błąd serwera podczas przetwarzania zapytania."}), 500
