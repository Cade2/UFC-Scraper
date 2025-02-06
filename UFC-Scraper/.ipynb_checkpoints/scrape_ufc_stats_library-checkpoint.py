'''
Overview

library of functions to scrape ufc stats

'''

# imports
import pandas as pd
import numpy as np
import re
import requests
from bs4 import BeautifulSoup
import itertools
import string
import aiohttp  
import asyncio
import random
from datetime import datetime
import os


# get soup from url
def get_soup(url):
    '''
    get soup from url using beautifulsoup

    arguments:
    url (str): url of page to parse

    returns:
    soup
    '''
    
    # get page of url
    page = requests.get(url)
    # create soup
    soup = BeautifulSoup(page.content, 'html.parser')

    # return
    return soup

# Asynchronous function to fetch soup
async def get_soup_async(url, session, retries=3):
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return BeautifulSoup(html, 'html.parser')
                elif response.status == 429:
                    print(f"Rate-limited on {url}. Retrying in {2 ** attempt} seconds...")
                    await asyncio.sleep(2 ** attempt)
        except Exception as e:
            print(f"Error fetching URL: {url}, attempt {attempt + 1}")
    return None


import asyncio
import aiohttp
import random
from bs4 import BeautifulSoup

# Asynchronous function to fetch multiple soups
async def fetch_all_soups(urls, max_concurrent=5, max_attempts=3):
    """
    Fetches multiple webpages asynchronously and returns a list of BeautifulSoup objects.

    Args:
        urls (list): List of URLs to fetch.
        max_concurrent (int): Maximum number of concurrent requests.
        max_attempts (int): Maximum retry attempts for each URL.

    Returns:
        list: List of BeautifulSoup objects.
    """
    connector = aiohttp.TCPConnector(limit=max_concurrent)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        soups = []
        
        for url in urls:
            if url == "N/A":
                soups.append(None)
                continue
            
            success = False
            for attempt in range(max_attempts):
                try:
                    soup = await get_soup_async(url, session)
                    if soup:
                        soups.append(soup)
                        success = True
                        break  # ✅ Stop retrying once successful
                except Exception:
                    await asyncio.sleep(random.uniform(1, 2))  # ✅ Random delay to avoid detection
            
            if not success:
                print(f"❌ Failed to fetch event page: {url}")
                soups.append(None)  # Append None if all attempts fail

        return soups

import pandas as pd
from bs4 import BeautifulSoup

def parse_upcoming_events(soup):
    """
    Parses UFCStats.com upcoming events and extracts event details.

    Arguments:
        soup (BeautifulSoup): Parsed HTML of UFC events page.

    Returns:
        DataFrame: A DataFrame containing upcoming event details.
    """
    event_names = []
    event_dates = []
    event_locations = []
    event_urls = []

    # 🔍 Find all event containers
    event_containers = soup.find_all("tr", class_="b-statistics__table-row")

    if not event_containers:
        print("⚠️ No event containers found! UFCStats.com might have changed the structure.")
        return pd.DataFrame()

    for event in event_containers:
        # ✅ Extract event name
        name_tag = event.find("a", class_="b-link")
        event_name = name_tag.text.strip() if name_tag else "N/A"

        # ✅ Extract event URL
        event_url = name_tag["href"] if name_tag and name_tag.has_attr("href") else "N/A"

        # ✅ Extract event date
        date_tag = event.find("span", class_="b-statistics__date")
        event_date = date_tag.text.strip() if date_tag else "N/A"

        # ✅ Extract event location (not always present)
        location_tag = event.find("td", class_="b-statistics__table-col")
        event_location = location_tag.text.strip() if location_tag else "N/A"

        event_names.append(event_name)
        event_dates.append(event_date)
        event_locations.append(event_location)
        event_urls.append(event_url)

    # ✅ Create DataFrame
    event_df = pd.DataFrame({
        "EVENT": event_names,
        "DATE": event_dates,
        "LOCATION": event_locations,
        "URL": event_urls
    })

    return event_df



import re

def generate_event_name(event_url, bout_name):
    """
    Generates the correct event name based on the event URL.

    Args:
        event_url (str): The URL of the event.
        bout_name (str): The main fight (e.g., "Adesanya vs Imavov").

    Returns:
        str: Properly formatted event name (e.g., "UFC Fight Night: Adesanya vs Imavov").
    """
    try:
        # ✅ Fight Night Events
        if "fight-night" in event_url:
            return f"UFC Fight Night: {bout_name}"

        # ✅ Pay-Per-View (PPV) Events
        ppv_match = re.search(r"ufc-(\d+)", event_url)
        if ppv_match:
            ppv_number = ppv_match.group(1)
            return f"UFC {ppv_number}: {bout_name}"

        # ✅ Default Label for Unknown Events
        return f"UFC Event: {bout_name}"

    except Exception as e:
        print(f"❌ Error generating event name: {e}")
        return "UFC Event"

from datetime import datetime

async def extract_event_date(session, event_url):
    """
    Extracts the event date from the UFC event page using the data-timestamp attribute.
    
    Args:
        session (aiohttp.ClientSession): Async session for fetching the webpage.
        event_url (str): The event's URL.

    Returns:
        str: The event date in "Month Day, Year" format or "N/A" if not found.
    """
    try:
        async with session.get(event_url) as response:
            if response.status != 200:
                print(f"⚠️ Failed to fetch event page: {event_url}")
                return "N/A"
            
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # Find the span element containing the date timestamp
            date_span = soup.find("span", class_="hero-fixed-bar__date tz-change-inner")
            
            if date_span and date_span.get("data-timestamp"):
                # Convert UNIX timestamp to readable date
                timestamp = int(date_span["data-timestamp"])
                event_date = datetime.utcfromtimestamp(timestamp).strftime("%B %d, %Y")  # Format: "February 01, 2025"
                return event_date

            print(f"⚠️ Date not found for {event_url}")
            return "N/A"
        
    except Exception as e:
        print(f"❌ Error extracting event date from {event_url}: {e}")
        return "N/A"

def clean_event_date(raw_date):
    """
    Cleans the raw event date format from UFC.com and converts it to 'Month Day, Year'.
    
    Args:
        raw_date (str): Raw date string (e.g., "Sat, Feb 1 / 12:00 PM EST / Main Card").

    Returns:
        str: Formatted date string (e.g., "February 01, 2025") or "N/A" if parsing fails.
    """
    try:
        # Extract only the month and day using regex
        match = re.search(r"([A-Za-z]+) (\d+)", raw_date)
        if match:
            month = match.group(1)
            day = match.group(2)

            # Get the current year (Assuming events are in the future)
            today = datetime.today()
            year = today.year

            # Convert to datetime and format correctly
            formatted_date = datetime.strptime(f"{month} {day} {year}", "%b %d %Y").strftime("%B %d, %Y")
            return formatted_date

    except Exception as e:
        print(f"❌ Error formatting event date: {raw_date} -> {e}")

    return "N/A"

