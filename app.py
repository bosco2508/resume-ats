import streamlit as st
# -------------------------
# Backend imports
# -------------------------
from backend.parser import extract_text, extract_candidate_name
from backend.experience import calculate_experience
from backend.skills import skill_match
from backend.llm import hr_evaluate
from backend.jd_parser import extract_jd_attributes
from backend.jd_matcher import match_jd_attributes
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
st.set_page_config(
    page_title="GenAI Resume Screener",
    layout="wide"
)

st.title("GenAI Resume Screener – Strict HR Mode")

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
        "Minimum Experience (Years)",
        min_value=0.0,
        max_value=30.0,
        step=0.5
    )

with col2:
    mandatory_skills_input = st.text_input(
        "Mandatory Skills (comma-separated)"
    )
    mandatory_skills = [
        s.strip() for s in mandatory_skills_input.split(",") if s.strip()
    ]

st.subheader("JD Description (Responsibilities / Tools / Expectations)")
jd_description = st.text_area(
    "This text is used to infer additional requirements",
    height=180
)

# ======================================================
# SCORING WEIGHTS
# ======================================================
st.header("Scoring Weights (Dynamic)")

w1, w2, w3, w4, w5 = st.columns(5)

with w1:
    exp_w = st.slider("Experience", 0.0, 1.0, 0.30)

with w2:
    skill_w = st.slider("Mandatory Skills", 0.0, 1.0, 0.35)

with w3:
    jd_w = st.slider("JD Alignment", 0.0, 1.0, 0.15)

with w4:
    proj_w = st.slider("Projects", 0.0, 1.0, 0.10)

with w5:
    qual_w = st.slider("Resume Quality", 0.0, 1.0, 0.10)

weights = {
    "experience": exp_w,
    "skills": skill_w,
    "jd_alignment": jd_w,
    "projects": proj_w,
    "resume_quality": qual_w
}

# ======================================================
# START SESSION
# ======================================================
if st.button("Start Screening Session"):
    if not role or not mandatory_skills:
        st.error("Role and Mandatory Skills are required.")
    else:
        with st.spinner("Analyzing JD description..."):
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

        st.success("Screening session started successfully.")

# ======================================================
# RESUME UPLOAD & PROCESSING
# ======================================================
st.header("Resume Screening")

resume = st.file_uploader(
    "Upload Resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

if resume and st.button("Process Resume"):
    if not st.session_state.session_id:
        st.error("Please start a screening session first.")
    else:
        with st.spinner("Processing resume..."):
            resume_text = extract_text(resume)
            candidate_name = extract_candidate_name(resume_text)

            # -------------------------
            # Fetch JD session data
            # -------------------------
            session_data = get_session(st.session_state.session_id)
            jd_data = session_data["jd"]
            derived_attrs = jd_data["derived_attributes"]

            explicit_requirements = derived_attrs.get(
                "explicit_requirements", []
            )

            # -------------------------
            # Experience (Soft Rule)
            # -------------------------
            total_exp = calculate_experience(resume_text)
            experience_gap_reason = None

            if total_exp < jd_data["min_exp"]:
                experience_gap_reason = (
                    f"Experience below requirement: required "
                    f"{jd_data['min_exp']} years, found {total_exp} years"
                )

            # -------------------------
            # Mandatory Skill Matching
            # -------------------------
            skill_pct, matched_skills = skill_match(
                jd_data["mandatory_skills"],
                resume_text
            )

            # -------------------------
            # JD Attribute Matching
            # -------------------------
            jd_match_pct, jd_matched, jd_missing = match_jd_attributes(
                derived_attrs,
                resume_text
            )

            # -------------------------
            # Gemini HR Evaluation
            # -------------------------
            llm_eval = hr_evaluate(
                jd_data["jd_description"],
                resume_text
            )

            # -------------------------
            # Final Scoring
            # -------------------------
            score = final_score(
                experience_score=total_exp,
                skill_score=skill_pct,
                jd_score=jd_match_pct,
                project_score=llm_eval["project_relevance_score"],
                resume_quality=llm_eval["resume_quality_score"],
                weights=weights
            )

            # -------------------------
            # Rejection Reasons (EXPLICIT ONLY)
            # -------------------------
            rejection_reasons = []

            if experience_gap_reason:
                rejection_reasons.append(experience_gap_reason)

            if skill_pct < 50:
                rejection_reasons.append(
                    "Insufficient match on mandatory skills"
                )

            if jd_match_pct < 40:
                rejection_reasons.append(
                    "Low alignment with job responsibilities"
                )

            explicit_missing = [
                item for item in jd_missing
                if item in explicit_requirements
            ]

            for item in explicit_missing[:3]:
                rejection_reasons.append(
                    f"Missing explicit JD requirement: {item}"
                )

            rejection_reasons.extend(
                llm_eval.get("rejection_reasons", [])
            )

            # -------------------------
            # Final Result (JSON)
            # -------------------------
            result = {
                "candidate_name": candidate_name,
                "experience_years": total_exp,
                "experience_required": jd_data["min_exp"],
                "skill_match_pct": skill_pct,
                "jd_alignment_pct": jd_match_pct,
                "project_relevance_score": llm_eval["project_relevance_score"],
                "resume_quality_score": llm_eval["resume_quality_score"],
                "final_score": round(score, 2),
                "status": "Selected" if score >= 70 else "Rejected",
                "rejection_reasons": rejection_reasons,
                "remarks": llm_eval["remarks"]
            }

            append_result(st.session_state.session_id, result)

        st.subheader("Screening Result")
        st.json(result)

# ======================================================
# DOWNLOAD RESULTS
# ======================================================
st.header("Finalize Session")

if st.button("Download Excel & Clear Session"):
    if not st.session_state.session_id:
        st.warning("No active session.")
    else:
        session_data = get_session(st.session_state.session_id)
        results = session_data["results"]

        if not results:
            st.warning("No resumes processed.")
        else:
            file_path = export_excel(results)
            st.download_button(
                label="Download Results (Excel)",
                data=open(file_path, "rb"),
                file_name="resume_screening_results.xlsx"
            )

            clear_session(st.session_state.session_id)
            st.session_state.session_id = None
            st.success("Session cleared successfully.")
