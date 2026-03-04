"""Página de validación — comparación modelo vs. datos experimentales."""
import streamlit as st
from core.auth import require_auth
require_auth()
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.stats import pearsonr
import os
from core.physics import calculate_dose_map

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mapas_REALES.npz")

st.markdown("## 📈 Validación del modelo")
st.caption("Comparación entre el modelo teórico y los mapas del fabricante / medidas experimentales.")

# ── Cargar datos ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_experimental(path: str):
    data = np.load(path, allow_pickle=True)
    return dict(data)

try:
    raw = load_experimental(DATA_PATH)
except FileNotFoundError:
    st.warning("⚠️ Fichero `data/mapas_REALES.npz` no encontrado. "
               "Cárgalo desde la página Configuración.")
    st.stop()

keys = list(raw.keys())
st.info(f"Datos cargados. Claves disponibles: `{'`, `'.join(keys)}`")

# ── Calcular mapa teórico ────────────────────────────────────────────────────
pp = st.session_state["phys_params"]
with st.spinner("Calculando mapa teórico…"):
    X, Z, G_model = calculate_dose_map(
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

x_model = X[0]
z_model = Z[:, 0]

# ── Intentar leer mapas de referencia ────────────────────────────────────────
# Intentar nombres comunes usados en el notebook
def _try_key(d, *names):
    for n in names:
        if n in d:
            return d[n]
    return None

x_ref = _try_key(raw, "x_fab", "x", "X")
y_ref = _try_key(raw, "y_fab", "y", "Y", "z_fab", "z")
G_fab = _try_key(raw, "G_fab", "G_fabricante", "fabricante", "fab")
G_exp = _try_key(raw, "G_exp", "G_experimental", "experimental", "exp")

if x_ref is None or y_ref is None or G_fab is None:
    st.error("No se encontraron las claves esperadas en el fichero .npz. "
             "Claves disponibles: " + str(keys))
    st.stop()

x_ref = np.asarray(x_ref, dtype=float)
y_ref = np.asarray(y_ref, dtype=float)
G_fab = np.asarray(G_fab, dtype=float)

# Interpolar modelo en la malla de referencia
interp = RegularGridInterpolator(
    (z_model, x_model), G_model, method="linear",
    bounds_error=False, fill_value=np.nan,
)
yy, xx = np.meshgrid(y_ref, x_ref, indexing="ij")
pts    = np.column_stack([yy.ravel(), xx.ravel()])
G_mod_i = interp(pts).reshape(yy.shape)

# ── Métricas ─────────────────────────────────────────────────────────────────
mask = ~np.isnan(G_fab) & ~np.isnan(G_mod_i)
diff = G_mod_i[mask] - G_fab[mask]
rmse = float(np.sqrt(np.mean(diff**2)))
mae  = float(np.mean(np.abs(diff)))
bias = float(np.mean(diff))
ss_tot = float(np.sum((G_fab[mask] - G_fab[mask].mean())**2))
ss_res = float(np.sum(diff**2))
r2     = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
r_p, p_val = pearsonr(G_fab[mask], G_mod_i[mask])

semaforo = "🟢 EXCELENTE" if rmse < 0.02 else ("🟡 BUENO" if rmse < 0.05 else "🔴 MEJORABLE")

col1, col2, col3, col4 = st.columns(4)
col1.metric("RMSE", f"{rmse:.4f}", help="Raíz del error cuadrático medio")
col2.metric("MAE",  f"{mae:.4f}",  help="Error absoluto medio")
col3.metric("R²",   f"{r2:.4f}",   help="Coeficiente de determinación")
col4.metric("Pearson r", f"{r_p:.4f}", help=f"p = {p_val:.2e}")

st.markdown(f"**Calidad del ajuste:** {semaforo}  |  Sesgo: {bias:+.4f}")
st.markdown("---")

# ── Gráficas ─────────────────────────────────────────────────────────────────
fig = make_subplots(
    rows=1, cols=3,
    subplot_titles=["Modelo teórico", "Datos fabricante", "Residuos (Mod − Fab)"],
    horizontal_spacing=0.06,
)

cmin = min(float(G_mod_i[mask].min()), float(G_fab[mask].min()))
cmax = max(float(G_mod_i[mask].max()), float(G_fab[mask].max()))

common_hm = dict(colorscale="Viridis", zmin=cmin, zmax=cmax, showscale=False)

fig.add_trace(go.Heatmap(x=x_ref, y=y_ref, z=G_mod_i,
              colorbar=dict(title="G"), **common_hm), row=1, col=1)
fig.add_trace(go.Heatmap(x=x_ref, y=y_ref, z=G_fab,
              colorbar=dict(title="G"), **common_hm), row=1, col=2)

rmax = float(np.nanmax(np.abs(diff)))
fig.add_trace(go.Heatmap(
    x=x_ref, y=y_ref,
    z=(G_mod_i - G_fab),
    colorscale="RdBu", zmin=-rmax, zmax=rmax,
    colorbar=dict(title="ΔG", x=1.01),
), row=1, col=3)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=440,
    margin=dict(l=0, r=60, t=40, b=0),
)
for i in range(1, 4):
    fig.update_xaxes(title_text="x (cm)", row=1, col=i)
    fig.update_yaxes(title_text="z (cm)", row=1, col=i)

st.plotly_chart(fig, use_container_width=True)

# ── Histograma de residuos ────────────────────────────────────────────────────
st.markdown("### Distribución de residuos")
fig_hist = go.Figure(go.Histogram(
    x=diff, nbinsx=40,
    marker_color="#00ACC1",
    opacity=0.8,
    name="Residuos",
))
fig_hist.add_vline(x=0, line=dict(color="#FFA726", dash="dash"))
fig_hist.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="G_modelo − G_fabricante",
    yaxis_title="Frecuencia",
    height=280,
    margin=dict(l=0, r=0, t=10, b=0),
)
st.plotly_chart(fig_hist, use_container_width=True)

# Datos experimentales (si existen)
if G_exp is not None:
    st.markdown("---")
    st.markdown("### Comparación adicional con datos experimentales")
    G_exp = np.asarray(G_exp, dtype=float)
    mask2 = ~np.isnan(G_exp) & ~np.isnan(G_mod_i)
    if mask2.any():
        diff2 = G_mod_i[mask2] - G_exp[mask2]
        rmse2 = float(np.sqrt(np.mean(diff2**2)))
        st.metric("RMSE vs. Experimental", f"{rmse2:.4f}")
