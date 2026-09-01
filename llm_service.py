import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

DEFAULT_MODEL = "openai/gpt-oss-20b"


def create_fallback_summary(
    student_profile: dict[str, Any],
    recommendations: list[dict[str, Any]],
) -> str:
    """Return a summary when an API key is missing or the API fails."""
    career_goal = student_profile["career_goal"]

    if not recommendations:
        return (
            f"No additional courses were found for the "
            f"{career_goal} learning path."
        )

    course_names = [
        recommendation["course"]
        for recommendation in recommendations
    ]

    return (
        f"This learning path prepares you for a {career_goal} role. "
        f"Start with {course_names[0]} and progress through "
        f"{', '.join(course_names[1:])}. Focus on completing each "
        f"course's prerequisites before moving to the next stage."
    )


def generate_ai_summary(
    student_profile: dict[str, Any],
    recommendations: list[dict[str, Any]],
) -> str:
    """Generate a short personalized summary using Groq."""
    fallback_summary = create_fallback_summary(
        student_profile,
        recommendations,
    )

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return fallback_summary

    model = os.getenv(
        "GROQ_MODEL",
        DEFAULT_MODEL,
    )

    simplified_path = [
        {
            "order": item["order"],
            "course": item["course"],
            "skills": item["skills"],
            "difficulty": item["difficulty"],
        }
        for item in recommendations
    ]

    prompt = f"""
Create a short personalized career-learning summary.

Student profile:
{json.dumps(student_profile, indent=2)}

Ordered learning path:
{json.dumps(simplified_path, indent=2)}

Rules:
- Write no more than 120 words.
- Explain how this path supports the student's career goal.
- Respect the given course order.
- Mention the student's existing skills.
- Do not add courses that are not in the learning path.
- Do not make employment or salary guarantees.
- Use clear and encouraging professional language.
"""

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a career learning-path assistant. "
                        "Provide concise, factual guidance based only "
                        "on the supplied student profile and courses."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_completion_tokens=250,
        )

        generated_text = response.choices[0].message.content

        if generated_text:
            return generated_text.strip()

        return fallback_summary

    except Exception:
        return fallback_summary