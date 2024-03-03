import webbrowser

import addland
import rightmove
import uklandandfarms


def examine_houses(houses):
    for house in houses:
        print(house.url)
        # Focused on properties between 15 and 150 acres
        # This excludes a lot of building plots due to size
        if house.acres() < 50 or house.acres() > 150:
            print(f" - Skipped due to size of property: {house.acres()}")
            continue

        # We skip POA (since they're a pain to get) and anything that costs more than 10,000 GBP per acre
        if house.guide_price() == 'POA' or house.price_per_acre() > 5000:
            print(f" - Skipped due to price per acre: {house.price_per_acre()}")
            continue

        # Exclude any properties with red flags. This is a bit fuzzy and might exclude
        if len(house.detect_red_flags()):
            print(" - Skipped due to red flags:")
            print(house.detect_red_flags())
            continue

        # print(house.URL)
        webbrowser.open(house.url, new=2, autoraise=True)
        print(house.data)
        print()


def examine_add_land():
    addland.setup()
    houses = []
    for region in addland.regions:
        print(f"Examining Region {region}....")

        print("Polling AddLand")
        houses = addland.get_list_of_properties(region)
        print(f"Found {len(houses)} properties to examine")
        examine_houses(houses)
    addland.shutdown()


def examine_uklandandfarms():
    houses = []
    urls = uklandandfarms.get_properties_for_region_and_country('', '')
    for url in urls:
        house = uklandandfarms.House(url)
        if not house.invalid:
            houses.append(house)
    examine_houses(houses)


def examine_rightmove():
    for region, code in rightmove.regions.items():
        houses = []
        print(f"Examining Region {region}....")
        urls = rightmove.get_house_urls(code)

        print(f"Found {len(urls)} properties to examine")
        for url in urls:
            houses.append(rightmove.House(url))
        examine_houses(houses)


if __name__ == '__main__':
    examine_add_land()
    examine_uklandandfarms()
    examine_rightmove()
