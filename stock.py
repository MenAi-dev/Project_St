import streamlit as st
import pandas as pd
from database import lister_produits, ajouter_produit, modifier_produit, supprimer_produit

def app():
    st.title("📦 Gestion de Stock")
    
    # Créer deux colonnes pour l'affichage du stock et le formulaire
    col1, col2 = st.columns([2, 1])
    
    # Colonne 1: Liste des produits
    with col1:
        st.subheader("Liste des Produits")
        
        # Récupérer et afficher la liste des produits
        produits = lister_produits()
        
        # Ajouter une recherche
        search = st.text_input("🔍 Rechercher un produit")
        
        if search:
            produits = produits[produits['nom'].str.contains(search, case=False) | 
                              produits['categorie'].str.contains(search, case=False)]
        
        if not produits.empty:
            # Coloration conditionnelle pour les produits en stock bas
            def highlight_stock_bas(row):
                if row['stock'] <= row['stock_min']:
                    return ['background-color: #FFCCCC'] * len(row)
                return [''] * len(row)
            
            # Formatter les colonnes monétaires
            produits_display = produits.copy()
            produits_display['prix_unitaire'] = produits_display['prix_unitaire'].apply(lambda x: f"{x:,.0f} FCFA")
            
            # Afficher le dataframe avec styling
            st.dataframe(
                produits_display.style.apply(highlight_stock_bas, axis=1),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Aucun produit en stock. Utilisez le formulaire pour ajouter de nouveaux produits.")
    
    # Colonne 2: Formulaire pour ajouter/modifier des produits
    with col2:
        # On va utiliser des onglets pour séparer ajout et modification
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "✏️ Modifier", "❌ Supprimer"])
        
        # Onglet 1: Ajouter un produit
        with tab1:
            st.subheader("Ajouter un Produit")
            
            with st.form("add_product_form"):
                nom = st.text_input("Nom du produit")
                categorie = st.selectbox(
                    "Catégorie",
                    options=["Maquillage", "Soin", "Parfum", "Accessoire", "Autre"]
                )
                prix = st.number_input("Prix unitaire (FCFA)", min_value=0, step=100)
                stock = st.number_input("Stock initial", min_value=0, step=1)
                stock_min = st.number_input("Stock minimum (alerte)", min_value=0, step=1)
                
                submit_button = st.form_submit_button(label="Ajouter")
                
                if submit_button:
                    if nom and prix > 0:
                        ajouter_produit(nom, categorie, prix, stock, stock_min)
                        st.success(f"✅ Produit '{nom}' ajouté avec succès!")
                        st.rerun()  # Actualiser la page pour voir le nouveau produit
                    else:
                        st.error("❌ Veuillez remplir tous les champs obligatoires.")
        
        # Onglet 2: Modifier un produit
        with tab2:
            st.subheader("Modifier un Produit")
            
            if not produits.empty:
                produit_id = st.selectbox(
                    "Sélectionner un produit à modifier",
                    options=produits['id'].tolist(),
                    format_func=lambda x: produits.loc[produits['id'] == x, 'nom'].iloc[0]
                )
                
                # Récupérer les informations du produit sélectionné
                produit_selected = produits[produits['id'] == produit_id].iloc[0]
                
                with st.form("edit_product_form"):
                    nom = st.text_input("Nom du produit", value=produit_selected['nom'])
                    categorie = st.selectbox(
                        "Catégorie",
                        options=["Maquillage", "Soin", "Parfum", "Accessoire", "Autre"],
                        index=["Maquillage", "Soin", "Parfum", "Accessoire", "Autre"].index(produit_selected['categorie']) 
                              if produit_selected['categorie'] in ["Maquillage", "Soin", "Parfum", "Accessoire", "Autre"] else 4
                    )
                    prix = st.number_input("Prix unitaire (FCFA)", 
                                         min_value=0, 
                                         step=100, 
                                         value=int(produit_selected['prix_unitaire']))
                    stock = st.number_input("Stock actuel", 
                                         min_value=0, 
                                         step=1, 
                                         value=int(produit_selected['stock']))
                    stock_min = st.number_input("Stock minimum (alerte)", 
                                             min_value=0, 
                                             step=1, 
                                             value=int(produit_selected['stock_min']))
                    
                    submit_edit = st.form_submit_button(label="Enregistrer les modifications")
                    
                    if submit_edit:
                        if nom and prix > 0:
                            modifier_produit(produit_id, nom, categorie, prix, stock, stock_min)
                            st.success(f"✅ Produit '{nom}' modifié avec succès!")
                            st.rerun()  # Actualiser la page
                        else:
                            st.error("❌ Veuillez remplir tous les champs obligatoires.")
            else:
                st.info("Aucun produit disponible pour modification.")
        
        # Onglet 3: Supprimer un produit
        with tab3:
            st.subheader("Supprimer un Produit")
            st.warning("⚠️ Attention: Cette action est irréversible!")
            
            if not produits.empty:
                produit_id_delete = st.selectbox(
                    "Sélectionner un produit à supprimer",
                    options=produits['id'].tolist(),
                    format_func=lambda x: f"{produits.loc[produits['id'] == x, 'nom'].iloc[0]} ({produits.loc[produits['id'] == x, 'stock'].iloc[0]} en stock)"
                )
                
                if st.button("🗑️ Supprimer ce produit", 
                           key="delete_button", 
                           type="primary", 
                           use_container_width=True):
                    produit_nom = produits.loc[produits['id'] == produit_id_delete, 'nom'].iloc[0]
                    supprimer_produit(produit_id_delete)
                    st.success(f"✅ Produit '{produit_nom}' supprimé avec succès!")
                    st.rerun()  # Actualiser la page
            else:
                st.info("Aucun produit disponible pour suppression.")

# Pour tester ce module individuellement
if __name__ == "__main__":
    import sys
    import os
    
    # Ajuster le chemin pour importer le module database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    # Configurer la page
    st.set_page_config(page_title="Gestion de Stock", page_icon="📦", layout="wide")
    
    # Exécuter l'application
    app()