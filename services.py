"""
services.py — IA, voz, lectura de archivos y PDF
Versión corregida: modelos gratuitos, errores visibles, prompt mejorado para sesiones
"""

import streamlit as st
import requests
import docx2txt
import fitz
import json
import re
import io
import logging
from gtts import gTTS
from datetime import datetime
from config import get_api_key, MAX_CONTENT_CHARS, MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

OPENROUTER_URL  = "https://openrouter.ai/api/v1/chat/completions"
MODEL_PRIMARIO  = "openrouter/free"
MODEL_FALLBACK  = "qwen/qwen3-next-80b-a3b-instruct:free"
TIMEOUT_SECONDS = 90

SYSTEM_PEDAGOGO = (
    "Eres un experto pedagógico del MINEDU Perú especializado en el CNEB. "
    "Das retroalimentación clara, formativa y motivadora, adaptada al nivel del estudiante."
)


# ──────────────────────────────────────────────
# NÚCLEO IA
# ──────────────────────────────────────────────
def preguntar_ia(prompt: str, system: str = SYSTEM_PEDAGOGO,
                 temperatura: float = 0.2, modelo: str = None) -> str | None:
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://minedu.gob.pe",
        "X-Title": "IA CNEB MINEDU",
    }
    payload = {
        "model": MODEL_PRIMARIO,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": temperatura,
        "max_tokens": 2000,
    }

    errores = []
    for m in ([modelo] if modelo else [MODEL_PRIMARIO, MODEL_FALLBACK]):
        payload["model"] = m
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers,
                                 json=payload, timeout=TIMEOUT_SECONDS)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            errores.append(f"{m} → HTTP {resp.status_code}: {resp.text[:150]}")
            if resp.status_code not in (429, 503):
                break
        except requests.exceptions.Timeout:
            errores.append(f"{m} → Timeout tras {TIMEOUT_SECONDS}s")
        except Exception as e:
            errores.append(f"{m} → {e}")

    detalle = " | ".join(errores)
    st.error(f"❌ La IA no respondió. Detalle: {detalle}")
    st.info("💡 Verifica que **OPENROUTER_API_KEY** sea válida en Streamlit Secrets.")
    return None


# ──────────────────────────────────────────────
# GENERAR PREGUNTAS desde sesión de aprendizaje
# ──────────────────────────────────────────────
def generar_preguntas(contenido: str, grado: str, idioma: str,
                      n_preguntas: int = 5) -> list | None:
    """
    Lee la sesión de aprendizaje del docente (PDF/DOCX) y genera
    preguntas alineadas al CNEB detectando automáticamente:
    nivel, área, tema, competencias, capacidades y situación significativa.
    """
    extra_idioma = ""
    if idioma == "Quechua":
        extra_idioma = "Redacta las preguntas en quechua sureño con traducción al español entre paréntesis."
    elif idioma == "Aymara":
        extra_idioma = "Redacta las preguntas en aymara con traducción al español entre paréntesis."

    prompt = f"""Eres un especialista pedagógico del MINEDU Perú.
Analiza la siguiente SESIÓN DE APRENDIZAJE para {grado} y extrae:
- Área curricular, tema, nivel/grado
- Competencias y capacidades del CNEB involucradas
- Situación significativa o contexto

Luego genera EXACTAMENTE {n_preguntas} preguntas de evaluación que midan
el logro de las competencias identificadas. {extra_idioma}

SESIÓN DE APRENDIZAJE:
---
{contenido[:MAX_CONTENT_CHARS]}
---

Devuelve ÚNICAMENTE un array JSON sin texto extra ni bloques de código.
Mezcla tipos: al menos 3 de opción múltiple y el resto abiertas.

Formato JSON requerido:
[
  {{
    "id": 1,
    "tipo": "opcion_multiple",
    "pregunta": "Texto de la pregunta contextualizada",
    "opciones": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "respuesta_correcta": "A) ...",
    "competencia": "Nombre exacto de la competencia CNEB",
    "capacidad": "Capacidad específica evaluada"
  }},
  {{
    "id": 2,
    "tipo": "abierta",
    "pregunta": "Pregunta que exige análisis o producción",
    "criterio": "Qué se espera en una respuesta de nivel AD/A",
    "competencia": "Nombre exacto de la competencia CNEB",
    "capacidad": "Capacidad específica evaluada"
  }}
]"""

    respuesta = preguntar_ia(
        prompt,
        system="Eres un generador JSON estricto para MINEDU Perú. Devuelves SOLO el array JSON, sin explicaciones.",
        temperatura=0.1
    )
    if not respuesta:
        return None

    try:
        limpio = re.sub(r"```(?:json)?|```", "", respuesta).strip()
        # Extrae solo el array JSON si hay texto sobrante
        match = re.search(r"\[[\s\S]*\]", limpio)
        if match:
            limpio = match.group(0)
        preguntas = json.loads(limpio)
        if isinstance(preguntas, list) and len(preguntas) > 0:
            return preguntas
        st.warning("⚠️ La IA generó un JSON vacío. Intenta con un documento más detallado.")
    except json.JSONDecodeError as e:
        st.error(f"❌ La IA no devolvió JSON válido: {e}")
        st.code(respuesta[:400], language="text")

    return None


