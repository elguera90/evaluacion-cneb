"""
database.py — Capa de acceso a Google Sheets
Diseño robusto: mapeo por nombre de columna, reintentos y caché controlada
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

# ──────────────────────────────────────────────
# ESQUEMA DE HOJAS (nombres de columna fijos)
# ──────────────────────────────────────────────
SHEET_NAME = "Evaluaciones_CNEB"

COL_EXAMENES = ["ID_Examen", "Grado", "Idioma", "Docente", "Fecha_Creacion", "JSON_Preguntas", "Activo"]
COL_RESULTADOS = ["Timestamp", "ID_Examen", "Nombre_Estudiante", "Grado", "Seccion", "Idioma",
                  "JSON_Respuestas", "Retroalimentacion", "Nivel_Logro", "Sesion_ID"]


# ──────────────────────────────────────────────
# CONEXIÓN (cache de 50 min para evitar token expiry)
# ──────────────────────────────────────────────
@st.cache_resource(ttl=3000)
def _get_client():
    """Crea y cachea el cliente de gspread."""
    creds_dict = json.loads(get_google_creds())
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


# ──────────────────────────────────────────────
# HELPERS ROBUSTOS
# ──────────────────────────────────────────────
def _safe_get(fila: dict, columna: str, default=""):
    """Accede a columna por nombre; tolerante a variaciones de clave."""
    return fila.get(columna, fila.get(columna.lower(), default))


def _retry(func, retries=3, delay=1.5):
    """Reintenta una función ante errores transitorios de la API."""
    for intento in range(retries):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            if intento == retries - 1:
                raise
            logger.warning(f"Google Sheets APIError (intento {intento+1}): {e}")
            time.sleep(delay * (intento + 1))


def _ensure_headers(sheet, columnas: list):
    """Crea encabezados si la hoja está vacía."""
    if not sheet.row_values(1):
        sheet.append_row(columnas)


# ──────────────────────────────────────────────
# OPERACIONES: EXÁMENES
# ──────────────────────────────────────────────
def guardar_examen(examen_id: str, grado: str, idioma: str,
                   docente: str, preguntas: list) -> bool:
    """Persiste un examen generado por el docente."""
    def _op():
        sheet = _get_sheet("Examenes_Activos")
        _ensure_headers(sheet, COL_EXAMENES)
        sheet.append_row([
            examen_id,
            grado,
            idioma,
            docente,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            json.dumps(preguntas, ensure_ascii=False),
            "SI",
        ])
    try:
        _retry(_op)
        return True
    except Exception as e:
        logger.error(f"guardar_examen: {e}")
        return False


@st.cache_data(ttl=120)  # Caché de 2 min para lecturas frecuentes
def obtener_examen(examen_id: str) -> dict | None:
    """Busca un examen por ID. Retorna dict con los datos o None."""
    try:
        def _op():
            sheet = _get_sheet("Examenes_Activos")
            registros = sheet.get_all_records()
            for fila in registros:
                if str(_safe_get(fila, "ID_Examen")) == examen_id:
                    if _safe_get(fila, "Activo", "SI") == "SI":
                        return fila
            return None
        return _retry(_op)
    except Exception as e:
        logger.error(f"obtener_examen: {e}")
        return None


def listar_examenes(docente: str = None) -> list[dict]:
    """Lista todos los exámenes (filtrado opcional por docente)."""
    try:
        def _op():
            sheet = _get_sheet("Examenes_Activos")
            registros = sheet.get_all_records()
            if docente:
                return [r for r in registros if _safe_get(r, "Docente") == docente]
            return registros
        return _retry(_op) or []
    except Exception as e:
        logger.error(f"listar_examenes: {e}")
        return []


# ──────────────────────────────────────────────
# OPERACIONES: RESULTADOS
# ──────────────────────────────────────────────
def registrar_resultado(datos: dict) -> bool:
    """Guarda el resultado de un estudiante."""
    def _op():
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
    try:
        _retry(_op)
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Detalle del error Google Sheets: {type(e).__name__}: {e}")
        logger.error(f"guardar_examen: {e}")
        return False


@st.cache_data(ttl=60)
def obtener_resultados(examen_id: str = None) -> list[dict]:
    """Obtiene resultados; filtra por examen si se especifica."""
    try:
        def _op():
            sheet = _get_sheet("Resultados")
            registros = sheet.get_all_records()
            if examen_id:
                return [r for r in registros if str(_safe_get(r, "ID_Examen")) == examen_id]
            return registros
        return _retry(_op) or []
    except Exception as e:
        logger.error(f"obtener_resultados: {e}")
        return []


def obtener_todos_resultados() -> list[dict]:
    """Todos los resultados para el dashboard analítico."""
    try:
        def _op():
            return _get_sheet("Resultados").get_all_records()
        return _retry(_op) or []
    except Exception as e:
        logger.error(f"obtener_todos_resultados: {e}")
        return []
