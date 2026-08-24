"""Genera el SVG animado del tanque conico, replicando la geometria y el
estilo visual (vidrio translucido, superficie de agua, chorro) de la version
Next.js original, ahora renderizado desde Python para Streamlit."""

from __future__ import annotations

VIEW_W = 320
VIEW_H = 420
APEX_Y = 372
TOP_Y = 46
CENTER_X = VIEW_W / 2
CONE_HEIGHT_PX = APEX_Y - TOP_Y


def _radius_px(r_m: float) -> float:
    clamped = min(max(r_m, 0.1), 1.6)
    return 44 + clamped * 78


def build_tank_svg(H: float, R: float, h: float, Q: float, q_max: float, is_empty: bool) -> str:
    r_px = _radius_px(R)
    clamped_h = min(max(h, 0.0), H) if H > 0 else 0.0
    fill_ratio = (clamped_h / H) if H > 0 else 0.0
    water_y = APEX_Y - fill_ratio * CONE_HEIGHT_PX
    water_half_width = fill_ratio * r_px

    flow_ratio = min(Q / q_max, 1.0) if q_max > 0 else 0.0
    jet_visible = (not is_empty) and flow_ratio > 0.002
    jet_height = 18 + flow_ratio * 30
    jet_width = 3 + flow_ratio * 7

    outline_points = f"{CENTER_X},{APEX_Y} {CENTER_X - r_px},{TOP_Y} {CENTER_X + r_px},{TOP_Y}"
    water_points = (
        f"{CENTER_X},{APEX_Y} "
        f"{CENTER_X - water_half_width},{water_y} "
        f"{CENTER_X + water_half_width},{water_y}"
    )

    water_block = ""
    if clamped_h > 0:
        surface_ry = max(water_half_width * 0.16, 2)
        water_block = f"""
          <polygon points="{water_points}" fill="url(#water)" />
          <ellipse cx="{CENTER_X}" cy="{water_y}" rx="{max(water_half_width, 0.001)}" ry="{surface_ry}"
                   fill="url(#surface)" stroke="#cffafe" stroke-opacity="0.5" stroke-width="1" />
        """

    jet_block = ""
    if jet_visible:
        opacity = 0.55 + flow_ratio * 0.4
        jet_block = f"""
          <path d="M {CENTER_X - jet_width / 2} {APEX_Y + 3}
                   C {CENTER_X - jet_width} {APEX_Y + jet_height * 0.5},
                     {CENTER_X - jet_width * 0.4} {APEX_Y + jet_height * 0.8},
                     {CENTER_X - jet_width * 0.7} {APEX_Y + jet_height}
                   L {CENTER_X + jet_width * 0.7} {APEX_Y + jet_height}
                   C {CENTER_X + jet_width * 0.4} {APEX_Y + jet_height * 0.8},
                     {CENTER_X + jet_width} {APEX_Y + jet_height * 0.5},
                     {CENTER_X + jet_width / 2} {APEX_Y + 3} Z"
                fill="url(#jet)" opacity="{opacity}" />
        """

    empty_label = ""
    if is_empty:
        empty_label = (
            f'<text x="{CENTER_X}" y="{APEX_Y - 14}" text-anchor="middle" '
            'fill="#78716c" font-size="10" letter-spacing="1.5" '
            'font-family="monospace">TANQUE VACIO</text>'
        )

    return f"""
<svg viewBox="0 0 {VIEW_W} {VIEW_H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:360px;display:block;margin:0 auto;">
  <defs>
    <linearGradient id="glass" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.09" />
      <stop offset="45%" stop-color="#f5f0e6" stop-opacity="0.03" />
      <stop offset="100%" stop-color="#fbbf24" stop-opacity="0.11" />
    </linearGradient>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#67e8f9" stop-opacity="0.85" />
      <stop offset="100%" stop-color="#0891b2" stop-opacity="0.75" />
    </linearGradient>
    <radialGradient id="surface" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#a5f3fc" stop-opacity="0.9" />
      <stop offset="100%" stop-color="#22d3ee" stop-opacity="0.55" />
    </radialGradient>
    <linearGradient id="jet" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#a5f3fc" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#22d3ee" stop-opacity="0.15" />
    </linearGradient>
    <clipPath id="cone-clip">
      <polygon points="{outline_points}" />
    </clipPath>
  </defs>

  <ellipse cx="{CENTER_X}" cy="{APEX_Y + 22}" rx="{r_px * 0.75}" ry="8" fill="#000" opacity="0.35" />

  <g clip-path="url(#cone-clip)">
    <rect x="0" y="0" width="{VIEW_W}" height="{VIEW_H}" fill="url(#glass)" />
    {water_block}
  </g>

  <polygon points="{outline_points}" fill="none" stroke="#a8a29e" stroke-width="2" stroke-linejoin="round" />
  <ellipse cx="{CENTER_X}" cy="{TOP_Y}" rx="{r_px}" ry="10" fill="none" stroke="#a8a29e" stroke-width="2" />

  <circle cx="{CENTER_X}" cy="{APEX_Y}" r="4.5" fill="#0c0a09" stroke="#d6d3d1" stroke-width="1.5" />

  {jet_block}
  {empty_label}
</svg>
"""
