import json
import re
from pathlib import Path

from recommender import load_courses, recommend_courses


BASE_DIR = Path(__file__).resolve().parent
PROFILES_FILE = BASE_DIR / "data" / "sample_profiles.json"
OUTPUT_DIR = BASE_DIR / "outputs"


def create_filename(career_goal: str) -> str:
    """Convert a career goal into a safe filename."""
    filename = career_goal.lower()
    filename = re.sub(r"[^a-z0-9]+", "_", filename)
    return filename.strip("_") + "_path.json"


def load_profiles() -> list[dict]:
    """Load sample student profiles."""
    with open(PROFILES_FILE, "r", encoding="utf-8") as file:
        profiles = json.load(file)

    if not isinstance(profiles, list):
        raise ValueError("Sample profiles must contain a JSON list.")

    return profiles


def generate_sample_outputs() -> None:
    """Generate and save recommendations for every sample profile."""
    courses = load_courses()
    profiles = load_profiles()

    OUTPUT_DIR.mkdir(exist_ok=True)

    for profile in profiles:
        recommendations = recommend_courses(
            student_profile=profile,
            courses=courses,
            maximum_courses=6,
        )

        output = {
            "student_profile": profile,
            "total_recommendations": len(recommendations),
            "recommended_learning_path": recommendations,
        }

        filename = create_filename(profile["career_goal"])
        output_file = OUTPUT_DIR / filename

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(
                output,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"Created: {output_file.name} "
            f"({len(recommendations)} recommendations)"
        )


if __name__ == "__main__":
    generate_sample_outputs()