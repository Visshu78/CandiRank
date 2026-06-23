#!/usr/bin/env python3
"""Produce a Redrob challenge submission CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.config import DEFAULT_CANDIDATES_PATH, DEFAULT_JD_PATH, DEFAULT_OUTPUT_PATH
from src.explainer import build_reasoning
from src.feature_engineering import build_features
from src.jd_parser import parse_jd
from src.reranker import rerank_key
from src.schema import validate_candidate
from src.scorer import score_candidate


def iter_candidates(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc


def rank_candidates(candidates_path: Path, jd_path: Path, limit: int = 100):
    parsed_jd = parse_jd(jd_path)
    ranked = []
    skipped = 0

    for candidate in iter_candidates(candidates_path):
        errors = validate_candidate(candidate)
        if errors:
            skipped += 1
            continue

        features = build_features(candidate, parsed_jd)
        score = score_candidate(features, parsed_jd)
        ranked.append((features, score))

    ranked.sort(key=rerank_key, reverse=True)
    top = ranked[:limit]
    if len(top) < limit:
        raise RuntimeError(f"Only {len(top)} valid candidates found; need {limit}. Skipped {skipped}.")
    return top


def write_submission(rows, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        previous_score = 1.0
        for rank, (features, score) in enumerate(rows, start=1):
            adjusted_score = min(score.final_score, previous_score - 0.0001)
            adjusted_score = max(adjusted_score, 0.0001)
            previous_score = adjusted_score
            writer.writerow(
                [
                    features.candidate_id,
                    rank,
                    f"{adjusted_score:.4f}",
                    build_reasoning(features, score),
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank Redrob candidates and write submission.csv")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--jd", type=Path, default=DEFAULT_JD_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    rows = rank_candidates(args.candidates, args.jd, args.limit)
    write_submission(rows, args.out)
    print(f"Wrote {args.limit} ranked candidates to {args.out}")
    print(f"Top candidate: {rows[0][0].candidate_id} score={rows[0][1].final_score:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
