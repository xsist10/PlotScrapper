import locale

from bs4 import BeautifulSoup
import urllib3
import re

import house

regions = [
    'Devon',
    'Cornwall',
    'Herefordshire',
    'Worcestershire',
    'Warwickshire',
    'South-Wales'
]

red_flags = [
    # Common red flags we want to ignore
    "Peat bog",
    "Tenure not vacant",
    "Currently let",
    "Currently occupied",
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

    # Woodland
    # "Woodland" # (might cause issues with nearby woodland)
    "Freehold woodland",
    "Commercial woodland",
    "woodland investment",

    # Active Pasture/Agriculture phrases
    "Productive Pasture",
    "pasture land",
    "arable land",
    "pasture/arable land",
]

http = urllib3.PoolManager()
# Used to convert localized numbers to numbers
locale.setlocale(locale.LC_NUMERIC, 'en_GB')

base_url = "https://www.uklandandfarms.co.uk"


def get_properties_for_region_and_country(region, county):
    index = 1
    more_results = 1
    property_urls = []

    while more_results:
        url = "{}/Search/SearchResult.aspx?keyword=&Region={}&County={}&PageIndex={}&kw=&PropertyType=land" \
              "&Status=sale&Maxprice=1000000".format(base_url, region, county, index)
        headers = {'Cookie': 'ASP.NET_SessionId=hzxxhtfyslczsa55i1tdka45'}

        r = http.request('GET', url, headers=headers)
        page = BeautifulSoup(r.data, 'html.parser')

        links = page.select('div#propertyList ul li h3 a')
        if len(links):
            index += 1
            for link in links:
                url = link.get('href')
                # Make sure it's in a region we care about
                pattern = "(" + "|".join(regions) + ")"
                matches = re.findall(pattern, url, flags=re.IGNORECASE)
                if len(matches):
                    print("Adding " + url)
                    full_url = base_url + url
                    property_urls.append(full_url)
                else:
                    print("Skipping " + url + " based on region")
        else:
            more_results = 0

    # Get a unique list of URLs
    return list(set(property_urls))


def get_house_page(url):
    """
    Returns house object from house_url
    """

    print("Fetching " + url)
    r = http.request('GET', url)
    return BeautifulSoup(r.data, 'html.parser')


class House(house.House):

    def __init__(self, url):
        self.url = url
        self.page = get_house_page(self.url)
        self.data = {}
        self.parse_property_data()

    def parse_property_data(self):
        # Different Formats Identified:
        """
            3 acres, Long Acre, Elmstone Hardwicke, Cheltenham, GL51 9TG, Gloucestershire<br />
            For Sale -
            Guide Price £525,000<br />
        """

        """
            151.11 acres, Milton Damerel, Holsworthy, EX22, Devon<br />
            Under Offer - 
            Guide Price £2,000,000<br />
        """

        """
            63.36 acres, Straloch House, Newmachar, Aberdeenshire, AB21, Highlands and Islands<br />
            For Sale - 
            Offers Over £1,950,000<br />
        """

        """
            63.74 acres, Beards Farm Bemzells Lane, Cowbeech, East Sussex, BN27 4QN<br />
            For Sale - 
            Offers In Excess Of £1,870,000<br />
        """

        """
            5 acres, Two Garden Centres with or without Landscape Business Located In., Devon
            For Sale 
        """

        content = self.page.select_one('div#maincontent h1')
        if not content:
            print(self.page)
            exit()
        title = content.text

        # Acres
        pattern = '([0-9\.]+) acres'
        self.data['acres'] = float(re.findall(pattern, title, flags=re.IGNORECASE)[0])

        # Sale type
        # - For Sale
        # - Under Offer
        self.data['sale_type'] = 'Unknown'
        pattern = '(For Sale|Under Offer)'
        sale_type = re.findall(pattern, title, flags=re.IGNORECASE);
        if len(sale_type):
            self.data['sale_type'] = sale_type[0]

        # Pricing type
        # - Guide Price
        # - Offers In Excess
        # - Offers Over
        pattern = '(Guide Price|Offers In Excess|Offers Over|Fixed Price)'
        pricing_type = re.findall(pattern, title, flags=re.IGNORECASE)
        if len(pricing_type):
            self.data['pricing_type'] = re.findall(pattern, title, flags=re.IGNORECASE)[0]
        else:
            self.data['pricing_type'] = 'Unknown'

        # Pricing amount
        pattern = '(£[0-9,]+)'
        pricing = re.findall(pattern, title, flags=re.IGNORECASE)
        if len(pricing):
            self.data['price'] = float(locale.atof(pricing[0].replace('£', '')))
            self.data['price_per_acre'] = round(self.data['price'] / self.data['acres'], 1)
        else:
            self.data['price'] = 'POA'

    def acres(self):
        return self.data['acres']

    def guide_price(self):
        return self.data['price']

    def price_per_acre(self):
        return self.data['price_per_acre']

    def detect_red_flags(self):
        flags = []

        if self.data['sale_type'] == 'Under Offer':
            flags.append('Under Offer')

        for flag in red_flags:
            hit = self.page.find(text=re.compile(flag, re.IGNORECASE))
            if hit:
                flags.append(flag)

        return flags
