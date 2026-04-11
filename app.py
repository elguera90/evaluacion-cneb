import streamlit as st
import requests
import docx2txt
import fitz  # PyMuPDF

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Evaluación con IA", layout="centered")
st.title("📚 Evaluación automática con IA")

# ==============================
# API KEY (SEGURA)
# ==============================
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("❌ Falta configurar OPENROUTER_API_KEY en Streamlit Secrets")
    st.stop()

# ==============================
# FUNCIÓN IA (CORREGIDA)
