UFC Scraper Project

Overview
The UFC Scraper project is a comprehensive data collection tool designed to scrape and compile detailed statistics from various UFC-related sources. The project collects data about fighters, fights, events, and associated statistics, storing them in clean and structured datasets. These datasets are then prepared for machine learning (ML) models to perform advanced analyses, such as fight predictions.

Features
Primary Scrapers:
fight_scraper: Scrapes detailed fight results, fight statistics, and event data from ufcstats.com.
fighter_scraper: Collects fighter details and tale-of-the-tape data.

Backup Scrapers:
scrape_ufc_athletes: Retrieves fighter details and tale-of-the-tape data from UFC Athletes.
scrape_ufc_events: Retrieves past event details from UFC Events.
scrape_sherdog_events: Fetches recent fight and event data from Sherdog.
scrape_mma_decisions: Provides additional fight details, such as judges' scores and decisions.

Centralized Cleaning Workflow:
clean_and_fill_data.ipynb: Identifies and fills missing data using backup scrapers, consolidating clean datasets for further use.

Folder Structure

UFC-Scraper/
├── scrapers/
│   ├── fight_scraper.py
│   ├── fighter_scraper.py
│   ├── scrape_ufc_athletes.py
│   ├── scrape_ufc_events.py
│   ├── scrape_sherdog_events.py
│   └── scrape_mma_decisions.py
├── datasets/
│   ├── raw/
│   │   ├── ufc_fight_results.csv
│   │   ├── ufc_fight_stats.csv
│   │   ├── ufc_fighter_details.csv
│   │   └── ufc_fighter_tott.csv
│   ├── cleaned/
│       ├── ufc_fight_results_cleaned.csv
│       ├── ufc_fight_stats_cleaned.csv
│       ├── ufc_fighter_details_cleaned.csv
│       └── ufc_fighter_tott_cleaned.csv
├── notebooks/
│   ├── clean_and_fill_data.ipynb
│   └── analysis_and_modeling.ipynb
├── config/
│   └── scrape_ufc_stats_config.yaml
└── README.md

Workflow
1. Scrape Data
Run the primary scrapers to collect initial data:

Fight Data:
python scrapers/fight_scraper.py

Fighter Data:
python scrapers/fighter_scraper.py

Output CSV files are stored in the datasets/raw/ folder.

2. Analyze Missing Data
Load the raw datasets and analyze missing values using clean_and_fill_data.ipynb.

Check missing values:

import pandas as pd

fight_results_df = pd.read_csv('datasets/raw/ufc_fight_results.csv')
print(fight_results_df.isnull().sum())

3. Fill Missing Data Using Backup Scrapers
Use backup scrapers to fill in missing values:

Fighter details: scrape_ufc_athletes
Event details: scrape_ufc_events
Fight details: scrape_mma_decisions
Recent fight data: scrape_sherdog_events

4. Clean and Consolidate Data
Use clean_and_fill_data.ipynb to integrate missing data and finalize cleaned datasets:

jupyter notebook notebooks/clean_and_fill_data.ipynb

Output CSVs are stored in the datasets/cleaned/ folder.

5. Model Preparation
Use analysis_and_modeling.ipynb to prepare data for ML modeling and analysis.
Key Components:

Fight Scraper
Purpose: Scrapes detailed fight statistics and event data from ufcstats.com.
Output Files:
ufc_fight_results.csv: Fight results, referee, method, and other metadata.
ufc_fight_stats.csv: Per-round statistics for each fight.

Fighter Scraper
Purpose: Collects fighter details and tale-of-the-tape data.
Output Files:
ufc_fighter_details.csv: Names, nicknames, and other details.
ufc_fighter_tott.csv: Height, weight, reach, stance, and date of birth.

Backup Scrapers
Purpose: Fills in missing or incomplete data from secondary sources.
Scripts:
scrape_ufc_athletes.py: Fills missing fighter details and tale of the tape.
scrape_ufc_events.py: Fills event-level details.
scrape_sherdog_events.py: Fills recent fight and event data.
scrape_mma_decisions.py: Fills fight-level details (judges' decisions, deductions, etc.).

Cleaning Notebook
Purpose: Centralizes data cleaning and filling of missing values.
File: clean_and_fill_data.ipynb
Functions:
Identifies missing values.
Calls appropriate backup scrapers.
Consolidates and saves cleaned datasets.

Usage Notes
Rate-Limiting:
Primary scrapers include delay and retry logic to handle rate-limiting.
If rate-limited, use backup scrapers to fill missing data.

Error Handling:
All scrapers log errors and skip problematic rows without stopping execution.

Data Validation:
Use clean_and_fill_data.ipynb to verify and finalize datasets before modeling.

Future Improvements
Add asynchronous capabilities to backup scrapers for faster performance.
Implement proxy rotation to bypass rate-limiting.
Enhance error logging and reporting for easier debugging.
