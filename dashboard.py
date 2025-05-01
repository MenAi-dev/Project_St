import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from database import lister_produits, lister_commandes, produits_stock_bas, calculer_benefice
plt.style.use("seaborn-v0_8-whitegrid")  # Style propre, fond blanc/gris
plt.rcParams.update({
    "axes.facecolor": "#FAFAFA",
    "figure.facecolor": "#FFFFFF",
    "axes.labelcolor": "#212121",
    "xtick.color": "#212121",
    "ytick.color": "#212121",
    "text.color": "#212121"
})

def app():
    st.title("📊 Dashboard")
    
    # Récupérer les données
    produits = lister_produits()
    commandes = lister_commandes()
    produits_alerte = produits_stock_bas()
    
    # KPIs en haut
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total des Ventes", 
                 value=f"{len(commandes)} orders")
    
    with col2:
        total_revenu = commandes['total'].sum() if not commandes.empty else 0
        st.metric(label="Revenu Total", 
                 value=f"{total_revenu:,.0f} FCFA")
    
    with col3:
        total_produits = len(produits)
        st.metric(label="Produits en Stock", 
                 value=f"{total_produits}")
    
    with col4:
        benefice = calculer_benefice()
        st.metric(label="Bénéfice Net", 
                 value=f"{benefice:,.0f} FCFA",
                 delta=None,
                 delta_color="normal")

    # Deux sections côte à côte
    col1, col2 = st.columns(2)
    
    # Produits en alerte de stock
    with col1:
        st.subheader("⚠️ Produits en Stock Faible")
        if not produits_alerte.empty:
            st.dataframe(
                produits_alerte[['nom', 'categorie', 'stock', 'stock_min']], 
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Aucun produit en alerte de stock.")
    
    # Dernières commandes
    with col2:
        st.subheader("📝 Dernières Commandes")
        if not commandes.empty:
            dernieres_commandes = commandes.head(5)
            # Formater la date pour un meilleur affichage
            dernieres_commandes['date'] = pd.to_datetime(
                dernieres_commandes['date']
            ).dt.strftime('%d/%m/%Y')
            st.dataframe(
                dernieres_commandes[['id', 'client', 'date', 'total']], 
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Aucune commande enregistrée.")

    # Graphiques
    if not produits.empty or not commandes.empty:
        st.subheader("📈 Graphiques")
        
        graph1, graph2 = st.columns(2)
        
        with graph1:
            if not produits.empty:
                st.subheader("Répartition des Produits par Catégorie")
                # Créer un dataframe avec le compte des catégories
                cat_counts = produits['categorie'].value_counts().reset_index()
                cat_counts.columns = ['categorie', 'count']
                
                # Créer le graphique en camembert
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(cat_counts['count'], labels=cat_counts['categorie'], autopct='%1.1f%%', startangle=90)
                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                
                st.pyplot(fig)
        
        with graph2:
            if not commandes.empty:
                st.subheader("Évolution des Ventes")
                # Convertir la date en datetime
                commandes['date'] = pd.to_datetime(commandes['date'])
                
                # Regrouper par mois et calculer le total
                ventes_mensuelles = commandes.groupby(commandes['date'].dt.strftime('%m-%Y')).agg({
                    'total': 'sum'
                }).reset_index()
                
                # Créer le graphique à barres
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(ventes_mensuelles['date'], ventes_mensuelles['total'])
                ax.set_xlabel('Mois')
                ax.set_ylabel('Total des ventes (FCFA)')
                ax.set_xticklabels(ventes_mensuelles['date'], rotation=45)
                
                st.pyplot(fig)

# Pour tester ce module individuellement
if __name__ == "__main__":
    import sys
    import os
    
    # Ajuster le chemin pour importer le module database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    # Configurer la page
    st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
    
    # Exécuter l'application
    app()