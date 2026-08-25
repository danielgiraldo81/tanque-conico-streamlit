"""
Simulador de Vaciado de Tanque Conico - Streamlit
Punto 5 del trabajo de Modelacion y Simulacion: aplicacion web que anima el
vaciado del tanque, permite modificar dimensiones/orificio/altura inicial
desde la interfaz, y muestra en tiempo real la altura del agua y el tiempo
transcurrido.

La animacion esta dirigida por la solucion analitica h(t) del modelo fisico
(ver physics.py) usando el tiempo real transcurrido (time.perf_counter), no
por numero de fotogramas.
"""

from __future__ import annotations

import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from physics import (
    TankParams,
    analytical_drain_time,
    analytical_height,
    drain_constant,
    instantaneous_flow,
    orifice_area,
    validate_params,
)
from tank_svg import build_tank_svg

st.set_page_config(page_title="Simulacion de Tanque Conico - Daniel Giraldo y Allison Correa", page_icon="🌀", layout="wide")

# Valores por defecto = condiciones reales del tanque fisico construido para
# el trabajo (H=20 cm, R=5 cm, radio de orificio 0.2 cm -> d0=0.4 cm).
DEFAULT_PARAMS = dict(H=0.20, R=0.05, h0=0.20, d0=0.004, Cd=0.62, g=9.81)
SPEED_OPTIONS = [0.25, 0.5, 1.0, 2.0, 5.0]

# Rangos amplios: cubren desde el tanque de escala pequena realmente
# construido (cm) hasta tanques de mesa mas grandes (metros).
PARAM_LIMITS = {
    "H": dict(min_value=0.02, max_value=3.0, step=0.01, format="%.2f"),
    "R": dict(min_value=0.01, max_value=1.5, step=0.005, format="%.3f"),
    "h0": dict(min_value=0.005, max_value=3.0, step=0.005, format="%.3f"),
    "d0": dict(min_value=0.001, max_value=0.3, step=0.0005, format="%.4f"),
    "Cd": dict(min_value=0.3, max_value=1.0, step=0.01, format="%.2f"),
    "g": dict(min_value=1.0, max_value=25.0, step=0.01, format="%.2f"),
}


