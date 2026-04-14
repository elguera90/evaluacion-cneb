"""
config.py — Configuración global, CSS y validación de credenciales
"""

import streamlit as st


# ──────────────────────────────────────────────
# CONSTANTES DE APLICACIÓN
# ──────────────────────────────────────────────
APP_TITLE = "IA CNEB · MINEDU Perú"
APP_VERSION = "2.0.0"
MAX_FILE_SIZE_MB = 10
MAX_CONTENT_CHARS = 4000  # Límite de tokens seguros para el LLM

GRADOS = [
    "1° Primaria", "2° Primaria", "3° Primaria",
    "4° Primaria", "5° Primaria", "6° Primaria",
    "1° Secundaria", "2° Secundaria", "3° Secundaria",
    "4° Secundaria", "5° Secundaria",
]

IDIOMAS = {
    "Español": "es",
    "Quechua": "qu",
    "Aymara": "ay",
}

NIVELES_LOGRO = ["AD", "A", "B", "C"]

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ──────────────────────────────────────────────
def setup_page():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://www.minedu.gob.pe",
            "About": f"Sistema IA CNEB v{APP_VERSION} — MINEDU Perú",
        },
    )
    _validate_secrets()


def _validate_secrets():
    required = ["OPENROUTER_API_KEY", "GOOGLE_CREDENTIALS", "ADMIN_PASSWORD"]
    missing = [k for k in required if not st.secrets.get(k)]
    if missing:
        st.error(f"❌ Faltan credenciales en st.secrets: `{'`, `'.join(missing)}`")
        st.info("Configura estos valores en Settings → Secrets de Streamlit Cloud.")
        st.stop()


# ──────────────────────────────────────────────
# ACCESO A SECRETS (con fallback seguro)
# ──────────────────────────────────────────────
def get_api_key() -> str:
    return st.secrets["OPENROUTER_API_KEY"]


def get_google_creds() -> str:
    return st.secrets["GOOGLE_CREDENTIALS"]


def get_admin_password() -> str:
    return st.secrets["ADMIN_PASSWORD"]


def get_app_url() -> str:
    """Detecta la URL base de la app dinámicamente."""
    return st.secrets.get("APP_URL", "https://tu-app.streamlit.app")


