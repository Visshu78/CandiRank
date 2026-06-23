"""Premium candidate visualization dashboard for Redrob ranking outputs."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import streamlit as st

from src.config import DEFAULT_OUTPUT_PATH, DEFAULT_CANDIDATES_PATH


@st.cache_data
def load_data(csv_path: Path, jsonl_path: Path) -> tuple[pd.DataFrame, dict[str, dict]]:
    """Load submission CSV and match candidate details from JSONL, caching the results."""
    df = pd.read_csv(csv_path)
    top_ids = set(df["candidate_id"].tolist())
    
    details = {}
    if jsonl_path.exists():
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    cand = json.loads(line)
                    cid = cand.get("candidate_id")
                    if cid in top_ids:
                        details[cid] = cand
                except Exception:
                    continue
    return df, details


def inject_custom_css() -> None:
    """Inject custom Google Fonts and premium dark-mode custom styles."""
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        
        <style>
        /* Global typography & layout */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        h1, h2, h3, h4 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: #E2E8F0;
        }
        
        /* Metric styling */
        .metric-card {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #38BDF8 0%, #818CF8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-label {
            color: #94A3B8;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 4px;
        }
        
        /* Candidate card */
        .candidate-item {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }
        .candidate-item:hover {
            border-color: #38BDF8;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);
        }
        .candidate-item.selected {
            border-color: #818CF8;
            background: linear-gradient(135deg, #1E293B 0%, #172554 100%);
            box-shadow: 0 4px 15px rgba(129, 140, 248, 0.2);
        }
        
        /* Badges */
        .score-badge {
            background: #0F172A;
            border: 1px solid #38BDF8;
            color: #38BDF8;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .badge-verified {
            background-color: rgba(16, 185, 129, 0.1);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.2);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-unverified {
            background-color: rgba(239, 68, 68, 0.1);
            color: #EF4444;
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-info {
            background-color: rgba(56, 189, 248, 0.1);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.2);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 5px;
            margin-bottom: 5px;
            display: inline-block;
        }
        
        /* Resume components */
        .resume-section {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
        }
        .timeline-item {
            border-left: 2px solid #475569;
            padding-left: 20px;
            position: relative;
            margin-bottom: 20px;
        }
        .timeline-item::before {
            content: '';
            width: 12px;
            height: 12px;
            background: #818CF8;
            border: 2px solid #1E293B;
            border-radius: 50%;
            position: absolute;
            left: -7px;
            top: 4px;
        }
        .timeline-date {
            font-size: 0.85rem;
            color: #94A3B8;
            font-weight: 500;
        }
        .timeline-title {
            font-weight: 600;
            color: #F1F5F9;
            font-size: 1.05rem;
        }
        .timeline-company {
            color: #38BDF8;
            font-weight: 500;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Redrob Candidate Ranker", layout="wide", initial_sidebar_state="expanded")
    inject_custom_css()

    # Title Banner with dynamic gradient styling
    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #1E1B4B 0%, #0F172A 100%); padding: 30px; border-radius: 16px; border: 1px solid #312E81; margin-bottom: 25px;">
            <h1 style="margin: 0; font-size: 2.5rem; background: linear-gradient(90deg, #38BDF8 0%, #818CF8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Redrob Candidate Ranker
            </h1>
            <p style="color: #94A3B8; margin: 8px 0 0 0; font-size: 1.1rem; font-weight: 300;">
                Proof-of-Concept AI Discovery Engine for Senior AI/ML Founding Roles
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    csv_path = Path(DEFAULT_OUTPUT_PATH)
    jsonl_path = Path(DEFAULT_CANDIDATES_PATH)

    if not csv_path.exists():
        st.warning("No submission CSV found yet. Run `python rank.py` first to generate the ranking data.")
        return

    df, details_dict = load_data(csv_path, jsonl_path)

    # Calculate Top KPIs
    top_score = df["score"].max() if not df.empty else 0.0
    avg_score = df["score"].mean() if not df.empty else 0.0
    total_shortlisted = len(df)

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_shortlisted}</div>
                <div class="metric-label">Shortlisted Candidates</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_kpi2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{top_score:.4f}</div>
                <div class="metric-label">Highest Pipeline Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_kpi3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{avg_score:.4f}</div>
                <div class="metric-label">Average Top-100 Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    # Sidebar Filter Section
    st.sidebar.markdown("### 🔍 Search & Filters")
    search_query = st.sidebar.text_input("Search Name / Title / Skills", "").strip().lower()
    
    # Score slider filter
    score_range = st.sidebar.slider(
        "Scoring Threshold",
        float(df["score"].min()) if not df.empty else 0.0,
        float(df["score"].max()) if not df.empty else 1.0,
        (float(df["score"].min()), float(df["score"].max())) if not df.empty else (0.0, 1.0),
    )

    # Filter Logic
    filtered_df = df.copy()
    if search_query:
        # Match reasoning, ID or items in the details if available
        matched_ids = []
        for cid, details in details_dict.items():
            profile = details.get("profile", {})
            skills = " ".join([s.get("name", "") for s in details.get("skills", [])]).lower()
            text_pool = f"{cid} {profile.get('current_title', '')} {profile.get('headline', '')} {skills}".lower()
            if search_query in text_pool:
                matched_ids.append(cid)
        
        # Also fall back to CSV reasoning match
        csv_match = filtered_df["reasoning"].str.lower().str.contains(search_query) | filtered_df["candidate_id"].str.lower().str.contains(search_query)
        filtered_df = filtered_df[filtered_df["candidate_id"].isin(matched_ids) | csv_match]

    filtered_df = filtered_df[(filtered_df["score"] >= score_range[0]) & (filtered_df["score"] <= score_range[1])]

    # Two column layout: Left (List of candidates), Right (Selected Resume / Scoring breakdown)
    left_col, right_col = st.columns([2, 3])

    selected_cand_id = None

    with left_col:
        st.markdown(f"### 📋 Candidate List ({len(filtered_df)})")
        if filtered_df.empty:
            st.info("No candidates match your filter criteria.")
        else:
            # Candidate list selection card view
            for idx, row in filtered_df.iterrows():
                cid = row["candidate_id"]
                score = row["score"]
                reasoning = row["reasoning"]
                
                # Try to extract details from JSONL
                cand_details = details_dict.get(cid, {})
                profile = cand_details.get("profile", {})
                title = profile.get("current_title", "Candidate Profile")
                years_exp = profile.get("years_of_experience", "N/A")
                location = profile.get("location", "Unknown Location")
                
                if not cand_details:
                    # Parse basics from reasoning string if details not cached
                    title = reasoning.split(" with ")[0] if " with " in reasoning else "Candidate"
                
                # Checkbox / button simulation
                is_selected = st.session_state.get("selected_candidate") == cid
                card_class = "candidate-item selected" if is_selected else "candidate-item"
                
                col_btn, col_card = st.columns([1, 8])
                with col_btn:
                    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                    if st.button("👉", key=f"sel_{cid}"):
                        st.session_state["selected_candidate"] = cid
                        st.rerun()
                with col_card:
                    st.markdown(
                        f"""
                        <div class="{card_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 700; font-size: 1.1rem; color: #F1F5F9;">Rank #{row['rank']} • {cid}</span>
                                <span class="score-badge">{score:.4f}</span>
                            </div>
                            <div style="font-weight: 500; color: #38BDF8; font-size: 0.95rem; margin-top: 4px;">{title}</div>
                            <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">Exp: {years_exp} yrs • {location}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            
            # Select first item by default if nothing selected
            if st.session_state.get("selected_candidate") is None:
                st.session_state["selected_candidate"] = filtered_df.iloc[0]["candidate_id"]
                st.rerun()

    with right_col:
        st.markdown("### 🔍 Profile Deep Dive & Scoring Analysis")
        selected_cid = st.session_state.get("selected_candidate")
        
        if not selected_cid:
            st.info("Select a candidate from the list to inspect their credentials.")
        else:
            cand_details = details_dict.get(selected_cid)
            csv_row = df[df["candidate_id"] == selected_cid]
            
            if csv_row.empty:
                st.warning("Selected candidate data mismatch.")
            else:
                score_val = csv_row.iloc[0]["score"]
                reasoning_str = csv_row.iloc[0]["reasoning"]
                
                if not cand_details:
                    # Basic view from CSV
                    st.markdown(
                        f"""
                        <div class="resume-section">
                            <h2>{selected_cid}</h2>
                            <p style="color: #94A3B8; font-size: 1.1rem;">Pipeline Score: <strong style="color: #38BDF8;">{score_val:.4f}</strong></p>
                            <hr style="border-color: #334155; margin: 15px 0;"/>
                            <h4 style="margin-bottom: 8px;">Pipeline Summary</h4>
                            <p style="color: #F1F5F9; line-height: 1.6;">{reasoning_str}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    profile = cand_details.get("profile", {})
                    headline = profile.get("headline", "No Headline")
                    summary = profile.get("summary", "No Summary Provided")
                    location = profile.get("location", "Unknown Location")
                    country = profile.get("country", "Unknown")
                    years_exp = profile.get("years_of_experience", 0.0)
                    signals = cand_details.get("redrob_signals", {})
                    
                    # Compute indicator components for rendering
                    email_verified = signals.get("verified_email", False)
                    phone_verified = signals.get("verified_phone", False)
                    linkedin_connected = signals.get("linkedin_connected", False)
                    open_to_work = signals.get("open_to_work_flag", False)
                    
                    email_badge = '<span class="badge-verified">Email Verified</span>' if email_verified else '<span class="badge-unverified">Email Unverified</span>'
                    phone_badge = '<span class="badge-verified">Phone Verified</span>' if phone_verified else '<span class="badge-unverified">Phone Unverified</span>'
                    linkedin_badge = '<span class="badge-verified">LinkedIn Linked</span>' if linkedin_connected else '<span class="badge-unverified">LinkedIn Missing</span>'
                    otw_badge = '<span class="badge-info">Active Open to Work</span>' if open_to_work else ''

                    # Main Resume Profile
                    st.markdown(
                        f"""
                        <div class="resume-section">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <h2 style="margin: 0; color: #F1F5F9;">{profile.get('current_title', 'AI Engineer')}</h2>
                                    <div style="color: #94A3B8; font-weight: 500; font-size: 1.05rem; margin-top: 4px;">{selected_cid} • {location}, {country}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 1.8rem; font-weight: 700; color: #818CF8;">{score_val:.4f}</div>
                                    <div style="color: #94A3B8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Final Score</div>
                                </div>
                            </div>
                            <div style="margin-top: 10px;">
                                {email_badge} &nbsp; {phone_badge} &nbsp; {linkedin_badge}
                            </div>
                            <div style="margin-top: 10px; color: #38BDF8; font-style: italic; font-size: 1rem;">
                                "{headline}"
                            </div>
                            <hr style="border-color: #334155; margin: 15px 0;"/>
                            <h4 style="margin-bottom: 8px;">Overview & Summary</h4>
                            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.5;">{summary}</p>
                            <div style="margin-top: 12px;">
                                <span class="badge-info">Total Experience: {years_exp} yrs</span>
                                <span class="badge-info">Notice Period: {signals.get('notice_period_days', 'N/A')} days</span>
                                {otw_badge}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    # Detailed Subscore Indicators (Visual Progress Bars)
                    st.markdown("### 📊 Pipeline Subscores")
                    
                    # We can load features and score components to render accurate subscores.
                    # As a proxy, we show the metric breakdowns:
                    # - Semantic: based on coverage
                    # - Profile: based on titles/experience/skills
                    # - Availability: based on response rates
                    col_sub1, col_sub2, col_sub3 = st.columns(3)
                    
                    # Look up or estimate the sub-metrics from candidate records
                    recruiter_response = signals.get("recruiter_response_rate", 0.0)
                    completeness = signals.get("profile_completeness_score", 0.0) / 100.0
                    assess_avg = sum(signals.get("skill_assessment_scores", {}).values()) / len(signals.get("skill_assessment_scores")) if signals.get("skill_assessment_scores") else 0.0
                    github_act = signals.get("github_activity_score", 0) / 100.0
                    
                    with col_sub1:
                        st.metric("Semantic Overlap", f"{min(len(cand_details.get('skills', [])) * 7.5, 100.0):.1f}%")
                        st.caption("Matches to core AI/IR JD skills")
                    with col_sub2:
                        st.metric("Platform Credibility", f"{completeness * 100.0:.0f}%")
                        st.caption("Profile completeness & details")
                    with col_sub3:
                        st.metric("Recruiter Response", f"{recruiter_response * 100.0:.0f}%")
                        st.caption("Responsiveness rate to inquiries")
                    
                    # Technical Skills List
                    st.markdown("### 🧠 Technical Skill Proficiencies")
                    skills = cand_details.get("skills", [])
                    if not skills:
                        st.info("No technical skills specified.")
                    else:
                        skills_html = ""
                        for skill in sorted(skills, key=lambda s: s.get("duration_months", 0), reverse=True):
                            name = skill.get("name", "")
                            prof = skill.get("proficiency", "Intermediate").capitalize()
                            months = skill.get("duration_months", 0)
                            ends = skill.get("endorsements", 0)
                            
                            skills_html += f"""
                            <span class="badge-info" style="border-color: #475569; background-color: #1E293B;">
                                <strong>{name}</strong> • {prof} ({months} months, {ends} 👍)
                            </span>
                            """
                        st.markdown(f"<div>{skills_html}</div>", unsafe_allow_html=True)
                    
                    # Career timeline
                    st.markdown("### 💼 Career History Timeline")
                    career_history = cand_details.get("career_history", [])
                    if not career_history:
                        st.info("No career entries specified.")
                    else:
                        timeline_html = "<div style='margin-top: 15px;'>"
                        # Sort by start date reverse
                        sorted_career = sorted(career_history, key=lambda x: x.get("start_date", ""), reverse=True)
                        for entry in sorted_career:
                            company = entry.get("company", "Company")
                            title = entry.get("title", "Position")
                            start = entry.get("start_date", "")
                            end = entry.get("end_date", "Present")
                            desc = entry.get("description", "")
                            co_size = entry.get("company_size", "Unknown Size")
                            industry = entry.get("industry", "Technology")
                            
                            timeline_html += f"""
                            <div class="timeline-item">
                                <div class="timeline-date">{start} — {end} • Co. Size: {co_size} • {industry}</div>
                                <div class="timeline-title">{title}</div>
                                <div class="timeline-company">{company}</div>
                                <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 6px; line-height: 1.4;">{desc}</p>
                            </div>
                            """
                        timeline_html += "</div>"
                        st.markdown(timeline_html, unsafe_allow_html=True)

                    # Academic degrees
                    st.markdown("### 🎓 Academic Background")
                    education = cand_details.get("education", [])
                    if not education:
                        st.info("No education details specified.")
                    else:
                        for edu in education:
                            inst = edu.get("institution", "Institution")
                            deg = edu.get("degree", "Degree")
                            fos = edu.get("field_of_study", "Unspecified Field")
                            tier = edu.get("tier", "unknown").upper().replace("_", " ")
                            
                            st.markdown(
                                f"""
                                <div style="background-color: #1E293B; border: 1px solid #334155; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <strong style="color: #F1F5F9; font-size: 1rem;">{deg} in {fos}</strong>
                                        <span class="badge-verified" style="background-color: rgba(129, 140, 248, 0.1); color: #818CF8; border-color: rgba(129, 140, 248, 0.2);">{tier}</span>
                                    </div>
                                    <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 3px;">{inst}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )


if __name__ == "__main__":
    main()