async def fetch_ufc_events():
    """Fetch upcoming UFC events and extract event details."""
    url = "https://www.ufc.com/events#events-list-upcoming"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ Failed to fetch UFC Events page, Status Code: {response.status}")
                return pd.DataFrame()

            page_html = await response.text()
    
    soup = BeautifulSoup(page_html, "html.parser")
    
    # 🔍 Find all event cards
    event_cards = soup.find_all("div", class_="c-card-event--result")

    if not event_cards:
        print("⚠️ No event cards found! UFC may have changed the structure.")
        return pd.DataFrame()

    events = []
    for event in event_cards:
        event_name_tag = event.find("h3", class_="c-card-event--result__headline")
        event_name = event_name_tag.text.strip() if event_name_tag else "Unknown Event"

        event_date_tag = event.find("div", class_="c-card-event--result__date")
        event_date = event_date_tag.text.strip() if event_date_tag else "Unknown Date"

        event_location_tag = event.find("div", class_="c-card-event--result__location")
        event_location = event_location_tag.text.strip() if event_location_tag else "Unknown Location"

        event_link_tag = event.find("a", class_="c-card-event--result__logo-link")
        event_url = f"https://www.ufc.com{event_link_tag['href']}" if event_link_tag else "Unknown URL"

        event_type = determine_event_type(event_url)

        events.append({
            "EVENT": f"{event_type}: {event_name}",
            "DATE": format_event_date(event_date),
            "LOCATION": event_location,
            "URL": event_url
        })

    print(f"✅ Successfully extracted {len(events)} upcoming UFC events!")
    return pd.DataFrame(events)

def determine_event_type(event_url):
    """Identify if an event is a Fight Night or a PPV."""
    if "ufc-fight-night" in event_url:
        return "UFC Fight Night"
    elif re.search(r'ufc-\d+$', event_url):
        return "UFC PPV"
    return "Unknown"

def extract_fight_urls(soup, event_url):
    """
    Extracts fight URLs from UFC.com event pages.

    Args:
        soup (BeautifulSoup): Parsed HTML of the event page.
        event_url (str): The main event page URL.

    Returns:
        list: A list of properly formatted fight URLs.
    """
    fight_urls = []

    fight_containers = soup.find_all("div", class_="c-listing-fight")

    for fight in fight_containers:
        fight_id = fight.get("data-fmid", "N/A")  # Extract fight ID from data-fmid
        if fight_id != "N/A":
            fight_url = f"{event_url}#{fight_id}"  # Construct full fight URL
            fight_urls.append(fight_url)

    return fight_urls


# Function to extract fight URLs correctly with fight ID
def extract_fight_urls_ufc_com(soup, event_url):
    """
    Extracts fight URLs from UFC.com event pages by finding fight IDs.

    Args:
        soup (BeautifulSoup): Parsed HTML of the event page.
        event_url (str): Base event URL.

    Returns:
        list: List of dictionaries with properly formatted fight URLs and fight IDs.
    """
    fight_urls = []

    try:
        # ✅ Find all fight elements with "data-fmid"
        fight_blocks = soup.find_all("div", class_="c-listing-fight", attrs={"data-fmid": True})

        for fight in fight_blocks:
            fight_id = fight.get("data-fmid")  # Extract fight ID from data-fmid

            if fight_id:
                fight_url = f"{event_url}#{fight_id}"  # ✅ Construct full fight URL
                fight_urls.append({"fight_url": fight_url, "fight_id": fight_id})  # ✅ Return dictionary instead of string

        if not fight_urls:
            print(f"⚠️ No fight URLs found for {event_url} (Check HTML structure)")

    except Exception as e:
        print(f"❌ Error extracting fight URLs for {event_url}: {e}")

    return fight_urls  # ✅ Ensure it returns a list of dictionaries

def fetch_upcoming_events():
    """ Fetches all upcoming UFC events and returns a list of dictionaries with event details. """
    url = f"{BASE_URL}/events#events-list-upcoming"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for event in soup.select(".c-card-event--result"):
        event_name = event.select_one(".c-card-event__headline").text.strip()
        event_url = BASE_URL + event.select_one("a")["href"]
        event_date = event.select_one(".c-card-event__date").text.strip()

        events.append({"event_name": event_name, "event_url": event_url, "event_date": event_date})

    return events


def fetch_fight_list(event_url):
    """ Extracts fight URLs and fight IDs from the event page. """
    response = requests.get(event_url)
    soup = BeautifulSoup(response.text, "html.parser")

    fights = []
    for fight in soup.select(".c-listing-fight"):
        fight_id = fight["data-fmid"]
        fight_url = f"{event_url}#{fight_id}"

        red_fighter = fight.select_one(".c-listing-fight__corner-name--red a").text.strip()
        blue_fighter = fight.select_one(".c-listing-fight__corner-name--blue a").text.strip()

        weight_class = fight.select_one(".c-listing-fight__class-text").text.strip()
        rounds = "3"  # Default to 3 rounds unless found otherwise

        fights.append({
            "fight_url": fight_url,
            "fight_id": fight_id,
            "red_fighter": red_fighter,
            "blue_fighter": blue_fighter,
            "weight_class": weight_class,
            "rounds": rounds
        })

    return fights


def fetch_fighter_profile(fighter_url):
    """ Extracts all relevant fighter stats from their UFC profile page. """
    response = requests.get(fighter_url)
    soup = BeautifulSoup(response.text, "html.parser")

    fighter_stats = {
        "record": None, "country": None, "height": None, "weight": None, "reach": None, "leg_reach": None,
        "ko_tko_pct": None, "submission_pct": None, "decision_pct": None, "avg_fight_time": None,
        "knockdown_avg_15_min": None, "sig_strikes_landed_per_min": None, "significant_strike_accuracy": None,
        "significant_strike_absorbed_per_min": None, "defense": None, "takedown_avg_15_min": None,
        "takedown_accuracy": None, "takedown_defense": None, "submission_avg_15_min": None
    }

    # Extracting stats
    for stat in soup.select(".athlete-stats__stat"):
        label = stat.select_one(".athlete-stats__stat-text").text.strip()
        value = stat.select_one(".athlete-stats__stat-numb").text.strip()

        if "Wins by Knockout" in label:
            fighter_stats["ko_tko_pct"] = value
        elif "Submission" in label:
            fighter_stats["submission_pct"] = value
        elif "Decision" in label:
            fighter_stats["decision_pct"] = value

    return fighter_stats


def save_fight_data(fight_data, file_path):
    """ Saves fight data to a CSV file. """
    df = pd.DataFrame(fight_data)
    df.to_csv(file_path, index=False)
    print(f"📁 Saved updated fight data to {file_path}")

from bs4 import BeautifulSoup

def extract_fight_info(soup):
    """
    Extracts detailed fight information.

    Args:
        soup (BeautifulSoup): Parsed HTML of the fight page.

    Returns:
        list: A list of dictionaries (one per fighter).
    """
    fight_details = []

    try:
        # ✅ Extract Weight Class
        weight_class_tag = soup.find("div", class_="c-listing-fight__class-text")
        weight_class = weight_class_tag.text.strip() if weight_class_tag else "N/A"

        # ✅ Extract Fighter Details
        fighter_blocks = soup.find_all("div", class_="c-listing-fight__corner-name")
        if len(fighter_blocks) < 2:
            print("⚠️ Could not extract both fighters!")
            return []

        for fighter in fighter_blocks:
            fighter_name = fighter.text.strip()
            fighter_profile = "https://www.ufc.com" + fighter.find("a")["href"] if fighter.find("a") else "N/A"

            fighter_data = {
                "FIGHTER": fighter_name,
                "PROFILE": fighter_profile,
                "WEIGHT CLASS": weight_class,
                "RECORD": "N/A",
                "HEIGHT": "N/A",
                "WEIGHT": "N/A",
                "REACH": "N/A",
                "LEG REACH": "N/A",
                "KO/TKO %": "N/A",
                "SUBMISSION %": "N/A",
                "DECISION %": "N/A",
                "AVG FIGHT TIME": "N/A",
                "KNOCKDOWN AVG/15 MIN": "N/A",
                "SIG. STR. LANDED/MIN": "N/A",
                "SIG. STR. ABSORBED/MIN": "N/A",
                "DEFENSE": "N/A",
                "TAKEDOWN AVG/15 MIN": "N/A",
                "TAKEDOWN ACCURACY": "N/A",
                "TAKEDOWN DEFENSE": "N/A",
                "SUBMISSION AVG/15 MIN": "N/A",
                "ODDS": "N/A",
                "MONEY LINE": "N/A",
                "TOTAL ROUNDS": "N/A",
                "ODDS TO WIN BY KO": "N/A",
                "ODDS TO WIN BY SUBMISSION": "N/A",
                "ODDS TO WIN BY DECISION": "N/A"
            }

            fight_details.append(fighter_data)

    except Exception as e:
        print(f"❌ Error extracting fight details: {e}")

    return fight_details



