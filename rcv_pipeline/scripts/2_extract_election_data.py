#!/usr/bin/env python3
"""
Script 2: Extract Election Data from Text Files
===============================================

This script processes text files in the data/processing/extracted_text/ directory to extract
structured election data using LLM processing, and saves the results as CSV files
in the data/processing/extracted_data/ directory.

Usage: python scripts/2_extract_election_data.py
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.llm_utils import process_text_files_for_elections
from dotenv import load_dotenv

def main():
    """Main function to extract election data from text files."""
    print("RCV Pipeline - Step 2: Election Data Extraction")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        return 1
    
    # Define input and output directories
    input_dir = "data/processing/extracted_text"
    output_dir = "data/processing/extracted_data"
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Check if input directory exists and has text files
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print("Please run 'python scripts/1_extract_pdfs.py' first.")
        print("Or add text files to: data/inputs/text/")
        return 1
    
    text_files = list(input_path.glob("*.txt"))
    if not text_files:
        print(f"No text files found in '{input_dir}'.")
        print("Please run 'python scripts/1_extract_pdfs.py' first.")
        print("Or add text files to: data/inputs/text/")
        return 1
    
    print(f"Found {len(text_files)} text files to process.")
    print("This will use the OpenAI API to extract structured election data.")
    print(f"Estimated API calls: {len(text_files)}")
    print()
    
    # Ask for confirmation
    response = input("Continue with election data extraction? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Extraction cancelled.")
        return 0
    
    # Process the text files
    try:
        print("\nStarting election data extraction...")
        stats = process_text_files_for_elections(
            input_dir=input_dir,
            output_dir=output_dir,
            api_key=api_key,
            batch_size=5  # Save data every 5 files
        )
        
        print("\n" + "=" * 50)
        print("Election Data Extraction Complete!")
        print(f"Files processed: {stats['processed']}")
        print(f"Files successful: {stats['successful']}")
        print(f"Files failed: {stats['failed']}")
        print(f"API calls made: {stats['api_calls']}")
        
        if stats['failed'] > 0:
            print(f"\nWarning: {stats['failed']} files failed to process.")
            print("Check the error messages above for details.")
        
        print(f"\nCSV files saved to: {output_dir}")
        print("\nNext step: Run 'python scripts/3_post_process.py'")
        
    except Exception as e:
        print(f"Error during election data extraction: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
