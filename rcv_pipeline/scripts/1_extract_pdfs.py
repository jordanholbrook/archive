#!/usr/bin/env python3
"""
Script 1: Extract text from PDF files
=====================================

This script converts PDF files in the data/inputs/pdfs/ directory to text files
in the data/processing/extracted_text/ directory.

Usage: python scripts/1_extract_pdfs.py
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.pdf_utils import process_pdf_directory

def main():
    """Main function to extract PDFs to text."""
    print("RCV Pipeline - Step 1: PDF Text Extraction")
    print("=" * 50)
    
    # Define input and output directories
    input_dir = "data/inputs/pdfs"
    output_dir = "data/processing/extracted_text"
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Check if input directory exists and has PDF files
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print("Please create the directory and add your PDF files.")
        print("Directory structure should be:")
        print("   data/inputs/pdfs/ - for PDF files")
        print("   data/inputs/text/ - for pre-existing text files")
        return
    
    # Search recursively for PDF files (supports sample data in subdirectories)
    pdf_files = list(input_path.glob("**/*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in '{input_dir}' (searched recursively).")
        print("Please add PDF files to the directory and run the script again.")
        print("You can also place sample data in subdirectories like 'data/inputs/pdfs/sample/'")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process.")
    print()
    
    # Process the PDF files
    try:
        stats = process_pdf_directory(input_dir, output_dir)
        
        print("\n" + "=" * 50)
        print("PDF Extraction Complete!")
        print(f"Files processed: {stats['processed']}")
        print(f"Files successful: {stats['successful']}")
        print(f"Files failed: {stats['failed']}")
        
        if stats['failed'] > 0:
            print(f"\nWarning: {stats['failed']} files failed to process.")
            print("Check the error messages above for details.")
        
        print(f"\nText files saved to: {output_dir}")
        print("\nNext step: Run 'python scripts/2_extract_election_data.py'")
        
    except Exception as e:
        print(f"Error during PDF extraction: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
