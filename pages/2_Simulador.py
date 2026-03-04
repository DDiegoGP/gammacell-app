"""Página Simulador — mapa de dosis G(x,z) con Plotly."""
import streamlit as st
from core.auth import require_auth
require_auth()
import plotly.graph_objects as go
import numpy as np
from core.physics import calculate_dose_map, dose_stats, PHYSICS_DEFAULTS

st.markdown("## 📊 Simulador — Mapa de dosis G(x,z)")
st.caption("El mapa muestra la distribución de dosis relativa normalizada al centro del canister.")

# ── Controles en sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Parámetros del modelo")
    pp = st.session_state["phys_params"]

    R_source   = st.slider("Radio fuente (cm)",     0.5,  5.0, float(pp["R_source_cm"]),   0.1)
    H_source   = st.slider("Altura fuente (cm)",   14.0, 24.0, float(pp["H_source_cm"]),   0.2)
    D_source   = st.slider("Distancia fuente (cm)", 6.0, 12.0, float(pp["D_source_cm"]),   0.1)
    atten      = st.slider("Factor atenuación",     0.1,  1.0, float(pp["attenuation_factor"]), 0.05)
    buildup    = st.slider("Factor buildup",        1.0,  2.0, float(pp["buildup_factor"]),     0.05)

    st.markdown("---")
    nx = st.select_slider("Resolución X", options=[20, 30, 40, 60], value=int(pp["n_x_points"]))
    nz = st.select_slider("Resolución Z", options=[30, 40, 50, 70], value=int(pp["n_z_points"]))

    calcular = st.button("🔄 Calcular mapa", use_container_width=True, type="primary")

    if calcular:
        # Actualizar parámetros en session_state
        st.session_state["phys_params"].update({
            "R_source_cm": R_source, "H_source_cm": H_source,
            "D_source_cm": D_source, "attenuation_factor": atten,
            "buildup_factor": buildup, "n_x_points": nx, "n_z_points": nz,
        })

# ── Cálculo ──────────────────────────────────────────────────────────────────
pp = st.session_state["phys_params"]
with st.spinner("Calculando distribución de dosis…"):
    X, Z, G = calculate_dose_map(
        R_source_cm=float(pp["R_source_cm"]),
        H_source_cm=float(pp["H_source_cm"]),
        D_source_cm=float(pp["D_source_cm"]),
        attenuation_factor=float(pp["attenuation_factor"]),
        buildup_factor=float(pp["buildup_factor"]),
        buildup_radial_coef=float(pp["buildup_radial_coef"]),
        self_shielding_coef=float(pp["self_shielding_coef"]),
        mu_water=float(pp["mu_water"]),
        diameter_canister_cm=float(pp["diameter_canister_cm"]),
        H_canister_cm=float(pp["H_canister_cm"]),
        n_x_points=int(pp["n_x_points"]),
        n_z_points=int(pp["n_z_points"]),
        n_rotation_angles=int(pp["n_rotation_angles"]),
        n_source_height_points=int(pp["n_source_height_points"]),
    )

stats = dose_stats(G)

# ── Métricas rápidas ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("G mínimo",   f"{stats['min']:.4f}")
c2.metric("G máximo",   f"{stats['max']:.4f}")
c3.metric("G centro",   f"{stats['centro']:.4f}")
c4.metric("Uniformidad", f"{stats['uniformidad_pct']:.1f}%",
          help="Dmin / Dcentro × 100%")

st.markdown("---")

# ── Vista: heatmap o superficie 3D ───────────────────────────────────────────
tab_map, tab_3d = st.tabs(["🗺️ Mapa 2D", "🔵 Superficie 3D"])

with tab_map:
    fig2d = go.Figure()

    fig2d.add_trace(go.Heatmap(
        x=X[0], y=Z[:, 0], z=G,
        colorscale="Viridis",
        colorbar=dict(title="G(x,z)", tickformat=".3f"),
        zmin=G.min(), zmax=1.0,
        hovertemplate="x=%{x:.2f} cm<br>z=%{y:.2f} cm<br>G=%{z:.4f}<extra></extra>",
    ))

    # Contornos
    fig2d.add_trace(go.Contour(
        x=X[0], y=Z[:, 0], z=G,
        contours=dict(
            start=round(float(G.min()), 2),
            end=1.0,
            size=0.02,
            showlabels=True,
            labelfont=dict(color="white", size=10),
        ),
        line=dict(color="white", width=0.8),
        showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
    ))

    # Punto central
    fig2d.add_trace(go.Scatter(
        x=[pp["diameter_canister_cm"] / 2],
        y=[pp["H_canister_cm"] / 2],
        mode="markers",
        marker=dict(symbol="star", size=14, color="#FF5252"),
        name="Centro",
        hovertemplate="Centro<extra></extra>",
    ))

    fig2d.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Diámetro (cm)",
        yaxis_title="Altura (cm)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
    )
    st.plotly_chart(fig2d, use_container_width=True)

with tab_3d:
    fig3d = go.Figure(go.Surface(
        x=X, y=Z, z=G,
        colorscale="Viridis",
        colorbar=dict(title="G(x,z)"),
        hovertemplate="x=%{x:.2f}<br>z=%{y:.2f}<br>G=%{z:.4f}<extra></extra>",
    ))
    fig3d.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis_title="Diámetro (cm)",
            yaxis_title="Altura (cm)",
            zaxis_title="G(x,z)",
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
    )
    st.plotly_chart(fig3d, use_container_width=True)
