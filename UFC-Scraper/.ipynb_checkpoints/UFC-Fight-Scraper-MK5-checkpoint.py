#!/usr/bin/env python
# coding: utf-8

# In[1]:


pip install nest_asyncio


# In[1]:


#!/usr/bin/env python
# coding: utf-8

# imports
import pandas as pd
from tqdm.notebook import tqdm_notebook
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import scrape_ufc_stats_library as LIB
import yaml
import nest_asyncio
import time
import random
import os


# In[2]:


# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


# In[3]:


# Load configuration
config = yaml.safe_load(open('scrape_ufc_stats_config.yaml'))


# In[5]:


# Asynchronous get_soup replacement
async def get_soup_async(url, session, retries=3):
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return BeautifulSoup(html, 'html.parser')
                elif response.status == 429:  # Too Many Requests
                    print(f"Rate-limited on {url}. Retrying in {2 ** attempt} seconds...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            print(f"Error fetching URL: {url}, attempt {attempt + 1}")
    print(f"Failed to fetch URL after {retries} attempts: {url}")
    return None


# In[6]:


# Fetch multiple soups concurrently
async def fetch_all_soups(urls):
    connector = aiohttp.TCPConnector(limit=5)  # Limit simultaneous requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        soups = []
        for url in urls:
            soup = await get_soup_async(url, session)
            soups.append(soup)
            # Add a random delay between 1 and 3 seconds
            await asyncio.sleep(random.uniform(1, 3))
        return soups


# In[7]:


# Fallback mechanism for missing data
def use_backup_scraper(url, column_names):
    # Replace this with the backup scraper logic for the relevant data
    # For now, return a placeholder DataFrame
    backup_data = pd.DataFrame(columns=column_names)
    # Example: fetch data from Sherdog, UFC Athletes, or other sources
    backup_data.loc[0] = ["Backup Value"] * len(column_names)
    return backup_data


# In[8]:


# ## Parse Event Details
# Includes: Event, URL, Date, Location

# Define URL to parse
events_url = config['completed_events_all_url']

# Fetch and parse event details
soup = LIB.get_soup(events_url)
all_event_details_df = LIB.parse_event_details(soup)

# Load existing event details
existing_event_file = config['event_details_file_name']
if os.path.exists(existing_event_file):
    existing_event_details_df = pd.read_csv(existing_event_file)
    existing_event_urls = set(existing_event_details_df['URL'])
else:
    existing_event_urls = set()

# Filter for new events
all_event_details_df = all_event_details_df[~all_event_details_df['URL'].isin(existing_event_urls)]

# Save: Append new events to the top
if not all_event_details_df.empty:
    all_event_details_df = pd.concat([all_event_details_df, existing_event_details_df], ignore_index=True)
    all_event_details_df.to_csv(existing_event_file, index=False)

# Show updated event details
display(all_event_details_df)

# Extract the URLs of all events (use the correct DataFrame name)
list_of_events_urls = list(all_event_details_df['URL'])


# In[9]:


# Asynchronous parsing of fight details
async def parse_fight_details_async(event_urls):
    soups = await fetch_all_soups(event_urls)
    all_fight_details = pd.DataFrame(columns=config['fight_details_column_names'])

    for soup, url in zip(soups, event_urls):
        try:
            # Parse fight details with fallback for missing data
            fight_details_df = LIB.parse_fight_details(soup)
            if fight_details_df.empty or fight_details_df.isnull().values.any():
                print(f"Missing data for URL: {url}. Using backup scraper.")
                fight_details_df = use_backup_scraper(url, config['fight_details_column_names'])
            all_fight_details = pd.concat([all_fight_details, fight_details_df])
        except Exception as e:
            print(f"Error processing URL: {url}")
            print(f"Error: {e}")
            print(soup.prettify())  # Debug the HTML for this specific page
    return all_fight_details

# Execute async function for fight details
loop = asyncio.get_event_loop()
all_fight_details_df = loop.run_until_complete(parse_fight_details_async(list_of_events_urls))

# Load existing fight details
existing_fight_details_file = config['fight_details_file_name']
if os.path.exists(existing_fight_details_file):
    existing_fight_details_df = pd.read_csv(existing_fight_details_file)
    existing_fight_urls = set(existing_fight_details_df['URL'])
else:
    existing_fight_urls = set()

# Filter for new fights
all_fight_details_df = all_fight_details_df[~all_fight_details_df['URL'].isin(existing_fight_urls)]

# Save: Append new fights to the top
if not all_fight_details_df.empty:
    all_fight_details_df = pd.concat([all_fight_details_df, existing_fight_details_df], ignore_index=True)
    all_fight_details_df.to_csv(existing_fight_details_file, index=False)

# Show updated fight details
display(all_fight_details_df)


# In[10]:


# print(soup.prettify())


# In[ ]:


# ## Parse Fight Results and Stats
# Includes Fight Results and Fight Stats

# Define list of fight URLs to parse
list_of_fight_details_urls = list(all_fight_details_df['URL'])

# Asynchronous parsing of fight results and stats
async def parse_fight_results_and_stats_async(fight_urls):
    soups = await fetch_all_soups(fight_urls)
    all_fight_results = pd.DataFrame(columns=config['fight_results_column_names'])
    all_fight_stats = pd.DataFrame(columns=config['fight_stats_column_names'])

    for soup, url in zip(soups, fight_urls):
        try:
            # Parse fight results and stats with fallback for missing data
            fight_results_df, fight_stats_df = LIB.parse_organise_fight_results_and_stats(
                soup,
                url,
                config['fight_results_column_names'],
                config['totals_column_names'],
                config['significant_strikes_column_names']
            )
            if fight_results_df.empty or fight_results_df.isnull().values.any():
                print(f"Missing fight results for URL: {url}. Using backup scraper.")
                fight_results_df = use_backup_scraper(url, config['fight_results_column_names'])
            if fight_stats_df.empty or fight_stats_df.isnull().values.any():
                print(f"Missing fight stats for URL: {url}. Using backup scraper.")
                fight_stats_df = use_backup_scraper(url, config['fight_stats_column_names'])
            all_fight_results = pd.concat([all_fight_results, fight_results_df])
            all_fight_stats = pd.concat([all_fight_stats, fight_stats_df])
        except Exception as e:
            print(f"Error processing URL: {url}")
            print(f"Error: {e}")
            print(soup.prettify())  # Debug the HTML for this specific page
    return all_fight_results, all_fight_stats

# Execute async function for fight results and stats
all_fight_results_df, all_fight_stats_df = loop.run_until_complete(parse_fight_results_and_stats_async(list_of_fight_details_urls))


# In[5]:


# Show and save results
# Load existing fight results
existing_fight_results_file = config['fight_results_file_name']
if os.path.exists(existing_fight_results_file):
    existing_fight_results_df = pd.read_csv(existing_fight_results_file)
    existing_fight_results_urls = set(existing_fight_results_df['URL'])
else:
    existing_fight_results_urls = set()

# Filter for new fights
all_fight_results_df = all_fight_results_df[~all_fight_results_df['URL'].isin(existing_fight_results_urls)]

# Save: Append new fight results to the top
if not all_fight_results_df.empty:
    all_fight_results_df = pd.concat([all_fight_results_df, existing_fight_results_df], ignore_index=True)
    all_fight_results_df.to_csv(existing_fight_results_file, index=False)

# Show updated fight results
display(all_fight_results_df)

# Load existing fight stats
existing_fight_stats_file = config['fight_stats_file_name']
if os.path.exists(existing_fight_stats_file):
    existing_fight_stats_df = pd.read_csv(existing_fight_stats_file)
else:
    existing_fight_stats_df = pd.DataFrame(columns=config['fight_stats_column_names'])

# Save: Append new fight stats to the top
all_fight_stats_df = pd.concat([all_fight_stats_df, existing_fight_stats_df], ignore_index=True)
all_fight_stats_df.to_csv(existing_fight_stats_file, index=False)

# Show updated fight stats
display(all_fight_stats_df)


# In[ ]:




