import asyncio
import json
import logging
import datetime
from typing import List, Dict, Any, Optional

from ..utils.openrouter_client import call_openrouter_api_async
from ..prompts import prompts
from ..models import schemas

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definicje modeli dla poszczególnych kroków (zgodnie z finalnym planem)
MODEL_CONFIG = {
    "analysis": "openchat/openchat-3.5-0106",
    "perspective_1": {
        "model": "meta-llama/llama-3-70b-instruct", # lub inny Llama
        "type": "Informative"
    },
    "perspective_2": {
        "model": "teknium/openhermes-2.5-mistral-7b", # Zmieniono model na OpenHermes
        "type": "Contrarian"
    },
    "perspective_3": {
        "model": "qwen/qwen-2.5-coder-32b-instruct:free", # Zmieniono model na Qwen Coder
        "type": "Complementary"
    },
    "verification_synthesis": "google/gemini-2.5-pro-exp-03-25:free" # lub dokładna nazwa
}

async def run_analysis_step(api_key: str, query: str, documents_summary: str) -> schemas.AnalysisResult:
    """Wykonuje krok analizy zapytania."""
    model = MODEL_CONFIG["analysis"]
    prompt = prompts.QUERY_ANALYSIS_PROMPT.format(
        query=query,
        documents_summary=documents_summary
    )
    raw_response = ""
    analysis_json = None
    error_message = None

    try:
        raw_response = await call_openrouter_api_async(api_key, model, prompt)
        # Próba sparsowania JSON z odpowiedzi
        try:
            json_start = raw_response.find("```json")
            json_end = raw_response.rfind("```")
            if json_start != -1 and json_end != -1:
                json_str = raw_response[json_start + 7:json_end].strip()
            else:
                 # Spróbuj znaleźć JSON bez znaczników
                 start_brace = raw_response.find('{')
                 end_brace = raw_response.rfind('}')
                 if start_brace != -1 and end_brace != -1:
                      json_str = raw_response[start_brace:end_brace+1]
                 else:
                      json_str = raw_response # Ostateczność

            if json_str:
                analysis_json = json.loads(json_str)
                logger.info(f"Pomyślnie sparsowano JSON z analizy: {analysis_json}")
            else:
                 logger.warning("Pusta odpowiedź analizy po próbie czyszczenia.")
                 error_message = "Model analizy zwrócił pustą odpowiedź."

        except json.JSONDecodeError as json_e:
            logger.warning(f"Nie udało się sparsować JSON z analizy: {json_e}. Surowa odpowiedź: '{raw_response[:200]}...'")
            error_message = f"Błąd parsowania JSON z analizy: {json_e}"
        except Exception as e:
             logger.error(f"Nieoczekiwany błąd podczas parsowania JSON analizy: {e}", exc_info=True)
             error_message = f"Nieoczekiwany błąd parsowania JSON: {e}"

    except Exception as e:
        logger.error(f"Błąd podczas kroku analizy (model: {model}): {e}", exc_info=True)
        error_message = f"Błąd wywołania API analizy: {e}"
        raw_response = f"BŁĄD: {error_message}" # Zapisz błąd w surowej odpowiedzi

    return schemas.AnalysisResult(
        model=model,
        prompt=prompt,
        result_json=analysis_json,
        raw_response=raw_response,
        error=error_message
    )

