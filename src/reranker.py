"""Deterministic tie-break reranker.

The architecture leaves room for a cross-encoder precision gate. For the
offline submission we keep ranking deterministic and dependency-light.
"""

from .schema import CandidateFeatures, ScoreBreakdown


def rerank_key(item: tuple[CandidateFeatures, ScoreBreakdown]) -> tuple[float, int, float, str]:
    features, score = item
    return (
        score.final_score,
        features.production_signal_count,
        features.recruiter_response_rate,
        "".join(reversed(features.candidate_id)),
    )
