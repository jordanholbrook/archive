#!/usr/bin/env python3
"""
Setup New Sample
================

Helper script to set up a new sample directory and copy PDF files and/or text files into it.

Usage: 
  python scripts/setup_sample.py <sample_name> <pdf_source_directory>
  python scripts/setup_sample.py <sample_name> --pdf-dir <pdf_dir> --txt-dir <txt_dir>
  python scripts/setup_sample.py <sample_name> --txt-only <txt_source_directory>

Examples:
  python scripts/setup_sample.py sample_1 /path/to/pdfs
  python scripts/setup_sample.py mixed_sample --pdf-dir /pdfs --txt-dir /txts
  python scripts/setup_sample.py txt_only_sample --txt-only /path/to/txts
"""

import sys
import shutil
from pathlib import Path
import argparse

def setup_new_sample(sample_name, pdf_source_dir=None, txt_source_dir=None, txt_only=False):
    """Set up a new sample directory and copy PDFs and/or text files."""
    print(f"🔧 Setting up new sample: {sample_name}")
    print("=" * 50)
    
    # Create sample directory structure
    sample_base = Path("data") / "samples" / sample_name
    sample_dirs = {
        "raw": sample_base / "raw",
        "txt_inputs": sample_base / "txt_inputs",  # Pre-existing text files
        "txt_files": sample_base / "txt_files",    # Generated + existing text files (merged)
        "csv_files": sample_base / "csv_files", 
        "cleaned": sample_base / "cleaned",
        "reports": sample_base / "validation_reports"
    }
    
    # Create directories
    for dir_path in sample_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")
    
    files_copied = {"pdfs": 0, "txts": 0}
    
    # Copy PDFs (if provided)
    if pdf_source_dir and not txt_only:
        source_path = Path(pdf_source_dir)
        if not source_path.exists():
            print(f"❌ PDF source directory not found: {pdf_source_dir}")
            return False
        
        pdf_files = list(source_path.glob("*.pdf"))
        if not pdf_files:
            print(f"⚠️  No PDF files found in: {pdf_source_dir}")
        else:
            # Copy PDFs to sample raw directory
            for pdf_file in pdf_files:
                dest_file = sample_dirs["raw"] / pdf_file.name
                shutil.copy2(pdf_file, dest_file)
                print(f"✓ Copied PDF: {pdf_file.name}")
                files_copied["pdfs"] += 1
    
    # Copy pre-existing text files (if provided)
    if txt_source_dir:
        source_path = Path(txt_source_dir)
        if not source_path.exists():
            print(f"❌ Text source directory not found: {txt_source_dir}")
            return False
        
        txt_files = list(source_path.glob("*.txt"))
        if not txt_files:
            print(f"⚠️  No text files found in: {txt_source_dir}")
        else:
            # Copy text files to txt_inputs directory
            for txt_file in txt_files:
                dest_file = sample_dirs["txt_inputs"] / txt_file.name
                shutil.copy2(txt_file, dest_file)
                print(f"✓ Copied text: {txt_file.name}")
                files_copied["txts"] += 1
    
    # Validate that we have at least some input files
    total_files = files_copied["pdfs"] + files_copied["txts"]
    if total_files == 0:
        print("❌ No files found in any source directory")
        return False
    
    print(f"\n🎉 Sample '{sample_name}' setup complete!")
    print(f"📁 Sample directory: {sample_base}")
    print(f"📄 PDF files copied: {files_copied['pdfs']}")
    print(f"📝 Text files copied: {files_copied['txts']}")
    print(f"📊 Total input files: {total_files}")
    
    if files_copied["pdfs"] > 0 and files_copied["txts"] > 0:
        print(f"\n💡 Mixed input sample created!")
        print(f"   - PDFs will be converted to text in Step 1")
        print(f"   - Pre-existing text files will be merged automatically")
        print(f"   - All text files will be processed together in Step 2")
    
    print(f"\nTo run the pipeline on this sample:")
    print(f"  python scripts/run_sample.py {sample_name}")
    
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
    parser = argparse.ArgumentParser(description="Set up a new sample directory with mixed input support")
    parser.add_argument("sample_name", help="Name of the new sample")
    
    # Input source options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("pdf_source", nargs="?", help="Directory containing PDF files (legacy positional argument)")
    group.add_argument("--pdf-dir", help="Directory containing PDF files")
    group.add_argument("--txt-only", help="Directory containing text files (text-only sample)")
    
    # Additional options
    parser.add_argument("--txt-dir", help="Directory containing pre-existing text files (use with --pdf-dir)")
    parser.add_argument("--list", action="store_true", help="List all available samples")
    
    args = parser.parse_args()
    
    if args.list:
        list_samples()
        return
    
    # Handle different input scenarios
    if args.txt_only:
        # Text-only sample
        success = setup_new_sample(args.sample_name, txt_source_dir=args.txt_only, txt_only=True)
    elif args.pdf_dir:
        # PDF + optional text sample
        success = setup_new_sample(args.sample_name, pdf_source_dir=args.pdf_dir, txt_source_dir=args.txt_dir)
    elif args.pdf_source:
        # Legacy PDF-only sample
        success = setup_new_sample(args.sample_name, pdf_source_dir=args.pdf_source)
    else:
        print("❌ Please provide input source directories")
        print("Examples:")
        print("  python scripts/setup_sample.py sample_1 /path/to/pdfs")
        print("  python scripts/setup_sample.py mixed_sample --pdf-dir /pdfs --txt-dir /txts")
        print("  python scripts/setup_sample.py txt_only_sample --txt-only /path/to/txts")
        return
    
    if not success:
        print("\n❌ Sample setup failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
