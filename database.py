import sqlite3
import os
import pandas as pd
import streamlit as st

# Chemin vers le dossier data
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'royal_cosmetik.db')

# Création du dossier data s'il n'existe pas
os.makedirs(DATA_DIR, exist_ok=True)

def get_db_connection():
    """Établit une connexion à la base de données SQLite avec les clés étrangères activées"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # Active les contraintes FK
    conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par leur nom
    return conn

def init_db():
    """Initialise la base de données avec les tables requises"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Création de la table produit
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS produit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            categorie TEXT NOT NULL,
            prix_unitaire REAL NOT NULL,
            stock INTEGER NOT NULL,
            stock_min INTEGER NOT NULL
        )
        ''')
        
        # Création de la table mouvement
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouvement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER NOT NULL,
            type TEXT NOT NULL,  -- 'entree' ou 'sortie'
            quantite INTEGER NOT NULL,
            date TEXT NOT NULL,
            commentaire TEXT,
            FOREIGN KEY (produit_id) REFERENCES produit (id) ON DELETE CASCADE
        )
        ''')
        
        # Création de la table commande
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS commande (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            date TEXT NOT NULL,
            total REAL NOT NULL
        )
        ''')
        
        # Création de la table commande_details
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS commande_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commande_id INTEGER NOT NULL,
            produit_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            FOREIGN KEY (commande_id) REFERENCES commande (id) ON DELETE CASCADE,
            FOREIGN KEY (produit_id) REFERENCES produit (id) ON DELETE RESTRICT
        )
        ''')
        
        # Création de la table budget
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,  -- 'revenu' ou 'depense'
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
        ''')
        
        # Création de la table utilisateur (optionnelle)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            mot_de_passe TEXT NOT NULL,
            role TEXT NOT NULL  -- 'admin' ou 'utilisateur'
        )
        ''')
        
        # Création de la table paramètres (optionnelle)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS parametres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cle TEXT NOT NULL UNIQUE,
            valeur TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Fonctions pour les opérations CRUD sur les produits
def ajouter_produit(nom, categorie, prix_unitaire, stock, stock_min):
    conn = None
    try:
        # Validation des données
        if not nom or not categorie:
            return False, "Le nom et la catégorie sont obligatoires"
        if not isinstance(prix_unitaire, (int, float)) or prix_unitaire < 0:
            return False, "Le prix unitaire doit être un nombre positif"
        if not isinstance(stock, int) or stock < 0:
            return False, "Le stock doit être un nombre entier positif"
        if not isinstance(stock_min, int) or stock_min < 0:
            return False, "Le stock minimum doit être un nombre entier positif"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO produit (nom, categorie, prix_unitaire, stock, stock_min) VALUES (?, ?, ?, ?, ?)",
            (nom, categorie, prix_unitaire, stock, stock_min)
        )
        conn.commit()
        return True, "Produit ajouté avec succès"
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de l'ajout du produit: {e}"
    finally:
        if conn:
            conn.close()

