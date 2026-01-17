def skill_match(mandatory_skills: list[str], resume_text: str):
    """
    Soft skill match percentage (used only AFTER hard fail).
    """
    resume_text = resume_text.lower()

    matched = [
        skill for skill in mandatory_skills
        if skill.lower() in resume_text
    ]

    if not mandatory_skills:
        return 0.0, []

    pct = (len(matched) / len(mandatory_skills)) * 100
    return round(pct, 2), matched


def hard_fail_mandatory_skills(
    mandatory_skills: list[str],
    resume_text: str
):
    """
    Hard reject if ANY mandatory skill is missing.
    """
    resume_text = resume_text.lower()

    missing = [
        skill for skill in mandatory_skills
        if skill.lower() not in resume_text
    ]

    return len(missing) == 0, missing
