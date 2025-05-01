import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import io
from database import lister_commandes, init_db, get_db_connection
import openpyxl
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
    st.title("💰 Gestion de Budget")
    
    # Initialiser la base de données si nécessaire
    init_db()
    
    # Création des tables pour le budget si elles n'existent pas déjà
    init_budget_tables()
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["📊 Aperçu Budget", "💵 Ajouter Transaction", "📜 Historique"])
    
    # Onglet 1: Aperçu du budget
    with tab1:
        apercu_budget()
    
    # Onglet 2: Ajouter une transaction
    with tab2:
        ajouter_transaction()
    
    # Onglet 3: Historique des transactions
    with tab3:
        historique_transactions()

def init_budget_tables():
    """Initialise les tables pour la gestion du budget"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table des transactions (revenus et dépenses)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            description TEXT NOT NULL,
            montant REAL NOT NULL
        )
    ''')
    
    # Table des catégories de dépenses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories_depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Table des catégories de revenus
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories_revenus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Insérer des catégories par défaut si elles n'existent pas déjà
    categories_depenses = ["Achat de produits", "Salaires", "Loyer", "Transport", "Marketing", "Utilités", "Équipement", "Maintenance", "Taxes", "Autres dépenses"]
    categories_revenus = ["Ventes", "Prestations de service", "Remboursements", "Investissements", "Subventions", "Autres revenus"]
    
    for categorie in categories_depenses:
        cursor.execute("INSERT OR IGNORE INTO categories_depenses (nom) VALUES (?)", (categorie,))
    
    for categorie in categories_revenus:
        cursor.execute("INSERT OR IGNORE INTO categories_revenus (nom) VALUES (?)", (categorie,))
    
    conn.commit()
    conn.close()

def lister_categories(type_transaction):
    """Récupère les catégories disponibles selon le type de transaction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if type_transaction == "depense":
        cursor.execute("SELECT nom FROM categories_depenses ORDER BY nom")
    else:  # revenu
        cursor.execute("SELECT nom FROM categories_revenus ORDER BY nom")
    
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return categories

def ajouter_categorie(nom, type_transaction):
    """Ajoute une nouvelle catégorie"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if type_transaction == "depense":
            cursor.execute("INSERT INTO categories_depenses (nom) VALUES (?)", (nom,))
        else:  # revenu
            cursor.execute("INSERT INTO categories_revenus (nom) VALUES (?)", (nom,))
        
        conn.commit()
        result = True
    except Exception as e:
        print(f"Erreur lors de l'ajout de la catégorie: {e}")
        result = False
    
    conn.close()
    return result

def enregistrer_transaction(date, type_transaction, categorie, description, montant):
    """Enregistre une nouvelle transaction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO transactions (date, type, categorie, description, montant) VALUES (?, ?, ?, ?, ?)",
            (date, type_transaction, categorie, description, montant)
        )
        
        conn.commit()
        result = True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de la transaction: {e}")
        result = False
    
    conn.close()
    return result

