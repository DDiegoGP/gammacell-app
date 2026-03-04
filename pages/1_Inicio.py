"""Página de inicio — estado del equipo y curva de decaimiento."""
import streamlit as st
from core.auth import require_auth
require_auth()
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from core.calibration import MODELO_NAMES, tasa_modelo, decay_curve

params = st.session_state["cal_params"]
hoy = datetime.now()

# ── Cabecera ────────────────────────────────────────────────────────────────
st.markdown("## 🏠 Estado del equipo")
st.caption(f"Fecha actual: {hoy.strftime('%d/%m/%Y')}")

# ── Tarjetas de estado ───────────────────────────────────────────────────────
tasas = {
    "Teórico":  tasa_modelo(MODELO_NAMES[0], params, hoy),
    "Display":  tasa_modelo(MODELO_NAMES[1], params, hoy),
    "Aire":     tasa_modelo(MODELO_NAMES[2], params, hoy),
    "Agua ★":   tasa_modelo(MODELO_NAMES[3], params, hoy),
}

cols = st.columns(4)
colores = ["#00ACC1", "#42A5F5", "#66BB6A", "#FFA726"]
iconos  = ["🔬", "🖥️", "💨", "💧"]
for col, (nombre, tasa), color, icono in zip(cols, tasas.items(), colores, iconos):
    col.markdown(
        f"""
        <div style='background:{color}18; border:1px solid {color}55;
                    border-radius:12px; padding:1rem; text-align:center;'>
            <div style='font-size:1.8rem;'>{icono}</div>
            <div style='font-size:0.85rem; color:#90A4AE;'>{nombre}</div>
            <div style='font-size:1.6rem; font-weight:700; color:{color};'>
                {tasa:.3f}
            </div>
            <div style='font-size:0.75rem; color:#78909C;'>Gy/min</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Curva de decaimiento ─────────────────────────────────────────────────────
st.markdown("### 📉 Decaimiento de la fuente Cs-137")

col_left, col_right = st.columns([3, 1])
with col_right:
    years_ahead = st.slider("Años a proyectar", 5, 30, 15)

fechas, tasas_vec, t0_years = decay_curve(params, years_ahead)
fecha_cert = params["fecha_cert"]

fig = go.Figure()

# Línea de decaimiento
fig.add_trace(go.Scatter(
    x=fechas, y=tasas_vec,
    mode="lines",
    line=dict(color="#00ACC1", width=2.5),
    name="Tasa teórica",
    hovertemplate="%{x|%Y-%m-%d}: %{y:.3f} Gy/min<extra></extra>",
))

# Línea vertical "hoy"
fig.add_vline(
    x=hoy.timestamp() * 1000,
    line=dict(color="#FFA726", dash="dash", width=1.5),
    annotation_text=f"Hoy: {tasa_modelo(MODELO_NAMES[0], params, hoy):.3f} Gy/min",
    annotation_font_color="#FFA726",
)

# Zona de utilidad (> 1 Gy/min)
fig.add_hrect(y0=0, y1=1.0, fillcolor="rgba(239,83,80,0.12)", line_width=0,
              annotation_text="Tasa mínima útil (1 Gy/min)",
              annotation_position="bottom left",
              annotation_font_color="#EF5350")

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis_title="Año",
    yaxis_title="Tasa de dosis (Gy/min)",
    legend=dict(orientation="h", y=1.05),
    height=360,
)
with col_left:
    st.plotly_chart(fig, use_container_width=True)

# ── Ficha técnica del equipo ─────────────────────────────────────────────────
st.markdown("### 📋 Ficha técnica")
years_elapsed = (hoy - fecha_cert).days / 365.25
A_actual = params["A0_TBq"] * np.exp(-np.log(2) / params["half_life_years"] * years_elapsed)

data = {
    "Parámetro": [
        "Modelo", "Isótopo", "Energía fotón",
        "Actividad inicial (certificado)", "Fecha certificado",
        "Actividad actual (calculada)", "Vida media",
        "Radio canister", "Altura canister", "μ agua",
    ],
    "Valor": [
        "Gammacell Elite 1000 (ex-Gammacell 3000 Elan)",
        "Cs-137", "661.7 keV",
        f"{params['A0_TBq']:.1f} TBq ({params['A0_TBq']*27.027:.0f} Ci)",
        fecha_cert.strftime("%d/%m/%Y"),
        f"{A_actual:.2f} TBq ({A_actual*27.027:.0f} Ci)",
        "30.17 años",
        "6.2 cm", "19.4 cm", "0.086 cm⁻¹",
    ],
}

import pandas as pd
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True, hide_index=True,
             column_config={"Parámetro": st.column_config.TextColumn(width="medium"),
                            "Valor": st.column_config.TextColumn(width="large")})
