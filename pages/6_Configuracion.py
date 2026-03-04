"""Configuración — edición de parámetros de calibración y modelo."""
import streamlit as st
import numpy as np
import os
from datetime import datetime
from core.calibration import DEFAULTS as CAL_DEF, MODELO_NAMES
from core.physics import PHYSICS_DEFAULTS as PHY_DEF

st.markdown("## ⚙️ Configuración")

# ── Parámetros de calibración ────────────────────────────────────────────────
st.markdown("### 📡 Modelos de calibración")
st.caption("Modifica los parámetros y pulsa **Guardar** para que surtan efecto en toda la app.")

cp = st.session_state["cal_params"]

with st.form("form_calibracion"):
    st.markdown("#### Certificado / Decaimiento")
    c1, c2 = st.columns(2)
    fecha_cert = c1.date_input("Fecha certificado",
                                value=cp["fecha_cert"].date()
                                if hasattr(cp["fecha_cert"], "date")
                                else cp["fecha_cert"])
    A0    = c2.number_input("Actividad inicial (TBq)", value=float(cp["A0_TBq"]),
                             min_value=0.1, step=0.1)
    c3, c4 = st.columns(2)
    tasa0 = c3.number_input("Tasa inicial (Gy/min)",
                             value=float(cp["tasa_inicial_Gy_min"]), step=0.01)
    k     = c4.number_input("Constante k (Gy·min⁻¹·TBq⁻¹)",
                             value=float(cp["k_Gy_min_TBq"]), step=0.001, format="%.4f")

    st.markdown("#### Display")
    tasa_disp = st.number_input("Tasa display (Gy/min)",
                                 value=float(cp["tasa_display_Gy_min"]), step=0.01)

    st.markdown("#### Calibración Aire (Radcal)")
    c5, c6 = st.columns(2)
    sl_aire = c5.number_input("Slope aire", value=float(cp["slope_aire"]),
                               step=0.0001, format="%.4f")
    ic_aire = c6.number_input("Intercept aire (Gy)", value=float(cp["intercept_aire"]),
                               step=0.0001, format="%.4f")

    st.markdown("#### Calibración Agua (PMMA)")
    c7, c8 = st.columns(2)
    sl_agua = c7.number_input("Slope agua", value=float(cp["slope_agua"]),
                               step=0.0001, format="%.4f")
    ic_agua = c8.number_input("Intercept agua (Gy)", value=float(cp["intercept_agua"]),
                               step=0.0001, format="%.4f")

    guardar_cal = st.form_submit_button("💾 Guardar parámetros de calibración",
                                         type="primary", use_container_width=True)

if guardar_cal:
    st.session_state["cal_params"].update({
        "fecha_cert":           datetime.combine(fecha_cert, datetime.min.time()),
        "A0_TBq":               A0,
        "tasa_inicial_Gy_min":  tasa0,
        "k_Gy_min_TBq":         k,
        "tasa_display_Gy_min":  tasa_disp,
        "slope_aire":           sl_aire,
        "intercept_aire":       ic_aire,
        "slope_agua":           sl_agua,
        "intercept_agua":       ic_agua,
    })
    st.success("✅ Parámetros de calibración guardados.")

st.markdown("---")

# ── Parámetros del modelo físico ─────────────────────────────────────────────
st.markdown("### 🔬 Modelo físico (avanzado)")
st.caption("Parámetros que controlan la simulación de la distribución espacial de dosis.")

pp = st.session_state["phys_params"]

with st.form("form_fisica"):
    cc1, cc2, cc3 = st.columns(3)
    R_s  = cc1.number_input("Radio fuente (cm)",     value=float(pp["R_source_cm"]),   step=0.1)
    H_s  = cc2.number_input("Altura fuente (cm)",    value=float(pp["H_source_cm"]),   step=0.1)
    D_s  = cc3.number_input("Distancia fuente (cm)", value=float(pp["D_source_cm"]),   step=0.1)
    cd1, cd2 = st.columns(2)
    atten_f  = cd1.number_input("Factor atenuación",  value=float(pp["attenuation_factor"]), step=0.01)
    build_f  = cd2.number_input("Factor buildup",     value=float(pp["buildup_factor"]),      step=0.01)
    brc      = cd1.number_input("Coef. buildup radial", value=float(pp["buildup_radial_coef"]), step=0.001, format="%.4f")
    ssc      = cd2.number_input("Coef. auto-blindaje",  value=float(pp["self_shielding_coef"]), step=0.00001, format="%.5f")

    guardar_fis = st.form_submit_button("💾 Guardar parámetros físicos",
                                         type="primary", use_container_width=True)

if guardar_fis:
    st.session_state["phys_params"].update({
        "R_source_cm": R_s, "H_source_cm": H_s, "D_source_cm": D_s,
        "attenuation_factor": atten_f, "buildup_factor": build_f,
        "buildup_radial_coef": brc, "self_shielding_coef": ssc,
    })
    # Limpiar caché de física para forzar recálculo
    from core.physics import calculate_dose_map
    calculate_dose_map.clear()
    st.success("✅ Parámetros físicos guardados. El mapa se recalculará.")

st.markdown("---")

# ── Cargar nuevos datos experimentales ───────────────────────────────────────
st.markdown("### 📂 Actualizar datos experimentales")
st.caption("Sube un nuevo fichero `.npz` con mapas de dosis experimentales o del fabricante.")

uploaded = st.file_uploader("Seleccionar fichero .npz", type=["npz"])
if uploaded is not None:
    dest = os.path.join(os.path.dirname(__file__), "..", "data", "mapas_REALES.npz")
    with open(dest, "wb") as f:
        f.write(uploaded.read())
    # Limpiar caché de validación
    st.cache_data.clear()
    st.success(f"✅ Fichero guardado como `data/mapas_REALES.npz` ({uploaded.size/1024:.1f} kB). "
               "Recarga la página de Validación.")

st.markdown("---")

# ── Restaurar valores por defecto ────────────────────────────────────────────
st.markdown("### 🔄 Restaurar valores por defecto")
col_a, col_b = st.columns(2)
if col_a.button("Restaurar calibración", use_container_width=True):
    from core.calibration import DEFAULTS
    st.session_state["cal_params"] = dict(DEFAULTS)
    st.success("Calibración restaurada a valores del notebook original.")
if col_b.button("Restaurar física", use_container_width=True):
    st.session_state["phys_params"] = dict(PHY_DEF)
    calculate_dose_map_fn = __import__("core.physics", fromlist=["calculate_dose_map"]).calculate_dose_map
    calculate_dose_map_fn.clear()
    st.success("Parámetros físicos restaurados.")