def load_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap');
        .stApp { background: #0e0c0a; }
        .metric-card {
            background: rgba(0,0,0,0.25);
            border: 1px solid #2a2420;
            border-radius: 12px;
            padding: 12px 14px;
            min-height: 92px;
        }
        .metric-label {
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #a39a8f;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-value {
            font-family: 'Courier New', monospace;
            font-size: 19px;
            font-weight: 700;
            color: #fef3e2;
            margin-top: 2px;
            white-space: nowrap;
        }
        .metric-hint { font-size: 11px; color: #8a8078; }
        .app-title { font-family: 'Space Grotesk', sans-serif; font-size: 21px; font-weight: 700; color: #fef3e2; margin-bottom: 0; }
        .app-subtitle { font-size: 13px; color: #a39a8f; margin-top: 2px; }
        section[data-testid="stSidebar"] { background: #16120e; border-right: 1px solid #2a2420; }
        div[data-testid="stMetricValue"] { font-family: 'Courier New', monospace; }
        .stButton > button[kind="primary"] { background-color: #f59e0b; border-color: #f59e0b; color: #1c1508; }
        .stButton > button[kind="primary"]:hover { background-color: #fbbf24; border-color: #fbbf24; }
        h6, .stMarkdown h6 { color: #f59e0b !important; letter-spacing: 0.1em; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    st.session_state.setdefault("params", dict(DEFAULT_PARAMS))
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("t_accum", 0.0)
    st.session_state.setdefault("t_start_perf", None)
    st.session_state.setdefault("speed", 1.0)


def reset_simulation() -> None:
    st.session_state.running = False
    st.session_state.t_accum = 0.0
    st.session_state.t_start_perf = None


def toggle_simulation(is_valid: bool) -> None:
    if not is_valid:
        return
    if st.session_state.running:
        st.session_state.t_accum = current_elapsed_time()
        st.session_state.t_start_perf = None
        st.session_state.running = False
    else:
        st.session_state.t_start_perf = time.perf_counter()
        st.session_state.running = True


def current_elapsed_time() -> float:
    if st.session_state.running and st.session_state.t_start_perf is not None:
        real_delta = time.perf_counter() - st.session_state.t_start_perf
        return st.session_state.t_accum + real_delta * st.session_state.speed
    return st.session_state.t_accum


def _clamp_widget_state(key: str, lo: float, hi: float) -> None:
    if key in st.session_state:
        st.session_state[key] = min(max(st.session_state[key], lo), hi)


def render_sidebar() -> tuple[TankParams, list[str]]:
    st.sidebar.markdown("**PARAMETROS DEL SISTEMA**")

    st.sidebar.caption("GEOMETRIA")
    lim_h = PARAM_LIMITS["H"]
    _clamp_widget_state("H", lim_h["min_value"], lim_h["max_value"])
    H = st.sidebar.slider("Altura del tanque H (m)", value=st.session_state.params["H"], key="H", **lim_h)

    lim_r = PARAM_LIMITS["R"]
    _clamp_widget_state("R", lim_r["min_value"], lim_r["max_value"])
    R = st.sidebar.slider("Radio superior R (m)", value=st.session_state.params["R"], key="R", **lim_r)

    lim_h0 = dict(PARAM_LIMITS["h0"])
    lim_h0["max_value"] = max(H, lim_h0["min_value"])
    _clamp_widget_state("h0", lim_h0["min_value"], lim_h0["max_value"])
    h0 = st.sidebar.slider("Altura inicial del agua h0 (m)", value=min(st.session_state.params["h0"], H), key="h0", **lim_h0)

    st.sidebar.caption("ORIFICIO")
    lim_d0 = PARAM_LIMITS["d0"]
    _clamp_widget_state("d0", lim_d0["min_value"], lim_d0["max_value"])
    d0 = st.sidebar.slider("Diametro del orificio d0 (m)", value=st.session_state.params["d0"], key="d0", **lim_d0)
    st.sidebar.caption(f"Ao = pi (d0/2)^2 = {orifice_area(d0):.6f} m^2")

    st.sidebar.caption("COEFICIENTES FISICOS")
    lim_cd = PARAM_LIMITS["Cd"]
    _clamp_widget_state("Cd", lim_cd["min_value"], lim_cd["max_value"])
    Cd = st.sidebar.slider("Coeficiente de descarga Cd", value=st.session_state.params["Cd"], key="Cd", **lim_cd)

    lim_g = PARAM_LIMITS["g"]
    _clamp_widget_state("g", lim_g["min_value"], lim_g["max_value"])
    g = st.sidebar.slider("Gravedad g (m/s^2)", value=st.session_state.params["g"], key="g", **lim_g)

    new_params = dict(H=H, R=R, h0=h0, d0=d0, Cd=Cd, g=g)
    if new_params != st.session_state.params:
        st.session_state.params = new_params
        reset_simulation()

    params = TankParams(**new_params)
    errors = validate_params(params)
    if errors:
        for e in errors:
            st.sidebar.error(e)

    return params, errors


def height_curve(params: TankParams, k: float, t_analytical: float) -> pd.DataFrame:
    if t_analytical <= 0 or t_analytical == float("inf"):
        return pd.DataFrame({"Tiempo (s)": [0.0], "Altura (m)": [params.h0]})
    samples = 80
    tiempos = []
    alturas = []
    for i in range(samples + 1):
        ti = (i / samples) * t_analytical
        tiempos.append(round(ti, 3))
        alturas.append(analytical_height(ti, params.h0, k))
    return pd.DataFrame({"Tiempo (s)": tiempos, "Altura (m)": alturas})


def render_config_panel(params: TankParams, is_valid: bool) -> None:
    # Fuera del fragmento de animacion a proposito: esta columna solo debe
    # volver a dibujarse cuando cambian los parametros (rerun normal de
    # Streamlit), no 10 veces por segundo -- redibujar la grafica en cada
    # tick del fragmento causaba parpadeos/carreras de render en el chart.
    st.markdown("###### CONFIGURACION")
    st.markdown("**Condiciones actuales**")
    st.write(
        f"- Altura del tanque **H** = {params.H:.3f} m\n"
        f"- Radio superior **R** = {params.R:.3f} m\n"
        f"- Altura inicial del agua **h0** = {params.h0:.3f} m\n"
        f"- Diametro del orificio **d0** = {params.d0:.4f} m\n"
        f"- Coeficiente de descarga **Cd** = {params.Cd:.2f}\n"
        f"- Gravedad **g** = {params.g:.2f} m/s^2"
    )
    st.caption("Modifica cualquier valor en el panel lateral izquierdo; la simulacion se reinicia automaticamente.")

    st.markdown("**Altura vs. tiempo**")
    if is_valid:
        k = drain_constant(params)
        t_analytical = analytical_drain_time(params.h0, k)
        st.line_chart(height_curve(params, k, t_analytical), x="Tiempo (s)", y="Altura (m)", height=220, color="#f59e0b")
    else:
        st.caption("Corrige los parametros para ver la curva.")


@st.fragment(run_every=0.1)
def render_tank_animation(params: TankParams, is_valid: bool) -> None:
    k = drain_constant(params) if is_valid else 0.0
    t_analytical = analytical_drain_time(params.h0, k) if is_valid else 0.0

    t = current_elapsed_time()
    if is_valid and t_analytical and t_analytical != float("inf") and t >= t_analytical:
        t = t_analytical
        if st.session_state.running:
            st.session_state.running = False
            st.session_state.t_accum = t_analytical
            st.session_state.t_start_perf = None
    is_finished = is_valid and t_analytical > 0 and t >= t_analytical

    h = analytical_height(t, params.h0, k) if is_valid else params.h0
    q = instantaneous_flow(h, params) if is_valid else 0.0
    q_max = instantaneous_flow(params.h0, params) if is_valid else 1.0
    percent_remaining = (max(0.0, min(1.0, h / params.h0)) ** 3 * 100) if params.h0 > 0 else 0.0

    st.markdown("###### SIMULACION")
    st.markdown("**Animacion del tanque**")
    svg = build_tank_svg(params.H, params.R, h, q, q_max, is_finished)
    html_snippet = f'<div style="background:transparent">{svg}</div>'
    if hasattr(st, "iframe"):
        st.iframe(html_snippet, height=440)
    else:
        components.html(html_snippet, height=440, scrolling=False)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Altura actual</div>'
            f'<div class="metric-value">{h:.3f} m</div><div class="metric-hint">h(t)</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Tiempo transcurrido</div>'
            f'<div class="metric-value">{t:.2f} s</div><div class="metric-hint">t</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        t_txt = f"{t_analytical:.2f} s" if is_valid and t_analytical != float("inf") else "--"
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Vaciado estimado</div>'
            f'<div class="metric-value">{t_txt}</div><div class="metric-hint">T analitico</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Agua restante</div>'
            f'<div class="metric-value">{percent_remaining:.1f} %</div><div class="metric-hint">% del volumen</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        label = "Pausar" if st.session_state.running else "Iniciar"
        if st.button(label, type="primary", disabled=(not is_valid) or (is_finished and not st.session_state.running)):
            toggle_simulation(is_valid)
            st.rerun(scope="fragment")
    with c2:
        if st.button("Reiniciar"):
            reset_simulation()
            st.rerun(scope="fragment")
    with c3:
        speed = st.select_slider("Velocidad", options=SPEED_OPTIONS, value=st.session_state.speed, key="speed_widget", label_visibility="collapsed")
        if speed != st.session_state.speed:
            st.session_state.t_accum = current_elapsed_time()
            if st.session_state.running:
                st.session_state.t_start_perf = time.perf_counter()
            st.session_state.speed = speed

    if not is_valid:
        st.error("Corrige los parametros en el panel lateral para poder simular.")


def main() -> None:
    load_css()
    init_state()

    col_icon, col_title = st.columns([0.05, 0.95])
    with col_icon:
        st.markdown("### 🌀")
    with col_title:
        st.markdown('<p class="app-title">Simulacion de Tanque Conico &mdash; Daniel Giraldo y Allison Correa</p>', unsafe_allow_html=True)
        st.markdown('<p class="app-subtitle">Simulacion animada del vaciado por orificio inferior</p>', unsafe_allow_html=True)

    params, errors = render_sidebar()
    is_valid = len(errors) == 0

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        render_tank_animation(params, is_valid=is_valid)
    with right:
        render_config_panel(params, is_valid=is_valid)

    st.markdown(
        '<p style="text-align:center;color:#5c5449;font-size:12px;margin-top:24px;">'
        "Herramienta de simulacion desarrollada para el curso de Modelacion y Simulacion &middot; "
        "Vaciado de tanque conico</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
