import streamlit as st
import pandas as pd
import io

# =============================================================================
# Fonction principale pour le traitement des données
# =============================================================================
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie le DataFrame en gardant la ligne la plus récente pour chaque 
    compteur, en s'assurant que l'index n'est pas vide.

    Logique :
    1. Convertit la colonne 'Date' au format datetime pour un tri fiable.
    2. Pour chaque 'N° compteur' unique :
        a. Trie les lignes de la plus récente à la plus ancienne.
        b. Cherche la première ligne (la plus récente) où la colonne 'Index' n'est pas vide.
        c. Si aucune ligne n'a d'index valide, le compteur est ignoré.
    3. Retourne un nouveau DataFrame avec les lignes sélectionnées.
    """
    
    # Copie pour éviter de modifier le dataframe original
    df_copy = df.copy()

    # --- Étape 1: Préparation et validation des colonnes ---
    # S'assurer que les colonnes nécessaires existent
    required_columns = ["N° compteur", "Date", "Index"]
    if not all(col in df_copy.columns for col in required_columns):
        missing_cols = [col for col in required_columns if col not in df_copy.columns]
        st.error(f"Le fichier CSV doit contenir les colonnes suivantes : {', '.join(missing_cols)}")
        return pd.DataFrame() # Retourne un dataframe vide en cas d'erreur

    # Conversion de la colonne 'Date' en datetime. Les dates invalides deviennent NaT (Not a Time).
    # Le format de la date est inféré automatiquement avec dayfirst=True (format français JJ/MM/AAAA privilégié)
    df_copy['Date'] = pd.to_datetime(df_copy['Date'], errors='coerce', dayfirst=True)

    # Suppression des lignes où la date n'a pas pu être interprétée ou est manquante
    df_copy.dropna(subset=['Date'], inplace=True)
    
    # --- Étape 2: Logique de sélection ---
    
    # On trie le dataframe par N° compteur puis par Date (du plus récent au plus ancien)
    df_sorted = df_copy.sort_values(by=["N° compteur", "Date"], ascending=[True, False])

    # On supprime les lignes où l'index est vide (NaN, None, ou chaîne vide)
    # pd.isna() gère les NaN et None. On ajoute une condition pour les chaînes vides.
    df_filtered = df_sorted[pd.notna(df_sorted['Index']) & (df_sorted['Index'].astype(str).str.strip() != '')]

    # Maintenant, il suffit de garder la première occurrence de chaque 'N° compteur'
    # Comme le dataframe est déjà trié par date décroissante, la première est la bonne !
    df_final = df_filtered.drop_duplicates(subset="N° compteur", keep="first")
    
    return df_final

# =============================================================================
# Interface utilisateur avec Streamlit
# =============================================================================

st.set_page_config(page_title="Nettoyeur de Données Compteur", layout="wide")

st.title("CleanCSV 🧹")
st.header("Outil de nettoyage de relevés de compteur")
st.markdown("""
Cette application vous permet de nettoyer vos fichiers CSV de relevés de compteurs en suivant une règle simple :
1.  **Chargez** votre fichier CSV.
2.  L'application supprime les doublons de la colonne **"N° compteur"**.
3.  Pour chaque compteur, elle conserve **uniquement la ligne la plus récente** (basée sur la colonne "Date") qui possède une valeur dans la colonne **"Index"**.
4.  **Téléchargez** le fichier propre et prêt à l'emploi !
""")

# --- Zone de chargement du fichier ---
uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    try:
        # Lecture du fichier CSV. Le séparateur ';' est courant en France.
        df_original = pd.read_csv(uploaded_file, sep=';')
        
        st.subheader("Aperçu des données originales")
        st.dataframe(df_original.head())

        # --- Bouton pour lancer le traitement ---
        if st.button("Nettoyer le fichier", type="primary"):
            with st.spinner("Traitement en cours..."):
                df_cleaned = process_data(df_original)
            
            st.success("Nettoyage terminé !")
            
            st.subheader("Données nettoyées")
            st.dataframe(df_cleaned)

            # --- Affichage des statistiques ---
            st.metric(label="Lignes dans le fichier original", value=f"{len(df_original)}")
            st.metric(label="Lignes après nettoyage (compteurs uniques et valides)", value=f"{len(df_cleaned)}")

            # --- Zone de téléchargement ---
            # Conversion du dataframe en CSV pour le téléchargement
            csv_buffer = io.StringIO()
            df_cleaned.to_csv(csv_buffer, index=False, sep=';')
            csv_bytes = csv_buffer.getvalue().encode('utf-8')

            st.download_button(
                label="Télécharger le fichier nettoyé",
                data=csv_bytes,
                file_name="donnees_compteurs_nettoyees.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Une erreur est survenue lors de la lecture ou du traitement du fichier : {e}")
        st.warning("Vérifiez que votre fichier est bien un CSV et que le séparateur est un point-virgule ';'.")
