"""
router.py — Vistas principales: modo docente y modo estudiante
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from config import get_app_url, GRADOS, IDIOMAS, NIVELES_LOGRO
from auth import render_session_info
from database import (guardar_examen, obtener_examen, listar_examenes,
                      registrar_resultado, obtener_todos_resultados,
                      obtener_resultados)
from services import (preguntar_ia, generar_preguntas, evaluar_examen,
                      texto_a_voz, leer_archivo, generar_reporte_pdf)


# ══════════════════════════════════════════════
# MODO DOCENTE
# ══════════════════════════════════════════════

def render_docente():
    _sidebar_docente()

    vista = st.session_state.get("vista_docente", "Crear Examen")

    if vista == "Crear Examen":
        _vista_crear_examen()
    elif vista == "Mis Exámenes":
        _vista_mis_examenes()
    elif vista == "Analítica":
        _vista_analitica()


def _sidebar_docente():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0 0.5rem;">
            <div style="font-size:2.5rem;">🎓</div>
            <div style="font-size:0.82rem; font-weight:800; color:white; letter-spacing:0.01em; line-height:1.3; margin-top:0.3rem;">
                Sistema de Retroalimentación<br>con IA Generativa
            </div>
            <div style="font-size:0.72rem; color:rgba(255,255,255,0.8); margin-top:0.2rem; font-weight:500;">
                Aula de Innovación Pedagógica
            </div>
            <div style="font-size:0.68rem; color:rgba(255,255,255,0.6); margin-top:0.1rem;">
                MINEDU · Perú
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        opciones = ["Crear Examen", "Mis Exámenes", "Analítica"]
        iconos   = ["✏️", "📋", "📊"]
        actual   = st.session_state.get("vista_docente", "Crear Examen")

        for op, ic in zip(opciones, iconos):
            activo = "background:rgba(255,255,255,0.2); border-radius:8px;" if op == actual else ""
            if st.button(f"{ic}  {op}", use_container_width=True, key=f"nav_{op}"):
                st.session_state["vista_docente"] = op
                st.rerun()

        render_session_info()


def _vista_crear_examen():
    _header_institucional("✏️ Crear Nuevo Examen", "Genera evaluaciones alineadas al CNEB con IA")

    col1, col2 = st.columns([1.6, 1], gap="large")

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📐 Configuración del Examen")

        grado = st.selectbox("Grado / Nivel", GRADOS, key="cfg_grado")
        idioma = st.selectbox("Idioma de evaluación", list(IDIOMAS.keys()), key="cfg_idioma")
        n_preguntas = st.slider("Número de preguntas", 3, 10, 5, key="cfg_npreguntas")
        archivo = st.file_uploader(
            "Sube la unidad didáctica o matriz de conocimiento",
            type=["pdf", "docx"],
            help="Máximo 10 MB · PDF o DOCX",
            key="cfg_archivo"
        )

        if archivo:
            st.caption(f"📄 {archivo.name} cargado correctamente")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card" style="height:100%;">', unsafe_allow_html=True)
        st.markdown("#### 💡 Indicaciones")
        st.markdown("""
        <div style="font-size:0.88rem; color:#4A5568; line-height:1.7;">
        1. Selecciona el grado y el idioma<br>
        2. Sube tu material curricular (PDF/DOCX)<br>
        3. Haz clic en <strong>Generar Examen</strong><br>
        4. Copia el enlace y compártelo con tus estudiantes<br><br>
        <strong>Idiomas disponibles:</strong><br>
        🇵🇪 Español · Quechua · Aymara
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("⚡ Generar Examen con IA", use_container_width=True, key="btn_generar"):
        if not archivo:
            st.warning("⚠️ Sube un documento para continuar.")
            return

        _generar_y_guardar_examen(archivo, grado, idioma, n_preguntas)


