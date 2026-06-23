"""Honeypot detection utilities."""

def is_honeypot(candidate: dict) -> bool:
    """
    Determine if a candidate is a honeypot based on patterns.
    
    Honeypots often have:
    - Empty or near-empty profile
    - Suspiciously high skill scores without experience
    - Frequent changes in current title/company
    - Missing key details like summary or education
    
    Args:
        candidate: Candidate dictionary from candidates.jsonl
        
    Returns:
        True if candidate is identified as honeypot, False otherwise
    """
    profile = candidate.get("profile", {})

    # Check for empty summary or headline
    if not profile.get("summary") or not profile.get("headline"):
        return True
    
    # Check for missing core fields
    required_profile_fields = ["current_title", "current_industry"]
    if any(field not in profile for field in required_profile_fields):
        return True
    if "education" not in candidate:
        return True
    
    # Check for overly generic profile
    headline = profile.get("headline", "").lower()
    if any(generic_phrase in headline for generic_phrase in [
        "looking for opportunities",
        "seeking new challenges",
        "open to work"
    ]):
        return True
    
    # Check for missing education details
    education = candidate.get("education", [])
    if not education or not any(edu.get("degree") for edu in education):
        return True
    
    return False
