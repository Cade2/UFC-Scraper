#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from bs4 import BeautifulSoup
import pandas as pd


# In[2]:


def scrape_ufc_events():
    url = "https://www.ufc.com/events"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    events_data = []
    event_cards = soup.find_all('div', class_='c-card-event--result')

    for card in event_cards:
        name = card.find('h3', class_='c-card-event--result__headline').text.strip()
        date = card.find('div', class_='c-card-event--result__date').text.strip()
        location = card.find('div', class_='c-card-event--result__location')
        location = location.text.strip() if location else None

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
events_df = scrape_ufc_events()
events_df.to_csv('ufc_events_backup.csv', index=False)


# In[ ]:




