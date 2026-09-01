import json

import streamlit as st

from recommender import load_courses, recommend_courses
from llm_service import generate_ai_summary

st.set_page_config(
    page_title="AI Course Recommendation Agent",
    page_icon="🎓",
    layout="wide",
)


@st.cache_data
def get_courses():
    """Load and cache the course catalogue."""
    return load_courses()


def get_available_skills(courses):
    """Return all unique skills from the course catalogue."""
    skills = set()

    for course in courses:
        skills.update(course.get("skills", []))
        skills.update(course.get("prerequisites", []))

    return sorted(skills)


courses = get_courses()
available_skills = get_available_skills(courses)

career_goals = [
    "Python Backend Developer",
    "Full-Stack Developer",
    "Data Analyst",
    "Machine Learning Engineer",
    "Generative AI Engineer",
]


st.title("🎓 AI Course Recommendation Agent")

st.write(
    "Enter your background, current skills, and career goal. "
    "The agent will generate a personalized and ordered learning path."
)

st.divider()


with st.form("student_profile_form"):
    left_column, right_column = st.columns(2)

    with left_column:
        name = st.text_input(
            "Student name",
            placeholder="Enter your name",
        )

        education = st.text_input(
            "Educational background",
            placeholder="Example: BCA, MCA, B.Tech or B.Com",
        )

        experience_level = st.selectbox(
            "Experience level",
            options=[
                "Beginner",
                "Intermediate",
                "Advanced",
            ],
        )

    with right_column:
        career_goal = st.selectbox(
            "Career goal",
            options=career_goals,
        )

        current_skills = st.multiselect(
            "Current skills",
            options=available_skills,
            placeholder="Select the skills you already know",
        )

        additional_skills = st.text_input(
            "Other skills (optional)",
            placeholder="Example: Excel, Power BI, Linux",
            help="Separate multiple skills using commas.",
        )

    maximum_courses = st.slider(
        "Number of courses to recommend",
        min_value=3,
        max_value=8,
        value=6,
    )

    submitted = st.form_submit_button(
        "Generate Learning Path",
        type="primary",
        use_container_width=True,
    )


if submitted:
    if not name.strip():
        st.error("Please enter the student's name.")
        st.stop()

    if not education.strip():
        st.error("Please enter the educational background.")
        st.stop()

    extra_skills = [
        skill.strip()
        for skill in additional_skills.split(",")
        if skill.strip()
    ]

    combined_skills = list(
        dict.fromkeys(current_skills + extra_skills)
    )

    student_profile = {
        "name": name.strip(),
        "education": education.strip(),
        "current_skills": combined_skills,
        "career_goal": career_goal,
        "experience_level": experience_level,
    }

    try:
        recommendations = recommend_courses(
            student_profile=student_profile,
            courses=courses,
            maximum_courses=maximum_courses,
        )
    except ValueError as error:
        st.error(str(error))
        st.stop()

    st.success(
        f"Learning path generated successfully for {name.strip()}."
    )

    st.subheader(f"Recommended path: {career_goal}")
    with st.spinner("Generating personalized AI guidance..."):
        ai_summary = generate_ai_summary(
            student_profile,
            recommendations,
        )

    st.subheader("AI Career Guidance")
    st.info(ai_summary)

    st.divider()
    

    profile_column, result_column = st.columns(2)

    with profile_column:
        st.metric(
            "Experience level",
            experience_level,
        )

    with result_column:
        st.metric(
            "Recommended courses",
            len(recommendations),
        )

    if combined_skills:
        st.write(
            "**Current skills:** "
            + ", ".join(combined_skills)
        )
    else:
        st.write("**Current skills:** No skills provided")

    st.divider()

    if not recommendations:
        st.warning(
            "No new courses were found. You may already know "
            "the available skills for this career path."
        )

    for recommendation in recommendations:
        st.markdown(
            f"### {recommendation['order']}. "
            f"{recommendation['course']}"
        )

        score_column, difficulty_column, duration_column = st.columns(3)

        with score_column:
            st.metric(
                "Relevance score",
                f"{recommendation['score']}/100",
            )

        with difficulty_column:
            st.metric(
                "Difficulty",
                recommendation["difficulty"],
            )

        with duration_column:
            st.metric(
                "Duration",
                f"{recommendation['duration_weeks']} weeks",
            )

        st.write(
            "**Skills covered:** "
            + ", ".join(recommendation["skills"])
        )

        prerequisites = recommendation["prerequisites"]

        st.write(
            "**Prerequisites:** "
            + (
                ", ".join(prerequisites)
                if prerequisites
                else "None"
            )
        )

        st.info(recommendation["reason"])
        st.divider()

    downloadable_output = {
        "student_profile": student_profile,
        "total_recommendations": len(recommendations),
        "recommended_learning_path": recommendations,
    }

    st.download_button(
        label="Download Learning Path as JSON",
        data=json.dumps(
            downloadable_output,
            indent=2,
            ensure_ascii=False,
        ),
        file_name="recommended_learning_path.json",
        mime="application/json",
        use_container_width=True,
    )


with st.sidebar:
    st.header("How it works")

    st.write(
        "1. Enter your student profile.\n"
        "2. Select your current skills.\n"
        "3. Choose a career goal.\n"
        "4. Generate an ordered learning path."
    )

    st.info(
        "The recommendation score uses career relevance, "
        "missing skills, and prerequisite readiness."
    )