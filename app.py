import streamlit as st
import pandas as pd
import io

def nettoyer_fichier(df):
    colonnes_requises = ["N° compteur", "Date", "Index"]
    if not all(col in df.columns for col in colonnes_requises):
        cols_manquantes = [col for col in colonnes_requises if col not in df.columns]
        st.error(f"Erreur : il manque les colonnes suivantes : {', '.join(cols_manquantes)}")
        return pd.DataFrame()

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df.dropna(subset=['Date'], inplace=True)
    
    df_trie = df.sort_values(by=["N° compteur", "Date"], ascending=[True, False])
    
    df_filtre = df_trie[pd.notna(df_trie['Index']) & (df_trie['Index'].astype(str).str.strip() != '')]
    
    df_final = df_filtre.drop_duplicates(subset="N° compteur", keep="first")
    
    return df_final

def comparer_fichiers(df1, df2):
    if 'N° compteur' not in df1.columns or 'N° compteur' not in df2.columns:
        st.error("La colonne 'N° compteur' doit exister dans les deux fichiers.")
        return pd.DataFrame()
    
    compteurs_f1 = set(df1['N° compteur'])
    compteurs_f2 = set(df2['N° compteur'])
    
    compteurs_manquants = compteurs_f1 - compteurs_f2
    
    resultat = df1[df1['N° compteur'].isin(compteurs_manquants)].copy()
    
    return resultat

st.set_page_config(page_title="Outils CSV", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Choisis un outil :", ["Nettoyage Doublons", "Comparaison Fichiers"])

if page == "Nettoyage Doublons":
    st.title("Outil de Nettoyage CSV")
    st.header("Charger le fichier")
    st.markdown("""
    Cet outil nettoie un fichier CSV de relevés pour ne garder que la ligne la plus récente et valide pour chaque compteur.
    - Il supprime les doublons de la colonne **"N° compteur"**.
    - Il garde la ligne avec la **date la plus récente**.
    - Il vérifie que la colonne **"Index"** de cette ligne n'est pas vide.
    """)

    fichier_charge = st.file_uploader("Sélectionne un fichier CSV", type="csv")

    if fichier_charge is not None:
        try:
            df_initial = pd.read_csv(fichier_charge, sep=';', dtype={'Réf. abonné': str})
            st.subheader("Aperçu du fichier original")
            st.dataframe(df_initial.head())

            if st.button("Lancer le nettoyage", type="primary"):
                with st.spinner("Nettoyage en cours..."):
                    df_nettoye = nettoyer_fichier(df_initial)
                    st.session_state['df_nettoye'] = df_nettoye
                    st.session_state['lignes_originales'] = len(df_initial)
                st.success("C'est terminé !")
            
            if 'df_nettoye' in st.session_state:
                st.header("2. Résultat")
                resultat_nettoyage = st.session_state['df_nettoye']
                st.dataframe(resultat_nettoyage)

                col1, col2 = st.columns(2)
                col1.metric("Lignes avant", st.session_state['lignes_originales'])
                col2.metric("Lignes après", len(resultat_nettoyage))
                
                buffer = io.StringIO()
                resultat_nettoyage.to_csv(buffer, index=False, sep=';')
                csv_final = buffer.getvalue().encode('utf-8')

                st.download_button(
                    label="📥 Télécharger le résultat (CSV)",
                    data=csv_final,
                    file_name="fichier_nettoye.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"Oups, une erreur est survenue : {e}")

elif page == "Comparaison Fichiers":
    st.title("Outil de Comparaison de Fichiers")
    st.header("Trouver les compteurs manquants")
    st.markdown("""
    Cet outil trouve les compteurs présents dans un **Fichier 1** mais absents d'un **Fichier 2**.
    1.  Chargez le fichier de référence (**Fichier 1**).
    2.  Chargez le fichier dans lequel vous voulez vérifier la présence des compteurs (**Fichier 2**).
    3.  Cliquez sur "Comparer" pour obtenir la liste des manquants.
    """)

    col1, col2 = st.columns(2)
    fichier1 = col1.file_uploader("Fichier 1 (de référence)", type="csv")
    fichier2 = col2.file_uploader("Fichier 2 (à comparer)", type="csv")

    if fichier1 and fichier2:
        if st.button("Comparer", type="primary"):
            try:
                df1 = pd.read_csv(fichier1, sep=';', dtype={'Réf. abonné': str})
                df2 = pd.read_csv(fichier2, sep=';', dtype={'Réf. abonné': str})

                with st.spinner("Comparaison en cours..."):
                    df_manquants = comparer_fichiers(df1, df2)
                
                st.success(f"Analyse terminée : **{len(df_manquants)}** compteur(s) sont manquants.")

                if not df_manquants.empty:
                    st.subheader("Liste des compteurs manquants")
                    st.dataframe(df_manquants)

                    buffer_comp = io.StringIO()
                    df_manquants.to_csv(buffer_comp, index=False, sep=';')
                    csv_comp = buffer_comp.getvalue().encode('utf-8')

                    st.download_button(
                        label="📥 Télécharger la liste (CSV)",
                        data=csv_comp,
                        file_name="compteurs_manquants.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("Bonne nouvelle, aucun compteur ne manque !")
            
            except Exception as e:
                st.error(f"Oups, une erreur est survenue : {e}")
