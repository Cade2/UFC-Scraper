#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from bs4 import BeautifulSoup
import pandas as pd


# In[2]:


# Function to scrape fighter details from UFC Athletes
def scrape_ufc_athletes():
    base_url = "https://www.ufc.com/athletes/all"
    fighters_data = []

    # Iterate through the pages (pagination)
    page = 1
    while True:
        # Fetch the page content
        url = f"{base_url}?page={page}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find fighter cards on the page
        fighter_cards = soup.find_all('div', class_='c-listing-athlete__text')
        if not fighter_cards:  # Stop if no fighters found (end of pagination)
            break

        # Extract fighter details from each card
        for card in fighter_cards:
            name = card.find('h3', class_='c-listing-athlete__name').text.strip()
            nickname = card.find('div', class_='c-listing-athlete__nickname')
            nickname = nickname.text.strip() if nickname else None
            link = card.find('a', class_='c-listing-athlete__link')['href']
            full_url = f"https://www.ufc.com{link}"

            # Append to the data list
            fighters_data.append({
                'Name': name,
                'Nickname': nickname,
                'URL': full_url
            })

        # Move to the next page
        page += 1

    # Convert to DataFrame
    fighters_df = pd.DataFrame(fighters_data)
    return fighters_df


# In[5]:


# Example usage
fighters_df = scrape_ufc_athletes()
fighters_df.to_csv('ufc_athletes_backup.csv', index=False)


# In[7]:


print(f"Found {len(fighter_cards)} fighter cards on this page.")
for card in fighter_cards:
    print(card.prettify())  # Print each card's raw HTML


# In[ ]:




