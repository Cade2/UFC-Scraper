#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from bs4 import BeautifulSoup
import pandas as pd


# In[2]:


def scrape_mma_decisions():
    base_url = "https://mmadecisions.com/decisions-by-fighter/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    fighter_data = []
    fighter_links = soup.find_all('a', class_='fighter-link')

    for link in fighter_links:
        name = link.text.strip()
        profile_url = f"https://mmadecisions.com{link['href']}"

        fighter_data.append({
            'Name': name,
            'URL': profile_url
        })

    # Convert to DataFrame
    fighter_df = pd.DataFrame(fighter_data)
    return fighter_df


# In[3]:


# Example usage
mma_decisions_df = scrape_mma_decisions()
mma_decisions_df.to_csv('mma_decisions_backup.csv', index=False)


# In[ ]:




