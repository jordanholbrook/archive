"""
Simple validation utilities for election data quality checks.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ------------------------------
# Tier-based Validation System
# ------------------------------

# Tier meaning: 0=clean, 1=warning/minor, 2=moderate, 3=major
TIER_RULES = {
    "positive_transfer_balance": 3,    # sum(transfer)>0 in any round
    "single_winner_violation": 3,      # !=1 elected in final round
    "cands_gt_round_total": 3,         # sum(cands) > round_total

    "large_neg_transfer_balance": 2,   # e.g., ≤ -1000 or ≤ −2% of round size
    "transfer_diff_large": 2,          # |transfer_orig - calc| > δ_large
    "round_sequence_gap": 2,           # skipped/duplicated rounds

    "vote_monotonicity_violation": 1,  # continuing cand loses votes
    "cands_lt_round_total_gap": 1,     # gap likely exhausted/undervote/overvote
    "transfer_diff_small": 1,          # |transfer_orig - calc| in (δ_small, δ_large]
}

DEFAULT_THRESHOLDS = {
    # tweak centrally; the pipeline code won't change
    "large_neg_transfer_abs": 1000,  # treat ≤ -1000 as "large"
    "transfer_diff_small": 50,       # 0..50 = ignore; 51..200 = small
    "transfer_diff_large": 200,      # >200 = large
    "percent_small": 0.01,           # 1% of round size
    "percent_large": 0.02,           # 2% of round size
}

def _max_tier_from_flags(flags):
    if not flags:
        return 0
    tiers = []
    for f in flags:
        tiers.append(TIER_RULES.get(f, 1))  # unknown flags default to minor
    return max(tiers) if tiers else 0

# ---------- Classifiers: turn numeric anomalies into standardized flags ----------

def classify_transfer_balance(sum_transfer, round_total=None):
    """
    Return a flag string or None.
    Major if positive. (Votes appearing from nowhere.)
    Optionally can treat 'very large negatives' as moderate.
    """
    if sum_transfer is None:
        return None
    if sum_transfer > 0:
        return "positive_transfer_balance"
    # Optionally flag very large negatives:
    if round_total is not None:
        # Scale threshold by % of round size if available
        large_abs = max(DEFAULT_THRESHOLDS["large_neg_transfer_abs"],
                        int(round_total * DEFAULT_THRESHOLDS["percent_large"]))
    else:
        large_abs = DEFAULT_THRESHOLDS["large_neg_transfer_abs"]
    if sum_transfer <= -large_abs:
        return "large_neg_transfer_balance"
    return None

def classify_vote_consistency(cands_sum, round_total):
    """
    Candidate sums vs. round totals.
    """
    if cands_sum is None or round_total is None:
        return None
    if cands_sum > round_total:
        return "cands_gt_round_total"
    if round_total - cands_sum > 0:
        return "cands_lt_round_total_gap"
    return None

def classify_transfer_diff(diff_abs, round_total=None):
    """
    Compare original vs computed transfer magnitudes.
    Return None, 'transfer_diff_small', or 'transfer_diff_large'.
    """
    if diff_abs is None:
        return None

    δ_small = DEFAULT_THRESHOLDS["transfer_diff_small"]
    δ_large = DEFAULT_THRESHOLDS["transfer_diff_large"]

    if round_total is not None:
        δ_small = max(δ_small, int(round_total * DEFAULT_THRESHOLDS["percent_small"]))
        δ_large = max(δ_large, int(round_total * DEFAULT_THRESHOLDS["percent_large"]))

    if diff_abs > δ_large:
        return "transfer_diff_large"
    if diff_abs > δ_small:
        return "transfer_diff_small"
    return None

def flag_single_winner(violation_bool):
    return "single_winner_violation" if violation_bool else None

def flag_round_sequence(violation_bool):
    return "round_sequence_gap" if violation_bool else None

def flag_monotonicity(violation_bool):
    return "vote_monotonicity_violation" if violation_bool else None

# ---------- Scorers: fold flags into a simple dict ----------

def score_election_from_flags(election_id, flags_list):
    """
    flags_list: list of strings (may include None; we'll ignore those)
    Return dict: {"election_id": eid, "tier": 0..3, "flags": [unique sorted flags]}
    """
    flags = [f for f in (flags_list or []) if f]
    flags = sorted(set(flags))
    tier = _max_tier_from_flags(flags)
    return {"election_id": election_id, "tier": int(tier), "flags": flags}



def compute_tier_based_scores(elections_df, candidates_df, rounds_df):
    """
    Compute election-level validation scores using the tier-based system.
    
    Args:
        elections_df: Elections DataFrame
        candidates_df: Candidates DataFrame  
        rounds_df: Rounds DataFrame
        
    Returns:
        election_scores_df: DataFrame with election validation scores
    """
    print("Computing tier-based validation scores...")
    
    election_scores = []
    
    # Process each election
    for election_id in elections_df['election_id'].unique():
        election_flags = []
        
        # Get election data
        election_candidates = candidates_df[candidates_df['election_id'] == election_id].copy()
        election_rounds = rounds_df[rounds_df['election_id'] == election_id].copy()
        
        if len(election_candidates) == 0 or len(election_rounds) == 0:
            continue
            
        # Election-level checks
        
        # 1. Single winner check
        final_round = election_rounds['round'].max()
        final_round_data = election_rounds[election_rounds['round'] == final_round]
        if len(final_round_data) > 0:
            round_total = final_round_data['total_votes'].iloc[0]
            # Check for elected candidates (case-insensitive)
            elected_count = len(election_candidates[election_candidates['status'].str.lower() == 'elected'])
            if elected_count != 1:
                election_flags.append(flag_single_winner(True))
        
        # 2. Round sequence check
        expected_rounds = list(range(1, final_round + 1))
        actual_rounds = sorted(election_rounds['round'].unique())
        if actual_rounds != expected_rounds:
            election_flags.append(flag_round_sequence(True))
        
        # 3. Transfer balance checks per round
        for round_num in election_rounds['round'].unique():
            round_data = election_rounds[election_rounds['round'] == round_num]
            if len(round_data) > 0:
                round_total = round_data['total_votes'].iloc[0]
                
                # Get transfers for this round
                round_candidates = election_candidates[election_candidates['round'] == round_num]
                if len(round_candidates) > 0 and 'transfer_calc' in round_candidates.columns:
                    sum_transfer = round_candidates['transfer_calc'].sum()
                    flag = classify_transfer_balance(sum_transfer, round_total)
                    if flag:
                        election_flags.append(flag)
                
                # Vote consistency check
                if len(round_candidates) > 0:
                    cands_sum = round_candidates['votes'].sum()
                    flag = classify_vote_consistency(cands_sum, round_total)
                    if flag:
                        election_flags.append(flag)
        
        # Store election score
        election_score = score_election_from_flags(election_id, election_flags)
        election_scores.append(election_score)
    
    # Convert to DataFrames
    election_scores_df = pd.DataFrame(election_scores)
    
    # Add flags as string representation for CSV storage
    if len(election_scores_df) > 0:
        election_scores_df['flags_str'] = election_scores_df['flags'].apply(lambda x: '|'.join(x) if x else '')
    
    print(f"Computed scores for {len(election_scores)} elections")
    
    return election_scores_df

def validate_election_data(elections_df, candidates_df, rounds_df):
    """
    Run comprehensive validation on election data.
    
    Args:
        elections_df: Elections DataFrame
        candidates_df: Candidates DataFrame
        rounds_df: Rounds DataFrame
        
    Returns:
        Dictionary containing validation results
    """
    print("Running election data validation...")
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "total_elections": len(elections_df),
        "total_candidates": len(candidates_df),
        "total_rounds": len(rounds_df),
        "validation_rules": {},
        "problematic_elections": [],
        "overall_score": 0
    }
    
    # Run individual validation rules
    validation_results["validation_rules"]["data_completeness"] = _validate_data_completeness(
        elections_df, candidates_df, rounds_df
    )
    
    validation_results["validation_rules"]["vote_consistency"] = _validate_vote_consistency(
        candidates_df, rounds_df
    )
    
    validation_results["validation_rules"]["transfer_balance"] = _validate_transfer_balance(
        candidates_df
    )
    
    # Transfer comparison validation - commented out for now but available for future use
    # validation_results["validation_rules"]["transfer_comparison"] = _validate_transfer_comparison(
    #     candidates_df
    # )
    
    validation_results["validation_rules"]["single_winner"] = _validate_single_winner(
        candidates_df
    )
    
    validation_results["validation_rules"]["vote_monotonicity"] = _validate_vote_monotonicity(
        candidates_df
    )
    
    validation_results["validation_rules"]["election_id_consistency"] = _validate_election_id_consistency(
        elections_df, candidates_df, rounds_df
    )
    
    validation_results["validation_rules"]["round_sequence"] = _validate_round_sequence(
        candidates_df, rounds_df
    )
    
    # Calculate overall score
    validation_results["overall_score"] = _calculate_overall_score(validation_results["validation_rules"])
    
    # Identify problematic elections
    validation_results["problematic_elections"] = _identify_problematic_elections(
        validation_results["validation_rules"]
    )
    
    # Compute tier-based validation scores
    election_scores_df = compute_tier_based_scores(
        elections_df, candidates_df, rounds_df
    )
    validation_results["election_scores"] = election_scores_df
    
    print(f"Validation complete. Overall score: {validation_results['overall_score']:.1f}/100")
    
    return validation_results

def _validate_data_completeness(elections_df, candidates_df, rounds_df):
    """Validate that all required fields are present and complete."""
    results = {
        "rule_name": "Data Completeness",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    # Check elections data
    required_election_fields = ["election_id", "year", "state", "office", "juris", "election_type"]
    for field in required_election_fields:
        if field not in elections_df.columns:
            results["issues"].append(f"Missing field '{field}' in elections data")
            results["passed"] = False
        elif elections_df[field].isna().any():
            missing_count = elections_df[field].isna().sum()
            results["issues"].append(f"{missing_count} missing values in elections.{field}")
            results["passed"] = False
    
    # Check candidates data
    required_candidate_fields = ["election_id", "candidate_id", "round", "votes", "percentage"]
    for field in required_candidate_fields:
        if field not in candidates_df.columns:
            results["issues"].append(f"Missing field '{field}' in candidates data")
            results["passed"] = False
        elif candidates_df[field].isna().any():
            missing_count = candidates_df[field].isna().sum()
            results["issues"].append(f"{missing_count} missing values in candidates.{field}")
            results["passed"] = False
    
    # Check for computed transfer field
    if "transfer_calc" not in candidates_df.columns:
        results["issues"].append("Missing computed transfer field 'transfer_calc' in candidates data")
        results["passed"] = False
    
    # Check rounds data
    required_round_fields = ["election_id", "round", "total_votes"]
    for field in required_round_fields:
        if field not in rounds_df.columns:
            results["issues"].append(f"Missing field '{field}' in rounds data")
            results["passed"] = False
        elif rounds_df[field].isna().any():
            missing_count = rounds_df[field].isna().sum()
            results["issues"].append(f"{missing_count} missing values in rounds.{field}")
            results["passed"] = False
    
    # Calculate score based on number of issues
    if results["issues"]:
        results["score"] = max(0, 100 - len(results["issues"]) * 10)
    
    return results

def _validate_vote_consistency(candidates_df, rounds_df):
    """Validate that vote counts are consistent across rounds."""
    results = {
        "rule_name": "Vote Consistency",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    # Check that total votes in candidates match total votes in rounds
    for election_id in candidates_df["election_id"].unique():
        election_candidates = candidates_df[candidates_df["election_id"] == election_id]
        election_rounds = rounds_df[rounds_df["election_id"] == election_id]
        
        for round_num in election_rounds["round"].unique():
            round_candidates = election_candidates[election_candidates["round"] == round_num]
            round_total = election_rounds[election_rounds["round"] == round_num]["total_votes"].iloc[0]
            
            candidate_vote_sum = round_candidates["votes"].sum()
            
            # In RCV, round total includes overvotes, undervotes, and exhausted ballots
            # So candidates sum should be <= round total
            if candidate_vote_sum > round_total:
                results["issues"].append(
                    f"Vote count mismatch in {election_id} round {round_num}: "
                    f"candidates sum to {candidate_vote_sum}, round total is {round_total} "
                    f"(candidates sum should not exceed round total)"
                )
                results["passed"] = False
            elif candidate_vote_sum < round_total:
                # This is normal - round total includes overvotes, undervotes, exhausted ballots
                difference = round_total - candidate_vote_sum
                if difference > 100:  # Flag significant differences for review
                    results["issues"].append(
                        f"Large vote difference in {election_id} round {round_num}: "
                        f"candidates sum to {candidate_vote_sum}, round total is {round_total} "
                        f"(difference: {difference} votes - may include overvotes/undervotes/exhausted)"
                    )
                    # Don't fail validation for this, just note it
                    results["score"] = min(results["score"], 95)  # Slight score reduction
    
    # Calculate score based on number of critical issues
    critical_issues = [issue for issue in results["issues"] if "should not exceed" in issue]
    if critical_issues:
        results["score"] = max(0, 100 - len(critical_issues) * 10)
    
    return results

def _validate_transfer_balance(candidates_df):
    """Validate that vote transfers balance across rounds using computed transfer values."""
    results = {
        "rule_name": "Transfer Balance",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    # Check transfer balance for each election and round (after round 1)
    for election_id in candidates_df["election_id"].unique():
        election_data = candidates_df[candidates_df["election_id"] == election_id]
        
        for round_num in election_data["round"].unique():
            if round_num == 1:  # Skip round 1 (no transfers)
                continue
            
            round_data = election_data[election_data["round"] == round_num]
            transfer_sum = round_data["transfer_calc"].sum()
            
            # Transfers should sum to non-positive (≤ 0)
            # Negative sums are normal due to exhausted ballots, overvotes, undervotes
            # Positive sums indicate votes appearing "out of thin air" (mathematically impossible)
            if transfer_sum > 0:
                results["issues"].append(
                    f"Transfer imbalance in {election_id} round {round_num}: "
                    f"sum = {transfer_sum} (should be ≤ 0, indicates votes appearing from nowhere)"
                )
                results["passed"] = False
            elif transfer_sum < 0:
                # This is normal - negative transfers indicate exhausted ballots, overvotes, undervotes
                if abs(transfer_sum) > 100:  # Flag significant negative transfers for review
                    results["issues"].append(
                        f"Large negative transfer sum in {election_id} round {round_num}: "
                        f"sum = {transfer_sum} (may include many exhausted ballots/overvotes/undervotes)"
                    )
                    # Don't fail validation for this, just note it
                    results["score"] = min(results["score"], 95)  # Slight score reduction
    
    # Calculate score based on number of critical issues (positive transfer sums)
    critical_issues = [issue for issue in results["issues"] if "should be ≤ 0" in issue]
    if critical_issues:
        results["score"] = max(0, 100 - len(critical_issues) * 10)
    
    return results

def _validate_transfer_comparison(candidates_df):
    """Compare original transfer values with computed transfer values."""
    results = {
        "rule_name": "Transfer Comparison",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    # Check if we have both original and computed transfer fields
    if "transfer_original" not in candidates_df.columns:
        results["issues"].append("No original transfer field available for comparison")
        results["passed"] = False
        results["score"] = 50
        return results
    
    if "transfer_calc" not in candidates_df.columns:
        results["issues"].append("No computed transfer field available for comparison")
        results["passed"] = False
        results["score"] = 50
        return results
    
    # Compare original vs computed transfers
    comparison_df = candidates_df[["election_id", "candidate_id", "round", "transfer_original", "transfer_calc"]].copy()
    
    # Convert to numeric for comparison
    comparison_df["transfer_original_num"] = pd.to_numeric(comparison_df["transfer_original"], errors="coerce").fillna(0)
    comparison_df["transfer_calc_num"] = pd.to_numeric(comparison_df["transfer_calc"], errors="coerce").fillna(0)
    
    # Calculate differences
    comparison_df["transfer_diff"] = comparison_df["transfer_calc_num"] - comparison_df["transfer_original_num"]
    
    # Find significant differences (more than 1 vote difference)
    significant_diffs = comparison_df[abs(comparison_df["transfer_diff"]) > 1]
    
    if len(significant_diffs) > 0:
        diff_count = len(significant_diffs)
        results["issues"].append(
            f"Found {diff_count} significant differences between original and computed transfer values"
        )
        
        # Show examples of differences
        sample_diffs = significant_diffs.head(3)
        for _, row in sample_diffs.iterrows():
            results["issues"].append(
                f"  {row['election_id']} {row['candidate_id']} round {row['round']}: "
                f"original={row['transfer_original']}, computed={row['transfer_calc']}, diff={row['transfer_diff']}"
            )
        
        results["passed"] = False
        results["score"] = max(0, 100 - min(diff_count, 20) * 2)  # Reduce score based on number of differences
    
    return results

def _validate_single_winner(candidates_df):
    """Validate that each election has exactly one winner."""
    results = {
        "rule_name": "Single Winner",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    for election_id in candidates_df["election_id"].unique():
        election_data = candidates_df[candidates_df["election_id"] == election_id]
        
        # Find the final round
        final_round = election_data["round"].max()
        final_round_data = election_data[election_data["round"] == final_round]
        
        # Count candidates with status "Elected"
        elected_candidates = final_round_data[final_round_data["status"] == "Elected"]
        
        if len(elected_candidates) == 0:
            results["issues"].append(
                f"Election {election_id}: No winner identified in final round {final_round}"
            )
            results["passed"] = False
        elif len(elected_candidates) > 1:
            winner_names = elected_candidates["name"].tolist()
            results["issues"].append(
                f"Election {election_id}: Multiple winners identified in final round {final_round}: {winner_names}"
            )
            results["passed"] = False
    
    # Calculate score based on number of issues
    if results["issues"]:
        results["score"] = max(0, 100 - len(results["issues"]) * 10)
    
    return results

def _validate_vote_monotonicity(candidates_df):
    """Validate that for all remaining candidates, votes are monotonically increasing over rounds."""
    results = {
        "rule_name": "Vote Monotonicity",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    for election_id in candidates_df["election_id"].unique():
        election_data = candidates_df[candidates_df["election_id"] == election_id]
        
        for candidate_id in election_data["candidate_id"].unique():
            candidate_data = election_data[election_data["candidate_id"] == candidate_id].sort_values("round")
            
            # Check vote monotonicity for this candidate
            prev_votes = None
            for _, row in candidate_data.iterrows():
                current_votes = row["votes"]
                
                if prev_votes is not None:
                    # For remaining candidates (not eliminated), votes should not decrease
                    if row["status"] != "Eliminated" and current_votes < prev_votes:
                        results["issues"].append(
                            f"Vote monotonicity violation in {election_id} candidate {candidate_id}: "
                            f"Round {row['round']-1}: {prev_votes} votes, Round {row['round']}: {current_votes} votes"
                        )
                        results["passed"] = False
                
                prev_votes = current_votes
    
    # Calculate score based on number of issues
    if results["issues"]:
        results["score"] = max(0, 100 - len(results["issues"]) * 5)
    
    return results

def _validate_election_id_consistency(elections_df, candidates_df, rounds_df):
    """Validate that election IDs are consistent across all DataFrames."""
    results = {
        "rule_name": "Election ID Consistency",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    # Get all election IDs
    election_ids = set(elections_df["election_id"])
    candidate_election_ids = set(candidates_df["election_id"])
    round_election_ids = set(rounds_df["election_id"])
    
    # Check that all elections appear in all DataFrames
    missing_in_candidates = election_ids - candidate_election_ids
    missing_in_rounds = election_ids - round_election_ids
    
    if missing_in_candidates:
        results["issues"].append(
            f"Elections missing from candidates data: {list(missing_in_candidates)}"
        )
        results["passed"] = False
    
    if missing_in_rounds:
        results["issues"].append(
            f"Elections missing from rounds data: {list(missing_in_rounds)}"
        )
        results["passed"] = False
    
    # Check for extra elections in other DataFrames
    extra_in_candidates = candidate_election_ids - election_ids
    extra_in_rounds = round_election_ids - election_ids
    
    if extra_in_candidates:
        results["issues"].append(
            f"Extra elections in candidates data: {list(extra_in_candidates)}"
        )
        results["passed"] = False
    
    if extra_in_rounds:
        results["issues"].append(
            f"Extra elections in rounds data: {list(extra_in_rounds)}"
        )
        results["passed"] = False
    
    # Calculate score based on number of issues
    if results["issues"]:
        results["score"] = max(0, 100 - len(results["issues"]) * 10)
    
    return results

def _validate_round_sequence(candidates_df, rounds_df):
    """Validate that round sequences are logical."""
    results = {
        "rule_name": "Round Sequence",
        "passed": True,
        "issues": [],
        "score": 100
    }
    
    # Check that rounds start from 1 and are sequential
    for election_id in candidates_df["election_id"].unique():
        election_candidates = candidates_df[candidates_df["election_id"] == election_id]
        election_rounds = rounds_df[rounds_df["election_id"] == election_id]
        
        # Check candidates data
        candidate_rounds = sorted(election_candidates["round"].unique())
        if candidate_rounds[0] != 1:
            results["issues"].append(
                f"Election {election_id}: rounds don't start from 1 (starts with {candidate_rounds[0]})"
            )
            results["passed"] = False
        
        # Check for gaps in round sequence
        expected_rounds = list(range(1, max(candidate_rounds) + 1))
        if candidate_rounds != expected_rounds:
            results["issues"].append(
                f"Election {election_id}: non-sequential rounds: {candidate_rounds}"
            )
            results["passed"] = False
        
        # Check rounds data
        round_numbers = sorted(election_rounds["round"].unique())
        if round_numbers != candidate_rounds:
            results["issues"].append(
                f"Election {election_id}: round mismatch between candidates ({candidate_rounds}) "
                f"and rounds ({round_numbers})"
            )
            results["passed"] = False
    
    # Calculate score based on number of issues
    if results["issues"]:
        results["score"] = max(0, 100 - len(results["issues"]) * 10)
    
    return results

def _calculate_overall_score(validation_rules):
    """Calculate overall validation score."""
    if not validation_rules:
        return 0
    
    total_score = sum(rule["score"] for rule in validation_rules.values())
    return total_score / len(validation_rules)

def _identify_problematic_elections(validation_rules):
    """Identify elections with validation issues."""
    problematic_elections = []
    
    for rule_name, rule_result in validation_rules.items():
        if not rule_result["passed"]:
            # Extract election IDs from issues
            for issue in rule_result["issues"]:
                if "election" in issue.lower():
                    # Try to extract election ID from issue message
                    if "Election " in issue:
                        election_id = issue.split("Election ")[1].split(":")[0].strip()
                        if election_id not in problematic_elections:
                            problematic_elections.append(election_id)
    
    return problematic_elections

def save_validation_report(validation_results, output_dir):
    """
    Save validation results to a report file.
    
    Args:
        validation_results: Validation results dictionary
        output_dir: Directory to save the report
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_path / f"validation_report_{timestamp}.txt"
    
    with open(report_path, 'w') as f:
        f.write("RCV Pipeline - Election Data Validation Report\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Validation Date: {validation_results['timestamp']}\n")
        f.write(f"Overall Score: {validation_results['overall_score']:.1f}/100\n\n")
        
        f.write(f"Data Summary:\n")
        f.write(f"  Total Elections: {validation_results['total_elections']}\n")
        f.write(f"  Total Candidate Records: {validation_results['total_candidates']}\n")
        f.write(f"  Total Round Records: {validation_results['total_rounds']}\n\n")
        
        f.write("Validation Results:\n")
        f.write("-" * 20 + "\n")
        
        for rule_name, rule_result in validation_results["validation_rules"].items():
            f.write(f"\n{rule_result['rule_name']}:\n")
            f.write(f"  Status: {'✓ PASSED' if rule_result['passed'] else '✗ FAILED'}\n")
            f.write(f"  Score: {rule_result['score']}/100\n")
            
            if rule_result["issues"]:
                f.write(f"  Issues:\n")
                for issue in rule_result["issues"]:
                    f.write(f"    - {issue}\n")
        
        if validation_results["problematic_elections"]:
            f.write(f"\nProblematic Elections:\n")
            f.write("-" * 20 + "\n")
            for election_id in validation_results["problematic_elections"]:
                f.write(f"  - {election_id}\n")
    
    print(f"Validation report saved to: {report_path}")
    return report_path
