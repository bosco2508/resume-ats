import numpy as np
from backend.embeddings import get_embedding


def cosine_similarity(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def chunk_text(text: str, chunk_size: int = 400) -> list[str]:
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]


def semantic_jd_alignment(
    jd_requirements: list[str],
    resume_text: str,
    threshold: float = 0.65
):
    """
    Returns:
    - alignment_pct
    - matched_requirements
    - missing_requirements
    """

    resume_chunks = chunk_text(resume_text)
    resume_embeddings = [get_embedding(chunk) for chunk in resume_chunks]

    matched = []
    missing = []

    for req in jd_requirements:
        req_embedding = get_embedding(req)

        similarities = [
            cosine_similarity(req_embedding, r_emb)
            for r_emb in resume_embeddings
            if r_emb
        ]

        max_sim = max(similarities) if similarities else 0.0

        if max_sim >= threshold:
            matched.append(req)
        else:
            missing.append(req)

    alignment_pct = (
        (len(matched) / len(jd_requirements)) * 100
        if jd_requirements else 0
    )

    return round(alignment_pct, 2), matched, missing
