import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re
import numpy as np

# Base AutoTrader URL
base_url = "https://www.autotrader.ca/cars/subaru/outback/bc/?rcp=15&rcs={}&srt=35&prx=-2&prv=British%20Columbia&loc=V1E%204J5&hprc=True&wcp=True&sts=New-Used&inMarket=advancedSearch"

headers = {"User-Agent": "Mozilla/5.0"}

# Scrape AutoTrader
@st.cache_data
def scrape_autotrader():
    page = 0
    all_listings = []

    while True:
        url = base_url.format(page * 15)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break  # Stop if there's an error

        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find_all("div", class_="result-item")
        if not listings:
            break  # Stop if no more listings

        for listing in listings:
            title = listing.find("h2").text.strip() if listing.find("h2") else "No title"
            
            # Extract year from title
            year_match = re.search(r"\b(19|20)\d{2}\b", title)
            year = int(year_match.group()) if year_match else None

            price = listing.find("span", class_="price-amount").text.strip() if listing.find("span", class_="price-amount") else "No price"
            mileage = listing.find("span", class_="odometer-proximity").text.strip() if listing.find("span", class_="odometer-proximity") else "No mileage"
            location = listing.find("span", class_="proximity-text overflow-ellipsis").text.strip() if listing.find("span", class_="proximity-text overflow-ellipsis") else "Unknown"
            distance = listing.find_all("span", class_="proximity-text")[1].text.strip() if len(listing.find_all("span", "proximity-text")) > 1 else "Unknown"
            seller = listing.find("div", class_="seller-name").text.strip() if listing.find("div", class_="seller-name") else "Private Seller" if listing.find("div", class_="svg_privateBadge") else "Unknown"
            link = "https://www.autotrader.ca" + listing.find("a").get("href", "") if listing.find("a") else "No link"

            all_listings.append([year, title, price, mileage, location, distance, seller, link])

        page += 1
        if page > 10:
            break

    df = pd.DataFrame(all_listings, columns=["Year", "Title", "Price", "Mileage", "Location", "Distance", "Seller", "Link"])
    df["Price"] = pd.to_numeric(df["Price"].str.replace("[\\$,]", "", regex=True), errors='coerce')
    df["Mileage"] = pd.to_numeric(df["Mileage"].str.replace("[\\ km,]", "", regex=True), errors='coerce')
    df = df.drop_duplicates().dropna(subset=["Price", "Mileage", "Year"])
    
    return df

if "car_data" not in st.session_state:
    st.session_state["car_data"] = scrape_autotrader()

df = st.session_state["car_data"]

st.title("🚗 AutoTrader Car Finder")
st.write("Find the best Subaru Outback deals in BC.")

sort_column = st.selectbox("Sort By", ["Year", "Title", "Price", "Mileage"], index=0)
sort_order = st.selectbox("Sort Order", ["Ascending", "Descending"], index=0)
ascending = True if sort_order == "Ascending" else False

year_filter = st.slider("Select Model Year Range", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
price_filter = st.slider("Max Price", 5000, 100000, 40000, step=500)
mileage_filter = st.slider("Max Mileage", 10000, 250000, 80000, step=5000)
keyword_filter = st.text_input("Keyword Filter", "")

df_filtered = df[(df["Year"] >= year_filter[0]) & (df["Year"] <= year_filter[1]) & (df["Price"] <= price_filter) & (df["Mileage"] <= mileage_filter)]

if keyword_filter:
    df_filtered = df_filtered[df_filtered["Title"].str.contains(keyword_filter, case=False, na=False)]

# Calculate median price and mileage within the filtered dataset
median_price = df_filtered["Price"].median()
median_mileage = df_filtered["Mileage"].median()

# Calculate Deal Score based on the filtered dataset
if not df_filtered.empty:
    df_filtered["Deal Score"] = ((median_price - df_filtered["Price"]) / median_price * 100) - ((df_filtered["Mileage"] - median_mileage) / median_mileage * 5)
    df_filtered = df_filtered.sort_values(by=sort_column, ascending=ascending)

st.write(f"Market Median Price: ${median_price:,.2f} | Market Median Mileage: {median_mileage:,.0f} km")
st.write(f"Showing {len(df_filtered)} cars matching your filters:")
st.dataframe(df_filtered)

st.download_button("📥 Download Listings as CSV", data=df_filtered.to_csv(index=False), file_name="autotrader_listings_filtered.csv", mime="text/csv")
