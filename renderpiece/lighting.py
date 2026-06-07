"""Estado e parametros de iluminacao do Projeto 3.

O professor pede parametros difusos/especulares proprios por objeto, sem
depender dos valores prontos dos arquivos `.mtl`. Este modulo centraliza esses
valores e a posicao do sol externo, que tambem e a fonte de luz pontual.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


SUN_MODEL_SCALE = 2.20
SUN_RADIUS = 4.157928 * SUN_MODEL_SCALE
SUN_ORBIT_RADIUS = 130.0
SUN_BASE_HEIGHT = 150.0

AMBIENT_LIGHT_COLOR = (0.95, 0.98, 1.00)
EXTERNAL_LIGHT_COLOR = (1.00, 0.86, 0.54)
FIREFLY_LIGHT_COLOR = (0.78, 1.00, 0.34)
LAMP_LIGHT_COLOR = (1.00, 0.78, 0.42)

EXTERNAL_LIGHT_INTENSITY = 120.0
FIREFLY_LIGHT_INTENSITY = 4.75
LAMP_LIGHT_INTENSITY = 5.60

FIREFLY_LIGHT_KEY = "firefly"
LAMP_LIGHT_KEY = "lamp"


@dataclass(frozen=True)
class LightingProfile:
    ambient: tuple[float, float, float]
    diffuse: tuple[float, float, float]
    specular: tuple[float, float, float]
    shininess: float
    emissive: tuple[float, float, float] = (0.0, 0.0, 0.0)
    emissive_off: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class LightingState:
    ambient_enabled: bool = True
    external_light_enabled: bool = True
    firefly_light_enabled: bool = True
    lamp_light_enabled: bool = True
    ambient_strength: float = 0.28
    diffuse_strength: float = 1.10
    specular_strength: float = 0.75
    sun_orbit_angle: float = 0.0

    def adjust_ambient(self, delta: float) -> None:
        self.ambient_strength = _clamp(self.ambient_strength + delta, 0.0, 0.85)

    def adjust_diffuse(self, delta: float) -> None:
        self.diffuse_strength = _clamp(self.diffuse_strength + delta, 0.0, 1.60)

    def adjust_specular(self, delta: float) -> None:
        self.specular_strength = _clamp(self.specular_strength + delta, 0.0, 1.80)

    def translate_sun(self, delta_angle: float) -> None:
        self.sun_orbit_angle = (self.sun_orbit_angle + delta_angle) % (2.0 * np.pi)


def internal_light_enabled(lighting: LightingState, light_name: str | None) -> bool:
    if light_name == FIREFLY_LIGHT_KEY:
        return lighting.firefly_light_enabled
    if light_name == LAMP_LIGHT_KEY:
        return lighting.lamp_light_enabled
    return True


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def sun_base_position(orbit_angle: float) -> np.ndarray:
    """Posicao da base do modelo do sol no ambiente externo.

    A matriz do modelo ancora a esfera pela base, entao a luz em si fica um raio
    acima dessa posicao. A translacao acontece somente via teclado, mudando o
    angulo orbital em torno do navio.
    """
    return np.array(
        [
            SUN_ORBIT_RADIUS * np.sin(orbit_angle),
            SUN_BASE_HEIGHT,
            -SUN_ORBIT_RADIUS * np.cos(orbit_angle),
        ],
        dtype=np.float32,
    )


def sun_light_position(orbit_angle: float) -> np.ndarray:
    position = sun_base_position(orbit_angle).copy()
    position[1] += SUN_RADIUS
    return position
