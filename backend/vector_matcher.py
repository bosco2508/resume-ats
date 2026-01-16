import re
import numpy as np
from backend.embeddings import get_embedding


# -------------------------------------------------
# Utility: cosine similarity
# -------------------------------------------------
def cosine_similarity(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# -------------------------------------------------
# Extract important / connected phrases only
# -------------------------------------------------
def extract_key_phrases(text: str) -> list[str]:
    """
    Extract meaningful technical phrases instead of full sentences.
    Focuses on skills, tools, technologies, actions.
    """

    text = text.lower()

    # Patterns for connected technical phrases
    patterns = [
        r"\b[a-zA-Z]+\s+[a-zA-Z]+\b",            # two-word phrases
        r"\b[a-zA-Z]+\s+[a-zA-Z]+\s+[a-zA-Z]+\b" # three-word phrases
    ]

    phrases = set()

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            phrases.add(m.strip())

    # Remove generic / non-informative phrases
    stop_phrases = {
        "years experience",
        "hands on",
        "strong knowledge",
        "good understanding",
        "responsible for",
        "worked on",
        "experience in",
        "knowledge of"
    }

    clean_phrases = [
        p for p in phrases
        if p not in stop_phrases
        and len(p.split()) <= 3
        and len(p) > 6
    ]

    return list(set(clean_phrases))


# -------------------------------------------------
# Semantic JD ↔ Resume alignment (CONCEPT BASED)
# -------------------------------------------------
def semantic_jd_alignment(
    jd_requirements: list[str],
    resume_text: str,
    threshold: float = 0.70
):
    """
    Keyword / phrase level semantic matching.
    NO sentence embeddings.
    """

    if not jd_requirements or not resume_text:
        return 0.0, [], jd_requirements

    # 🔹 Extract important phrases from resume
    resume_phrases = extract_key_phrases(resume_text)

    # 🔹 Embed resume phrases
    resume_embeddings = {
        phrase: get_embedding(phrase)
        for phrase in resume_phrases
    }

    matched = []
    missing = []

    # 🔹 Compare each JD requirement against resume phrases
    for req in jd_requirements:
        req_embedding = get_embedding(req)

        similarities = [
            cosine_similarity(req_embedding, emb)
            for emb in resume_embeddings.values()
            if emb
        ]

        max_similarity = max(similarities) if similarities else 0.0

        if max_similarity >= threshold:
            matched.append(req)
        else:
            missing.append(req)

    alignment_pct = (
        (len(matched) / len(jd_requirements)) * 100
        if jd_requirements else 0
    )

    return round(alignment_pct, 2), matched, missing
