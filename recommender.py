import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
COURSES_FILE = BASE_DIR / "data" / "courses.json"

DIFFICULTY_ORDER = {
    "Beginner": 1,
    "Intermediate": 2,
    "Advanced": 3,
}


def normalize(value: str) -> str:
    """Normalize text before comparing skills and career goals."""
    return value.strip().lower()


def load_courses(file_path: Path = COURSES_FILE) -> list[dict[str, Any]]:
    """Load the course catalogue from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            courses = json.load(file)

        if not isinstance(courses, list):
            raise ValueError("Course catalogue must contain a JSON list.")

        return courses

    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Course catalogue not found: {file_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in course catalogue: {error}"
        ) from error


def get_missing_prerequisites(
    course: dict[str, Any],
    available_skills: set[str],
) -> list[str]:
    """Return prerequisites that the student does not currently have."""
    return [
        prerequisite
        for prerequisite in course.get("prerequisites", [])
        if normalize(prerequisite) not in available_skills
    ]


def student_already_knows_course(
    course: dict[str, Any],
    available_skills: set[str],
) -> bool:
    """Return True when the student already knows every skill in a course."""
    course_skills = {
        normalize(skill)
        for skill in course.get("skills", [])
    }

    return bool(course_skills) and course_skills.issubset(available_skills)


def calculate_score(
    course: dict[str, Any],
    career_goal: str,
    available_skills: set[str],
) -> int:
    """
    Calculate a transparent recommendation score.

    Career relevance: 50 points
    Missing skills: 20 points
    Prerequisite readiness: 30 points
    """
    score = 0

    career_paths = {
        normalize(path)
        for path in course.get("career_paths", [])
    }

    if normalize(career_goal) in career_paths:
        score += 50

    course_skills = {
        normalize(skill)
        for skill in course.get("skills", [])
    }

    if course_skills - available_skills:
        score += 20

    prerequisites = course.get("prerequisites", [])

    if not prerequisites:
        score += 30
    else:
        completed_count = sum(
            normalize(prerequisite) in available_skills
            for prerequisite in prerequisites
        )
        readiness = completed_count / len(prerequisites)
        score += round(readiness * 30)

    return score


def create_reason(
    course: dict[str, Any],
    career_goal: str,
    missing_prerequisites: list[str],
) -> str:
    """Generate a reliable fallback explanation without requiring an API."""
    skills = ", ".join(course.get("skills", []))

    if missing_prerequisites:
        missing_text = ", ".join(missing_prerequisites)
        return (
            f"This course develops {skills}, which supports the "
            f"{career_goal} career path. Complete or review "
            f"{missing_text} before starting it."
        )

    return (
        f"This course develops {skills}, which are relevant to becoming "
        f"a {career_goal}. You currently meet its prerequisites."
    )


def recommend_courses(
    student_profile: dict[str, Any],
    courses: list[dict[str, Any]],
    maximum_courses: int = 6,
) -> list[dict[str, Any]]:
    """Return an ordered and scored learning path for a student."""
    career_goal = student_profile.get("career_goal", "").strip()

    if not career_goal:
        raise ValueError("Student career goal is required.")

    current_skills = student_profile.get("current_skills", [])
    available_skills = {
        normalize(skill)
        for skill in current_skills
        if isinstance(skill, str)
    }

    relevant_courses = []

    for course in courses:
        career_paths = {
            normalize(path)
            for path in course.get("career_paths", [])
        }

        if normalize(career_goal) not in career_paths:
            continue

        if student_already_knows_course(course, available_skills):
            continue

        relevant_courses.append(course)

    recommended_path = []

    while relevant_courses and len(recommended_path) < maximum_courses:
        scored_courses = []

        for course in relevant_courses:
            missing_prerequisites = get_missing_prerequisites(
                course,
                available_skills,
            )
            score = calculate_score(
                course,
                career_goal,
                available_skills,
            )

            scored_courses.append(
                (
                    len(missing_prerequisites),
                    DIFFICULTY_ORDER.get(
                        course.get("difficulty", "Advanced"),
                        3,
                    ),
                    -score,
                    course,
                    missing_prerequisites,
                )
            )

        # Prefer ready courses, then easier courses, then higher scores.
        scored_courses.sort(key=lambda item: item[:3])

        _, _, negative_score, selected_course, missing = scored_courses[0]
        score = -negative_score

        recommendation = {
            "order": len(recommended_path) + 1,
            "course_id": selected_course["id"],
            "course": selected_course["name"],
            "score": score,
            "difficulty": selected_course["difficulty"],
            "duration_weeks": selected_course["duration_weeks"],
            "skills": selected_course["skills"],
            "prerequisites": selected_course["prerequisites"],
            "missing_prerequisites": missing,
            "reason": create_reason(
                selected_course,
                career_goal,
                missing,
            ),
        }

        recommended_path.append(recommendation)

        for skill in selected_course.get("skills", []):
            available_skills.add(normalize(skill))

        relevant_courses.remove(selected_course)

    return recommended_path


if __name__ == "__main__":
    sample_profile = {
        "name": "Anuj",
        "education": "MCA",
        "current_skills": ["Python", "SQL", "Django"],
        "career_goal": "Python Backend Developer",
        "experience_level": "Intermediate",
    }

    course_catalogue = load_courses()
    learning_path = recommend_courses(
        sample_profile,
        course_catalogue,
    )

    print(json.dumps(learning_path, indent=2, ensure_ascii=False))