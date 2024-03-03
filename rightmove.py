import locale

from bs4 import BeautifulSoup
import urllib3
import re
import json

import house

regions = {
    'Devon': 'REGION^61297',
    'Cornwall': 'REGION^61294',
    'Herefordshire': 'REGION^61304',
    'Worcestershire': 'REGION^61329',
    'Warwickshire': 'REGION^61327',
    'South Wales': 'REGION^91990',
    'Swindon':  'USERDEFINEDAREA%5E%7B%22polylines%22%3A%22%7BufzHbvjJetAsst%40vyNpkHldQaqC%3Fdcx%40_j%5EaiG%22%7D',
    'Bristol':  'USERDEFINEDAREA%5E%7B%22polylines%22%3A%22wkmzHhitNxmfA%60icB%7EvKirzAgkCmjq%40ivLqwPulMngKwnd%40eyf%40ydM%7C%7DuA%22%7D',
}

red_flags = [
    # Common red flags we want to ignore
    "Under Offer",
    "Peat bog",
    "Blanket bog",
    "Tenure not vacant",
    "Grade 1",
    "Grade 2",
    "SSSI",

    # Selling to build houses. We can ignore (will probably be caught by the size requirements)
    "Plot for sale",
    "Building Plot",
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

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 8_7_6; en-US) Gecko/20100101 Firefox/60.3'}

http = urllib3.PoolManager()
# Used to convert localized numbers to numbers
locale.setlocale(locale.LC_NUMERIC, 'en_GB')


def get_house_urls(region):
    """
    Returns a list of URLs of houses from a region
    """

    search_url = "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier={}" \
          "&radius=0.0&currencyCode=GBP" \
          "&maxPrice=150000&numberOfPropertiesPerPage=499&propertyTypes=land&mustHave=&dontShow=" \
          "&furnishTypes=&maxDaysSinceAdded=14&keywords=".format(region)

    print(f"Polling RightMove: {search_url}")

    r = http.request('GET', search_url, headers=headers)
    property_links = set()
    page = BeautifulSoup(r.data, 'html.parser')
    property_links_objs = page.find_all('a', class_='propertyCard-link')
    for property_links_obj in property_links_objs:
        if property_links_obj.get("href"):
            parts = property_links_obj["href"].split('?')
            property_links.add("https://www.rightmove.co.uk" + parts[0])

    return list(property_links)


def get_house_page(house_url):
    """
    Returns house object from house_url
    """

    r = http.request('GET', house_url, headers=headers)
    house = BeautifulSoup(r.data, 'html.parser')

    return house


class House(house.House):

    def __init__(self, url):
        self.url = url
        self.page = get_house_page(self.url)
        self.data = self.property_data()

    def property_data(self):
        # Find the JSON blob on the page
        data_node = self.page.find('script', text=re.compile('window.PAGE_MODEL'))
        if not data_node:
            return None

        # Extract the JSON blob
        pattern = 'window.PAGE_MODEL = (.*)'
        payload = re.findall(pattern, data_node.text, flags=re.IGNORECASE)
        return json.loads(payload[0])

    def property_type(self):
        return self.data['analyticsInfo']['analyticsProperty']['propertyType']

    def sqft(self):
        for size in self.data['propertyData']['sizings']:
            if size['unit'] == 'sqft':
                return size['maximumSize']
        return None

    def sqm(self):
        for size in self.data['propertyData']['sizings']:
            if size['unit'] == 'sqm':
                return size['maximumSize']
        return None

    def acres(self):
        for size in self.data['propertyData']['sizings']:
            if size['unit'] == 'ac':
                return size['maximumSize']

        # Use Square Meter Conversion
        if self.sqm():
            return round(self.sqm() / 4046.85642, 2)

        # Use Square Feet Conversion
        if self.sqft():
            return round(self.sqft() * 0.0026598201911744, 2)

        return -1

    def guide_price(self):
        price = self.data['propertyData']['prices']['primaryPrice']
        if price == 'POA':
            return price

        return locale.atof(price.replace('£', ''))

    def price_per_acre(self):
        return round(self.guide_price() / self.acres(), 1)

    def detect_red_flags(self):
        flags = []

        for flag in red_flags:
            hit = self.page.find(text=re.compile(flag, re.IGNORECASE))
            if hit:
                flags.append(hit)

        return flags
