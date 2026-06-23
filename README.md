# Redrob Intelligent Candidate Discovery

Deterministic offline ranker for the India Runs / Redrob data and AI challenge.

## Run

```bash
python rank.py
```

This reads `data/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl`,
parses the provided `job_description.docx`, and writes `outputs/submission.csv`.

Optional parsed-JD artifact:

```bash
python precompute.py
```

## Method

The ranker is built around the JD's real intent: Senior AI Engineer for a product-focused founding team. It combines:

- semantic lexical fit against the JD and curated AI/IR terms,
- profile fit from title, 5-9 year experience band, AI/IR skills, production retrieval/ranking evidence, product-company tenure, assessments, GitHub activity, and education tier,
- availability from open-to-work status, recent activity, recruiter response rate, response time, notice period, location/relocation, interview completion, and profile completeness.

It explicitly down-weights consulting-only careers, inactive low-response profiles, honeypot-like incomplete records, and non-technical keyword-stuffed profiles.

The ranking command is CPU-only, has no network calls, and emits exactly 100 rows in the required CSV format.
