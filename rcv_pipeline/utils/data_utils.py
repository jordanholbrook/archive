"""
Simple data utilities for post-processing election data.
"""
import pandas as pd
import re
from pathlib import Path

def load_election_data(input_dir):
    """
    Load election data from CSV files.
    
    Args:
        input_dir: Directory containing CSV files
        
    Returns:
        Tuple of (elections_df, candidates_df, rounds_df)
    """
    input_path = Path(input_dir)
    
    # Look for CSV files (handle both batch files and single files)
    elections_files = list(input_path.glob("Elections_DF*.csv"))
    candidates_files = list(input_path.glob("Candidates_DF*.csv"))
    rounds_files = list(input_path.glob("Rounds_DF*.csv"))
    
    if not elections_files or not candidates_files or not rounds_files:
        raise FileNotFoundError(f"Missing required CSV files in {input_dir}")
    
    # Load and combine all files
    elections_dfs = []
    candidates_dfs = []
    rounds_dfs = []
    
    for file in elections_files:
        df = pd.read_csv(file)
        elections_dfs.append(df)
    
    for file in candidates_files:
        df = pd.read_csv(file)
        candidates_dfs.append(df)
    
    for file in rounds_files:
        df = pd.read_csv(file)
        rounds_dfs.append(df)
    
    # Combine all DataFrames
    elections_df = pd.concat(elections_dfs, ignore_index=True)
    candidates_df = pd.concat(candidates_dfs, ignore_index=True)
    rounds_df = pd.concat(rounds_dfs, ignore_index=True)
    
    print(f"Loaded data: {len(elections_df)} elections, {len(candidates_df)} candidate records, {len(rounds_df)} round records")
    
    return elections_df, candidates_df, rounds_df

def compute_transfer_from_votes(
    candidates_df: pd.DataFrame,
    *,
    colname: str = "transfer_calc",
    as_string: bool = False,
    round_col: str = "round",
    votes_col: str = "votes",
    election_col: str = "election_id",
    cand_col: str = "candidate_id",
) -> pd.DataFrame:
    """
    Compute per-candidate, per-round transfer as the vote delta from the previous round.
    Round 1 is explicitly set to 0 (no transfers happen in the first round).
    
    This function builds a complete candidate×round panel for each election and fills
    missing post-elimination rounds with votes=0 before computing transfers.

    Parameters
    ----------
    candidates_df : DataFrame with columns:
        ['election_id','candidate_id','name','round','votes','percentage','transfer']
    colname : name of the new transfer column to create (default 'transfer_calc')
    as_string : if True, outputs '+INT'/'-INT' strings; round 1 = "0"
    round_col, votes_col, election_col, cand_col : column names (override if different)

    Returns
    -------
    DataFrame with a new column `colname`.
    """
    df = candidates_df.copy()
    
    gcols = [election_col]
    # Build full candidate×round grid per election
    max_rounds = df.groupby(election_col)[round_col].max()
    grids = []
    for eid, rmax in max_rounds.items():
        cands = df.loc[df[election_col]==eid, cand_col].unique()
        grid = (
            pd.MultiIndex.from_product([[eid], cands, range(1, rmax+1)],
                                       names=[election_col, cand_col, round_col])
              .to_frame(index=False)
        )
        grids.append(grid)
    full = pd.concat(grids, ignore_index=True)

    # Join original data; fill missing post-elimination rounds with votes=0
    cols_to_keep = [election_col, cand_col, round_col, votes_col, "name", "percentage"]
    merged = full.merge(df[cols_to_keep].drop_duplicates([election_col, cand_col, round_col]),
                        on=[election_col, cand_col, round_col], how="left")
    # Fill name per candidate
    merged["name"] = merged.groupby([election_col, cand_col])["name"].ffill().bfill()
    # Fill percentage per candidate (use forward fill for missing rounds)
    if "percentage" in merged.columns:
        merged["percentage"] = merged.groupby([election_col, cand_col])["percentage"].ffill().bfill()
    # Fill votes missing -> 0
    merged[votes_col] = pd.to_numeric(merged[votes_col], errors="coerce").fillna(0).astype(int)

    # Stable sort then diff
    merged.sort_values([election_col, cand_col, round_col], inplace=True, kind="mergesort")
    merged[colname] = (merged.groupby([election_col, cand_col])[votes_col]
                             .diff()
                             .fillna(0)
                             .astype(int))
    
    # Handle string output if requested
    if as_string:
        merged[colname] = merged[colname].apply(
            lambda x: f"+{x}" if x > 0 else (f"{x}" if x < 0 else "0")
        )
    
    return merged

def explain_transfer_computation(candidates_df, election_id=None):
    """
    Explain how transfer values are computed for a specific election or all elections.
    
    Args:
        candidates_df: Candidates DataFrame with transfer_calc column
        election_id: Specific election to explain (if None, shows first election)
    """
    if "transfer_calc" not in candidates_df.columns:
        print("No computed transfer values found. Run post-processing first.")
        return
    
    if election_id is None:
        election_id = candidates_df["election_id"].iloc[0]
    
    election_data = candidates_df[candidates_df["election_id"] == election_id].copy()
    election_data = election_data.sort_values(["candidate_id", "round"])
    
    print(f"Transfer Computation Explanation for Election: {election_id}")
    print("=" * 60)
    print("Transfer = Current Round Votes - Previous Round Votes")
    print("Round 1 transfers are always 0 (no previous round)")
    print()
    
    # Show example for each candidate
    for candidate_id in election_data["candidate_id"].unique():
        candidate_data = election_data[election_data["candidate_id"] == candidate_id].sort_values("round")
        candidate_name = candidate_data["name"].iloc[0]
        
        print(f"Candidate: {candidate_name} ({candidate_id})")
        print("-" * 40)
        
        for i, (_, row) in enumerate(candidate_data.iterrows()):
            round_num = row["round"]
            votes = row["votes"]
            transfer = row["transfer_calc"]
            
            if round_num == 1:
                print(f"  Round {round_num}: {votes} votes → Transfer: {transfer} (no previous round)")
            else:
                prev_votes = candidate_data[candidate_data["round"] == round_num - 1]["votes"].iloc[0]
                print(f"  Round {round_num}: {votes} votes → Transfer: {transfer} ({votes} - {prev_votes})")
        
        print()

def clean_and_standardize_data(elections_df, candidates_df, rounds_df):
    """
    Clean and standardize election data.
    
    Args:
        elections_df: Elections DataFrame
        candidates_df: Candidates DataFrame
        rounds_df: Rounds DataFrame
        
    Returns:
        Tuple of cleaned DataFrames
    """
    print("Cleaning and standardizing data...")
    
    # Clean elections data
    elections_clean = _clean_elections(elections_df)
    
    # Clean candidates data
    candidates_clean = _clean_candidates(candidates_df)
    
    # Clean rounds data
    rounds_clean = _clean_rounds(rounds_df)
    
    # Standardize election IDs
    elections_clean, candidates_clean, rounds_clean = _standardize_election_ids(
        elections_clean, candidates_clean, rounds_clean
    )
    
    # Compute transfer values directly from vote counts
    print("Computing transfer values from vote counts...")
    candidates_clean = compute_transfer_from_votes(
        candidates_clean, 
        colname="transfer_calc", 
        as_string=False
    )
    
    # Add candidate status
    candidates_clean = _add_candidate_status(candidates_clean)
    
    print("Data cleaning and standardization complete")
    
    return elections_clean, candidates_clean, rounds_clean

def _clean_elections(df):
    """Clean elections DataFrame."""
    df = df.copy()
    
    # Ensure numeric fields are properly typed
    numeric_fields = ["year", "n_cands", "n_rounds"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    
    # Clean date field
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Remove rows with missing critical data
    critical_fields = ["election_id", "state", "office"]
    initial_count = len(df)
    df = df.dropna(subset=critical_fields)
    
    if len(df) < initial_count:
        print(f"Removed {initial_count - len(df)} elections with missing critical data")
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["election_id"])
    
    return df

def _clean_candidates(df):
    """Clean candidates DataFrame."""
    df = df.copy()
    
    # Ensure numeric fields are properly typed
    numeric_fields = ["round", "votes", "percentage"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    
    # Clean transfer field (keep original for comparison)
    if "transfer" in df.columns:
        df["transfer_original"] = _clean_transfer_field(df["transfer"])
    
    # Remove rows with missing critical data
    critical_fields = ["election_id", "candidate_id", "round", "votes"]
    initial_count = len(df)
    df = df.dropna(subset=critical_fields)
    
    if len(df) < initial_count:
        print(f"Removed {initial_count - len(df)} candidate records with missing critical data")
    
    return df

def _clean_rounds(df):
    """Clean rounds DataFrame."""
    df = df.copy()
    
    # Ensure numeric fields are properly typed
    numeric_fields = ["round", "total_votes", "exhausted", "overvotes"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0)
    
    # Remove rows with missing critical data
    critical_fields = ["election_id", "round", "total_votes"]
    initial_count = len(df)
    df = df.dropna(subset=critical_fields)
    
    if len(df) < initial_count:
        print(f"Removed {initial_count - len(df)} round records with missing critical data")
    
    return df

def _clean_transfer_field(transfer_series):
    """Clean transfer field by converting to numeric values."""
    def convert_transfer(value):
        if pd.isna(value) or value == '' or value is None:
            return 0
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            transfer_str = str(value).strip()
            if transfer_str == '':
                return 0
            if transfer_str.startswith('+'):
                try:
                    return int(transfer_str[1:])
                except ValueError:
                    return 0
            elif transfer_str.startswith('-'):
                try:
                    return int(transfer_str)
                except ValueError:
                    return 0
            else:
                try:
                    return int(transfer_str)
                except ValueError:
                    return 0
        else:
            return 0
    
    return transfer_series.apply(convert_transfer)

def _standardize_election_ids(elections_df, candidates_df, rounds_df):
    """Standardize election IDs across all DataFrames."""
    print("Standardizing election IDs...")
    
    # Create standardized election IDs
    elections_df = elections_df.copy()
    elections_df["election_id_std"] = elections_df.apply(_create_standard_election_id, axis=1)
    
    # Create mapping from old to new IDs
    id_mapping = dict(zip(elections_df["election_id"], elections_df["election_id_std"]))
    
    # Apply mapping to all DataFrames
    candidates_df["election_id"] = candidates_df["election_id"].map(id_mapping)
    rounds_df["election_id"] = rounds_df["election_id"].map(id_mapping)
    
    # Update elections DataFrame
    elections_df["election_id"] = elections_df["election_id_std"]
    elections_df = elections_df.drop(columns=["election_id_std"])
    
    return elections_df, candidates_df, rounds_df

def _create_standard_election_id(row):
    """Create a standardized election ID."""
    office_map = {
        "U.S. House": "US_House",
        "U.S. Senator": "US_Senate",
        "Senate": "State_Senate",
        "House": "State_House",
        "City Council": "Council",
        "Council Member": "Council",
        "Mayor": "Mayor",
        "Governor": "Governor",
        "District Attorney": "DistrictAttorney",
        "School Board": "SchoolBoard",
        "Board of Education": "BoardOfEducation"
    }
    
    type_abbr_map = {"general": "G", "primary": "P", "special": "S"}
    party_abbr_map = {"Democratic": "DEM", "Republican": "REP"}
    
    # Clean office name
    office = str(row["office"]).strip()
    office_std = office_map.get(office, office.replace(" ", ""))
    
    # Clean jurisdiction
    juris = str(row["juris"]).strip()
    juris_std = re.sub(r'[^\w\s]', '', juris).replace(" ", "").title()
    
    # Clean district
    dist = str(row["dist"]).strip()
    if dist.lower() == "at_large":
        dist_std = "At_Large"
    else:
        try:
            dist_std = str(int(dist)).zfill(2)
        except:
            dist_std = str(dist).zfill(2)
    
    # Create standardized ID
    type_abbr = type_abbr_map.get(str(row["election_type"]).lower(), "X")
    
    parts = [str(row["state"]), str(row["year"]), type_abbr, juris_std, dist_std, office_std]
    
    if str(row["election_type"]).lower() == "primary":
        party = row.get("prm_party")
        if pd.notnull(party):
            party_clean = str(party).strip().title()
            parts.append(party_abbr_map.get(party_clean, party_clean[:3].upper()))
    
    return "_".join(parts)

def _add_candidate_status(df):
    """Add candidate status (Elected, Eliminated, Continuing) to candidates DataFrame."""
    print("Adding candidate status...")
    
    df = df.copy()
    
    # Initialize status column
    df['status'] = 'Continuing'
    
    # Process each election separately to avoid column dropping issues
    for election_id in df['election_id'].unique():
        election_mask = df['election_id'] == election_id
        election_df = df[election_mask].copy()
        
        if len(election_df) == 0:
            continue
            
        final_round = election_df['round'].max()
        
        # Identify winner: candidate_id with highest votes in final round
        final_round_mask = election_df['round'] == final_round
        final_round_df = election_df[final_round_mask]
        
        if len(final_round_df) > 0:
            max_votes = final_round_df['votes'].max()
            winner_ids = final_round_df[final_round_df['votes'] == max_votes]['candidate_id'].tolist()
            
            # Set status for final round
            final_round_indices = df[election_mask & (df['round'] == final_round)].index
            for idx in final_round_indices:
                if df.loc[idx, 'candidate_id'] in winner_ids:
                    df.loc[idx, 'status'] = 'Elected'
                else:
                    df.loc[idx, 'status'] = 'Eliminated'
            
            # Set status for earlier rounds
            earlier_rounds_indices = df[election_mask & (df['round'] < final_round)].index
            for idx in earlier_rounds_indices:
                if df.loc[idx, 'votes'] > 0:
                    df.loc[idx, 'status'] = 'Continuing'
                else:
                    df.loc[idx, 'status'] = 'Eliminated'
    
    return df

def save_cleaned_data(elections_df, candidates_df, rounds_df, output_dir):
    """
    Save cleaned data to CSV files.
    
    Args:
        elections_df: Cleaned elections DataFrame
        candidates_df: Cleaned candidates DataFrame
        rounds_df: Cleaned rounds DataFrame
        output_dir: Directory to save cleaned files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save cleaned data
    elections_path = output_path / "Elections_DF_cleaned.csv"
    candidates_path = output_path / "Candidates_DF_cleaned.csv"
    rounds_path = output_path / "Rounds_DF_cleaned.csv"
    
    elections_df.to_csv(elections_path, index=False)
    candidates_df.to_csv(candidates_path, index=False)
    rounds_df.to_csv(rounds_path, index=False)
    
    print(f"Cleaned data saved to {output_dir}")
    print(f"  Elections: {elections_path}")
    print(f"  Candidates: {candidates_path}")
    print(f"  Rounds: {rounds_path}")
