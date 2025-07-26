# -*- coding: utf-8 -*-

# Prompt Analizy (Oczekiwany format: JSON) - ROZWINIĘTY V4 z rozszerzoną strukturą
QUERY_ANALYSIS_PROMPT_V4 = """
You are an advanced analytical assistant trained to interpret user queries and contextual documents with precision, creativity, and domain sensitivity. Your task is to dissect the request and relevant document context, surfacing meaningful metadata and strategic guidance.

Proceed with the following steps:
1. Extract and list the main topics or conceptual areas present in the query.
2. Clarify the user's core intent—what they are trying to accomplish, decide, or learn.
3. Evaluate the task's complexity (low/medium/high) based on reasoning depth, ambiguity, or domain expertise required.
4. Identify the type of domain knowledge or competencies that might be necessary to handle this task well.
5. Suggest tools, models, APIs, or libraries that could support resolving or accelerating the task.
6. Anticipate potential challenges, ambiguities, or bottlenecks that may arise.
7. Write a clear and structured summary of your reasoning and findings.

IMPORTANT: Return your answer as a valid JSON object in the following format:
```json
{{
  "main_topics": ["topic1", "topic2"],
  "user_intent": "Clear and specific description of user’s goal",
  "complexity": "high/medium/low",
  "required_knowledge": ["domain1", "concept2", "skill3"],
  "suggested_tools": ["tool1", "API2", "framework3"],
  "potential_challenges": ["challenge1", "uncertainty2"],
  "analysis_summary": "Thoughtful synthesis of reasoning, including rationale behind choices"
}}
```

User Query:
{query}

Available Documents Summary:
{documents_summary}
"""
# Prompt Generowania Perspektyw (Z dostępem do internetu)
RESPONSE_GENERATION_PROMPT_V2 = """
You are model: {model_name} with strength: {specialization}.

Answer this query: {query}

IMPORTANT: You have access to the internet. You MUST search for and include up-to-date information from the web to answer this query. Include relevant facts, data, and current information.

Documents (cite if used):
{documents_content}

Instructions:
1. ALWAYS search the internet for current and relevant information
2. Include specific facts, data, and information from reliable sources
3. Cite your sources with links when possible
4. Use Markdown formatting for clarity
5. Be thorough and comprehensive
6. Focus on the user's intent
"""

# Prompt Weryfikacji (Uproszczony)
VERIFICATION_PROMPT_V2 = """
Verify this response to the query: {query}

Response from {model_name}:
{perspective_response}

Check for:
1. Factual accuracy
2. Completeness
3. Relevance

Format in Markdown:
## Verification Report
* **Accuracy:** [brief assessment]
* **Completeness:** [brief assessment]
* **Relevance:** [brief assessment]
* **Strengths:** [list]
* **Weaknesses:** [list]
* **Overall:** [1-2 sentence summary]
"""

# Nowy Prompt Weryfikacji i Syntezy
VERIFICATION_SYNTHESIS_PROMPT = """
You are an expert evaluator and synthesizer. Your task is to analyze two perspectives provided in response to a user query, verify their content, compare them, and then synthesize a final, improved, and verified answer.

User Query:
{query}

Perspective 1 ({model_1_name} - {model_1_spec}):
--- START PERSPECTIVE 1 ---
{perspective_1_response}
--- END PERSPECTIVE 1 ---

Perspective 2 ({model_2_name} - {model_2_spec}):
--- START PERSPECTIVE 2 ---
{perspective_2_response}
--- END PERSPECTIVE 2 ---

Instructions:

1.  **Verification:**
    *   Critically evaluate BOTH perspectives for factual accuracy, completeness, and relevance to the query.
    *   You MUST use your knowledge and access to real-time information (internet access) to verify claims, data, and facts presented in both perspectives.
    *   Identify any inaccuracies, outdated information, or potential biases.

2.  **Comparison:**
    *   Compare the strengths and weaknesses of each perspective.
    *   Which perspective is more helpful, accurate, or comprehensive? Why?
    *   Are there any contradictions between the perspectives?

3.  **Synthesis:**
    *   Create a final, comprehensive, and accurate response to the user's query.
    *   Combine the best elements and verified information from both perspectives.
    *   Correct any errors or inaccuracies identified during verification.
    *   Ensure the final answer is well-structured, clear, concise, and directly addresses the user's query.
    *   Use Markdown formatting for clarity (headings, lists, bold text, etc.).
    *   If citing sources, ensure they are accurate and properly formatted.

Output Format:

Return your response as a single block of text containing the following sections clearly marked with Markdown headings:

## Verification and Comparison Report

*   **Perspective 1 Accuracy:** [Brief assessment with specific examples of errors/correct points]
*   **Perspective 2 Accuracy:** [Brief assessment with specific examples of errors/correct points]
*   **Completeness:** [Assessment of how well both perspectives cover the query]
*   **Relevance:** [Assessment of relevance]
*   **Comparison Summary:** [Brief comparison of strengths/weaknesses, contradictions, and overall helpfulness]

## Final Synthesized Answer

[Your final, synthesized, and verified answer to the user's query goes here, formatted in Markdown.]
"""
