def final_score(
    experience_score: float,
    skill_score: float,
    jd_score: float,
    project_score: float,
    resume_quality: float,
    weights: dict
) -> float:

    score = (
        experience_score * weights["experience"] +
        skill_score * weights["skills"] +
        jd_score * weights.get("jd_alignment", 0.15) +
        project_score * weights["projects"] +
        resume_quality * weights["resume_quality"]
    )

    return round(score, 2)
