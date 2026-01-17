import streamlit as st
import pandas as pd

from backend.parser import extract_text, extract_candidate_name
from backend.experience import calculate_experience
from backend.skills import skill_match, hard_fail_mandatory_skills
from backend.llm import hr_evaluate
from backend.jd_parser import extract_weighted_keywords
from backend.vector_matcher import (
    keyword_based_jd_score,
    keyword_coverage_report
)
from backend.scorer import final_score, normalize_weights
from backend.firebase_db import (
    create_session,
    append_result,
    get_session,
    clear_session
)
from backend.exporter import export_excel

# -------------------------------------------------
# Page setup
# -------------------------------------------------
st.set_page_config(
    page_title="GenAI Resume Screener",
    layout="wide"
)

st.title("GenAI Resume Screener – ATS Mode")

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# =================================================
# JOB DESCRIPTION INPUT
# =================================================
st.header("Job Description")

col1, col2 = st.columns(2)

with col1:
    role = st.text_input("Job Title")
    min_exp = st.number_input(
        "Minimum Experience (Years)",
        min_value=0.0,
        max_value=30.0,
        step=0.5
    )

with col2:
    skills_input = st.text_input("Mandatory Skills (comma-separated)")
    mandatory_skills = [
        s.strip() for s in skills_input.split(",") if s.strip()
    ]

jd_description = st.text_area(
    "Job Description",
    height=180
)

# =================================================
# HR WEIGHT SELECTION
# =================================================
st.header("Scoring Priority (HR Controlled)")

exp_w = st.slider("Experience", 0.0, 1.0, 0.3)
skill_w = st.slider("Mandatory Skills", 0.0, 1.0, 0.35)
jd_w = st.slider("JD Keyword Alignment", 0.0, 1.0, 0.2)
proj_w = st.slider("Projects", 0.0, 1.0, 0.1)
qual_w = st.slider("Resume Quality", 0.0, 1.0, 0.05)

weights_ui = {
    "experience": exp_w,
    "skills": skill_w,
    "jd_alignment": jd_w,
    "projects": proj_w,
    "resume_quality": qual_w
}

# =================================================
# START SESSION
# =================================================
if st.button("Start Screening Session"):
    if not role or not mandatory_skills:
        st.error("Job title and mandatory skills are required.")
    else:
        try:
            weights = normalize_weights(weights_ui)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        keyword_weights = extract_weighted_keywords(
            jd_description,
            role,
            mandatory_skills
        )

        st.session_state.session_id = create_session(
            jd={
                "role": role,
                "min_exp": min_exp,
                "mandatory_skills": mandatory_skills,
                "jd_description": jd_description,
                "keyword_weights": keyword_weights
            },
            weights=weights
        )

        st.success("Screening session started")
        st.info(f"Applied weights: {weights}")

# =================================================
# RESUME PROCESSING
# =================================================
st.header("Resume Screening")

resume = st.file_uploader(
    "Upload Resume (PDF / DOCX)",
    type=["pdf", "docx"]
)

if resume and st.button("Process Resume"):
    if not st.session_state.session_id:
        st.error("Start a screening session first.")
        st.stop()

    session = get_session(st.session_state.session_id)
    jd_data = session["jd"]
    weights = session["weights"]

    resume_text = extract_text(resume)
    candidate_name = extract_candidate_name(resume_text)
    experience = calculate_experience(resume_text)

    # ---------------- HARD FAIL ----------------
    passed, missing_skills = hard_fail_mandatory_skills(
        jd_data["mandatory_skills"],
        resume_text
    )

    if not passed:
        result = {
            "candidate_name": candidate_name,
            "experience_years": experience,
            "final_score": 0,
            "status": "Rejected",
            "rejection_reasons": [
                f"Missing mandatory skill: {s}"
                for s in missing_skills
            ],
            "remarks": "Auto-rejected due to missing mandatory skills"
        }

        append_result(st.session_state.session_id, result)
        st.json(result)
        st.stop()

    # ---------------- SOFT MATCHING ----------------
    skill_pct, _ = skill_match(
        jd_data["mandatory_skills"],
        resume_text
    )

    jd_match_pct = keyword_based_jd_score(
        jd_data["keyword_weights"],
        resume_text
    )

    llm_eval = hr_evaluate(
        jd_data["jd_description"],
        resume_text
    )

    score = final_score(
        experience_score=experience,
        skill_score=skill_pct,
        jd_score=jd_match_pct,
        project_score=llm_eval["project_relevance_score"],
        resume_quality=llm_eval["resume_quality_score"],
        weights=weights
    )

    status = "Selected" if score >= 70 else "Rejected"

    result = {
        "candidate_name": candidate_name,
        "experience_years": experience,
        "skill_match_pct": skill_pct,
        "jd_alignment_pct": jd_match_pct,
        "project_relevance_score": llm_eval["project_relevance_score"],
        "resume_quality_score": llm_eval["resume_quality_score"],
        "final_score": score,
        "status": status,
        "remarks": llm_eval["remarks"]
    }

    append_result(st.session_state.session_id, result)

    st.subheader("Screening Result")
    st.json(result)

    # =================================================
    # KEYWORD COVERAGE VISUALIZATION
    # =================================================
    coverage = keyword_coverage_report(
        jd_data["keyword_weights"],
        resume_text
    )

    df = pd.DataFrame(coverage)

    st.subheader("Keyword Coverage Analysis")

    st.metric(
        "Keyword Coverage %",
        f"{round((df['present'].sum() / len(df)) * 100, 2)}%"
    )

    st.dataframe(
        df.sort_values("weight", ascending=False),
        use_container_width=True
    )

    st.bar_chart(
        df.set_index("keyword")["present"].astype(int)
    )

# =================================================
# EXPORT & CLEAR
# =================================================
st.header("Finalize Session")

if st.button("Download Excel & Clear Session"):
    if not st.session_state.session_id:
        st.warning("No active session.")
    else:
        session = get_session(st.session_state.session_id)
        file_path = export_excel(session["results"])

        st.download_button(
            label="Download Results (Excel)",
            data=open(file_path, "rb"),
            file_name="resume_screening_results.xlsx"
        )

        clear_session(st.session_state.session_id)
        st.session_state.session_id = None
        st.success("Session cleared successfully.")
