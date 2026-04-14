"""
database.py — Capa de acceso a Google Sheets
Versión con diagnóstico completo visible en UI
"""

import streamlit as st
import gspread
import json
import time
import logging
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from config import get_google_creds

logger = logging.getLogger(__name__)

SHEET_NAME    = "Evaluaciones_CNEB"
COL_EXAMENES  = ["ID_Examen", "Grado", "Idioma", "Docente", "Fecha_Creacion", "JSON_Preguntas", "Activo"]
COL_RESULTADOS= ["Timestamp", "ID_Examen", "Nombre_Estudiante", "Grado", "Seccion", "Idioma",
                 "JSON_Respuestas", "Retroalimentacion", "Nivel_Logro", "Sesion_ID"]


# ──────────────────────────────────────────────
# CONEXIÓN
# ──────────────────────────────────────────────
@st.cache_resource(ttl=3000)
def _get_client():
    raw = get_google_creds()
    creds_dict = json.loads(raw)
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)


def _get_workbook():
    return _get_client().open(SHEET_NAME)


def _get_sheet(nombre: str):
    return _get_workbook().worksheet(nombre)


def _safe_get(fila: dict, columna: str, default=""):
    return fila.get(columna, fila.get(columna.lower(), default))


def _ensure_headers(sheet, columnas: list):
    try:
        existing = sheet.row_values(1)
        if not existing:
            sheet.append_row(columnas)
    except Exception:
        sheet.append_row(columnas)


# ──────────────────────────────────────────────
# GUARDAR EXAMEN — con diagnóstico completo
# ──────────────────────────────────────────────
def guardar_examen(examen_id: str, grado: str, idioma: str,
                   docente: str, preguntas: list) -> bool:
    try:
        # Paso 1: conectar cliente
        cliente = _get_client()
    except Exception as e:
        st.error(f"❌ Error de credenciales Google: {type(e).__name__}: {e}")
        return False

    try:
        # Paso 2: abrir hoja de cálculo
        wb = cliente.open(SHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"❌ No se encontró la hoja de cálculo **'{SHEET_NAME}'**. "
                 f"Verifica que el nombre sea exactamente ese (sin espacios extra).")
        return False
    except Exception as e:
        st.error(f"❌ Error abriendo la hoja de cálculo: {type(e).__name__}: {e}")
        return False

    try:
        # Paso 3: abrir pestaña
        sheet = wb.worksheet("Examenes_Activos")
    except gspread.exceptions.WorksheetNotFound:
        st.error("❌ No se encontró la pestaña **'Examenes_Activos'**. "
                 "Crea una pestaña con ese nombre exacto en tu Google Sheets.")
        return False
    except Exception as e:
        st.error(f"❌ Error abriendo pestaña: {type(e).__name__}: {e}")
        return False

    try:
        # Paso 4: asegurar encabezados
        _ensure_headers(sheet, COL_EXAMENES)
    except Exception as e:
        st.warning(f"⚠️ No se pudieron crear encabezados: {e}")

    try:
        # Paso 5: escribir fila
        fila = [
            examen_id,
            grado,
            idioma,
            docente,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            json.dumps(preguntas, ensure_ascii=False),
            "SI",
        ]
        sheet.append_row(fila)
        return True
    except gspread.exceptions.APIError as e:
        st.error(f"❌ Error de API Google Sheets al escribir: {e.response.status_code} — {e.response.text[:300]}")
        return False
    except Exception as e:
        st.error(f"❌ Error inesperado al guardar fila: {type(e).__name__}: {e}")
        return False


# ──────────────────────────────────────────────
# OBTENER EXAMEN
# ──────────────────────────────────────────────
@st.cache_data(ttl=120)
def obtener_examen(examen_id: str) -> dict | None:
    try:
        sheet = _get_sheet("Examenes_Activos")
        for fila in sheet.get_all_records():
            if str(_safe_get(fila, "ID_Examen")) == examen_id:
                if _safe_get(fila, "Activo", "SI") == "SI":
                    return fila
        return None
    except Exception as e:
        logger.error(f"obtener_examen: {e}")
        return None


def listar_examenes(docente: str = None) -> list:
    try:
        sheet = _get_sheet("Examenes_Activos")
        registros = sheet.get_all_records()
        if docente:
            return [r for r in registros if _safe_get(r, "Docente") == docente]
        return registros
    except Exception as e:
        logger.error(f"listar_examenes: {e}")
        return []


# ──────────────────────────────────────────────
# REGISTRAR RESULTADO
# ──────────────────────────────────────────────
def registrar_resultado(datos: dict) -> bool:
    try:
        sheet = _get_sheet("Resultados")
        _ensure_headers(sheet, COL_RESULTADOS)
        fila = [
            datos.get("timestamp", datetime.now().strftime("%d/%m/%Y %H:%M")),
            datos.get("examen_id", ""),
            datos.get("nombre", ""),
            datos.get("grado", ""),
            datos.get("seccion", ""),
            datos.get("idioma", "Español"),
            json.dumps(datos.get("respuestas", {}), ensure_ascii=False),
            datos.get("retroalimentacion", ""),
            datos.get("nivel_logro", "C"),
            datos.get("sesion_id", ""),
        ]
        sheet.append_row(fila)
        return True
    except gspread.exceptions.WorksheetNotFound:
        st.error("❌ No se encontró la pestaña **'Resultados'**. Créala en tu Google Sheets.")
        return False
    except Exception as e:
        st.error(f"❌ Error registrando resultado: {type(e).__name__}: {e}")
        return False


# ──────────────────────────────────────────────
# ANALYTICS
# ──────────────────────────────────────────────
@st.cache_data(ttl=60)
def obtener_resultados(examen_id: str = None) -> list:
    try:
        sheet = _get_sheet("Resultados")
        registros = sheet.get_all_records()
        if examen_id:
            return [r for r in registros if str(_safe_get(r, "ID_Examen")) == examen_id]
        return registros
    except Exception as e:
        logger.error(f"obtener_resultados: {e}")
        return []


def obtener_todos_resultados() -> list:
    try:
        return _get_sheet("Resultados").get_all_records()
    except Exception as e:
        logger.error(f"obtener_todos_resultados: {e}")
        return []