def extract_bout_ufc_com(soup):
    """
    Extracts the bout name (if available) or constructs it from fighter names.

    Args:
        soup (BeautifulSoup): Parsed HTML of the fight page.

    Returns:
        str: The bout name (e.g., "Adesanya vs Pereira").
    """
    try:
        # ✅ Try extracting the bout name if available
        bout_header = soup.find("h2", class_="c-bout-title")
        if bout_header:
            return bout_header.text.strip()  # Example: "Middleweight Bout"

        # ✅ If no bout title, construct from fighter names
        fighter_names = soup.find_all("div", class_="c-listing-fight__name")
        if len(fighter_names) == 2:
            fighter_1 = fighter_names[0].text.strip()
            fighter_2 = fighter_names[1].text.strip()
            return f"{fighter_1} vs {fighter_2}"  # Example: "Adesanya vs Pereira"

        return "N/A"

    except Exception as e:
        print(f"❌ Error extracting bout info: {e}")
        return "N/A"


def extract_fight_data_ufc_com(soup):
    """
    Extracts fight details including fighter names, weight class, country, and profile links.

    Args:
        soup (BeautifulSoup): Parsed HTML of the fight page.

    Returns:
        dict: A dictionary containing extracted fight details.
    """
    base_url = "https://www.ufc.com"

    fight_data = {
        "BOUT": "N/A",
        "WEIGHT CLASS": "N/A",
        "RED FIGHTER": "N/A",
        "BLUE FIGHTER": "N/A",
        "RED COUNTRY": "N/A",
        "BLUE COUNTRY": "N/A",
        "RED FIGHTER PROFILE": "N/A",
        "BLUE FIGHTER PROFILE": "N/A",
        "RED ODDS": "N/A",
        "BLUE ODDS": "N/A",
    }

    try:
        # ✅ Extract Fighter Names & Profile URLs
        fighter_blocks = soup.find_all("div", class_="c-listing-fight__corner-name")

        if len(fighter_blocks) >= 2:
            # ✅ Red Fighter
            red_fighter_tag = fighter_blocks[0].find("a")
            fight_data["RED FIGHTER"] = red_fighter_tag.text.strip() if red_fighter_tag else "N/A"
            fight_data["RED FIGHTER PROFILE"] = base_url + red_fighter_tag["href"] if red_fighter_tag and "href" in red_fighter_tag.attrs else "N/A"

            # ✅ Blue Fighter
            blue_fighter_tag = fighter_blocks[1].find("a")
            fight_data["BLUE FIGHTER"] = blue_fighter_tag.text.strip() if blue_fighter_tag else "N/A"
            fight_data["BLUE FIGHTER PROFILE"] = base_url + blue_fighter_tag["href"] if blue_fighter_tag and "href" in blue_fighter_tag.attrs else "N/A"

            # ✅ BOUT Name
            fight_data["BOUT"] = f"{fight_data['RED FIGHTER']} vs {fight_data['BLUE FIGHTER']}"

        # ✅ Extract Weight Class
        weight_class_element = soup.find("div", class_="c-listing-fight__class-text")
        if weight_class_element:
            fight_data["WEIGHT CLASS"] = weight_class_element.text.strip()

        # ✅ Extract Fighter Countries
        country_elements = soup.find_all("div", class_="c-listing-fight__country-text")
        if len(country_elements) >= 2:
            fight_data["RED COUNTRY"] = country_elements[0].text.strip()
            fight_data["BLUE COUNTRY"] = country_elements[1].text.strip()

        # ✅ Extract Betting Odds
        odds_elements = soup.find_all("span", class_="c-listing-fight__odds-amount")
        if len(odds_elements) >= 2:
            fight_data["RED ODDS"] = odds_elements[0].text.strip()
            fight_data["BLUE ODDS"] = odds_elements[1].text.strip()

    except Exception as e:
        print(f"❌ Error extracting fight data: {e}")

    return fight_data


def extract_weight_class(soup):
    """
    Extracts the weight class from the fight page.

    Args:
        soup (BeautifulSoup): Parsed HTML of the fight page.

    Returns:
        str: The weight class (e.g., "Middleweight").
    """
    try:
        # ✅ Look for the bout title (e.g., "Middleweight Bout")
        bout_title = soup.find("h2", class_="c-bout-title")
        
        if bout_title:
            weight_class = bout_title.text.strip().replace(" Bout", "")  # ✅ Remove "Bout"
            return weight_class

        return "Catchweight"  # ✅ Default if no weight class is found

    except Exception as e:
        print(f"❌ Error extracting weight class: {e}")
        return "N/A"


# Add inside LIB.extract_fight_data_ufc_com()
def extract_fight_rounds(soup):
    """
    Extracts the number of rounds in a fight.
    
    Args:
        soup (BeautifulSoup): Parsed fight page HTML.
    
    Returns:
        str: Number of rounds (e.g., "3", "5").
    """
    try:
        rounds_tag = soup.find("div", class_="some-class-that-has-rounds")  # Replace with actual class
        return rounds_tag.text.strip() if rounds_tag else "N/A"
    except Exception as e:
        print(f"❌ Error extracting fight rounds: {e}")
        return "N/A"


async def extract_fighter_profile_ufc_com(url, session):
    """
    Extracts fighter stats from their profile page.

    Args:
        url (str): The URL of the fighter's UFC profile.
        session (aiohttp.ClientSession): The async session to make requests.

    Returns:
        dict: A dictionary containing the fighter's stats.
    """
    fighter_stats = {
        "RECORD": "N/A",
        "HEIGHT": "N/A",
        "WEIGHT": "N/A",
        "REACH": "N/A",
        "LEG REACH": "N/A",
        "KO/TKO %": "N/A",
        "SUBMISSION %": "N/A",
        "DECISION %": "N/A",
        "AVERAGE FIGHT TIME": "N/A",
        "KNOCKDOWN AVG/15 MIN": "N/A",
        "SIG.STR. LANDED PER MIN": "N/A",
        "SIGNIFICANT STRIKES ACCURACY": "N/A",
        "SIG.STR. ABSORBED PER MIN": "N/A",
        "DEFENSE": "N/A",
        "TAKEDOWN AVG/15 MIN": "N/A",
        "TAKEDOWN ACCURACY": "N/A",
        "TAKEDOWN DEFENSE": "N/A",
        "SUBMISSION AVG/15 MIN": "N/A",
    }

    try:
        soup = await LIB.get_soup_async(url, session)  # ✅ Fetch fighter profile page

        # ✅ Extract fighter stats from their profile
        stat_blocks = soup.find_all("div", class_="c-stat-compare__group")

        for stat in stat_blocks:
            stat_label = stat.find("div", class_="c-stat-compare__label").text.strip()
            stat_value = stat.find("div", class_="c-stat-compare__number").text.strip()

            if stat_label in fighter_stats:
                fighter_stats[stat_label] = stat_value

    except Exception as e:
        print(f"❌ Error extracting stats from {url}: {e}")

    return fighter_stats

