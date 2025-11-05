#!/usr/bin/env python3
"""
Run All Pipeline Steps
======================

This script runs all four pipeline steps in sequence, automatically detecting
input types and adapting the pipeline accordingly.

Supported Input Types:
- PDF files only (in data/raw/)
- Text files only (in data/txt_inputs/)
- Mixed inputs (both PDFs and text files)

Usage: python scripts/run_all.py
"""

import sys
import subprocess
import shutil
from pathlib import Path

def detect_input_types():
    """Detect what types of input files are available."""
    pdfs_dir = Path("data/inputs/pdfs")
    text_dir = Path("data/inputs/text")
    
    # Check for PDFs (search recursively to support sample data in subdirectories)
    pdf_files = list(pdfs_dir.glob("**/*.pdf")) if pdfs_dir.exists() else []
    
    # Check for pre-existing text files (search recursively to support sample data in subdirectories)
    txt_files = list(text_dir.glob("**/*.txt")) if text_dir.exists() else []
    
    # Check if text directory exists but is empty
    if text_dir.exists() and not txt_files:
        print("📁 Found text input directory but it's empty")
    
    return {
        "pdfs": pdf_files,
        "existing_txts": txt_files,
        "total_inputs": len(pdf_files) + len(txt_files)
    }

def setup_mixed_input_directories():
    """Set up directories for mixed input processing."""
    # Create input directories if they don't exist
    pdfs_dir = Path("data/inputs/pdfs")
    text_dir = Path("data/inputs/text")
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    
    # Create processing directories
    extracted_text_dir = Path("data/processing/extracted_text")
    extracted_data_dir = Path("data/processing/extracted_data")
    extracted_text_dir.mkdir(parents=True, exist_ok=True)
    extracted_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output directories
    cleaned_dir = Path("data/outputs/cleaned")
    reports_dir = Path("data/outputs/validation_reports")
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    return pdfs_dir, text_dir, extracted_text_dir, extracted_data_dir, cleaned_dir, reports_dir

def merge_text_inputs(text_dir, extracted_text_dir):
    """Merge pre-existing text files with generated text files."""
    print("🔄 Merging text input sources...")
    
    # Get all text files from both sources (search recursively to support sample data in subdirectories)
    generated_txts = list(extracted_text_dir.glob("*.txt"))  # Keep non-recursive for processing output
    existing_txts = list(text_dir.glob("**/*.txt"))  # Search recursively for input text files
    
    total_txts = len(generated_txts) + len(existing_txts)
    
    if total_txts == 0:
        print("⚠️  No text files found to process")
        return False
    
    print(f"   📄 Generated from PDFs: {len(generated_txts)}")
    print(f"   📝 Pre-existing text files: {len(existing_txts)}")
    print(f"   📊 Total text files: {total_txts}")
    
    # Copy existing text files to extracted_text directory (merge with generated ones)
    for txt_file in existing_txts:
        dest_file = extracted_text_dir / txt_file.name
        # Avoid overwriting if file with same name exists
        if dest_file.exists():
            base_name = txt_file.stem
            extension = txt_file.suffix
            counter = 1
            while dest_file.exists():
                dest_file = extracted_text_dir / f"{base_name}_existing_{counter}{extension}"
                counter += 1
        shutil.copy2(txt_file, dest_file)
        print(f"   ✓ Merged: {txt_file.name}")
    
    print("✓ Text input merging completed")
    return True

