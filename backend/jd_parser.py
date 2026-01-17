import re
from collections import Counter


def extract_weighted_keywords(
    jd_description: str,
    role: str,
    mandatory_skills: list[str]
) -> dict:
    """
    Extract keywords from Job Title + JD with frequency & priority.
    """

    text = f"{role} {jd_description}".lower()

    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]*", text)

    stopwords = {
        "and", "or", "with", "to", "for", "of", "in", "on",
        "the", "a", "an", "is", "are", "will", "should"
    }

    tokens = [t for t in tokens if t not in stopwords]
    freq = Counter(tokens)

    keyword_weights = {}

    # Mandatory skills → highest weight
    for skill in mandatory_skills:
        keyword_weights[skill.lower()] = {
            "weight": 3.0,
            "freq": freq.get(skill.lower(), 1)
        }

    # JD + Role keywords
    for token, count in freq.items():
        if token not in keyword_weights:
            keyword_weights[token] = {
                "weight": 1.0,
                "freq": count
            }

    return keyword_weights