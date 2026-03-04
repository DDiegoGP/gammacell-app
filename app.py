"""
Gammacell Elite 1000 — Simulador de dosis
Instituto de Radioquímica · UCM
"""
import streamlit as st
from core.auth import check_auth, logout

st.set_page_config(
    page_title="Gammacell Elite 1000",
    page_icon="☢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inicializar parámetros de calibración en session_state ──────────────────
from core.calibration import DEFAULTS as CAL_DEFAULTS
if "cal_params" not in st.session_state:
    st.session_state["cal_params"] = dict(CAL_DEFAULTS)

from core.physics import PHYSICS_DEFAULTS
if "phys_params" not in st.session_state:
    st.session_state["phys_params"] = dict(PHYSICS_DEFAULTS)

if "historial" not in st.session_state:
    st.session_state["historial"] = []

# ── Autenticación ───────────────────────────────────────────────────────────
if not check_auth():
    st.stop()

# ── Sidebar: navegación + logout ────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding-bottom: 1rem;'>
            <span style='font-size:2rem;'>☢️</span><br>
            <span style='font-size:1.1rem; font-weight:700; color:#00ACC1;'>
                Gammacell Elite 1000
            </span><br>
            <span style='font-size:0.8rem; color:#78909C;'>IRC · UCM</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

# ── Navegación multi-página ─────────────────────────────────────────────────
pages = [
    st.Page("pages/1_Inicio.py",        title="Inicio",        icon="🏠"),
    st.Page("pages/2_Simulador.py",     title="Simulador",     icon="📊"),
    st.Page("pages/3_Calculadora.py",   title="Calculadora",   icon="⏱️"),
    st.Page("pages/4_Validacion.py",    title="Validación",    icon="📈"),
    st.Page("pages/5_Historial.py",     title="Historial",     icon="📋"),
    st.Page("pages/6_Configuracion.py", title="Configuración", icon="⚙️"),
]

pg = st.navigation(pages, position="sidebar")

with st.sidebar:
    st.divider()
    if st.button("🔒 Cerrar sesión", use_container_width=True):
        logout()

pg.run()
