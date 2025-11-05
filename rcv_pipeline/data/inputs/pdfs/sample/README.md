# Sample PDF Data

This directory contains sample PDF election reports for testing the pipeline.

**Purpose**: These sample files allow users to test the pipeline immediately after cloning the repository.

**Usage**: 
- Place your own PDF files directly in `data/inputs/pdfs/` (not in this `sample/` subdirectory)
- The pipeline searches recursively, so files in `sample/` will also be processed
- To test with sample data only, keep only the sample files and remove any files from the parent `pdfs/` directory

**Note**: The pipeline will process all PDF files found in `data/inputs/pdfs/` and its subdirectories, including files in this `sample/` folder.

