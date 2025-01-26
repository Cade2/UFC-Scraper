# UFC-Scraper
Scrapes UFC data 

Step-by-Step Instructions for Using the Fighter Details Scraper

This guide will help you set up and use the Fighter Details Scraper to collect data from multiple websites.

Prerequisites
Python Environment: Ensure you have Python 3.8 or later installed on your system.
Install Required Libraries:
Open a terminal and run the following command to install the necessary libraries:
pip install requests beautifulsoup4 pandas

Prepare a Dataset:
Create a CSV file with a column named Name that lists the fighter names you want to scrape.
Example:
Name
Conor McGregor
Khabib Nurmagomedov
Jon Jones
Save the file as fighter_names.csv (or any preferred name).

How to Use the Scraper
1. Set Up Logging
The scraper logs progress, errors, and other messages to the console. No additional setup is required for logging.
2. Run the Script
Open the script in a Jupyter Notebook or a Python IDE.
Uncomment the following line in the script to activate the scraping process:

scrape_from_dataset_parallel("fighter_names.csv", threads=4)

Replace fighter_names.csv with the path to your dataset if it is stored elsewhere.
Adjust the threads parameter (default is 4) to increase or decrease parallel processing threads based on your system's capability.

3. Start Scraping
Run the script. The scraper will:
Attempt to scrape details for each fighter from the following websites, in order of priority:
UFC Stats
MMA Decisions
Tapology

Save the results to a CSV file named scraped_fighter_details.csv in the current directory.

Understanding the Output

The output CSV file will have the following columns:

| FIGHTER          | HEIGHT  | WEIGHT    | REACH  | STANCE   | DOB       | Source     | Error             |
|-------------------|---------|-----------|--------|----------|-----------|-------------|
| Conor McGregor   | 5'9"    | 155 lbs   | 74"    | Southpaw | 1988-07-14 | UFC Stats   |                   |
| Khabib Nurmagomedov | 5'10" | 155 lbs   | 70"    | Orthodox | 1988-09-20 | MMA Decisions |                   |
| Unknown Fighter  |         |           |        |          |           | Tapology    | Incomplete data   |

Column Explanation
FIGHTER: Name of the fighter.
HEIGHT, WEIGHT, REACH, STANCE, DOB: Scraped data.
Source: The website where the data was retrieved.
Error: If an error occurred, it will be logged here.

Troubleshooting
No Data Found:
If the fighter's name cannot be found on any website, the row will include Incomplete data in the Error column.

Connection Issues:
Ensure you have an active internet connection.
Retry if scraping fails due to temporary server issues.

Customizing Search:
If fighter names in your dataset use unconventional spellings, adjust them manually for better results.

Advanced Usage
Customize the Script
Modify Scraping Order:

Change the order of website priority in the scrape_fighter_details function to fit your preferences.
Adjust Thread Count:
Increase the threads parameter for faster scraping on powerful machines.
Run Single Scraping Tests

Test scraping for a single fighter by running:
scrape_fighter_details("Conor McGregor")