import aiohttp
from bs4 import BeautifulSoup

async def extract_fighter_stats(fighter_url, session):
    """
    Fetches a fighter's profile page and extracts detailed statistics including AGE.
    
    Args:
        fighter_url (str): The URL of the fighter's profile page.
        session (aiohttp.ClientSession): The async session for HTTP requests.

    Returns:
        dict: Fighter's stats (record, height, weight, reach, age, etc.).
    """
    fighter_stats = {
        "AGE": "N/A",
        "RECORD": "N/A",
        "HEIGHT": "N/A",
        "WEIGHT": "N/A",
        "REACH": "N/A",
        "LEG REACH": "N/A",
        "KO/TKO %": "N/A",
        "SUBMISSION %": "N/A",
        "DECISION %": "N/A",
        "AVERAGE FIGHT TIME": "N/A",
        "KNOCKDOWN AVG/15 MIN": "N/A",
        "SIG.STR. LANDED PER MIN": "N/A",
        "SIGNIFICANT STRIKES ACCURACY": "N/A",
        "SIG.STR. ABSORBED PER MIN": "N/A",
        "DEFENSE": "N/A",
        "TAKEDOWN AVG/15 MIN": "N/A",
        "TAKEDOWN ACCURACY": "N/A",
        "TAKEDOWN DEFENSE": "N/A",
        "SUBMISSION AVG/15 MIN": "N/A"
    }

    try:
        async with session.get(fighter_url) as response:
            if response.status != 200:
                print(f"❌ Error fetching fighter profile: {fighter_url}")
                return fighter_stats

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # ✅ Extract Fighter Age
            age_elem = soup.find("div", class_="c-bio__label", text="Age")
            if age_elem:
                value_elem = age_elem.find_next_sibling("div", class_="c-bio__text")
                if value_elem:
                    fighter_stats["AGE"] = value_elem.text.strip()

            # ✅ Extract Fighter Record
            record_elem = soup.find("p", class_="hero-profile__division-body")
            if record_elem:
                fighter_stats["RECORD"] = record_elem.text.strip()

            # ✅ Extract Physical Stats
            stats_mapping = {
                "Height": "HEIGHT",
                "Weight": "WEIGHT",
                "Reach": "REACH",
                "Leg reach": "LEG REACH"
            }
            for stat_label, stat_key in stats_mapping.items():
                stat_elem = soup.find("div", class_="c-bio__label", text=stat_label)
                if stat_elem:
                    value_elem = stat_elem.find_next_sibling("div", class_="c-bio__text")
                    if value_elem:
                        fighter_stats[stat_key] = value_elem.text.strip()

            # ✅ Extract Fight Statistics
            stats_table = {
                "Significant Strikes Accuracy": "SIGNIFICANT STRIKES ACCURACY",
                "Significant Strikes Landed": "SIG.STR. LANDED PER MIN",
                "Significant Strikes Absorbed": "SIG.STR. ABSORBED PER MIN",
                "Knockdown Avg": "KNOCKDOWN AVG/15 MIN",
                "Takedown Accuracy": "TAKEDOWN ACCURACY",
                "Takedown Defense": "TAKEDOWN DEFENSE",
                "Submission Avg": "SUBMISSION AVG/15 MIN",
                "Average fight time": "AVERAGE FIGHT TIME"
            }
            for stat_label, stat_key in stats_table.items():
                stat_elem = soup.find("div", class_="c-stat-compare__label", text=stat_label)
                if stat_elem:
                    value_elem = stat_elem.find_previous_sibling("div", class_="c-stat-compare__number")
                    if value_elem:
                        fighter_stats[stat_key] = value_elem.text.strip()

            # ✅ Extract Win Method Percentages
            method_mapping = {
                "KO/TKO": "KO/TKO %",
                "SUB": "SUBMISSION %",
                "DEC": "DECISION %"
            }
            for method_label, method_key in method_mapping.items():
                method_elem = soup.find("div", class_="c-stat-3bar__label", text=method_label)
                if method_elem:
                    value_elem = method_elem.find_next_sibling("div", class_="c-stat-3bar__value")
                    if value_elem:
                        fighter_stats[method_key] = value_elem.text.strip().split()[1].replace("(", "").replace(")", "")

    except Exception as e:
        print(f"❌ Error extracting fighter stats from {fighter_url}: {e}")

    return fighter_stats

def clean_and_save_fight_data(fight_data, config):
    """
    Cleans the fight dataset by removing duplicate columns and fixing column order before saving.

    Args:
        fight_data (DataFrame): DataFrame containing all fights.
        config (dict): Config with file path for saving.

    Returns:
        None
    """
    # ✅ Remove duplicate columns
    fight_data = fight_data.loc[:, ~fight_data.columns.duplicated()]

    # ✅ Ensure correct column order
    expected_columns = [
        "Event", "Date", "Location", "Bout", "Weight Class",
        "Red Fighter", "Blue Fighter", "Red Record", "Blue Record",
        "Red Country", "Blue Country", "Red Height", "Blue Height",
        "Red Weight", "Blue Weight", "Red Reach", "Blue Reach",
        "Red Leg Reach", "Blue Leg Reach", "Red KO/TKO %", "Blue KO/TKO %",
        "Red Submission %", "Blue Submission %", "Red Decision %", "Blue Decision %",
        "Red Average Fight Time", "Blue Average Fight Time",
        "Red Knockdown Avg/15 Min", "Blue Knockdown Avg/15 Min",
        "Red Significant Strikes Landed Per Min", "Blue Significant Strikes Landed Per Min",
        "Red Significant Strike Accuracy", "Blue Significant Strike Accuracy",
        "Red Significant Strike Absorbed Per Min", "Blue Significant Strike Absorbed Per Min",
        "Red Defense", "Blue Defense", "Red Takedown Avg/15 Min", "Blue Takedown Avg/15 Min",
        "Red Takedown Accuracy", "Blue Takedown Accuracy", "Red Takedown Defense", "Blue Takedown Defense",
        "Red Submission Avg/15 Min", "Blue Submission Avg/15 Min",
        "Red Money Line", "Blue Money Line", "Red Odds to Win by KO", "Blue Odds to Win by KO",
        "Red Odds to Win by Submission", "Blue Odds to Win by Submission",
        "Red Odds to Win by Decision", "Blue Odds to Win by Decision"
    ]

    fight_data = fight_data.reindex(columns=expected_columns, fill_value="N/A")

    # ✅ Save the cleaned dataset
    fight_data.to_csv(config["dataset/upcoming_fights_ufc_file"], index=False)
    print(f"📁 Saved cleaned fight data to {config['dataset/upcoming_fights_ufc_file']}")


# Function to filter out past events
from datetime import datetime

def filter_future_events(events):
    """
    Filters out past events and unconfirmed matchups from the events list.

    Args:
        events (list of dicts): List of event dictionaries with 'DATE' field.

    Returns:
        list: Filtered list with only valid future events.
    """
    filtered_events = []
    today = datetime.today()
    current_year = today.year  # Get the current year

    for event in events:
        try:
            # Convert date to datetime object
            event_date = datetime.strptime(event["DATE"], "%B %d, %Y")

            # Ensure the event is in the future and within the current year or beyond
            if event_date >= today and event_date.year >= current_year:

                # Exclude unconfirmed matchups (TBD vs TBD)
                if "TBD vs TBD" not in event["EVENT"]:
                    filtered_events.append(event)
                else:
                    print(f"⚠️ Skipping unconfirmed event: {event['EVENT']}")

        except ValueError:
            print(f"⚠️ Skipping event due to unknown date format: {event['DATE']}")

    return filtered_events