def _generar_y_guardar_examen(archivo, grado, idioma, n_preguntas):
    with st.status("Generando examen con IA...", expanded=True) as status:
        st.write("📖 Leyendo documento...")
        contenido = leer_archivo(archivo)
        if not contenido.strip():
            status.update(label="Error en lectura", state="error")
            st.error("No se pudo extraer texto del documento.")
            return

        st.write("🧠 Generando preguntas alineadas al CNEB...")
        docente = st.session_state.get("docente_nombre", "Docente")
        preguntas = generar_preguntas(contenido, grado, idioma, n_preguntas)

        if not preguntas:
            status.update(label="Error de IA", state="error")
            st.error("❌ No se pudieron generar las preguntas. Intenta de nuevo.")
            return

        st.write("💾 Guardando en Google Sheets...")
        examen_id = str(uuid.uuid4())[:8].upper()
        guardado = guardar_examen(examen_id, grado, idioma, docente, preguntas)

        if not guardado:
            status.update(label="Error al guardar", state="error")
            st.error("❌ Fallo al guardar en Google Sheets.")
            return

        status.update(label="✅ Examen creado exitosamente", state="complete")

    # ── Resultado ──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🔗 Examen Listo para Compartir")

    url_base = get_app_url()
    enlace = f"{url_base}?id={examen_id}"

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.code(enlace, language=None)
    with col_b:
        st.markdown(f"""
        <a href="{enlace}" target="_blank">
            <button style="width:100%;padding:0.5rem;background:#C8102E;color:white;
                           border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                🔗 Abrir
            </button>
        </a>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="alert-info" style="margin-top:0.8rem;">
        <strong>ID del examen:</strong> <code>{examen_id}</code> |
        <strong>Grado:</strong> {grado} |
        <strong>Idioma:</strong> {idioma} |
        <strong>Preguntas:</strong> {len(preguntas)}
    </div>
    """, unsafe_allow_html=True)

    # ── Vista previa ──
    with st.expander("👁️ Vista previa de preguntas generadas"):
        for q in preguntas:
            st.markdown(f"**{q['id']}.** {q['pregunta']}")
            if q["tipo"] == "opcion_multiple":
                for op in q.get("opciones", []):
                    tick = "✅" if op == q.get("respuesta_correcta") else "○"
                    st.markdown(f"&nbsp;&nbsp;&nbsp;{tick} {op}")
            else:
                st.caption(f"📝 Criterio: {q.get('criterio', '—')}")
            st.markdown(f"<small>📌 {q.get('competencia', '')}</small>", unsafe_allow_html=True)
            st.divider()

    st.markdown('</div>', unsafe_allow_html=True)


def _vista_mis_examenes():
    _header_institucional("📋 Mis Exámenes", "Historial de evaluaciones creadas")

    docente = st.session_state.get("docente_nombre", "")
    examenes = listar_examenes(docente)

    if not examenes:
        st.info("ℹ️ Aún no has creado ningún examen. Ve a **Crear Examen** para comenzar.")
        return

    # ── Filtros ──
    col1, col2 = st.columns(2)
    with col1:
        filtro_grado = st.selectbox("Filtrar por grado", ["Todos"] + GRADOS, key="fil_grado")
    with col2:
        filtro_idioma = st.selectbox("Filtrar por idioma", ["Todos"] + list(IDIOMAS.keys()), key="fil_idioma")

    filtrados = examenes
    if filtro_grado != "Todos":
        filtrados = [e for e in filtrados if e.get("Grado") == filtro_grado]
    if filtro_idioma != "Todos":
        filtrados = [e for e in filtrados if e.get("Idioma") == filtro_idioma]

    st.markdown(f"**{len(filtrados)} examen(es) encontrado(s)**")

    for examen in filtrados:
        ex_id  = examen.get("ID_Examen", "—")
        grado  = examen.get("Grado", "—")
        idioma = examen.get("Idioma", "Español")
        fecha  = examen.get("Fecha_Creacion", "—")

        resultados = obtener_resultados(ex_id)
        n_res = len(resultados)

        with st.expander(f"📘 {ex_id} · {grado} · {idioma} — {fecha}"):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Respuestas recibidas", n_res)

            if resultados:
                niveles = [r.get("Nivel_Logro", "C") for r in resultados]
                dist = {n: niveles.count(n) for n in NIVELES_LOGRO if n in niveles}
                col_b.metric("Nivel más frecuente", max(dist, key=dist.get) if dist else "—")

            url = f"{get_app_url()}?id={ex_id}"
            col_c.markdown(f"[🔗 Abrir enlace]({url})")

            if n_res > 0:
                pdf_bytes = generar_reporte_pdf(resultados,
                    titulo=f"Reporte · {grado} · {ex_id}")
                st.download_button(
                    label="⬇️ Descargar reporte PDF",
                    data=pdf_bytes,
                    file_name=f"reporte_{ex_id}.pdf",
                    mime="application/pdf",
                    key=f"dl_{ex_id}"
                )


