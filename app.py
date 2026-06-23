"""Small Streamlit viewer for the generated Redrob ranking."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import DEFAULT_OUTPUT_PATH


def main() -> None:
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit is not installed. Run `python rank.py` to generate the submission CSV.")
        return

    st.set_page_config(page_title="Redrob Candidate Ranker", layout="wide")
    st.title("Redrob Candidate Ranker")

    output_path = Path(DEFAULT_OUTPUT_PATH)
    if not output_path.exists():
        st.warning("No submission CSV found yet. Run `python rank.py` first.")
        return

    df = pd.read_csv(output_path)
    st.metric("Ranked candidates", len(df))
    st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