from datetime import datetime

def filter_future_fights(fights):
    """
    Filters out past fights and keeps only future fights.

    Args:
        fights (list of dicts): List of fight dictionaries with 'DATE' field.

    Returns:
        list: Filtered list with only future fights.
    """
    future_fights = []
    today = datetime.today()

    for fight in fights:
        try:
            fight_date = datetime.strptime(fight["DATE"], "%B %d, %Y")  # Example: "February 01, 2025"
            if fight_date >= today:
                future_fights.append(fight)

        except ValueError:
            pass  # Skip fights with unknown date format

    return future_fights



def save_progress(data_type, url, config):
    """Save progress of scraped data to prevent duplicates."""
    progress_file = config['scraped_progress_file']
    progress_entry = {
    'TYPE': data_type, 
    'URL': url, 
    'STATUS': 'Completed', 
    'TIMESTAMP': datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ✅ Corrected reference
}
    pd.DataFrame([progress_entry]).to_csv(progress_file, mode='a', header=not os.path.exists(progress_file), index=False)

# parse event details
def parse_event_details(soup):
    '''
    parse event details from soup
    includes names, urls, dates, locations of events
    clean each element in the list, removing '\n' and ' ' 
    e.g cleans '\n      Las Vegas, Nevada, USA\n' into 'Las Vegas, Nevada, USA'
    return details as a df

    arguments:
    soup (html): output of get_soup()

    returns:
    a dataframe of event details
    '''

    # create empty list to store event names and urls
    event_names = []
    event_urls = []
    event_dates = []
    event_locations = []

    # extract event name and urls
    for tag in soup.find_all('a', class_='b-link b-link_style_black'):
        event_names.append(tag.text.strip())
        event_urls.append(tag['href'])

    # extract event dates
    for tag in soup.find_all('span', class_='b-statistics__date'):
        event_dates.append(tag.text.strip())

    # extract event locations
    for tag in soup.find_all('td', class_='b-statistics__table-col b-statistics__table-col_style_big-top-padding'):
        event_locations.append(tag.text.strip())

    # remove first element of event dates and locations
    # as first element here represent an upcoming event with no stats yet
    event_dates = event_dates[1:]
    event_locations = event_locations[1:]

    # create df to store event details
    event_details_df = pd.DataFrame({
        'EVENT':event_names,
        'URL':event_urls,
        'DATE':event_dates,
        'LOCATION':event_locations
    })

    # return
    return event_details_df


# parse fight details
def parse_fight_details(soup):
    '''
    parse fight details from soup
    includes urls, and fights
    create bout from fighters' names and create event column as keys
    return a df of fight details of an event

    arguments:
    soup (html): output of get_soup()
    
    returns:
    a df of fight details
    '''
    
    # create empty list to store fight urls
    fight_urls = []
    # extract all fight detail urls for further parsing
    for tag in soup.find_all('tr', class_='b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click'):
        fight_urls.append(tag['data-link'])

    # create an empty list to store fighters in an event
    fighters_in_event = []
    # extract all fighters in an event
    for tag in soup.find_all('a', class_='b-link b-link_style_black'):
        fighters_in_event.append(tag.text.strip())

    # combine fighters in event in pairs to create fights
    fights_in_event = [fighter_a+' vs. '+fighter_b for fighter_a, fighter_b in zip(fighters_in_event[::2], fighters_in_event[1::2])]    
    
    # create df to store fights
    fight_details_df = pd.DataFrame({'BOUT':fights_in_event, 'URL':fight_urls})
    # create event column as key
    fight_details_df['EVENT'] = soup.find('h2', class_='b-content__title').text.strip()
    # reorder columns
    fight_details_df = move_columns(fight_details_df, ['EVENT'], 'BOUT', 'before')

    # return
    return fight_details_df

def parse_fight_details_ufc_com(soup, event_name, event_date, event_location, fight_url):
    """
    Parses detailed fight data from UFC.com event pages.

    Arguments:
    soup (BeautifulSoup): Parsed HTML of the fight page.
    event_name (str): Name of the UFC event.
    event_date (str): Date of the event.
    event_location (str): Location of the event.
    fight_url (str): URL of the fight.

    Returns:
    dict: A dictionary containing the fight details.
    """
    
    fight_details = {
        "EVENT": event_name,
        "DATE": event_date,
        "LOCATION": event_location,
        "BOUT": "N/A",
        "RECORD": "N/A",
        "COUNTRY": "N/A",
        "HEIGHT": "N/A",
        "WEIGHT": "N/A",
        "REACH": "N/A",
        "LEG REACH": "N/A",
        "KO/TKO %": "N/A",
        "SUBMISSION %": "N/A",
        "DECISION %": "N/A",
        "AVERAGE FIGHT TIME": "N/A",
        "KNOCKDOWN AVG/15 MIN": "N/A",
        "LANDED PER MIN": "N/A",
        "SIGNIFICANT STRIKES": "N/A",
        "ABSORBED PER MIN": "N/A",
        "DEFENSE": "N/A",
        "TAKEDOWN AVG/15 MIN": "N/A",
        "TAKEDOWN ACCURACY": "N/A",
        "TAKEDOWN DEFENSE": "N/A",
        "SUBMISSION AVG/15 MIN": "N/A",
        "ODDS": "N/A",
        "MONEY LINE": "N/A",
        "TOTAL ROUNDS": "N/A",
        "ODDS TO WIN BY KO": "N/A",
        "ODDS TO WIN BY SUBMISSION": "N/A",
        "ODDS TO WIN BY DECISION": "N/A",
        "URL": fight_url
    }

    try:
        # ✅ Extract Fighter Names
        fighters = soup.find_all("div", class_="c-listing-fight__name")
        if len(fighters) == 2:
            fighter1 = fighters[0].text.strip()
            fighter2 = fighters[1].text.strip()
            fight_details["BOUT"] = f"{fighter1} vs. {fighter2}"

        # ✅ Extract Stats
        stat_sections = {
            "MATCHUP STATS": ["RECORD", "COUNTRY", "HEIGHT", "WEIGHT", "REACH", "LEG REACH"],
            "WIN BY": ["KO/TKO %", "SUBMISSION %", "DECISION %", "AVERAGE FIGHT TIME", "KNOCKDOWN AVG/15 MIN"],
            "SIGNIFICANT STRIKES": ["LANDED PER MIN", "SIGNIFICANT STRIKES", "ABSORBED PER MIN", "DEFENSE"],
            "GRAPPLING": ["TAKEDOWN AVG/15 MIN", "TAKEDOWN ACCURACY", "TAKEDOWN DEFENSE", "SUBMISSION AVG/15 MIN"],
            "ODDS": ["ODDS", "MONEY LINE", "TOTAL ROUNDS", "ODDS TO WIN BY KO", "ODDS TO WIN BY SUBMISSION", "ODDS TO WIN BY DECISION"]
        }

        # ✅ Find each section
        for section_name, keys in stat_sections.items():
            section = soup.find("h2", string=section_name)
            if section:
                stat_values = section.find_next("div").find_all("div", class_="c-stat-compare__value")
                
                if len(stat_values) >= len(keys):  
                    for key, stat in zip(keys, stat_values):
                        fight_details[key] = stat.text.strip()

    except Exception as e:
        print(f"❌ Error parsing fight details for {fight_url}: {e}")

    return fight_details


