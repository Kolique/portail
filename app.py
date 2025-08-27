import streamlit as st
import pandas as pd
import io

# =============================================================================
# FONCTION POUR L'APP 1 : Nettoyeur de Fichier
# =============================================================================
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie le DataFrame en gardant la ligne la plus récente pour chaque 
    compteur, en s'assurant que l'index n'est pas vide."""
    df_copy = df.copy()
    required_columns = ["N° compteur", "Date", "Index"]
    if not all(col in df_copy.columns for col in required_columns):
        missing_cols = [col for col in required_columns if col not in df_copy.columns]
        st.error(f"Le fichier CSV pour le nettoyage doit contenir les colonnes : {', '.join(missing_cols)}")
        return pd.DataFrame()

    df_copy['Date'] = pd.to_datetime(df_copy['Date'], errors='coerce', dayfirst=True)
    df_copy.dropna(subset=['Date'], inplace=True)
    
    df_sorted = df_copy.sort_values(by=["N° compteur", "Date"], ascending=[True, False])
    df_filtered = df_sorted[pd.notna(df_sorted['Index']) & (df_sorted['Index'].astype(str).str.strip() != '')]
    df_final = df_filtered.drop_duplicates(subset="N° compteur", keep="first")
    
    return df_final

# =============================================================================
# FONCTION POUR L'APP 2 : Comparateur de Fichiers
# =============================================================================
def compare_files(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Compare deux DataFrames et retourne les lignes de df1 dont le 'N° compteur' 
    n'est pas dans df2."""
    if 'N° compteur' not in df1.columns or 'N° compteur' not in df2.columns:
        st.error("La colonne 'N° compteur' doit être présente dans les deux fichiers.")
        return pd.DataFrame()
    
    ids_in_df1 = set(df1['N° compteur'])
    ids_in_df2 = set(df2['N° compteur'])
    missing_ids = ids_in_df1 - ids_in_df2
    result_df = df1[df1['N° compteur'].isin(missing_ids)].copy()
    
    return result_df

# =============================================================================
# Interface utilisateur principale
# =============================================================================
st.set_page_config(page_title="Outils CSV Compteurs", layout="wide")

# --- NAVIGATION AMÉLIORÉE DANS LA BARRE LATERALE ---
st.sidebar.title("Boîte à Outils CSV ⚙️")
st.sidebar.markdown("---") # Ajoute une ligne de séparation

page = st.sidebar.radio(
    "Choisissez une application :", 
    ["🧹 Suppresion doublons", "🔄 Comparaison"]
)

# --- AFFICHAGE DE LA PAGE SÉLECTIONNÉE ---

if page == "🧹 Suppresion doublons":
    st.title("🧹 Suppresion doublons")
    st.header("Étape 1 : Charger votre fichier à nettoyer")
    st.markdown("""
    Cette application supprime les doubons et garde que les plus récent.
    1.  **Chargez** votre fichier CSV via le bouton ci-dessous.
    2.  L'application supprime les doublons de la colonne **"N° compteur"**.
    3.  Pour chaque compteur, elle conserve **uniquement la ligne la plus récente** (basée sur la colonne "Date") qui possède une valeur dans la colonne **"Index"**.
    4.  Cliquez sur le bouton **"Nettoyer le fichier"** pour lancer le traitement.
    """)

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

    if uploaded_file is not None:
        try:
            df_original = pd.read_csv(uploaded_file, sep=';', dtype={'Réf. abonné': str})
            st.subheader("Aperçu des données originales")
            st.dataframe(df_original.head())

            if st.button("Nettoyer le fichier", type="primary"):
                with st.spinner("Traitement en cours..."):
                    df_cleaned = process_data(df_original)
                    st.session_state['cleaned_df'] = df_cleaned
                    st.session_state['original_rows'] = len(df_original)
                st.success("Traitement terminé !")
            
            if 'cleaned_df' in st.session_state:
                st.header("Étape 2 : Visualiser et télécharger")
                df_cleaned_result = st.session_state['cleaned_df']
                st.subheader("Données nettoyées")
                st.dataframe(df_cleaned_result)

                col1, col2 = st.columns(2)
                col1.metric(label="Lignes dans le fichier original", value=st.session_state['original_rows'])
                col2.metric(label="Lignes après nettoyage", value=len(df_cleaned_result))
                
                csv_buffer = io.StringIO()
                df_cleaned_result.to_csv(csv_buffer, index=False, sep=';')
                csv_bytes = csv_buffer.getvalue().encode('utf-8')

                st.download_button(
                    label="📥 Télécharger le fichier nettoyé (CSV)",
                    data=csv_bytes,
                    file_name="donnees_compteurs_nettoyees.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")

elif page == "🔄 Comparaison":
    st.title("🔄 Comparaison")
    st.header("Trouver les compteurs manquants")
    st.markdown("""
    Cette application compare deux fichiers pour trouver les numéros de compteur qui sont dans le **Fichier 1** mais pas dans le **Fichier 2**.
    1.  Chargez le fichier de référence (**Fichier 1**).
    2.  Chargez le fichier dans lequel vous voulez vérifier la présence des compteurs (**Fichier 2**).
    3.  Cliquez sur "Comparer" pour obtenir la liste des manquants.
    """)

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file_1 = st.file_uploader("Fichier 1 (Référence)", type="csv", key="compare1")
    with col2:
        uploaded_file_2 = st.file_uploader("Fichier 2 (À vérifier)", type="csv", key="compare2")

    if uploaded_file_1 and uploaded_file_2:
        if st.button("Comparer les fichiers", type="primary"):
            try:
                df1 = pd.read_csv(uploaded_file_1, sep=';', dtype={'Réf. abonné': str})
                df2 = pd.read_csv(uploaded_file_2, sep=';', dtype={'Réf. abonné': str})

                with st.spinner("Comparaison en cours..."):
                    missing_df = compare_files(df1, df2)
                
                st.success(f"Comparaison terminée ! **{len(missing_df)}** compteur(s) du Fichier 1 sont manquants dans le Fichier 2.")

                if not missing_df.empty:
                    st.subheader("Lignes des compteurs manquants (issues du Fichier 1)")
                    st.dataframe(missing_df)

                    csv_buffer_missing = io.StringIO()
                    missing_df.to_csv(csv_buffer_missing, index=False, sep=';')
                    csv_bytes_missing = csv_buffer_missing.getvalue().encode('utf-8')

                    st.download_button(
                        label="📥 Télécharger la liste des manquants (CSV)",
                        data=csv_bytes_missing,
                        file_name="compteurs_manquants.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("Bonne nouvelle ! Tous les compteurs du Fichier 1 sont présents dans le Fichier 2.")
            
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
