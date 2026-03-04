"""Autenticación simple con credenciales almacenadas en st.secrets."""
import hmac
import streamlit as st


def _verify(username: str, password: str) -> bool:
    try:
        expected_user = st.secrets["auth"]["username"]
        expected_pass = st.secrets["auth"]["password"]
    except Exception:
        st.error("⚠️ Secrets no configurados. "
                 "En local: revisa `.streamlit/secrets.toml`. "
                 "En Streamlit Cloud: configura los secrets en el dashboard.")
        return False
    user_ok = hmac.compare_digest(username.strip(), expected_user.strip())
    pass_ok = hmac.compare_digest(password, expected_pass)
    return user_ok and pass_ok


def check_auth() -> bool:
    """Devuelve True si el usuario está autenticado; si no, muestra el login."""
    if st.session_state.get("authenticated"):
        return True

    _show_login()
    return False


def require_auth():
    """Llamar al inicio de cada página. Redirige al login si no hay sesión."""
    if not st.session_state.get("authenticated"):
        st.switch_page("app.py")
        st.stop()


def logout():
    st.session_state["authenticated"] = False
    st.session_state.pop("auth_user", None)
    st.rerun()


def _show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align:center; padding: 2rem 0 1rem 0;'>
                <h1 style='font-size:2.2rem; color:#00ACC1;'>☢️ Gammacell Elite 1000</h1>
                <p style='color:#90A4AE; font-size:1rem;'>Instituto de Radioquímica · UCM</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuario", placeholder="irc")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Acceder", use_container_width=True)

        if submitted:
            if _verify(username, password):
                st.session_state["authenticated"] = True
                st.session_state["auth_user"] = username
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
