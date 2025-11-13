import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from time import sleep
import ssl
import certifi

def get_location(geolocator, adresse, ville, code_postal):
    try:
        query = f"{adresse}, {code_postal} {ville}, Corse, France"
        print(f"Essai 1: {query}")
        location = geolocator.geocode(query, timeout=10)
        sleep(1) 
        if location:
            return location
    except Exception:
        pass 

    try:
        query = f"{code_postal} {ville}, Corse, France"
        print(f"  -> Essai 2 (ville): {query}")
        location = geolocator.geocode(query, timeout=10)
        sleep(1)
        if location:
            return location
    except Exception:
        pass

    print(f"    -> Échec de la localisation pour : {adresse}, {ville}")
    return None



try:
    df_stages = pd.read_csv('stage_entreprises.csv', delimiter=';')
    df_stages.columns = df_stages.columns.str.strip()

    df_alternance = pd.read_csv('alternance_entreprise.csv', delimiter=';')
    df_alternance.columns = df_alternance.columns.str.strip()

    df_entreprises = pd.read_csv('entreprises.csv', delimiter=';')
    df_entreprises.columns = df_entreprises.columns.str.strip()
except Exception as e:
    print(f"Erreur lors de la lecture des fichiers : {e}")
    df_stages, df_alternance, df_entreprises = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

if not df_stages.empty:
    df_stages = df_stages[['NomStructure', 'AdresseStructure', 'CodePostalStructure', 'VilleStructure']].rename(columns={
        'NomStructure': 'nom', 'AdresseStructure': 'adresse', 'CodePostalStructure': 'code_postal', 'VilleStructure': 'ville'
    })
    df_stages['type'] = 'stage'

if not df_alternance.empty:
    df_alternance = df_alternance[['NOM_ENTREPRISE', 'ADR1_ENTREPRISE', 'CP_ENTREPRISE', 'VILLE_ENTREPRISE']].rename(columns={
        'NOM_ENTREPRISE': 'nom', 'ADR1_ENTREPRISE': 'adresse', 'CP_ENTREPRISE': 'code_postal', 'VILLE_ENTREPRISE': 'ville'
    })
    df_alternance['type'] = 'alternance'

if not df_entreprises.empty:
    df_entreprises = df_entreprises[['Raison_sociale', 'Voie', 'Code_postal', 'Libelle_commune', 'Libelle_code_APE']].rename(columns={
        'Raison_sociale': 'nom', 'Voie': 'adresse', 'Code_postal': 'code_postal', 'Libelle_commune': 'ville', 'Libelle_code_APE': 'secteur_activite'
    })

df_opportunites = pd.concat([df_stages, df_alternance], ignore_index=True) if not df_stages.empty or not df_alternance.empty else pd.DataFrame()

if not df_entreprises.empty:
    df_opportunites['nom_lower'] = df_opportunites['nom'].str.lower().str.strip()
    df_entreprises['nom_lower'] = df_entreprises['nom'].str.lower().str.strip()
    df_final = pd.merge(df_opportunites, df_entreprises[['nom_lower', 'secteur_activite']], on='nom_lower', how='left')
    df_final.drop(columns=['nom_lower'], inplace=True)
else:
    df_final = df_opportunites
    df_final['secteur_activite'] = "Non spécifié"

df_final.drop_duplicates(subset=['nom', 'adresse', 'ville'], inplace=True)

for col in ['adresse', 'ville', 'code_postal', 'nom']:
    if col in df_final.columns:
        df_final[col] = df_final[col].astype(str).str.strip()

df_final.dropna(subset=['ville', 'code_postal'], inplace=True)
df_final = df_final[df_final['ville'].str.lower() != 'nan']
df_final = df_final[df_final['code_postal'].str.lower() != 'nan']

ctx = ssl.create_default_context(cafile=certifi.where())

geolocator = Nominatim(
    user_agent="carte_etudiants_corse_v6",
    ssl_context=ctx
)

latitudes, longitudes = [], []

print("\n--- Début de la géolocalisation des adresses ---")
for index, row in df_final.iterrows():
    location = get_location(geolocator, row['adresse'], row['ville'], row['code_postal'])
    if location:
        latitudes.append(location.latitude)
        longitudes.append(location.longitude)
    else:
        latitudes.append(None)
        longitudes.append(None)

df_final['latitude'] = latitudes
df_final['longitude'] = longitudes

df_final.dropna(subset=['latitude', 'longitude'], inplace=True)
print(f"\n--- {len(df_final)} entreprises ont été localisées avec succès. ---")

if not df_final.empty:
    map_corse = folium.Map(location=[42.15, 9.0], zoom_start=9)
    marker_cluster = MarkerCluster().add_to(map_corse)

    for index, row in df_final.iterrows():
        color = 'blue' if row.get('type') == 'stage' else 'green'
        icon = 'briefcase' if row.get('type') == 'stage' else 'graduation-cap'
        
        popup_html = f"""
        <h4><b>{row['nom']}</b></h4>
        <b>Type :</b> {row.get('type', 'N/A').title()}<br>
        <b>Secteur :</b> {row.get('secteur_activite', 'N/A')}<br>
        <b>Adresse :</b> {row['adresse']}, {row['code_postal']} {row['ville']}
        """
        popup = folium.Popup(popup_html, max_width=300)

        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup,
            tooltip=row['nom'],
            icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
        ).add_to(marker_cluster)

    map_corse.save('carte_entreprises_corse.html')
    print("\n🗺️  La carte a été générée avec succès dans le fichier 'carte_entreprises_corse.html'")
else:
    print("\nAucune entreprise n'a pu être localisée. La carte n'a pas été générée.")