# ──────────────────────────────────────────────
# CSS — DISEÑO INSTITUCIONAL MINEDU
# ──────────────────────────────────────────────
CSS = """
<style>
/* ── Importar fuente institucional ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Sora:wght@300;400;600;700&display=swap');

/* ── Tokens de diseño ── */
:root {
    --minedu-rojo:     #C8102E;
    --minedu-rojo-2:   #9e0c24;
    --minedu-blanco:   #FFFFFF;
    --minedu-gris-bg:  #F4F6F9;
    --minedu-gris-1:   #E8ECF0;
    --minedu-gris-2:   #9AA5B1;
    --minedu-gris-3:   #4A5568;
    --minedu-negro:    #1A202C;
    --minedu-verde:    #2ECC71;
    --minedu-azul:     #2980B9;
    --minedu-amarillo: #F39C12;
    --sombra-sm:       0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
    --sombra-md:       0 4px 12px rgba(0,0,0,.10);
    --sombra-lg:       0 10px 40px rgba(0,0,0,.14);
    --radio:           12px;
    --radio-lg:        18px;
    --font-body:       'Plus Jakarta Sans', sans-serif;
    --font-display:    'Sora', sans-serif;
    --trans:           all 0.22s cubic-bezier(.4,0,.2,1);
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: var(--font-body);
    color: var(--minedu-negro);
}

.stApp {
    background: var(--minedu-gris-bg);
}

/* ── Barra lateral ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--minedu-rojo) 0%, var(--minedu-rojo-2) 100%);
    border-right: none;
    box-shadow: var(--sombra-lg);
}

[data-testid="stSidebar"] * {
    color: var(--minedu-blanco) !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label {
    color: rgba(255,255,255,0.85) !important;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 8px !important;
    color: white !important;
}

/* ── Encabezados ── */
h1 {
    font-family: var(--font-display) !important;
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    color: var(--minedu-negro) !important;
    letter-spacing: -0.02em;
    line-height: 1.2;
}

h2, h3 {
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    color: var(--minedu-gris-3) !important;
}

/* ── Cards contenedoras ── */
.card {
    background: var(--minedu-blanco);
    border-radius: var(--radio-lg);
    padding: 1.6rem 1.8rem;
    box-shadow: var(--sombra-sm);
    border: 1px solid var(--minedu-gris-1);
    margin-bottom: 1rem;
    transition: var(--trans);
}

.card:hover { box-shadow: var(--sombra-md); }

/* ── Bandas de color en métricas ── */
.metric-card {
    background: var(--minedu-blanco);
    border-radius: var(--radio);
    padding: 1.2rem 1.4rem;
    border-left: 4px solid var(--minedu-rojo);
    box-shadow: var(--sombra-sm);
    transition: var(--trans);
}

/* ── Botones primarios ── */
.stButton > button[kind="primary"],
.stButton > button:first-child {
    background: linear-gradient(135deg, var(--minedu-rojo), var(--minedu-rojo-2)) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.4rem !important;
    font-weight: 600 !important;
    font-family: var(--font-body) !important;
    letter-spacing: 0.01em !important;
    transition: var(--trans) !important;
    box-shadow: 0 2px 8px rgba(200,16,46,0.35) !important;
}

.stButton > button:first-child:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(200,16,46,0.45) !important;
}

/* ── Botón de descarga ── */
[data-testid="stDownloadButton"] > button {
    background: var(--minedu-azul) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: var(--trans) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--minedu-gris-bg) !important;
    border: 1.5px solid var(--minedu-gris-1) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-size: 0.95rem !important;
    transition: var(--trans) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--minedu-rojo) !important;
    box-shadow: 0 0 0 3px rgba(200,16,46,0.1) !important;
}

/* ── Fix: color de texto en inputs (evita texto blanco invisible) ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    color: #1A202C !important;
}

/* ── Fix: labels visibles en todo el formulario ── */
label,
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stSlider label,
.stFileUploader label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] {
    color: #1A202C !important;
    font-weight: 500 !important;
}

/* ── Fix: ocultar toolbar de Streamlit ── */
[data-testid="stToolbar"],
#MainMenu,
footer { display: none !important; }

/* ── Fix: selectbox texto visible ── */
[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #1A202C !important;
}

/* ── Alertas personalizadas ── */
.alert-success {
    background: rgba(46,204,113,0.1);
    border: 1px solid rgba(46,204,113,0.4);
    border-radius: var(--radio);
    padding: 0.9rem 1.2rem;
    color: #1e8449;
    font-weight: 500;
}

.alert-info {
    background: rgba(41,128,185,0.08);
    border: 1px solid rgba(41,128,185,0.3);
    border-radius: var(--radio);
    padding: 0.9rem 1.2rem;
    color: #1a5276;
}

/* ── Badge de nivel de logro ── */
.badge-AD { background:#1a9e6c; color:white; border-radius:20px; padding:3px 12px; font-weight:700; font-size:0.82rem; }
.badge-A  { background:#2980B9; color:white; border-radius:20px; padding:3px 12px; font-weight:700; font-size:0.82rem; }
.badge-B  { background:#F39C12; color:white; border-radius:20px; padding:3px 12px; font-weight:700; font-size:0.82rem; }
.badge-C  { background:#C8102E; color:white; border-radius:20px; padding:3px 12px; font-weight:700; font-size:0.82rem; }

/* ── Encabezado institucional ── */
.header-institucional {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: white;
    border-radius: var(--radio-lg);
    box-shadow: var(--sombra-sm);
    border-left: 5px solid var(--minedu-rojo);
    margin-bottom: 1.5rem;
}

/* ── Spinner override ── */
.stSpinner > div { border-top-color: var(--minedu-rojo) !important; }

/* ── Divisores ── */
hr { border-color: var(--minedu-gris-1) !important; margin: 1.5rem 0 !important; }

/* ── Tabs ── */
[data-baseweb="tab-list"] { border-bottom: 2px solid var(--minedu-gris-1) !important; gap: 0 !important; }
[data-baseweb="tab"] { font-family: var(--font-body) !important; font-weight: 600 !important; color: var(--minedu-gris-2) !important; }
[aria-selected="true"] { color: var(--minedu-rojo) !important; border-bottom: 3px solid var(--minedu-rojo) !important; }

/* ── Progress bar ── */
.stProgress > div > div { background: var(--minedu-rojo) !important; border-radius: 999px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--minedu-gris-1); }
::-webkit-scrollbar-thumb { background: var(--minedu-rojo); border-radius: 999px; }
</style>
"""


def load_css():
    st.markdown(CSS, unsafe_allow_html=True)
