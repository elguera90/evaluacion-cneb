"""
config.py — Configuración global, CSS institucional y validación de credenciales
Sistema de Retroalimentación con IA Generativa · MINEDU Perú
"""

import streamlit as st

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
APP_TITLE      = "Sistema de Retroalimentación con IA Generativa"
APP_SUBTITLE   = "Aula de Innovación Pedagógica"
APP_ORG        = "MINEDU · Perú"
APP_COPYRIGHT  = "© EdTech · Ingeniería Educativa"
APP_VERSION    = "2.0.0"
MAX_FILE_SIZE_MB   = 10
MAX_CONTENT_CHARS  = 4000

GRADOS = [
    "1° Primaria", "2° Primaria", "3° Primaria",
    "4° Primaria", "5° Primaria", "6° Primaria",
    "1° Secundaria", "2° Secundaria", "3° Secundaria",
    "4° Secundaria", "5° Secundaria",
]

IDIOMAS = {"Español": "es", "Quechua": "qu", "Aymara": "ay"}
NIVELES_LOGRO = ["AD", "A", "B", "C"]


# ──────────────────────────────────────────────
# SETUP DE PÁGINA
# ──────────────────────────────────────────────
def setup_page():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://www.minedu.gob.pe",
            "About": f"{APP_TITLE} v{APP_VERSION}",
        },
    )
    _validate_secrets()


def _validate_secrets():
    required = ["OPENROUTER_API_KEY", "GOOGLE_CREDENTIALS", "ADMIN_PASSWORD"]
    missing = [k for k in required if not st.secrets.get(k)]
    if missing:
        st.error(f"❌ Faltan credenciales en st.secrets: `{'`, `'.join(missing)}`")
        st.stop()


def get_api_key() -> str:
    return st.secrets["OPENROUTER_API_KEY"]


def get_google_creds() -> str:
    return st.secrets["GOOGLE_CREDENTIALS"]


def get_admin_password() -> str:
    return st.secrets["ADMIN_PASSWORD"]


def get_app_url() -> str:
    return st.secrets.get("APP_URL", "https://tu-app.streamlit.app")


# ──────────────────────────────────────────────
# CSS INSTITUCIONAL
# ──────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Sora:wght@300;400;600;700&display=swap');

:root {
    --rojo:      #C8102E;
    --rojo-2:    #9e0c24;
    --blanco:    #FFFFFF;
    --gris-bg:   #F4F6F9;
    --gris-1:    #E8ECF0;
    --gris-2:    #9AA5B1;
    --gris-3:    #4A5568;
    --negro:     #1A202C;
    --verde:     #2ECC71;
    --azul:      #2980B9;
    --amarillo:  #F39C12;
    --sombra-sm: 0 1px 3px rgba(0,0,0,.08);
    --sombra-md: 0 4px 12px rgba(0,0,0,.10);
    --sombra-lg: 0 10px 40px rgba(0,0,0,.14);
    --radio:     12px;
    --radio-lg:  18px;
    --font:      'Plus Jakarta Sans', sans-serif;
    --font-d:    'Sora', sans-serif;
    --trans:     all 0.22s cubic-bezier(.4,0,.2,1);
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: var(--font) !important;
    color: var(--negro) !important;
}
.stApp { background: var(--gris-bg) !important; }

/* ── Ocultar toolbar Streamlit ── */
[data-testid="stToolbar"], #MainMenu, footer { display:none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--rojo) 0%, var(--rojo-2) 100%) !important;
    box-shadow: var(--sombra-lg);
}
[data-testid="stSidebar"] * { color: var(--blanco) !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 8px !important;
    color: white !important;
}

/* ── Encabezados ── */
h1 {
    font-family: var(--font-d) !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: var(--negro) !important;
}
h2, h3 {
    font-family: var(--font-d) !important;
    font-weight: 600 !important;
    color: var(--gris-3) !important;
}

/* ── Cards ── */
.card {
    background: var(--blanco);
    border-radius: var(--radio-lg);
    padding: 1.6rem 1.8rem;
    box-shadow: var(--sombra-sm);
    border: 1px solid var(--gris-1);
    margin-bottom: 1rem;
    transition: var(--trans);
}
.card:hover { box-shadow: var(--sombra-md); }

/* ── Métrica ── */
.metric-card {
    background: var(--blanco);
    border-radius: var(--radio);
    padding: 1.2rem 1.4rem;
    border-left: 4px solid var(--rojo);
    box-shadow: var(--sombra-sm);
}

