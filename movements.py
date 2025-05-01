import streamlit as st
import pandas as pd
from datetime import datetime
from database import lister_produits, enregistrer_mouvement, lister_mouvements, supprimer_mouvement

def app():
    st.title("🔄 Mouvements de Stock")
    
    # Initialiser les états de session si nécessaire
    if "confirmer_suppression_mouvement" not in st.session_state:
        st.session_state.confirmer_suppression_mouvement = False
    if "mouvement_a_supprimer" not in st.session_state:
        st.session_state.mouvement_a_supprimer = None
    
    # Fonctions de callback pour la gestion des boutons
    def demander_confirmation(mouvement_id):
        st.session_state.confirmer_suppression_mouvement = True
        st.session_state.mouvement_a_supprimer = mouvement_id
    
    def confirmer_suppression():
        if st.session_state.mouvement_a_supprimer:
            supprimer_mouvement(st.session_state.mouvement_a_supprimer)
            st.session_state.confirmer_suppression_mouvement = False
            st.session_state.mouvement_a_supprimer = None
            st.session_state.need_rerun = True  # 👈 Drapeau pour forcer le rerun
    
    def annuler_suppression():
        st.session_state.confirmer_suppression_mouvement = False
        st.session_state.mouvement_a_supprimer = None
        st.rerun()
    
    # Créer deux colonnes pour le formulaire et l'historique
    col1, col2 = st.columns([1, 2])
    
    # Colonne 1: Formulaire pour enregistrer un mouvement
    with col1:
        st.subheader("Enregistrer un Mouvement")
        
        # Récupérer la liste des produits
        produits = lister_produits()
        
        if not produits.empty:
            with st.form("movement_form"):
                # Type de mouvement
                type_mouvement = st.radio(
                    "Type de mouvement",
                    options=["entree", "sortie"],
                    format_func=lambda x: "Entrée (Approvisionnement)" if x == "entree" else "Sortie (Vente, Perte)"
                )
                
                # Sélection du produit
                produit_id = st.selectbox(
                    "Produit",
                    options=produits['id'].tolist(),
                    format_func=lambda x: f"{produits.loc[produits['id'] == x, 'nom'].iloc[0]} - Stock: {produits.loc[produits['id'] == x, 'stock'].iloc[0]}"
                )
                
                # Quantité
                quantite = st.number_input("Quantité", min_value=1, step=1)
                
                # Date (par défaut aujourd'hui)
                date = st.date_input("Date", value=datetime.now())
                
                # Commentaire
                commentaire = st.text_area("Commentaire", placeholder="Raison du mouvement...")
                
                # Bouton de soumission
                submit = st.form_submit_button("Enregistrer")
                
                if submit:
                    # Vérifier si la quantité est suffisante pour une sortie
                    produit_stock = produits.loc[produits['id'] == produit_id, 'stock'].iloc[0]
                    
                    if type_mouvement == "sortie" and quantite > produit_stock:
                        st.error(f"❌ Stock insuffisant! Seulement {produit_stock} unité(s) disponible(s).")
                    else:
                        # Formater la date en string
                        date_str = date.strftime("%Y-%m-%d")
                        
                        # Enregistrer le mouvement
                        enregistrer_mouvement(produit_id, type_mouvement, quantite, date_str, commentaire)
                        
                        produit_nom = produits.loc[produits['id'] == produit_id, 'nom'].iloc[0]
                        success_msg = (f"✅ {quantite} unité(s) du produit '{produit_nom}' "
                                     f"{'ajoutée(s)' if type_mouvement == 'entree' else 'retirée(s)'} "
                                     f"du stock.")
                        st.success(success_msg)
                        st.rerun()  # Actualiser la page
        else:
            st.warning("Aucun produit disponible. Veuillez d'abord ajouter des produits dans la gestion de stock.")
    
    # Colonne 2: Historique des mouvements
    with col2:
        st.subheader("Historique des Mouvements")
        
        # Filtres pour l'historique
        col_date, col_type = st.columns(2)
        
        with col_date:
            date_filter = st.date_input("Filtrer par date", value=None)
        
        with col_type:
            type_filter = st.selectbox(
                "Type de mouvement",
                options=["Tous", "entree", "sortie"],
                format_func=lambda x: "Tous" if x == "Tous" else "Entrée" if x == "entree" else "Sortie"
            )
        
        # Récupérer l'historique des mouvements
        mouvements = lister_mouvements()
        
        if not mouvements.empty:
            # Appliquer les filtres
            if date_filter:
                date_str = date_filter.strftime("%Y-%m-%d")
                mouvements = mouvements[mouvements['date'] == date_str]
            
            if type_filter != "Tous":
                mouvements = mouvements[mouvements['type'] == type_filter]
            
            # Formater pour l'affichage
            mouvements_display = mouvements.copy()
            mouvements_display['date'] = pd.to_datetime(mouvements_display['date']).dt.strftime('%d/%m/%Y')
            mouvements_display['type'] = mouvements_display['type'].apply(
                lambda x: "➕ Entrée" if x == "entree" else "➖ Sortie"
            )
            
            # Afficher le tableau
            st.dataframe(
                mouvements_display[['date', 'nom', 'type', 'quantite', 'commentaire']],
                hide_index=True,
                use_container_width=True
            )
            
            # Ajouter une section pour supprimer un mouvement
            st.subheader("Supprimer un Mouvement")
            mouvements_display["label"] = mouvements_display.apply(
                lambda row: f"{row['date']} | {row['type']} | {row['nom']} ({row['quantite']})", axis=1
            )
            mouvement_id = st.selectbox(
                "Sélectionnez un mouvement à supprimer",
                options=mouvements_display["id"],
                format_func=lambda x: mouvements_display[mouvements_display["id"] == x]["label"].iloc[0]
            )
            
            # Bouton pour demander confirmation
            if not st.session_state.confirmer_suppression_mouvement:
                if st.button("Supprimer ce mouvement"):
                    demander_confirmation(mouvement_id)
            else:
                # Afficher le message de confirmation
                st.warning(f"Êtes-vous sûr de vouloir supprimer le mouvement #{st.session_state.mouvement_a_supprimer}?")
                
                # Boutons de confirmation ou d'annulation
                col1_conf, col2_conf = st.columns(2)
                with col1_conf:
                    st.button("✅ Confirmer la suppression", on_click=confirmer_suppression)
                with col2_conf:
                    st.button("❌ Annuler", on_click=annuler_suppression)
        else:
            st.info("Aucun mouvement de stock enregistré.")
    if st.session_state.get("need_rerun", False):
        st.session_state.need_rerun = False  # Réinitialise pour éviter boucle infinie
        st.rerun()  # 👈 Là, c’est safe de le faire

# Pour tester ce module individuellement
if __name__ == "__main__":
    import sys
    import os
    
    # Ajuster le chemin pour importer le module database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    # Configurer la page
    st.set_page_config(page_title="Mouvements de Stock", page_icon="🔄", layout="wide")
    
    # Exécuter l'application
    app()