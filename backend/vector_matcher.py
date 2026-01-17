def keyword_based_jd_score(
    keyword_weights: dict,
    resume_text: str
) -> float:
    """
    Compute JD alignment using keyword coverage + frequency.
    """
    resume_text = resume_text.lower()

    total_weight = 0.0
    matched_weight = 0.0

    for kw, meta in keyword_weights.items():
        w = meta["weight"]
        f = min(meta["freq"], 3)

        total_weight += w

        if kw in resume_text:
            matched_weight += w * f

    if total_weight == 0:
        return 0.0

    return round(min((matched_weight / total_weight) * 100, 100), 2)


def keyword_coverage_report(
    keyword_weights: dict,
    resume_text: str
):
    """
    Detailed keyword coverage for UI visualization.
    """
    resume_text = resume_text.lower()
    report = []

    for kw, meta in keyword_weights.items():
        report.append({
            "keyword": kw,
            "present": kw in resume_text,
            "weight": meta["weight"],
            "frequency": meta["freq"]
        })

    return report
