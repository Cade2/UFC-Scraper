#!/usr/bin/env python
# coding: utf-8

# 
# **Overview**
# 
# This notebook parses all past ufc fight stats when run, it does not include upcoming fights
# 
# 
# **scrape ufc fight stats**
# 
# Get all event details, name, url, date, location for all ufc events
# for each event, get fight details all fights on card
# parse each fight to get fight stats of both fighters
# 

# In[1]:


# imports
import pandas as pd
from tqdm.notebook import tqdm_notebook

# import library
import scrape_ufc_stats_library as LIB

# import config
import yaml
config = yaml.safe_load(open('scrape_ufc_stats_config.yaml'))


# ## Parse Event Details
# 
# Includes:
# * Event
# * URL
# * Date
# * Location

# In[2]:


# define url to parse
events_url = config['completed_events_all_url']


# In[3]:


# get soup
soup = LIB.get_soup(events_url)

# parse event details
all_event_details_df = LIB.parse_event_details(soup)

# show event details
display(all_event_details_df)

# write event details to file
all_event_details_df.to_csv(config['event_details_file_name'], index=False)


# ## Parse Fight Details
# Includes:
# * Event
# * Bout
# * URL

# In[4]:


# define list of urls of fights to parse
list_of_events_urls = list(all_event_details_df['URL'])


# In[5]:


# create empty df to store fight details
all_fight_details_df = pd.DataFrame(columns=config['fight_details_column_names'])

# loop through each event and parse fight details
for url in tqdm_notebook(list_of_events_urls):

    # get soup
    soup = LIB.get_soup(url)

    # parse fight links
    fight_details_df = LIB.parse_fight_details(soup)
    
    # concat fight details
    all_fight_details_df = pd.concat([all_fight_details_df, fight_details_df])

# show all fight details
display(all_fight_details_df)

# write fight details to file
all_fight_details_df.to_csv(config['fight_details_file_name'], index=False)


# ## Parse Fight Results and Fight Stats
# ### Fight Results Includes:
# * Event
# * Bout
# * Weightclass
# * Method
# * Round
# * Time
# * Time Format
# * Referee
# * Details
# 
# ### Fight Stats Includes:
# * Event
# * Bout
# * Round
# * Fighter
# * Kd
# * Sig.Str.
# * Sig.Str. %
# * Total Str.
# * Td
# * Td %
# * Sub.Att
# * Rev.
# * Ctrl
# * Head
# * Body
# * Leg
# * Distance
# * Clinch
# * Ground

# In[ ]:


# define list of urls of fights to parse
list_of_fight_details_urls = list(all_fight_details_df['URL'])


# In[ ]:


# create empty df to store fight results
all_fight_results_df = pd.DataFrame(columns=config['fight_results_column_names'])
# create empty df to store fight stats
all_fight_stats_df = pd.DataFrame(columns=config['fight_stats_column_names'])

# loop through each fight and parse fight results and stats
for url in tqdm_notebook(list_of_fight_details_urls):

    # get soup
    soup = LIB.get_soup(url)

    # parse fight results and fight stats
    fight_results_df, fight_stats_df = LIB.parse_organise_fight_results_and_stats(
        soup,
        url,
        config['fight_results_column_names'],
        config['totals_column_names'],
        config['significant_strikes_column_names']
        )

    # concat fight results
    all_fight_results_df = pd.concat([all_fight_results_df, fight_results_df])
    # concat fight stats
    all_fight_stats_df = pd.concat([all_fight_stats_df, fight_stats_df])

# show all fight results
display(all_fight_results_df)
# show all fight stats
display(all_fight_stats_df)

# write to file
all_fight_results_df.to_csv(config['fight_results_file_name'], index=False)
# write to file
all_fight_stats_df.to_csv(config['fight_stats_file_name'], index=False)


# In[ ]:




