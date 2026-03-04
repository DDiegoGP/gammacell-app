"""Historial de irradiaciones — registro de sesión con exportación."""
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

st.markdown("## 📋 Historial de irradiaciones")
st.caption(
    "⚠️ El historial se almacena en la sesión actual. "
    "**Descarga el registro** antes de cerrar el navegador para no perderlo."
)

historial = st.session_state.get("historial", [])

# ── Añadir entrada manual ────────────────────────────────────────────────────
with st.expander("➕ Añadir entrada manual"):
    from core.calibration import MODELO_NAMES
    with st.form("form_hist_manual"):
        c1, c2 = st.columns(2)
        fecha     = c1.date_input("Fecha", value=datetime.now().date())
        hora      = c2.time_input("Hora",  value=datetime.now().time())
        operador  = c1.text_input("Operador")
        muestra   = c2.text_input("Muestra / ID")
        dosis     = c1.number_input("Dosis (Gy)", min_value=0.0, step=0.5, value=0.0)
        t_min     = c2.number_input("Tiempo (min)", min_value=0.0, step=0.1, value=0.0)
        modelo    = st.selectbox("Modelo", MODELO_NAMES, index=3)
        unif      = st.number_input("Uniformidad (%)", min_value=0.0, max_value=100.0,
                                     step=0.1, value=0.0)
        notas     = st.text_area("Observaciones", height=70)
        ok = st.form_submit_button("Añadir", type="primary")
        if ok:
            st.session_state["historial"].append({
                "Fecha":           f"{fecha} {hora.strftime('%H:%M')}",
                "Operador":        operador,
                "Muestra":         muestra,
                "Dosis obj. (Gy)": dosis,
                "Modelo":          modelo[:30],
                "Tiempo (min)":    round(t_min, 3),
                "Uniformidad (%)": round(unif, 1),
                "Observaciones":   notas,
            })
            st.success("Entrada añadida.")
            st.rerun()

st.markdown("---")

if not historial:
    st.info("No hay registros todavía. Usa la **Calculadora** para registrar irradiaciones.")
    st.stop()

df = pd.DataFrame(historial)

# ── Tabla editable ───────────────────────────────────────────────────────────
st.markdown(f"### {len(df)} irradiaciones registradas")
df_edit = st.data_editor(df, use_container_width=True, num_rows="dynamic",
                          key="historial_editor")

# Sync edits back
if st.button("💾 Guardar cambios de la tabla"):
    st.session_state["historial"] = df_edit.to_dict("records")
    st.success("Cambios guardados.")

# ── Exportar ─────────────────────────────────────────────────────────────────
st.markdown("---")
col_csv, col_xls = st.columns(2)

csv_bytes = df.to_csv(index=False).encode("utf-8")
col_csv.download_button(
    "⬇️ Descargar CSV",
    data=csv_bytes,
    file_name=f"historial_gammacell_{datetime.now():%Y%m%d}.csv",
    mime="text/csv",
    use_container_width=True,
)

buf = BytesIO()
df.to_excel(buf, index=False, engine="openpyxl")
col_xls.download_button(
    "⬇️ Descargar Excel",
    data=buf.getvalue(),
    file_name=f"historial_gammacell_{datetime.now():%Y%m%d}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

# ── Estadísticas rápidas ─────────────────────────────────────────────────────
if "Dosis obj. (Gy)" in df.columns and df["Dosis obj. (Gy)"].notna().any():
    st.markdown("---")
    st.markdown("### 📊 Estadísticas del historial")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total irradiaciones", len(df))
    c2.metric("Dosis media (Gy)", f"{df['Dosis obj. (Gy)'].mean():.1f}")
    c3.metric("Tiempo total (min)", f"{df['Tiempo (min)'].sum():.1f}")

    fig = px.bar(df.reset_index(), x=df.index, y="Dosis obj. (Gy)",
                 color="Modelo" if "Modelo" in df.columns else None,
                 labels={"index": "Irradiación #"},
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 template="plotly_dark")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)