def lister_transactions(debut=None, fin=None, type_transaction=None, categorie=None):
    """Récupère la liste des transactions avec filtres optionnels"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions"
    params = []
    
    # Construire la requête avec les filtres
    filters = []
    
    if debut:
        filters.append("date >= ?")
        params.append(debut)
    
    if fin:
        filters.append("date <= ?")
        params.append(fin)
    
    if type_transaction:
        filters.append("type = ?")
        params.append(type_transaction)
    
    if categorie:
        filters.append("categorie = ?")
        params.append(categorie)
    
    if filters:
        query += " WHERE " + " AND ".join(filters)
    
    query += " ORDER BY date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convertir en DataFrame
    transactions = pd.DataFrame(rows, columns=["id", "date", "type", "categorie", "description", "montant"])
    
    conn.close()
    return transactions

def calculer_statistiques_budget(debut=None, fin=None):
    """Calcule les statistiques du budget pour la période spécifiée"""
    transactions = lister_transactions(debut, fin)
    
    if transactions.empty:
        return {
            "total_revenus": 0,
            "total_depenses": 0,
            "benefice_net": 0,
            "revenus_par_categorie": pd.DataFrame(),
            "depenses_par_categorie": pd.DataFrame()
        }
    
    # Calculer les totaux
    revenus = transactions[transactions["type"] == "revenu"]
    depenses = transactions[transactions["type"] == "depense"]
    
    total_revenus = revenus["montant"].sum() if not revenus.empty else 0
    total_depenses = depenses["montant"].sum() if not depenses.empty else 0
    benefice_net = total_revenus - total_depenses
    
    # Regrouper par catégorie
    revenus_par_categorie = revenus.groupby("categorie").agg({"montant": "sum"}).reset_index() if not revenus.empty else pd.DataFrame()
    depenses_par_categorie = depenses.groupby("categorie").agg({"montant": "sum"}).reset_index() if not depenses.empty else pd.DataFrame()
    
    return {
        "total_revenus": total_revenus,
        "total_depenses": total_depenses,
        "benefice_net": benefice_net,
        "revenus_par_categorie": revenus_par_categorie,
        "depenses_par_categorie": depenses_par_categorie
    }

def apercu_budget():
    """Affiche l'aperçu du budget"""
    st.subheader("Aperçu du Budget")
    
    # Filtres de période
    col1, col2 = st.columns(2)
    
    with col1:
        periode_options = [
            "Aujourd'hui",
            "Cette semaine",
            "Ce mois",
            "Les 3 derniers mois",
            "Cette année",
            "Tout l'historique"
        ]
        periode = st.selectbox("Période", options=periode_options)
    
    with col2:
        today = datetime.now().date()
        
        # Définir la période en fonction de la sélection
        if periode == "Aujourd'hui":
            date_debut = today.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Cette semaine":
            start_of_week = today - timedelta(days=today.weekday())
            date_debut = start_of_week.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Ce mois":
            start_of_month = today.replace(day=1)
            date_debut = start_of_month.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Les 3 derniers mois":
            three_months_ago = today - timedelta(days=90)
            date_debut = three_months_ago.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Cette année":
            start_of_year = today.replace(month=1, day=1)
            date_debut = start_of_year.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        else:  # Tout l'historique
            date_debut = None
            date_fin = None
        
        # Période sélectionnée
        if date_debut and date_fin:
            st.write(f"Du {pd.to_datetime(date_debut).strftime('%d/%m/%Y')} au {pd.to_datetime(date_fin).strftime('%d/%m/%Y')}")
    
    # Calculer les statistiques pour la période
    stats = calculer_statistiques_budget(date_debut, date_fin)
    
    # Afficher les métriques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total des Revenus", 
            value=f"{stats['total_revenus']:,.0f} FCFA"
        )
    
    with col2:
        st.metric(
            label="Total des Dépenses", 
            value=f"{stats['total_depenses']:,.0f} FCFA"
        )
    
    with col3:
        st.metric(
            label="Bénéfice Net", 
            value=f"{stats['benefice_net']:,.0f} FCFA",
            delta=f"{stats['benefice_net']:,.0f}" if stats['benefice_net'] != 0 else None,
            delta_color="normal" if stats['benefice_net'] >= 0 else "inverse"
        )
    
    # Graphiques
    st.subheader("Visualisation")
    
    col1, col2 = st.columns(2)
    
    # Graphique des revenus par catégorie
    with col1:
        st.subheader("Répartition des Revenus")
        
        if not stats["revenus_par_categorie"].empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Trier par montant décroissant
            revenus_triees = stats["revenus_par_categorie"].sort_values("montant", ascending=False)
            
            # Créer le graphique en camembert
            ax.pie(
                revenus_triees["montant"], 
                labels=revenus_triees["categorie"], 
                autopct='%1.1f%%', 
                startangle=90
            )
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
            st.pyplot(fig)
        else:
            st.info("Aucun revenu enregistré pour cette période.")
    
    # Graphique des dépenses par catégorie
    with col2:
        st.subheader("Répartition des Dépenses")
        
        if not stats["depenses_par_categorie"].empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Trier par montant décroissant
            depenses_triees = stats["depenses_par_categorie"].sort_values("montant", ascending=False)
            
            # Créer le graphique en camembert
            ax.pie(
                depenses_triees["montant"], 
                labels=depenses_triees["categorie"], 
                autopct='%1.1f%%', 
                startangle=90
            )
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
            st.pyplot(fig)
        else:
            st.info("Aucune dépense enregistrée pour cette période.")
    
    # Évolution des revenus et dépenses
    st.subheader("Évolution des Revenus et Dépenses")
    
    # Récupérer les transactions pour la période
    transactions = lister_transactions(date_debut, date_fin)
    
    if not transactions.empty:
        # Convertir les dates
        transactions["date"] = pd.to_datetime(transactions["date"])
        
        # Regrouper par mois et type
        if periode in ["Cette année", "Tout l'historique"]:
            # Regrouper par mois
            transactions["period"] = transactions["date"].dt.to_period("M")
            period_format = "%m/%Y"
        elif periode in ["Les 3 derniers mois", "Ce mois"]:
            # Regrouper par semaine
            transactions["period"] = transactions["date"].dt.to_period("W")
            period_format = "Semaine %U"
        else:
            # Regrouper par jour
            transactions["period"] = transactions["date"].dt.to_period("D")
            period_format = "%d/%m"
        
        # Regrouper les données
        grouped = transactions.groupby(["period", "type"]).agg({"montant": "sum"}).reset_index()
        
        # Convertir la période en string pour l'affichage
        grouped["period_str"] = grouped["period"].dt.strftime(period_format)
        
        # Créer le pivot pour le graphique
        pivot = grouped.pivot(index="period_str", columns="type", values="montant").reset_index()
        pivot = pivot.fillna(0)
        
        # Trier par période
        pivot = pivot.sort_values("period_str")
        
        # Créer le graphique à barres groupées
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Les barres de revenus et dépenses
        x = range(len(pivot))
        width = 0.35
        
        if "revenu" in pivot.columns:
            ax.bar([i - width/2 for i in x], pivot["revenu"], width, label="Revenus", color="green", alpha=0.7)
        
        if "depense" in pivot.columns:
            ax.bar([i + width/2 for i in x], pivot["depense"], width, label="Dépenses", color="red", alpha=0.7)
        
        # Ajouter les bénéfices comme une ligne
        if "revenu" in pivot.columns and "depense" in pivot.columns:
            benefices = pivot["revenu"] - pivot["depense"]
            ax.plot(x, benefices, marker='o', linestyle='-', color='blue', label="Bénéfice net")
        
        # Configurer les axes
        ax.set_xticks(x)
        ax.set_xticklabels(pivot["period_str"], rotation=45)
        ax.set_ylabel("Montant (FCFA)")
        ax.set_title("Évolution des Revenus et Dépenses")
        ax.legend()
        
        fig.tight_layout()
        st.pyplot(fig)
    else:
        st.info("Aucune transaction enregistrée pour cette période.")

