def match_jd_attributes(derived_attrs: dict, resume_text: str):
    matched = []
    missing = []

    combined_attrs = (
        derived_attrs.get("additional_skills", []) +
        derived_attrs.get("tools", []) +
        derived_attrs.get("keywords", [])
    )

    for attr in combined_attrs:
        if attr.lower() in resume_text.lower():
            matched.append(attr)
        else:
            missing.append(attr)

    total = len(combined_attrs)
    match_pct = round((len(matched) / total) * 100, 2) if total else 100.0

    return match_pct, matched, missing
