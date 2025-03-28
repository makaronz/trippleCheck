# -*- coding: utf-8 -*-

# Prompt Analizy (Oczekiwany format: JSON)
QUERY_ANALYSIS_PROMPT_V2 = """
Act as an expert query analyst. Your task is to meticulously analyze the user's query and associated document context (if any) to determine:
1. Main topics and sub-topics.
2. Required level of expertise and specific knowledge domains.
3. Implicit user intent and desired output format (e.g., summary, explanation, draft).
4. Potential ambiguities or areas needing clarification.
5. Complexity of the required response (low/medium/high).
6. Suggested LLMs from OpenRouter for generating diverse perspectives (at least 3, considering capabilities like reasoning, creativity, speed, cost, context window, and relevance to the query type). Justify each suggestion briefly.

Format your response strictly as a JSON object with the following keys:
"main_topics": ["topic1", "topic2"],
"sub_topics": ["subtopic1", "subtopic2"],
"expertise_required": ["domain1", "domain2"],
"user_intent": "...",
"ambiguities": "...",
"complexity": "high/medium/low",
"suggested_models": [
    {{"model_id": "vendor/model-name-v1", "reason": "..."}},
    {{"model_id": "vendor/model-name-v2", "reason": "..."}},
    {{"model_id": "vendor/model-name-v3", "reason": "..."}}
],
"analysis_summary": "A brief summary of the query and requirements."

User Query:
{query}

Available Documents Summary:
{documents_summary}
"""

# Prompt Generowania Perspektyw (Ulepszony)
RESPONSE_GENERATION_PROMPT_V2 = """
You are a specialized AI model: {model_name}. Your designated role requires you to provide a comprehensive and expert response based on your specific strengths: {specialization}.

Address the user's query meticulously from your unique perspective.

User Query: {query}

Query Analysis (for context):
{analysis}

Available Document Content (Use if relevant, cite document name when used):
{documents_content}

Instructions:
1. Generate a detailed, accurate, and in-depth response from the viewpoint of your specialization.
2. Leverage the provided documents as a knowledge source if they are relevant to the query. When using information from a document, explicitly mention the document name (e.g., "According to Document 'report.pdf', ...").
3. If the documents are irrelevant or insufficient, rely on your internal knowledge base.
4. Structure your response clearly. Use Markdown for formatting (headings, lists, bold text).
5. If you encounter uncertainty or lack specific information, clearly state this limitation rather than fabricating an answer. Indicate the level of confidence if possible.
6. Focus on fulfilling the user's intent as identified in the query analysis.
"""

# Prompt Weryfikacji (Dostosowany do pojedynczej perspektywy, format Markdown)
VERIFICATION_PROMPT_V2 = """
Act as a critical AI fact-checker and content evaluator. Your task is to rigorously assess the single AI-generated perspective provided below in response to the user's query.

User Query: {query}

Perspective for Verification:
--- START PERSPECTIVE ({model_name} - {model_spec}) ---
{perspective_response}
--- END PERSPECTIVE ---

Evaluate the perspective based on the following criteria. Be specific, provide justifications, and cite examples from the response:
1.  **Factual Accuracy:** Verify claims against known facts or indicate if unverifiable. Note any potential inaccuracies or hallucinations.
2.  **Logical Consistency:** Check for internal contradictions and soundness of reasoning.
3.  **Completeness:** Assess if the response fully addresses the user's query and covers key aspects.
4.  **Relevance:** Ensure the response is on-topic and aligned with the user's intent and the model's stated specialization.
5.  **Document Usage:** Check if documents were used appropriately and cited correctly (if applicable).
6.  **Bias and Objectivity:** Identify any potential bias or non-neutral language.
7.  **Clarity and Structure:** Evaluate the readability and organization of the response.
8.  **Strengths:** Briefly mention the strongest points or unique contributions of the perspective.
9.  **Weaknesses/Areas for Improvement:** Identify any significant weaknesses, omissions, or areas where the response could be improved.

Format your output using Markdown:

## Verification Report for Perspective ({model_name})

*   **Factual Accuracy:** [Evaluation + Justification + Examples]
*   **Logical Consistency:** [Evaluation + Justification]
*   **Completeness:** [Evaluation + Justification]
*   **Relevance:** [Evaluation + Justification]
*   **Document Usage:** [Evaluation + Justification]
*   **Bias/Objectivity:** [Evaluation + Justification]
*   **Clarity/Structure:** [Evaluation + Justification]
*   **Strengths:** [List]
*   **Weaknesses/Areas for Improvement:** [List]
*   **Overall Assessment:** [Brief summary of the perspective's quality and reliability]
"""

# Prompt Syntezy (Ulepszony - dostosowany do pojedynczej perspektywy i zmienionego raportu weryfikacji)
SYNTHESIS_PROMPT_V2 = """
Act as an AI Knowledge Synthesizer and Editor. Your goal is to create a single, comprehensive, accurate, and coherent final response to the user's query, based on the provided AI perspective and its verification report.

User Query: {query}

Generated Perspective (for context):
{perspectives_summary} # Note: This will contain only one perspective now

Verification Report (Crucial Guidance):
{verification_report}

Instructions:
1. Carefully review the Verification Report to understand the strengths and weaknesses of the provided perspective.
2. Construct a final response based primarily on the generated perspective, but refine it based on the verification report.
3. Correct any information identified as inaccurate, biased, or poorly reasoned in the verification report.
4. Address any points raised in the "Weaknesses/Areas for Improvement" section of the report, if possible, by augmenting or clarifying the original perspective's content.
5. Ensure the final response directly and fully addresses the user's original query and intent.
6. Maintain a neutral, objective, and informative tone.
7. Structure the response logically using Markdown for clarity (headings, lists, bolding, etc.).
8. Attribute information to specific documents if appropriate (based on generation/verification steps).
9. Clearly state any remaining uncertainties highlighted in the verification report.
10. Do not simply copy the original perspective; perform a genuine synthesis and refinement based on the verification. The final output should be a polished, standalone response.

Generate the final synthesized response below:
"""
