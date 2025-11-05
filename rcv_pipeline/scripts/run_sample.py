#!/usr/bin/env python3
"""
Run Pipeline on Specific Sample
===============================

This script allows you to run the full RCV pipeline on different PDF samples
without deleting existing data. Each sample gets its own directory structure.

Usage: python scripts/run_sample.py <sample_name>
Example: python scripts/run_sample.py sample_1
"""

import sys
import os
import shutil
from pathlib import Path
import argparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.pdf_utils import process_pdf_directory
from utils.llm_utils import process_text_files_for_elections
from utils.data_utils import load_election_data, clean_and_standardize_data, save_cleaned_data
from utils.validation_utils import validate_election_data, save_validation_report

def setup_sample_directories(sample_name):
    """Create directory structure for a specific sample."""
    base_dir = Path("data") / "samples" / sample_name
    
    # Create sample-specific directories
    directories = {
        "raw": base_dir / "raw",
        "txt_inputs": base_dir / "txt_inputs",  # Pre-existing text files
        "txt_files": base_dir / "txt_files",    # Generated + existing text files (merged)
        "csv_files": base_dir / "csv_files",
        "cleaned": base_dir / "cleaned",
        "reports": base_dir / "validation_reports"
    }
    
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    return directories

def copy_pdfs_to_sample(source_dir, sample_dirs):
    """Copy PDFs from source directory to sample raw directory."""
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return False
    
    pdf_files = list(source_path.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in: {source_dir}")
        return False
    
    # Copy PDFs to sample raw directory
    for pdf_file in pdf_files:
        dest_file = sample_dirs["raw"] / pdf_file.name
        shutil.copy2(pdf_file, dest_file)
        print(f"✓ Copied: {pdf_file.name}")
    
    print(f"✓ Copied {len(pdf_files)} PDF files to sample directory")
    return True

def detect_input_types(sample_dirs):
    """Detect and categorize input files."""
    pdf_files = list(sample_dirs["raw"].glob("*.pdf"))
    existing_txt_files = list(sample_dirs["txt_inputs"].glob("*.txt"))
    
    return {
        "pdfs": pdf_files,
        "existing_txts": existing_txt_files,
        "total_inputs": len(pdf_files) + len(existing_txt_files)
    }

def merge_text_inputs(sample_dirs):
    """Merge PDF-generated text files with pre-existing text files."""
    print("🔄 Merging text input sources...")
    
    # Get all text files from both sources
    generated_txts = list(sample_dirs["txt_files"].glob("*.txt"))
    existing_txts = list(sample_dirs["txt_inputs"].glob("*.txt"))
    
    total_txts = len(generated_txts) + len(existing_txts)
    
    if total_txts == 0:
        print("⚠️  No text files found to process")
        return False
    
    print(f"   📄 Generated from PDFs: {len(generated_txts)}")
    print(f"   📝 Pre-existing text files: {len(existing_txts)}")
    print(f"   📊 Total text files: {total_txts}")
    
    # Copy existing text files to txt_files directory (merge with generated ones)
    for txt_file in existing_txts:
        dest_file = sample_dirs["txt_files"] / txt_file.name
        # Avoid overwriting if file with same name exists
        if dest_file.exists():
            base_name = txt_file.stem
            extension = txt_file.suffix
            counter = 1
            while dest_file.exists():
                dest_file = sample_dirs["txt_files"] / f"{base_name}_existing_{counter}{extension}"
                counter += 1
        shutil.copy2(txt_file, dest_file)
        print(f"   ✓ Merged: {txt_file.name}")
    
    print("✓ Text input merging completed")
    return True

def run_pipeline_on_sample(sample_name, source_dir=None):
    """Run the complete pipeline on a specific sample."""
    print(f"🚀 Running RCV Pipeline on Sample: {sample_name}")
    print("=" * 60)
    
    # Setup directories
    sample_dirs = setup_sample_directories(sample_name)
    
    # Detect input types
    input_info = detect_input_types(sample_dirs)
    print(f"\n📊 Input Analysis:")
    print(f"   📄 PDF files: {len(input_info['pdfs'])}")
    print(f"   📝 Pre-existing text files: {len(input_info['existing_txts'])}")
    print(f"   📊 Total inputs: {input_info['total_inputs']}")
    
    if input_info['total_inputs'] == 0:
        print("❌ No input files found. Please add PDFs to 'raw/' or text files to 'txt_inputs/'")
        return False
    
    # Copy PDFs if source directory provided
    if source_dir:
        print(f"\n📁 Copying PDFs from: {source_dir}")
        if not copy_pdfs_to_sample(source_dir, sample_dirs):
            return False
        # Re-detect after copying
        input_info = detect_input_types(sample_dirs)
    
    # Step 1: Extract PDFs to text (if PDFs exist)
    if len(input_info['pdfs']) > 0:
        print(f"\n📄 Step 1: Extracting PDFs to text...")
        try:
            process_pdf_directory(
                input_dir=str(sample_dirs["raw"]),
                output_dir=str(sample_dirs["txt_files"])
            )
            print("✓ PDF extraction completed")
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            return False
    else:
        print(f"\n📄 Step 1: Skipping PDF extraction (no PDFs found)")
    
    # Merge text inputs (combine generated + existing)
    if not merge_text_inputs(sample_dirs):
        return False
    
    # Step 2: Extract election data using LLM
    print(f"\n🤖 Step 2: Extracting election data using LLM...")
    try:
        process_text_files_for_elections(
            input_dir=str(sample_dirs["txt_files"]),
            output_dir=str(sample_dirs["csv_files"])
        )
        print("✓ Election data extraction completed")
    except Exception as e:
        print(f"❌ Election data extraction failed: {e}")
        return False
    
    # Step 3: Post-process and clean data
    print(f"\n🧹 Step 3: Post-processing and cleaning data...")
    try:
        elections_df, candidates_df, rounds_df = load_election_data(str(sample_dirs["csv_files"]))
        elections_clean, candidates_clean, rounds_clean = clean_and_standardize_data(
            elections_df, candidates_df, rounds_df
        )
        save_cleaned_data(
            elections_clean, candidates_clean, rounds_clean, str(sample_dirs["cleaned"])
        )
        print("✓ Data cleaning completed")
    except Exception as e:
        print(f"❌ Data cleaning failed: {e}")
        return False
    
    # Step 4: Validate data
    print(f"\n✅ Step 4: Validating data...")
    try:
        validation_results = validate_election_data(
            elections_clean, candidates_clean, rounds_clean
        )
        save_validation_report(validation_results, str(sample_dirs["reports"]))
        
        # Save tier-based scores to CSV files
        print("Saving tier-based validation scores...")
        
        if len(validation_results["election_scores"]) > 0:
            election_scores_path = sample_dirs["cleaned"] / "Elections_DF_cleaned_with_scores.csv"
            
            # Merge election scores with original election data
            elections_with_scores = elections_clean.merge(
                validation_results["election_scores"][['election_id', 'tier', 'flags_str']], 
                on='election_id', 
                how='left'
            )
            elections_with_scores['validation_tier'] = elections_with_scores['tier'].fillna(0).astype(int)
            elections_with_scores['validation_flags'] = elections_with_scores['flags_str'].fillna('')
            elections_with_scores = elections_with_scores.drop(columns=['tier', 'flags_str'], errors='ignore')
            
            elections_with_scores.to_csv(election_scores_path, index=False)
            print(f"Election scores saved to: {election_scores_path}")
        
        # Also save standalone score file
        if len(validation_results["election_scores"]) > 0:
            standalone_election_path = sample_dirs["reports"] / "election_validation_scores.csv"
            validation_results["election_scores"].to_csv(standalone_election_path, index=False)
            print(f"Standalone election scores saved to: {standalone_election_path}")
        
        print("✓ Data validation completed")
    except Exception as e:
        print(f"❌ Data validation failed: {e}")
        return False
    
    print(f"\n🎉 Pipeline completed successfully for sample: {sample_name}")
    print(f"📊 Results saved in: {sample_dirs['cleaned']}")
    print(f"📋 Validation report: {sample_dirs['reports']}")
    
    return True

def list_samples():
    """List all available samples."""
    samples_dir = Path("data") / "samples"
    if not samples_dir.exists():
        print("No samples found.")
        return
    
    samples = [d.name for d in samples_dir.iterdir() if d.is_dir()]
    if not samples:
        print("No samples found.")
        return
    
    print("Available samples:")
    for sample in samples:
        print(f"  - {sample}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run RCV pipeline on specific sample")
    parser.add_argument("sample_name", nargs='?', help="Name of the sample to process")
    parser.add_argument("--source", help="Source directory containing PDF files")
    parser.add_argument("--list", action="store_true", help="List all available samples")
    
    args = parser.parse_args()
    
    if args.list:
        list_samples()
        return
    
    if not args.sample_name:
        print("❌ Please provide a sample name")
        print("Usage: python scripts/run_sample.py <sample_name> [--source <pdf_directory>]")
        print("       python scripts/run_sample.py --list")
        return
    
    # Run pipeline on sample
    success = run_pipeline_on_sample(args.sample_name, args.source)
    
    if not success:
        print("\n❌ Pipeline failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
