"""Reasoning string templates for submission output."""

from .schema import CandidateFeatures, ScoreBreakdown


def build_reasoning(features: CandidateFeatures, score: ScoreBreakdown) -> str:
    strengths = "; ".join(score.reasons[:2]) if score.reasons else "balanced profile signals"
    return (
        f"{features.current_title} with {features.years_of_experience:.1f} yrs; "
        f"{features.ai_core_skill_count} AI/IR core skills; "
        f"{features.product_company_months} product-company months; "
        f"response rate {features.recruiter_response_rate:.2f}; {strengths}."
    )
