import streamlit as st
from streamlit_option_menu import option_menu as som
from modules import dashboard, stock, movements, orders, sales_history, analytics, budget

# Configuration globale
st.set_page_config(page_title="Royal Cosmetik", layout="wide")

# === CSS pour personnaliser la sidebar ===
st.markdown("""
    <style>
        /* Titre dans la sidebar */
        .sidebar-title {
            font-size: 24px;
            color: black;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }

        /* Style du radio bouton (amélioration générale) */
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 0.5rem 1rem;
            border-radius: 10px;
            background-color: rgba(255,255,255,0.1);
            margin-bottom: 5px;
            transition: background-color 0.3s ease;
        }

        /* Hover sur les boutons du menu */
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background-color: rgba(255,255,255,0.2);
        }

        /* Bouton sélectionné */
        section[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# === Titre stylisé dans la sidebar ===
#st.sidebar.markdown('<div class="sidebar-title">📁 Menu</div>', unsafe_allow_html=True)

# === Menu latéral ===
PAGES = {
    "Dash": dashboard,
    "Stock": stock,
    "Move": movements,
    "Orders": orders,
    "Sales": sales_history,
    "Stats": analytics,
    "Budget": budget
}




selected=som(  
    menu_title=None,  # Pas de titre de menu
    options=list(PAGES.keys()),  # Les titres des pages
    icons=["house", "box", "arrow-left-right", "cart", "file-earmark-text", "bar-chart-line", "cash"],  # Icônes pour chaque page
    default_index=0,  # Page par défaut (index)
    menu_icon="cast",  # Icône du menu
    orientation="horizontal",  # Orientation verticale
)

if selected in PAGES:
    page = PAGES[selected]
    page.app()  # Appeler la fonction app() de la page sélectionnée
