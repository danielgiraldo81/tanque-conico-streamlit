"""
Fuente unica de verdad matematica del modelo de vaciado de un tanque conico
invertido (apice hacia abajo, radio maximo R en la parte superior a la
altura H).

Geometria:   r(h) = (R/H) h          =>  A(h) = pi (R/H)^2 h^2
Torricelli:  Q(h) = Cd Ao sqrt(2 g h)
Balance:     A(h) dh/dt = -Q(h)      =>  dh/dt = -K h^(-3/2)
             con K = Cd Ao H^2 sqrt(2g) / (pi R^2)

Solucion analitica (separacion de variables):
    h(t) = [ h0^(5/2) - (5/2) K t ]^(2/5)
    T     = 2 h0^(5/2) / (5 K)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class TankParams:
    H: float   # altura total del tanque (m)
    R: float   # radio superior del tanque (m)
    h0: float  # altura inicial del agua (m)
    d0: float  # diametro del orificio inferior (m)
    Cd: float  # coeficiente de descarga (adimensional)
    g: float   # gravedad (m/s^2)


def orifice_area(d0: float) -> float:
    return math.pi * (d0 / 2) ** 2


def drain_constant(p: TankParams) -> float:
    ao = orifice_area(p.d0)
    return (p.Cd * ao * p.H * p.H * math.sqrt(2 * p.g)) / (math.pi * p.R * p.R)


def instantaneous_flow(h: float, p: TankParams) -> float:
    if h <= 0:
        return 0.0
    ao = orifice_area(p.d0)
    return p.Cd * ao * math.sqrt(2 * p.g * h)


def analytical_height(t: float, h0: float, k: float) -> float:
    if h0 <= 0:
        return 0.0
    if k <= 0:
        return h0
    if t <= 0:
        return h0
    inner = h0**2.5 - 2.5 * k * t
    if inner <= 0:
        return 0.0
    h = inner**0.4
    return h if math.isfinite(h) and h > 0 else 0.0


def analytical_drain_time(h0: float, k: float) -> float:
    if h0 <= 0:
        return 0.0
    if k <= 0:
        return math.inf
    return (2 * h0**2.5) / (5 * k)


def validate_params(p: TankParams) -> list[str]:
    errors: list[str] = []
    if not (p.H > 0):
        errors.append("La altura del tanque (H) debe ser mayor que 0.")
    if not (p.R > 0):
        errors.append("El radio superior (R) debe ser mayor que 0.")
    if not (p.h0 > 0):
        errors.append("La altura inicial (h0) debe ser mayor que 0.")
    elif p.H > 0 and p.h0 > p.H:
        errors.append("La altura inicial (h0) no puede superar la altura del tanque (H).")
    if not (p.d0 > 0):
        errors.append("El diametro del orificio (d0) debe ser mayor que 0.")
    elif p.R > 0 and p.d0 >= 2 * p.R:
        errors.append("El diametro del orificio (d0) debe ser menor que el diametro del tanque (2R).")
    if not (0 < p.Cd <= 1):
        errors.append("El coeficiente de descarga (Cd) debe estar entre 0 y 1.")
    if not (p.g > 0):
        errors.append("La gravedad (g) debe ser mayor que 0.")
    return errors
