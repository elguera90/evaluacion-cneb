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
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)

        # Si falla la API
        if r.status_code != 200:
            return f"❌ Error API: {r.text}"

        respuesta = r.json()

        # Validación robusta
        if "choices" in respuesta and len(respuesta["choices"]) > 0:
            return respuesta["choices"][0]["message"]["content"]
        else:
            return f"⚠ Respuesta inesperada: {respuesta}"

    except Exception as e:
        return f"❌ Error: {e}"

# ==============================
# LECTURA ARCHIVOS
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
# UI
# ==============================
archivo = st.file_uploader("Sube sesión (PDF o DOCX)", type=["pdf","docx"])

if archivo:
    texto = leer(archivo)

    if texto:
        st.success("Archivo cargado")

        if st.button("Generar preguntas"):
            with st.spinner("Generando..."):
                preguntas = ia(f"Genera 3 preguntas con respuestas sobre:\n{texto[:2000]}")
                st.session_state["preguntas"] = preguntas

# ==============================
# RESPUESTAS
# ==============================
if "preguntas" in st.session_state:
    st.subheader("Preguntas")
    st.write(st.session_state["preguntas"])

    respuestas = st.text_area("Responde aquí")

    if st.button("Evaluar"):
        if respuestas.strip() == "":
            st.warning("Escribe tus respuestas")
        else:
            with st.spinner("Evaluando..."):
                resultado = ia(f"Evalúa estas respuestas:\n{respuestas}")
                st.subheader("Resultado")
                st.write(resultado)
