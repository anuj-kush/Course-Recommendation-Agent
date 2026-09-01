import pytest

from recommender import (
    calculate_score,
    load_courses,
    recommend_courses,
    student_already_knows_course,
)


def test_course_catalogue_loads_successfully():
    courses = load_courses()

    assert isinstance(courses, list)
    assert len(courses) >= 10
    assert all("name" in course for course in courses)
    assert all("career_paths" in course for course in courses)


def test_recommendations_match_career_goal():
    courses = load_courses()

    profile = {
        "education": "BCA",
        "current_skills": ["Python"],
        "career_goal": "Python Backend Developer",
        "experience_level": "Beginner",
    }

    recommendations = recommend_courses(
        profile,
        courses,
        maximum_courses=6,
    )

    recommended_ids = {
        recommendation["course_id"]
        for recommendation in recommendations
    }

    relevant_ids = {
        course["id"]
        for course in courses
        if profile["career_goal"] in course["career_paths"]
    }

    assert recommendations
    assert recommended_ids.issubset(relevant_ids)


def test_maximum_course_limit_is_respected():
    courses = load_courses()

    profile = {
        "education": "MCA",
        "current_skills": [],
        "career_goal": "Python Backend Developer",
        "experience_level": "Beginner",
    }

    recommendations = recommend_courses(
        profile,
        courses,
        maximum_courses=3,
    )

    assert len(recommendations) <= 3


def test_course_is_skipped_when_all_skills_are_known():
    course = {
        "skills": ["Python", "SQL"]
    }

    available_skills = {"python", "sql"}

    assert student_already_knows_course(
        course,
        available_skills,
    ) is True


def test_relevant_ready_course_receives_full_score():
    course = {
        "career_paths": ["Python Backend Developer"],
        "skills": ["Django"],
        "prerequisites": ["Python"],
    }

    score = calculate_score(
        course=course,
        career_goal="Python Backend Developer",
        available_skills={"python"},
    )

    assert score == 100


def test_missing_prerequisite_reduces_score():
    course = {
        "career_paths": ["Generative AI Engineer"],
        "skills": ["RAG"],
        "prerequisites": ["Python", "LLMs"],
    }

    score = calculate_score(
        course=course,
        career_goal="Generative AI Engineer",
        available_skills={"python"},
    )

    assert score == 85


def test_empty_career_goal_raises_error():
    courses = load_courses()

    invalid_profile = {
        "education": "BCA",
        "current_skills": ["Python"],
        "career_goal": "",
        "experience_level": "Beginner",
    }

    with pytest.raises(
        ValueError,
        match="Student career goal is required",
    ):
        recommend_courses(
            invalid_profile,
            courses,
        )


def test_recommendation_order_is_sequential():
    courses = load_courses()

    profile = {
        "education": "B.Com",
        "current_skills": [],
        "career_goal": "Data Analyst",
        "experience_level": "Beginner",
    }

    recommendations = recommend_courses(
        profile,
        courses,
        maximum_courses=6,
    )

    actual_order = [
        recommendation["order"]
        for recommendation in recommendations
    ]

    expected_order = list(
        range(1, len(recommendations) + 1)
    )

    assert actual_order == expected_order