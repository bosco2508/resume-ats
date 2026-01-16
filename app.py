import streamlit as st

# -------------------------
# Backend imports
# -------------------------
from backend.parser import extract_text, extract_candidate_name
from backend.experience import calculate_experience
from backend.skills import skill_match
from backend.llm import hr_evaluate
from backend.jd_parser import extract_jd_attributes
from backend.vector_matcher import semantic_jd_alignment
from backend.scorer import final_score
from backend.firebase_db import (
    create_session,
    append_result,
    get_session,
    clear_session
)
from backend.exporter import export_excel

# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="GenAI Resume Screener", layout="wide")
st.title("GenAI Resume Screener – Semantic HR Mode")

# -------------------------
# Session State
# -------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ======================================================
# JOB DESCRIPTION INPUT
# ======================================================
st.header("Job Description")

col1, col2 = st.columns(2)

with col1:
    role = st.text_input("Role / Position")
    min_exp = st.number_input(
        "Minimum Experience (Years)", 0.0, 30.0, 0.0, 0.5
    )

with col2:
    skills_input = st.text_input("Mandatory Skills (comma-separated)")
    mandatory_skills = [
        s.strip() for s in skills_input.split(",") if s.strip()
    ]

jd_description = st.text_area("JD Description", height=180)

# ======================================================
# SCORING WEIGHTS
# ======================================================
st.header("Scoring Weights")

weights = {
    "experience": st.slider("Experience", 0.0, 1.0, 0.30),
    "skills": st.slider("Mandatory Skills", 0.0, 1.0, 0.35),
    "jd_alignment": st.slider("JD Alignment", 0.0, 1.0, 0.15),
    "projects": st.slider("Projects", 0.0, 1.0, 0.10),
    "resume_quality": st.slider("Resume Quality", 0.0, 1.0, 0.10)
}

# ======================================================
# START SESSION
# ======================================================
if st.button("Start Screening Session"):
    with st.spinner("Analyzing JD..."):
        derived_attrs = extract_jd_attributes(jd_description)

    st.session_state.session_id = create_session(
        jd={
            "role": role,
            "min_exp": min_exp,
            "mandatory_skills": mandatory_skills,
            "jd_description": jd_description,
            "derived_attributes": derived_attrs
        },
        weights=weights
    )

    st.success("Session started.")

# ======================================================
# RESUME PROCESSING
# ======================================================
st.header("Resume Screening")

resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if resume and st.button("Process Resume"):
    session = get_session(st.session_state.session_id)
    jd = session["jd"]
    explicit_reqs = jd["derived_attributes"]["explicit_requirements"]

    resume_text = extract_text(resume)
    candidate = extract_candidate_name(resume_text)

    experience = calculate_experience(resume_text)
    skill_pct, _ = skill_match(jd["mandatory_skills"], resume_text)

    jd_pct, jd_matched, jd_missing = semantic_jd_alignment(
        explicit_reqs,
        resume_text
    )

    llm_eval = hr_evaluate(jd["jd_description"], resume_text)

    score = final_score(
        experience_score=experience,
        skill_score=skill_pct,
        jd_score=jd_pct,
        project_score=llm_eval["project_relevance_score"],
        resume_quality=llm_eval["resume_quality_score"],
        weights=weights
    )

    rejection_reasons = []
    if experience < jd["min_exp"]:
        rejection_reasons.append(
            f"Experience below requirement: {experience} < {jd['min_exp']}"
        )

    if skill_pct < 50:
        rejection_reasons.append("Insufficient mandatory skill match")

    for item in jd_missing:
        rejection_reasons.append(
            f"Missing explicit JD requirement: {item}"
        )

    rejection_reasons.extend(llm_eval["rejection_reasons"])

    result = {
        "candidate_name": candidate,
        "experience_years": experience,
        "skill_match_pct": skill_pct,
        "jd_alignment_pct": jd_pct,
        "final_score": round(score, 2),
        "status": "Selected" if score >= 70 else "Rejected",
        "rejection_reasons": rejection_reasons,
        "remarks": llm_eval["remarks"]
    }

    append_result(st.session_state.session_id, result)
    st.json(result)

# ======================================================
# EXPORT
# ======================================================
if st.button("Download Excel & Clear Session"):
    session = get_session(st.session_state.session_id)
    file_path = export_excel(session["results"])
    st.download_button(
        "Download Excel",
        data=open(file_path, "rb"),
        file_name="resume_results.xlsx"
    )
    clear_session(st.session_state.session_id)
    st.session_state.session_id = None
