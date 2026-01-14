from google import genai
import json
import os
import re

# -----------------------------
# Gemini Client
# -----------------------------
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Use a model that EXISTS for your project
MODEL_NAME = "models/gemini-flash-latest"


def hr_evaluate(jd_text: str, resume_text: str) -> dict:
    """
    Strict HR evaluation.
    Always returns a valid dict.
    """

    prompt = f"""
You MUST respond with ONLY valid JSON.
NO explanations. NO markdown. NO text outside JSON.

Job Description:
{jd_text}

Candidate Resume:
{resume_text}

JSON format:
{{
  "project_relevance_score": 0-100,
  "resume_quality_score": 0-100,
  "remarks": "string",
  "rejection_reasons": ["string"]
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return _safe_llm_json(response.text)

    except Exception as e:
        return _llm_fallback(f"LLM error: {str(e)}")


# -----------------------------
# Helpers
# -----------------------------
def _safe_llm_json(text: str) -> dict:
    if not text or not text.strip():
        return _llm_fallback("Empty LLM response")

    # Remove markdown fences
    cleaned = re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()

    # Extract first JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return _llm_fallback("No JSON object found")

    try:
        return json.loads(match.group())
    except Exception:
        return _llm_fallback("JSON parsing failed")


def _llm_fallback(reason: str) -> dict:
    """
    Deterministic fallback so scoring never breaks.
    """
    return {
        "project_relevance_score": 50,
        "resume_quality_score": 50,
        "remarks": f"LLM fallback applied ({reason})",
        "rejection_reasons": []
    }
