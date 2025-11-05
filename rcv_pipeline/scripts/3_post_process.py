#!/usr/bin/env python3
"""
Script 3: Post-Process Election Data
===================================

This script loads the extracted election data CSV files, cleans and standardizes
the data, and saves the cleaned results to the data/outputs/cleaned/ directory.

Usage: python scripts/3_post_process.py
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.data_utils import load_election_data, clean_and_standardize_data, save_cleaned_data

def main():
    """Main function to post-process election data."""
    print("RCV Pipeline - Step 3: Post-Processing Election Data")
    print("=" * 50)
    
    # Define input and output directories
    input_dir = "data/processing/extracted_data"
    output_dir = "data/outputs/cleaned"
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Check if input directory exists and has CSV files
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print("Please run 'python scripts/2_extract_election_data.py' first.")
        return 1
    
    csv_files = list(input_path.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in '{input_dir}'.")
        print("Please run 'python scripts/2_extract_election_data.py' first.")
        return 1
    
    print(f"Found {len(csv_files)} CSV files to process.")
    print()
    
    # Process the data
    try:
        print("Loading election data...")
        elections_df, candidates_df, rounds_df = load_election_data(input_dir)
        
        print("\nCleaning and standardizing data...")
        elections_clean, candidates_clean, rounds_clean = clean_and_standardize_data(
            elections_df, candidates_df, rounds_df
        )
        
        # Show transfer computation summary
        if "transfer_original" in candidates_clean.columns and "transfer_calc" in candidates_clean.columns:
            print("\nTransfer Computation Summary:")
            print("-" * 30)
            
            # Count non-zero transfers in original data
            original_nonzero = (candidates_clean["transfer_original"] != 0).sum()
            total_records = len(candidates_clean)
            
            print(f"Total candidate-round records: {total_records}")
            print(f"Records with non-zero original transfers: {original_nonzero}")
            print(f"Records with computed transfers: {len(candidates_clean)}")
            
            # Show sample of computed transfers
            sample_transfers = candidates_clean[
                (candidates_clean["transfer_calc"] != 0) & 
                (candidates_clean["round"] > 1)
            ].head(5)
            
            if len(sample_transfers) > 0:
                print(f"\nSample computed transfers (rounds > 1):")
                for _, row in sample_transfers.iterrows():
                    print(f"  {row['election_id']} {row['candidate_id']} round {row['round']}: {row['transfer_calc']}")
        
        print("\nSaving cleaned data...")
        save_cleaned_data(elections_clean, candidates_clean, rounds_clean, output_dir)
        
        print("\n" + "=" * 50)
        print("Post-Processing Complete!")
        print(f"Input elections: {len(elections_df)}")
        print(f"Input candidate records: {len(candidates_df)}")
        print(f"Input round records: {len(rounds_df)}")
        print()
        print(f"Cleaned elections: {len(elections_clean)}")
        print(f"Cleaned candidate records: {len(candidates_clean)}")
        print(f"Cleaned round records: {len(rounds_clean)}")
        
        if "transfer_calc" in candidates_clean.columns:
            print(f"\n✓ Transfer values computed from vote counts")
            print(f"✓ Original transfer values preserved as 'transfer_original'")
            print(f"✓ Computed transfer values stored as 'transfer_calc'")
        
        print(f"\nCleaned data saved to: {output_dir}")
        print("\nNext step: Run 'python scripts/4_validate_data.py'")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure you have the required CSV files from step 2.")
        return 1
    except Exception as e:
        print(f"Error during post-processing: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
