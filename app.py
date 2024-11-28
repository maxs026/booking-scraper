import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from urllib.parse import urlencode
import matplotlib.pyplot as plt

# Streamlit Configuration
st.set_page_config(page_title="Booking Scraper", page_icon="🏨", layout="wide")
st.title("🏨 Booking Scraper")
st.markdown("### Scraper, nettoyer et analyser des données directement depuis Booking.com")
st.markdown("---")

# Function to generate Booking URL
def generate_booking_url(location, stars=None):
    base_url = "https://www.booking.com/searchresults.html"
    params = {"ss": location, "lang": "en-us"}
    if stars:
        params["nflt"] = f"class%3D{stars}"
    return f"{base_url}?{urlencode(params)}"

# Function to scrape hotel data
def scrape_booking(url, max_pages=1):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5"
    }
    hotels = []

    for page in range(max_pages):
        paginated_url = f"{url}&offset={page * 25}"  # Adjust for pagination
        response = requests.get(paginated_url, headers=headers)

        if response.status_code != 200:
            st.error(f"Erreur lors de la connexion à Booking.com (code {response.status_code})")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse hotels
        for hotel in soup.select('div[data-testid="property-card"]'):
            try:
                name = hotel.select_one('a[data-testid="title-link"]').text.strip()
                address = hotel.find_next("div", class_="aee5343fdb").text.strip() if hotel.find_next("div", class_="aee5343fdb") else "N/A"
                description = hotel.find_next("div", class_="abf093bdfe").text.strip() if hotel.find_next("div", class_="abf093bdfe") else "N/A"
                rating = hotel.find_next("div", class_="a3b8729ab1").text.strip() if hotel.find_next("div", class_="a3b8729ab1") else "N/A"
                image_url = hotel.find_next("img", class_="f9671d49b1")["src"] if hotel.find_next("img", class_="f9671d49b1") else "N/A"

                # Clean up the rating
                if "Scored" in rating:
                    rating = rating.split()[1]

                hotels.append({
                    "Name": name,
                    "Address": address,
                    "Rating": rating,
                    "Description": description,
                    "Image URL": image_url
                })
            except Exception:
                continue  # Skip problematic entries

    return pd.DataFrame(hotels)

# Function for cleaning data
def clean_data(df):
    # Drop unnecessary columns
    df = df.dropna(how='all', axis=1)  # Remove empty columns
    df = df.dropna(how='all', axis=0)  # Remove empty rows

    # Clean specific columns
    if "Name" in df.columns:
        df["Name"] = df["Name"].str.replace("Opens in new window", "").str.strip()
    if "Rating" in df.columns:
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")  # Convert ratings to numbers
    if "Address" in df.columns:
        df["Address"] = df["Address"].fillna("Adresse inconnue")
    if "Description" in df.columns:
        df["Description"] = df["Description"].fillna("Pas de description")

    # Add classification column based on rating
    if "Rating" in df.columns:
        df["Classification"] = pd.cut(
            df["Rating"],
            bins=[0, 5, 7, 8.5, 10],
            labels=["Médiocre", "Correct", "Bien", "Excellent"],
            include_lowest=True,
        )

    return df

# Sidebar configuration
st.sidebar.title("🏨 Options de recherche")
search_location = st.sidebar.text_input("Ville ou région :", "Bordeaux")
stars = st.sidebar.selectbox("Nombre d'étoiles :", [None, 1, 2, 3, 4, 5], index=0)
max_pages = st.sidebar.slider("Nombre de pages à scraper :", 1, 5, 1)

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["🔎 Recherche et Scraping", "🧹 Nettoyage des données", "📊 Analyse des données"])

# Tab 1: Scraping
with tab1:
    if st.button("Lancer le scraping"):
        st.info("Création du lien Booking.com...")
        booking_url = generate_booking_url(search_location, stars)
        st.markdown(f"🔗 **Lien Booking généré :** [Cliquez ici pour voir les résultats sur Booking.com]({booking_url})")
        st.write(f"URL complète : {booking_url}")
        st.warning("Scraping des données en cours...")
        data = scrape_booking(booking_url, max_pages)
        if not data.empty:
            st.success(f"Scraping terminé avec succès : {len(data)} hôtels trouvés.")
            st.dataframe(data)
            st.download_button("Télécharger en CSV", data.to_csv(index=False), "hotels.csv")
        else:
            st.error("Aucun hôtel trouvé. Veuillez changer les critères et réessayer.")

# Tab 2: Cleaning
with tab2:
    st.markdown("### 🧹 Nettoyage des données brutes")
    uploaded_file = st.file_uploader("Téléchargez un fichier CSV brut :", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("**Aperçu des données brutes :**")
        st.dataframe(df)

        st.markdown("**Nettoyage en cours...**")
        cleaned_data = clean_data(df)
        st.write("**Données nettoyées :**")
        st.dataframe(cleaned_data)

        # Download cleaned data
        st.download_button("Télécharger les données nettoyées en CSV", cleaned_data.to_csv(index=False), "cleaned_hotels.csv")

# Tab 3: Analysis
with tab3:
    st.markdown("### 📊 Analyse des données nettoyées")
    uploaded_file = st.file_uploader("Téléchargez un fichier CSV nettoyé :", type=["csv"], key="analysis")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("**Aperçu des données :**")
        st.dataframe(df)

        # Statistiques descriptives
        st.markdown("### Résumé des données :")
        st.write(f"- Nombre total d'hôtels : {len(df)}")
        if "Rating" in df.columns:
            df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
            st.write(f"- Note moyenne : {df['Rating'].mean():.2f}")
            st.write(f"- Médiane des notes : {df['Rating'].median():.2f}")
            st.write(f"- Écart type des notes : {df['Rating'].std():.2f}")

        if "Classification" in df.columns:
            st.write("**Répartition par classification :**")
            classification_counts = df["Classification"].value_counts()
            st.write(classification_counts)

            # Graphique en barres pour la répartition par classification
            st.markdown("### Répartition par classification :")
            fig1 = plt.figure(figsize=(8, 5))
            classification_counts.plot(kind="bar", color="skyblue", edgecolor="black")
            plt.title("Répartition des classifications")
            plt.xlabel("Classification")
            plt.ylabel("Nombre d'hôtels")
            st.pyplot(fig1)

            # Histogramme des notes
            st.markdown("### Distribution des notes :")
            fig2 = plt.figure(figsize=(8, 5))
            df["Rating"].dropna().plot(kind="hist", bins=10, color="lightgreen", edgecolor="black")
            plt.title("Distribution des notes des hôtels")
            plt.xlabel("Note")
            plt.ylabel("Nombre d'hôtels")
            st.pyplot(fig2)

# Add footer
st.markdown("""
    <style>
    footer {
        visibility: hidden;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #262730;
        color: white;
        text-align: center;
        padding: 10px;
    }
    </style>
    <div class="footer">
        <p>Made with ❤️ by Maxime</p>
    </div>
""", unsafe_allow_html=True)