import math

import numpy as np

from .config import DECK_Y, OCEAN_Y, SKY_CEILING_Y, TERRAIN_Y, WINDOW_HEIGHT, WINDOW_WIDTH, WORLD_HALF_SIZE
from .math3d import look_at, normalize


class Camera:
    def __init__(self) -> None:
        self.position = np.array([0.0, DECK_Y + 2.0, 24.0], dtype=np.float32)
        self.yaw = -90.0
        self.pitch = -8.0
        self.speed = 9.0
        self.mouse_sensitivity = 0.09
        self.front = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        self.world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.first_mouse = True
        self.last_mouse_x = WINDOW_WIDTH / 2
        self.last_mouse_y = WINDOW_HEIGHT / 2
        self.update_vectors()

    def update_vectors(self) -> None:
        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)
        self.front = normalize(
            np.array(
                [
                    math.cos(yaw) * math.cos(pitch),
                    math.sin(pitch),
                    math.sin(yaw) * math.cos(pitch),
                ],
                dtype=np.float32,
            )
        )
        self.right = normalize(np.cross(self.front, self.world_up))
        self.up = normalize(np.cross(self.right, self.front))

    def view_matrix(self) -> np.ndarray:
        return look_at(self.position, self.position + self.front, self.up)

    def process_mouse(self, xpos: float, ypos: float) -> None:
        if self.first_mouse:
            self.last_mouse_x = xpos
            self.last_mouse_y = ypos
            self.first_mouse = False

        xoffset = (xpos - self.last_mouse_x) * self.mouse_sensitivity
        yoffset = (self.last_mouse_y - ypos) * self.mouse_sensitivity
        self.last_mouse_x = xpos
        self.last_mouse_y = ypos

        self.yaw += xoffset
        self.pitch = max(-89.0, min(89.0, self.pitch + yoffset))
        self.update_vectors()

    def move(self, direction: np.ndarray, amount: float) -> None:
        self.position += direction * amount
        self.position[0] = np.clip(self.position[0], -WORLD_HALF_SIZE + 1.0, WORLD_HALF_SIZE - 1.0)
        self.position[2] = np.clip(self.position[2], -WORLD_HALF_SIZE + 1.0, WORLD_HALF_SIZE - 1.0)
        # Limite inferior é a superfície do oceano (com folga para amplitude
        # máxima das ondas), conforme requisito 9: a câmera não pode atravessar
        # o piso do ambiente externo (que aqui é a água).
        floor_y = max(TERRAIN_Y + 0.35, OCEAN_Y + 1.0)
        self.position[1] = np.clip(self.position[1], floor_y, SKY_CEILING_Y - 0.5)