# ──────────────────────────────────────────────
# EVALUAR RESPUESTAS del estudiante
# ──────────────────────────────────────────────
def evaluar_examen(preguntas: list, respuestas: dict,
                   grado: str, idioma: str) -> dict | None:
    extra_idioma = ""
    if idioma == "Quechua":
        extra_idioma = "Responde en quechua sureño con traducción al español."
    elif idioma == "Aymara":
        extra_idioma = "Responde en aymara con traducción al español."

    prompt = f"""Evalúa las respuestas de un estudiante de {grado} según el CNEB. {extra_idioma}

PREGUNTAS Y RESPUESTAS:
{json.dumps({"preguntas": preguntas, "respuestas": respuestas}, ensure_ascii=False, indent=2)}

Devuelve SOLO este JSON (sin texto extra):
{{
  "nivel_logro": "AD",
  "puntaje_estimado": 18,
  "retroalimentacion": "Texto motivador de 3-4 oraciones dirigido al estudiante.",
  "fortalezas": ["Logro específico 1", "Logro específico 2"],
  "sugerencias": ["Acción concreta 1", "Acción concreta 2"],
  "competencias_logradas": ["Competencia 1"],
  "competencias_por_reforzar": ["Competencia 2"]
}}

Escala MINEDU: AD=18-20 (Destacado), A=14-17 (Esperado), B=11-13 (En proceso), C=0-10 (En inicio).
La retroalimentación debe ser cálida, específica y orientada a la mejora."""

    respuesta = preguntar_ia(prompt, temperatura=0.15)
    if not respuesta:
        return None

    try:
        limpio = re.sub(r"```(?:json)?|```", "", respuesta).strip()
        match = re.search(r"\{[\s\S]*\}", limpio)
        if match:
            limpio = match.group(0)
        resultado = json.loads(limpio)
        if "nivel_logro" not in resultado:
            resultado["nivel_logro"] = "C"
        return resultado
    except Exception:
        # Fallback: extrae nivel del texto libre
        nivel = "C"
        for n in ["AD", "A", "B"]:
            if n in respuesta[:40]:
                nivel = n
                break
        return {
            "nivel_logro": nivel,
            "retroalimentacion": respuesta,
            "fortalezas": [],
            "sugerencias": [],
        }


