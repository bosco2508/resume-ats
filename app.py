import streamlit as st

from backend.parser import extract_text, extract_candidate_name
from backend.experience import calculate_experience
from backend.skills import skill_match
from backend.llm import hr_evaluate
from backend.jd_parser import extract_jd_attributes
from backend.vector_matcher import semantic_jd_alignment
from backend.scorer import final_score, normalize_weights
from backend.firebase_db import (
    create_session, append_result, get_session, clear_session
)
from backend.exporter import export_excel

st.set_page_config(page_title="GenAI Resume Screener", layout="wide")
st.title("GenAI Resume Screener – Strict ATS Mode")

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ---------------- JD INPUT ----------------
st.header("Job Description")

col1, col2 = st.columns(2)

with col1:
    role = st.text_input("Role / Position")
    min_exp = st.number_input("Minimum Experience (Years)", 0.0, 30.0, 0.0, 0.5)

with col2:
    skills_input = st.text_input("Mandatory Skills (comma-separated)")
    mandatory_skills = [s.strip() for s in skills_input.split(",") if s.strip()]

jd_description = st.text_area("JD Description", height=180)

# ---------------- WEIGHTS ----------------
st.header("Scoring Priority (HR Controlled)")

exp_w = st.slider("Experience", 0.0, 1.0, 0.3)
skill_w = st.slider("Mandatory Skills", 0.0, 1.0, 0.35)
jd_w = st.slider("JD Alignment", 0.0, 1.0, 0.15)
proj_w = st.slider("Projects", 0.0, 1.0, 0.1)
qual_w = st.slider("Resume Quality", 0.0, 1.0, 0.1)

weights_ui = {
    "experience": exp_w,
    "skills": skill_w,
    "jd_alignment": jd_w,
    "projects": proj_w,
    "resume_quality": qual_w
}

# ---------------- START SESSION ----------------
if st.button("Start Screening Session"):
    if not role or not mandatory_skills:
        st.error("Role and Mandatory Skills are required.")
    else:
        try:
            weights = normalize_weights(weights_ui)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        derived_attrs = extract_jd_attributes(
            jd_description, role, mandatory_skills
        )

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

        st.success("Screening session started")
        st.info(f"Applied weights: {weights}")

# ---------------- RESUME PROCESS ----------------
st.header("Resume Screening")

resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if resume and st.button("Process Resume"):
    session = get_session(st.session_state.session_id)
    jd_data = session["jd"]
    weights = session["weights"]

    resume_text = extract_text(resume)
    name = extract_candidate_name(resume_text)
    exp = calculate_experience(resume_text)

    skill_pct, _ = skill_match(jd_data["mandatory_skills"], resume_text)

    jd_pct, _, jd_missing = semantic_jd_alignment(
        jd_data["derived_attributes"], resume_text
    )

    llm_eval = hr_evaluate(jd_data["jd_description"], resume_text)

    score = final_score(
        exp, skill_pct, jd_pct,
        llm_eval["project_relevance_score"],
        llm_eval["resume_quality_score"],
        weights
    )

    result = {
        "candidate_name": name,
        "experience_years": exp,
        "skill_match_pct": skill_pct,
        "jd_alignment_pct": jd_pct,
        "project_relevance_score": llm_eval["project_relevance_score"],
        "resume_quality_score": llm_eval["resume_quality_score"],
        "final_score": score,
        "status": "Selected" if score >= 70 else "Rejected",
        "rejection_reasons": jd_missing[:3],
        "remarks": llm_eval["remarks"]
    }

    append_result(st.session_state.session_id, result)
    st.json(result)

# ---------------- EXPORT ----------------
st.header("Finalize Session")

if st.button("Download Excel & Clear"):
    session = get_session(st.session_state.session_id)
    path = export_excel(session["results"])
    st.download_button("Download Excel", open(path, "rb"), "results.xlsx")
    clear_session(st.session_state.session_id)
    st.session_state.session_id = None