# Asynchronous parsing of fight details
async def parse_fight_details_async(event_urls, existing_fight_urls, config):
    soups = await fetch_all_soups(event_urls)
    all_fight_details = pd.DataFrame(columns=config['fight_details_column_names'])

    for soup, url in zip(soups, event_urls):
        if soup is None:
            continue  # Skip empty soup

        try:
            fight_details_df = parse_fight_details(soup)

            # Filter out already scraped fights
            fight_details_df = fight_details_df[~fight_details_df['URL'].isin(existing_fight_urls)]

            # Only append if there are new fights
            if not fight_details_df.empty:
                all_fight_details = pd.concat([all_fight_details, fight_details_df])
        except Exception:
            pass  # Silently ignore errors

    return all_fight_details


def extract_event_urls(soup):
    """
    Extracts event URLs from UFC.com event listings.

    Args:
        soup (BeautifulSoup): Parsed HTML of the events list.

    Returns:
        list: List of event URLs.
    """
    event_urls = []
    
    event_containers = soup.find_all("div", class_="c-card-event--result__info")
    for event in event_containers:
        url_tag = event.find("a")  # Get event link
        if url_tag and "href" in url_tag.attrs:
            event_url = "https://www.ufc.com" + url_tag["href"]  # Append full domain
            event_urls.append(event_url)
    
    return event_urls

def extract_fight_urls(soup, event_url):
    """
    Extracts fight URLs from a UFC.com event page.

    Arguments:
    soup (BeautifulSoup): Parsed HTML of the event page.
    event_url (str): The main event page URL.

    Returns:
    list: A list of properly formatted fight URLs.
    """
    fight_urls = []

    fight_containers = soup.find_all("div", class_="c-listing-fight__content")

    for fight in fight_containers:
        fight_link = fight.find("a", class_="c-listing-fight__name")
        if fight_link and "href" in fight_link.attrs:
            fight_url = "https://www.ufc.com" + fight_link["href"]
        else:
            # If fight URL is missing, construct it manually using the event URL
            fight_id = fight.get("id", "unknown")
            fight_url = f"{event_url}#{fight_id}" if fight_id != "unknown" else "N/A"

        fight_urls.append(fight_url)

    return fight_urls


# parse fight results from soup
def parse_fight_results(soup):
    '''
    parase fight results from soup
    results include event, bout, outcome weightclass, method, round, time, timeformat, referee, details
    clean each element in the list, removing '\n' and ' ' 
    e.g cleans '\n      Welterweight Bout\n' into 'Welterweight Bout'
    details include description of finish or judges and scores
    judges and scores also include details of point deduction
    e.g. 'Point Deducted: Illegal Knee by Menne Tony Weeks 45 - 49.Doug Crosby 42 - 49.Jeff Mullen 44 - 49.'
    return fight results as a list

    arguments:
    soup (html): output of get_soup() parser

    returns:
    a list of fight results
    '''

    # create an empty list to store results
    fight_results = []

    # parse event name
    fight_results.append(soup.find('h2', class_='b-content__title').text)

    # parse fighters
    for tag in soup.find_all('a', class_='b-link b-fight-details__person-link'):
        fight_results.append(tag.text)

    # parse outcome as either w for win or l for loss
    for tag in soup.find_all('div', class_='b-fight-details__person'):
        for i_text in tag.find_all('i'):
            fight_results.append(i_text.text)

    # parse weightclass
    fight_results.append(soup.find('div', class_='b-fight-details__fight-head').text)

    # parse win method
    fight_results.append(soup.find('i', class_='b-fight-details__text-item_first').text)

    # parse remaining results
    # includes round, time, time format, referee, details
    remaining_results = soup.find_all('p', class_='b-fight-details__text')

    # parse round, time, time format, referee
    for tag in remaining_results[0].find_all('i', class_='b-fight-details__text-item'):
        fight_results.append(tag.text.strip())

    # parse details
    fight_results.append(remaining_results[1].get_text())

    # clean each element in the list, removing '\n' and '  ' 
    fight_results = [text.replace('\n', '').replace('  ', '') for text in fight_results]

    # return
    return fight_results



# organise fight results
def organise_fight_results(results_from_soup, fight_results_column_names):
    '''
    organise list of fight results
    fighters' names should be from index 1 and 2
    fight outcome should be from index 3 and 4
    other results includes from index 5 onwards
    weightclass, method, round, time, time format, referee, and details, should be 
    append all results into list and convert to a df

    arguments:
    results_from_soup (list): list of results from parse_fight_results()
    fight_results_column_names (list): list of column names for fight results

    returns:
    an organised list of fight results
    '''

    # create empty list to store results
    fight_results_clean = []
    # append event name
    fight_results_clean.append(results_from_soup[0])
    # join fighters name into one, e.g. fighter_a vs. fighter_b
    fight_results_clean.append(' vs. '.join(results_from_soup[1:3]))
    # join outcome as 'w/l' or 'l/w'
    fight_results_clean.append('/'.join(results_from_soup[3:5]))
    # remove label of results using regex
    # regrex, at the start of the string remove all characterts up to the first ':' 
    # remove and a single ' ', if any,  after the ':'
    fight_results_clean.extend([re.sub('^(.+?): ?', '', text) for text in results_from_soup[5:]])

    # create empty df to store results
    fight_result_df = pd.DataFrame(columns=fight_results_column_names)
    # append each round of totals stats from first half of list to totals_df
    fight_result_df.loc[len(fight_result_df)] = fight_results_clean

    # return
    return fight_result_df



# parse full fight stats for both fighters
def parse_fight_stats(soup):
    '''
    parse full fight stats for both fighters from soup
    loop through soup to find all 'td' tags with the class 'b-fight-details__table-col'
    this returns a list of stats for both fighters in alternate order
    e.g. [0, 1, 2, 2, 20, 30] stats [0, 2, 20] belong to the first fighter and [1, 2, 30] belong to the second fighter
    use enumerate to add index to results
    stats with even indexes belongs to the first fighter and odd indexes belong to the second fighter
    clean each element in the list, removing '\n' and ' ' 
    e.g cleans '\n fighter name \n' into 'fighter name' and  '\n      19 of 32\n    ' into '19 of 32'
    
    arguments:
    soup (html): output of get_soup() parser

    returns:
    two lists of fighter stats, one for each fighter
    '''

    # create empty list to store each fighter's stats
    fighter_a_stats = []
    fighter_b_stats = []

    # loop through soup to find all 'td' tags with the class 'b-fight-details__table-col'
    for tag in soup.find_all('td', class_='b-fight-details__table-col'):
        # loop through each 'td' tag and find all 'p' tags
        # this returns a list of stats for both fighters in alternate order
        # stats with even indexes belongs to the first fighter and odd indexes belong to the second fighter
        for index, p_text in enumerate(tag.find_all('p')):
            # check if index is even, if true then append to fighter_a_stats
            if index % 2 == 0:
                fighter_a_stats.append(p_text.text.strip())
            # if index is odd then append to fighter_b_stats
            else:
                fighter_b_stats.append(p_text.text.strip())

    # return
    return fighter_a_stats, fighter_b_stats



