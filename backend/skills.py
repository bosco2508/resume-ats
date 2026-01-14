def skill_match(required, candidate_text):
    matched = []
    for skill in required:
        if skill.lower() in candidate_text.lower():
            matched.append(skill)

    return round(len(matched) / len(required) * 100, 2), matched