def run_script(script_name, step_description):
    """Run a script and handle errors."""
    print(f"\n{'='*60}")
    print(f"STEP: {step_description}")
    print(f"Running: {script_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"✓ {step_description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {step_description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"✗ Script {script_name} not found")
        return False

def main():
    """Main function to run all pipeline steps."""
    print("RCV Pipeline - Running All Steps")
    print("=" * 60)
    print("This will run all four pipeline steps in sequence.")
    print("The pipeline automatically detects your input types and adapts accordingly.")
    print()
    
    # Detect input types
    input_info = detect_input_types()
    print("📊 Input Analysis:")
    print(f"   📄 PDF files: {len(input_info['pdfs'])}")
    print(f"   📝 Pre-existing text files: {len(input_info['existing_txts'])}")
    print(f"   📊 Total inputs: {input_info['total_inputs']}")
    
    if input_info['total_inputs'] == 0:
        print("\n❌ No input files found!")
        print("Please add files to one of these locations:")
        print("   📁 data/inputs/pdfs/ - for PDF files")
        print("   📁 data/inputs/text/ - for pre-existing text files")
        print("\nOr use the sample-based approach:")
        print("   python scripts/setup_sample.py <sample_name> --pdf-dir /path/to/pdfs")
        print("   python scripts/setup_sample.py <sample_name> --txt-dir /path/to/txts")
        return 1
    
    print("\nMake sure you have:")
    print("1. Input files (PDFs and/or text files)")
    print("2. OpenAI API key in .env file")
    print()
    
    # Ask for confirmation
    response = input("Continue with full pipeline? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Pipeline cancelled.")
        return 0
    
    # Set up directories for mixed inputs
    pdfs_dir, text_dir, extracted_text_dir, extracted_data_dir, cleaned_dir, reports_dir = setup_mixed_input_directories()
    
    # Define scripts to run based on input types
    scripts_to_run = []
    
    # Step 1: PDF extraction (only if PDFs exist)
    if len(input_info['pdfs']) > 0:
        scripts_to_run.append(("scripts/1_extract_pdfs.py", "PDF Text Extraction"))
    else:
        print("\n📄 Skipping PDF extraction (no PDFs found)")
    
    # Step 1.5: Text file preparation (if only text files exist)
    if len(input_info['pdfs']) == 0 and len(input_info['existing_txts']) > 0:
        print("\n📝 Preparing text files for processing...")
        if not merge_text_inputs(text_dir, extracted_text_dir):
            print("❌ Failed to prepare text files")
            return 1
        print("✓ Text files prepared successfully")
    
    # Step 2: Text merging (if we have mixed inputs)
    if len(input_info['pdfs']) > 0 and len(input_info['existing_txts']) > 0:
        # We'll handle merging manually after PDF extraction
        pass
    
    # Step 3: Election data extraction (always needed)
    scripts_to_run.append(("scripts/2_extract_election_data.py", "Election Data Extraction"))
    
    # Step 4: Post-processing (always needed)
    scripts_to_run.append(("scripts/3_post_process.py", "Post-Processing"))
    
    # Step 5: Validation (always needed)
    scripts_to_run.append(("scripts/4_validate_data.py", "Data Validation"))
    
    # Run each script
    for script_name, description in scripts_to_run:
        if not run_script(script_name, description):
            print(f"\n❌ Pipeline failed at: {description}")
            print("Please fix the issue and run the failed step individually:")
            print(f"python {script_name}")
            return 1
        
        # After PDF extraction, merge text inputs if needed
        if description == "PDF Text Extraction" and len(input_info['existing_txts']) > 0:
            print("\n🔄 Merging text inputs after PDF extraction...")
            if not merge_text_inputs(text_dir, extracted_text_dir):
                print("⚠️  Text merging failed, but continuing with pipeline...")
    
    print(f"\n{'='*60}")
    print("🎉 PIPELINE COMPLETE!")
    print("All steps completed successfully.")
    print("Your election data is ready for use.")
    print(f"{'='*60}")
    
    # Show final summary
    final_txt_files = list(extracted_text_dir.glob("*.txt"))
    print(f"\n📊 Final Results:")
    print(f"   📄 Total text files processed: {len(final_txt_files)}")
    print(f"   📁 Output location: data/outputs/cleaned/")
    print(f"   📋 Validation report: data/outputs/validation_reports/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
