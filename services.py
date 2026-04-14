"""
services.py — Servicios de IA, voz, lectura de archivos y generación de PDF
"""

import streamlit as st
import requests
import docx2txt
import fitz  # PyMuPDF
import json
import re
import io
import logging
from gtts import gTTS
from datetime import datetime
from config import get_api_key, MAX_CONTENT_CHARS, MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# CONSTANTES DE IA
# ──────────────────────────────────────────────
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_PRIMARIO  = "anthropic/claude-3-haiku"        # Estable y rápido
MODEL_FALLBACK  = "qwen/qwen3-30b-a3b:free"         # Gratuito de respaldo
TIMEOUT_SECONDS = 60

SYSTEM_PEDAGOGO = (
    "Eres un experto pedagógico del MINEDU Perú especializado en el CNEB "
    "(Currículo Nacional de Educación Básica). Tus respuestas son claras, "
    "precisas, formativas y adaptadas al nivel del estudiante. "
    "Siempre das retroalimentación constructiva."
)


# ──────────────────────────────────────────────
# SERVICIO IA — OpenRouter con fallback
# ──────────────────────────────────────────────
def preguntar_ia(prompt: str, system: str = SYSTEM_PEDAGOGO,
                 temperatura: float = 0.2, modelo: str = None) -> str | None:
    """
    Consulta al LLM vía OpenRouter.
    Retorna el texto de respuesta o None en caso de error.
    """
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://minedu.gob.pe",
        "X-Title": "IA CNEB MINEDU",
    }
    payload = {
        "model": modelo or MODEL_PRIMARIO,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": temperatura,
        "max_tokens": 1500,
    }

    for modelo_intento in [modelo or MODEL_PRIMARIO, MODEL_FALLBACK]:
        payload["model"] = modelo_intento
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers,
                                 json=payload, timeout=TIMEOUT_SECONDS)
            resp.raise_for_status()
            data = resp.json()
            contenido = data["choices"][0]["message"]["content"]
            logger.info(f"IA respondió con modelo: {modelo_intento}")
            return contenido
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout con {modelo_intento}")
            continue
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP {resp.status_code} con {modelo_intento}: {e}")
            if resp.status_code == 429:   # Rate limit → intenta fallback
                continue
            return None
        except Exception as e:
            logger.error(f"Error inesperado IA: {e}")
            return None

    return None  # Ambos modelos fallaron


# ──────────────────────────────────────────────
# GENERACIÓN DE EXAMEN (JSON estructurado)
# ──────────────────────────────────────────────
def generar_preguntas(contenido: str, grado: str, idioma: str,
                      n_preguntas: int = 5) -> list | None:
    """
    Genera preguntas de evaluación alineadas al CNEB en formato JSON.
    Retorna lista de dicts o None si falla.
    """
    instruccion_idioma = ""
    if idioma == "Quechua":
        instruccion_idioma = "Genera las preguntas en quechua sureño (Cusco-Collao). Incluye también la versión en español entre paréntesis."
    elif idioma == "Aymara":
        instruccion_idioma = "Genera las preguntas en aymara. Incluye también la versión en español entre paréntesis."

    prompt = f"""
Basado en el siguiente contenido curricular para {grado}:

---
{contenido[:MAX_CONTENT_CHARS]}
---

{instruccion_idioma}

Genera exactamente {n_preguntas} preguntas de evaluación alineadas al CNEB.
Devuelve ÚNICAMENTE un array JSON válido, sin texto adicional, sin comillas de código.

Formato estricto:
[
  {{
    "id": 1,
    "tipo": "opcion_multiple",
    "pregunta": "Texto de la pregunta",
    "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
    "respuesta_correcta": "Opción A",
    "competencia": "Nombre de la competencia CNEB relacionada"
  }},
  {{
    "id": 2,
    "tipo": "abierta",
    "pregunta": "Texto de la pregunta abierta",
    "criterio": "Criterio de evaluación para el docente",
    "competencia": "Nombre de la competencia CNEB relacionada"
  }}
]

Combina al menos 3 de opción múltiple y {n_preguntas - 3} abiertas.
"""

    respuesta = preguntar_ia(prompt, system="Eres un generador JSON estricto. Solo devuelves JSON puro.", temperatura=0.1)
    if not respuesta:
        return None

    try:
        # Limpia posibles restos de markdown
        limpio = re.sub(r"```(?:json)?|```", "", respuesta).strip()
        preguntas = json.loads(limpio)
        if isinstance(preguntas, list) and len(preguntas) > 0:
            return preguntas
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido generado por IA: {e}\nRespuesta: {respuesta[:300]}")

    return None


