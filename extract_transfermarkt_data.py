# Copyright       : @TacticsBadger (also known as @AnalyticsGopher), member of @CPFCInsights
# Website         : TacticsNotAntics: https://tacticsnotantics.org
# Github          : https://github.com/TacticsBadger/
# Version 1.0.0   : December 05, 2021
# Current version : 1.5.0
# Last Updated    : February 05, 2024

'''
Brief: Scrape data from Transfermarkt for any given team.
'''
import sys
import re
import requests
import pandas as pd
import seaborn as sns
import plotly as py
import matplotlib as plt
import unicodedata as ud
from string import printable
from bs4 import BeautifulSoup

print("*************************** Tactics Not Antics *************************")
print("*************           Transfermarkt Data Extractor      **************")
print("*************        Version 1.0.0: December  05, 2021    **************")
print("*************        Version 1.5.0: February  05, 2024    **************")
print("*************        Last Update  : February  05, 2024    **************")
print("************************************************************************") 
"""
To make the request to the page we have to inform the website that we are a browser and that is why we use the headers variable
"""
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

# define some variables we will need later
thousands_1 = "Th"
thousands_2 = "k"
noprice = "-"

# List of clubs - TODO - read the data from a separate file so I can just get all the info at the same time for all the teams
# NOTE: the link for the Transfermarkt team MUST be in the DETAILED view - you will know this by the keywords in the link:
# kader; plus/1
# Example: https://www.transfermarkt.co.uk/luton-town/kader/verein/1031/saison_id/2023/plus/1
PL_market_values = input("*** Input in the Transfermarkt link for the club:")

# due to some changes between Python 2 and >3
if sys.version_info[0] >= 3:
    unicode = str

# necessary for names that have accents
def remove_accents(input_str):
    nkfd_form = ud.normalize('NFKD', unicode(input_str))
    return u"".join([c for c in nkfd_form if not ud.combining(c)])

# remove diacritics
def rmdiacritics(char):
    '''
    Return the base character of char, by "removing" any
    diacritics like accents or curls and strokes and the like.
    '''
    desc = ud.name(char)
    cutoff = desc.find(' WITH ')
    if cutoff != -1:
        desc = desc[:cutoff]
        try:
            char = ud.lookup(desc)
        except KeyError:
            pass  # removing "WITH ..." produced an invalid name
    return char
	
"""
Now we will create a BeautifulSoup object from our object_response.
The 'html.parser' parameter represents which parser we will use when creating our object,
a parser is a software responsible for converting an entry to a data structure.
"""
# In the page_response variable we will download the web page
page_response = requests.get(PL_market_values, headers=headers)
page_bs = BeautifulSoup(page_response.content, 'html.parser')
player_names  = [] # List that will receive all the players names
player_prices = [] # List that will receive all the players prices

# The find_all () method returns the occurences of whatever is between the parantheses
# Get all the players
tags_players = page_bs.find_all("td", {"class": "hauptlink"})
# Get their market values
tags_prices = page_bs.find_all("td", {"class": "rechts hauptlink"})
# Get the player links
tags_links = page_bs.find_all('a', href=True)

# let's get the player profiles for every player
# we'll need to do some manipulation to get the correct links
# as they're missing the first part (https://www.transfermarkt.co.uk")
list_links_raw = []
final_links = []
for link in tags_links:
    list_links_raw.append(link['href'])
for item in range(len(list_links_raw)):
    if "/profil/spieler" in list_links_raw[item]:
        clean_link = "https://www.transfermarkt.co.uk" + list_links_raw[item]
        final_links.append(clean_link)      

# We need to clean up the prices because they have currency symbols and if the value is < 1 million, it will have
# either "k" or "Th" added after the price.
for tag_price in tags_prices:
    price_text = tag_price.text
    # The price text contains characters that we don’t need like £ (pounds) or € (euros) and m (million) so we’ll remove them.
    # Feb 05, 2024 - it seems that even the .co.uk website now has the values default in Euros, instead of pounds
    price_text = price_text.replace("£", "").replace("m","").replace("€", "")
    if thousands_1 in price_text:
       price_text = price_text.replace("Th.","")
       price_text = "0." + price_text
    if thousands_2 in price_text:
       price_text = price_text.replace("k","")
       price_text = "0." + price_text
    # We will now convert the value to a numeric variable (float)
    if noprice in price_text:
       price_text = "0."
    numerical_price = float(price_text)
    player_prices.append(numerical_price)

# Now we will get only the names of all players
for tag_player in tags_players:
    txt = tag_player.text
    # Remove accents to avoid issues with displaying them
    unaccented_name = remove_accents(txt)
    # By default when scraping the data the names have dashes, empty spaces, and return symbols
    clean_name = unaccented_name.replace('-',"")
    clean_name = clean_name.replace("\n","")
    clean_name = clean_name.strip()
    player_names.append(clean_name)	
del player_names[1::2]

# The bulk of the data is in the "zentriert" class
lots_of_data = page_bs.find_all("td", {"class": "zentriert"})
i=0
# breakdown of lots_of_data: 
# index 1: shirt nr; 
# index 2: date of birth; 
# index 3: empty (nationality flag); 
# index 4: height; 
# index 5: foot; 
# index 6: date joined; 
# index 7: empty (club player arrived from); 
# index 8: contract expiry

index_match_player_numbers=1
index_match_height=4
index_match_foot=5
index_match_date_joined=6
index_match_contract_expiry=8

player_numbers = []
player_heights = []
player_foot = []
player_date_joined = []
player_contract_expiry = []

# clean up the data to add to a dataframe
dash="-"
for data in lots_of_data:
     i=i+1
     linestring = data.text.splitlines()
     dataline = ''.join(str(e) for e in linestring)
     if dash in dataline or set(dataline).difference(printable): # the condition after "or" is necessary if there are special characters but the column appears empty on the website
        dataline="not assigned"
     if i == index_match_player_numbers:
        if not dataline:
            dataline = "not assigned"
        player_numbers.append(dataline)
        index_match_player_numbers=i+8
     if i == index_match_height:
        if not dataline:
            dataline == "not assigned"
        else:
            dataline = dataline.replace(",","").replace("m","").strip()
        player_heights.append(dataline)
        index_match_height=i+8
     if i == index_match_foot:
        if not dataline:
            dataline = "not assigned"
        player_foot.append(dataline)
        index_match_foot=i+8
     if i == index_match_date_joined:
        if not dataline:
            dataline = "not assigned"
        player_date_joined.append(dataline)
        index_match_date_joined=i+8
     if i == index_match_contract_expiry:
        if not dataline:
            dataline = "not assigned"
        player_contract_expiry.append(dataline)
        index_match_contract_expiry=i+8

# Create the dataframe
df = pd.DataFrame({"Player Name":player_names,"Player #":player_numbers,"Player Height(cm)":player_heights, "Preferred Foot": player_foot, "Market Val(EUR)":player_prices, "Player Date Joined": player_date_joined, "Contract Expiration Date": player_contract_expiry, "Player Profile": final_links})

# Add an Entry column
df.insert(0, 'Entry', range(1, 1 + len(df)))

# Printing our gathered data, with headers but no index
print(df)
df.to_csv('TransferMarkt_Data.csv', mode="w", header=True, index=False, encoding='utf-8')