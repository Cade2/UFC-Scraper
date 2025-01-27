#!/usr/bin/env python
# coding: utf-8

# **Overview**
# This notebook parses all fighters' details and tale of the tape
# 
# **Scrape ufc fighters' details**
# Includes 
# * First
# * Last
# * Nickname
# * Url
# 
# **From url scrape scrape fighter's tale of the tape**
# Includes 
# * Fighter
# * Height
# * Weight
# * Reach
# * Stance
# * DOB
# 

# In[1]:


# imports
import pandas as pd
import numpy as np
from tqdm.notebook import tqdm_notebook

# import library
import scrape_ufc_stats_library as LIB
import importlib
importlib.reload(LIB)

# import configs
import yaml
config = yaml.safe_load(open('scrape_ufc_stats_config.yaml'))


# ## Parse Fighter Details
# Includes 
# * First
# * Last
# * Nickname
# * Url

# In[2]:


# generate list of urls for fighter details
list_of_alphabetical_urls = LIB.generate_alphabetical_urls()


# In[3]:


# create empty dataframe to store all fighter details
all_fighter_details_df = pd.DataFrame()

# loop through list of alphabetical urls
for url in tqdm_notebook(list_of_alphabetical_urls):
    # get soup
    soup = LIB.get_soup(url)
    # parse fighter details
    fighter_details_df = LIB.parse_fighter_details(soup, config['fighter_details_column_names'])
    # concat fighter_details_df to all_fighter_details_df
    all_fighter_details_df = pd.concat([all_fighter_details_df, fighter_details_df])

# show all fighter details
display(all_fighter_details_df)

# write to file
all_fighter_details_df.to_csv(config['fighter_details_file_name'], index=False)


# ## Parse Fighter Tale of the Tape
# Includes 
# * Fighter
# * Height
# * Weight
# * Reach
# * Stance
# * DOB
# * URL

# In[4]:


# define list of urls of fighters to parse
list_of_fighter_urls = list(all_fighter_details_df['URL'])


# In[ ]:


# create empty df to store fighters' tale of the tape
all_fighter_tott_df = pd.DataFrame(columns=config['fighter_tott_column_names'])

# loop through list_of_fighter_urls
for url in tqdm_notebook(list_of_fighter_urls):
    # get soup
    soup = LIB.get_soup(url)
    # parse fighter tale of the tape
    fighter_tott = LIB.parse_fighter_tott(soup)
    # organise fighter tale of the tape
    fighter_tott_df = LIB.organise_fighter_tott(fighter_tott, config['fighter_tott_column_names'], url)
    # concat fighter
    all_fighter_tott_df = pd.concat([all_fighter_tott_df, fighter_tott_df])

# show all fighters' tale of the tape
display(all_fighter_tott_df)

# write to file
all_fighter_tott_df.to_csv(config['fighter_tott_file_name'], index=False)


# In[ ]:




