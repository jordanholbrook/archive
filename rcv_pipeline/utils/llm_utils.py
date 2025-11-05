"""
Simple LLM utilities for election data extraction.
"""
import json
import time
import os
from pathlib import Path
import requests
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_prompt(file_content):
    """
    Generate the prompt for LLM extraction.
    
    Args:
        file_content: Text content to process
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""
    Parse the following election results data into a structured JSON format.
    Ensure the output conforms strictly to the schema and instructions below.
    
    Ranked Choice Voting Election Results - Structured JSON Format
    ===============================================================
    
    Target JSON Schema:
    -------------------
    
    {{
      "election_id": "State_Year_ElectionType_Juris_District_Office[_Party]",
      "year": INT,
      "state": "XX",
      "office": "Office Name",
      "dist": "District Number or 'At_Large'",
      "juris": "Jurisdiction Name",
      "type": "Election Type (general, primary, special)",
      "prm_party": "Primary Party or null",
      "n_cands": INT,
      "n_rounds": INT,
      "date": "MM/DD/YYYY",
      "level": "country, state, federal, municipal, school_board",
      "candidates": [
        {{
          "candidate_id": "FirstName_LastName_State_Year",
          "name": "Candidate Name",
          "rounds": [
            {{
              "round_number": INT,
              "votes": INT,
              "percentage": FLOAT,
              "transfer": null or "+/-INT"
            }},
            ...
          ]
        }},
        ...
      ],
      "rounds": [
        {{
          "round_number": INT,
          "total_votes": INT,
          "blanks": INT,
          "exhausted": INT,
          "overvotes": INT
        }},
        ...
      ]
    }}
    
    Input data:
    -----------
    {file_content}
    """
    return prompt

def clean_json_string(json_string):
    """
    Clean up the JSON string from LLM response.
    
    Args:
        json_string: Raw JSON string from LLM
        
    Returns:
        Cleaned JSON string
    """
    if not json_string:
        return ""
    
    # Remove specific prefixes (e.g., '''python, '''json)
    json_string = json_string.lstrip("```python").lstrip("```json").strip()
    # Remove trailing ''' marker
    json_string = json_string.rstrip("```").strip()
    return json_string

