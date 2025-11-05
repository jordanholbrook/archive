# Input Data Directory

This directory contains input files for the RCV pipeline.

## Directory Structure

```
data/inputs/
├── pdfs/              # PDF election reports
│   └── sample/        # Sample PDF data (for testing)
└── text/              # Pre-existing text election reports
    └── sample/        # Sample text data (for testing)
```

## Usage

### For Your Own Data

Place your election data files directly in:
- **PDF files**: `data/inputs/pdfs/`
- **Text files**: `data/inputs/text/`

### For Sample/Test Data

Sample data is organized in subdirectories:
- **Sample PDFs**: `data/inputs/pdfs/sample/`
- **Sample text**: `data/inputs/text/sample/`

## How It Works

The pipeline searches recursively through input directories, so:
- ✅ Files in `pdfs/` and `text/` are processed
- ✅ Files in `pdfs/sample/` and `text/sample/` are also processed
- ✅ Files in any subdirectory are found and processed

**Note**: If files from different subdirectories have the same name, the pipeline will handle naming conflicts automatically.

## Best Practices

1. **Your own data**: Place directly in `pdfs/` and `text/` directories
2. **Sample/test data**: Keep in `sample/` subdirectories for organization
3. **Multiple datasets**: Use descriptive subdirectory names (e.g., `pdfs/jurisdiction_2024/`)

## Sample Data

The `sample/` subdirectories contain example election data files that allow you to test the pipeline immediately after cloning the repository. These files are included for demonstration purposes.

