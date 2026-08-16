import re
from core.config import WEIGHTS

def skill_match_score(cv_skills: list, job_skills: list) -> float:
    """
    Returns skill overlap score (0.0–1.0).
    Case-insensitive exact and partial matching.
    """
    if not job_skills:
        return 0.5  # neutral if no skills listed

    cv_lower = {str(s).lower() for s in cv_skills}
    matched = 0

    for js in job_skills:
        js_lower = str(js).lower()
        # Exact match
        if js_lower in cv_lower:
            matched += 1
        else:
            # Partial match (e.g. "REST" matches "REST API")
            for cs in cv_lower:
                if js_lower in cs or cs in js_lower:
                    matched += 0.5
                    break

    return min(matched / len(job_skills), 1.0)

def experience_match_score(cv_years: float, required_str: str) -> float:
    """
    Returns experience match score (0.0–1.0).
    Parses strings like '2+ years', '1-3 years', 'fresher', etc.
    """
    if not required_str:
        return 0.5  # neutral

    required_str = str(required_str).lower()

    # Extract first number found
    numbers = re.findall(r"\d+", required_str)
    if not numbers:
        return 0.5

    required_min = float(numbers[0])

    if cv_years >= required_min:
        return 1.0
    elif cv_years >= required_min * 0.6:
        return 0.6
    elif cv_years >= required_min * 0.3:
        return 0.3
    else:
        return 0.0

def location_match_score(cv_location: str, job_location: str) -> float:
    """
    Returns location match score (0.0–1.0).
    Remote jobs always score 1.0.
    Same city/country gets 1.0.
    """
    if not job_location:
        return 0.5

    job_loc = job_location.lower()
    cv_loc = (cv_location or "").lower()

    # Remote jobs are always a match
    if "remote" in job_loc:
        return 1.0

    # Check for city/country overlap
    cv_tokens = set(cv_loc.replace(",", " ").split())
    job_tokens = set(job_loc.replace(",", " ").split())

    overlap = cv_tokens & job_tokens
    if overlap:
        return 1.0

    # Different location
    return 0.2

def compute_match_score(cv_profile: dict, job_info: dict, semantic_score: float) -> dict:
    """
    Computes a comprehensive match score for one CV vs one job.
    Returns a dict with sub-scores and total score (0–100).
    """

    # --- Skill Score ---
    cv_skills   = cv_profile.get("skills", []) + cv_profile.get("frameworks", []) + cv_profile.get("languages", [])
    job_skills  = job_info.get("skills", [])
    s_skill     = skill_match_score(cv_skills, job_skills)

    # --- Experience Score ---
    cv_years    = float(cv_profile.get("experience_years", 0) or 0)
    req_exp     = str(job_info.get("experience_years", "") or "")
    s_exp       = experience_match_score(cv_years, req_exp)

    # --- Location Score ---
    cv_loc      = cv_profile.get("location", "")
    job_loc     = job_info.get("location", "")
    s_loc       = location_match_score(cv_loc, job_loc)

    # --- Weighted Total ---
    total = (
        s_skill      * WEIGHTS["skill"] +
        s_exp        * WEIGHTS["experience"] +
        s_loc        * WEIGHTS["location"] +
        semantic_score * WEIGHTS["semantic"]
    ) * 100  # convert to 0–100

    total = round(total, 1)

    return {
        "skill_score"      : round(s_skill * 100, 1),
        "experience_score" : round(s_exp * 100, 1),
        "location_score"   : round(s_loc * 100, 1),
        "semantic_score"   : round(semantic_score * 100, 1),
        "total_score"      : total
    }

def score_to_stars(score: float) -> int:
    """Maps 0–100 score to 1–5 stars."""
    if score >= 85:
        return 5
    elif score >= 70:
        return 4
    elif score >= 50:
        return 3
    elif score >= 30:
        return 2
    else:
        return 1
