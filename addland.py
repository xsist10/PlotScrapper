import locale
import random
import string
import time

from bs4 import BeautifulSoup
import re
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import addland
import house

# Used to convert localized numbers to numbers
locale.setlocale(locale.LC_NUMERIC, 'en_GB')

land_types = [
    2,
    6,
    9,
    11,
    1,
    7,
    13,
    3,
    300
]

regions = [
    'Devon',
    'Cornwall',
    'Herefordshire',
    'Wales',
    'Warwickshire',
    'Worcestershire',
]

# Different from rightmove due to terminology and static links on the site
red_flags = [
    # Common red flags we want to ignore
    "Under Offer",
    "Peat bog",
    "Tenure not vacant",
    "Grade 1",
    "Grade 2",
    "SSSI",

    # Selling to build houses. We can ignore (will probably be caught by the size requirements)
    "with planning permission",

    # Commoner Rights exclusion phrases
    "Commoners Rights",
    "Common Land",

    # Active Pasture/Agriculture phrases
    "Productive Pasture",
    "pasture land",
    "arable land",
    "pasture/arable land",
]

base_url = "https://addland.com"
county_filter = "placeType=County&query={}&radius=0"
size_filter = "maxSize=150&minSize=50"
additional_filters = "dropdowns=720&filters=ls.3&filters=ls.4&filters=gpd.1&filters=gpd.2&filters=t.1&filters=t.3&showProListingsOnly=false"

driver = False

TIMEOUT = 30


def setup():
    options = Options()
    options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
    addland.driver = webdriver.Firefox(options=options)


def shutdown():
    if addland.driver:
        addland.driver.close()


def build_country_url(county: string):
    return "{}/land-search/{}/?{}&{}&{}&{}".format(
        base_url,
        urllib.parse.quote_plus(county.lower()),
        county_filter.format(urllib.parse.quote_plus(county.lower().title())),
        size_filter,
        "&".join(map(lambda x: f"landTypes={x}", land_types)),
        additional_filters
    )


def build_property_url(parts: string):
    return "{}{}".format(
        base_url,
        parts
    )


def get_list_of_properties(county: string):
    url = build_country_url(county)
    print(url)

    driver.get(url)
    try:
        # Wait around until we see LandCards
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "LandCards_link"))
        )
    finally:
        pass

    page = BeautifulSoup(driver.page_source, 'html.parser')

    # Skip if no matches were found. Ignore the "suggestions".
    no_results = page.find('span', class_='ResultsPanelList_noResults')
    if no_results:
        print("Skipping region as no results were found")
        return [];

    houses = []
    links = page.find_all('a', class_='LandCards_link')
    for link in links:
        house = House(build_property_url(link['href']))
        houses.append(house)

    return houses


def get_property_page(property_url):
    """
    Returns json object from house_URL
    """

    driver.get(property_url)
    try:
        # Wait around until we see LandCards
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "LandDetailSummary"))
        )
    finally:
        pass

    time.sleep(random.randrange(4))
    return BeautifulSoup(driver.page_source, 'html.parser')


class House(house.House):

    def __init__(self, URL):
        self.URL = URL
        self.page = get_property_page(self.URL)
        self.data = self.extract_details()

    def extract_details(self):
        # Details are tuples
        details = self.page.find_all('span', class_='LandDetailSummary_detail')
        data = dict()
        for index in range(0, int(len(details) / 2)):
            data[details[index * 2].text] = details[index * 2 + 1].text.strip()

        return data

    def property_type(self):
        return self.data['Type']

    def acres(self):
        pattern = '([0-9\.]*) Acres'
        payload = re.findall(pattern, self.data['Size'], flags=re.IGNORECASE)
        return float(payload[0])

    def guide_price(self):
        price = self.page.find('span', class_='LandDetailSummary_guidePrice').text.strip()

        # POA we just assume is unaffordable
        if price == 'POA' or price == 'Sold':
            return 9999999999

        return float(locale.atof(price.replace('£', '')))

    def price_per_acre(self):
        return round(self.guide_price() / self.acres(), 1)

    def detect_red_flags(self):
        flags = []

        for flag in red_flags:
            hit = self.page.find(text=re.compile(flag, re.IGNORECASE))
            if hit:
                flags.append(hit)

        return flags
