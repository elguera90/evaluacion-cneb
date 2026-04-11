import streamlit as st
import requests
import docx2txt
import fitz  # PyMuPDF
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gtts import gTTS
import io
import re
import uuid

# ==============================
# ⚙️ CONFIGURACIÓN INICIAL
# ==============================
st.set_page_config(page_title="IA CNEB Evaluador", layout="wide", page_icon="🌌")

# ==============================
# 🎨 DISEÑO SURREALISTA Y MODERNO (CSS)
# ==============================
css_surrealista = """
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #e0eaf5; }
    div[data-testid="stForm"], div.stExpander {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    h1, h2, h3 { color: #00ffcc !important; text-shadow: 0px 0px 10px rgba(0, 255, 204, 0.7); font-family: 'Courier New', Courier, monospace; }
    .stButton>button {
        background: linear-gradient(45deg, #ff00cc, #333399); color: white; border: none; border-radius: 25px;
        height: 3.5em; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;
        box-shadow: 0px 0px 15px rgba(255, 0, 204, 0.5); transition: 0.3s ease-in-out; width: 100%;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0px 0px 25px rgba(0, 255, 204, 0.8); }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(0, 0, 0, 0.4); color: #00ffcc; border: 1px solid #ff00cc; border-radius: 10px;
    }
</style>
"""

# ==============================
# 🔑 CREDENCIALES
# ==============================
API_KEY = st.secrets.get("OPENROUTER_API_KEY")
GOOGLE_CREDS = st.secrets.get("GOOGLE_CREDENTIALS")

if not API_KEY or not GOOGLE_CREDS:
    st.error("❌ Faltan credenciales en st.secrets.")
    st.stop()

# ==============================
# 🧠 FUNCIONES IA Y LECTURA
# ==============================
def preguntar_ia(prompt, system_prompt="Eres un experto pedagógico del MINEDU Perú."):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # Usamos un modelo gratuito y rápido para evitar problemas de saldo en OpenRouter
    data = {
        "model": "mistralai/mistral-7b-instruct:free", 
        "messages": [
            {"role": "system", "content": system_prompt}, 
            {"role": "user", "content": prompt}
        ], 
        "temperature": 0.2
    }
     try:
        response = requests.post(url, headers=headers, json=data, timeout=50)
        response.raise_for_status() 
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        status = response.status_code if 'response' in locals() else 'Desconocido'
        texto_error = response.text if 'response' in locals() else str(e)
        return f"ERROR_API: {status} - {texto_error}"

def leer_archivo(file):
    try:
        if file.name.endswith(".pdf"):
            pdf = fitz.open(stream=file.read(), filetype="pdf")
            return "".join(page.get_text() for page in pdf)
        elif file.name.endswith(".docx"):
            return docx2txt.process(file)
        return ""
    except Exception as e:
        st.error(f"Error procesando documento: {e}")
        return ""

def texto_a_voz(texto):
    try:
        texto_limpio = re.sub(r'[*#_]', '', texto)
        tts = gTTS(text=texto_limpio, lang='es', tld='com.mx')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# ==============================
# 📊 GOOGLE SHEETS (CONEXIÓN DUAL)
# ==============================
@st.cache_resource
def conectar_sheets():
    creds_dict = json.loads(GOOGLE_CREDS)
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("Evaluaciones_CNEB")

def guardar_examen_creado(examen_id, grado, json_preguntas):
    try:
        sheet = conectar_sheets().worksheet("Examenes_Activos")
        sheet.append_row([examen_id, grado, str(datetime.now()), json.dumps(json_preguntas)])
        return True
    except Exception as e:
        st.error(f"Error guardando examen: {e}")
        return False

def obtener_examen(examen_id):
    try:
        sheet = conectar_sheets().worksheet("Examenes_Activos")
        registros = sheet.get_all_records()
        for fila in registros:
            if str(fila.get("ID_Examen", fila[sheet.row_values(1)[0]])) == examen_id:
                return fila
        return None
    except Exception as e:
        return None

def registrar_resultado(datos):
    try:
        sheet = conectar_sheets().worksheet("Resultados")
        sheet.append_row(datos)
        return True
    except Exception as e:
        st.error(f"Error registrando resultado: {e}")
        return False

# ==============================
# 🖥️ ENRUTAMIENTO (DOCENTE VS ESTUDIANTE)
# ==============================
# Captura el ID de la URL
id_examen_url = st.query_params.get("id")

