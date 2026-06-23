"""Lightweight data contracts used by the ranking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParsedJD:
    title: str
    must_have_skills: list[str]
    nice_to_have_skills: list[str] = field(default_factory=list)
    disqualifiers: list[str] = field(default_factory=list)
    preferred_locations: list[str] = field(default_factory=list)
    min_years: float = 5.0
    max_years: float = 9.0
    raw_text: str = ""


@dataclass
class CandidateFeatures:
    candidate_id: str
    embed_text: str
    years_of_experience: float
    is_senior: bool
    product_company_months: int
    is_consulting_only: bool
    current_title: str
    current_industry: str
    location: str
    country: str
    skill_scores: dict[str, float]
    must_have_skill_coverage: float
    ai_core_skill_count: int
    production_signal_count: int
    assessment_avg: float
    edu_tier: str
    open_to_work: bool
    days_since_active: int
    recruiter_response_rate: float
    avg_response_time_hours: float
    notice_period_days: int
    github_activity_score: float
    interview_completion_rate: float
    offer_acceptance_rate: float
    profile_completeness: float
    willing_to_relocate: bool
    preferred_work_mode: str
    applications_submitted_30d: int
    saved_by_recruiters_30d: int
    is_honeypot: bool
    # New fields — Priority 1 & 2 enhancements
    profile_views_30d: int
    search_appearance_30d: int
    connection_count: int
    endorsements_received: int
    linkedin_connected: bool
    verified_email: bool
    verified_phone: bool
    field_of_study: str          # best STEM field from education entries
    company_size_score: float    # avg product-company size fit score from career history


@dataclass(frozen=True)
class ScoreBreakdown:
    candidate_id: str
    semantic_score: float
    profile_score: float
    availability_score: float
    final_score: float
    disqualified: bool
    reasons: list[str]


def validate_candidate(candidate: dict[str, Any]) -> list[str]:
    """Return validation errors for fields the ranker depends on."""
    errors: list[str] = []
    for key in ("candidate_id", "profile", "career_history", "education", "skills", "redrob_signals"):
        if key not in candidate:
            errors.append(f"missing {key}")

    profile = candidate.get("profile") or {}
    signals = candidate.get("redrob_signals") or {}
    if not isinstance(profile, dict):
        errors.append("profile must be an object")
    if not isinstance(signals, dict):
        errors.append("redrob_signals must be an object")
    if not isinstance(candidate.get("career_history", []), list):
        errors.append("career_history must be a list")
    if not isinstance(candidate.get("skills", []), list):
        errors.append("skills must be a list")
    if not str(candidate.get("candidate_id", "")).startswith("CAND_"):
        errors.append("candidate_id must start with CAND_")
    return errors
