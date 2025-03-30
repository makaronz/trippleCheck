import asyncio
import json
import logging
import datetime
from typing import List, Dict, Any, Optional

from ..utils.openrouter_client import call_openrouter_api_async
from ..prompts import prompts
from ..models import schemas

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model definitions for each step (according to the final plan)
MODEL_CONFIG = {
    "analysis": "openchat/openchat-3.5-0106",
    "perspective_1": {
        "model": "meta-llama/llama-3-70b-instruct", # or another Llama
        "type": "Informative"
    },
    "perspective_2": {
        "model": "teknium/openhermes-2.5-mistral-7b", # Changed model to OpenHermes
        "type": "Contrarian"
    },
    "perspective_3": {
        "model": "qwen/qwen-2.5-coder-32b-instruct:free", # Changed model to Qwen Coder
        "type": "Complementary"
    },
    "verification_synthesis": "google/gemini-2.5-pro-exp-03-25:free" # or exact name
}

async def run_analysis_step(api_key: str, query: str, documents_summary: str) -> schemas.AnalysisResult:
    """Executes the query analysis step."""
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
        # Attempt to parse JSON from the response
        try:
            json_start = raw_response.find("```json")
            json_end = raw_response.rfind("```")
            if json_start != -1 and json_end != -1:
                json_str = raw_response[json_start + 7:json_end].strip()
            else:
                 # Try to find JSON without markers
                 start_brace = raw_response.find('{')
                 end_brace = raw_response.rfind('}')
                 if start_brace != -1 and end_brace != -1:
                      json_str = raw_response[start_brace:end_brace+1]
                 else:
                      json_str = raw_response # Last resort

            if json_str:
                analysis_json = json.loads(json_str)
                logger.info(f"Successfully parsed JSON from analysis: {analysis_json}")
            else:
                 logger.warning("Empty analysis response after cleaning attempt.")
                 error_message = "Analysis model returned an empty response."

        except json.JSONDecodeError as json_e:
            logger.warning(f"Failed to parse JSON from analysis: {json_e}. Raw response: '{raw_response[:200]}...'")
            error_message = f"Error parsing JSON from analysis: {json_e}"
        except Exception as e:
             logger.error(f"Unexpected error during analysis JSON parsing: {e}", exc_info=True)
             error_message = f"Unexpected JSON parsing error: {e}"

    except Exception as e:
        logger.error(f"Error during analysis step (model: {model}): {e}", exc_info=True)
        error_message = f"Analysis API call error: {e}"
        raw_response = f"ERROR: {error_message}" # Save error in raw response

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
    """Executes the perspective generation step in parallel."""
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
            # Add other necessary variables if prompts require them
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

    # Process results (handle exceptions from gather)
    processed_results: List[schemas.PerspectiveResult] = []
    for i, result in enumerate(perspective_results):
        p_def = perspective_defs[i]
        if isinstance(result, Exception):
            logger.error(f"Exception during perspective generation {p_def['config']['type']} ({p_def['config']['model']}): {result}", exc_info=True)
            # Return an error object
            processed_results.append(schemas.PerspectiveResult(
                type=p_def["config"]["type"],
                model=p_def["config"]["model"],
                prompt=p_def["prompt_template"].format(model_name=p_def["config"]["model"], query=query, documents_content="...", analysis_summary="..."), # Save approximate prompt
                response=f"ERROR: {result}",
                error=str(result)
            ))
        elif isinstance(result, schemas.PerspectiveResult):
             processed_results.append(result)
        else:
             # Unexpected result type
             logger.error(f"Unexpected result type for perspective {p_def['config']['type']}: {type(result)}")
             processed_results.append(schemas.PerspectiveResult(
                type=p_def["config"]["type"],
                model=p_def["config"]["model"],
                prompt="N/A",
                response="ERROR: Unexpected result type.",
                error="Unexpected result type."
            ))


    return processed_results

