"""Flags globais de UI/audio mutaveis pelo `key_callback` do `app.py`."""

from dataclasses import dataclass


@dataclass
class Toggles:
    # `wireframe` cumpre o requisito 10 (tecla P alterna malha poligonal)
    wireframe: bool = False
    paused: bool = False
    muted: bool = False


@dataclass
class UserTransforms:
    """Transformacoes interativas mantidas do Projeto 2.

    O Projeto 3 nao exige mais esses controles, mas eles continuam uteis para
    demonstrar escala, rotacao e translacao por matriz de modelo.
    """

    luffy_scale: float = 1.0
    franky_rotation_y: float = 0.0
    chopper_offset_x: float = 0.0
    chopper_offset_z: float = 0.0
