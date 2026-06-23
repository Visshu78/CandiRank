# Redrob Intelligent Candidate Discovery Engine

An intelligent, production-grade, deterministic candidate ranking engine designed for the **India Runs / Redrob Data & AI Challenge**. 

Traditional talent acquisition tools rely on shallow keyword filters, which miss hidden gems (due to lexical mismatch) and are highly vulnerable to fake, spam, or bot-generated candidate profiles (honeypots). This system resolves these challenges by combining **semantic search capabilities**, **rich candidate behavior profiling**, and **advanced anti-honeypot heuristics** into a robust scoring pipeline.

---

## 🏗️ System Architecture & Codebase Layout

The project is structured modularly to separate feature extraction, scoring logic, and output validation:

```
├── outputs/
│   └── submission.csv          # Final ranked shortlist of top-100 candidates
├── src/
│   ├── __init__.py
│   ├── config.py               # Constants, weight ratios, domain taxonomies, and location mappings
│   ├── embedder.py             # Sentence-Transformers wrappers (BAAI/bge-base-en-v1.5) for text embeddings
│   ├── explainer.py            # Natural language rationale generator for shortlisted candidates
│   ├── feature_engineering.py  # Feature extraction pipeline (converts raw JSON to structured profiles)
│   ├── honeypot.py             # Heuristics-based bot, ghost, and fraudulent profile detector
│   ├── jd_parser.py            # DOCX parser for extracting job requirements, nice-to-haves, and experience bounds
│   ├── reranker.py             # Deterministic tie-breaking logic for candidate sorting
│   ├── schema.py               # Data models and strict schema-level input validation
│   ├── scorer.py               # Math-based scoring engine (semantic, profile, and availability subscores)
│   └── vector_store.py         # Light retrieval helpers and lexical overlap calculations
├── app.py                      # Interactive Streamlit UI to visualize and filter candidate rankings
├── precompute.py               # Utility script to precompute embeddings and index candidates
├── rank.py                     # Execution entry point (parses JD, processes 100,000 candidates, writes submission)
└── README.md                   # Complete architectural documentation (this file)
```

---

## ⚡ Execution Instructions

### 1. Requirements Installation
Ensure Python 3.8+ is installed. Install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Ranking Pipeline
To process the 100,000 candidates dataset, clean out honeypots, apply feature weighting, and output the ranked shortlist:
```bash
python rank.py
```
* **Input**: Candidate profiles from `data/` and the job description `data/.../job_description.docx`
* **Output**: A structured candidate shortlist written to `outputs/submission.csv`

### 3. Run Submission Format Validator
To verify that the output CSV conforms to all validation rules of the challenge:
```bash
python "data/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py" outputs/submission.csv
```
* **Output Expected**: `Submission is valid.`

