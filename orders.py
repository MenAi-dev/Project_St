import streamlit as st
import pandas as pd
from datetime import datetime
import io
from database import lister_produits, creer_commande, details_commande, supprimer_commande, lister_commandes
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import tempfile

def app():
    st.title("🛒 Commandes Clients")
    
    tab1, tab2 = st.tabs(["📝 Nouvelle Commande", "🔍 Détails d'une Commande"])
    
    # Onglet 1: Nouvelle commande
    with tab1:
        st.subheader("Créer une Nouvelle Commande")
        
        # Récupérer la liste des produits
        produits = lister_produits()
        
        if not produits.empty:
            with st.form("commande_form"):
                # Informations du client
                client = st.text_input("Nom du Client", placeholder="Entrez le nom du client...")
                
                # Date (par défaut aujourd'hui)
                date = st.date_input("Date", value=datetime.now())
                
                st.subheader("Sélection des Produits")
                
                # Initialiser la session state pour le panier si nécessaire
                if 'panier' not in st.session_state:
                    st.session_state.panier = []
                
                # Sélection du produit
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    produit_id = st.selectbox(
                        "Produit",
                        options=produits['id'].tolist(),
                        format_func=lambda x: f"{produits.loc[produits['id'] == x, 'nom'].iloc[0]} - Prix: {produits.loc[produits['id'] == x, 'prix_unitaire'].iloc[0]:,.0f} FCFA - Stock: {produits.loc[produits['id'] == x, 'stock'].iloc[0]}"
                    )
                
                with col2:
                    stock_dispo = produits.loc[produits['id'] == produit_id, 'stock'].iloc[0]
                    quantite = st.number_input("Quantité", min_value=1, max_value=stock_dispo, step=1)
                
                with col3:
                    add_btn = st.form_submit_button("Ajouter")
                
                # Afficher le panier actuel
                if st.session_state.panier:
                    st.subheader("Panier")
                    
                    panier_data = []
                    total_commande = 0
                    
                    for item in st.session_state.panier:
                        produit_info = produits.loc[produits['id'] == item['id']].iloc[0]
                        sous_total = item['quantite'] * produit_info['prix_unitaire']
                        total_commande += sous_total
                        
                        panier_data.append({
                            'id': item['id'],
                            'nom': produit_info['nom'],
                            'quantite': item['quantite'],
                            'prix_unitaire': f"{produit_info['prix_unitaire']:,.0f} FCFA",
                            'sous_total': f"{sous_total:,.0f} FCFA"
                        })
                    
                    panier_df = pd.DataFrame(panier_data)
                    st.dataframe(panier_df, hide_index=True, use_container_width=True)
                    
                    st.subheader(f"Total: {total_commande:,.0f} FCFA")
                
                submit_commande = st.form_submit_button("Confirmer la Commande")
                # Utiliser form_submit_button au lieu de button
                generer_recu_btn = st.form_submit_button("Générer un Reçu")
                
                if add_btn and not submit_commande:
                    # Ajouter le produit au panier
                    produit_existe = False
                    for i, item in enumerate(st.session_state.panier):
                        if item['id'] == produit_id:
                            st.session_state.panier[i]['quantite'] += quantite
                            produit_existe = True
                            break
                    
                    if not produit_existe:
                        st.session_state.panier.append({
                            'id': produit_id,
                            'quantite': quantite
                        })
                    
                    st.rerun()
                
                if submit_commande:
                    if not client:
                        st.error("❌ Veuillez entrer le nom du client.")
                    elif not st.session_state.panier:
                        st.error("❌ Le panier est vide. Veuillez ajouter des produits.")
                    else:
                        # Calculer le total de la commande
                        total_commande = 0
                        produits_commandes = []
                        
                        for item in st.session_state.panier:
                            produit_info = produits.loc[produits['id'] == item['id']].iloc[0]
                            sous_total = item['quantite'] * produit_info['prix_unitaire']
                            total_commande += sous_total
                            
                            produits_commandes.append({
                                'id': item['id'],
                                'quantite': item['quantite'],
                                'prix_unitaire': produit_info['prix_unitaire']
                            })
                        
                        # Créer la commande
                        date_str = date.strftime("%Y-%m-%d")
                        commande_id = creer_commande(client, date_str, total_commande, produits_commandes)
                        
                        # Afficher la confirmation
                        st.success(f"✅ Commande #{commande_id} créée avec succès!")
                        
                        # Réinitialiser le panier
                        st.session_state.panier = []
                        
                        # Vérifier si le bouton générer reçu a été cliqué
                        if generer_recu_btn:
                            generer_recu(commande_id, client, date_str, total_commande, produits_commandes, produits)
                        
                        st.rerun()
        else:
            st.warning("Aucun produit disponible. Veuillez d'abord ajouter des produits dans la gestion de stock.")
    
    # Onglet 2: Détails d'une commande
    with tab2:
        commandes = lister_commandes()
        
        if not commandes.empty:
            # Formater les dates pour un meilleur affichage
            commandes_display = commandes.copy()
            commandes_display['date'] = pd.to_datetime(commandes_display['date']).dt.strftime('%d/%m/%Y')
            
            # Sélection de la commande
            commande_id = st.selectbox(
                "Sélectionnez une commande",
                options=commandes['id'].tolist(),
                format_func=lambda x: f"Commande #{x} - {commandes_display.loc[commandes_display['id'] == x, 'client'].iloc[0]} - {commandes_display.loc[commandes_display['id'] == x, 'date'].iloc[0]} - {commandes_display.loc[commandes_display['id'] == x, 'total'].iloc[0]:,.0f} FCFA"
            )
            
            # Récupérer les détails de la commande
            details = details_commande(commande_id)
            commande_info = commandes[commandes['id'] == commande_id].iloc[0]
            
            if not details.empty:
                # Afficher les informations de la commande
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Client:** {commande_info['client']}")
                with col2:
                    date_formatted = pd.to_datetime(commande_info['date']).strftime('%d/%m/%Y')
                    st.info(f"**Date:** {date_formatted}")
                with col3:
                    st.info(f"**Total:** {commande_info['total']:,.0f} FCFA")
                
                # Afficher les détails des produits
                st.subheader("Produits commandés")
                
                # Formater le tableau pour l'affichage
                details_display = details.copy()
                details_display['prix_unitaire'] = details_display['prix_unitaire'].apply(lambda x: f"{x:,.0f} FCFA")
                details_display['sous_total'] = details_display['sous_total'].apply(lambda x: f"{x:,.0f} FCFA")
                
                st.dataframe(details_display, hide_index=True, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                # Générer un reçu pour une commande existante
                with col1:
                    if st.button("📄 Générer un Reçu", key="gen_recu_existant"):
                        # Convertir les détails en format pour la fonction generer_recu
                        produits_commandes = []
                        for _, row in details.iterrows():
                            produits_commandes.append({
                                'id': row['produit_id'],  # ID du produit
                                'quantite': row['quantite'],
                                'prix_unitaire': row['prix_unitaire']
                            })
                        
                        generer_recu(commande_id, 
                                  commande_info['client'], 
                                  commande_info['date'], 
                                  commande_info['total'], 
                                  produits_commandes,
                                  lister_produits())
                
                # Ajouter un bouton de suppression
                with col2:
                    if st.button("🗑️ Supprimer cette commande", key="delete_order"):
                        # Afficher une confirmation
                        st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer la commande #{commande_id}?")
                        confirm_col1, confirm_col2 = st.columns(2)
                        
                        with confirm_col1:
                            if st.button("✅ Confirmer", key=f"confirm_delete_{commande_id}"):
                                supprimer_commande(commande_id)
                                st.success(f"✅ Commande #{commande_id} supprimée avec succès!")
                                st.rerun()
                        
                        with confirm_col2:
                            if st.button("❌ Annuler", key=f"cancel_delete_{commande_id}"):
                                st.rerun()
        else:
            st.info("Aucune commande enregistrée.")
    
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import pandas as pd
import streamlit as st

import os
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import pandas as pd
import streamlit as st

def generer_recu(commande_id, client, date, total, produits_commandes, produits_df):
    """Génère un reçu PDF simple et clair pour la commande."""
    
    # Vérifier que produits_df n'est pas None et est un DataFrame
    if produits_df is None or not isinstance(produits_df, pd.DataFrame):
        st.error("Erreur: La liste des produits n'est pas disponible.")
        return
    
    # S'assurer que le DataFrame contient les colonnes nécessaires
    required_columns = ['id', 'nom']
    if not all(col in produits_df.columns for col in required_columns):
        st.error("Erreur: Le DataFrame des produits ne contient pas toutes les colonnes nécessaires.")
        return

    # Création du fichier PDF temporaire
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)
    largeur, hauteur = A4

    # --- Logo (facultatif) ---
    logo_path = "Assets/MoCosmetik.png"  # Chemin relatif dans votre projet
    
    logo_added = False
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            c.drawImage(logo, 50, hauteur - 100, width=80, height=80)
            logo_added = True
        except Exception as e:
            st.warning(f"Le logo local n'a pas pu être chargé : {e}")
    
    # --- En-tête ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(150, hauteur - 50, "ROYAL COSMETIK - REÇU")
    
    c.setFont("Helvetica", 11)
    c.drawString(50, hauteur - 100, f"Commande n° : {commande_id}")
    c.drawString(50, hauteur - 115, f"Client : {client}")
    c.drawString(50, hauteur - 130, f"Date : {pd.to_datetime(date).strftime('%d/%m/%Y')}")

    # --- Tableau des produits ---
    c.setFont("Helvetica-Bold", 11)
    y = hauteur - 170
    c.drawString(50, y, "Produit")
    c.drawString(250, y, "Quantité")
    c.drawString(350, y, "Prix U.")
    c.drawString(450, y, "Sous-total")
    
    c.setFont("Helvetica", 10)
    y -= 20
    for item in produits_commandes:
        produit_id = item['id']
        # Vérifier si le produit existe dans le DataFrame
        produit_row = produits_df[produits_df['id'] == produit_id]
        
        if not produit_row.empty:
            nom = produit_row['nom'].iloc[0]
        else:
            # Si le produit n'est pas trouvé, utiliser un nom générique
            nom = f"Produit ID: {produit_id}"
            st.warning(f"Produit avec ID {produit_id} non trouvé dans la liste des produits")
        
        quantite = item['quantite']
        prix_u = item['prix_unitaire']
        sous_total = quantite * prix_u

        c.drawString(50, y, nom)
        c.drawString(250, y, str(quantite))
        c.drawString(350, y, f"{prix_u:,.0f} FCFA")
        c.drawString(450, y, f"{sous_total:,.0f} FCFA")
        y -= 18

    # --- Total ---
    c.setFont("Helvetica-Bold", 12)
    y -= 20
    c.drawString(350, y, "Total :")
    c.drawString(450, y, f"{total:,.0f} FCFA")

    # --- Pied de page ---
    y -= 40
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, y, "Merci pour votre achat ! Contact : client@royalcosmetik.ci")

    c.save()

    # Lecture du PDF pour Streamlit
    with open(temp_file.name, "rb") as f:
        pdf = f.read()

    st.download_button(
        label="📥 Télécharger le reçu (PDF)",
        data=pdf,
        file_name=f"recu_{commande_id}.pdf",
        mime="application/pdf"
    )

# Pour tester ce module individuellement
if __name__ == "__main__":
    import sys
    import os
    
    # Ajuster le chemin pour importer le module database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    # Configurer la page
    st.set_page_config(page_title="Commandes Clients", page_icon="🛒", layout="wide")
    
    # Exécuter l'application
    app()