if id_examen_url:
    # 👨‍🎓 MODO ESTUDIANTE
    st.markdown(css_surrealista, unsafe_allow_html=True)
    datos_examen = obtener_examen(id_examen_url)
    
    if datos_examen:
        hoja_activos = conectar_sheets().worksheet("Examenes_Activos")
        grado = datos_examen[hoja_activos.row_values(1)[1]] # Columna Grado
        preguntas_json = json.loads(datos_examen[hoja_activos.row_values(1)[3]]) # Columna JSON
        
        st.title("🌌 Enlace Neuronal de Evaluación")
        st.markdown(f"**Nivel de Sincronización:** {grado}")
        
        with st.form("examen_estudiante"):
            st.subheader("🧬 Identidad del Usuario")
            nombre = st.text_input("Ingresa tu designación (Nombre completo):")
            seccion = st.text_input("Sector asignado (Sección):")
            st.divider()
            
            respuestas_usuario = {}
            for q in preguntas_json:
                st.markdown(f"### 💠 Dato Solicitado {q['id']}:")
                st.write(q['pregunta'])
                if q['tipo'] == "opcion_multiple":
                    respuestas_usuario[q['id']] = st.radio("Selecciona la matriz correcta:", q['opciones'], key=f"q_{q['id']}")
                else:
                    respuestas_usuario[q['id']] = st.text_area("Desarrolla tu análisis aquí:", key=f"q_{q['id']}")
                st.write("")
                
            enviado = st.form_submit_button("⚡ Iniciar Análisis CNEB")
            
        if enviado:
            if not nombre:
                st.warning("⚠️ Identidad requerida para procesar.")
            else:
                with st.spinner("Procesando datos en el núcleo de IA..."):
                    data_eval = {"examen": preguntas_json, "respuestas": respuestas_usuario}
                    prompt = f"Evalúa este examen de {grado}. Data: {json.dumps(data_eval)}. Devuelve: 1. Nota Literal (AD, A, B, C). 2. Breve retroalimentación. 3. Sugerencia."
                    
                    eval_final = preguntar_ia(prompt)
                    
                    if eval_final and not eval_final.startswith("ERROR_API"):
                        nivel = "C"
                        for n in ["AD", "A", "B"]:
                            if n in eval_final[:20]: nivel = n; break
                        
                        st.success("✅ Análisis Completado")
                        st.info(eval_final)
                        
                        audio_fp = texto_a_voz(eval_final)
                        if audio_fp:
                            st.subheader("🔊 Transmisión de Voz Recibida")
                            st.audio(audio_fp, format="audio/mp3")
                        
                        datos_fila = [datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, grado, seccion, json.dumps(respuestas_usuario), eval_final, nivel]
                        registrar_resultado(datos_fila)
                    else:
                        st.error("Error al evaluar. Intenta de nuevo más tarde.")
    else:
        st.error("❌ El enlace neuronal está roto o el examen no existe.")

else:
    # 👨‍🏫 MODO DOCENTE
    st.title("⚙️ Panel de Control - Creador de Exámenes IA")
    
    grado = st.selectbox("Nivel Objetivo:", ["1° Primaria", "2° Primaria", "3° Primaria", "4° Primaria", "5° Primaria", "6° Primaria", "1° Secundaria", "2° Secundaria", "3° Secundaria", "4° Secundaria", "5° Secundaria"])
    archivo = st.file_uploader("Sube la matriz de conocimiento (PDF/DOCX)", type=["pdf", "docx"])
    
    if archivo and st.button("Construir Examen Virtual"):
        with st.spinner("Ensamblando preguntas de pensamiento crítico..."):
            contenido = leer_archivo(archivo)[:3500]
            
            prompt_json = f"""Basado en: {contenido}. Genera una evaluación para {grado} en formato JSON ESTRICTO. Lista de 5 objetos: [{{"id":1, "tipo":"opcion_multiple", "pregunta":"...", "opciones":["A","B"], "respuesta_correcta":"A"}}, {{"id":2, "tipo":"abierta", "pregunta":"...", "criterio":"..."}}] Solo devuelve el JSON."""
            
            respuesta = preguntar_ia(prompt_json, "Generador JSON estricto")
            
            if respuesta is None or str(respuesta).startswith("ERROR_API"):
                st.error("❌ Falló la comunicación con OpenRouter. Detalles:")
                st.code(respuesta)
                st.stop()
            
            try:
                json_clean = respuesta.replace("```json", "").replace("```", "").strip()
                preguntas = json.loads(json_clean)
                examen_id = str(uuid.uuid4())[:8] 
                
                if guardar_examen_creado(examen_id, grado, preguntas):
                    st.success("✅ Examen anclado en la base de datos.")
                    st.subheader("🔗 Enlace para Compartir con Alumnos:")
                    # Asegúrate de cambiar esto por la URL real de tu app de Streamlit si la tienes.
                    # Si no, usa la URL base predeterminada o dinámicamente:
                    url_base = "https://tudominio.streamlit.app" 
                    enlace_final = f"{url_base}?id={examen_id}"
                    
                    st.code(enlace_final, language="http")
            except Exception as e:
                st.error("❌ La IA no respetó el formato JSON o hubo un error inesperado. Intenta de nuevo.")
                st.warning(f"Detalle técnico: {e}")