# ──────────────────────────────────────────────
# EVALUACIÓN DE RESPUESTAS
# ──────────────────────────────────────────────
def evaluar_examen(preguntas: list, respuestas: dict,
                   grado: str, idioma: str) -> dict | None:
    """
    Evalúa las respuestas de un estudiante.
    Retorna dict con nivel_logro, retroalimentacion, sugerencias.
    """
    instruccion_idioma = ""
    if idioma == "Quechua":
        instruccion_idioma = "Responde en quechua sureño con traducción en español."
    elif idioma == "Aymara":
        instruccion_idioma = "Responde en aymara con traducción en español."

    data_eval = {
        "grado": grado,
        "preguntas": preguntas,
        "respuestas_estudiante": respuestas,
    }

    prompt = f"""
Evalúa el siguiente examen del CNEB para {grado}.
{instruccion_idioma}

Datos: {json.dumps(data_eval, ensure_ascii=False)}

Devuelve ÚNICAMENTE JSON con esta estructura:
{{
  "nivel_logro": "AD|A|B|C",
  "puntaje_estimado": 18,
  "retroalimentacion": "Texto formativo y motivador de 3-4 oraciones.",
  "fortalezas": ["fortaleza 1", "fortaleza 2"],
  "sugerencias": ["sugerencia 1", "sugerencia 2"],
  "competencias_logradas": ["competencia 1"],
  "competencias_por_reforzar": ["competencia 2"]
}}

Criterios MINEDU:
- AD: Logro destacado (18-20)
- A: Logro esperado (14-17)
- B: En proceso (11-13)
- C: En inicio (0-10)
"""

    respuesta = preguntar_ia(prompt, temperatura=0.15)
    if not respuesta:
        return None

    try:
        limpio = re.sub(r"```(?:json)?|```", "", respuesta).strip()
        resultado = json.loads(limpio)
        # Validación mínima
        if "nivel_logro" not in resultado:
            resultado["nivel_logro"] = "C"
        if "retroalimentacion" not in resultado:
            resultado["retroalimentacion"] = respuesta
        return resultado
    except Exception:
        # Fallback: extrae nivel del texto libre
        nivel = "C"
        for n in ["AD", "A", "B"]:
            if n in respuesta[:30]:
                nivel = n
                break
        return {"nivel_logro": nivel, "retroalimentacion": respuesta,
                "fortalezas": [], "sugerencias": []}


# ──────────────────────────────────────────────
# TEXTO A VOZ
# ──────────────────────────────────────────────
def texto_a_voz(texto: str, idioma_code: str = "es") -> io.BytesIO | None:
    """
    Convierte texto a audio MP3 con gTTS.
    Para quechua/aymara usa español (no soportados por gTTS).
    """
    try:
        # Limpia markdown
        limpio = re.sub(r"[*#_`>]", "", texto)
        # Trunca si es muy largo (gTTS tiene límites)
        limpio = limpio[:2000]

        # gTTS no soporta qu/ay; se usa español como fallback
        lang = "es" if idioma_code in ("qu", "ay") else idioma_code
        tld = "com.pe"  # Acento peruano

        tts = gTTS(text=limpio, lang=lang, tld=tld, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        logger.warning(f"TTS falló: {e}")
        return None


# ──────────────────────────────────────────────
# LECTURA DE ARCHIVOS
# ──────────────────────────────────────────────
def leer_archivo(file) -> str:
    """
    Extrae texto de PDF o DOCX.
    Valida tamaño antes de procesar.
    """
    # Validar tamaño
    file.seek(0, 2)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)

    if size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ El archivo supera el límite de {MAX_FILE_SIZE_MB} MB ({size_mb:.1f} MB).")
        return ""

    try:
        if file.name.lower().endswith(".pdf"):
            pdf = fitz.open(stream=file.read(), filetype="pdf")
            texto = " ".join(page.get_text() for page in pdf)
            return texto[:MAX_CONTENT_CHARS * 2]  # Margen para truncar luego

        elif file.name.lower().endswith(".docx"):
            return docx2txt.process(file)[:MAX_CONTENT_CHARS * 2]

    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {e}")

    return ""