def modifier_produit(id, nom, categorie, prix_unitaire, stock, stock_min):
    conn = None
    try:
        # Validation des données
        if not id or not isinstance(id, int):
            return False, "ID de produit invalide"
        if not nom or not categorie:
            return False, "Le nom et la catégorie sont obligatoires"
        if not isinstance(prix_unitaire, (int, float)) or prix_unitaire < 0:
            return False, "Le prix unitaire doit être un nombre positif"
        if not isinstance(stock, int) or stock < 0:
            return False, "Le stock doit être un nombre entier positif"
        if not isinstance(stock_min, int) or stock_min < 0:
            return False, "Le stock minimum doit être un nombre entier positif"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE produit 
               SET nom = ?, categorie = ?, prix_unitaire = ?, stock = ?, stock_min = ?
               WHERE id = ?""",
            (nom, categorie, prix_unitaire, stock, stock_min, id)
        )
        if cursor.rowcount == 0:
            return False, "Produit non trouvé"
        conn.commit()
        return True, "Produit modifié avec succès"
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de la modification du produit: {e}"
    finally:
        if conn:
            conn.close()

def supprimer_produit(id):
    conn = None
    try:
        conn = get_db_connection()
        # Vérifier si le produit existe dans une commande
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM commande_details WHERE produit_id = ?", (id,))
        count = cursor.fetchone()[0]
        if count > 0:
            return False, "Ce produit est référencé dans des commandes et ne peut pas être supprimé"
        
        cursor.execute("DELETE FROM produit WHERE id = ?", (id,))
        if cursor.rowcount == 0:
            return False, "Produit non trouvé"
        conn.commit()
        return True, "Produit supprimé avec succès"
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de la suppression du produit: {e}"
    finally:
        if conn:
            conn.close()

def lister_produits():
    conn = None
    try:
        conn = get_db_connection()
        produits = pd.read_sql_query("SELECT * FROM produit", conn)
        return produits
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des produits: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def produits_stock_bas():
    conn = None
    try:
        conn = get_db_connection()
        produits = pd.read_sql_query(
            "SELECT * FROM produit WHERE stock <= stock_min", 
            conn
        )
        return produits
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des produits en stock bas: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# Fonctions pour les mouvements de stock
def enregistrer_mouvement(produit_id, type_mouvement, quantite, date, commentaire="", conn=None):
    close_conn = False
    try:
        # Validation des données
        if not produit_id or not isinstance(produit_id, int):
            return False, "ID de produit invalide"
        if type_mouvement not in ['entree', 'sortie']:
            return False, "Type de mouvement invalide (doit être 'entree' ou 'sortie')"
        if not isinstance(quantite, int) or quantite <= 0:
            return False, "La quantité doit être un nombre entier positif"
        if not date:
            return False, "La date est obligatoire"
        
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        cursor = conn.cursor()
        
        # Vérifier si le produit existe
        cursor.execute("SELECT stock FROM produit WHERE id = ?", (produit_id,))
        result = cursor.fetchone()
        if not result:
            if close_conn:
                conn.close()
            return False, "Produit non trouvé"
        
        stock_actuel = result[0]
        
        # Vérifier si le stock est suffisant pour une sortie
        if type_mouvement == 'sortie' and quantite > stock_actuel:
            if close_conn:
                conn.close()
            return False, "Stock insuffisant pour cette sortie"

        # Enregistrer le mouvement
        cursor.execute(
            "INSERT INTO mouvement (produit_id, type, quantite, date, commentaire) VALUES (?, ?, ?, ?, ?)",
            (produit_id, type_mouvement, quantite, date, commentaire)
        )

        # Mettre à jour le stock
        if type_mouvement == 'entree':
            cursor.execute("UPDATE produit SET stock = stock + ? WHERE id = ?", (quantite, produit_id))
        elif type_mouvement == 'sortie':
            cursor.execute("UPDATE produit SET stock = stock - ? WHERE id = ?", (quantite, produit_id))

        if close_conn:
            conn.commit()
            conn.close()
        return True, "Mouvement enregistré avec succès"
    except sqlite3.Error as e:
        if conn and close_conn:
            conn.rollback()
            conn.close()
        return False, f"Erreur lors de l'enregistrement du mouvement: {e}"

def lister_mouvements():
    conn = None
    try:
        conn = get_db_connection()
        mouvements = pd.read_sql_query(
            """SELECT m.id, p.nom, m.type, m.quantite, m.date, m.commentaire 
               FROM mouvement m
               JOIN produit p ON m.produit_id = p.id
               ORDER BY m.date DESC""", 
            conn
        )
        return mouvements
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des mouvements: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# Fonctions pour les commandes
def creer_commande(client, date, total, produits_commandes):
    conn = None
    try:
        # Validation des données
        if not client:
            return False, "Le nom du client est obligatoire"
        if not date:
            return False, "La date est obligatoire"
        if not isinstance(total, (int, float)) or total < 0:
            return False, "Le total doit être un nombre positif"
        if not produits_commandes or not isinstance(produits_commandes, list) or len(produits_commandes) == 0:
            return False, "La liste des produits commandés est vide ou invalide"
        
        conn = get_db_connection()
        conn.execute("BEGIN TRANSACTION")  # Début explicite de la transaction
        cursor = conn.cursor()

        # Créer la commande
        cursor.execute(
            "INSERT INTO commande (client, date, total) VALUES (?, ?, ?)",
            (client, date, total)
        )
        commande_id = cursor.lastrowid

        # Vérifier les stocks avant de les modifier
        for produit in produits_commandes:
            if not isinstance(produit, dict) or 'id' not in produit or 'quantite' not in produit or 'prix_unitaire' not in produit:
                conn.rollback()
                return False, "Format de produit commandé invalide"
            
            cursor.execute("SELECT stock FROM produit WHERE id = ?", (produit['id'],))
            result = cursor.fetchone()
            if not result:
                conn.rollback()
                return False, f"Produit ID {produit['id']} non trouvé"
            
            stock_actuel = result[0]
            if stock_actuel < produit['quantite']:
                conn.rollback()
                return False, f"Stock insuffisant pour le produit ID {produit['id']}"

        # Ajouter les détails de la commande et mettre à jour les stocks
        for produit in produits_commandes:
            cursor.execute(
                """INSERT INTO commande_details 
                   (commande_id, produit_id, quantite, prix_unitaire) 
                   VALUES (?, ?, ?, ?)""",
                (commande_id, produit['id'], produit['quantite'], produit['prix_unitaire'])
            )

            # Mise à jour du stock
            cursor.execute(
                "UPDATE produit SET stock = stock - ? WHERE id = ?",
                (produit['quantite'], produit['id'])
            )
            
            # Enregistrement du mouvement
            cursor.execute(
                """INSERT INTO mouvement 
                   (produit_id, type, quantite, date, commentaire)
                   VALUES (?, 'sortie', ?, ?, ?)""",
                (produit['id'], produit['quantite'], date, f"Commande #{commande_id}")
            )

        conn.commit()
        return True, commande_id
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de la création de la commande: {e}"
    finally:
        if conn:
            conn.close()

def lister_commandes():
    conn = None
    try:
        conn = get_db_connection()
        commandes = pd.read_sql_query(
            "SELECT * FROM commande ORDER BY date DESC", 
            conn
        )
        return commandes
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des commandes: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def details_commande(commande_id):
    conn = None
    try:
        if not commande_id or not isinstance(commande_id, int):
            return pd.DataFrame()
            
        conn = get_db_connection()
        details = pd.read_sql_query(
            """SELECT cd.produit_id, p.nom, cd.quantite, cd.prix_unitaire, 
               (cd.quantite * cd.prix_unitaire) as sous_total
               FROM commande_details cd
               JOIN produit p ON cd.produit_id = p.id
               WHERE cd.commande_id = ?""", 
            conn,
            params=(commande_id,)
        )
        return details
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des détails de commande: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# Fonctions pour le budget
def ajouter_transaction(type_transaction, montant, categorie, date, description=""):
    conn = None
    try:
        # Validation des données
        if type_transaction not in ['revenu', 'depense']:
            return False, "Type de transaction invalide (doit être 'revenu' ou 'depense')"
        if not isinstance(montant, (int, float)) or montant <= 0:
            return False, "Le montant doit être un nombre positif"
        if not categorie:
            return False, "La catégorie est obligatoire"
        if not date:
            return False, "La date est obligatoire"
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO budget (type, montant, categorie, date, description) VALUES (?, ?, ?, ?, ?)",
            (type_transaction, montant, categorie, date, description)
        )
        conn.commit()
        return True, "Transaction ajoutée avec succès"
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de l'ajout de la transaction: {e}"
    finally:
        if conn:
            conn.close()

def lister_transactions():
    conn = None
    try:
        conn = get_db_connection()
        transactions = pd.read_sql_query(
            "SELECT * FROM budget ORDER BY date DESC", 
            conn
        )
        return transactions
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des transactions: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# Pour supprimer une commande
def supprimer_commande(commande_id):
    conn = None
    try:
        conn = get_db_connection()
        conn.execute("BEGIN TRANSACTION")
        cursor = conn.cursor()
        
        # Récupérer les détails de la commande pour mettre à jour les stocks
        cursor.execute(
            """SELECT produit_id, quantite 
               FROM commande_details 
               WHERE commande_id = ?""", 
            (commande_id,)
        )
        details = cursor.fetchall()
        
        # Supprimer la commande et ses détails
        cursor.execute("DELETE FROM commande_details WHERE commande_id = ?", (commande_id,))
        cursor.execute("DELETE FROM commande WHERE id = ?", (commande_id,))
        
        # Remettre en stock les produits
        for detail in details:
            produit_id = detail[0]
            quantite = detail[1]
            cursor.execute(
                "UPDATE produit SET stock = stock + ? WHERE id = ?", 
                (quantite, produit_id)
            )
            
        conn.commit()
        return True, "Commande supprimée avec succès"
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de la suppression de la commande: {e}"
    finally:
        if conn:
            conn.close()

# Pour supprimer une transaction budgétaire
def supprimer_transaction(transaction_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        if cursor.rowcount == 0:
            return False, "Transaction non trouvée"
        conn.commit()
        return True, "Transaction supprimée avec succès"
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de la suppression de la transaction: {e}"
    finally:
        if conn:
            conn.close()

# Pour supprimer un mouvement de stock
def supprimer_mouvement(mouvement_id):
    conn = None
    try:
        conn = get_db_connection()
        conn.execute("BEGIN TRANSACTION")
        cursor = conn.cursor()
        
        # Récupérer les infos du mouvement
        cursor.execute(
            "SELECT produit_id, type, quantite FROM mouvement WHERE id = ?", 
            (mouvement_id,)
        )
        mouvement = cursor.fetchone()
        if not mouvement:
            return False, "Mouvement non trouvé"
            
        produit_id = mouvement[0]
        type_mouvement = mouvement[1]
        quantite = mouvement[2]
        
        # Corriger le stock (inverser l'effet du mouvement)
        if type_mouvement == 'entree':
            cursor.execute(
                "UPDATE produit SET stock = stock - ? WHERE id = ?", 
                (quantite, produit_id)
            )
        else:  # sortie
            cursor.execute(
                "UPDATE produit SET stock = stock + ? WHERE id = ?", 
                (quantite, produit_id)
            )
            
        # Supprimer le mouvement
        cursor.execute("DELETE FROM mouvement WHERE id = ?", (mouvement_id,))
        
        conn.commit()
        return True, "Mouvement supprimé avec succès"
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return False, f"Erreur lors de la suppression du mouvement: {e}"
    finally:
        if conn:
            conn.close()

def calculer_benefice():
    conn = None
    try:
        conn = get_db_connection()
        revenus = pd.read_sql_query(
            "SELECT SUM(montant) as total FROM budget WHERE type = 'revenu'", 
            conn
        )
        depenses = pd.read_sql_query(
            "SELECT SUM(montant) as total FROM budget WHERE type = 'depense'", 
            conn
        )
        
        total_revenus = revenus['total'].iloc[0] if not pd.isna(revenus['total'].iloc[0]) else 0
        total_depenses = depenses['total'].iloc[0] if not pd.isna(depenses['total'].iloc[0]) else 0
        
        return total_revenus - total_depenses
    except sqlite3.Error as e:
        print(f"Erreur lors du calcul du bénéfice: {e}")
        return 0
    finally:
        if conn:
            conn.close()

# Initialiser la base de données au démarrage du script
if __name__ == "__main__":
    if init_db():
        print(f"Base de données initialisée à {DB_PATH}")
    else:
        print("Échec de l'initialisation de la base de données")