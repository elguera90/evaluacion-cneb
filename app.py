import streamlit as st
import requests
import docx2txt
import fitz

st.title("📚 Evaluación con IAG - EdTech • Ingeniería Educativa")

API_KEY = st.secrets["OPENROUTER_API_KEY"]

def leer(file):
    if file.name.endswith(".pdf"):
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        return "".join([p.get_text() for p in pdf])
    else:
        return docx2txt.process(file)

def ia(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(url, headers=headers, json=data)
    return r.json()["choices"][0]["message"]["content"]

archivo = st.file_uploader("Sube sesión", type=["pdf","docx"])

if archivo:
    texto = leer(archivo)

    if st.button("Generar preguntas"):
        preguntas = ia(f"Genera 3 preguntas con respuestas sobre: {texto}")
        st.session_state["preguntas"] = preguntas

if "preguntas" in st.session_state:
    st.write(st.session_state["preguntas"])

    respuestas = st.text_area("Responde aquí")

    if st.button("Evaluar"):
        resultado = ia(f"Evalúa: {respuestas}")
        st.write(resultado)