# ──────────────────────────────────────────────
# GENERACIÓN DE REPORTE PDF
# ──────────────────────────────────────────────
def generar_reporte_pdf(resultados: list, titulo: str = "Reporte de Evaluaciones") -> io.BytesIO:
    """
    Genera un PDF con los resultados de evaluación usando reportlab.
    Compatible con Streamlit download_button.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2.5*cm, bottomMargin=2*cm)

        estilos = getSampleStyleSheet()
        story = []

        # ── Estilo personalizado ──
        estilo_titulo = ParagraphStyle("titulo",
            fontName="Helvetica-Bold", fontSize=16,
            textColor=colors.HexColor("#C8102E"),
            alignment=TA_CENTER, spaceAfter=4)

        estilo_subtitulo = ParagraphStyle("sub",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#9AA5B1"),
            alignment=TA_CENTER, spaceAfter=12)

        estilo_normal = ParagraphStyle("normal",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#1A202C"),
            leading=14)

        estilo_encabezado = ParagraphStyle("enc",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=6, spaceBefore=12)

        # ── Cabecera ──
        story.append(Paragraph("MINISTERIO DE EDUCACIÓN · PERÚ", estilo_subtitulo))
        story.append(Paragraph(titulo, estilo_titulo))
        story.append(Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
            f"Total registros: {len(resultados)}",
            estilo_subtitulo
        ))
        story.append(HRFlowable(width="100%", thickness=1.5,
                                color=colors.HexColor("#C8102E"),
                                spaceAfter=12))

        if not resultados:
            story.append(Paragraph("No hay resultados para mostrar.", estilo_normal))
        else:
            # ── Tabla de resultados ──
            story.append(Paragraph("Detalle por Estudiante", estilo_encabezado))

            encabezados = ["Fecha", "Estudiante", "Grado", "Sección", "Nivel", "Idioma"]
            filas = [encabezados]

            colores_nivel = {
                "AD": colors.HexColor("#1a9e6c"),
                "A":  colors.HexColor("#2980B9"),
                "B":  colors.HexColor("#F39C12"),
                "C":  colors.HexColor("#C8102E"),
            }

            for r in resultados[:200]:  # Límite de filas por PDF
                filas.append([
                    str(r.get("Timestamp", ""))[:16],
                    str(r.get("Nombre_Estudiante", ""))[:28],
                    str(r.get("Grado", "")),
                    str(r.get("Seccion", "")),
                    str(r.get("Nivel_Logro", "—")),
                    str(r.get("Idioma", "Español")),
                ])

            tabla = Table(filas, colWidths=[3*cm, 5.5*cm, 3.2*cm, 2.5*cm, 1.8*cm, 2.5*cm])
            estilo_tabla = TableStyle([
                ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#C8102E")),
                ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
                ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",     (0, 0), (-1, -1), 8),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.HexColor("#F4F6F9"), colors.white]),
                ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#E8ECF0")),
                ("TOPPADDING",   (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROUNDEDCORNERS", [4]),
            ])
            tabla.setStyle(estilo_tabla)
            story.append(tabla)

            # ── Distribución por nivel ──
            story.append(Spacer(1, 0.6*cm))
            story.append(Paragraph("Distribución por Nivel de Logro", estilo_encabezado))

            conteo = {}
            for r in resultados:
                n = r.get("Nivel_Logro", "C")
                conteo[n] = conteo.get(n, 0) + 1

            resumen_filas = [["Nivel", "Descripción", "Cantidad", "Porcentaje"]]
            descripciones = {"AD": "Logro destacado", "A": "Logro esperado",
                             "B": "En proceso", "C": "En inicio"}
            total = len(resultados)
            for nivel in ["AD", "A", "B", "C"]:
                cant = conteo.get(nivel, 0)
                pct = f"{cant/total*100:.1f}%" if total > 0 else "0%"
                resumen_filas.append([nivel, descripciones.get(nivel, ""), str(cant), pct])

            tabla_resumen = Table(resumen_filas, colWidths=[2*cm, 6*cm, 2.5*cm, 3*cm])
            tabla_resumen.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#4A5568")),
                ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
                ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",     (0, 0), (-1, -1), 9),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.HexColor("#F4F6F9"), colors.white]),
                ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#E8ECF0")),
                ("TOPPADDING",   (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(tabla_resumen)

        # ── Pie de página ──
        story.append(Spacer(1, 0.8*cm))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#E8ECF0"), spaceAfter=6))
        story.append(Paragraph(
            "Sistema IA CNEB v2.0 · Ministerio de Educación · Perú · www.minedu.gob.pe",
            estilo_subtitulo
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer

    except ImportError:
        # reportlab no instalado
        st.error("❌ reportlab no está instalado. Agrega `reportlab` a requirements.txt")
        return io.BytesIO()
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        return io.BytesIO()