### 4. Interactive Streamlit Dashboard
Visualize the top candidates, check their scores, and view the reasoning explanations:
```bash
python -m streamlit run app.py
```
Access the application on [http://localhost:8501](http://localhost:8501).

---

## 📐 Scoring Formulation

The final ranking metric ($S_{\text{final}}$) is computed via a multi-dimensional weighted formulation combining three core aspects:

$$S_{\text{final}} = 0.32 \times S_{\text{semantic}} + 0.48 \times S_{\text{profile}} + 0.20 \times S_{\text{availability}}$$

If a candidate is flagged as a honeypot or is otherwise disqualified (e.g. invalid title with zero AI experience), their score is heavily penalized:

$$\text{If disqualified: } S_{\text{final}} \leftarrow S_{\text{final}} \times 0.35$$
$$\text{If consulting-only career: } S_{\text{final}} \leftarrow S_{\text{final}} \times 0.80$$

---

### 1. Semantic Score ($S_{\text{semantic}}$)
Computes textual relevance between the Job Description (JD) intent and candidate profiles.
* **Text Construction**: A unified context block `embed_text` is created for each candidate from their headline, summary, certifications, core skills, and details of their three most recent jobs.
* **Matching Criteria**: Evaluates candidate text overlap with the JD's `must_have_skills` and a curated list of AI engineering production signals (e.g., *A/B testing*, *vector indexing*, *retrieval evaluation*, *offline/online metrics*).
* **Formula**:
  $$S_{\text{semantic}} = \text{clamp}\left(0.85 \times \frac{\text{matched\_terms}}{\text{total\_terms}} + 0.15 \times \text{density\_factor}\right)$$
  The `density_factor` is based on the word length of the profile (clamped at 700 words) to prevent short, keyword-stuffed entries from gaining artificial boosts.

---

### 2. Profile Score ($S_{\text{profile}}$)
Evaluates the candidate's career fit, tech stack depth, academic pedigree, and credibility.

$$S_{\text{profile}} = 0.20 \cdot S_{\text{title}} + 0.15 \cdot S_{\text{exp}} + 0.20 \cdot S_{\text{skills}} + 0.15 \cdot S_{\text{prod}} + 0.10 \cdot S_{\text{tenure}} + 0.06 \cdot S_{\text{co\_size}} + 0.05 \cdot S_{\text{assess}} + 0.03 \cdot S_{\text{github}} + 0.03 \cdot S_{\text{edu}} + 0.03 \cdot S_{\text{social}}$$

#### Subscore Details:
* **Title Score ($S_{\text{title}}$)**: Assesses current role matching. Senior AI/ML Engineers, Data Scientists, and Backend Engineers get maximum score (`1.0`), while non-technical profiles (e.g., marketing, HR) are heavily penalized (`0.08`).
* **Experience Fit ($S_{\text{exp}}$)**: Fits the candidate's experience against the target range (5–9 years). Experience within this band receives a score of `1.0`. Scores drop to `0.75` for 4 years, `0.78` for 10-12 years, and `0.48` for $>12$ years.
* **Skill Strength ($S_{\text{skills}}$)**: Blends JD skill coverage and core AI/ML proficiency:
  $$S_{\text{skills}} = 0.65 \times \text{must\_have\_coverage} + 0.35 \times \min\left(\frac{\text{ai\_core\_skills}}{8}, 1.0\right)$$
* **Production Signal ($S_{\text{prod}}$)**: Measures the count of production-grade terms scanned across **all** career history descriptions, normalized as $\min(\text{terms\_count} / 6.0, 1.0)$.
* **Product Tenure ($S_{\text{tenure}}$)**: Evaluates months spent in non-consulting, product-oriented companies, normalized as $\min(\text{months} / 48.0, 1.0)$.
* **Company Size Fit ($S_{\text{co\_size}}$)**: Scores product companies in the candidate's career history. Mid-sized product companies (201-5000 employees) are scored at `1.00`, whereas large consulting giants ($10001+$ employees) score lower (`0.45`) to optimize fit for a lean, founding product team.
* **Assessments ($S_{\text{assess}}$)**: Averages candidate assessment scores on the platform (scaled to a 0-1 range). Defaults to `0.55` if no assessments are taken.
* **GitHub Activity ($S_{\text{github}}$)**: Scores open-source contributions (scaled to a 0-1 range). Defaults to `0.45` if empty.
* **Education Pedigree ($S_{\text{edu}}$)**: Evaluates tier quality of their college (Tier 1 = `1.0`, Tier 2 = `0.78`, Tier 3 = `0.55`). The score is boosted if the field of study is STEM/CS, and penalised by a `0.7` multiplier for unrelated fields.
* **Social Score ($S_{\text{social}}$)**: Combines connection count, endorsements received, and LinkedIn linking status:
  $$S_{\text{social}} = 0.4 \times \min\left(\frac{\text{connections}}{500}, 1.0\right) + 0.4 \times \min\left(\frac{\text{endorsements}}{100}, 1.0\right) + 0.2 \times (\text{linked\_in\_connected} ? 1.0 : 0.5)$$

---

### 3. Availability Score ($S_{\text{availability}}$)
Measures the candidate's hiring intent, platform activity, and communication responsiveness.

$$S_{\text{availability}} = 0.12 \cdot A_{\text{open}} + 0.18 \cdot A_{\text{recency}} + 0.18 \cdot A_{\text{responsiveness}} + 0.10 \cdot A_{\text{notice}} + 0.08 \cdot A_{\text{time}} + 0.08 \cdot A_{\text{location}} + 0.06 \cdot A_{\text{interview}} + 0.03 \cdot A_{\text{offer}} + 0.03 \cdot A_{\text{complete}} + 0.05 \cdot A_{\text{demand}} + 0.04 \cdot A_{\text{apps}} + 0.05 \cdot A_{\text{views}}$$

#### Subscore Details:
* **Open to Work ($A_{\text{open}}$)**: Active flag on the profile (`1.0` if active, `0.35` if passive).
* **Recency of Activity ($A_{\text{recency}}$)**: Evaluates days since active on platform: $e^{-\max(\text{days}, 0) / 120.0}$.
* **Recruiter Response Rate ($A_{\text{responsiveness}}$)**: Candidate response rate to recruiter inquiries.
* **Notice Period ($A_{\text{notice}}$)**: Immediate/short notice period ($\le 30$ days) receives `1.0`, while long notice periods ($>60$ days) receive `0.45`.
* **Response Time ($A_{\text{time}}$)**: Quick response times ($\le 48$ hours) receive `1.0`, dropping to `0.4` for slow responders.
* **Location & Relocation ($A_{\text{location}}$)**: Candidates located in job hubs (e.g. Pune, Noida, Bangalore) get `1.0`. Willingness to relocate yields `0.75`; non-local candidates unwilling to relocate get `0.35`.
* **Interview Completion Rate ($A_{\text{interview}}$)**: Percentage of scheduled interviews completed.
* **Offer Acceptance Rate ($A_{\text{offer}}$)**: Past offer acceptance percentage. Defaults to `0.55` if none.
* **Profile Completeness ($A_{\text{complete}}$)**: Stated completeness score from the platform database.
* **Recruiter Demand ($A_{\text{demand}}$)**: Frequency of recruiters saving their profile over the last 30 days: $\min(\text{saves} / 10.0, 1.0)$.
* **Active Seeker Applications ($A_{\text{apps}}$)**: Applications submitted in 30 days. Moderate application volume (2-15 applications) signifies strong intent (`1.0`). Inactivity (0-1 applications) yields `0.6`, and high application spam ($>15$) yields `0.4`.
* **Profile Views & Searches ($A_{\text{views}}$)**: Combines platform search appearances and profile views:
  $$A_{\text{views}} = 0.5 \times \min\left(\frac{\text{views}}{50}, 1.0\right) + 0.5 \times \min\left(\frac{\text{search\_appearances}}{150}, 1.0\right)$$

---

## 🛡️ Anti-Honeypot Sanitation Filters

Honeypots are invalid, bot-generated, or highly fabricated candidate profiles inserted into challenge datasets to test the robustness of filtering pipelines. To keep honeypots out of the shortlisted top 100, the system executes an array of automated checks inside `src/honeypot.py`:

| Filter Rule | Logic Trigger | Rationale |
|---|---|---|
| **Credential Verification** | `verified_email == False` AND `verified_phone == False` | Standard bot/ghost registration pattern. Genuine job seekers verify at least one primary channel. |
| **Temporal Consistency** | Stated `years_of_experience` $> 2 \times$ actual duration computed from `career_history` | Detects fabricated, inflated experience summaries. |
| **Skill Inflation Trap** | $\ge 5$ skills marked as "Expert" where stated duration is $<3$ months | Detects automated skill-stuffing scripts attempting to exploit naive search indexes. |
| **Data Completeness** | Missing `summary`, `headline`, `current_title`, or `current_industry` | Incomplete profiles not suitable for professional ranking. |
| **Academic Completeness** | Empty `education` list OR education records missing degrees | Identifies incomplete or invalid academic backgrounds. |

---

## 📈 Verification & Final Shortlist Overview

Our final shortlist generated inside `outputs/submission.csv` successfully filters out all honeypots while capturing elite talent.

### Top Candidate Profile Showcase

1. **Rank 1 — CAND_0077337 (Score: 0.7785)**: 
   - **Profile**: Staff Machine Learning Engineer
   - **Details**: 7.0 years experience; 13 core AI/IR skills; 83 product-company months; 95% recruiter response rate.
   - **Key strengths**: Strong role alignment, extensive product tenure, and verified production ranking/retrieval experience.

2. **Rank 2 — CAND_0081846 (Score: 0.7746)**:
   - **Profile**: Lead AI Engineer
   - **Details**: 6.7 years experience; 13 core AI/IR skills; 79 product-company months; 73% recruiter response rate.

3. **Rank 3 — CAND_0055905 (Score: 0.7652)**:
   - **Profile**: Senior Machine Learning Engineer
   - **Details**: 8.1 years experience; 9 core AI/IR skills; 96 product-company months; 87% recruiter response rate.