def call_openai_api(prompt, api_key=None, max_retries=3):
    """
    Call OpenAI API to extract election data.
    
    Args:
        prompt: The prompt to send
        api_key: OpenAI API key (defaults to environment variable)
        max_retries: Maximum number of retry attempts
        
    Returns:
        API response content or None if failed
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "Respond only with a structured Python dictionary based on the user's input."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 15000
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"API request failed (attempt {attempt + 1}): {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    print(f"Final error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"API call error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            else:
                return None
    
    return None

def extract_election_data_from_text(text_content, api_key=None):
    """
    Extract election data from text using LLM.
    
    Args:
        text_content: Text content to process
        api_key: OpenAI API key
        
    Returns:
        Extracted election data dictionary or None if failed
    """
    try:
        # Generate prompt
        prompt = generate_prompt(text_content)
        
        # Call API
        response = call_openai_api(prompt, api_key)
        
        if not response:
            return None
        
        # Clean and parse response
        cleaned_response = clean_json_string(response)
        election_data = json.loads(cleaned_response)
        
        return election_data
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

def process_text_files_for_elections(input_dir, output_dir, api_key=None, batch_size=5):
    """
    Process all text files in a directory to extract election data.
    
    Args:
        input_dir: Directory containing text files
        output_dir: Directory to save CSV files
        api_key: OpenAI API key
        batch_size: Number of files to process before saving
        
    Returns:
        Dictionary with processing statistics
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all text files
    text_files = list(input_path.glob("*.txt"))
    
    if not text_files:
        print(f"No text files found in {input_dir}")
        return {"processed": 0, "successful": 0, "failed": 0}
    
    print(f"Found {len(text_files)} text files to process")
    
    # Initialize data storage
    all_elections = []
    all_candidates = []
    all_rounds = []
    
    stats = {"processed": 0, "successful": 0, "failed": 0, "api_calls": 0}
    
    # Process files
    for i, text_file in enumerate(tqdm(text_files, desc="Processing files")):
        print(f"\nProcessing: {text_file.name}")
        
        try:
            # Read file content
            with open(text_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            if not file_content.strip():
                print(f"  ✗ Empty file content")
                stats["failed"] += 1
                continue
            
            # Extract election data
            election_data = extract_election_data_from_text(file_content, api_key)
            stats["api_calls"] += 1
            
            if election_data:
                # Store the data
                _store_election_data(election_data, text_file.name, all_elections, all_candidates, all_rounds)
                print(f"  ✓ Successfully extracted data")
                stats["successful"] += 1
            else:
                print(f"  ✗ Failed to extract data")
                stats["failed"] += 1
            
            stats["processed"] += 1
            
            # Save batch if we have enough data or this is the last file
            if (i + 1) % batch_size == 0 or i == len(text_files) - 1:
                if all_elections or all_candidates or all_rounds:
                    _save_batch_data(all_elections, all_candidates, all_rounds, output_path, i)
                    # Clear batch data
                    all_elections.clear()
                    all_candidates.clear()
                    all_rounds.clear()
            
        except Exception as e:
            print(f"  ✗ Error processing {text_file.name}: {e}")
            stats["failed"] += 1
            stats["processed"] += 1
    
    print(f"\nProcessing complete: {stats['successful']} successful, {stats['failed']} failed")
    return stats

def _store_election_data(election_data, filename, all_elections, all_candidates, all_rounds):
    """
    Store extracted election data in the appropriate lists.
    
    Args:
        election_data: Extracted election data
        filename: Source filename
        all_elections: List to store election data
        all_candidates: List to store candidate data
        all_rounds: List to store round data
    """
    # Store election metadata
    election_row = {
        "election_id": election_data["election_id"],
        "year": election_data["year"],
        "state": election_data["state"],
        "office": election_data["office"],
        "dist": election_data.get("dist", "At_Large"),
        "juris": election_data["juris"],
        "election_type": election_data["type"],
        "prm_party": election_data.get("prm_party"),
        "n_cands": election_data["n_cands"],
        "n_rounds": election_data["n_rounds"],
        "date": election_data["date"],
        "level": election_data["level"],
        "source_file": filename
    }
    all_elections.append(election_row)
    
    # Store candidate data
    for candidate in election_data["candidates"]:
        for round_info in candidate["rounds"]:
            candidate_row = {
                "election_id": election_data["election_id"],
                "candidate_id": candidate["candidate_id"],
                "name": candidate["name"],
                "round": round_info["round_number"],
                "votes": round_info["votes"],
                "percentage": round_info["percentage"],
                "transfer": round_info["transfer"],
                "source_file": filename
            }
            all_candidates.append(candidate_row)
    
    # Store round data
    for round_info in election_data["rounds"]:
        round_row = {
            "election_id": election_data["election_id"],
            "round": round_info["round_number"],
            "total_votes": round_info["total_votes"],
            "exhausted": round_info.get("exhausted", 0),
            "overvotes": round_info.get("overvotes", 0),
            "source_file": filename
        }
        all_rounds.append(round_row)

def _save_batch_data(all_elections, all_candidates, all_rounds, output_path, batch_num):
    """
    Save a batch of extracted data to CSV files.
    
    Args:
        all_elections: List of election data
        all_candidates: List of candidate data
        all_rounds: List of round data
        output_path: Output directory path
        batch_num: Batch number for filename
    """
    import pandas as pd
    
    try:
        # Create DataFrames
        elections_df = pd.DataFrame(all_elections)
        candidates_df = pd.DataFrame(all_candidates)
        rounds_df = pd.DataFrame(all_rounds)
        
        # Save to CSV files
        elections_path = output_path / f"Elections_DF_batch_{batch_num}.csv"
        candidates_path = output_path / f"Candidates_DF_batch_{batch_num}.csv"
        rounds_path = output_path / f"Rounds_DF_batch_{batch_num}.csv"
        
        elections_df.to_csv(elections_path, index=False)
        candidates_df.to_csv(candidates_path, index=False)
        rounds_df.to_csv(rounds_path, index=False)
        
        print(f"  ✓ Saved batch {batch_num} data")
        
    except Exception as e:
        print(f"  ✗ Error saving batch {batch_num}: {e}")
