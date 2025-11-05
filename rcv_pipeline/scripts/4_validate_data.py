#!/usr/bin/env python3
"""
Script 4: Validate Election Data
================================

This script loads the cleaned election data CSV files and runs comprehensive
validation checks to identify data quality issues and problematic elections.

Usage: python scripts/4_validate_data.py
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.data_utils import load_election_data
from utils.validation_utils import validate_election_data, save_validation_report

def main():
    """Main function to validate election data."""
    print("RCV Pipeline - Step 4: Data Validation")
    print("=" * 50)
    
    # Define input and output directories
    input_dir = "data/outputs/cleaned"
    output_dir = "data/outputs/validation_reports"
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Check if input directory exists and has cleaned CSV files
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print("Please run 'python scripts/3_post_process.py' first.")
        return 1
    
    cleaned_files = list(input_path.glob("*_cleaned.csv"))
    if not cleaned_files:
        print(f"No cleaned CSV files found in '{input_dir}'.")
        print("Please run 'python scripts/3_post_process.py' first.")
        return 1
    
    print(f"Found {len(cleaned_files)} cleaned CSV files to validate.")
    print()
    
    # Process the data
    try:
        print("Loading cleaned election data...")
        elections_df, candidates_df, rounds_df = load_election_data(input_dir)
        
        print("\nRunning validation checks...")
        validation_results = validate_election_data(elections_df, candidates_df, rounds_df)
        
        print("\nSaving validation report...")
        report_path = save_validation_report(validation_results, output_dir)
        
        # Save tier-based scores to CSV files
        print("Saving tier-based validation scores...")
        
        if len(validation_results["election_scores"]) > 0:
            election_scores_path = Path(input_dir) / "Elections_DF_cleaned_with_scores.csv"
            
            # Merge election scores with original election data
            elections_with_scores = elections_df.merge(
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
            standalone_election_path = Path(output_dir) / "election_validation_scores.csv"
            validation_results["election_scores"].to_csv(standalone_election_path, index=False)
            print(f"Standalone election scores saved to: {standalone_election_path}")
        
        print("\n" + "=" * 50)
        print("Data Validation Complete!")
        print(f"Overall Score: {validation_results['overall_score']:.1f}/100")
        print()
        
        # Display validation summary
        print("Validation Summary:")
        print("-" * 20)
        for rule_name, rule_result in validation_results["validation_rules"].items():
            status = "✓ PASSED" if rule_result["passed"] else "✗ FAILED"
            print(f"  {rule_result['rule_name']}: {status} ({rule_result['score']}/100)")
        
        # Display problematic elections if any
        if validation_results["problematic_elections"]:
            print(f"\nProblematic Elections ({len(validation_results['problematic_elections'])}):")
            print("-" * 30)
            for election_id in validation_results["problematic_elections"]:
                print(f"  - {election_id}")
        else:
            print("\n✓ No problematic elections identified!")
        
        print(f"\nDetailed validation report saved to: {report_path}")
        print("\nPipeline complete! Your election data is ready for use.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure you have the required cleaned CSV files from step 3.")
        return 1
    except Exception as e:
        print(f"Error during validation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
