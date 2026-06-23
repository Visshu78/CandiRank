#!/usr/bin/env python3
"""Offline precompute step for parsed JD artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import DEFAULT_JD_PATH, DEFAULT_PRECOMPUTE_DIR
from src.jd_parser import parse_jd, parsed_jd_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse the job description into a JSON artifact.")
    parser.add_argument("--jd", type=Path, default=DEFAULT_JD_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_PRECOMPUTE_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    parsed = parse_jd(args.jd)
    output_path = args.out_dir / "jd_parsed.json"
    output_path.write_text(json.dumps(parsed_jd_to_dict(parsed), indent=2), encoding="utf-8")
    print(f"Wrote parsed JD to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
