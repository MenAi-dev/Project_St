import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io
from database import lister_commandes, details_commande, lister_produits, supprimer_commande

def app():
    st.title("📚 Historique des Ventes")
    
    # Initialiser les états de session pour la suppression des commandes
    if "confirmer_suppression_commande" not in st.session_state:
        st.session_state.confirmer_suppression_commande = False
    if "commande_a_supprimer" not in st.session_state:
        st.session_state.commande_a_supprimer = None
    if "do_rerun" not in st.session_state:
        st.session_state.do_rerun = False

    
    # Fonctions de callback pour la gestion des boutons
    def demander_confirmation_commande(commande_id):
        st.session_state.confirmer_suppression_commande = True
        st.session_state.commande_a_supprimer = commande_id
    
    def confirmer_suppression_commande():
        if st.session_state.commande_a_supprimer:
            supprimer_commande(st.session_state.commande_a_supprimer)
            st.session_state.confirmer_suppression_commande = False
            st.session_state.commande_a_supprimer = None
            st.session_state.do_rerun = True  # 🔁 On déclenche le rerun à la fin du script
    
    def annuler_suppression_commande():
        st.session_state.confirmer_suppression_commande = False
        st.session_state.commande_a_supprimer = None
        st.rerun()
    
    # Récupérer l'historique des commandes
    commandes = lister_commandes()
    
    if not commandes.empty:
        # Convertir les dates pour filtrage
        commandes['date'] = pd.to_datetime(commandes['date'])
        
        # Filtres
        st.subheader("Filtres")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre par période prédéfinie
            periode_options = [
                "Toutes les périodes",
                "Aujourd'hui",
                "Cette semaine",
                "Ce mois",
                "Les 3 derniers mois",
                "Cette année"
            ]
            periode = st.selectbox("Période", options=periode_options)
            
            # Appliquer le filtre de période
            today = datetime.now().date()
            if periode == "Aujourd'hui":
                commandes = commandes[commandes['date'].dt.date == today]
            elif periode == "Cette semaine":
                start_of_week = today - timedelta(days=today.weekday())
                commandes = commandes[commandes['date'].dt.date >= start_of_week]
            elif periode == "Ce mois":
                start_of_month = today.replace(day=1)
                commandes = commandes[commandes['date'].dt.date >= start_of_month]
            elif periode == "Les 3 derniers mois":
                three_months_ago = today - timedelta(days=90)
                commandes = commandes[commandes['date'].dt.date >= three_months_ago]
            elif periode == "Cette année":
                start_of_year = today.replace(month=1, day=1)
                commandes = commandes[commandes['date'].dt.date >= start_of_year]
        
        with col2:
# Filtre par montant
# Filtre par montant
            if not commandes.empty:
                montant_min_total = int(commandes['total'].min())
                montant_max_total = int(commandes['total'].max())
                
                if montant_min_total == montant_max_total:
                    st.info(f"Toutes les commandes ont un montant de {montant_min_total:,} FCFA.")
                    min_montant, max_montant = montant_min_total, montant_max_total
                else:
                    st.markdown("**Filtrer par montant total (FCFA)**")
                    min_montant, max_montant = st.slider(
                        "Sélectionnez la plage de montants",
                        min_value=montant_min_total,
                        max_value=montant_max_total,
                        value=(montant_min_total, montant_max_total),
                        step=1000
                    )
                
                commandes = commandes[
                    (commandes['total'] >= min_montant) & 
                    (commandes['total'] <= max_montant)
                ]
        
        with col3:
            # Filtre par client
            clients = ["Tous les clients"] + sorted(commandes['client'].unique().tolist())
            client_filtre = st.selectbox("Client", options=clients)
            
            if client_filtre != "Tous les clients":
                commandes = commandes[commandes['client'] == client_filtre]
        
        # Afficher les statistiques
        st.subheader("Statistiques")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Nombre de Ventes", 
                value=f"{len(commandes)}"
            )
        
        with col2:
            st.metric(
                label="Montant Total", 
                value=f"{commandes['total'].sum():,.0f} FCFA"
            )
        
        with col3:
            if not commandes.empty:
                st.metric(
                    label="Panier Moyen", 
                    value=f"{commandes['total'].mean():,.0f} FCFA"
                )
            else:
                st.metric(
                    label="Panier Moyen", 
                    value="0 FCFA"
                )
        
        # Afficher l'historique
        st.subheader("Historique des Commandes")
        
        if not commandes.empty:
            # Formater pour l'affichage
            commandes_display = commandes.copy()
            commandes_display['date'] = commandes_display['date'].dt.strftime('%d/%m/%Y')
            commandes_display['total'] = commandes_display['total'].apply(lambda x: f"{x:,.0f} FCFA")
            
            # Afficher le tableau sans le bouton d'action
            st.dataframe(
                commandes_display[['id', 'date', 'client', 'total']],
                hide_index=True,
                use_container_width=True
            )
            
            # Section pour supprimer une commande
            st.subheader("Supprimer une Commande")
            commande_ids = commandes['id'].tolist()
            commande_a_supprimer = st.selectbox("Sélectionnez une commande à supprimer", commande_ids)
            
            # Logique de suppression avec confirmation
            if not st.session_state.confirmer_suppression_commande:
                if st.button("Supprimer cette commande"):
                    demander_confirmation_commande(commande_a_supprimer)
            else:
                # Afficher message de confirmation
                st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer la commande #{st.session_state.commande_a_supprimer}?")
                
                # Boutons de confirmation et d'annulation
                conf_col1, conf_col2 = st.columns(2)
                with conf_col1:
                    st.button("✅ Confirmer", on_click=confirmer_suppression_commande)
                with conf_col2:
                    st.button("❌ Annuler", on_click=annuler_suppression_commande)
            
            # Exporter les données
            col1, col2 = st.columns(2)
            
            with col1:
                # Export CSV
                csv = commandes.to_csv(index=False)
                st.download_button(
                    label="📄 Télécharger en CSV",
                    data=csv,
                    file_name="historique_ventes.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Export Excel
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer) as writer:
                    commandes.to_excel(writer, index=False, sheet_name="Ventes")
                
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="📊 Télécharger en Excel",
                    data=excel_data,
                    file_name="historique_ventes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Visualisation
            st.subheader("Visualisation")
            
            # Choisir le type de graphique
            graph_type = st.radio(
                "Type de graphique",
                options=["Ventes par jour", "Ventes par client", "Évolution des ventes"],
                horizontal=True
            )
            
            if graph_type == "Ventes par jour":
                # Regrouper par jour
                ventes_quotidiennes = commandes.groupby(commandes['date'].dt.date).agg({
                    'id': 'count',
                    'total': 'sum'
                }).reset_index()
                ventes_quotidiennes.columns = ['date', 'nombre_ventes', 'montant_total']
                
                # Créer le graphique
                fig, ax1 = plt.subplots(figsize=(10, 5))
                
                # Axe principal pour le nombre de ventes
                ax1.set_xlabel('Date')
                ax1.set_ylabel('Nombre de Ventes', color='tab:blue')
                ax1.bar(ventes_quotidiennes['date'], ventes_quotidiennes['nombre_ventes'], color='tab:blue', alpha=0.7)
                ax1.tick_params(axis='y', labelcolor='tab:blue')
                
                # Axe secondaire pour le montant total
                ax2 = ax1.twinx()
                ax2.set_ylabel('Montant Total (FCFA)', color='tab:red')
                ax2.plot(ventes_quotidiennes['date'], ventes_quotidiennes['montant_total'], color='tab:red', marker='o')
                ax2.tick_params(axis='y', labelcolor='tab:red')
                
                # Format de la date sur l'axe X
                plt.xticks(rotation=45)
                fig.tight_layout()
                
                st.pyplot(fig)
                
            elif graph_type == "Ventes par client":
                # Regrouper par client
                ventes_par_client = commandes.groupby('client').agg({
                    'id': 'count',
                    'total': 'sum'
                }).reset_index()
                ventes_par_client.columns = ['client', 'nombre_ventes', 'montant_total']
                ventes_par_client = ventes_par_client.sort_values('montant_total', ascending=False).head(10)
                
                # Créer le graphique
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.barh(ventes_par_client['client'], ventes_par_client['montant_total'], color='skyblue')
                
                # Ajouter les valeurs sur les barres
                for bar in bars:
                    width = bar.get_width()
                    label_x_pos = width * 1.01
                    ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:,.0f} FCFA',
                            va='center')
                
                ax.set_xlabel('Montant Total (FCFA)')
                ax.set_ylabel('Client')
                ax.set_title('Top 10 des Clients par Montant Total')
                
                fig.tight_layout()
                st.pyplot(fig)
                
            elif graph_type == "Évolution des ventes":
                # Regrouper par mois
                commandes['mois'] = commandes['date'].dt.to_period('M')
                ventes_mensuelles = commandes.groupby('mois').agg({
                    'id': 'count',
                    'total': 'sum'
                }).reset_index()
                ventes_mensuelles['mois'] = ventes_mensuelles['mois'].dt.to_timestamp()
                ventes_mensuelles.columns = ['mois', 'nombre_ventes', 'montant_total']
                
                # Créer le graphique
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(ventes_mensuelles['mois'], ventes_mensuelles['montant_total'], 
                       marker='o', linestyle='-', color='green')
                
                # Ajouter les points avec les valeurs
                for i, point in enumerate(ventes_mensuelles['montant_total']):
                    ax.text(ventes_mensuelles['mois'].iloc[i], point + point*0.03, 
                           f'{point:,.0f}', ha='center')
                
                ax.set_xlabel('Mois')
                ax.set_ylabel('Montant Total (FCFA)')
                ax.set_title('Évolution des Ventes Mensuelles')
                
                plt.xticks(rotation=45)
                fig.tight_layout()
                st.pyplot(fig)
            
            # Afficher les détails d'une commande
            st.subheader("Détails d'une Commande")
            commande_id = st.selectbox(
                "Sélectionnez une commande pour voir les détails",
                options=commandes['id'].tolist(),
                format_func=lambda x: f"Commande #{x} - {commandes.loc[commandes['id'] == x, 'client'].iloc[0]} - {commandes.loc[commandes['id'] == x, 'date'].iloc[0].strftime('%d/%m/%Y')} - {commandes.loc[commandes['id'] == x, 'total'].iloc[0]:,.0f} FCFA"
            )
            
            # Récupérer et afficher les détails
            details = details_commande(commande_id)
            
            if not details.empty:
                # Formater pour l'affichage
                details_display = details.copy()
                details_display['prix_unitaire'] = details_display['prix_unitaire'].apply(lambda x: f"{x:,.0f} FCFA")
                details_display['sous_total'] = details_display['sous_total'].apply(lambda x: f"{x:,.0f} FCFA")
                
                st.dataframe(details_display, hide_index=True, use_container_width=True)
                
                # Récupérer les infos de la commande sélectionnée
                commande_info = commandes[commandes['id'] == commande_id].iloc[0]
                
                # Option pour générer un reçu
                if st.button("Générer un Reçu", key="gen_recu_historique"):
                    from modules.orders import generer_recu
                    
                    # Convertir les détails en format pour la fonction generer_recu
                    produits_commandes = []
                    for _, row in details.iterrows():
                        produits_commandes.append({
                            'id': row['produit_id'],
                            'quantite': row['quantite'],
                            'prix_unitaire': row['prix_unitaire']
                        })                    
                    generer_recu(commande_id, 
                               commande_info['client'], 
                               commande_info['date'], 
                               commande_info['total'], 
                               produits_commandes,
                               produits_df=lister_produits())
        else:
            st.info("Aucune commande correspondant aux critères de filtrage.")
    else:
        st.info("Aucune commande enregistrée.")

# Pour tester ce module individuellement
if __name__ == "__main__":
    import sys
    import os
    
    # Ajuster le chemin pour importer le module database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    # Configurer la page
    st.set_page_config(page_title="Historique des Ventes", page_icon="📚", layout="wide")
    
    # Exécuter l'application
    app()

if st.session_state.get("do_rerun", False):
    st.session_state.do_rerun = False
    st.rerun()  # ✅ Ici ça fonctionne
