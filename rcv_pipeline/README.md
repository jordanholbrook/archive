# RCV Pipeline - Complete Documentation

A comprehensive pipeline for extracting, processing, and validating ranked choice voting (RCV) election data from PDF documents and text files.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Core Pipeline Scripts](#core-pipeline-scripts)
- [Utility Scripts](#utility-scripts)
- [Sample Management](#sample-management)
- [Data Structure](#data-structure)
- [Command Reference](#command-reference)
- [Workflow Details](#workflow-details)
- [Validation Rules](#validation-rules)
- [Troubleshooting](#troubleshooting)

## Overview

This pipeline processes RCV election data through four main stages:

1. **PDF Extraction**: Converts PDF files to text files
2. **Data Extraction**: Uses LLM to extract structured election data
3. **Post-Processing**: Cleans and standardizes data, computes transfer values
4. **Validation**: Performs data quality checks and generates reports

### Key Features

- Automatic transfer computation from vote counts
- Comprehensive data quality validation
- Mixed input support (PDFs and text files)
- Batch processing capabilities
- Sample-based organization for multiple datasets

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key (for Step 2 - LLM extraction)

### Setup Steps

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp env_template.txt .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your-api-key-here
```

**Important**: Never commit the `.env` file to version control. The `.env` file is already in `.gitignore`.

## Quick Start

### 1. Add Input Files

Place your election data in one of these locations:

- **PDF files**: `data/inputs/pdfs/` (or in subdirectories like `data/inputs/pdfs/sample/`)
- **Text files**: `data/inputs/text/` (or in subdirectories like `data/inputs/text/sample/`)
- **Mixed**: Use both directories

**Note**: The pipeline searches recursively, so you can organize sample/test data in subdirectories. Sample data is included in `data/inputs/pdfs/sample/` and `data/inputs/text/sample/` for testing purposes.

### 2. Run the Pipeline

```bash
# Run all steps automatically (recommended)
python scripts/run_all.py
```

This will:
- Detect your input types automatically
- Run only necessary steps
- Merge mixed inputs seamlessly
- Process everything in sequence

## Core Pipeline Scripts

### 1. Extract PDFs (`1_extract_pdfs.py`)

Converts PDF files to text files for processing.

**Usage:**
```bash
python scripts/1_extract_pdfs.py
```

**Input**: PDF files in `data/inputs/pdfs/` (searches recursively, including subdirectories like `sample/`)
**Output**: Text files in `data/processing/extracted_text/`

**Notes**:
- Skips if no PDFs are found
- Requires PDF files to be text-based (not scanned images)
- Automatically creates output directory if it doesn't exist
- Searches recursively, so sample data in `data/inputs/pdfs/sample/` will be found

### 2. Extract Election Data (`2_extract_election_data.py`)

Uses OpenAI's LLM to extract structured election data from text files.

**Usage:**
```bash
python scripts/2_extract_election_data.py
```

**Input**: Text files in `data/processing/extracted_text/`
**Output**: CSV files in `data/processing/extracted_data/`
- `Elections_DF_batch_*.csv`
- `Candidates_DF_batch_*.csv`
- `Rounds_DF_batch_*.csv`

**Requirements**:
- OpenAI API key must be set in `.env`
- API key must have sufficient credits

**Notes**:
- Processes files in batches for efficiency
- Saves progress after each batch
- Can be interrupted and resumed

### 3. Post-Process (`3_post_process.py`)

Cleans, standardizes, and computes transfer values from vote counts.

**Usage:**
```bash
python scripts/3_post_process.py
```

**Input**: CSV files in `data/processing/extracted_data/`
**Output**: Cleaned CSV files in `data/outputs/cleaned/`
- `Elections_DF_cleaned.csv`
- `Candidates_DF_cleaned.csv`
- `Rounds_DF_cleaned.csv`

**Features**:
- Cleans and standardizes data
- Computes transfer values from vote counts
- Standardizes election IDs
- Adds candidate status (Elected/Eliminated/Continuing)

### 4. Validate Data (`4_validate_data.py`)

Performs comprehensive data quality validation.

**Usage:**
```bash
python scripts/4_validate_data.py
```

**Input**: Cleaned CSV files in `data/outputs/cleaned/`
**Output**: Validation reports in `data/outputs/validation_reports/`
- `validation_report_YYYYMMDD_HHMMSS.txt`
- `election_validation_scores.csv`

**Validation Checks**:
- Data completeness
- Vote consistency across rounds
- Transfer balance (mathematical consistency)
- Single winner validation
- Vote monotonicity
- Election ID consistency
- Round sequence logic

## Utility Scripts

### Run All Pipeline Steps (`run_all.py`)

Runs all four pipeline steps in sequence with automatic input detection.

**Usage:**
```bash
python scripts/run_all.py
```

**Features**:
- Automatically detects input types (PDFs, text files, or both)
- Runs only necessary steps
- Merges mixed inputs seamlessly
- Prompts for confirmation before running

**Output**: Complete pipeline results in `data/outputs/`

### Combine Cleaned Datasets (`combine_cleaned_datasets.py`)

Combines standardized 'cleaned' CSVs from multiple jurisdiction subfolders into master CSV files.

**Usage:**
```bash
python scripts/combine_cleaned_datasets.py <samples_root> [--out OUTPUT_DIR] [--pattern PATTERN]
```

**Arguments**:
- `samples_root` (required): Path to parent folder containing jurisdiction subfolders
- `--out OUTPUT_DIR` (optional): Directory to write combined CSVs (default: `combined_outputs`)
- `--pattern PATTERN` (optional): Glob pattern to select jurisdiction folders (default: `*`)

**Examples**:
```bash
# Combine all samples
python scripts/combine_cleaned_datasets.py data/samples

# Combine only versioned samples
python scripts/combine_cleaned_datasets.py data/samples --pattern "*_v*"

# Specify custom output directory
python scripts/combine_cleaned_datasets.py data/samples --out my_combined_data
```

**Input Structure Expected**:
```
samples_root/
├── jurisdiction1/
│   └── cleaned/
│       ├── Candidates_DF_cleaned.csv
│       ├── Elections_DF_cleaned.csv
│       ├── Elections_DF_cleaned_with_scores.csv
│       └── Rounds_DF_cleaned.csv
└── jurisdiction2/
    └── cleaned/
        └── ...
```

**Output**:
- `Candidates_DF_clean_combined.csv`
- `Elections_DF_cleaned_combined.csv`
- `Elections_DF_cleaned_with_scores_combined.csv`
- `Rounds_DF_cleaned_combined.csv`

**Notes**:
- Adds `source_key` column to each combined file (jurisdiction folder name)
- Skips jurisdictions missing any expected CSVs (with warning)
- Concatenates with union of columns (missing columns become NaN)

### Summary Statistics (`summary_stats.py`)

Generates comprehensive summary statistics for RCV datasets.

**Usage:**
```bash
python scripts/summary_stats.py [--base-dir BASE_DIR] [--version VERSION] [--export-excel]
```

**Arguments**:
- `--base-dir BASE_DIR` (optional): Base directory containing CSV files (default: `output`)
- `--version VERSION` (optional): Version suffix to analyze (default: `v12`)
- `--export-excel` (optional): Export datasets to Excel workbook

**Examples**:
```bash
# Generate summary statistics
python scripts/summary_stats.py

# Analyze specific version
python scripts/summary_stats.py --version v11

# Export to Excel
python scripts/summary_stats.py --export-excel

# Custom base directory
python scripts/summary_stats.py --base-dir combined_outputs --version vA11
```

**Output**:
- Console summary statistics
- Optional Excel workbook with all datasets (if `--export-excel` is used)

## Sample Management

For processing multiple independent datasets, use the sample management system.

### Setup New Sample (`setup_sample.py`)

Creates a new sample directory and copies PDF/text files into it.

**Usage:**
```bash
# PDF-only sample (legacy syntax)
python scripts/setup_sample.py <sample_name> <pdf_source_directory>

# PDF-only sample (new syntax)
python scripts/setup_sample.py <sample_name> --pdf-dir <pdf_dir>

# Text-only sample
python scripts/setup_sample.py <sample_name> --txt-only <txt_source_directory>

# Mixed PDF + text sample
python scripts/setup_sample.py <sample_name> --pdf-dir <pdf_dir> --txt-dir <txt_dir>

# List all samples
python scripts/setup_sample.py --list
```

**Arguments**:
- `sample_name` (required): Name of the new sample
- `pdf_source` (optional, legacy): Directory containing PDF files (positional argument)
- `--pdf-dir PDF_DIR` (optional): Directory containing PDF files
- `--txt-dir TXT_DIR` (optional): Directory containing pre-existing text files
- `--txt-only TXT_DIR` (optional): Directory containing text files (text-only sample)
- `--list` (optional): List all available samples

**Examples**:
```bash
# PDF-only sample
python scripts/setup_sample.py alaska_2024 /path/to/alaska/pdfs

# Text-only sample
python scripts/setup_sample.py maine_2024 --txt-only /path/to/maine/texts

# Mixed sample
python scripts/setup_sample.py nyc_2024 --pdf-dir /path/to/pdfs --txt-dir /path/to/texts

# List samples
python scripts/setup_sample.py --list
```

**What it does**:
- Creates sample directory structure in `data/samples/<sample_name>/`
- Copies PDF files to `raw/` directory
- Copies text files to `txt_inputs/` directory
- Creates all necessary subdirectories

### Run Pipeline on Sample (`run_sample.py`)

Runs the complete pipeline on a specific sample.

**Usage:**
```bash
python scripts/run_sample.py <sample_name> [--source SOURCE_DIR]
python scripts/run_sample.py --list
```

**Arguments**:
- `sample_name` (required): Name of the sample to process
- `--source SOURCE_DIR` (optional): Source directory containing PDF files (copies to sample)
- `--list` (optional): List all available samples

**Examples**:
```bash
# Run pipeline on sample
python scripts/run_sample.py alaska_2024

# Run with PDFs from different directory
python scripts/run_sample.py alaska_2024 --source /path/to/pdfs

# List all samples
python scripts/run_sample.py --list
```

**What it does**:
- Sets up sample directory structure
- Detects input types (PDFs, text files, or both)
- Runs all four pipeline steps
- Saves results in sample-specific directories

**Sample Directory Structure**:
```
data/samples/<sample_name>/
├── raw/                    # PDF files
├── txt_inputs/             # Pre-existing text files
├── txt_files/              # Generated + existing text (merged)
├── csv_files/              # Raw extracted CSV data
├── cleaned/                 # Cleaned and standardized data
└── validation_reports/      # Validation results
```

## Data Structure

### Main Pipeline Structure

```
rcv_pipeline/
├── data/
│   ├── inputs/                    # Input files
│   │   ├── pdfs/                  # PDF files to convert
│   │   │   └── sample/             # Sample PDF data (for testing)
│   │   └── text/                  # Pre-existing text files
│   │       └── sample/             # Sample text data (for testing)
│   ├── processing/                # Intermediate files
│   │   ├── extracted_text/        # All text files (generated + existing)
│   │   └── extracted_data/        # Raw extracted CSV data
│   └── outputs/                   # Final results
│       ├── cleaned/               # Cleaned and standardized data
│       └── validation_reports/    # Validation results and reports
├── scripts/                       # Pipeline scripts
├── utils/                         # Utility functions
└── combined_outputs/              # Combined datasets (if using combine script)
```

**Note**: The pipeline searches recursively in input directories, so you can organize sample data in subdirectories (e.g., `sample/`) without affecting file paths. Place your own data directly in `data/inputs/pdfs/` and `data/inputs/text/` (not in subdirectories).

### Sample-Based Structure

```
data/samples/
├── <sample_name>/
│   ├── raw/                       # PDF files
│   ├── txt_inputs/                # Pre-existing text files
│   ├── txt_files/                 # Generated + existing text (merged)
│   ├── csv_files/                 # Raw extracted CSV data
│   ├── cleaned/                   # Cleaned and standardized data
│   └── validation_reports/         # Validation results
```

## Command Reference

### Quick Reference Table

| Script | Purpose | Input | Output | Key Options |
|--------|---------|-------|--------|-------------|
| `1_extract_pdfs.py` | PDF to text | `data/inputs/pdfs/` (recursive) | `data/processing/extracted_text/` | None |
| `2_extract_election_data.py` | LLM extraction | `data/processing/extracted_text/` | `data/processing/extracted_data/` | Requires API key |
| `3_post_process.py` | Clean & standardize | `data/processing/extracted_data/` | `data/outputs/cleaned/` | None |
| `4_validate_data.py` | Validate data | `data/outputs/cleaned/` | `data/outputs/validation_reports/` | None |
| `run_all.py` | Run all steps | Auto-detected | `data/outputs/` | Prompts for confirmation |
| `setup_sample.py` | Create sample | Source dirs | `data/samples/<name>/` | `--pdf-dir`, `--txt-dir`, `--txt-only`, `--list` |
| `run_sample.py` | Run on sample | Sample dirs | `data/samples/<name>/` | `--source`, `--list` |
| `combine_cleaned_datasets.py` | Combine samples | `data/samples/` | `combined_outputs/` | `--out`, `--pattern` |
| `summary_stats.py` | Generate stats | CSV files | Console/Excel | `--base-dir`, `--version`, `--export-excel` |

## Workflow Details

### Standard Workflow

1. **Add Input Files**
   - Place PDFs in `data/inputs/pdfs/`
   - Place text files in `data/inputs/text/`
   - Or use both for mixed inputs

2. **Run Pipeline**
   ```bash
   python scripts/run_all.py
   ```
   - Step 1: Extracts text from PDFs (if PDFs exist)
   - Step 1.5: Merges text inputs (if text files exist)
   - Step 2: Extracts structured data using LLM
   - Step 3: Cleans and standardizes data
   - Step 4: Validates data quality

3. **Review Results**
   - Check cleaned data in `data/outputs/cleaned/`
   - Review validation reports in `data/outputs/validation_reports/`

### Sample-Based Workflow

1. **Set Up Sample**
   ```bash
   python scripts/setup_sample.py my_sample --pdf-dir /path/to/pdfs
   ```

2. **Run Pipeline on Sample**
   ```bash
   python scripts/run_sample.py my_sample
   ```

3. **Combine Multiple Samples** (optional)
   ```bash
   python scripts/combine_cleaned_datasets.py data/samples
   ```

4. **Generate Statistics** (optional)
   ```bash
   python scripts/summary_stats.py --base-dir combined_outputs
   ```

## Validation Rules

The pipeline performs comprehensive validation checks:

### Core Data Quality

- **Data Completeness**: All required fields present and complete
- **Vote Consistency**: Vote totals match between candidates and rounds
- **Election ID Consistency**: All elections appear in all DataFrames
- **Round Sequence**: Rounds start from 1 and are sequential

### RCV-Specific Rules

- **Single Winner**: Each election must have exactly one winner in the final round
- **Vote Monotonicity**: Remaining candidates' votes must not decrease
- **Transfer Balance**: Vote transfers must sum to ≤ 0 across all candidates

### Transfer Computation

The pipeline automatically computes transfer values from vote counts:

```
Transfer = Current Round Votes - Previous Round Votes
```

**Benefits**:
- Mathematical consistency (transfers balance to ~0)
- Identifies discrepancies between extracted and computed transfers
- Not dependent on LLM extraction accuracy for transfer values

## Troubleshooting

### Common Issues

**PDF Extraction Issues**
- **Problem**: PDFs not converting to text
- **Solution**: Ensure PDFs are text-based (not scanned images)
- **Check**: Verify PDFs contain selectable text

**API Errors**
- **Problem**: OpenAI API errors during extraction
- **Solution**: Verify API key is correct and has sufficient credits
- **Check**: Confirm `.env` file exists and contains valid `OPENAI_API_KEY`

**File Not Found Errors**
- **Problem**: Scripts can't find input files
- **Solution**: Ensure you've run scripts in order (1 → 2 → 3 → 4)
- **Check**: Verify input files are in correct directories

**Transfer Validation Failures**
- **Problem**: Transfer balance validation fails
- **Solution**: Review validation report for specific elections with issues
- **Check**: Verify vote counts are correct in source data

**Single Winner Violations**
- **Problem**: Elections don't have exactly one winner
- **Solution**: Check if elections are properly configured for single-winner contests
- **Check**: Verify final round has exactly one candidate with winner status

**Monotonicity Violations**
- **Problem**: Remaining candidates' votes decrease
- **Solution**: Indicates potential data extraction errors or non-standard RCV procedures
- **Check**: Review original election documents

### Getting Help

1. Check validation reports for specific error messages
2. Verify input file formats and locations
3. Ensure all dependencies are installed
4. Check that API key is correctly configured
5. Review console output for detailed error messages

## Output Files

### Main Output Files

The pipeline produces three main CSV files:

1. **Elections_DF_cleaned.csv**
   - Election metadata (election_id, year, state, office, etc.)
   - One row per election

2. **Candidates_DF_cleaned.csv**
   - Candidate performance data
   - Includes `transfer_original` (from extraction) and `transfer_calc` (computed)
   - Includes `status` (Elected/Eliminated/Continuing)
   - One row per candidate per round

3. **Rounds_DF_cleaned.csv**
   - Round-level summary statistics
   - One row per round per election

### Validation Reports

- **validation_report_YYYYMMDD_HHMMSS.txt**: Detailed validation report
- **election_validation_scores.csv**: Validation scores per election

## License

See LICENSE file in repository root for details.
