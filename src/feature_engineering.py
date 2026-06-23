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

# Company size -> fit score for a product-focused founding-team role
# Sweet spot is mid-sized product companies (201-5000 employees)
COMPANY_SIZE_SCORE: Dict[str, float] = {
    "1-10":       0.55,
    "11-50":      0.75,
    "51-200":     0.88,
    "201-500":    1.00,
    "501-1000":   0.95,
    "1001-5000":  0.85,
    "5001-10000": 0.65,
    "10001+":     0.45,
}

# STEM fields that are strong signals for this role
STEM_FIELDS = {
    "computer science",
    "computer engineering",
    "information technology",
    "software engineering",
    "electronics",
    "electrical engineering",
    "mathematics",
    "statistics",
    "data science",
    "artificial intelligence",
    "machine learning",
    "information systems",
}


def _contains_term(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def build_features(candidate: Dict[str, Any], parsed_jd: ParsedJD) -> CandidateFeatures:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    # ---- Build embed_text ----
    parts = []
    if profile.get("headline"):
        parts.append(profile["headline"])
    if profile.get("summary"):
        summary = profile["summary"]
        if len(summary.split()) > 150:
            summary = " ".join(summary.split()[:150])
        parts.append(summary)

    # Most recent 3 career entries in embed_text for semantic scoring
    career_history = candidate.get("career_history", [])
    if career_history:
        recent = sorted(career_history, key=lambda x: x.get("start_date", ""), reverse=True)[:3]
        for entry in recent:
            title = entry.get("title", "")
            company = entry.get("company", "")
            industry = entry.get("industry", "")
            description = entry.get("description", "")
            desc_preview = description[:200]
            entry_str = f"{title} at {company} ({industry}): {desc_preview}"
            parts.append(entry_str)

    if "skills" in candidate and isinstance(candidate["skills"], list):
        filtered_skills = [
            s.get("name", "")
            for s in candidate["skills"]
            if s.get("proficiency", "").lower() in ("advanced", "expert")
            or s.get("duration_months", 0) >= 18
        ]
        if filtered_skills:
            parts.append("Core skills: " + ", ".join(sorted(filtered_skills)))

    if "certifications" in candidate and isinstance(candidate["certifications"], list):
        certs = [c.get("name", "") for c in candidate["certifications"] if c.get("name")]
        if certs:
            parts.append("Certifications: " + ", ".join(certs))

    embed_text = ". ".join(parts)

    # ---- Skill scores ----
    assessment_scores = {k.lower(): float(v) for k, v in signals.get("skill_assessment_scores", {}).items()}
    proficiency_map = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 1.0}
    skill_scores: Dict[str, float] = {}
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

    # ---- Must-have skill coverage ----
    matched = sum(
        1 for jd_skill in parsed_jd.must_have_skills
        if any(
            jd_skill.lower() in skill_name or skill_name in jd_skill.lower()
            for skill_name in skill_scores
        )
    )
    coverage = matched / len(parsed_jd.must_have_skills) if parsed_jd.must_have_skills else 0.0

    # ---- AI core skill count ----
    ai_core_skill_count = len({
        skill.get("name", "").lower()
        for skill in candidate.get("skills", [])
        if any(_contains_term(skill.get("name", ""), term) for term in AI_CORE_TERMS)
    })

    # Priority 3b: scan ALL career descriptions for production terms (not just last 3)
    all_text = embed_text.lower()
    all_career_text = " ".join(
        entry.get("description", "").lower()
        for entry in career_history
    )
    production_text = all_text + " " + all_career_text
    production_signal_count = sum(1 for term in PRODUCTION_TERMS if term in production_text)

    # ---- Product company months + is_consulting_only ----
    product_company_months = 0
    all_consulting = True
    has_entries = False
    for entry in career_history:
        company = entry.get("company", "").strip()
        industry = entry.get("industry", "")
        if company in CONSULTING_COMPANIES or industry in CONSULTING_INDUSTRIES:
            has_entries = True
        else:
            all_consulting = False
            product_company_months += entry.get("duration_months", 0)
    is_consulting_only = has_entries and all_consulting

    # ---- Company size score (average over non-consulting entries) ----
    size_scores = []
    for entry in career_history:
        company = entry.get("company", "").strip()
        industry = entry.get("industry", "")
        if company not in CONSULTING_COMPANIES and industry not in CONSULTING_INDUSTRIES:
            size = entry.get("company_size", "")
            if size in COMPANY_SIZE_SCORE:
                size_scores.append(COMPANY_SIZE_SCORE[size])
    company_size_score = sum(size_scores) / len(size_scores) if size_scores else 0.6

    # ---- Days since active ----
    days_since_active = 0
    if signals.get("last_active_date"):
        try:
            last_active = date.fromisoformat(signals["last_active_date"])
            days_since_active = min((date.today() - last_active).days, 730)
        except Exception:
            days_since_active = 0

    # ---- Assessment average ----
    assessment_avg = (
        sum(assessment_scores.values()) / len(assessment_scores)
        if assessment_scores else -1.0
    )

    # ---- Education: tier + best STEM field of study ----
    tier_rank = {"tier_1": 1, "tier_2": 2, "tier_3": 3, "tier_4": 4, "unknown": 5}
    edu_tier = "unknown"
    best_field = ""
    if "education" in candidate and isinstance(candidate["education"], list) and candidate["education"]:
        best_edu = min(candidate["education"], key=lambda x: tier_rank.get(x.get("tier", "unknown"), 5))
        edu_tier = best_edu.get("tier", "unknown")
        # Collect field_of_study from all degrees, pick one that's STEM if possible
        for edu in candidate["education"]:
            fos = edu.get("field_of_study", "").lower()
            if any(stem in fos for stem in STEM_FIELDS):
                best_field = fos
                break
        if not best_field:
            best_field = candidate["education"][0].get("field_of_study", "").lower()

    # ---- Honeypot check ----
    is_honeypot_candidate = is_honeypot(candidate)

    return CandidateFeatures(
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
        # New fields
        profile_views_30d=signals.get("profile_views_received_30d", 0),
        search_appearance_30d=signals.get("search_appearance_30d", 0),
        connection_count=signals.get("connection_count", 0),
        endorsements_received=signals.get("endorsements_received", 0),
        linkedin_connected=signals.get("linkedin_connected", False),
        verified_email=signals.get("verified_email", False),
        verified_phone=signals.get("verified_phone", False),
        field_of_study=best_field,
        company_size_score=company_size_score,
    )


def build_features_batch(candidates: List[Dict[str, Any]], parsed_jd: ParsedJD, show_progress: bool = True) -> List[CandidateFeatures]:
    features_list = []
    for idx, candidate in enumerate(candidates):
        features_list.append(build_features(candidate, parsed_jd))
    return features_list
