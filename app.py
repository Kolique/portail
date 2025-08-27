import streamlit as st
import pandas as pd
import io

# =============================================================================
# Fonction principale pour le traitement des données (INCHANGÉE)
# =============================================================================
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie le DataFrame en gardant la ligne la plus récente pour chaque 
    compteur, en s'assurant que l'index n'est pas vide.
    """
    df_copy = df.copy()

    required_columns = ["N° compteur", "Date", "Index"]
    if not all(col in df_copy.columns for col in required_columns):
        missing_cols = [col for col in required_columns if col not in df_copy.columns]
        st.error(f"Le fichier CSV doit contenir les colonnes suivantes : {', '.join(missing_cols)}")
        return pd.DataFrame()

    df_copy['Date'] = pd.to_datetime(df_copy['Date'], errors='coerce', dayfirst=True)
    df_copy.dropna(subset=['Date'], inplace=True)
    
    df_sorted = df_copy.sort_values(by=["N° compteur", "Date"], ascending=[True, False])
    df_filtered = df_sorted[pd.notna(df_sorted['Index']) & (df_sorted['Index'].astype(str).str.strip() != '')]
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
4.  **Téléchargez** le fichier propre au format **Excel (.xlsx)** !
""")

uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    try:
        df_original = pd.read_csv(uploaded_file, sep=';')
        
        st.subheader("Aperçu des données originales")
        st.dataframe(df_original.head())

        if st.button("Nettoyer le fichier", type="primary"):
            with st.spinner("Traitement en cours..."):
                df_cleaned = process_data(df_original)
            
            st.success("Nettoyage terminé !")
            
            st.subheader("Données nettoyées")
            st.dataframe(df_cleaned)

            st.metric(label="Lignes dans le fichier original", value=f"{len(df_original)}")
            st.metric(label="Lignes après nettoyage", value=f"{len(df_cleaned)}")

            # --- NOUVELLE SECTION DE TÉLÉCHARGEMENT AU FORMAT XLSX ---
            # Conversion du dataframe en fichier Excel en mémoire
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_cleaned.to_excel(writer, index=False, sheet_name='Donnees_Nettoyees')
            
            # Récupération des données binaires du fichier Excel
            excel_bytes = output.getvalue()

            st.download_button(
                label="📥 Télécharger le fichier nettoyé (Excel)",
                data=excel_bytes,
                file_name="donnees_compteurs_nettoyees.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            # --- FIN DE LA MODIFICATION ---

    except Exception as e:
        st.error(f"Une erreur est survenue lors de la lecture ou du traitement du fichier : {e}")
        st.warning("Vérifiez que votre fichier est bien un CSV et que le séparateur est un point-virgule ';'.")
