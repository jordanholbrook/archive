# RCV Election Data Processing Pipeline

A production-ready pipeline for extracting, processing, and validating ranked choice voting (RCV) election data from PDF documents and text files.

## Overview

This repository contains a comprehensive data processing pipeline designed to extract structured election data from RCV election reports. The pipeline automatically:

- Extracts text from PDF election reports
- Uses Large Language Models (LLMs) to extract structured data from election text
- Cleans and standardizes election data
- Computes vote transfer values mathematically from vote counts
- Validates data quality and generates comprehensive validation reports

## Key Features

- **Automatic PDF Processing**: Converts PDF election reports to text
- **LLM-Powered Data Extraction**: Extracts structured data (elections, candidates, rounds) using OpenAI's API
- **Mathematical Transfer Computation**: Automatically computes vote transfers from vote counts for consistency
- **Comprehensive Validation**: Validates data quality, transfer balance, vote consistency, and election logic
- **Mixed Input Support**: Handles both PDF files and pre-existing text files
- **Batch Processing**: Efficiently processes large numbers of election files
- **Sample Management**: Organize and process multiple election datasets independently

## What You Need to Know

### Prerequisites

1. **Python 3.9+**: Required to run the pipeline scripts
2. **OpenAI API Key**: Required for LLM-based data extraction (Step 2)
3. **Basic Terminal/Command Line**: Familiarity with running Python scripts
4. **Understanding of RCV**: Basic knowledge of ranked choice voting terminology

### Key Concepts

- **Election Data**: Structured information about elections, candidates, and voting rounds
- **Transfer Values**: Vote transfers between rounds when candidates are eliminated
- **Data Validation**: Automated checks to ensure data quality and mathematical consistency
- **Samples**: Organized collections of election data from different jurisdictions or time periods

### Knowledge Required

- **Python**: Basic understanding of running Python scripts
- **Command Line**: Ability to navigate directories and run commands
- **RCV Terminology**: Understanding of elections, candidates, rounds, transfers
- **Data Formats**: Familiarity with CSV files and basic data concepts

## Quick Start

### 1. Installation

```bash
# Navigate to the pipeline directory
cd rcv_pipeline

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy the environment template
cp env_template.txt .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your-api-key-here
```

### 3. Add Input Files

Place your election data files in one of these locations:

- **PDF files**: `rcv_pipeline/data/inputs/pdfs/` (or in subdirectories like `sample/`)
- **Text files**: `rcv_pipeline/data/inputs/text/` (or in subdirectories like `sample/`)

**Sample Data**: The repository includes sample data in `rcv_pipeline/data/inputs/pdfs/sample/` and `rcv_pipeline/data/inputs/text/sample/` for testing. The pipeline searches recursively, so these files will be processed automatically.

### 4. Run the Pipeline

```bash
# Run all steps automatically
python scripts/run_all.py
```

The pipeline will:
1. Detect your input types (PDFs, text files, or both)
2. Extract text from PDFs (if present)
3. Extract structured data using LLM
4. Clean and standardize the data
5. Validate data quality
6. Generate validation reports

## Repository Structure

```
archive/
├── README.md                    # This file - main repository overview
├── LICENSE                      # License information
└── rcv_pipeline/               # Main pipeline directory
    ├── README.md               # Detailed pipeline documentation
    ├── requirements.txt        # Python dependencies
    ├── env_template.txt        # Environment variables template
    ├── scripts/                # Pipeline scripts
    ├── utils/                  # Utility functions
    └── data/                   # Data directories (inputs/outputs)
```

## Output Files

The pipeline produces three main CSV files:

1. **Elections_DF_cleaned.csv**: Election metadata (election_id, year, state, office, etc.)
2. **Candidates_DF_cleaned.csv**: Candidate performance data with computed transfers
3. **Rounds_DF_cleaned.csv**: Round-level summary statistics

Plus validation reports in `data/outputs/validation_reports/`.

## Documentation

For detailed documentation, including:
- Complete command syntax for all scripts
- Detailed workflow explanations
- Advanced usage examples
- Troubleshooting guide

See **[rcv_pipeline/README.md](rcv_pipeline/README.md)**.

## Getting Help

If you encounter issues:

1. Check the detailed README in `rcv_pipeline/README.md`
2. Verify your input files are in the correct directories
3. Ensure your OpenAI API key is correctly configured
4. Check that all dependencies are installed

## License

See LICENSE file for details.
