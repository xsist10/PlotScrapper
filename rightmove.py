import locale

from bs4 import BeautifulSoup
import urllib3
import re
import json

import house

regions = {
    'Devon':          'REGION^61297',
    'Cornwall':       'REGION^61294',
    'Herefordshire':  'REGION^61304',
    'Worcestershire': 'REGION^61329',
    'Warwickshire':   'REGION^61327',
    'South Wales':    'REGION^91990',
}

red_flags = [
    # Common red flags we want to ignore
    "Under Offer",
    "Peat bog",
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

http = urllib3.PoolManager()
# Used to convert localized numbers to numbers
locale.setlocale(locale.LC_NUMERIC, 'en_GB')

def get_house_page(house_url):
    """
    Returns house object from house_url
    """

    headers = {'USer-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}

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
