from __future__ import annotations
import math
import numpy as np


def normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm <= 1e-8:
        return v
    return v / norm


def translate(x: float, y: float, z: float) -> np.ndarray:
    matrix = np.identity(4, dtype=np.float32)
    matrix[0, 3] = x
    matrix[1, 3] = y
    matrix[2, 3] = z
    return matrix


def scale(sx: float, sy: float | None = None, sz: float | None = None) -> np.ndarray:
    if sy is None:
        sy = sx
    if sz is None:
        sz = sx
    matrix = np.identity(4, dtype=np.float32)
    matrix[0, 0] = sx
    matrix[1, 1] = sy
    matrix[2, 2] = sz
    return matrix


def rotate_x(angle_radians: float) -> np.ndarray:
    c = math.cos(angle_radians)
    s = math.sin(angle_radians)
    matrix = np.identity(4, dtype=np.float32)
    matrix[1, 1] = c
    matrix[1, 2] = -s
    matrix[2, 1] = s
    matrix[2, 2] = c
    return matrix


def rotate_y(angle_radians: float) -> np.ndarray:
    c = math.cos(angle_radians)
    s = math.sin(angle_radians)
    matrix = np.identity(4, dtype=np.float32)
    matrix[0, 0] = c
    matrix[0, 2] = s
    matrix[2, 0] = -s
    matrix[2, 2] = c
    return matrix


def rotate_z(angle_radians: float) -> np.ndarray:
    c = math.cos(angle_radians)
    s = math.sin(angle_radians)
    matrix = np.identity(4, dtype=np.float32)
    matrix[0, 0] = c
    matrix[0, 1] = -s
    matrix[1, 0] = s
    matrix[1, 1] = c
    return matrix


def euler_xyz(rx: float, ry: float, rz: float) -> np.ndarray:
    return rotate_z(rz) @ rotate_y(ry) @ rotate_x(rx)


def perspective(fov_radians: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(fov_radians / 2.0)
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = f / aspect
    matrix[1, 1] = f
    matrix[2, 2] = (far + near) / (near - far)
    matrix[2, 3] = (2.0 * far * near) / (near - far)
    matrix[3, 2] = -1.0
    return matrix


def look_at(eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> np.ndarray:
    f = normalize(center - eye)
    s = normalize(np.cross(f, up))
    u = np.cross(s, f)

    matrix = np.identity(4, dtype=np.float32)
    matrix[0, 0:3] = s
    matrix[1, 0:3] = u
    matrix[2, 0:3] = -f
    matrix[0, 3] = -np.dot(s, eye)
    matrix[1, 3] = -np.dot(u, eye)
    matrix[2, 3] = np.dot(f, eye)
    return matrix


def compose_transform(
    position: tuple[float, float, float],
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    object_scale: tuple[float, float, float] | float = 1.0,
) -> np.ndarray:
    if isinstance(object_scale, (int, float)):
        object_scale = (float(object_scale), float(object_scale), float(object_scale))
    rx, ry, rz = (math.radians(v) for v in rotation)
    return (
        translate(*position)
        @ euler_xyz(rx, ry, rz)
        @ scale(object_scale[0], object_scale[1], object_scale[2])
    )
