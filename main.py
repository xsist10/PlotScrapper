import rightmove_webscraper
import webbrowser
import scrapper

regions = {
    'Cornwall':       'REGION^61294',
    'Devon':          'REGION^61297',
    'Herefordshire':  'REGION^61304',
    'Worcestershire': 'REGION^61329',
    'Warwickshire':   'REGION^61327',
    'South Wales':    'REGION^91990',
}

if __name__ == '__main__':
    for region, code in regions.items():
        print(f"Examining Region {region}....")
        url = "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier={}" \
              "&maxPrice=150000&numberOfPropertiesPerPage=499&propertyTypes=land&mustHave=&dontShow" \
              "=&furnishTypes=&maxDaysSinceAdded=14&keywords=".format(code)
        rm = rightmove_webscraper.RightmoveData(url)
        properties = rm.get_results.values.tolist()

        # Get a unique list of URLs
        urls = list(set(map(lambda a: a[3], properties)))

        print(f"Found {len(urls)} properties to examine")

        for url in urls:
            # print(url)
            house = scrapper.House(url)

            # Focused on properties between 15 and 150 acres
            # This excludes a lot of building plots due to size
            if house.acres() < 15 or house.acres() > 150:
                # print(f"Skipped due to size of property: {house.acres()}")
                continue

            # We skip POA (since they're a pain to get) and anything that costs more than 10,000 GBP per acre
            if house.guide_price() == 'POA' or house.price_per_acre() > 10000:
                # print(f"Skipped due to price per acre: {house.price_per_acre()}")
                continue

            # Exclude any properties with red flags. This is a bit fuzzy and might exclude
            if len(house.detect_red_flags()):
                # print("Skipped due to red flags:")
                # print(house.detect_red_flags())
                continue

            print(url)
            webbrowser.open(url, new=2, autoraise=True)
            print(house.data)
            print()
