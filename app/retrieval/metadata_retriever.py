import json
from pathlib import Path

from app.retrieval.matching import tokenize


PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_DIR = PROJECT_ROOT / "app" / "metadata"


FIELD_WEIGHTS = {
    "important_keywords": 5,
    "topics": 4,
    "possible_user_queries": 4,
    "summary": 3,
    "document_purpose": 2,
    "document_type": 2,
    "content_structure": 1,
}


def stringify(value) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)

    if isinstance(value, dict):
        return " ".join(str(item) for item in value.values())

    return "" if value is None else str(value)


def load_document_metadata(document_id: str) -> dict:
    metadata_path = METADATA_DIR / f"{document_id}.json"

    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_metadata_profiles() -> list[dict]:
    profiles = []

    if not METADATA_DIR.exists():
        return profiles

    for metadata_path in METADATA_DIR.glob("*.json"):
        with open(metadata_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        profile["document_id"] = metadata_path.stem
        profiles.append(profile)

    return profiles


def score_profile(query: str, profile: dict) -> float:
    query_terms = tokenize(query)

    if not query_terms:
        return 0

    score = 0.0

    for field, weight in FIELD_WEIGHTS.items():
        field_terms = tokenize(stringify(profile.get(field)))
        overlap = query_terms.intersection(field_terms)
        score += len(overlap) * weight

    searchable_text = " ".join(
        stringify(profile.get(field))
        for field in FIELD_WEIGHTS
    ).lower()

    if query.lower() in searchable_text:
        score += 8

    return score


def select_candidate_documents(
    query: str,
    top_k: int = 5,
    relative_score_threshold: float = 0.4
) -> list[dict]:
    scored_profiles = []

    for profile in list_metadata_profiles():
        score = score_profile(query, profile)
        profile["metadata_score"] = score

        if score > 0:
            scored_profiles.append(profile)

    scored_profiles.sort(
        key=lambda profile: profile["metadata_score"],
        reverse=True
    )

    if not scored_profiles:
        return []

    minimum_score = (
        scored_profiles[0]["metadata_score"]
        * relative_score_threshold
    )

    return [
        profile
        for profile in scored_profiles
        if profile["metadata_score"] >= minimum_score
    ][:top_k]
