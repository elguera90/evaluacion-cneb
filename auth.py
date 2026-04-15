"""
auth.py — Autenticación segura para docentes
"""

import streamlit as st
import hashlib
import time
from config import get_admin_password, APP_TITLE, APP_SUBTITLE, APP_ORG, APP_COPYRIGHT

SESSION_TIMEOUT_SECONDS = 3600


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def is_authenticated() -> bool:
    if not st.session_state.get("authenticated", False):
        return False
    if time.time() - st.session_state.get("login_time", 0) > SESSION_TIMEOUT_SECONDS:
        _logout()
        return False
    return True


def _logout():
    st.session_state["authenticated"] = False
    st.session_state["login_time"] = 0
    st.session_state["docente_nombre"] = ""


def render_login():
    col_l, col_c, col_r = st.columns([1, 1.6, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # ── Cabecera institucional ──
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:3rem; margin-bottom:0.6rem;">🎓</div>
            <div style="font-size:1.2rem; font-weight:800; color:#1A202C;
                        font-family:'Sora',sans-serif; line-height:1.3; margin-bottom:0.3rem;">
                {APP_TITLE}
            </div>
            <div style="font-size:0.95rem; font-weight:600; color:#C8102E; margin-bottom:0.2rem;">
                {APP_SUBTITLE}
            </div>
            <div style="font-size:0.82rem; color:#9AA5B1;">
                {APP_ORG}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Formulario ──
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔐 Acceso Docente")

        nombre = st.text_input("Nombre completo", placeholder="Prof. María García",
                               key="login_nombre")
        password = st.text_input("Contraseña institucional", type="password",
                                 placeholder="••••••••", key="login_password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ingresar", use_container_width=True):
                _handle_login(nombre, password)
        with col2:
            st.markdown(
                '<div style="text-align:center;padding-top:0.6rem;">'
                '<a href="https://www.minedu.gob.pe" target="_blank" '
                'style="color:#9AA5B1;font-size:0.8rem;text-decoration:none;">¿Necesitas ayuda?</a></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Copyright ──
        st.markdown(f"""
        <p style="text-align:center; color:#9AA5B1; font-size:0.76rem; margin-top:2rem; line-height:1.6;">
            Sistema de uso exclusivo para docentes registrados MINEDU<br>
            v{__import__('config').APP_VERSION} · Piloto institucional 2025<br>
            <strong style="color:#C8102E;">{APP_COPYRIGHT}</strong>
        </p>
        """, unsafe_allow_html=True)


def _handle_login(nombre: str, password: str):
    if not nombre.strip():
        st.error("⚠️ Ingresa tu nombre para continuar.")
        return
    if _hash(password) == _hash(get_admin_password()):
        st.session_state["authenticated"] = True
        st.session_state["login_time"] = time.time()
        st.session_state["docente_nombre"] = nombre.strip()
        st.rerun()
    else:
        st.error("❌ Contraseña incorrecta.")


def render_session_info():
    nombre   = st.session_state.get("docente_nombre", "Docente")
    restante = SESSION_TIMEOUT_SECONDS - int(time.time() - st.session_state.get("login_time", time.time()))
    minutos  = max(0, restante // 60)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="font-size:0.82rem; color:rgba(255,255,255,0.85); line-height:1.6;">
        👤 <strong>{nombre}</strong><br>
        ⏱️ Sesión expira en {minutos} min
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
        _logout()
        st.rerun()

    # Copyright en sidebar
    st.sidebar.markdown(f"""
    <div style="position:absolute; bottom:1rem; left:0; right:0; text-align:center;
                font-size:0.68rem; color:rgba(255,255,255,0.5); padding:0 1rem;">
        {__import__('config').APP_COPYRIGHT}
    </div>
    """, unsafe_allow_html=True)
