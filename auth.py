"""
auth.py — Autenticación segura para docentes
Sistema de sesión con hash SHA-256 y timeout automático
"""

import streamlit as st
import hashlib
import time
from config import get_admin_password

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
SESSION_TIMEOUT_SECONDS = 3600  # 1 hora


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def is_authenticated() -> bool:
    """Verifica si el docente tiene sesión activa y no expirada."""
    if not st.session_state.get("authenticated", False):
        return False
    login_time = st.session_state.get("login_time", 0)
    if time.time() - login_time > SESSION_TIMEOUT_SECONDS:
        _logout()
        return False
    return True


def _logout():
    st.session_state["authenticated"] = False
    st.session_state["login_time"] = 0
    st.session_state["docente_nombre"] = ""


def render_login():
    """Renderiza el formulario de acceso docente."""
    col_l, col_c, col_r = st.columns([1, 1.8, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Logo institucional
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:3.5rem;">🎓</div>
            <h1 style="font-family:'Sora',sans-serif; font-size:1.5rem; color:#1A202C; margin:0.5rem 0 0.2rem;">
                Sistema IA CNEB
            </h1>
            <p style="color:#9AA5B1; font-size:0.9rem; margin:0;">
                Ministerio de Educación · Perú
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 🔐 Acceso Docente")

            nombre = st.text_input(
                "Nombre completo",
                placeholder="Prof. María García",
                key="login_nombre"
            )
            password = st.text_input(
                "Contraseña institucional",
                type="password",
                placeholder="••••••••",
                key="login_password"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ingresar", use_container_width=True):
                    _handle_login(nombre, password)
            with col2:
                st.markdown(
                    '<div style="text-align:center;padding-top:0.6rem;">'
                    '<a href="https://www.minedu.gob.pe" target="_blank" '
                    'style="color:#9AA5B1;font-size:0.8rem;">¿Necesitas ayuda?</a></div>',
                    unsafe_allow_html=True
                )

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <p style="text-align:center; color:#9AA5B1; font-size:0.78rem; margin-top:2rem;">
            Sistema de uso exclusivo para docentes registrados MINEDU<br>
            v2.0.0 · Piloto institucional 2025
        </p>
        """, unsafe_allow_html=True)


def _handle_login(nombre: str, password: str):
    if not nombre.strip():
        st.error("⚠️ Ingresa tu nombre para continuar.")
        return

    admin_hash = _hash_password(get_admin_password())
    if _hash_password(password) == admin_hash:
        st.session_state["authenticated"] = True
        st.session_state["login_time"] = time.time()
        st.session_state["docente_nombre"] = nombre.strip()
        st.rerun()
    else:
        st.error("❌ Contraseña incorrecta. Verifica tus credenciales.")


def render_session_info():
    """Muestra info de sesión y botón de cierre en la barra lateral."""
    nombre = st.session_state.get("docente_nombre", "Docente")
    login_time = st.session_state.get("login_time", time.time())
    restante = SESSION_TIMEOUT_SECONDS - int(time.time() - login_time)
    minutos = restante // 60

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="font-size:0.82rem; color:rgba(255,255,255,0.8);">
        👤 <strong>{nombre}</strong><br>
        ⏱️ Sesión expira en {minutos} min
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
        _logout()
        st.rerun()