def ajouter_transaction():
    """Formulaire pour ajouter une transaction"""
    st.subheader("Ajouter une Transaction")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            type_transaction = st.radio(
                "Type de transaction",
                options=["revenu", "depense"],
                format_func=lambda x: "Revenu" if x == "revenu" else "Dépense"
            )
        
        with col2:
            date = st.date_input("Date", value=datetime.now())
        
        # Récupérer les catégories selon le type
        categories = lister_categories(type_transaction)
        
        # Permettre l'ajout d'une nouvelle catégorie
        col1, col2 = st.columns([3, 1])
        
        with col1:
            categorie = st.selectbox(
                "Catégorie",
                options=[""] + categories
            )
        
        with col2:
            st.write("&nbsp;")  # Espace pour aligner avec le selectbox
            ajouter_nouvelle_categorie = st.checkbox("Nouvelle catégorie")
        
        # Si l'utilisateur veut ajouter une nouvelle catégorie
        if ajouter_nouvelle_categorie:
            nouvelle_categorie = st.text_input("Nom de la nouvelle catégorie")
            
            if nouvelle_categorie:
                if st.button("Ajouter cette catégorie"):
                    if ajouter_categorie(nouvelle_categorie, type_transaction):
                        st.success(f"✅ Catégorie '{nouvelle_categorie}' ajoutée avec succès!")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de l'ajout de la catégorie.")
            
            categorie = "" if not categories else categories[0]
        
        # Description et montant
        description = st.text_area("Description", placeholder="Détails de la transaction...")
        montant = st.number_input("Montant (FCFA)", min_value=0.0, step=100.0)
        
        # Soumettre le formulaire
        submit = st.form_submit_button("Enregistrer la transaction")
        
        if submit:
            if not categorie:
                st.error("❌ Veuillez sélectionner une catégorie.")
            elif not description:
                st.error("❌ Veuillez entrer une description.")
            elif montant <= 0:
                st.error("❌ Le montant doit être supérieur à zéro.")
            else:
                # Formater la date
                date_str = date.strftime("%Y-%m-%d")
                
                # Enregistrer la transaction
                if enregistrer_transaction(date_str, type_transaction, categorie, description, montant):
                    st.success(f"✅ {type_transaction.capitalize()} de {montant:,.0f} FCFA enregistré(e) avec succès!")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de l'enregistrement de la transaction.")

