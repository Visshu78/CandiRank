"""Feature engineering utilities for candidate profiling."""

from datetime import date
from typing import List, Dict, Any

from .schema import CandidateFeatures, ParsedJD
from .config import AI_CORE_TERMS, CONSULTING_COMPANIES, CONSULTING_INDUSTRIES
from .honeypot import is_honeypot


PRODUCTION_TERMS = {
    "production",
    "deployed",
    "real users",
    "ranking",
    "retrieval",
    "search",
    "recommendation",
    "recommender",
    "embeddings",
    "vector",
    "index",
    "a/b",
    "ab test",
    "ndcg",
    "mrr",
    "map",
}


def _contains_term(text: str, term: str) -> bool:
    return term.lower() in text.lower()

def build_features(candidate: Dict[str, Any], parsed_jd: ParsedJD) -> CandidateFeatures:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    # Build embed_text
    parts = []
    # 1. profile.headline
    if profile.get("headline"):
        parts.append(profile["headline"])
    # 2. profile.summary (truncate)
    if profile.get("summary"):
        summary = profile["summary"]
        if len(summary.split()) > 150:
            summary = " ".join(summary.split()[:150])
        parts.append(summary)
    # 3. Most recent 3 career_history entries
    if "career_history" in candidate and isinstance(candidate["career_history"], list):
        recent = sorted(candidate["career_history"], key=lambda x: x.get("start_date", ""), reverse=True)[:3]
        for entry in recent:
            title = entry.get("title", "")
            company = entry.get("company", "")
            industry = entry.get("industry", "")
            description = entry.get("description", "")
            desc_preview = description[:200]
            entry_str = f"{title} at {company} ({industry}): {desc_preview}"
            parts.append(entry_str)
    # 4. Core skills
    # Assume candidate has "skills" list with dicts containing "name" and "proficiency"
    if "skills" in candidate and isinstance(candidate["skills"], list):
        # Filter skills with proficiency advanced/expert or duration >= 18 months
        filtered_skills = []
        for skill in candidate["skills"]:
            prof = skill.get("proficiency", "").lower()
            duration = skill.get("duration_months", 0)
            if prof in ["advanced", "expert"] or duration >= 18:
                filtered_skills.append(skill.get("name", ""))
        if filtered_skills:
            parts.append("Core skills: " + ", ".join(sorted(filtered_skills)))
    # 5. Certifications
    if "certifications" in candidate and isinstance(candidate["certifications"], list):
        certs = [c.get("name", "") for c in candidate["certifications"] if c.get("name")]
        if certs:
            parts.append("Certifications: " + ", ".join(certs))
    embed_text = ". ".join(parts)

    # Build skill_scores
    skill_scores = {}
    assessment_scores = {k.lower(): float(v) for k, v in signals.get("skill_assessment_scores", {}).items()}
    proficiency_map = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 1.0}
    for skill in candidate.get("skills", []):
        name = skill.get("name", "").lower()
        p = proficiency_map.get(skill.get("proficiency", "").lower(), 0.5)
        d = min(skill.get("duration_months", 0) / 60.0, 1.0)
        e = min(skill.get("endorsements", 0) / 50.0, 1.0) if "endorsements" in skill else 0.0
        assessment = assessment_scores.get(name, -1.0)
        if assessment >= 0:
            score = 0.35 * p + 0.30 * d + 0.25 * (assessment / 100.0) + 0.10 * e
        else:
            score = 0.45 * p + 0.45 * d + 0.10 * e
        skill_scores[name] = score

    # Build must_have_skill_coverage
    matched = 0
    for jd_skill in parsed_jd.must_have_skills:
        jd_skill_lower = jd_skill.lower()
        if any(jd_skill_lower in skill_name or skill_name in jd_skill_lower for skill_name in skill_scores.keys()):
            matched += 1
    coverage = matched / len(parsed_jd.must_have_skills) if parsed_jd.must_have_skills else 0.0

    all_text = " ".join(parts).lower()
    ai_core_skill_count = len(
        {
            skill.get("name", "").lower()
            for skill in candidate.get("skills", [])
            if any(_contains_term(skill.get("name", ""), term) for term in AI_CORE_TERMS)
        }
    )
    production_signal_count = sum(1 for term in PRODUCTION_TERMS if term in all_text)

    # Build product_company_months
    total_months = 0
    for entry in candidate.get("career_history", []):
        company = entry.get("company", "").strip()
        industry = entry.get("industry", "")
        if company not in CONSULTING_COMPANIES and industry not in CONSULTING_INDUSTRIES:
            total_months += entry.get("duration_months", 0)
    product_company_months = total_months

    # Build is_consulting_only
    all_consulting = True
    has_entries = False
    for entry in candidate.get("career_history", []):
        company = entry.get("company", "").strip()
        industry = entry.get("industry", "")
        if company in CONSULTING_COMPANIES or industry in CONSULTING_INDUSTRIES:
            has_entries = True
        else:
            all_consulting = False
    is_consulting_only = has_entries and all_consulting

    # Build days_since_active
    if signals.get("last_active_date"):
        try:
            last_active = date.fromisoformat(signals["last_active_date"])
            days_since = (date.today() - last_active).days
            days_since_active = min(days_since, 730)
        except Exception:
            days_since_active = 0
    else:
        days_since_active = 0

    # Build assessment_avg
    if assessment_scores:
        assessment_avg = sum(assessment_scores.values()) / len(assessment_scores)
    else:
        assessment_avg = -1.0

    # Build edu_tier
    tier_rank = {"tier_1": 1, "tier_2": 2, "tier_3": 3, "tier_4": 4, "unknown": 5}
    edu_tier = "tier_1"
    if "education" in candidate and isinstance(candidate["education"], list):
        # Assume lowest tier number is best; pick the one with smallest rank
        edu_tier = min(candidate["education"], key=lambda x: tier_rank.get(x.get("tier", "unknown"), 5)).get("tier", "unknown")
    else:
        edu_tier = "unknown"

    # Build is_honeypot via honeypot detection
    is_honeypot_candidate = is_honeypot(candidate)

    # Build CandidateFeatures
    features = CandidateFeatures(
        candidate_id=candidate.get("candidate_id", ""),
        embed_text=embed_text,
        years_of_experience=float(profile.get("years_of_experience", 0)),
        is_senior=float(profile.get("years_of_experience", 0)) >= 5,
        product_company_months=product_company_months,
        is_consulting_only=is_consulting_only,
        current_title=profile.get("current_title", ""),
        current_industry=profile.get("current_industry", ""),
        location=profile.get("location", ""),
        country=profile.get("country", ""),
        skill_scores=skill_scores,
        must_have_skill_coverage=coverage,
        ai_core_skill_count=ai_core_skill_count,
        production_signal_count=production_signal_count,
        assessment_avg=assessment_avg,
        edu_tier=edu_tier,
        open_to_work=signals.get("open_to_work_flag", False),
        days_since_active=days_since_active,
        recruiter_response_rate=signals.get("recruiter_response_rate", 0.0),
        avg_response_time_hours=signals.get("avg_response_time_hours", 0.0),
        notice_period_days=signals.get("notice_period_days", 0),
        github_activity_score=signals.get("github_activity_score", -1.0),
        interview_completion_rate=signals.get("interview_completion_rate", 0.0),
        offer_acceptance_rate=signals.get("offer_acceptance_rate", -1.0),
        profile_completeness=signals.get("profile_completeness_score", 0.0),
        willing_to_relocate=signals.get("willing_to_relocate", False),
        preferred_work_mode=signals.get("preferred_work_mode", ""),
        applications_submitted_30d=signals.get("applications_submitted_30d", 0),
        saved_by_recruiters_30d=signals.get("saved_by_recruiters_30d", 0),
        is_honeypot=is_honeypot_candidate,
    )

    return features

def build_features_batch(candidates: List[Dict[str, Any]], parsed_jd: ParsedJD, show_progress: bool = True) -> List[CandidateFeatures]:
    features_list = []
    total = len(candidates)
    for idx, candidate in enumerate(candidates):
        if show_progress and idx % 100 == 0:
            pass  # progress could be printed
        features = build_features(candidate, parsed_jd)
        features_list.append(features)
    return features_list
