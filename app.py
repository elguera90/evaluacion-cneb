import streamlit as st
import requests
import docx2txt
import fitz  # PyMuPDF
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Evaluación CNEB con IA", layout="centered")
st.title("📚 Sistemas PIP con IAG")

# ==============================
# API KEY
# ==============================
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("❌ Falta configurar OPENROUTER_API_KEY")
    st.stop()

# ==============================
# FUNCIÓN IA
# ==============================
def ia(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openrouter/auto",
        "messages": [
            {"role": "system", "content": "Eres un docente experto del CNEB Perú."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)

        if r.status_code != 200:
            return f"❌ Error API: {r.text}"

        res = r.json()

        if "choices" in res:
            return res["choices"][0]["message"]["content"]
        else:
            return f"⚠ Respuesta inesperada: {res}"

    except Exception as e:
        return f"❌ Error: {e}"

# ==============================
# LEER ARCHIVOS
# ==============================
def leer(file):
    try:
        if file.name.endswith(".pdf"):
            pdf = fitz.open(stream=file.read(), filetype="pdf")
            texto = ""
            for page in pdf:
                texto += page.get_text()
            return texto

        elif file.name.endswith(".docx"):
            return docx2txt.process(file)

        else:
            return None

    except Exception as e:
        st.error(f"Error leyendo archivo: {e}")
        return None

# ==============================
# GUARDAR EN SHEETS
# ==============================
def guardar_en_sheets(nombre, grado, seccion, respuestas, resultado):
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

        scope = ["https://spreadsheets.google.com/feeds"]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        sheet = client.open("Evaluaciones_CNEB").sheet1

        # detectar nivel
        if "AD" in resultado:
            nivel = "AD"
        elif "A" in resultado:
            nivel = "A"
        elif "B" in resultado:
            nivel = "B"
        else:
            nivel = "C"

        sheet.append_row([
            str(datetime.now()),
            nombre,
            grado,
            seccion,
            respuestas,
            resultado,
            nivel
        ])

    except Exception as e:
        st.error(f"Error guardando en Sheets: {e}")

# ==============================
# UI
# ==============================
archivo = st.file_uploader("📂 Sube sesión (PDF o DOCX)", type=["pdf","docx"])

if archivo:
    texto = leer(archivo)

    if texto:
        st.success("✅ Archivo cargado")

        if st.button("🚀 Generar evaluación"):
            with st.spinner("Generando evaluación..."):
                preguntas = ia(f"""
Actúa como docente experto del Currículo Nacional del Perú (CNEB).

Analiza este contenido:

{texto[:2000]}

Genera:

1. Área
2. Competencia
3. Capacidades

Luego:

4. 3 preguntas abiertas
5. Respuestas modelo
6. Criterios de evaluación

CONDICIONES:
- En español
- Basado SOLO en el texto
- Enfoque en pensamiento crítico
""")

                st.session_state["preguntas"] = preguntas

# ==============================
# MOSTRAR PREGUNTAS
# ==============================
if "preguntas" in st.session_state:
    st.subheader("📋 Evaluación")
    st.write(st.session_state["preguntas"])

    st.subheader("👤 Datos del estudiante")

    nombre = st.text_input("Nombre completo")
    grado = st.selectbox("Grado", [
        "1° Primaria","2° Primaria","3° Primaria",
        "4° Primaria","5° Primaria","6° Primaria",
        "1° Secundaria","2° Secundaria","3° Secundaria",
        "4° Secundaria","5° Secundaria"
    ])
    seccion = st.text_input("Sección")

    st.subheader("✍️ Respuestas")
    respuestas = st.text_area("Escribe tus respuestas aquí")

    if st.button("🧠 Evaluar"):
        if nombre.strip() == "":
            st.warning("Ingresa tu nombre")
            st.stop()

        if seccion.strip() == "":
            st.warning("Ingresa tu sección")
            st.stop()

        if respuestas.strip() == "":
            st.warning("Escribe tus respuestas")
            st.stop()

        with st.spinner("Evaluando..."):
            resultado = ia(f"""
Actúa como docente experto del CNEB Perú.

Evaluación:
{st.session_state["preguntas"]}

Respuestas:
{respuestas}

Evalúa y devuelve:

1. Nivel por pregunta (AD, A, B, C)
2. Justificación
3. Retroalimentación
4. Recomendaciones

CRITERIOS:
AD: Excelente
A: Correcto
B: En proceso
C: Inicial

En español, claro y motivador
""")

            st.subheader("📊 Resultado")
            st.write(resultado)

            guardar_en_sheets(nombre, grado, seccion, respuestas, resultado)

            st.success("✅ Guardado en Google Sheets")
