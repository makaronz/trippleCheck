# -*- coding: utf-8 -*-

# Prompt Analizy (Oczekiwany format: JSON) - UPROSZCZONY
QUERY_ANALYSIS_PROMPT_V2 = """
Analyze the user's query and document context to determine:
1. Main topics
2. User intent
3. Complexity (low/medium/high)

Format as JSON:
"main_topics": ["topic1", "topic2"],
"user_intent": "...",
"complexity": "high/medium/low",
"analysis_summary": "Brief summary"

User Query:
{query}

Available Documents Summary:
{documents_summary}
"""

# Prompt Generowania Perspektyw (Uproszczony)
RESPONSE_GENERATION_PROMPT_V2 = """
You are model: {model_name} with strength: {specialization}.

Answer this query: {query}

Documents (cite if used):
{documents_content}

Instructions:
1. Be concise but thorough
2. Use Markdown formatting
3. Cite documents when used
4. Focus on the user's intent
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

# Prompt Syntezy (Uproszczony)
SYNTHESIS_PROMPT_V2 = """
Create a final response to: {query}

Based on:
1. Original response: {perspectives_summary}
2. Verification: {verification_report}

Instructions:
1. Fix any issues noted in verification
2. Be concise and clear
3. Use Markdown formatting
4. Focus directly on answering the query
5. Provide a standalone, complete answer
"""
