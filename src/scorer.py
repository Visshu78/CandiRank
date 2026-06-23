"""Candidate scoring logic."""

from __future__ import annotations

import math
import re

from .config import NON_FIT_TITLE_TERMS, PREFERRED_LOCATIONS, TECHNICAL_TITLE_TERMS
from .schema import CandidateFeatures, ParsedJD, ScoreBreakdown


TOKEN_RE = re.compile(r"[a-z0-9+#.]+")


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def semantic_score(features: CandidateFeatures, parsed_jd: ParsedJD) -> float:
    text = features.embed_text.lower()
    terms = parsed_jd.must_have_skills + [
        "production",
        "real users",
        "search",
        "recommendation",
        "recommender",
        "vector",
        "product",
        "evaluation",
        "offline",
        "online",
    ]
    matched = sum(1 for term in terms if term.lower() in text)
    density = min(len(_tokenize(text)) / 700.0, 1.0)
    return _clamp((matched / len(terms)) * 0.85 + density * 0.15)


def title_score(title: str) -> float:
    title_l = title.lower()
    if any(term in title_l for term in TECHNICAL_TITLE_TERMS):
        return 1.0
    if "engineer" in title_l or "developer" in title_l:
        return 0.72
    if "analyst" in title_l and ("data" in title_l or "business" in title_l):
        return 0.45
    if any(term in title_l for term in NON_FIT_TITLE_TERMS):
        return 0.08
    return 0.25


def experience_score(years: float, parsed_jd: ParsedJD) -> float:
    if parsed_jd.min_years <= years <= parsed_jd.max_years:
        return 1.0
    if 4.0 <= years < parsed_jd.min_years:
        return 0.75
    if parsed_jd.max_years < years <= 12.0:
        return 0.78
    if years > 12.0:
        return 0.48
    return 0.2


def profile_score(features: CandidateFeatures, parsed_jd: ParsedJD) -> float:
    skill_strength = _clamp(features.must_have_skill_coverage * 0.65 + min(features.ai_core_skill_count / 8.0, 1.0) * 0.35)
    production = _clamp(features.production_signal_count / 6.0)
    product_months = _clamp(features.product_company_months / 48.0)
    assessment = 0.55 if features.assessment_avg < 0 else _clamp(features.assessment_avg / 100.0)
    github = 0.45 if features.github_activity_score < 0 else _clamp(features.github_activity_score / 100.0)
    edu = {"tier_1": 1.0, "tier_2": 0.78, "tier_3": 0.55, "tier_4": 0.35, "unknown": 0.35}.get(features.edu_tier, 0.35)

    score = (
        0.22 * title_score(features.current_title)
        + 0.16 * experience_score(features.years_of_experience, parsed_jd)
        + 0.22 * skill_strength
        + 0.18 * production
        + 0.12 * product_months
        + 0.05 * assessment
        + 0.03 * github
        + 0.02 * edu
    )

    if features.is_consulting_only:
        score *= 0.55
    if features.is_honeypot:
        score *= 0.5
    return _clamp(score)


def availability_score(features: CandidateFeatures) -> float:
    recency = math.exp(-max(features.days_since_active, 0) / 120.0)
    notice = 1.0 if features.notice_period_days <= 30 else 0.75 if features.notice_period_days <= 60 else 0.45
    response_time = 1.0 if features.avg_response_time_hours <= 48 else 0.7 if features.avg_response_time_hours <= 120 else 0.4
    location_l = features.location.lower()
    location = 1.0 if any(loc in location_l for loc in PREFERRED_LOCATIONS) else 0.75 if features.willing_to_relocate else 0.35
    completeness = _clamp(features.profile_completeness / 100.0)
    offer = 0.55 if features.offer_acceptance_rate < 0 else _clamp(features.offer_acceptance_rate)

    return _clamp(
        0.16 * (1.0 if features.open_to_work else 0.35)
        + 0.22 * recency
        + 0.22 * _clamp(features.recruiter_response_rate)
        + 0.12 * notice
        + 0.08 * response_time
        + 0.08 * location
        + 0.06 * _clamp(features.interview_completion_rate)
        + 0.03 * offer
        + 0.03 * completeness
    )


def is_disqualified(features: CandidateFeatures) -> bool:
    title_l = features.current_title.lower()
    non_fit_title = any(term in title_l for term in NON_FIT_TITLE_TERMS)
    weak_ai = features.ai_core_skill_count < 2 and features.production_signal_count < 2
    inactive = features.days_since_active > 240 and features.recruiter_response_rate < 0.15
    return features.is_honeypot or (non_fit_title and weak_ai) or inactive


def score_candidate(features: CandidateFeatures, parsed_jd: ParsedJD) -> ScoreBreakdown:
    sem = semantic_score(features, parsed_jd)
    prof = profile_score(features, parsed_jd)
    avail = availability_score(features)
    disqualified = is_disqualified(features)

    final = 0.32 * sem + 0.48 * prof + 0.20 * avail
    if disqualified:
        final *= 0.35
    if features.is_consulting_only:
        final *= 0.8

    reasons = []
    if title_score(features.current_title) >= 0.7:
        reasons.append("technical role fit")
    if features.production_signal_count >= 3:
        reasons.append("production ranking/retrieval evidence")
    if features.product_company_months >= 36:
        reasons.append("product-company depth")
    if features.open_to_work and features.days_since_active <= 60:
        reasons.append("active and open to work")
    if features.recruiter_response_rate >= 0.6:
        reasons.append("strong recruiter responsiveness")
    if features.is_consulting_only:
        reasons.append("consulting-only penalty")

    return ScoreBreakdown(
        candidate_id=features.candidate_id,
        semantic_score=sem,
        profile_score=prof,
        availability_score=avail,
        final_score=_clamp(final),
        disqualified=disqualified,
        reasons=reasons,
    )