async def run_perspective_generation_step(
    api_key: str,
    query: str,
    analysis_result: schemas.AnalysisResult,
    documents_content: str
) -> List[schemas.PerspectiveResult]:
    """Wykonuje krok generowania perspektyw równolegle."""
    perspective_defs = [
        {"config": MODEL_CONFIG["perspective_1"], "prompt_template": prompts.INFORMATIVE_PERSPECTIVE_PROMPT},
        {"config": MODEL_CONFIG["perspective_2"], "prompt_template": prompts.CONTRARIAN_PERSPECTIVE_PROMPT},
        {"config": MODEL_CONFIG["perspective_3"], "prompt_template": prompts.COMPLEMENTARY_PERSPECTIVE_PROMPT},
    ]

    tasks = []
    analysis_summary = analysis_result.result_json.get("analysis_summary", "Analysis unavailable.") if analysis_result.result_json else "Analysis unavailable."

    for p_def in perspective_defs:
        model = p_def["config"]["model"]
        prompt = p_def["prompt_template"].format(
            model_name=model,
            query=query,
            documents_content=documents_content,
            analysis_summary=analysis_summary
            # Dodaj inne potrzebne zmienne, jeśli prompty ich wymagają
        )
        tasks.append(
            _call_perspective_model(
                api_key=api_key,
                model=model,
                prompt=prompt,
                perspective_type=p_def["config"]["type"]
            )
        )

    perspective_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Przetwarzanie wyników (obsługa wyjątków z gather)
    processed_results: List[schemas.PerspectiveResult] = []
    for i, result in enumerate(perspective_results):
        p_def = perspective_defs[i]
        if isinstance(result, Exception):
            logger.error(f"Wyjątek podczas generowania perspektywy {p_def['config']['type']} ({p_def['config']['model']}): {result}", exc_info=True)
            # Zwróć obiekt błędu
            processed_results.append(schemas.PerspectiveResult(
                type=p_def["config"]["type"],
                model=p_def["config"]["model"],
                prompt=p_def["prompt_template"].format(model_name=p_def["config"]["model"], query=query, documents_content="...", analysis_summary="..."), # Zapisz przybliżony prompt
                response=f"BŁĄD: {result}",
                error=str(result)
            ))
        elif isinstance(result, schemas.PerspectiveResult):
             processed_results.append(result)
        else:
             # Nieoczekiwany typ wyniku
             logger.error(f"Nieoczekiwany typ wyniku dla perspektywy {p_def['config']['type']}: {type(result)}")
             processed_results.append(schemas.PerspectiveResult(
                type=p_def["config"]["type"],
                model=p_def["config"]["model"],
                prompt="N/A",
                response="BŁĄD: Nieoczekiwany typ wyniku.",
                error="Nieoczekiwany typ wyniku."
            ))


    return processed_results

async def _call_perspective_model(api_key: str, model: str, prompt: str, perspective_type: str) -> schemas.PerspectiveResult:
    """Pomocnicza funkcja do wywołania pojedynczego modelu perspektywy."""
    response_text = ""
    error_message = None
    try:
        response_text = await call_openrouter_api_async(api_key, model, prompt)
    except Exception as e:
        logger.error(f"Błąd podczas generowania perspektywy {perspective_type} (model: {model}): {e}", exc_info=True)
        error_message = str(e)
        response_text = f"BŁĄD: {error_message}"

    return schemas.PerspectiveResult(
        type=perspective_type,
        model=model,
        prompt=prompt,
        response=response_text,
        error=error_message
    )

async def run_verification_synthesis_step(
    api_key: str,
    query: str,
    analysis_result: schemas.AnalysisResult,
    perspectives: List[schemas.PerspectiveResult]
) -> schemas.VerificationSynthesisResult:
    """Wykonuje krok weryfikacji i syntezy."""
    model = MODEL_CONFIG["verification_synthesis"]
    prompt = "Błąd formatowania promptu." # Domyślna wartość
    raw_response = ""
    error_message = None
    verification_report = None
    final_answer = None

    # Sprawdź, czy mamy wystarczająco perspektyw
    if len(perspectives) < 3:
         error_message = "Nie wygenerowano wszystkich 3 perspektyw, pomijanie weryfikacji/syntezy."
         logger.warning(error_message)
         raw_response = f"BŁĄD: {error_message}"
    else:
        p1 = next((p for p in perspectives if p.type == "Informative"), None)
        p2 = next((p for p in perspectives if p.type == "Contrarian"), None)
        p3 = next((p for p in perspectives if p.type == "Complementary"), None)

        if not all([p1, p2, p3]):
             error_message = "Nie znaleziono wszystkich typów perspektyw."
             logger.error(error_message)
             raw_response = f"BŁĄD: {error_message}"
        else:
            # Sprawdź, czy perspektywy nie zawierają błędów
            if p1.error or p2.error or p3.error:
                 error_message = "Jedna lub więcej perspektyw zawiera błąd, pomijanie weryfikacji/syntezy."
                 logger.warning(error_message)
                 raw_response = f"BŁĄD: {error_message}"
            else:
                try:
                    analysis_summary = analysis_result.result_json.get("analysis_summary", "Analysis unavailable.") if analysis_result.result_json else "Analysis unavailable."
                    prompt = prompts.VERIFICATION_OBJECTIVE_SYNTHESIS_PROMPT.format(
                        query=query,
                        analysis_summary=analysis_summary,
                        model_p1_name=p1.model,
                        perspective_1_response=p1.response,
                        model_p2_name=p2.model,
                        perspective_2_response=p2.response,
                        model_p3_name=p3.model,
                        perspective_3_response=p3.response
                    )
                    raw_response = await call_openrouter_api_async(api_key, model, prompt)

                    # Prosta próba podziału odpowiedzi na raport i finalną odpowiedź
                    # Zakładamy, że model podąża za formatem z nagłówkami Markdown
                    report_marker = "## Verification and Comparison Report"
                    answer_marker = "## Final Synthesized Answer"

                    report_start = raw_response.find(report_marker)
                    answer_start = raw_response.find(answer_marker)

                    if report_start != -1 and answer_start != -1:
                        verification_report = raw_response[report_start + len(report_marker):answer_start].strip()
                        final_answer = raw_response[answer_start + len(answer_marker):].strip()
                    elif answer_start != -1: # Jeśli jest tylko finalna odpowiedź
                         final_answer = raw_response[answer_start + len(answer_marker):].strip()
                         verification_report = "Raport weryfikacji/porównania nie został znaleziony w odpowiedzi."
                    else: # Jeśli nie znaleziono żadnego markera
                         final_answer = raw_response # Zwróć całość jako finalną odpowiedź
                         verification_report = "Nie udało się podzielić odpowiedzi na raport i finalną odpowiedź."
                         logger.warning("Nie udało się podzielić odpowiedzi weryfikacji/syntezy.")

                except Exception as e:
                    logger.error(f"Błąd podczas kroku weryfikacji/syntezy (model: {model}): {e}", exc_info=True)
                    error_message = f"Błąd wywołania API weryfikacji/syntezy: {e}"
                    raw_response = f"BŁĄD: {error_message}"

    return schemas.VerificationSynthesisResult(
        model=model,
        prompt=prompt,
        verification_comparison_report=verification_report,
        final_synthesized_answer=final_answer,
        raw_response=raw_response,
        error=error_message
    )


