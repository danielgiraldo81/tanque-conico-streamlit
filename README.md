# Simulación de Tanque Cónico — Daniel Giraldo (Streamlit)

Aplicación web interactiva que simula mediante una animación el vaciado de
un tanque cónico por un orificio inferior. Corresponde al **punto 5** del
trabajo de Modelación y Simulación: "Desarrolle una aplicación web que
permita simular mediante una animación el vaciado del tanque."

**Demo en vivo:** _(agregar aquí la URL de Streamlit Community Cloud tras el despliegue)_

## Qué cumple

- Animación del tanque cónico sincronizada al tiempo físico real (no una
  animación de duración fija): el nivel del agua se calcula con la solución
  analítica `h(t)` del modelo, evaluada con el tiempo real transcurrido.
- Parámetros modificables desde la interfaz — como mínimo exigido:
  - Dimensiones del tanque (`H`, `R`).
  - Dimensiones del orificio (`d0`).
  - Altura inicial del agua (`h0`).
  - Además: coeficiente de descarga (`Cd`) y gravedad (`g`), necesarios para
    calcular el modelo.
  - Rangos amplios en todos los sliders (desde escala de centímetros hasta
    metros) para cubrir tanto el tanque físico real construido para el
    trabajo (`H=20 cm`, `R=5 cm`, radio de orificio `0.2 cm`) como tanques
    de mayor tamaño.
- Durante la simulación se muestran, como mínimo, la altura del agua y el
  tiempo transcurrido (`h(t)` y `t`), junto con el tiempo de vaciado
  estimado y el porcentaje de agua restante.
- Gráfica de altura vs. tiempo (analítica) junto al panel de configuración.
- Sección de validación experimental: hasta seis mediciones reales
  (altura inicial + tiempo cronometrado), con cálculo automático del
  tiempo analítico correspondiente, error relativo, y una gráfica
  comparando ambas series (analítico vs. experimental).
- Aplicación desplegada y accesible mediante un enlace público.

Los valores por defecto de los parámetros corresponden a las condiciones
reales del tanque físico construido para el trabajo.

## Modelo físico

Mismo modelo matemático que el resto de las entregas del trabajo (tanque
cónico invertido, ápice hacia abajo):

```
A(h) = pi (R/H)^2 h^2                    (geometria)
Q(h) = Cd Ao sqrt(2 g h)                 (Torricelli, Ao = pi (d0/2)^2)
dh/dt = -K h^(-3/2)                      (balance de volumen)
K = Cd Ao H^2 sqrt(2g) / (pi R^2)

h(t) = [ h0^(5/2) - (5/2) K t ]^(2/5)    (solucion analitica)
T     = 2 h0^(5/2) / (5 K)               (tiempo de vaciado)
```

Implementado en `physics.py` — única fuente de verdad matemática que usa
la app; la animación (`tank_svg.py`) y las gráficas solo dibujan el
resultado de `h(t)` y `T`.

## Stack

Python + [Streamlit](https://streamlit.io) + pandas. El tanque se dibuja
como SVG generado en Python (`tank_svg.py`) y se embebe con `st.iframe`.
La animación del tanque avanza en tiempo real mediante
`st.fragment(run_every=0.1)` (auto-actualización cada 100 ms basada en el
reloj físico `time.perf_counter()`, no en un contador de fotogramas); el
resto de la interfaz (gráficas, panel de configuración) vive fuera de ese
fragmento para no redibujarse innecesariamente 10 veces por segundo.

## Ejecutar localmente

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

Abrir [http://localhost:8501](http://localhost:8501).

## Estructura

```
app.py                  # UI de Streamlit, estado de la simulacion, reloj fisico
physics.py               # Modelo matematico (K, h(t), T, Q) — fuente unica de verdad
tank_svg.py                # Generador del SVG animado del tanque
requirements.txt            # streamlit, pandas
runtime.txt                   # version de Python fijada para el despliegue
.streamlit/config.toml         # tema oscuro (ambar/grafito)
```

## Despliegue en Streamlit Community Cloud

1. Entrar a [share.streamlit.io](https://share.streamlit.io) con la cuenta
   de GitHub dueña de este repositorio.
2. "New app" → seleccionar este repositorio, branch `main`, archivo
   principal `app.py`.
3. Deploy.
