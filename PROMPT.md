# LLM Extraction Prompt

This document describes the prompt used to extract structured election data from raw text, and how it fits into the pipeline.

---

## What the Prompt Does

Step 2 of the rcv pipeline code files, (`2_extract_election_data.py`) sends each raw text file — converted from a PDF or supplied directly — to OpenAI's `gpt-4o` model. The prompt instructs the model to read unstructured election result text and return a single, strictly-formatted JSON object conforming to the schema below.

The model is given no latitude to invent data; it is expected to transcribe what is present in the source document and leave fields `null` or `0` when information is absent.

---

## How the Prompt Is Constructed

The prompt is assembled by `generate_prompt()` in [utils/llm_utils.py](utils/llm_utils.py). It is a plain f-string that embeds the raw file content at the bottom:

```python
def generate_prompt(file_content):
    prompt = f"""
    Parse the following election results data into a structured JSON format.
    Ensure the output conforms strictly to the schema and instructions below.
    ...
    Input data:
    -----------
    {file_content}
    """
    return prompt
```

The filled prompt is then passed to `call_openai_api()`, which sends it as the **user message** alongside a fixed **system message**:

```
"Respond only with a structured Python dictionary based on the user's input."
```

API call parameters:

| Parameter     | Value   |
|---------------|---------|
| Model         | `gpt-4o` |
| Temperature   | `0.1`   |
| Max tokens    | `15 000` |
| Max retries   | `3`     |

Low temperature is intentional — the task is transcription, not generation, so deterministic output is preferred.

---

## Call Chain

```
process_text_files_for_elections()   # iterates over .txt files
  └─ extract_election_data_from_text()
       ├─ generate_prompt(file_content)   # builds the prompt
       ├─ call_openai_api(prompt)         # sends to GPT-4o, retries on failure
       └─ clean_json_string(response)     # strips markdown fences (``` json ... ```)
            └─ json.loads(...)            # parses to dict
```

---

## The Full Prompt Template

The text below is the exact prompt sent to the model, with `{Insert Raw Election Data for Extraction}` as a placeholder for the raw election text.

```
Parse the following election results data into a structured JSON format.
Ensure the output conforms strictly to the schema and instructions below.

Ranked Choice Voting Election Results - Structured JSON Format
===============================================================

Target JSON Schema:
-------------------

{
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
    {
      "candidate_id": "FirstName_LastName_State_Year",
      "name": "Candidate Name",
      "rounds": [
        {
          "round_number": INT,
          "votes": INT,
          "percentage": FLOAT,
          "transfer": null or "+/-INT"
        },
        ...
      ]
    },
    ...
  ],
  "rounds": [
    {
      "round_number": INT,
      "total_votes": INT,
      "blanks": INT,
      "exhausted": INT,
      "overvotes": INT
    },
    ...
  ]
}

Input data:
-----------
{file content}
```

---

## Schema Field Reference

### Election-level fields

| Field        | Type   | Description |
|--------------|--------|-------------|
| `election_id` | string | Composite key: `State_Year_ElectionType_Juris_District_Office[_Party]`. Example: `ME_2022_general_Portland_At_Large_Mayor` |
| `year`       | int    | Four-digit election year |
| `state`      | string | Two-letter state abbreviation (e.g. `ME`, `AK`) |
| `office`     | string | Name of the office being contested |
| `dist`       | string | District number, or `"At_Large"` if no district applies |
| `juris`      | string | Jurisdiction name (city, county, etc.) |
| `type`       | string | One of `general`, `primary`, or `special` |
| `prm_party`  | string or null | Party name for primary elections; `null` for general/special |
| `n_cands`    | int    | Total number of candidates on the ballot |
| `n_rounds`   | int    | Total number of rounds in the tabulation |
| `date`       | string | Election date in `MM/DD/YYYY` format |
| `level`      | string | One of `country`, `state`, `federal`, `municipal`, `school_board` |

### Candidate-level fields (nested under `candidates`)

| Field          | Type   | Description |
|----------------|--------|-------------|
| `candidate_id` | string | `FirstName_LastName_State_Year`. Example: `John_Smith_ME_2022` |
| `name`         | string | Full candidate name as it appears in the source |
| `rounds`       | array  | One entry per round the candidate appeared in |

#### Per-round candidate fields

| Field         | Type          | Description |
|---------------|---------------|-------------|
| `round_number` | int          | Round index starting at 1 |
| `votes`        | int          | Vote total for this candidate in this round |
| `percentage`   | float        | Share of active votes (0–100) |
| `transfer`     | null or string | Net votes received from eliminations, e.g. `"+312"` or `"-1024"`. `null` in round 1 or if not reported |

### Round-level fields (nested under `rounds`)

| Field         | Type | Description |
|---------------|------|-------------|
| `round_number` | int | Round index starting at 1 |
| `total_votes`  | int | Total active votes counted in this round |
| `blanks`       | int | Blank ballots (0 if not reported) |
| `exhausted`    | int | Exhausted ballots — ballots that ran out of ranked choices |
| `overvotes`    | int | Overvotes (0 if not reported) |

---

## Post-Processing Note

Transfer values extracted by the LLM are stored as `transfer_original` after post-processing. Step 3 (`3_post_process.py`) also independently **computes** transfers from successive round vote counts (`transfer_calc = current_votes − previous_votes`). Validation in Step 4 compares both values to flag discrepancies and verify mathematical consistency.