def supprimer_transaction_budget(transaction_id):
    """Interface pour supprimer une transaction budgétaire"""
    from database import supprimer_transaction
    return supprimer_transaction(transaction_id)

def historique_transactions():
    """Affiche l'historique des transactions avec filtres"""
    st.subheader("Historique des Transactions")
    
    # Initialiser les variables de session pour la suppression
    if 'confirmer_suppression' not in st.session_state:
        st.session_state.confirmer_suppression = False
    if 'transaction_id_a_supprimer' not in st.session_state:
        st.session_state.transaction_id_a_supprimer = None
    
    # Définir les fonctions de callback pour les boutons
    def demander_confirmation(transaction_id):
        st.session_state.transaction_id_a_supprimer = transaction_id
        st.session_state.confirmer_suppression = True
    
    def annuler_suppression():
        st.session_state.confirmer_suppression = False
        st.session_state.transaction_id_a_supprimer = None
    
    def confirmer_suppression():
        from database import supprimer_transaction
        success, message = supprimer_transaction(st.session_state.transaction_id_a_supprimer)
        if success:
            st.session_state.message_success = message
        else:
            st.session_state.message_error = message
        st.session_state.confirmer_suppression = False
        st.session_state.transaction_id_a_supprimer = None
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtre par période
        periode_options = [
            "Aujourd'hui",
            "Cette semaine",
            "Ce mois",
            "Les 3 derniers mois",
            "Cette année",
            "Tout l'historique"
        ]
        periode = st.selectbox("Période", options=periode_options, key="hist_periode")
        
        # Définir la période en fonction de la sélection
        today = datetime.now().date()
        
        if periode == "Aujourd'hui":
            date_debut = today.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Cette semaine":
            start_of_week = today - timedelta(days=today.weekday())
            date_debut = start_of_week.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Ce mois":
            start_of_month = today.replace(day=1)
            date_debut = start_of_month.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Les 3 derniers mois":
            three_months_ago = today - timedelta(days=90)
            date_debut = three_months_ago.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        elif periode == "Cette année":
            start_of_year = today.replace(month=1, day=1)
            date_debut = start_of_year.strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        else:  # Tout l'historique
            date_debut = None
            date_fin = None
    
    with col2:
        # Filtre par type de transaction
        type_filtre = st.selectbox(
            "Type",
            options=["Tous", "revenu", "depense"],
            format_func=lambda x: "Tous" if x == "Tous" else "Revenu" if x == "revenu" else "Dépense"
        )
        
        type_transaction = None if type_filtre == "Tous" else type_filtre
    
    with col3:
        # Filtre par catégorie
        if type_transaction:
            categories = ["Toutes"] + lister_categories(type_transaction)
        else:
            categories_revenus = lister_categories("revenu")
            categories_depenses = lister_categories("depense")
            categories = ["Toutes"] + categories_revenus + categories_depenses
        
        categorie_filtre = st.selectbox("Catégorie", options=categories)
        categorie = None if categorie_filtre == "Toutes" else categorie_filtre
    
    # Récupérer les transactions avec les filtres
    transactions = lister_transactions(date_debut, date_fin, type_transaction, categorie)
    
    # Afficher les messages de succès ou d'erreur s'ils existent
    if 'message_success' in st.session_state and st.session_state.message_success:
        st.success(f"✅ {st.session_state.message_success}")
        st.session_state.message_success = None
    
    if 'message_error' in st.session_state and st.session_state.message_error:
        st.error(f"❌ {st.session_state.message_error}")
        st.session_state.message_error = None
    
    if not transactions.empty:
        # Formater les données pour l'affichage
        transactions_display = transactions.copy()
        transactions_display["date"] = pd.to_datetime(transactions_display["date"]).dt.strftime('%d/%m/%Y')
        transactions_display["type"] = transactions_display["type"].apply(
            lambda x: "➕ Revenu" if x == "revenu" else "➖ Dépense"
        )
        transactions_display["montant"] = transactions_display["montant"].apply(lambda x: f"{x:,.0f} FCFA")
        
        # Afficher le tableau
        st.dataframe(
            transactions_display[["date", "type", "categorie", "description", "montant"]],
            hide_index=True,
            use_container_width=True
        )
        
        # Section pour supprimer une transaction
        st.subheader("Supprimer une transaction")
        
        # Créer la liste des transactions pour le selectbox
        transaction_ids = transactions["id"].tolist()
        transaction_labels = []
        
        for idx, row in transactions.iterrows():
            date = pd.to_datetime(row["date"]).strftime('%d/%m/%Y')
            type_label = "Revenu" if row["type"] == "revenu" else "Dépense"
            montant = f"{row['montant']:,.0f} FCFA"
            description = row['description'] if len(row['description']) <= 50 else row['description'][:47] + "..."
            transaction_labels.append(f"{date} - {type_label} - {row['categorie']} - {montant} - {description}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Sélection de la transaction à supprimer
            transaction_index = st.selectbox(
                "Sélectionner une transaction à supprimer",
                options=range(len(transaction_ids)),
                format_func=lambda x: transaction_labels[x]
            )
        
        with col2:
            st.write("&nbsp;")  # Espace pour aligner avec le selectbox
            if st.button("🗑️ Supprimer", type="primary", use_container_width=True, 
                        key="btn_supprimer", 
                        on_click=demander_confirmation, 
                        args=(transaction_ids[transaction_index],)):
                pass  # Le code s'exécute via le on_click
        
        # Afficher la boîte de dialogue de confirmation si nécessaire
        if st.session_state.confirmer_suppression:
            st.warning("⚠️ Êtes-vous sûr de vouloir supprimer cette transaction?")
            
            col1, col2 = st.columns(2)
            with col1:
                st.button("✅ Confirmer", type="primary", key="btn_confirmer", 
                         on_click=confirmer_suppression)
            with col2:
                st.button("❌ Annuler", type="secondary", key="btn_annuler", 
                         on_click=annuler_suppression)
        
        # Export des données
        st.subheader("Exporter les données")
        col1, col2 = st.columns(2)
        
        with col1:
            # Export CSV
            csv = transactions.to_csv(index=False)
            st.download_button(
                label="📄 Télécharger en CSV",
                data=csv,
                file_name="transactions_budget.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer) as writer:
                transactions.to_excel(writer, index=False, sheet_name="Transactions")
            
            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="📊 Télécharger en Excel",
                data=excel_data,
                file_name="transactions_budget.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Aucune transaction correspondant aux critères de filtrage.")
# Pour tester ce module individuellement
if __name__ == "__main__":
    import sys
    import os
    
    # Ajuster le chemin pour importer le module database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    # Configurer la page
    st.set_page_config(page_title="Gestion de Budget", page_icon="💰", layout="wide")
    
    # Exécuter l'application
    app()