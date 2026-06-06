"""Flags globais de UI/audio mutaveis pelo `key_callback` do `app.py`."""

from dataclasses import dataclass


@dataclass
class Toggles:
    # `wireframe` cumpre o requisito 10 (tecla P alterna malha poligonal)
    wireframe: bool = False
    paused: bool = False
    muted: bool = False
