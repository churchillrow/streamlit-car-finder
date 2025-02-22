import requests
from bs4 import BeautifulSoup

# Base AutoTrader URL for Subaru Outback in BC
base_url = "https://www.autotrader.ca/cars/subaru/outback/bc/?rcp=15&rcs={}&srt=35&prx=-2&prv=British%20Columbia&loc=V1E%204J5&hprc=True&wcp=True&sts=New-Used&inMarket=advancedSearch"

headers = {"User-Agent": "Mozilla/5.0"}

page = 0  # Start from page 1
listings_found = 0  # Track total listings found

while True:
    url = base_url.format(page * 15)  # Adjust "rcs" for pagination
    print(f"Scraping page {page + 1}: {url}")

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all car listings
    listings = soup.find_all("div", class_="result-item")

    if not listings:
        print("No more listings found. Stopping scraper.")
        break

    for listing in listings:
        title = listing.find("h2").text.strip() if listing.find("h2") else "No title"

        # 🔹 Extract price
        price = "No price"
        price_element = listing.find("span", class_="price-amount")
        if price_element:
            price = price_element.text.strip()

        # 🔹 Extract mileage
        mileage = "No mileage"
        mileage_element = listing.find("span", class_="odometer-proximity")
        if mileage_element:
            mileage = mileage_element.text.strip()

        # 🔹 Extract location (first proximity-text)
        location = "Unknown"
        location_element = listing.find("span", class_="proximity-text overflow-ellipsis")
        if location_element:
            location = location_element.text.strip()

        # 🔹 Extract distance (skip first proximity-text element)
        distance = "Unknown"
        proximity_elements = listing.find_all("span", class_="proximity-text")
        if len(proximity_elements) > 1:
            distance = proximity_elements[1].text.strip()  # Second occurrence is the distance

        # 🔹 Extract seller type (Dealer/Private)
        seller = "Unknown"
        seller_element = listing.find("div", class_="seller-name")  # Dealer name
        private_element = listing.find("div", class_="svg_privateBadge")  # Private seller badge

        if seller_element:
            seller = seller_element.text.strip()  # Dealer name
        elif private_element:
            seller = "Private Seller"

        # Extract the car listing link
        link_tag = listing.find("a", href=True)
        link = "https://www.autotrader.ca" + link_tag["href"] if link_tag else "No link"

        print(f"Title: {title}\nPrice: {price}\nMileage: {mileage}\nLocation: {location}\nDistance: {distance}\nSeller: {seller}\nLink: {link}\n")

        listings_found += 1  # Count listings

    page += 1  # Move to the next page