# organise stats extracted from soup
def organise_fight_stats(stats_from_soup):
    '''
    organise a list of raw stats extracted from soup
    each set of stats starts with the fighter's name, the function groups each set together into a list of lists by the fighter's name

    there are two different types of stats, totals and significant strikes
    Totals include KD, SIG.STR., SIG.STR. %, TOTAL STR., TD, TD %, SUB.ATT, REV., CTRL
    Significant Strikes include SIG.STR., SIG.STR. %, HEAD, BODY, LEG, DISTANCE, CLINCH, GROUND
    
    each type of stat has a summary of total stats for the fight, and individual round stats
    the sets of stats are returned as a list of lists
    e.g. [[totals - summary], [totals - round 1], [totals - round n]..., [significant strikes - summary], [significant strikes - round 1], [significant strikes - round n]...] 

    arguments:
    stats_from_soup (list): a list of fight stats from parse_fight_stats()

    returns: 
    a list of lists of fight stats
    '''

    # split clean stats by fighter's name into a list of list
    # each sub list represents total strike and sig strikes stats per round and totals

    # create empty list to store stats
    fighter_stats_clean = []
    # group stats by fighter's name
    for name, stats in itertools.groupby(stats_from_soup, lambda x: x == stats_from_soup[0]):
        # create empty sublist to store each set of stats
        if name: fighter_stats_clean.append([])
        # extend stats to sublist
        fighter_stats_clean[-1].extend(stats)

    # return
    return fighter_stats_clean


async def parse_fight_results_and_stats_async(fight_urls, config):
    soups = await fetch_all_soups(fight_urls)
    all_fight_results = pd.DataFrame(columns=config['fight_results_column_names'])
    all_fight_stats = pd.DataFrame(columns=config['fight_stats_column_names'])

    for soup, url in zip(soups, fight_urls):
        if soup is None:
            continue  # Skip empty soup

        try:
            fight_results_df, fight_stats_df = parse_organise_fight_results_and_stats(
                soup,
                url,
                config['fight_results_column_names'],
                config['totals_column_names'],
                config['significant_strikes_column_names']
            )

            if not fight_results_df.empty:
                all_fight_results = pd.concat([all_fight_results, fight_results_df])

            if not fight_stats_df.empty:
                all_fight_stats = pd.concat([all_fight_stats, fight_stats_df])

        except Exception as e:
            print(f"❌ Error processing {url}: {e}")

    return all_fight_results, all_fight_stats



# convert list of fighter stats into a structured dataframe
def convert_fight_stats_to_df(clean_fighter_stats, totals_column_names, significant_strikes_column_names):
    '''
    convert a list of fighter stats from organise_fight_stats() into a structured dataframe
    check if list of stats is empty, there are old fights that do not have stats
    if fight has no stats, then fill stat columns with nans
    if fight has stats continue and get number of rounds in the fight
    for each round in fight, get stats for totals and significant strikes
    the summary of stats for the fights are ignored
    merge totals and significant stike stats together and return as one df

    arguments:
    clean_fighter_stats (list): list of fighter stats from organise_fight_stats()
    totals_column_names (list): list of column names for totals type stats
    significant_strikes_column_names (list): list of column names for significant strike type stats

    returns:
    a dataframe of fight stats
    '''

    # create empty df to store each type of stat
    totals_df = pd.DataFrame(columns=totals_column_names)
    significant_strikes_df = pd.DataFrame(columns=significant_strikes_column_names)

    # check if list of stats is empty 
    # meaning that stats are unavailable for the fight
    if len(clean_fighter_stats) == 0:
        # append nans to totals_df and significant_strikes_df
        totals_df.loc[len(totals_df)] = [np.nan] * len(list(totals_df))
        significant_strikes_df.loc[len(significant_strikes_df)] = [np.nan] * len(list(significant_strikes_df))
    
    # if list of stats is no empty
    else:
        # get number of rounds in fight
        # fight stats has two summary rows and two rows of stats for each round
        # subtract two summary rows and divide the remaining rows by two to get the number of rounds
        number_of_rounds = int((len(clean_fighter_stats) - 2) / 2)

        # create empty df to store each type of stat
        totals_df = pd.DataFrame(columns=totals_column_names)
        significant_strikes_df = pd.DataFrame(columns=significant_strikes_column_names)

        # for each round in fight, get stats for totals and significant strikes
        # the first half of stats are totals type and the second half are significant strike type
        # [[totals - summary], [totals - round 1], [totals - round n]..., [significant strikes - summary], [significant strikes - round 1], [significant strikes - round n]...] 
        for round in range(number_of_rounds):
            # append each round of totals stats from first half of list to totals_df
            totals_df.loc[len(totals_df)] = ['Round '+str(round+1)] + clean_fighter_stats[round+1]
            # append each round of significant strike stats from second half of list to significant_strikes_df
            significant_strikes_df.loc[len(significant_strikes_df)] = ['Round '+str(round+1)] + clean_fighter_stats[round+1+int((len(clean_fighter_stats) / 2))]

    # merge totals and significant stike stats together as one df
    fighter_stats_df = totals_df.merge(significant_strikes_df, how='inner')

    # return
    return fighter_stats_df



# combine fighter stats into one
def combine_fighter_stats_dfs(fighter_a_stats_df, fighter_b_stats_df, soup):
    '''
    concat both fighter's stats into one df
    create new event and bout column as a key
    results in a dataframe of stats for both fighters for a fight

    arguments:
    fighter_a_stats_df (df): a df output from convert_fight_stats_to_df()
    fighter_b_stats_df (df): a df output from convert_fight_stats_to_df()
    soup (html): output of get_soup() parser

    returns
    a dataframe of stats for the fight
    '''

    # concat both fighters' stats into one df
    fight_stats = pd.concat([fighter_a_stats_df, fighter_b_stats_df])

    # get name of event from soup
    fight_stats['EVENT'] = soup.find('h2', class_='b-content__title').text.strip()

    # create empty list to store fighters' names
    fighters_names = []
    # parse fighters' name from soup
    for tag in soup.find_all('a', class_='b-link b-fight-details__person-link'):
        fighters_names.append(tag.text.strip())

    # get name of bout with using fighters' names
    fight_stats['BOUT'] = ' vs. '.join(fighters_names)

    # reorder columns
    fight_stats = move_columns(fight_stats, ['EVENT', 'BOUT'], 'ROUND', 'before')

    # return
    return fight_stats



# parse and organise fight results and fight stats
def parse_organise_fight_results_and_stats(soup, url, fight_results_column_names, totals_column_names, significant_strikes_column_names):
    '''
    parse and organise fight results and fight stats from soup
    this function combines other functions that parse fight results and stats into one
    and returns two dfs, one for fight results and the other for fight stats

    arguments:
    soup (html): output of get_soup() parser
    url (str): url of fight
    fight_results_df (df): an df
    fight_results_column_names (list): list of column names for fight results
    fight_stats_df (df):
    totals_column_names (list): list of column names for totals type stats
    significant_strikes_column_names (list): list of column names for significant strike type stats

    returns:
    two dfs for fight results and stats
    '''

    # parse fight results

    # parase fight results from soup
    fight_results = parse_fight_results(soup)
    # append fight url 
    fight_results.append('URL:'+url)
    # organise fight results
    fight_results_df = organise_fight_results(fight_results, fight_results_column_names)

    # parse fight stats

    # parse full fight stats for both fighters
    fighter_a_stats, fighter_b_stats = parse_fight_stats(soup)
    # organise stats extracted from soup
    fighter_a_stats_clean = organise_fight_stats(fighter_a_stats)
    fighter_b_stats_clean = organise_fight_stats(fighter_b_stats)
    # convert list of fighter stats into a structured dataframe
    fighter_a_stats_df = convert_fight_stats_to_df(fighter_a_stats_clean, totals_column_names, significant_strikes_column_names)
    fighter_b_stats_df = convert_fight_stats_to_df(fighter_b_stats_clean, totals_column_names, significant_strikes_column_names)
    # combine fighter stats into one
    fight_stats_df = combine_fighter_stats_dfs(fighter_a_stats_df, fighter_b_stats_df, soup)

    # return
    return fight_results_df, fight_stats_df



