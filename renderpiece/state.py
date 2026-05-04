"""Flags globais de UI/audio mutaveis pelo `key_callback` do `app.py`"""

from dataclasses import dataclass


@dataclass
class Toggles:
    # `wireframe` cumpre o requisito 10 (tecla P alterna malha poligonal)
    wireframe: bool = False
    paused: bool = False
    muted: bool = False


@dataclass
class UserTransforms:
    # Cumpre o requisito 7: cada delta abaixo eh aplicado em um modelo
    # diferente e controlado por teclas independentes
    #   Escala     -> Luffy  (teclas 1/2)
    #   Rotacao Y  -> Franky (teclas 3/4)
    #   Translacao -> Chopper (teclas 5/6 em X, 7/8 em Z)
    luffy_scale: float = 1.0
    franky_rotation_y: float = 0.0  # radianos, somado a rotacao base do modelo
    chopper_offset_x: float = 0.0
    chopper_offset_z: float = 0.0

