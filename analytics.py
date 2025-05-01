import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import io
from database import lister_produits, lister_commandes, details_commande
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
    st.title("📈 Graphiques & Analyses")
    
    # Récupérer les données
    produits = lister_produits()
    commandes = lister_commandes()
    
    if commandes.empty:
        st.warning("Aucune donnée de vente disponible pour l'analyse. Veuillez d'abord enregistrer des commandes.")
        return
    
    # Préparation des données
    commandes['date'] = pd.to_datetime(commandes['date'])
    
    # Créer un DataFrame complet pour l'analyse
    detailed_sales = []
    
    for _, commande in commandes.iterrows():
        details = details_commande(commande['id'])
        
        if not details.empty:
            for _, detail in details.iterrows():
                detailed_sales.append({
                    'commande_id': commande['id'],
                    'date': commande['date'],
                    'client': commande['client'],
                    'produit': detail['nom'],
                    'categorie': detail.get('categorie', 'Non spécifiée'),
                    'quantite': detail['quantite'],
                    'prix_unitaire': detail['prix_unitaire'],
                    'sous_total': detail['sous_total']
                })
    
    if not detailed_sales:
        st.warning("Aucun détail de vente disponible pour l'analyse.")
        return
    
    sales_df = pd.DataFrame(detailed_sales)
    
    # Sélection du type d'analyse
    analysis_type = st.selectbox(
        "Type d'Analyse",
        options=[
            "Produits les Plus Vendus",
            "Répartition des Ventes par Catégorie",
            "Évolution des Ventes",
            "Corrélation Prix vs Quantité",
            "Analyse des Pics de Vente"
        ]
    )
    
    # Analyse 1: Produits les plus vendus
    if analysis_type == "Produits les Plus Vendus":
        st.subheader("Top Produits")
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            # Filtre de période
            periode_options = [
                "Toutes les périodes",
                "7 derniers jours",
                "30 derniers jours",
                "90 derniers jours",
                "Cette année"
            ]
            periode = st.selectbox("Période", options=periode_options)
            
            # Appliquer le filtre de période
            today = datetime.now().date()
            filtered_sales = sales_df.copy()
            
            if periode == "7 derniers jours":
                seven_days_ago = today - timedelta(days=7)
                filtered_sales = filtered_sales[filtered_sales['date'].dt.date >= seven_days_ago]
            elif periode == "30 derniers jours":
                thirty_days_ago = today - timedelta(days=30)
                filtered_sales = filtered_sales[filtered_sales['date'].dt.date >= thirty_days_ago]
            elif periode == "90 derniers jours":
                ninety_days_ago = today - timedelta(days=90)
                filtered_sales = filtered_sales[filtered_sales['date'].dt.date >= ninety_days_ago]
            elif periode == "Cette année":
                start_of_year = datetime(today.year, 1, 1).date()
                filtered_sales = filtered_sales[filtered_sales['date'].dt.date >= start_of_year]
        
        with col2:
            # Nombre de produits à afficher
            n_products = st.slider("Nombre de produits à afficher", min_value=3, max_value=20, value=10)
        
        # Agrégation des ventes par produit
        product_sales = filtered_sales.groupby('produit').agg({
            'quantite': 'sum',
            'sous_total': 'sum'
        }).reset_index()
        
        # Trier par quantité vendue
        product_sales = product_sales.sort_values('quantite', ascending=False).head(n_products)
        
        # Afficher le tableau des résultats
        st.subheader("Tableau des produits les plus vendus")
        product_sales_display = product_sales.copy()
        product_sales_display['sous_total'] = product_sales_display['sous_total'].apply(lambda x: f"{x:,.0f} FCFA")
        product_sales_display.columns = ['Produit', 'Quantité Vendue', 'Montant Total']
        
        st.dataframe(product_sales_display, hide_index=True, use_container_width=True)
        
        # Graphique à barres horizontales
        st.subheader("Histogramme des produits les plus vendus")
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.update_layout(
        plot_bgcolor='#FAFAFA',
        paper_bgcolor='#FFFFFF',
        font=dict(color='#212121'),
        title_font=dict(size=20, color='#4CAF50')
    )

        
        # Inverser l'ordre pour que le plus vendu soit en haut
        bars = ax.barh(
            product_sales['produit'][::-1], 
            product_sales['quantite'][::-1],
            color=sns.color_palette("Blues_r", n_products)
        )
        
        # Ajouter les valeurs sur les barres
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{width:.0f}', 
                   ha='left', va='center')
        
        ax.set_xlabel('Quantité Vendue')
        ax.set_ylabel('Produit')
        ax.set_title('Produits les Plus Vendus')
        
        # Ajuster les marges
        plt.tight_layout()
        st.pyplot(fig)
        
        # Option d'exportation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Exporter en CSV"):
                csv_data = product_sales.to_csv(index=False)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv_data,
                    file_name="produits_plus_vendus.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Exporter le graphique"):
                fig_buffer = io.BytesIO()
                plt.savefig(fig_buffer, format='png', dpi=300, bbox_inches='tight')
                fig_buffer.seek(0)

                
                st.download_button(
                    label="Télécharger Image",
                    data=fig_buffer,
                    file_name="produits_plus_vendus.png",
                    mime="image/png"
                )
    
    # Analyse 2: Répartition des ventes par catégorie
    elif analysis_type == "Répartition des Ventes par Catégorie":
        st.subheader("Répartition des Ventes par Catégorie")
        
        # Obtenir les informations de catégorie depuis la table produits
        if 'categorie' not in sales_df.columns:
            # On va essayer de récupérer les catégories depuis la table produits
            categories_mapping = {}
            for _, produit in produits.iterrows():
                categories_mapping[produit['nom']] = produit['categorie']
            
            # Appliquer le mapping
            sales_df['categorie'] = sales_df['produit'].map(categories_mapping)
        
        # Agrégation par catégorie
        category_sales = sales_df.groupby('categorie').agg({
            'sous_total': 'sum',
            'quantite': 'sum',
            'commande_id': 'nunique'
        }).reset_index()
        
        category_sales.columns = ['Catégorie', 'Montant Total', 'Quantité Totale', 'Nombre de Commandes']
        
        # Afficher les résultats
        st.subheader("Tableau des ventes par catégorie")
        category_display = category_sales.copy()
        category_display['Montant Total'] = category_display['Montant Total'].apply(lambda x: f"{x:,.0f} FCFA")
        
        st.dataframe(category_display, hide_index=True, use_container_width=True)
        
        # Graphique en camembert
        st.subheader("Répartition du montant des ventes par catégorie")
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        
        # Créer un camembert
        wedges, texts, autotexts = ax1.pie(
            category_sales['Montant Total'], 
            labels=category_sales['Catégorie'],
            autopct='%1.1f%%',
            startangle=90,
            colors=sns.color_palette("Set3", len(category_sales))
        )
        
        # Égaliser les axes pour un cercle parfait
        ax1.axis('equal')
        
        # Ajouter une légende
        ax1.legend(wedges, category_sales['Catégorie'], title="Catégories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.setp(autotexts, size=8, weight="bold")
        plt.title("Répartition du montant des ventes par catégorie")
        
        plt.tight_layout()
        st.pyplot(fig1)
        
        # Graphique à barres pour la quantité
        st.subheader("Quantité vendue par catégorie")
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        bars = ax2.bar(
            category_sales['Catégorie'], 
            category_sales['Quantité Totale'],
            color=sns.color_palette("Set2", len(category_sales))
        )
        
        # Ajouter les valeurs sur les barres
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.0f}', ha='center', va='bottom')
        
        ax2.set_xlabel('Catégorie')
        ax2.set_ylabel('Quantité Vendue')
        ax2.set_title('Quantité vendue par catégorie')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)
    
    # Analyse 3: Évolution des ventes
    elif analysis_type == "Évolution des Ventes":
        st.subheader("Évolution des Ventes dans le Temps")
        
        # Options de granularité
        granularity = st.radio(
            "Granularité temporelle",
            options=["Jour", "Semaine", "Mois"],
            horizontal=True
        )
        
        # Grouper par période selon la granularité choisie
        if granularity == "Jour":
            sales_df['periode'] = sales_df['date'].dt.date
            title_granularity = "journalière"
        elif granularity == "Semaine":
            sales_df['periode'] = sales_df['date'].dt.to_period('W').dt.start_time
            title_granularity = "hebdomadaire"
        else:  # Mois
            sales_df['periode'] = sales_df['date'].dt.to_period('M').dt.start_time
            title_granularity = "mensuelle"
        
        # Agrégation par période
        time_sales = sales_df.groupby('periode').agg({
            'sous_total': 'sum',
            'quantite': 'sum',
            'commande_id': pd.Series.nunique
        }).reset_index()
        
        time_sales.columns = ['Période', 'Montant Total', 'Quantité', 'Nombre de Commandes']
        
        # Créer un graphique d'évolution
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Tracer la ligne du montant total
        color = 'tab:blue'
        ax1.set_xlabel('Période')
        ax1.set_ylabel('Montant Total (FCFA)', color=color)
        ax1.plot(time_sales['Période'], time_sales['Montant Total'], color=color, marker='o')
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Créer un axe secondaire pour la quantité
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Quantité', color=color)
        ax2.plot(time_sales['Période'], time_sales['Quantité'], color=color, marker='s', linestyle='--')
        ax2.tick_params(axis='y', labelcolor=color)
        
        # Formater les dates sur l'axe x
        plt.xticks(rotation=45)
        plt.title(f'Évolution {title_granularity} des ventes')
        
        fig.tight_layout()
        st.pyplot(fig)
        
        # Tableau des données
        st.subheader(f"Tableau d'évolution {title_granularity}")
        
        time_sales_display = time_sales.copy()
        # Formater la période en fonction de la granularité
        if granularity == "Jour":
            time_sales_display['Période'] = time_sales_display['Période'].dt.strftime('%d/%m/%Y')
        elif granularity == "Semaine":
            time_sales_display['Période'] = time_sales_display['Période'].dt.strftime('Sem. %W - %Y')
        else:  # Mois
            time_sales_display['Période'] = time_sales_display['Période'].dt.strftime('%b %Y')
            
        time_sales_display['Montant Total'] = time_sales_display['Montant Total'].apply(lambda x: f"{x:,.0f} FCFA")
        
        st.dataframe(time_sales_display, hide_index=True, use_container_width=True)
    
    # Analyse 4: Corrélation Prix vs Quantité
    elif analysis_type == "Corrélation Prix vs Quantité":
        st.subheader("Corrélation entre Prix Unitaire et Quantité Vendue")
        
        # Agréger les ventes par produit
        price_qty_data = sales_df.groupby(['produit', 'prix_unitaire']).agg({
            'quantite': 'sum'
        }).reset_index()
        
        # Créer un nuage de points avec régression
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Scatter plot
        scatter = sns.regplot(
            x='prix_unitaire', 
            y='quantite', 
            data=price_qty_data, 
            scatter_kws={"alpha": 0.6, "s": 80},
            line_kws={"color": "red"}
        )
        
        # Ajouter des labels pour les points
        for _, row in price_qty_data.iterrows():
            ax.annotate(
                row['produit'],
                (row['prix_unitaire'], row['quantite']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8
            )
        
        ax.set_xlabel('Prix Unitaire (FCFA)')
        ax.set_ylabel('Quantité Vendue')
        ax.set_title('Corrélation entre Prix Unitaire et Quantité Vendue')
        
        # Calculer la corrélation
        correlation = price_qty_data['prix_unitaire'].corr(price_qty_data['quantite'])
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Afficher le coefficient de corrélation
        st.metric(
            label="Coefficient de Corrélation", 
            value=f"{correlation:.3f}",
            delta=None,
            delta_color="normal"
        )
        
        # Interprétation
        st.subheader("Interprétation")
        if correlation < -0.5:
            st.info("Il existe une forte corrélation négative: les produits moins chers se vendent généralement en plus grande quantité.")
        elif correlation < -0.3:
            st.info("Il existe une corrélation négative modérée: une tendance à vendre plus de produits moins chers.")
        elif correlation < -0.1:
            st.info("Il existe une faible corrélation négative: une légère tendance à vendre plus de produits moins chers.")
        elif correlation < 0.1:
            st.info("Il n'y a pas de corrélation significative entre le prix et la quantité vendue.")
        elif correlation < 0.3:
            st.info("Il existe une faible corrélation positive: une légère tendance à vendre plus de produits plus chers.")
        elif correlation < 0.5:
            st.info("Il existe une corrélation positive modérée: une tendance à vendre plus de produits plus chers.")
        else:
            st.info("Il existe une forte corrélation positive: les produits plus chers se vendent généralement en plus grande quantité.")
        
        # Tableau des données
        st.subheader("Tableau des prix et quantités")
        
        price_qty_display = price_qty_data.copy()
        price_qty_display['prix_unitaire'] = price_qty_display['prix_unitaire'].apply(lambda x: f"{x:,.0f} FCFA")
        price_qty_display.columns = ['Produit', 'Prix Unitaire', 'Quantité Vendue']
        
        st.dataframe(price_qty_display, hide_index=True, use_container_width=True)
    
    # Analyse 5: Analyse des pics de vente
    elif analysis_type == "Analyse des Pics de Vente":
        st.subheader("Analyse des Pics de Vente (KDE)")
        
        # Filtres
        col1, col2 = st.columns(2)
        
        with col1:
            metric = st.radio(
                "Métrique à analyser",
                options=["Montant des ventes", "Quantité vendue"],
                horizontal=True
            )
        
        with col2:
            granularity = st.radio(
                "Granularité temporelle",
                options=["Heure", "Jour de la semaine", "Jour du mois"],
                horizontal=True
            )
        
        # Préparer les données selon la granularité
        if granularity == "Heure":
            sales_df['time_unit'] = sales_df['date'].dt.hour
            x_label = "Heure de la journée"
            x_ticks = range(24)
            x_ticks_labels = [f"{h}h" for h in range(24)]
        elif granularity == "Jour de la semaine":
            sales_df['time_unit'] = sales_df['date'].dt.dayofweek
            x_label = "Jour de la semaine"
            x_ticks = range(7)
            x_ticks_labels = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        else:  # Jour du mois
            sales_df['time_unit'] = sales_df['date'].dt.day
            x_label = "Jour du mois"
            x_ticks = range(1, 32)
            x_ticks_labels = [str(d) for d in range(1, 32)]
        
        # Sélectionner la métrique
        y_values = sales_df['sous_total'] if metric == "Montant des ventes" else sales_df['quantite']
        y_label = "Montant des ventes (FCFA)" if metric == "Montant des ventes" else "Quantité vendue"
        
        # Créer le graphique KDE
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Tracer le KDE
        sns.kdeplot(
            x=sales_df['time_unit'],
            weights=y_values,
            fill=True,
            alpha=0.5,
            ax=ax
        )
        
        # Ajouter des points pour les valeurs réelles agrégées
        time_agg = sales_df.groupby('time_unit').agg({
            'sous_total': 'sum',
            'quantite': 'sum'
        }).reset_index()
        
        y_agg = time_agg['sous_total'] if metric == "Montant des ventes" else time_agg['quantite']
        
        ax.scatter(
            time_agg['time_unit'],
            y_agg,
            color='red',
            alpha=0.7,
            s=50,
            zorder=5
        )
        
        # Ajouter les étiquettes
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(f"Distribution de {y_label} par {x_label.lower()}")
        
        # Ajouter les ticks appropriés
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_ticks_labels, rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Trouver les pics
        peaks = time_agg.sort_values('sous_total' if metric == "Montant des ventes" else 'quantite', ascending=False).head(3)
        
        # Afficher les pics
        st.subheader(f"Top 3 des {x_label.lower()}s avec le plus de ventes")
        
        peaks_display = peaks.copy()
        
        # Formater pour l'affichage
        if granularity == "Jour de la semaine":
            peaks_display['time_unit'] = peaks_display['time_unit'].map({
                0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 
                4: "Vendredi", 5: "Samedi", 6: "Dimanche"
            })
        elif granularity == "Heure":
            peaks_display['time_unit'] = peaks_display['time_unit'].apply(lambda x: f"{x}h")
        
        peaks_display['sous_total'] = peaks_display['sous_total'].apply(lambda x: f"{x:,.0f} FCFA")
        peaks_display.columns = [x_label, 'Montant Total', 'Quantité Totale']
        
        st.dataframe(peaks_display, hide_index=True, use_container_width=True)
        
        # Interprétation
        st.subheader("Interprétation")
        if granularity == "Heure":
            st.info("Ce graphique montre les heures de la journée où les ventes sont les plus élevées. Les pics indiquent les moments où l'activité commerciale est la plus intense.")
        elif granularity == "Jour de la semaine":
            st.info("Ce graphique montre quels jours de la semaine génèrent le plus de ventes. Cela peut vous aider à optimiser vos horaires d'ouverture ou votre personnel.")
        else:
            st.info("Ce graphique montre quels jours du mois génèrent le plus de ventes. Cela peut vous aider à identifier des tendances mensuelles importantes (jour de paie, début/fin de mois, etc).")
            
# Pour tester ce module individuellement
if __name__ == "__main__":
    import sys
    import os
    
    # Ajuster le chemin pour importer le module database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    # Configurer la page
    st.set_page_config(page_title="Graphiques & Analyses", page_icon="📈", layout="wide")
    
    # Exécuter l'application
    app()