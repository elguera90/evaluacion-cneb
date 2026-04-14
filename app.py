"""
╔══════════════════════════════════════════════════════════════════╗
║  SISTEMA IA CNEB - MINEDU PERÚ                                  ║
║  Evaluador Pedagógico con Retroalimentación por Voz             ║
║  Versión: 2.0.0 | Escala: Piloto (hasta 500 estudiantes)        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
from config import setup_page, load_css
from auth import render_login, is_authenticated
from router import render_docente, render_estudiante

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA (debe ser lo primero)
# ──────────────────────────────────────────────
setup_page()
load_css()

# ──────────────────────────────────────────────
# ENRUTAMIENTO PRINCIPAL
# ──────────────────────────────────────────────
id_examen_url = st.query_params.get("id")

if id_examen_url:
    # Modo estudiante — sin autenticación requerida
    render_estudiante(id_examen_url)
else:
    # Modo docente — requiere autenticación
    if not is_authenticated():
        render_login()
    else:
        render_docente()
