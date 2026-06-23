"""Honeypot detection utilities."""


def is_honeypot(candidate: dict) -> bool:
    """
    Determine if a candidate is a honeypot based on suspicious profile patterns.

    Honeypots often have:
    - Empty or near-empty profile (no summary/headline)
    - Missing key fields (title, industry, education)
    - Generic/low-effort headlines
    - Missing education degree details
    - Both email AND phone unverified (strong bot/spam signal)
    - Impossible experience dates (stated years >> total career history duration)

    Args:
        candidate: Candidate dictionary from candidates.jsonl

    Returns:
        True if candidate is identified as a honeypot, False otherwise
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    # Check for empty summary or headline
    if not profile.get("summary") or not profile.get("headline"):
        return True

    # Check for missing core profile fields
    required_profile_fields = ["current_title", "current_industry"]
    if any(field not in profile for field in required_profile_fields):
        return True

    if "education" not in candidate:
        return True

    # Check for overly generic headline
    headline = profile.get("headline", "").lower()
    if any(generic_phrase in headline for generic_phrase in [
        "looking for opportunities",
        "seeking new challenges",
        "open to work",
    ]):
        return True

    # Check for missing education details
    education = candidate.get("education", [])
    if not education or not any(edu.get("degree") for edu in education):
        return True

    # NEW — Priority 1c: both email AND phone unverified is a strong bot/spam signal
    if not signals.get("verified_email", True) and not signals.get("verified_phone", True):
        return True

    # NEW — Priority 1d: impossible experience dates
    # If stated years_of_experience is more than 1.6x the total career history duration,
    # the profile has a fabricated / inflated experience claim
    years_of_experience = float(profile.get("years_of_experience", 0))
    career_history = candidate.get("career_history", [])
    if years_of_experience > 0 and career_history:
        total_career_months = sum(
            entry.get("duration_months", 0) for entry in career_history
        )
        total_career_years = total_career_months / 12.0
        # Allow up to 60% gap (overlapping jobs, gaps between jobs are normal)
        # but > 2x the career history is suspicious
        if total_career_years > 0 and years_of_experience > total_career_years * 2.0:
            return True

    # NEW — Priority 1d: expert in many skills with near-zero duration is suspicious
    skills = candidate.get("skills", [])
    expert_zero_duration = sum(
        1 for s in skills
        if s.get("proficiency", "").lower() == "expert" and s.get("duration_months", 0) < 3
    )
    if expert_zero_duration >= 5:
        return True

    return False