async def _call_perspective_model(api_key: str, model: str, prompt: str, perspective_type: str) -> schemas.PerspectiveResult:
    """Helper function to call a single perspective model."""
    response_text = ""
    error_message = None
    try:
        response_text = await call_openrouter_api_async(api_key, model, prompt)
    except Exception as e:
        logger.error(f"Error during perspective generation {perspective_type} (model: {model}): {e}", exc_info=True)
        error_message = str(e)
        response_text = f"ERROR: {error_message}"

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
    """Executes the verification and synthesis step."""
    model = MODEL_CONFIG["verification_synthesis"]
    prompt = "Error formatting prompt." # Default value
    raw_response = ""
    error_message = None
    verification_report = None
    final_answer = None

    # Check if we have enough perspectives
    if len(perspectives) < 3:
         error_message = "Not all 3 perspectives were generated, skipping verification/synthesis."
         logger.warning(error_message)
         raw_response = f"ERROR: {error_message}"
    else:
        p1 = next((p for p in perspectives if p.type == "Informative"), None)
        p2 = next((p for p in perspectives if p.type == "Contrarian"), None)
        p3 = next((p for p in perspectives if p.type == "Complementary"), None)

        if not all([p1, p2, p3]):
             error_message = "Could not find all perspective types."
             logger.error(error_message)
             raw_response = f"ERROR: {error_message}"
        else:
            # Check if perspectives contain errors
            if p1.error or p2.error or p3.error:
                 error_message = "One or more perspectives contain an error, skipping verification/synthesis."
                 logger.warning(error_message)
                 raw_response = f"ERROR: {error_message}"
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

                    # Simple attempt to split the response into report and final answer
                    # Assumes the model follows the format with Markdown headers
                    report_marker = "## Verification and Comparison Report"
                    answer_marker = "## Final Synthesized Answer"

                    report_start = raw_response.find(report_marker)
                    answer_start = raw_response.find(answer_marker)

                    if report_start != -1 and answer_start != -1:
                        verification_report = raw_response[report_start + len(report_marker):answer_start].strip()
                        final_answer = raw_response[answer_start + len(answer_marker):].strip()
                    elif answer_start != -1: # If only the final answer is present
                         final_answer = raw_response[answer_start + len(answer_marker):].strip()
                         verification_report = "Verification/comparison report not found in the response."
                    else: # If no marker was found
                         final_answer = raw_response # Return the whole thing as the final answer
                         verification_report = "Could not split the response into report and final answer."
                         logger.warning("Could not split verification/synthesis response.")

                except Exception as e:
                    logger.error(f"Error during verification/synthesis step (model: {model}): {e}", exc_info=True)
                    error_message = f"Verification/synthesis API call error: {e}"
                    raw_response = f"ERROR: {error_message}"

    return schemas.VerificationSynthesisResult(
        model=model,
        prompt=prompt,
        verification_comparison_report=verification_report,
        final_synthesized_answer=final_answer,
        raw_response=raw_response,
        error=error_message
    )


async def run_ai_pipeline(request: schemas.ProcessQueryRequest, api_key: str) -> schemas.ProcessQueryResponse:
    """Orchestrates the entire AI pipeline using the provided API key."""
    start_time = datetime.datetime.now(datetime.timezone.utc)
    logger.info(f"Starting query processing: {request.query[:50]}...")

    # Prepare document data
    documents_summary = "No additional documents provided."
    documents_content = "No additional documents provided."
    if request.documents:
        # Logic for creating summary and full content can be added here
        # (similar to the old Flask app)
        # Simplified for now:
        if request.documents:
             documents_summary = f"{len(request.documents)} document(s) attached."
             contents = [f"--- START Document: {doc.name} ---\n{doc.content}\n--- END Document ---" for doc in request.documents]
             documents_content = "\n\n".join(contents)


    # Step 1: Analysis
    logger.info("Step 1: Query Analysis...")
    # Use the api_key passed as an argument
    analysis_result = await run_analysis_step(api_key, request.query, documents_summary)
    if analysis_result.error:
         logger.error(f"Error in analysis step: {analysis_result.error}")
         # Could decide here to stop the pipeline or continue with default analysis

    # Step 2: Perspective Generation (parallel)
    logger.info("Step 2: Generating Perspectives...")
    # Use the api_key passed as an argument
    perspective_results = await run_perspective_generation_step(
        api_key, request.query, analysis_result, documents_content
    )
    # Check for errors in perspectives
    perspective_errors = [p.error for p in perspective_results if p.error]
    if perspective_errors:
         logger.warning(f"Errors occurred during perspective generation: {perspective_errors}")

    # Step 3: Verification and Synthesis
    logger.info("Step 3: Verification and Synthesis...")
    # Use the api_key passed as an argument
    verification_synthesis_result = await run_verification_synthesis_step(
        api_key, request.query, analysis_result, perspective_results
    )
    if verification_synthesis_result.error:
         logger.error(f"Error in verification/synthesis step: {verification_synthesis_result.error}")

    end_time = datetime.datetime.now(datetime.timezone.utc)
    duration = end_time - start_time
    logger.info(f"Finished query processing in {duration.total_seconds():.2f}s.")

    return schemas.ProcessQueryResponse(
        query=request.query,
        timestamp=start_time.isoformat(),
        analysis=analysis_result,
        perspectives=perspective_results,
        verification_synthesis=verification_synthesis_result
    )
