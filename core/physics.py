"""
Motor de cálculo de distribución de dosis para el Gammacell Elite 1000.
Versión vectorizada (numpy) del algoritmo original del notebook.
Se usa @st.cache_data para evitar recalcular con los mismos parámetros.
"""
import numpy as np
import streamlit as st


# ─────────────────────────────────────────────
# Parámetros por defecto del modelo geométrico
# ─────────────────────────────────────────────
PHYSICS_DEFAULTS = {
    # Geometría fuente
    "R_source_cm": 2.0,
    "H_source_cm": 16.4,
    "D_source_cm": 9.0,
    # Física
    "attenuation_factor": 0.5,
    "buildup_factor": 1.2,
    "buildup_radial_coef": 0.03,
    "self_shielding_coef": 0.0001,
    "mu_water": 0.086,
    # Canister (fijo)
    "diameter_canister_cm": 6.0,
    "H_canister_cm": 16.4,
    # Resolución
    "n_x_points": 40,
    "n_z_points": 50,
    "n_rotation_angles": 36,
    "n_source_height_points": 20,
}


@st.cache_data(show_spinner=False)
def calculate_dose_map(
    R_source_cm: float = 2.0,
    H_source_cm: float = 16.4,
    D_source_cm: float = 9.0,
    attenuation_factor: float = 0.5,
    buildup_factor: float = 1.2,
    buildup_radial_coef: float = 0.03,
    self_shielding_coef: float = 0.0001,
    mu_water: float = 0.086,
    diameter_canister_cm: float = 6.0,
    H_canister_cm: float = 16.4,
    n_x_points: int = 40,
    n_z_points: int = 50,
    n_rotation_angles: int = 36,
    n_source_height_points: int = 20,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula el mapa de dosis normalizado G(x,z).

    Devuelve (X_grid, Z_grid, G_xz) donde G_xz está normalizado
    al valor del centro del canister.

    Versión vectorizada: opera sobre todo el grid a la vez para cada
    ángulo θ y altura z_s de la fuente → muy superior en velocidad
    a la versión con bucles del notebook.
    """
    x_pts = np.linspace(0, diameter_canister_cm, n_x_points)
    z_pts = np.linspace(0, H_canister_cm, n_z_points)
    X_grid, Z_grid = np.meshgrid(x_pts, z_pts)

    # Coordenadas centradas
    x_c = X_grid - diameter_canister_cm / 2.0   # (nz, nx)
    z_c = Z_grid - H_canister_cm / 2.0
    r   = np.abs(x_c)

    # Alturas de la fuente
    z_source = np.linspace(-H_source_cm / 2, H_source_cm / 2, n_source_height_points)
    angles   = np.linspace(0, 2 * np.pi, n_rotation_angles, endpoint=False)

    dose_grid = np.zeros((n_z_points, n_x_points))

    for theta in angles:
        x_p = r * np.cos(theta)
        y_p = r * np.sin(theta)
        x_s = D_source_cm
        y_s = 0.0

        dose_angle = np.zeros((n_z_points, n_x_points))

        for z_s in z_source:
            dx   = x_p - x_s
            dy   = y_p - y_s
            dz   = z_c - z_s
            dist = np.sqrt(dx**2 + dy**2 + dz**2)

            valid  = dist > 0.1
            inv_sq = np.where(valid, 1.0 / np.where(valid, dist**2, 1.0), 0.0)

            # Atenuación + buildup dependiente de radio
            atten   = np.exp(-mu_water * r * attenuation_factor)
            buildup = buildup_factor * (1.0 + buildup_radial_coef * r / 3.0)

            # Auto-blindaje (más pronunciado en el centro de la altura)
            altura_norm  = abs(z_s) / max(H_source_cm / 2, 1e-9)
            autoblindaje = np.exp(-self_shielding_coef * (1.0 - altura_norm))

            dose_angle += inv_sq * atten * buildup * autoblindaje

        dose_angle /= n_source_height_points
        dose_grid  += dose_angle

    dose_grid /= n_rotation_angles

    # Normalizar al centro
    i_zc = n_z_points   // 2
    i_xc = n_x_points   // 2
    center = dose_grid[i_zc, i_xc]
    G_xz = dose_grid / center if center > 0 else dose_grid

    return X_grid, Z_grid, G_xz


def dose_stats(G_xz: np.ndarray) -> dict:
    """Estadísticas básicas del mapa de dosis."""
    i_zc = G_xz.shape[0] // 2
    i_xc = G_xz.shape[1] // 2
    return {
        "min":       float(G_xz.min()),
        "max":       float(G_xz.max()),
        "centro":    float(G_xz[i_zc, i_xc]),
        "uniformidad_pct": float(G_xz.min() / G_xz[i_zc, i_xc] * 100),
    }