# generate list of urls for fighter details
def generate_alphabetical_urls():
    '''
    generate a list of alphabetical urls for fighter details
    fighter urls are split by their last name and categorised alphabetically
    loop through each character in the alphabet from a to z to parse all the urls
    return all fighter urls as a list

    arguments:
    none

    returns:
    a list of urls of fighter details
    '''
    # create empty list to store fighter urls to parse
    list_of_alphabetical_urls = []

    # fighters are split in alphabetically
    # generate url for each alphabet and append to list
    for character in list(string.ascii_lowercase):
        list_of_alphabetical_urls.append('http://ufcstats.com/statistics/fighters?char='+character+'&page=all')
    
    # return
    return list_of_alphabetical_urls



# parse fighter details
def parse_fighter_details(soup, fighter_details_column_names):
    '''
    parse fighter details from soup
    fighter details include first name, last name, nickname, and url
    returns dataframe with first, last, nickname, url

    arguments:
    soup (html): output of get_soup() parser

    returns:
    a dataframe of fighter details
    '''
    # parse fighter name
    # create empty list to store fighters' names
    fighter_names = []
    # loop through and get fighter's first name, last name, nickname
    for tag in soup.find_all('a', class_='b-link b-link_style_black'):
        # append name to fighter_names
        fighter_names.append(tag.text)

    # parse fighter url
    # create empty list to store fighters' urls
    fighter_urls = []
    # loop through and get fighter url
    for tag in soup.find_all('a', class_='b-link b-link_style_black'):
        # append url to list_of_fighter_urls
        # each tag will have three urls that are duplicated
        fighter_urls.append(tag['href'])

    # zip fighter's first name, last name, nickname, and url into a list of tuples
    # zip items in sets of threes
    # e.g. ('Tom', 'Aaron', '', 'http://ufcstats.com/fighter-details/93fe7332d16c6ad9')
    # if there is no first, last, or nickname, the field will be left blank
    fighter_details = list(zip(fighter_names[0::3], fighter_names[1::3], fighter_names[2::3], fighter_urls[0::3]))

    # convert list of tuples to a dataframe
    fighter_details_df = pd.DataFrame(fighter_details, columns=fighter_details_column_names)
    
    # return
    return fighter_details_df



# parse fighter tale of the tape
def parse_fighter_tott(soup):
    '''
    parse fighter tale of the tape from soup
    fighter details contain fighter, height, weight, reach, stance, dob
    clean each element in the list, removing '\n' and ' ' 
    e.g cleans '\n      Jose Aldo\n' into 'Jose Aldo'
    returns a list of fighter tale of the tape

    arguments:
    soup (html): output of get_soup() parser

    returns:
    a list of fighter tale of the tape
    '''
    # create empty list to store fighter tale of the tape
    fighter_tott = []

    # parse fighter name
    fighter_name = soup.find('span', class_='b-content__title-highlight').text
    # append fighter's name to fighter_tott
    fighter_tott.append('Fighter:'+fighter_name)

    # parse fighter's tale of the tape
    tott = soup.find_all('ul', class_='b-list__box-list')[0]
    # loop through each tag to get text and next_sibling text
    for tag in tott.find_all('i'):
        # add text together and append to fighter_tott
        fighter_tott.append(tag.text + tag.next_sibling)
    # clean each element in the list, removing '\n' and '  '
    fighter_tott = [text.replace('\n', '').replace('  ', '') for text in fighter_tott]
    
    # return
    return fighter_tott



# organise fighter tale of the tape
def organise_fighter_tott(tott_from_soup, fighter_tott_column_names, url):
    '''
    organise list of fighter tale of the tape
    remove label of tale of the tape using regex
    e.g. 'Height:5'7"' to '5'7"
    convert and return list as df

    arguments:
    tott_from_soup (list): list of fighter tale of the tale from parse_fighter_tott()
    fighter_tott_column_names (list): list of column names for fighter tale of the tape
    url (str): url of fighter

    results:
    a df of fighter tale of the tape
    '''
    # remove label of results using regex
    fighter_tott_clean = [re.sub('^(.+?): ?', '', text) for text in tott_from_soup]
    # append url to fighter_tott_clean
    fighter_tott_clean.append(url)
    # create empty df to store fighter's details
    fighter_tott_df = pd.DataFrame(columns=fighter_tott_column_names)
    # append fighter's details to fighter_details_df
    fighter_tott_df.loc[(len(fighter_tott_df))] = fighter_tott_clean

    # return
    return fighter_tott_df

import pandas as pd
from bs4 import BeautifulSoup

def parse_upcoming_ufc_events(soup):
    """
    Parses UFC.com upcoming events and extracts fight details.

    Arguments:
    soup (BeautifulSoup): Parsed HTML of UFC events page.

    Returns:
    DataFrame: A DataFrame containing upcoming event details.
    """
    event_names = []
    event_dates = []
    event_locations = []
    event_urls = []

    # Find all event containers
    event_containers = soup.find_all("article", class_="c-card-event--result")

    if not event_containers:
        print("⚠️ No event containers found! Check if UFC.com changed their structure.")
        return pd.DataFrame()

    for event in event_containers:
        # Extract event name
        name_tag = event.find("div", class_="c-hero--full__headline-prefix")
        event_name = name_tag.text.strip() if name_tag else "N/A"

        # Extract event date
        date_tag = event.find("div", class_="tz-change-inner")
        event_date = date_tag.text.strip() if date_tag else "N/A"

        # Extract event location (Not always present)
        location_tag = event.find("div", class_="c-card-event--result__location")
        event_location = location_tag.text.strip() if location_tag else "N/A"

        # Extract event URL
        url_tag = event.find("a", href=True)
        event_url = f"https://www.ufc.com{url_tag['href']}" if url_tag else "N/A"

        event_names.append(event_name)
        event_dates.append(event_date)
        event_locations.append(event_location)
        event_urls.append(event_url)

    # Create DataFrame
    event_df = pd.DataFrame({
        "EVENT": event_names,
        "DATE": event_dates,
        "LOCATION": event_locations,
        "URL": event_urls
    })

    return event_df



# reorder columns
def move_columns(df, cols_to_move=[], ref_col='', place=''):
    '''
    reoder columns in df
    move a list of columns before or after a reference column
    taken from https://towardsdatascience.com/reordering-pandas-dataframe-columns-thumbs-down-on-standard-solutions-1ff0bc2941d5

    arguments:
    df (df): a dataframe
    cols_to_move (list): list of columns to move
    ref_col (str): reference column on where to move list of columns
    place (str): where to place list of columns, enter 'before' or 'after'

    '''
    # get list of all columns in df
    cols = df.columns.tolist()
    
    if place == 'after':
        seg1 = cols[:list(cols).index(ref_col) + 1]
        seg2 = cols_to_move
    if place == 'before':
        seg1 = cols[:list(cols).index(ref_col)]
        seg2 = cols_to_move + [ref_col]

    seg1 = [i for i in seg1 if i not in seg2]
    seg3 = [i for i in cols if i not in seg1 + seg2]

    # return
    return(df[seg1 + seg2 + seg3])