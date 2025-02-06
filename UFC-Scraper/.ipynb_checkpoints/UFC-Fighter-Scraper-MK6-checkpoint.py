#!/usr/bin/env python
# coding: utf-8

# In[1]:


#!/usr/bin/env python
# coding: utf-8

# imports
import pandas as pd
import numpy as np
from tqdm.notebook import tqdm_notebook
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import scrape_ufc_stats_library as LIB
import yaml
import nest_asyncio
import random
import time
import os


# In[2]:


# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load configuration
config = yaml.safe_load(open('scrape_ufc_stats_config.yaml'))


# In[3]:


# Asynchronous get_soup replacement with retries and backoff
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


# In[4]:


# Fetch multiple soups concurrently with delay and limit
async def fetch_all_soups(urls, max_concurrent=5):
    connector = aiohttp.TCPConnector(limit=max_concurrent)  # Limit simultaneous requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        soups = []
        for url in urls:
            soup = await get_soup_async(url, session)
            soups.append(soup)
            # Add a random delay between 1 and 3 seconds to reduce rate-limiting
            await asyncio.sleep(random.uniform(1, 3))
        return soups


# In[5]:


# ## Parse Fighter Details
# Includes: First, Last, Nickname, URL

# Generate list of alphabetical URLs for fighter details
list_of_alphabetical_urls = LIB.generate_alphabetical_urls()

# Asynchronous parsing of fighter details
async def parse_fighter_details_async(fighter_urls):
    soups = await fetch_all_soups(fighter_urls)
    all_fighter_details = pd.DataFrame(columns=config['fighter_details_column_names'])

    for soup, url in zip(soups, fighter_urls):
        if soup is not None:
            try:
                fighter_details_df = LIB.parse_fighter_details(soup, config['fighter_details_column_names'])
                all_fighter_details = pd.concat([all_fighter_details, fighter_details_df])
            except Exception as e:
                print(f"Error parsing fighter details for URL: {url}")
                print(f"Error: {e}")
        else:
            print(f"Skipping URL due to empty soup: {url}")
    return all_fighter_details

# Execute async function for fighter details
loop = asyncio.get_event_loop()
all_fighter_details_df = loop.run_until_complete(parse_fighter_details_async(list_of_alphabetical_urls))

# Load existing fighter details
existing_fighter_details_file = config['fighter_details_file_name']
if os.path.exists(existing_fighter_details_file):
    existing_fighter_details_df = pd.read_csv(existing_fighter_details_file)
    existing_fighter_urls = set(existing_fighter_details_df['URL'])
else:
    existing_fighter_urls = set()

# Filter for new fighters
all_fighter_details_df = all_fighter_details_df[~all_fighter_details_df['URL'].isin(existing_fighter_urls)]

# Save: Append new fighters to the top
if not all_fighter_details_df.empty:
    all_fighter_details_df = pd.concat([all_fighter_details_df, existing_fighter_details_df], ignore_index=True)
    all_fighter_details_df.to_csv(existing_fighter_details_file, index=False)

# Show updated fighter details
display(all_fighter_details_df)


# In[6]:


# ## Parse Fighter Tale of the Tape
# Includes: Fighter, Height, Weight, Reach, Stance, DOB, URL

# Define list of fighter profile URLs
list_of_fighter_urls = list(all_fighter_details_df['URL'])

# Asynchronous parsing of fighter "Tale of the Tape"
async def parse_fighter_tott_async(fighter_urls):
    soups = await fetch_all_soups(fighter_urls)
    all_fighter_tott = pd.DataFrame(columns=config['fighter_tott_column_names'])

    for soup, url in zip(soups, fighter_urls):
        if soup is not None:
            try:
                fighter_tott = LIB.parse_fighter_tott(soup)
                fighter_tott_df = LIB.organise_fighter_tott(fighter_tott, config['fighter_tott_column_names'], url)
                all_fighter_tott = pd.concat([all_fighter_tott, fighter_tott_df])
            except Exception as e:
                print(f"Error parsing tale of the tape for URL: {url}")
                print(f"Error: {e}")
        else:
            print(f"Skipping URL due to empty soup: {url}")
    return all_fighter_tott

# Execute async function for fighter "Tale of the Tape"
all_fighter_tott_df = loop.run_until_complete(parse_fighter_tott_async(list_of_fighter_urls))

# Load existing fighter tale of the tape
existing_fighter_tott_file = config['fighter_tott_file_name']
if os.path.exists(existing_fighter_tott_file):
    existing_fighter_tott_df = pd.read_csv(existing_fighter_tott_file)
    existing_fighter_tott_urls = set(existing_fighter_tott_df['URL'])
else:
    existing_fighter_tott_urls = set()

# Filter for new fighter tales of the tape
all_fighter_tott_df = all_fighter_tott_df[~all_fighter_tott_df['URL'].isin(existing_fighter_tott_urls)]

# Save: Append new fighter tales of the tape to the top
if not all_fighter_tott_df.empty:
    all_fighter_tott_df = pd.concat([all_fighter_tott_df, existing_fighter_tott_df], ignore_index=True)
    all_fighter_tott_df.to_csv(existing_fighter_tott_file, index=False)

# Show updated fighter tale of the tape
display(all_fighter_tott_df)


# In[ ]:




