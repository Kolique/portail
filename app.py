import streamlit as st
import pandas as pd
import io

# =============================================================================
# FONCTION POUR L'ONGLET 1 : Nettoyeur de Fichier
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
# FONCTION POUR L'ONGLET 2 : Comparateur de Fichiers
# =============================================================================
def compare_files(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Compare deux DataFrames et retourne les lignes de df1 dont le 'N° compteur' 
    n'est pas dans df2."""
    # Vérification que la colonne 'N° compteur' existe dans les deux fichiers
    if 'N° compteur' not in df1.columns or 'N° compteur' not in df2.columns:
        st.error("La colonne 'N° compteur' doit être présente dans les deux fichiers.")
        return pd.DataFrame()
    
    # Utilisation des 'set' pour une comparaison très rapide
    ids_in_df1 = set(df1['N° compteur'])
    ids_in_df2 = set(df2['N° compteur'])
    
    # Trouver les IDs qui sont dans le premier set mais pas dans le second
    missing_ids = ids_in_df1 - ids_in_df2
    
    # Filtrer le dataframe original (df1) pour ne garder que les lignes avec les IDs manquants
    result_df = df1[df1['N° compteur'].isin(missing_ids)].copy()
    
    return result_df

# =============================================================================
# Interface utilisateur principale avec les onglets
# =============================================================================
st.set_page_config(page_title="Outils CSV Compteurs", layout="wide")

st.title("Boîte à Outils CSV pour Compteurs ⚙️")

# --- Création des onglets ---
tab1, tab2 = st.tabs([" सफाई CSV (Nettoyeur de Fichier)", "🔄 Comparateur de Fichiers"])

# --- CONTENU DE L'ONGLET 1 : NETTOYEUR DE FICHIER (CleanCSV) ---
with tab1:
    st.header("Étape 1 : Charger votre fichier à nettoyer")
    st.markdown("Cette application nettoie et dédoublonne un fichier de relevés de compteurs.")

    uploaded_file_clean = st.file_uploader("Choisissez un fichier CSV à nettoyer", type="csv", key="cleaner")

    if uploaded_file_clean is not None:
        try:
            df_original = pd.read_csv(uploaded_file_clean, sep=';')
            st.subheader("Aperçu des données originales")
            st.dataframe(df_original.head())

            if st.button("Nettoyer le fichier", type="primary"):
                with st.spinner("Traitement en cours..."):
                    df_cleaned = process_data(df_original)
                    st.session_state['cleaned_df'] = df_cleaned
                    st.session_state['original_rows'] = len(df_original)
                st.success("Traitement terminé ! Les résultats sont prêts.")

            if 'cleaned_df' in st.session_state:
                df_cleaned_result = st.session_state['cleaned_df']
                st.subheader("Données nettoyées")
                st.dataframe(df_cleaned_result)
                
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

# --- CONTENU DE L'ONGLET 2 : COMPARATEUR DE FICHIERS ---
with tab2:
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
                df1 = pd.read_csv(uploaded_file_1, sep=';')
                df2 = pd.read_csv(uploaded_file_2, sep=';')

                with st.spinner("Comparaison en cours..."):
                    missing_df = compare_files(df1, df2)
                
                st.success(f"Comparaison terminée ! **{len(missing_df)}** compteur(s) du Fichier 1 sont manquants dans le Fichier 2.")

                if not missing_df.empty:
                    st.subheader("Lignes des compteurs manquants (issues du Fichier 1)")
                    st.dataframe(missing_df)

                    # Préparation du bouton de téléchargement
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
                st.error(f"Une erreur est survenue lors de la lecture ou du traitement des fichiers : {e}")
