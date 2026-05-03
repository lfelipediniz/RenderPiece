from dataclasses import dataclass


@dataclass
class Toggles:
    wireframe: bool = False
    paused: bool = False

