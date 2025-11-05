#!/usr/bin/env python3
"""
Summary Statistics for RCV Data
==============================

Script to generate comprehensive summary statistics for RCV datasets.
Includes numeric summaries, data quality checks, and Excel export functionality.

Usage:
    python scripts/summary_stats.py [--base-dir BASE_DIR] [--version VERSION] [--export-excel]
"""

import pandas as pd
from pathlib import Path
import argparse
import sys

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
DEFAULT_BASE_DIR = Path("output")
DEFAULT_VERSION = "v12"

# File mappings for different versions
FILE_PATTERNS = {
    "candidates": "Candidates_DF_clean_combined_{version}.csv",
    "elections": "Elections_DF_cleaned_combined_{version}.csv", 
    "elections_scores": "Elections_DF_cleaned_with_scores_combined_{version}.csv",
    "rounds": "Rounds_DF_cleaned_combined_{version}.csv"
}

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------
def summarize_numeric(df):
    """Return summary stats (mean, std, min, max) for numeric columns."""
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) == 0:
        return pd.DataFrame()
    return df[numeric_cols].describe().T[["mean", "std", "min", "max"]]

def get_data_quality_summary(df, name):
    """Get basic data quality metrics."""
    summary = {
        "Dataset": name,
        "Total Rows": len(df),
        "Total Columns": len(df.columns),
        "Missing Values": df.isnull().sum().sum(),
        "Duplicate Rows": df.duplicated().sum()
    }
    return summary

def get_categorical_summary(df, name):
    """Get summary of categorical variables."""
    categorical_cols = df.select_dtypes(include=['object']).columns
    summary = {}
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        summary[f"{col}_unique_count"] = unique_count
        if unique_count <= 20:  # Show top values for small cardinality
            top_values = df[col].value_counts().head(5).to_dict()
            summary[f"{col}_top_values"] = top_values
    
    return summary

def analyze_rcv_specific_metrics(df_elections, df_candidates, df_rounds):
    """Analyze RCV-specific metrics across datasets."""
    metrics = {}
    
    if df_elections is not None:
        metrics["Unique Jurisdictions"] = df_elections["juris"].nunique()
        metrics["Unique Offices"] = df_elections["office"].nunique()
        metrics["Unique States"] = df_elections["state"].nunique()
        metrics["Unique Election Types"] = df_elections["election_type"].nunique()
        metrics["Date Range"] = f"{df_elections['date'].min()} to {df_elections['date'].max()}"
        
        # Elections by year
        if 'year' in df_elections.columns:
            year_counts = df_elections['year'].value_counts().sort_index()
            metrics["Elections by Year"] = year_counts.to_dict()
    
    if df_candidates is not None:
        metrics["Total Candidate Records"] = len(df_candidates)
        metrics["Unique Candidates"] = df_candidates["candidate_id"].nunique()
        if 'votes' in df_candidates.columns:
            metrics["Vote Statistics"] = {
                "Min Votes": df_candidates['votes'].min(),
                "Max Votes": df_candidates['votes'].max(),
                "Mean Votes": df_candidates['votes'].mean()
            }
    
    if df_rounds is not None:
        metrics["Total Round Records"] = len(df_rounds)
        if 'round' in df_rounds.columns:
            metrics["Max Rounds in Election"] = df_rounds['round'].max()
            metrics["Min Rounds in Election"] = df_rounds['round'].min()
    
    return metrics

def export_to_excel(dataframes, output_path):
    """Export dataframes to Excel workbook."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Excel workbook written to: {output_path}")

# ---------------------------------------------------------------------
# Main Processing Function
# ---------------------------------------------------------------------
def process_summary_stats(base_dir: Path, version: str, export_excel: bool = False):
    """Generate comprehensive summary statistics for RCV datasets."""
    print(f"[INFO] Generating summary statistics for version: {version}")
    print(f"[INFO] Base directory: {base_dir}")
    print("=" * 60)
    
    # Load datasets
    datasets = {}
    dataframes = {}
    
    for name, pattern in FILE_PATTERNS.items():
        filename = pattern.format(version=version)
        filepath = base_dir / filename
        
        if not filepath.exists():
            print(f"[SKIP] {filename} not found.")
            continue
        
        print(f"[INFO] Loading {filename}")
        df = pd.read_csv(filepath, low_memory=False)
        datasets[name] = df
        dataframes[name.replace('_', ' ').title()] = df
    
    if not datasets:
        print("[ERROR] No datasets found to analyze.")
        return
    
    # Generate summaries for each dataset
    print("\n" + "=" * 60)
    print("DATASET SUMMARIES")
    print("=" * 60)
    
    for name, df in datasets.items():
        print(f"\n===== {name.upper()} =====")
        
        # Basic info
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Data quality
        quality = get_data_quality_summary(df, name)
        print("\nData Quality:")
        for key, value in quality.items():
            print(f"  {key}: {value}")
        
        # Numeric summary
        numeric_summary = summarize_numeric(df)
        if not numeric_summary.empty:
            print("\nNumeric Summary:")
            print(numeric_summary)
        
        # Categorical summary
        categorical_summary = get_categorical_summary(df, name)
        if categorical_summary:
            print("\nCategorical Summary:")
            for key, value in categorical_summary.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {key}: {value}")
    
    # RCV-specific analysis
    print("\n" + "=" * 60)
    print("RCV-SPECIFIC METRICS")
    print("=" * 60)
    
    rcv_metrics = analyze_rcv_specific_metrics(
        datasets.get('elections'),
        datasets.get('candidates'), 
        datasets.get('rounds')
    )
    
    for key, value in rcv_metrics.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
    
    # Export to Excel if requested
    if export_excel and dataframes:
        excel_path = base_dir / f"RCV_data_panels_{version}.xlsx"
        export_to_excel(dataframes, excel_path)
    
    print("\n" + "=" * 60)
    print("SUMMARY COMPLETE")
    print("=" * 60)

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive summary statistics for RCV datasets."
    )
    parser.add_argument(
        "--base-dir", 
        type=Path, 
        default=DEFAULT_BASE_DIR,
        help=f"Base directory containing CSV files (default: {DEFAULT_BASE_DIR})"
    )
    parser.add_argument(
        "--version", 
        default=DEFAULT_VERSION,
        help=f"Version suffix to analyze (default: {DEFAULT_VERSION})"
    )
    parser.add_argument(
        "--export-excel", 
        action="store_true",
        help="Export datasets to Excel workbook"
    )
    
    args = parser.parse_args()
    
    base_dir = args.base_dir.expanduser().resolve()
    
    if not base_dir.exists():
        print(f"[ERROR] Base directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not base_dir.is_dir():
        print(f"[ERROR] Base directory is not a directory: {base_dir}", file=sys.stderr)
        sys.exit(1)
    
    process_summary_stats(base_dir, args.version, args.export_excel)

if __name__ == "__main__":
    main()
