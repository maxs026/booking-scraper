import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time

# --- Streamlit Interface ---
st.write("Code mis à jour le 28 novembre 2024")
st.set_page_config(page_title="Booking Scraper", page_icon="🏨", layout="wide")
st.title("🏨 Booking Scraper")
st.subheader("Scraper des données directement depuis Booking.com")

# --- Function to Generate Booking.com URL ---
def generate_booking_url(location, stars=None):
    base_url = "https://www.booking.com/searchresults.html"
    params = {"ss": location, "lang": "en-us"}
    if stars:
        params["nflt"] = f"class%3D{stars}"
    return f"{base_url}?{urlencode(params)}"

# --- Function to Scrape Booking Data ---
def scrape_booking(url, max_pages=1):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5"
    }
    hotels = []
    for page in range(max_pages):
        paginated_url = f"{url}&offset={page * 25}"
        response = requests.get(paginated_url, headers=headers)
        if response.status_code != 200:
            st.error(f"Erreur lors de la connexion à Booking.com (code {response.status_code})")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        for hotel in soup.select(".sr_property_block_main_row"):
            try:
                name = hotel.select_one(".sr-hotel__name").text.strip()
                address = hotel.select_one(".bui-card__subtitle").text.strip() if hotel.select_one(".bui-card__subtitle") else "N/A"
                rating = hotel.select_one(".bui-review-score__badge").text.strip() if hotel.select_one(".bui-review-score__badge") else "N/A"
                hotels.append({"Name": name, "Address": address, "Rating": rating})
            except Exception as e:
                print(f"Error parsing hotel: {e}")
                continue
        
        time.sleep(2)

    return pd.DataFrame(hotels)

# --- Sidebar ---
st.sidebar.title("🏨 Options de recherche")
search_location = st.sidebar.text_input("Ville ou région :", "Paris")
stars = st.sidebar.selectbox("Filtrer par étoiles :", [None, 1, 2, 3, 4, 5], index=0)
max_pages = st.sidebar.slider("Nombre de pages à scraper :", 1, 5, 1)

# --- Main Section ---
if st.sidebar.button("Rechercher et scraper"):
    st.info("Création du lien Booking.com...")
    booking_url = generate_booking_url(search_location, stars)

    st.markdown(f"🔗 **Lien Booking généré :** [Cliquez ici pour voir les résultats sur Booking.com]({booking_url})")

    st.warning("Scraping des données en cours...")
    data = scrape_booking(booking_url, max_pages)

    if not data.empty:
        st.success(f"Scraping terminé avec succès : {len(data)} hôtels trouvés.")
        st.dataframe(data)

        st.download_button(
            label="Télécharger les résultats en CSV",
            data=data.to_csv(index=False),
            file_name="hotels.csv",
            mime="text/csv",
        )
    else:
        st.error("Aucun hôtel trouvé. Vérifiez les filtres ou essayez une autre recherche.")