/* ── Botones ── */
.stButton > button {
    background: linear-gradient(135deg, var(--rojo), var(--rojo-2)) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.4rem !important;
    font-weight: 600 !important;
    font-family: var(--font) !important;
    transition: var(--trans) !important;
    box-shadow: 0 2px 8px rgba(200,16,46,0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(200,16,46,0.45) !important;
}
[data-testid="stDownloadButton"] > button {
    background: var(--azul) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ── INPUTS: texto siempre visible ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--blanco) !important;
    color: var(--negro) !important;
    border: 1.5px solid var(--gris-1) !important;
    border-radius: 8px !important;
    font-family: var(--font) !important;
    font-size: 0.95rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--rojo) !important;
    box-shadow: 0 0 0 3px rgba(200,16,46,0.12) !important;
    outline: none !important;
}
/* Input tipo password */
input[type="password"] {
    color: var(--negro) !important;
    background: var(--blanco) !important;
}

/* ── LABELS: siempre visibles ── */
label,
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stSlider label,
.stFileUploader label,
.stRadio label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] {
    color: var(--negro) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

/* ── Selectbox ── */
[data-baseweb="select"] span,
[data-baseweb="select"] div:not([data-testid="stSidebar"] *) {
    color: var(--negro) !important;
}
[data-baseweb="select"] > div {
    background: var(--blanco) !important;
    border: 1.5px solid var(--gris-1) !important;
    border-radius: 8px !important;
}

/* ── Radio buttons ── */
[data-baseweb="radio"] label { color: var(--negro) !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--blanco) !important;
    border: 2px dashed var(--gris-1) !important;
    border-radius: var(--radio) !important;
}

/* ── Alertas ── */
[data-testid="stAlert"] {
    border-radius: var(--radio) !important;
    font-weight: 500 !important;
}
/* Error: texto visible sobre fondo rojo claro */
[data-testid="stAlert"][data-type="error"] {
    background: rgba(200,16,46,0.08) !important;
    border: 1.5px solid rgba(200,16,46,0.4) !important;
    color: #7b0a1c !important;
}
[data-testid="stAlert"][data-type="error"] * { color: #7b0a1c !important; }

/* Info: texto visible */
[data-testid="stAlert"][data-type="info"] {
    background: rgba(41,128,185,0.08) !important;
    border: 1.5px solid rgba(41,128,185,0.35) !important;
    color: #1a5276 !important;
}
[data-testid="stAlert"][data-type="info"] * { color: #1a5276 !important; }

/* Warning */
[data-testid="stAlert"][data-type="warning"] * { color: #7d4e00 !important; }

/* Success */
[data-testid="stAlert"][data-type="success"] * { color: #1a6b3a !important; }

/* ── Status box (spinner expandido) ── */
[data-testid="stStatusWidget"] { border-radius: var(--radio) !important; }
[data-testid="stStatusWidget"] p,
[data-testid="stStatusWidget"] span,
[data-testid="stStatusWidget"] div { color: var(--negro) !important; }

/* ── Badges de nivel ── */
.badge-AD { background:#1a9e6c; color:white; border-radius:20px; padding:4px 14px; font-weight:700; font-size:0.85rem; display:inline-block; }
.badge-A  { background:#2980B9; color:white; border-radius:20px; padding:4px 14px; font-weight:700; font-size:0.85rem; display:inline-block; }
.badge-B  { background:#F39C12; color:white; border-radius:20px; padding:4px 14px; font-weight:700; font-size:0.85rem; display:inline-block; }
.badge-C  { background:#C8102E; color:white; border-radius:20px; padding:4px 14px; font-weight:700; font-size:0.85rem; display:inline-block; }

/* ── Header institucional ── */
.header-institucional {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: white;
    border-radius: var(--radio-lg);
    box-shadow: var(--sombra-sm);
    border-left: 5px solid var(--rojo);
    margin-bottom: 1.5rem;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] { border-bottom: 2px solid var(--gris-1) !important; }
[data-baseweb="tab"] { font-family: var(--font) !important; font-weight: 600 !important; color: var(--gris-2) !important; }
[aria-selected="true"] { color: var(--rojo) !important; border-bottom: 3px solid var(--rojo) !important; }

/* ── Progress bar ── */
.stProgress > div > div { background: var(--rojo) !important; border-radius:999px !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--rojo) !important; }

/* ── Divisores ── */
hr { border-color: var(--gris-1) !important; margin: 1.5rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--gris-1); }
::-webkit-scrollbar-thumb { background: var(--rojo); border-radius:999px; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] * { color: var(--negro) !important; }

/* ── Markdown general ── */
.stMarkdown p, .stMarkdown li { color: var(--negro) !important; }
</style>
"""


def load_css():
    st.markdown(CSS, unsafe_allow_html=True)
