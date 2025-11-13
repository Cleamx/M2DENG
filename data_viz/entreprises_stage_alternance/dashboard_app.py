import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Opportunités en Corse")

st.title("📊 Dashboard des Stages et Alternances en Corse")
st.markdown("Utilisez les filtres dans le menu à gauche pour explorer les données.")

@st.cache_data
def load_data():
    """
    Cette fonction charge, nettoie et fusionne les trois fichiers CSV.
    """
    try:
        df_stages = pd.read_csv('stage_entreprises.csv', delimiter=';',)
        df_alternance = pd.read_csv('alternance_entreprise.csv', delimiter=';')
        df_entreprises = pd.read_csv('entreprises.csv', delimiter=';')
    except FileNotFoundError:
        st.error("Erreur : Un ou plusieurs fichiers CSV sont introuvables. Assurez-vous que `stage_entreprises.csv`, `alternance_entreprise.csv` et `entreprises.csv` sont dans le même dossier que le script.")
        return pd.DataFrame()

    # --- Nettoyage et Renommage ---
    # On supprime les espaces superflus des noms de colonnes
    for df in [df_stages, df_alternance, df_entreprises]:
        df.columns = df.columns.str.strip()

    # Standardisation des colonnes pour la fusion
    df_stages = df_stages[['NomStructure', 'VilleStructure', 'SujetStage']].rename(columns={
        'NomStructure': 'nom', 'VilleStructure': 'ville', 'SujetStage': 'description'
    })
    df_stages['type'] = 'Stage'

    df_alternance = df_alternance[['NOM_ENTREPRISE', 'VILLE_ENTREPRISE']].rename(columns={
        'NOM_ENTREPRISE': 'nom', 'VILLE_ENTREPRISE': 'ville'
    })
    df_alternance['type'] = 'Alternance'
    df_alternance['description'] = 'Alternance' # Ajout d'une description par défaut

    # Sélection des colonnes utiles du fichier entreprises
    df_entreprises = df_entreprises[['Raison_sociale', 'Libelle_code_APE', 'Voie', 'Code_postal', 'Telephone', 'Email']].rename(columns={
        'Raison_sociale': 'nom', 'Libelle_code_APE': 'secteur_activite', 'Voie': 'adresse', 'Code_postal': 'code_postal'
    })

    # --- Fusion des données ---
    df_opportunites = pd.concat([df_stages, df_alternance], ignore_index=True)

    # Nettoyage des noms pour optimiser la fusion (minuscules, sans espaces)
    df_opportunites['nom_clean'] = df_opportunites['nom'].str.lower().str.strip()
    df_entreprises['nom_clean'] = df_entreprises['nom'].str.lower().str.strip()

    # Fusion pour enrichir les offres avec les infos de contact
    df_final = pd.merge(df_opportunites, df_entreprises, on='nom_clean', how='left')

    # Nettoyage final
    df_final['ville'] = df_final['ville'].str.strip().str.title()
    df_final.drop(columns=['nom_clean', 'nom_y'], inplace=True)
    df_final.rename(columns={'nom_x': 'nom'}, inplace=True)
    df_final.fillna({'secteur_activite': 'Non spécifié'}, inplace=True)

    return df_final

# Chargement des données
df = load_data()

if not df.empty:
    # --- Barre latérale pour les filtres ---
    st.sidebar.header("🔍 Filtres")

    # Filtre par type d'opportunité
    type_filter = st.sidebar.multiselect(
        "Type d'opportunité :",
        options=df['type'].unique(),
        default=df['type'].unique()
    )

    # Filtre par ville
    ville_filter = st.sidebar.multiselect(
        "Ville :",
        options=df['ville'].sort_values().unique(),
        default=[] # Par défaut, aucune ville n'est sélectionnée pour tout afficher
    )

    # Filtre par secteur d'activité
    secteur_filter = st.sidebar.multiselect(
        "Secteur d'activité :",
        options=df['secteur_activite'].sort_values().unique(),
        default=[]
    )

    # --- Application des filtres ---
    df_filtered = df[df['type'].isin(type_filter)]
    if ville_filter:
        df_filtered = df_filtered[df_filtered['ville'].isin(ville_filter)]
    if secteur_filter:
        df_filtered = df_filtered[df_filtered['secteur_activite'].isin(secteur_filter)]

    # --- Affichage des indicateurs clés (KPIs) ---
    total_opportunites = len(df_filtered)
    total_entreprises = df_filtered['nom'].nunique()
    total_villes = df_filtered['ville'].nunique()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Opportunités", f"{total_opportunites}")
    with col2:
        st.metric("Entreprises Uniques", f"{total_entreprises}")
    with col3:
        st.metric("Villes", f"{total_villes}")

    st.markdown("---")

    # --- Graphique interactif ---
    st.subheader("Top 10 des villes par nombre d'opportunités")
    
    if not df_filtered.empty:
        # Comptage des offres par ville
        ville_counts = df_filtered['ville'].value_counts().nlargest(10).reset_index()
        ville_counts.columns = ['Ville', 'Nombre d\'opportunités']

        fig = px.bar(
            ville_counts,
            x='Ville',
            y='Nombre d\'opportunités',
            text_auto=True,
            title="Cliquez sur les barres ou la légende pour filtrer"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée à afficher avec les filtres actuels.")

    # --- Tableau de données interactif ---
    st.subheader("Liste détaillée des opportunités")
    st.dataframe(df_filtered[[
        'nom', 'type', 'ville', 'secteur_activite', 'adresse', 'code_postal', 'Telephone', 'Email', 'description'
    ]], use_container_width=True, height=500)
