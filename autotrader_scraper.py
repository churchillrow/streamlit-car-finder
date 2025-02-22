import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re  # To extract the year from titles

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
            distance = listing.find_all("span", class_="proximity-text")[1].text.strip() if len(listing.find_all("span", class_="proximity-text")) > 1 else "Unknown"
            seller = listing.find("div", class_="seller-name").text.strip() if listing.find("div", class_="seller-name") else "Private Seller" if listing.find("div", class_="svg_privateBadge") else "Unknown"
            link = "https://www.autotrader.ca" + listing.find("a").get("href", "") if listing.find("a") else "No link"

            all_listings.append([year, title, price, mileage, location, distance, seller, link])

        page += 1  # Next page
        if page > 10:
            break

    df = pd.DataFrame(all_listings, columns=["Year", "Title", "Price", "Mileage", "Location", "Distance", "Seller", "Link"])

    # Convert price and mileage to numeric
    df["Price"] = pd.to_numeric(df["Price"].str.replace("[\$,]", "", regex=True), errors='coerce')
    df["Mileage"] = pd.to_numeric(df["Mileage"].str.replace("[\ km,]", "", regex=True), errors='coerce')
# ✅ REMOVE DUPLICATES
    df = df.drop_duplicates()  # Remove exact duplicate rows
    df = df.drop_duplicates(subset=["Title", "Price", "Mileage", "Seller", "Link"])  # Remove similar duplicates

    return df.dropna(subset=["Price", "Mileage", "Year"])  # Remove rows with missing values


### ✅ Store Scraped Data in `st.session_state`
if "car_data" not in st.session_state:
    st.session_state["car_data"] = scrape_autotrader()

df = st.session_state["car_data"]

# 🚗 **Streamlit Web App UI**
st.title("🚗 AutoTrader Car Finder")
st.write("Find the best Subaru Outback deals in BC.")

# 🏷 **Sorting Dropdowns**
sort_column = st.selectbox("Sort By", ["Year", "Title", "Price", "Mileage"], index=0)
sort_order = st.selectbox("Sort Order", ["Ascending (A-Z / Low-High)", "Descending (Z-A / High-Low)"], index=0)

# 🏷 **Apply Sorting**
ascending = True if sort_order == "Ascending (A-Z / Low-High)" else False
df = df.sort_values(by=sort_column, ascending=ascending)

# 🚘 **Year Filter**
min_year = int(df["Year"].min()) if not df["Year"].isnull().all() else 2000
max_year = int(df["Year"].max()) if not df["Year"].isnull().all() else 2025
year_filter = st.slider("Select Model Year Range", min_year, max_year, (min_year, max_year))

# 💰 **Price Filter**
price_filter = st.slider("Max Price", 5000, 100000, 40000, step=500)

# ⏳ **Mileage Filter**
mileage_filter = st.slider("Max Mileage", 10000, 250000, 80000, step=5000)

# 🏢 **Seller Type Filter**
seller_filter = st.radio("Seller Type", ["All", "Dealer", "Private Seller"])

# **Apply Filters**
filtered_df = df[
    (df["Year"] >= year_filter[0]) & (df["Year"] <= year_filter[1]) &
    (df["Price"] <= price_filter) &
    (df["Mileage"] <= mileage_filter)
]

if seller_filter == "Dealer":
    filtered_df = filtered_df[~filtered_df["Seller"].str.contains("Private Seller", na=False)]
elif seller_filter == "Private Seller":
    filtered_df = filtered_df[filtered_df["Seller"].str.contains("Private Seller", na=False)]

# **Show results**
st.write(f"Showing {len(filtered_df)} cars matching your filters:")
st.dataframe(filtered_df)

# **Download CSV Button**
st.download_button("📥 Download Listings as CSV", data=filtered_df.to_csv(index=False), file_name="autotrader_listings.csv", mime="text/csv")
