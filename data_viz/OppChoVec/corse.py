import folium
import pandas as pd
import geopandas as gpd
import branca.colormap as cm

geojson_path = 'Commune_Corse.geojson'
donnees_path = 'df_indicateur.csv'
bridge_path = 'donnee_brute.csv'

colonne_nom_data = 'Commune'
colonne_nom_bridge = 'zone' 
colonne_code_bridge = 'code' 

indicateurs_a_visualiser = [
    'Indicateur_Opp1', 'Indicateur_Opp2', 'Indicateur_Opp3', 'Indicateur_Opp4',
    'Indicateur_Cho1', 'Indicateur_Cho2', 'Indicateur_Vec1', 'Indicateur_Vec2',
    'Indicateur_Vec3', 'Indicateur_Vec4', 'Indice_OppChoVec'
]

try:
    gdf_map = gpd.read_file(geojson_path)
    df_data = pd.read_csv(donnees_path, sep=';', encoding='utf-8-sig')
    df_bridge = pd.read_csv(bridge_path, sep=';', encoding='utf-8-sig')
except Exception as e:
    print(f"Erreur de lecture de fichier : {e}")
    exit()

df_data.columns = df_data.columns.str.strip()
df_bridge.columns = df_bridge.columns.str.strip()
df_bridge.rename(columns={colonne_code_bridge: 'code'}, inplace=True)

df_data[colonne_nom_data] = df_data[colonne_nom_data].str.lower().str.strip()
df_bridge[colonne_nom_bridge] = df_bridge[colonne_nom_bridge].str.lower().str.strip()
df_bridge['code'] = df_bridge['code'].astype(str).str.strip()
gdf_map['code'] = gdf_map['code'].astype(str).str.strip()

df_complet = pd.merge(df_data, df_bridge[['code', colonne_nom_bridge]], left_on=colonne_nom_data, right_on=colonne_nom_bridge, how='inner')
df_complet.drop_duplicates(subset=['code'], keep='first', inplace=True)

for col in indicateurs_a_visualiser:
    if col in df_complet.columns:
        df_complet[col] = df_complet[col].astype(str).str.replace(',', '.', regex=False)
        df_complet[col] = pd.to_numeric(df_complet[col], errors='coerce')

gdf_final = gdf_map.merge(df_complet, on='code', how='left')

centre_corse = [42.15, 9.0]
carte_multi = folium.Map(location=centre_corse, zoom_start=8, tiles='OpenStreetMap')

for i, indicateur in enumerate(indicateurs_a_visualiser):
    if indicateur not in gdf_final.columns:
        continue
    
    valeurs = gdf_final[indicateur].dropna()
    if valeurs.empty:
        continue
        
    colormap = cm.linear.YlOrRd_09.scale(vmin=valeurs.min(), vmax=valeurs.max())
    colormap.caption = indicateur
    colormap.width = 200 
    colormap.height = 37
    
    def style_function(feature, col=indicateur, cmap=colormap):
        valeur = feature['properties'][col]
        return {
            'fillColor': cmap(valeur) if pd.notna(valeur) else 'gray',
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.6
        }

    layer_name = f"Indicateur: {indicateur}"
    feature_group = folium.FeatureGroup(name=layer_name, show=(i==0))

    folium.GeoJson(
        gdf_final,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['nom', indicateur],
            aliases=['Commune:', f'{indicateur}:'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 10px; padding: 5px;"),
            localize=True,
            sticky=False
        ),
        highlight_function=lambda x: {'weight': 2, 'color': 'black'}
    ).add_to(feature_group)
    
    colormap.add_to(carte_multi)
    feature_group.add_to(carte_multi)

folium.LayerControl(collapsed=False).add_to(carte_multi)
carte_multi.save('carte_finale_multicouche.html')

print("Carte multi-couches 'carte_finale_multicouche.html' générée avec succès !")