def _vista_analitica():
    _header_institucional("📊 Analítica de Aprendizaje", "Panel de seguimiento pedagógico CNEB")

    resultados = obtener_todos_resultados()

    if not resultados:
        st.info("ℹ️ Aún no hay resultados registrados.")
        return

    total = len(resultados)
    niveles = [r.get("Nivel_Logro", "C") for r in resultados]

    # ── KPIs ──
    cols = st.columns(4)
    kpis = [
        ("Total evaluados", total, "👥"),
        ("Logro destacado (AD)", niveles.count("AD"), "🌟"),
        ("Logro esperado (A)",   niveles.count("A"),  "✅"),
        ("En proceso/inicio (B+C)", niveles.count("B") + niveles.count("C"), "📈"),
    ]
    for col, (label, valor, emoji) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.8rem;">{emoji}</div>
                <div style="font-size:1.6rem; font-weight:700; color:#1A202C;">{valor}</div>
                <div style="font-size:0.78rem; color:#9AA5B1; font-weight:500;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficas ──
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Distribución por Nivel de Logro")
        dist = {n: niveles.count(n) for n in NIVELES_LOGRO}
        st.bar_chart(dist, color="#C8102E")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_der:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Distribución por Grado")
        grados_data = {}
        for r in resultados:
            g = r.get("Grado", "—")
            grados_data[g] = grados_data.get(g, 0) + 1
        if grados_data:
            st.bar_chart(grados_data, color="#2980B9")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Idiomas ──
    idiomas_data = {}
    for r in resultados:
        i = r.get("Idioma", "Español")
        idiomas_data[i] = idiomas_data.get(i, 0) + 1

    if len(idiomas_data) > 1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Evaluaciones por Idioma")
        st.bar_chart(idiomas_data, color="#1a9e6c")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tabla reciente ──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📋 Últimas 20 evaluaciones")

    import pandas as pd
    df = pd.DataFrame(resultados[-20:][::-1])[
        ["Timestamp", "Nombre_Estudiante", "Grado", "Seccion", "Nivel_Logro", "Idioma"]
    ].rename(columns={
        "Timestamp": "Fecha",
        "Nombre_Estudiante": "Estudiante",
        "Nivel_Logro": "Nivel",
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Exportar completo ──
    pdf_bytes = generar_reporte_pdf(resultados, "Reporte General · IA CNEB MINEDU")
    st.download_button(
        "⬇️ Exportar reporte completo PDF",
        data=pdf_bytes,
        file_name=f"reporte_general_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# MODO ESTUDIANTE
# ══════════════════════════════════════════════

def render_estudiante(examen_id: str):
    datos = obtener_examen(examen_id)

    if not datos:
        st.error("❌ El enlace es inválido o el examen ya no está disponible.")
        st.info("Contacta a tu docente para obtener un enlace actualizado.")
        return

    grado        = datos.get("Grado", "")
    idioma       = datos.get("Idioma", "Español")
    idioma_code  = IDIOMAS.get(idioma, "es")

    try:
        preguntas = json.loads(datos.get("JSON_Preguntas", "[]"))
    except Exception:
        st.error("❌ Error al cargar las preguntas. Contacta al docente.")
        return

    # ── Cabecera estudiante ──
    _header_institucional(
        f"📝 Evaluación · {grado}",
        f"Sistema Sistema de Retroalimentación con IA Generativa · Idioma: {idioma}",
        modo="estudiante"
    )

    if idioma == "Quechua":
        st.info("🌐 Esta evaluación está disponible en quechua y español.")
    elif idioma == "Aymara":
        st.info("🌐 Esta evaluación está disponible en aymara y español.")

    # ── Prevenir envíos múltiples ──
    if st.session_state.get(f"enviado_{examen_id}", False):
        st.success("✅ Ya enviaste tu evaluación. ¡Gracias!")
        return

    # ── Formulario de datos ──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 👤 Tus datos")
    col1, col2 = st.columns(2)
    nombre  = col1.text_input("Nombre completo *", placeholder="Nombre Apellido", key="est_nombre")
    seccion = col2.text_input("Sección",           placeholder="A, B, C...",     key="est_seccion")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Preguntas ──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"#### 📋 Preguntas ({len(preguntas)} en total)")

    progreso = st.progress(0, text="Progreso de respuestas")
    respuestas = {}
    respondidas = 0

    for idx, q in enumerate(preguntas):
        st.markdown(f"**{q['id']}.** {q['pregunta']}")
        if q.get("competencia"):
            st.caption(f"📌 Competencia: {q['competencia']}")

        if q["tipo"] == "opcion_multiple":
            respuestas[q["id"]] = st.radio(
                "Selecciona una opción:",
                q.get("opciones", []),
                key=f"resp_{q['id']}",
                index=None
            )
        else:
            respuestas[q["id"]] = st.text_area(
                "Desarrolla tu respuesta:",
                key=f"resp_{q['id']}",
                height=120,
                placeholder="Escribe aquí tu respuesta..."
            )

        respondidas = sum(1 for v in respuestas.values() if v)
        progreso.progress(respondidas / len(preguntas),
                          text=f"Respondidas: {respondidas}/{len(preguntas)}")
        st.divider()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Envío ──
    if st.button("✅ Enviar Evaluación", use_container_width=True, key="btn_enviar"):
        _procesar_envio(nombre, seccion, grado, idioma, idioma_code,
                        examen_id, preguntas, respuestas)


def _procesar_envio(nombre, seccion, grado, idioma, idioma_code,
                    examen_id, preguntas, respuestas):
    if not nombre.strip():
        st.warning("⚠️ Por favor ingresa tu nombre completo.")
        return

    respondidas = sum(1 for v in respuestas.values() if v)
    if respondidas < len(preguntas):
        st.warning(f"⚠️ Tienes {len(preguntas) - respondidas} pregunta(s) sin responder.")

    with st.status("Evaluando con IA pedagógica...", expanded=True) as status:
        st.write("🧠 Analizando tus respuestas...")
        resultado = evaluar_examen(preguntas, respuestas, grado, idioma)

        if not resultado:
            status.update(label="Error de evaluación", state="error")
            st.error("❌ Error al evaluar. Por favor intenta de nuevo.")
            return

        st.write("💾 Guardando resultado...")
        sesion_id = str(uuid.uuid4())[:6]
        datos_guardar = {
            "timestamp":        datetime.now().strftime("%d/%m/%Y %H:%M"),
            "examen_id":        examen_id,
            "nombre":           nombre.strip(),
            "grado":            grado,
            "seccion":          seccion,
            "idioma":           idioma,
            "respuestas":       respuestas,
            "retroalimentacion": resultado.get("retroalimentacion", ""),
            "nivel_logro":      resultado.get("nivel_logro", "C"),
            "sesion_id":        sesion_id,
        }
        registrar_resultado(datos_guardar)
        st.session_state[f"enviado_{examen_id}"] = True
        status.update(label="✅ Evaluación completada", state="complete")

    # ── Mostrar resultado ──
    nivel = resultado.get("nivel_logro", "C")
    retro = resultado.get("retroalimentacion", "")

    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center; padding:1.5rem 0 1rem;">
        <div style="font-size:0.85rem; color:#9AA5B1; margin-bottom:0.4rem;">
            Tu nivel de logro
        </div>
        <span class="badge-{nivel}" style="font-size:1.5rem; padding:8px 28px;">
            {nivel}
        </span>
        <div style="font-size:0.85rem; color:#9AA5B1; margin-top:0.5rem;">
            {'Logro Destacado 🌟' if nivel=='AD' else 'Logro Esperado ✅' if nivel=='A'
             else 'En Proceso 📈' if nivel=='B' else 'En Inicio 💪'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 💬 Retroalimentación de tu docente IA")
    st.markdown(retro)

    if resultado.get("fortalezas"):
        st.markdown("**✅ Fortalezas:**")
        for f in resultado["fortalezas"]:
            st.markdown(f"- {f}")

    if resultado.get("sugerencias"):
        st.markdown("**📚 Sugerencias para mejorar:**")
        for s in resultado["sugerencias"]:
            st.markdown(f"- {s}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Audio ──
    st.markdown("#### 🔊 Escucha tu retroalimentación")
    with st.spinner("Generando audio..."):
        audio = texto_a_voz(retro, idioma_code)
        if audio:
            st.audio(audio, format="audio/mp3")
        else:
            st.caption("Audio no disponible en este momento.")


# ──────────────────────────────────────────────
# COMPONENTE COMPARTIDO
# ──────────────────────────────────────────────
def _header_institucional(titulo: str, subtitulo: str, modo: str = "docente"):
    icono_modo = "👨‍🏫" if modo == "docente" else "👨‍🎓"
    st.markdown(f"""
    <div class="header-institucional">
        <div style="font-size:2rem;">{icono_modo}</div>
        <div>
            <div style="font-size:1.3rem; font-weight:700; color:#1A202C;">{titulo}</div>
            <div style="font-size:0.82rem; color:#9AA5B1;">{subtitulo}</div>
        </div>
        <div style="margin-left:auto; text-align:right; line-height:1.5;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Flag_of_Peru.svg/24px-Flag_of_Peru.svg.png"
                 style="height:16px; vertical-align:middle; margin-right:4px;"/>
            <span style="font-size:0.75rem; color:#9AA5B1; font-weight:600;">MINEDU · Perú</span><br>
            <span style="font-size:0.65rem; color:#C8102E; font-weight:700;">© EdTech · Ingeniería Educativa</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
