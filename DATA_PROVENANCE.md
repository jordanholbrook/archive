# Data Sources and Provenance: ARCHIVE Database

The ARCHIVE database aggregates ranked-choice voting (RCV) election results from 514 American elections (2004--2024). All raw source data and metadata used to build the database are stored in this repository under `rcv_pipeline/data/source_data/`.

## Source Data Inputs

### Raw Tabulated Results

The `rcv_pipeline/data/source_data/` directory contains the raw election results organized by jurisdiction. These are the input files (primarily `.txt` and `.rtf`) that were manually collected from official election websites and then processed through the pipeline.

```
rcv_pipeline/data/source_data/
├── Alaska/              # 119 files
├── Berkeley/            #  30 files
├── Burlington/          #   2 files
├── Colorado/            #   1 file
├── Corvallis_OR/        #   2 files
├── Maine/               #  21 files
├── Minneapolis/         #  96 files
├── Minnesota/           #   4 files
├── Minnetoka/           #   3 files
├── NYC/                 #  72 files
├── New_Mexico/          #   6 files
├── Oakland/             #  59 files
├── Pierce_County_WA/    #   9 files
├── Portland/            #   2 files
├── SanFrancisco/        #  83 files
├── San_Leandro/         #  21 files
├── Takoma_Park_MD/      #   6 files
├── Utah/                #  10 files
└── Source_Metadata.csv  # Source URL metadata (see below)
```

### Source URL Metadata

The file `rcv_pipeline/data/source_data/Source_Metadata.csv` contains the primary source URLs for all elections in the database. Each row records the state, year, election type, office, jurisdiction, district, and the URL from which the raw data was collected during the 2024--2025 data collection period. The file contains 844 URL entries across all jurisdictions.

| Column | Description |
|:-------|:------------|
| `state` | State abbreviation |
| `year` | Election year |
| `type` | Election type (e.g., general, primary) |
| `office` | Office contested |
| `juris` | Jurisdiction name |
| `dist` | District identifier |
| `url` | Source URL for the election data |

## Persistence and Reproducibility Disclaimer

The URLs provided in `Source_Metadata.csv` were active and verified at the time of data collection. However, users should note:

1. **URL Volatility:** Jurisdictions frequently restructure their web portals or archive past results to new subdirectories. Consequently, some original links may become inactive over time.
2. **Aggregated Reporting:** Several jurisdictions report multiple race results on a single landing page; in these cases, the landing page is the recorded source for all associated elections in the database.
3. **Archival Stability:** To ensure long-term reproducibility, the raw tabulated results stored in `rcv_pipeline/data/source_data/` remain the primary source data reference, independent of external URL availability.

## Primary Jurisdictional Sources

| Jurisdiction | Primary Data Portal URL |
| :--- | :--- |
| **Alaska** | [https://www.elections.alaska.gov/election-results/e/](https://www.elections.alaska.gov/election-results/e/) |
| **Maine** | [https://www.maine.gov/sos/elections-voting/election-results-data](https://www.maine.gov/sos/elections-voting/election-results-data) |
| **New York City, NY** | [https://www.vote.nyc/page/election-results-summary](https://www.vote.nyc/page/election-results-summary) |
| **San Francisco, CA** | [https://www.sf.gov/election-results](https://www.sf.gov/election-results) |
| **Alameda County, CA** | [https://acvote.alamedacountyca.gov/election-information/archived-elections](https://acvote.alamedacountyca.gov/election-information/archived-elections) |
| **Minneapolis, MN** | [https://vote.minneapolismn.gov/ranked-choice-voting/](https://vote.minneapolismn.gov/ranked-choice-voting/) |
| **St. Louis Park, MN** | [https://www.stlouisparkmn.gov/government/elections/ranked-choice-voting](https://www.stlouisparkmn.gov/government/elections/ranked-choice-voting) |
| **Santa Fe County, NM** | [https://www.santafecountynm.gov/clerk/community-outreach/live-election-results-rcv-tabulation](https://www.santafecountynm.gov/clerk/community-outreach/live-election-results-rcv-tabulation) |
| **Boulder County, CO** | [https://electionresults.bouldercounty.gov/ElectionResults2023C/](https://electionresults.bouldercounty.gov/ElectionResults2023C/) |
| **Utah County, UT** | [https://vote.utahcounty.gov/results](https://vote.utahcounty.gov/results) |
| **Benton County, OR** | [https://re.bentoncountyor.gov/past-elections/](https://re.bentoncountyor.gov/past-elections/) |
| **Corvallis, OR** | [https://www.corvallisoregon.gov/cm/page/prior-city-elections](https://www.corvallisoregon.gov/cm/page/prior-city-elections) |
| **Washington (State)** | [https://results.votewa.gov/results/public/washington](https://results.votewa.gov/results/public/washington) |
| **Maryland (State)** | [https://elections.maryland.gov/index.html](https://elections.maryland.gov/index.html) |
