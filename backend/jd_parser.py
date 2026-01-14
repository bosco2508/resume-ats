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


def extract_jd_attributes(jd_description: str) -> dict:
    """
    Extract additional requirements from JD description.
    Always returns a valid dict.
    """

    if not jd_description or not jd_description.strip():
        return _empty_jd_attrs()

    prompt = f"""
You MUST respond with ONLY valid JSON.
NO explanations. NO markdown. NO text outside JSON.

Job Description:
{jd_description}

JSON format:
{{
  "additional_skills": ["string"],
  "tools": ["string"],
  "soft_skills": ["string"],
  "keywords": ["string"]
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return _safe_json_parse(response.text, fallback=_empty_jd_attrs())

    except Exception:
        return _empty_jd_attrs()


# -----------------------------
# Helpers
# -----------------------------
def _safe_json_parse(text: str, fallback: dict) -> dict:
    if not text or not text.strip():
        return fallback

    # Remove markdown fences if present
    cleaned = re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()

    # Extract first JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return fallback

    try:
        return json.loads(match.group())
    except Exception:
        return fallback


def _empty_jd_attrs() -> dict:
    return {
        "additional_skills": [],
        "tools": [],
        "soft_skills": [],
        "keywords": []
    }