async def run_ai_pipeline(request: schemas.ProcessQueryRequest, api_key: str) -> schemas.ProcessQueryResponse:
    """Orkiestruje cały potok AI, używając podanego klucza API."""
    start_time = datetime.datetime.now(datetime.timezone.utc)
    logger.info(f"Rozpoczęcie przetwarzania zapytania: {request.query[:50]}...")

    # Przygotowanie danych dokumentów
    documents_summary = "Brak dodatkowych dokumentów."
    documents_content = "Brak dodatkowych dokumentów."
    if request.documents:
        # Tutaj można dodać logikę tworzenia podsumowania i pełnej treści
        # (podobnie jak w starej aplikacji Flask)
        # Na razie uproszczone:
        if request.documents:
             documents_summary = f"Załączono {len(request.documents)} dokument(y)."
             contents = [f"--- START Document: {doc.name} ---\n{doc.content}\n--- END Document ---" for doc in request.documents]
             documents_content = "\n\n".join(contents)


    # Krok 1: Analiza
    logger.info("Krok 1: Analiza zapytania...")
    # Użyj api_key przekazanego jako argument
    analysis_result = await run_analysis_step(api_key, request.query, documents_summary)
    if analysis_result.error:
         logger.error(f"Błąd w kroku analizy: {analysis_result.error}")
         # Można tu zdecydować o przerwaniu potoku lub kontynuacji z domyślną analizą

    # Krok 2: Generowanie Perspektyw (równolegle)
    logger.info("Krok 2: Generowanie perspektyw...")
    # Użyj api_key przekazanego jako argument
    perspective_results = await run_perspective_generation_step(
        api_key, request.query, analysis_result, documents_content
    )
    # Sprawdzenie błędów w perspektywach
    perspective_errors = [p.error for p in perspective_results if p.error]
    if perspective_errors:
         logger.warning(f"Wystąpiły błędy podczas generowania perspektyw: {perspective_errors}")

    # Krok 3: Weryfikacja i Synteza
    logger.info("Krok 3: Weryfikacja i Synteza...")
    # Użyj api_key przekazanego jako argument
    verification_synthesis_result = await run_verification_synthesis_step(
        api_key, request.query, analysis_result, perspective_results
    )
    if verification_synthesis_result.error:
         logger.error(f"Błąd w kroku weryfikacji/syntezy: {verification_synthesis_result.error}")

    end_time = datetime.datetime.now(datetime.timezone.utc)
    duration = end_time - start_time
    logger.info(f"Zakończono przetwarzanie zapytania w {duration.total_seconds():.2f}s.")

    return schemas.ProcessQueryResponse(
        query=request.query,
        timestamp=start_time.isoformat(),
        analysis=analysis_result,
        perspectives=perspective_results,
        verification_synthesis=verification_synthesis_result
    )