# ──────────────────────────────────────────────
# TEXTO A VOZ
# ──────────────────────────────────────────────
def texto_a_voz(texto: str, idioma_code: str = "es") -> io.BytesIO | None:
    try:
        limpio = re.sub(r"[*#_`>\[\]{}]", "", texto)[:2000]
        lang = "es" if idioma_code in ("qu", "ay") else idioma_code
        tts = gTTS(text=limpio, lang=lang, tld="com.pe", slow=False)
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
    file.seek(0, 2)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)

    if size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ Archivo demasiado grande: {size_mb:.1f} MB (máx. {MAX_FILE_SIZE_MB} MB)")
        return ""

    try:
        nombre = file.name.lower()
        if nombre.endswith(".pdf"):
            pdf = fitz.open(stream=file.read(), filetype="pdf")
            return " ".join(p.get_text() for p in pdf)
        elif nombre.endswith(".docx"):
            return docx2txt.process(file)
        else:
            st.error("❌ Formato no soportado. Usa PDF o DOCX.")
    except Exception as e:
        st.error(f"❌ Error leyendo el archivo: {e}")

    return ""


# ──────────────────────────────────────────────
# GENERAR PDF DE REPORTE
# ──────────────────────────────────────────────
def generar_reporte_pdf(resultados: list, titulo: str = "Reporte de Evaluaciones") -> io.BytesIO:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2.5*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        titulo_s = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=15,
                                  textColor=colors.HexColor("#C8102E"), alignment=TA_CENTER, spaceAfter=4)
        sub_s    = ParagraphStyle("s", fontName="Helvetica", fontSize=8,
                                  textColor=colors.HexColor("#9AA5B1"), alignment=TA_CENTER, spaceAfter=10)
        enc_s    = ParagraphStyle("e", fontName="Helvetica-Bold", fontSize=10,
                                  textColor=colors.HexColor("#4A5568"), spaceAfter=6, spaceBefore=12)

        story = [
            Paragraph("MINISTERIO DE EDUCACIÓN · PERÚ", sub_s),
            Paragraph(titulo, titulo_s),
            Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} · Total: {len(resultados)}", sub_s),
            HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#C8102E"), spaceAfter=10),
        ]

        if resultados:
            story.append(Paragraph("Detalle por Estudiante", enc_s))
            filas = [["Fecha", "Estudiante", "Grado", "Sección", "Nivel", "Idioma"]]
            for r in resultados[:200]:
                filas.append([
                    str(r.get("Timestamp", ""))[:16],
                    str(r.get("Nombre_Estudiante", ""))[:26],
                    str(r.get("Grado", "")),
                    str(r.get("Seccion", "")),
                    str(r.get("Nivel_Logro", "—")),
                    str(r.get("Idioma", "Español")),
                ])
            tabla = Table(filas, colWidths=[3*cm, 5.5*cm, 3*cm, 2.5*cm, 1.8*cm, 2.5*cm])
            tabla.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#C8102E")),
                ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.HexColor("#F4F6F9"), colors.white]),
                ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E8ECF0")),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(tabla)

            # Distribución
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("Distribución por Nivel de Logro", enc_s))
            niveles_list = [r.get("Nivel_Logro", "C") for r in resultados]
            total = len(resultados)
            desc  = {"AD": "Logro destacado", "A": "Logro esperado",
                     "B": "En proceso", "C": "En inicio"}
            res_filas = [["Nivel", "Descripción", "Cantidad", "%"]]
            for nv in ["AD", "A", "B", "C"]:
                c = niveles_list.count(nv)
                res_filas.append([nv, desc[nv], str(c),
                                  f"{c/total*100:.1f}%" if total else "0%"])
            t2 = Table(res_filas, colWidths=[2*cm, 6*cm, 2.5*cm, 2.5*cm])
            t2.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#4A5568")),
                ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 9),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.HexColor("#F4F6F9"), colors.white]),
                ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E8ECF0")),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(t2)

        story += [
            Spacer(1, 0.6*cm),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E8ECF0"), spaceAfter=4),
            Paragraph("Sistema IA CNEB v2.0 · Ministerio de Educación · Perú · www.minedu.gob.pe", sub_s),
        ]

        doc.build(story)
        buffer.seek(0)
        return buffer

    except ImportError:
        st.error("❌ Falta instalar reportlab. Agrégalo a requirements.txt")
        return io.BytesIO()
    except Exception as e:
        logger.error(f"Error PDF: {e}")
        return io.BytesIO()
