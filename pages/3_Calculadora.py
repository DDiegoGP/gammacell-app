"""Calculadora de tiempo de irradiación — dosis ↔ tiempo."""
import streamlit as st
from core.auth import require_auth
require_auth()
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from core.calibration import MODELO_NAMES, tiempo_para_dosis, tasa_modelo
from core.physics import calculate_dose_map, dose_stats

params = st.session_state["cal_params"]
pp     = st.session_state["phys_params"]
hoy    = datetime.now()

st.markdown("## ⏱️ Calculadora de irradiación")

# ── Layout principal ─────────────────────────────────────────────────────────
col_inp, col_res = st.columns([1, 1.6])

with col_inp:
    st.markdown("### Parámetros")
    modelo = st.selectbox("Modelo de calibración", MODELO_NAMES, index=3)
    dosis  = st.number_input("Dosis objetivo (Gy)", min_value=0.1, max_value=500.0,
                              value=35.0, step=0.5)
    st.markdown("---")
    st.markdown("**Calculadora inversa**")
    tiempo_inv = st.number_input("Tiempo disponible (min)", min_value=0.1,
                                  max_value=600.0, value=10.0, step=0.5)

# ── Cálculos ─────────────────────────────────────────────────────────────────
t_min, d_display = tiempo_para_dosis(dosis, modelo, params, hoy)
t_seg = t_min * 60
tasa  = tasa_modelo(modelo, params, hoy)

# Calculadora inversa
dosis_inv = tasa * tiempo_inv if modelo in (MODELO_NAMES[0], MODELO_NAMES[1]) else (
    params["slope_aire"] * params["tasa_display_Gy_min"] * tiempo_inv
    if modelo == MODELO_NAMES[2]
    else params["slope_agua"] * params["tasa_display_Gy_min"] * tiempo_inv
)

# Mapa de dosis espacial
with st.spinner("Cargando distribución espacial…"):
    X, Z, G = calculate_dose_map(
        **{k: float(v) if not isinstance(v, int) else int(v)
           for k, v in pp.items()
           if k in ["R_source_cm","H_source_cm","D_source_cm","attenuation_factor",
                    "buildup_factor","buildup_radial_coef","self_shielding_coef",
                    "mu_water","diameter_canister_cm","H_canister_cm",
                    "n_x_points","n_z_points","n_rotation_angles","n_source_height_points"]}
    )

stats  = dose_stats(G)
D_esp  = dosis * G
D_min  = float(D_esp.min())
D_max  = float(D_esp.max())
D_cent = float(D_esp[D_esp.shape[0]//2, D_esp.shape[1]//2])
unif   = D_min / D_cent * 100

with col_res:
    st.markdown("### Resultado")
    # Tarjeta de resultado principal
    mins_int = int(t_min)
    segs_int = int((t_min - mins_int) * 60)
    color_unif = "#66BB6A" if unif >= 90 else ("#FFA726" if unif >= 80 else "#EF5350")

    st.markdown(
        f"""
        <div style='background:#00ACC115; border:1px solid #00ACC155;
                    border-radius:14px; padding:1.5rem;'>
            <div style='font-size:0.85rem; color:#90A4AE;'>Tiempo de irradiación</div>
            <div style='font-size:2.8rem; font-weight:700; color:#00ACC1;'>
                {mins_int} min {segs_int:02d} s
            </div>
            <div style='font-size:0.9rem; color:#90A4AE;'>
                ({t_seg:.1f} s totales)
            </div>
            <hr style='border-color:#ffffff20; margin:0.8rem 0;'>
            <div style='display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;
                        font-size:0.9rem;'>
                <div><span style='color:#78909C;'>Dosis display:</span><br>
                     <b>{d_display:.2f} Gy</b></div>
                <div><span style='color:#78909C;'>Tasa ({modelo[:6]}…):</span><br>
                     <b>{tasa:.3f} Gy/min</b></div>
                <div><span style='color:#78909C;'>Dosis mínima:</span><br>
                     <b>{D_min:.2f} Gy</b></div>
                <div><span style='color:#78909C;'>Dosis máxima:</span><br>
                     <b>{D_max:.2f} Gy</b></div>
                <div><span style='color:#78909C;'>Uniformidad:</span><br>
                     <b style='color:{color_unif};'>{unif:.1f}%</b></div>
                <div><span style='color:#78909C;'>Dosis centro:</span><br>
                     <b>{D_cent:.2f} Gy</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Calculadora inversa
    st.info(f"⏪ Con **{tiempo_inv:.1f} min** disponibles → **{dosis_inv:.2f} Gy** en el centro")

# ── Tabla de dosis comunes ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Tabla de dosis habituales")

dosis_lista = [5, 10, 15, 20, 25, 30, 35, 40, 50, 75, 100]
rows = []
for d in dosis_lista:
    t, dd = tiempo_para_dosis(d, modelo, params, hoy)
    d_esp = d * G
    rows.append({
        "Dosis obj. (Gy)": d,
        "Tiempo (min)":    round(t, 2),
        "Tiempo (s)":      round(t * 60, 1),
        "Display (Gy)":    round(dd, 2),
        "D mín (Gy)":      round(float(d_esp.min()), 2),
        "D máx (Gy)":      round(float(d_esp.max()), 2),
        "Uniformidad (%)": round(float(d_esp.min()) / float(d_esp[d_esp.shape[0]//2,
                                  d_esp.shape[1]//2]) * 100, 1),
    })

df_tabla = pd.DataFrame(rows)
st.dataframe(df_tabla, use_container_width=True, hide_index=True)

# ── Mapa de dosis espacial ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗺️ Distribución espacial de dosis")

fig = go.Figure(go.Heatmap(
    x=X[0], y=Z[:, 0], z=D_esp,
    colorscale="RdYlGn",
    colorbar=dict(title="Dosis (Gy)", tickformat=".1f"),
    hovertemplate="x=%{x:.2f} cm<br>z=%{y:.2f} cm<br>Dosis=%{z:.2f} Gy<extra></extra>",
))
fig.add_trace(go.Contour(
    x=X[0], y=Z[:, 0], z=D_esp,
    contours=dict(start=D_min, end=D_max,
                  size=(D_max - D_min) / 8,
                  showlabels=True,
                  labelfont=dict(color="black", size=10)),
    line=dict(color="black", width=0.8),
    showscale=False,
    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
))
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Diámetro (cm)",
    yaxis_title="Altura (cm)",
    margin=dict(l=0, r=0, t=10, b=0),
    height=420,
)
st.plotly_chart(fig, use_container_width=True)

# ── Botón registrar en historial ─────────────────────────────────────────────
st.markdown("---")
with st.expander("📝 Registrar esta irradiación en el historial"):
    with st.form("form_registro"):
        operador = st.text_input("Operador")
        muestra  = st.text_input("Identificador de muestra")
        notas    = st.text_area("Observaciones", height=80)
        ok = st.form_submit_button("Guardar en historial", type="primary")
        if ok:
            registro = {
                "Fecha":          hoy.strftime("%Y-%m-%d %H:%M"),
                "Operador":       operador,
                "Muestra":        muestra,
                "Dosis obj. (Gy)": dosis,
                "Modelo":         modelo[:30],
                "Tiempo (min)":   round(t_min, 3),
                "Uniformidad (%)": round(unif, 1),
                "Observaciones":  notas,
            }
            st.session_state["historial"].append(registro)
            st.success("✅ Registrado correctamente. Visita la página Historial.")
