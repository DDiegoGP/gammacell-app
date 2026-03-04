"""
Modelos de calibración del Gammacell Elite 1000.
Todos los parámetros por defecto son los del notebook original.
"""
from datetime import datetime
import numpy as np

# ─────────────────────────────────────────────
# Parámetros por defecto (coinciden con el notebook)
# ─────────────────────────────────────────────
DEFAULTS = {
    # Certificado
    "fecha_cert": datetime(2006, 5, 15),
    "A0_TBq": 50.3,
    "tasa_inicial_Gy_min": 8.0,
    "k_Gy_min_TBq": 0.158,
    "half_life_years": 30.17,
    # Display
    "tasa_display_Gy_min": 5.36,
    # Calibración aire  (Radcal 10×5-180)
    "slope_aire": 1.2618,
    "intercept_aire": 0.3304,
    # Calibración agua  (fantoma PMMA Ø10×20 cm, 5 cm profundidad)
    "slope_agua": 1.046,
    "intercept_agua": 0.235,
}

MODELO_NAMES = [
    "Teórico (certificado + decaimiento)",
    "Display (lectura directa equipo)",
    "Calibración Aire (cámara Radcal)",
    "Calibración Agua (fantoma PMMA) ★",
]

LAMBDA = np.log(2) / DEFAULTS["half_life_years"]  # año⁻¹


def tasa_teorica(params: dict, fecha_ref: datetime | None = None) -> float:
    """Tasa de dosis teórica en Gy/min según decaimiento Cs-137."""
    if fecha_ref is None:
        fecha_ref = datetime.now()
    years = (fecha_ref - params["fecha_cert"]).days / 365.25
    return params["tasa_inicial_Gy_min"] * np.exp(-LAMBDA * years)


def tasa_modelo(modelo: str, params: dict, fecha_ref: datetime | None = None) -> float:
    """Devuelve la tasa de dosis en Gy/min para el modelo seleccionado."""
    if modelo == MODELO_NAMES[0]:
        return tasa_teorica(params, fecha_ref)
    elif modelo == MODELO_NAMES[1]:
        return params["tasa_display_Gy_min"]
    elif modelo == MODELO_NAMES[2]:
        return params["slope_aire"] * params["tasa_display_Gy_min"]
    else:  # agua
        return params["slope_agua"] * params["tasa_display_Gy_min"]


def tiempo_para_dosis(dosis_Gy: float, modelo: str, params: dict,
                      fecha_ref: datetime | None = None) -> tuple[float, float]:
    """
    Calcula el tiempo de irradiación.
    Devuelve (tiempo_min, dosis_display_Gy).
    """
    if modelo in (MODELO_NAMES[0], MODELO_NAMES[1]):
        t_min = dosis_Gy / tasa_modelo(modelo, params, fecha_ref)
        d_display = dosis_Gy
    elif modelo == MODELO_NAMES[2]:
        d_display = (dosis_Gy - params["intercept_aire"]) / params["slope_aire"]
        t_min = d_display / params["tasa_display_Gy_min"]
    else:  # agua
        d_display = (dosis_Gy - params["intercept_agua"]) / params["slope_agua"]
        t_min = d_display / params["tasa_display_Gy_min"]
    return t_min, d_display


def decay_curve(params: dict, years_ahead: int = 20) -> tuple:
    """Genera vectores (fechas, tasas) para la curva de decaimiento."""
    fecha_cert = params["fecha_cert"]
    hoy = datetime.now()
    t0_years = (hoy - fecha_cert).days / 365.25
    t_vec = np.linspace(0, t0_years + years_ahead, 400)
    tasa_vec = params["tasa_inicial_Gy_min"] * np.exp(-LAMBDA * t_vec)
    fechas = [fecha_cert.replace(year=fecha_cert.year + int(t)) for t in t_vec]
    return fechas, tasa_vec, t0_years
