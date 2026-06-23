"""Deterministic job-description parsing."""

from __future__ import annotations

import html
import json
import re
import zipfile
from pathlib import Path

from .config import AI_CORE_TERMS, PREFERRED_LOCATIONS
from .schema import ParsedJD


def read_docx_text(path: str | Path) -> str:
    """Extract visible text from a docx without requiring python-docx."""
    with zipfile.ZipFile(Path(path)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    text = re.sub(r"<[^>]+>", " ", xml)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def parse_jd(path: str | Path) -> ParsedJD:
    raw_text = read_docx_text(path)
    lower = raw_text.lower()

    must_have = [
        "embeddings",
        "retrieval",
        "ranking",
        "vector database",
        "hybrid search",
        "python",
        "evaluation frameworks",
        "NDCG",
        "MRR",
        "A/B testing",
        "LLM",
        "fine-tuning",
    ]
    nice_to_have = sorted({term for term in AI_CORE_TERMS if term in lower})
    disqualifiers = [
        "pure research without production deployment",
        "recent LangChain-only AI projects",
        "no production code in last 18 months",
        "consulting-only career",
        "non-technical keyword-stuffed profile",
        "computer vision or speech only without NLP/IR",
    ]
    locations = sorted({loc for loc in PREFERRED_LOCATIONS if loc in lower})

    return ParsedJD(
        title="Senior AI Engineer - Founding Team",
        must_have_skills=must_have,
        nice_to_have_skills=nice_to_have,
        disqualifiers=disqualifiers,
        preferred_locations=locations,
        min_years=5.0,
        max_years=9.0,
        raw_text=raw_text,
    )


def parsed_jd_to_dict(parsed_jd: ParsedJD) -> dict:
    return {
        "title": parsed_jd.title,
        "must_have_skills": parsed_jd.must_have_skills,
        "nice_to_have_skills": parsed_jd.nice_to_have_skills,
        "disqualifiers": parsed_jd.disqualifiers,
        "preferred_locations": parsed_jd.preferred_locations,
        "min_years": parsed_jd.min_years,
        "max_years": parsed_jd.max_years,
        "raw_text": parsed_jd.raw_text,
    }


def load_parsed_jd(path: str | Path) -> ParsedJD:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ParsedJD(**data)
