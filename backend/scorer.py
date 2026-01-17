def normalize_weights(raw_weights: dict) -> dict:
    """
    Normalize HR-selected weights from Streamlit UI.
    Uses ONLY UI values.
    Raises error if all weights are zero.
    """
    total = sum(raw_weights.values())

    if total == 0:
        raise ValueError(
            "All scoring weights are zero. "
            "Please set at least one weight in the UI."
        )

    return {
        k: round(v / total, 3)
        for k, v in raw_weights.items()
    }


def final_score(
    experience_score: float,
    skill_score: float,
    jd_score: float,
    project_score: float,
    resume_quality: float,
    weights: dict
) -> float:
    """
    Compute weighted final score (0–100).
    """

    # Normalize experience into percentage
    exp_normalized = min(experience_score * 10, 100)

    score = (
        exp_normalized * weights["experience"] +
        skill_score * weights["skills"] +
        jd_score * weights["jd_alignment"] +
        project_score * weights["projects"] +
        resume_quality * weights["resume_quality"]
    )

    return round(score, 2)
