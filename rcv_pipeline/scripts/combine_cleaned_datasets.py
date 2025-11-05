#!/usr/bin/env python3
"""
Combine standardized 'cleaned' CSVs from many jurisdiction subfolders into four master CSVs.

Each jurisdiction folder is expected to look like:
  <SAMPLES_ROOT>/<jurisdiction_key>/cleaned/
      Candidates_DF_clean.csv
      Elections_DF_cleaned_with_scores.csv
      Elections_DF_cleaned.csv
      Rounds_DF_cleaned.csv

Output:
  <OUT_DIR>/Candidates_DF_clean_combined.csv
  <OUT_DIR>/Elections_DF_cleaned_combined.csv
  <OUT_DIR>/Elections_DF_cleaned_with_scores_combined.csv
  <OUT_DIR>/Rounds_DF_cleaned_combined.csv

Notes:
- Adds a 'source_key' column (the jurisdiction folder name, e.g., 'Alaska_v1') to each combined file.
- Concatenates with union of columns; missing columns become NaN.
- Skips jurisdictions missing any of the expected CSVs, but logs a warning.
"""

import argparse
from pathlib import Path
import sys
import pandas as pd

EXPECTED_FILES = {
    "candidates": "Candidates_DF_cleaned.csv",
    "elections": "Elections_DF_cleaned.csv",
    "elections_scores": "Elections_DF_cleaned_with_scores.csv",
    "rounds": "Rounds_DF_cleaned.csv",
}

OUTPUT_FILENAMES = {
    "candidates": "Candidates_DF_clean_combined.csv",
    "elections": "Elections_DF_cleaned_combined.csv",
    "elections_scores": "Elections_DF_cleaned_with_scores_combined.csv",
    "rounds": "Rounds_DF_cleaned_combined.csv",
}

def find_jurisdiction_dirs(samples_root: Path, glob_pattern: str):
    """
    Find jurisdiction directories under samples_root according to a pattern.
    Default pattern '*', but you might use '*_v*' to only match versioned folders.
    """
    return sorted([p for p in samples_root.glob(glob_pattern) if p.is_dir()])

def load_one_csv(csv_path: Path, source_key: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.insert(0, "source_key", source_key)  # helpful for provenance
    return df

def combine_all(samples_root: Path, out_dir: Path, glob_pattern: str = "*"):
    # Prepare collectors
    combined = {k: [] for k in EXPECTED_FILES.keys()}
    missing = []

    jur_dirs = find_jurisdiction_dirs(samples_root, glob_pattern)
    if not jur_dirs:
        print(f"[WARN] No jurisdiction folders found under {samples_root} with pattern '{glob_pattern}'.")
        return

    print(f"[INFO] Found {len(jur_dirs)} jurisdiction folders. Scanning…")

    for jur_dir in jur_dirs:
        source_key = jur_dir.name
        cleaned_dir = jur_dir / "cleaned"

        if not cleaned_dir.is_dir():
            print(f"[WARN] Skipping {source_key}: missing 'cleaned/' directory", file=sys.stderr)
            missing.append((source_key, "cleaned/"))
            continue

        # Check for all expected files
        file_map = {k: cleaned_dir / v for k, v in EXPECTED_FILES.items()}
        missing_any = [k for k, p in file_map.items() if not p.exists()]

        if missing_any:
            print(f"[WARN] Skipping {source_key}: missing {', '.join(missing_any)}", file=sys.stderr)
            missing.append((source_key, ", ".join(missing_any)))
            continue

        # Load each CSV and append
        try:
            for key, path in file_map.items():
                df = load_one_csv(path, source_key)
                combined[key].append(df)
        except Exception as e:
            print(f"[ERROR] Failed reading {source_key}: {e}", file=sys.stderr)
            missing.append((source_key, f"read_error:{e}"))
            continue

    # Ensure output directory
    out_dir.mkdir(parents=True, exist_ok=True)

    # Concatenate and write
    for key, parts in combined.items():
        if not parts:
            print(f"[WARN] No data collected for '{key}'. Skipping write.", file=sys.stderr)
            continue

        # Union of columns across all frames, index reset
        big = pd.concat(parts, ignore_index=True, sort=False)

        # Optional: remove exact duplicate rows across jurisdictions (keep first)
        big = big.drop_duplicates()

        out_path = out_dir / OUTPUT_FILENAMES[key]
        big.to_csv(out_path, index=False)
        print(f"[OK] Wrote {len(big):,} rows → {out_path}")

    if missing:
        print("\n[SUMMARY] Skipped or had issues with the following jurisdictions/files:")
        for sk, reason in missing:
            print(f"  - {sk}: {reason}")

def main():
    ap = argparse.ArgumentParser(description="Combine standardized 'cleaned' CSVs from many jurisdictions.")
    ap.add_argument("samples_root", help="Path to the parent folder containing jurisdiction subfolders (e.g., …/samples)")
    ap.add_argument("--out", default="combined_outputs", help="Directory to write combined CSVs (default: ./combined_outputs)")
    ap.add_argument("--pattern", default="*", help="Glob to select jurisdiction folders (e.g., '*_v*'). Default: '*'")
    args = ap.parse_args()

    samples_root = Path(args.samples_root).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()

    if not samples_root.is_dir():
        print(f"[ERROR] samples_root not found or not a directory: {samples_root}", file=sys.stderr)
        sys.exit(1)

    combine_all(samples_root, out_dir, glob_pattern=args.pattern)

if __name__ == "__main__":
    main()