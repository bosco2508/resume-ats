from google import genai
import json
import os
import re

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "models/gemini-flash-latest"

FORBIDDEN_WORDS = {
    "expert", "advanced", "strong", "proficient",
    "senior", "mastery", "highly skilled"
}


def extract_jd_attributes(
    jd_description: str,
    role: str,
    mandatory_skills: list[str]
) -> dict:
    """
    Extract ONLY literal JD requirements.
    No skill inflation. No inferred seniority.
    """

    prompt = f"""
Extract ONLY explicitly written requirements.

STRICT RULES:
- DO NOT add seniority or expertise adjectives
- DO NOT infer skills from role
- DO NOT upgrade skill levels
- Preserve exact JD wording where possible

Role:
{role}

Mandatory Skills (must be kept EXACT):
{mandatory_skills}

JD:
{jd_description}

Return ONLY JSON:
{{
  "explicit_requirements": ["string"],
  "role_keywords": ["string"],
  "mandatory_skills": ["string"]
}}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    data = _safe_json_parse(response.text)

    # Remove forbidden adjectives
    explicit_cleaned = []
    for item in data.get("explicit_requirements", []):
        if not any(w in item.lower() for w in FORBIDDEN_WORDS):
            explicit_cleaned.append(item)

    return {
        "explicit_requirements": explicit_cleaned,
        "role_keywords": data.get("role_keywords", []),
        "mandatory_skills": mandatory_skills
    }


def _safe_json_parse(text: str) -> dict:
    text = re.sub(r"```(?:json)?|```", "", text, flags=re.I).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except Exception:
        return {}
