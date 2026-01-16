import re
import numpy as np
from backend.embeddings import get_embedding


def cosine_similarity(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def extract_key_phrases(text: str) -> list[str]:
    """
    Extract concrete technical terms only.
    No adjectives, no seniority.
    """
    text = text.lower()

    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\+\#\.]*\b", text)

    stopwords = {
        "expert", "advanced", "strong", "proficient",
        "senior", "junior", "experience", "knowledge",
        "skills", "level", "responsible", "worked"
    }

    return list({
        w for w in words
        if w not in stopwords and len(w) > 2
    })


def semantic_jd_alignment(
    jd_data: dict,
    resume_text: str,
    threshold: float = 0.70
):
    """
    Compare resume ONLY against:
    - mandatory skills
    - explicit JD requirements
    - role keywords
    """

    allowed_concepts = (
        jd_data.get("mandatory_skills", []) +
        jd_data.get("explicit_requirements", []) +
        jd_data.get("role_keywords", [])
    )

    resume_phrases = extract_key_phrases(resume_text)
    resume_embeddings = {
        phrase: get_embedding(phrase)
        for phrase in resume_phrases
    }

    matched, missing = [], []

    for concept in allowed_concepts:
        concept_emb = get_embedding(concept)

        sims = [
            cosine_similarity(concept_emb, emb)
            for emb in resume_embeddings.values()
            if emb
        ]

        if sims and max(sims) >= threshold:
            matched.append(concept)
        else:
            missing.append(concept)

    alignment_pct = (
        (len(matched) / len(allowed_concepts)) * 100
        if allowed_concepts else 0
    )

    return round(alignment_pct, 2), matched, missing
