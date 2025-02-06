#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from bs4 import BeautifulSoup
import pandas as pd


# In[2]:


def scrape_sherdog_events():
    url = "https://www.sherdog.com/organizations/Ultimate-Fighting-Championship-UFC-2"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    events_data = []
    event_cards = soup.find_all('tr', class_='event')

    for card in event_cards:
        name = card.find('td', class_='event-title').text.strip()
        date = card.find('td', class_='date').text.strip()
        location = card.find('td', class_='location').text.strip()

        events_data.append({
            'Event Name': name,
            'Date': date,
            'Location': location
        })

    # Convert to DataFrame
    events_df = pd.DataFrame(events_data)
    return events_df


# In[3]:


# Example usage
sherdog_events_df = scrape_sherdog_events()
sherdog_events_df.to_csv('sherdog_events_backup.csv', index=False)


# In[ ]:




