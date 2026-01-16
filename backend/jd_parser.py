from google import genai
import json
import os
import re

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "models/gemini-flash-latest"


def extract_jd_attributes(jd_description: str) -> dict:
    """
    Extract ONLY explicit JD requirements.
    Inferred skills are marked as nice-to-have and never used for rejection.
    """

    if not jd_description or not jd_description.strip():
        return {
            "explicit_requirements": [],
            "nice_to_have": []
        }

    prompt = f"""
Extract requirements from the Job Description.

RULES:
- ONLY include skills/tools/tasks that are EXPLICITLY mentioned in the JD
- If a skill is implied but NOT written, put it under nice_to_have
- DO NOT invent enterprise buzzwords
- DO NOT generalize

JD:
{jd_description}

Return ONLY valid JSON:
{{
  "explicit_requirements": ["string"],
  "nice_to_have": ["string"]
}}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return _safe_json_parse(response.text)


def _safe_json_parse(text: str) -> dict:
    if not text:
        return {"explicit_requirements": [], "nice_to_have": []}

    text = re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return {"explicit_requirements": [], "nice_to_have": []}

    try:
        return json.loads(match.group())
    except Exception:
        return {"explicit_requirements": [], "nice_to_have": []}
