from __future__ import annotations

import ctypes
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import glfw
import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_CLAMP_TO_EDGE,
    GL_COLOR_BUFFER_BIT,
    GL_COMPILE_STATUS,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FALSE,
    GL_FILL,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FRONT_AND_BACK,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_LINE,
    GL_LINK_STATUS,
    GL_REPEAT,
    GL_RGB,
    GL_RGBA,
    GL_STATIC_DRAW,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TRIANGLES,
    GL_TRUE,
    GL_UNSIGNED_BYTE,
    GL_UNSIGNED_INT,
    GL_VERTEX_SHADER,
    glActiveTexture,
    glAttachShader,
    glBindBuffer,
    glBindTexture,
    glBindVertexArray,
    glBufferData,
    glClear,
    glClearColor,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glDrawElements,
    glEnable,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenTextures,
    glGenVertexArrays,
    glGenerateMipmap,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glPixelStorei,
    glPolygonMode,
    glShaderSource,
    glTexImage2D,
    glTexParameteri,
    glUniform1i,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
    GL_UNPACK_ALIGNMENT,
)
from PIL import Image


ROOT = Path(__file__).resolve().parent
ASSET_ROOT = ROOT / "modelos"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WORLD_HALF_SIZE = 80.0
TERRAIN_Y = 0.0
SKY_CEILING_Y = 34.0

DECK_Y = 6.85
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tga", ".bmp")


VERTEX_SHADER = """
#version 330 core

layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 a_texcoord;
layout (location = 2) in vec3 a_normal;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

out vec2 v_texcoord;

void main()
{
    v_texcoord = a_texcoord;
    gl_Position = u_projection * u_view * u_model * vec4(a_position, 1.0);
}
"""


FRAGMENT_SHADER = """
#version 330 core

in vec2 v_texcoord;

uniform sampler2D u_texture;
uniform vec3 u_diffuse;

out vec4 frag_color;

void main()
{
    frag_color = texture(u_texture, v_texcoord) * vec4(u_diffuse, 1.0);
}
"""


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


@dataclass
class Material:
    name: str
    diffuse: tuple[float, float, float] = (1.0, 1.0, 1.0)
    texture_path: Path | None = None
    texture_id: int | None = None


@dataclass
class DrawBatch:
    start_index: int
    index_count: int
    material_name: str


@dataclass
class Bounds:
    minimum: np.ndarray
    maximum: np.ndarray

    @property
    def center(self) -> np.ndarray:
        return (self.minimum + self.maximum) * 0.5


@dataclass
class GpuMesh:
    name: str
    vao: int
    vbo: int
    ebo: int
    index_count: int
    batches: list[DrawBatch]
    materials: dict[str, Material]
    bounds: Bounds
    anchor_to_base: np.ndarray = field(default_factory=lambda: np.identity(4, dtype=np.float32))

    def draw(
        self,
        shader: "ShaderProgram",
        model_matrix: np.ndarray,
        white_texture: int,
    ) -> None:
        glUniformMatrix4fv(shader.uniforms["u_model"], 1, GL_TRUE, model_matrix)
        glBindVertexArray(self.vao)

        for batch in self.batches:
            material = self.materials.get(batch.material_name) or self.materials["default"]
            texture_id = material.texture_id or white_texture

            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glUniform1i(shader.uniforms["u_texture"], 0)
            glUniform3f(shader.uniforms["u_diffuse"], *material.diffuse)

            byte_offset = ctypes.c_void_p(batch.start_index * np.dtype(np.uint32).itemsize)
            glDrawElements(GL_TRIANGLES, batch.index_count, GL_UNSIGNED_INT, byte_offset)

        glBindVertexArray(0)


@dataclass
class SceneObject:
    name: str
    mesh: GpuMesh
    model_factory: Callable[[float], np.ndarray]

    def model_matrix(self, elapsed: float) -> np.ndarray:
        return self.model_factory(elapsed) @ self.mesh.anchor_to_base


@dataclass
class Toggles:
    wireframe: bool = False


class ShaderProgram:
    def __init__(self, vertex_source: str, fragment_source: str) -> None:
        vertex_shader = self._compile(GL_VERTEX_SHADER, vertex_source)
        fragment_shader = self._compile(GL_FRAGMENT_SHADER, fragment_source)

        self.program = glCreateProgram()
        glAttachShader(self.program, vertex_shader)
        glAttachShader(self.program, fragment_shader)
        glLinkProgram(self.program)

        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(self.program).decode("utf-8"))

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        self.uniforms = {
            "u_model": glGetUniformLocation(self.program, "u_model"),
            "u_view": glGetUniformLocation(self.program, "u_view"),
            "u_projection": glGetUniformLocation(self.program, "u_projection"),
            "u_texture": glGetUniformLocation(self.program, "u_texture"),
            "u_diffuse": glGetUniformLocation(self.program, "u_diffuse"),
        }

    @staticmethod
    def _compile(shader_type: int, source: str) -> int:
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(shader).decode("utf-8"))

        return shader

    def use(self) -> None:
        glUseProgram(self.program)


class TextureCache:
    def __init__(self) -> None:
        self.cache: dict[str, int] = {}
        self.white_texture = self.create_solid("white", (255, 255, 255, 255))

    def create_solid(self, name: str, color: tuple[int, int, int, int]) -> int:
        image = Image.new("RGBA", (1, 1), color)
        return self.from_image(name, image, repeat=False)

    def from_image(self, name: str, image: Image.Image, repeat: bool = True) -> int:
        if name in self.cache:
            return self.cache[name]

        image = image.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        width, height = image.size
        data = image.tobytes()

        texture_id = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT if repeat else GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT if repeat else GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            data,
        )
        glGenerateMipmap(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)

        self.cache[name] = texture_id
        return texture_id

    def from_file(self, path: Path, repeat: bool = True) -> int:
        key = str(path.resolve())
        if key in self.cache:
            return self.cache[key]

        try:
            image = Image.open(path)
        except Exception as exc:
            print(f"[texture] Could not load {path}: {exc}. Using white texture.")
            return self.white_texture

        return self.from_image(key, image, repeat=repeat)


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
        self.position[1] = np.clip(self.position[1], TERRAIN_Y + 0.35, SKY_CEILING_Y - 0.5)


def parse_texture_name(rest: str) -> str:
    option_lengths = {
        "-blendu": 1,
        "-blendv": 1,
        "-bm": 1,
        "-boost": 1,
        "-cc": 1,
        "-clamp": 1,
        "-imfchan": 1,
        "-mm": 2,
        "-o": 3,
        "-s": 3,
        "-t": 3,
        "-texres": 1,
        "-type": 1,
    }
    tokens = rest.split()
    filename_tokens: list[str] = []
    skip = 0
    for token in tokens:
        if skip:
            skip -= 1
            continue
        if token.startswith("-"):
            skip = option_lengths.get(token, 0)
            continue
        filename_tokens.append(token)
    return " ".join(filename_tokens)


def resolve_texture_path(texture_name: str, obj_path: Path, extra_dirs: list[Path]) -> Path | None:
    if not texture_name:
        return None

    texture_path = Path(texture_name)
    search_dirs = [obj_path.parent, obj_path.parent.parent / "textures", *extra_dirs]

    if texture_path.is_absolute() and texture_path.exists():
        return texture_path

    candidates: list[Path] = []
    for directory in search_dirs:
        candidates.append(directory / texture_path)
        candidates.append(directory / texture_path.name)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    stem = texture_path.stem
    for directory in search_dirs:
        for extension in IMAGE_EXTENSIONS:
            candidate = directory / f"{stem}{extension}"
            if candidate.exists():
                return candidate

    return None


def read_mtl(obj_path: Path, extra_texture_dirs: list[Path]) -> dict[str, Material]:
    materials: dict[str, Material] = {}
    mtl_files: list[Path] = []

    with obj_path.open("r", errors="ignore") as obj_file:
        for line in obj_file:
            if line.startswith("mtllib "):
                raw_name = line.split(None, 1)[1].strip()
                mtl_files.append(obj_path.parent / raw_name)

    for mtl_path in mtl_files:
        if not mtl_path.exists():
            print(f"[mtl] Missing {mtl_path}. The object will use fallback material data.")
            continue

        current: Material | None = None
        with mtl_path.open("r", errors="ignore") as mtl_file:
            for raw_line in mtl_file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                keyword = line.split(None, 1)[0].lower()
                if keyword == "newmtl":
                    name = line.split(None, 1)[1].strip()
                    current = Material(name=name)
                    materials[name] = current
                elif current and keyword == "kd":
                    parts = line.split()
                    if len(parts) >= 4:
                        current.diffuse = tuple(float(v) for v in parts[1:4])
                elif current and keyword == "map_kd":
                    texture_name = parse_texture_name(line.split(None, 1)[1])
                    current.texture_path = resolve_texture_path(texture_name, obj_path, extra_texture_dirs)
                    if current.texture_path is None:
                        print(f"[texture] Could not resolve {texture_name} referenced by {mtl_path}")

    return materials


def parse_obj_index(value: str, total: int) -> int | None:
    if not value:
        return None
    index = int(value)
    if index > 0:
        return index - 1
    return total + index


def fallback_uv(position: tuple[float, float, float]) -> tuple[float, float]:
    return (position[0] * 0.08, position[2] * 0.08)


def load_obj_mesh(
    name: str,
    obj_path: Path,
    textures: TextureCache,
    fallback_texture: int | None = None,
    fallback_diffuse: tuple[float, float, float] = (1.0, 1.0, 1.0),
    force_white_diffuse_when_textured: bool = False,
    extra_texture_dirs: list[Path] | None = None,
    material_texture_overrides: dict[str, Path] | None = None,
) -> GpuMesh:
    if extra_texture_dirs is None:
        extra_texture_dirs = []
    if material_texture_overrides is None:
        material_texture_overrides = {}

    print(f"[obj] Loading {name}: {obj_path}")
    start_time = time.perf_counter()

    positions: list[tuple[float, float, float]] = []
    texcoords: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []

    vertex_data: list[float] = []
    indices: list[int] = []
    vertex_lookup: dict[tuple[int | None, int | None, int | None], int] = {}
    batches: list[DrawBatch] = []

    materials = read_mtl(obj_path, extra_texture_dirs)
    materials.setdefault("default", Material("default", diffuse=fallback_diffuse))

    current_material = "default"
    current_batch_start = 0

    min_bound = np.array([math.inf, math.inf, math.inf], dtype=np.float32)
    max_bound = np.array([-math.inf, -math.inf, -math.inf], dtype=np.float32)

    def flush_batch() -> None:
        nonlocal current_batch_start
        count = len(indices) - current_batch_start
        if count > 0:
            batches.append(DrawBatch(current_batch_start, count, current_material))
            current_batch_start = len(indices)

    def material_for(name_to_get: str) -> Material:
        if name_to_get not in materials:
            materials[name_to_get] = Material(name_to_get, diffuse=fallback_diffuse)
        return materials[name_to_get]

    def add_vertex(token: str) -> int:
        parts = token.split("/")
        vertex_index = parse_obj_index(parts[0], len(positions)) if len(parts) > 0 else None
        texcoord_index = parse_obj_index(parts[1], len(texcoords)) if len(parts) > 1 else None
        normal_index = parse_obj_index(parts[2], len(normals)) if len(parts) > 2 else None
        key = (vertex_index, texcoord_index, normal_index)

        if key in vertex_lookup:
            return vertex_lookup[key]
        if vertex_index is None:
            raise ValueError(f"Face vertex without position in {obj_path}: {token}")

        position = positions[vertex_index]
        texcoord = texcoords[texcoord_index] if texcoord_index is not None else fallback_uv(position)
        normal = normals[normal_index] if normal_index is not None else (0.0, 1.0, 0.0)

        new_index = len(vertex_data) // 8
        vertex_data.extend(
            [
                position[0],
                position[1],
                position[2],
                texcoord[0],
                texcoord[1],
                normal[0],
                normal[1],
                normal[2],
            ]
        )
        vertex_lookup[key] = new_index
        return new_index

    with obj_path.open("r", errors="ignore") as obj_file:
        for raw_line in obj_file:
            if not raw_line or raw_line.startswith("#"):
                continue
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("v "):
                parts = line.split()
                position = (float(parts[1]), float(parts[2]), float(parts[3]))
                positions.append(position)
                min_bound = np.minimum(min_bound, np.array(position, dtype=np.float32))
                max_bound = np.maximum(max_bound, np.array(position, dtype=np.float32))
            elif line.startswith("vt "):
                parts = line.split()
                texcoords.append((float(parts[1]), float(parts[2])))
            elif line.startswith("vn "):
                parts = line.split()
                normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("usemtl "):
                flush_batch()
                current_material = line.split(None, 1)[1].strip()
                material_for(current_material)
            elif line.startswith("f "):
                face_tokens = line.split()[1:]
                if len(face_tokens) < 3:
                    continue

                face_indices = [add_vertex(face_token) for face_token in face_tokens]
                for i in range(1, len(face_indices) - 1):
                    indices.extend([face_indices[0], face_indices[i], face_indices[i + 1]])

    flush_batch()

    if not vertex_data or not indices:
        raise RuntimeError(f"No drawable geometry found in {obj_path}")

    for material in materials.values():
        override_path = material_texture_overrides.get(material.name)
        has_real_texture = material.texture_path is not None
        if override_path and override_path.exists():
            material.texture_id = textures.from_file(override_path)
            if force_white_diffuse_when_textured:
                material.diffuse = (1.0, 1.0, 1.0)
        elif has_real_texture:
            material.texture_id = textures.from_file(material.texture_path)
            if force_white_diffuse_when_textured:
                material.diffuse = (1.0, 1.0, 1.0)
        elif fallback_texture is not None:
            material.texture_id = fallback_texture
            if force_white_diffuse_when_textured:
                material.diffuse = (1.0, 1.0, 1.0)
        else:
            material.texture_id = textures.white_texture

    vertices_np = np.array(vertex_data, dtype=np.float32)
    indices_np = np.array(indices, dtype=np.uint32)

    vao = int(glGenVertexArrays(1))
    vbo = int(glGenBuffers(1))
    ebo = int(glGenBuffers(1))

    glBindVertexArray(vao)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices_np.nbytes, indices_np, GL_STATIC_DRAW)

    stride = 8 * np.dtype(np.float32).itemsize
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
    glEnableVertexAttribArray(2)

    glBindVertexArray(0)

    bounds = Bounds(min_bound, max_bound)
    center = bounds.center
    anchor = translate(-float(center[0]), -float(min_bound[1]), -float(center[2]))

    elapsed = time.perf_counter() - start_time
    print(
        f"[obj] {name}: {len(vertices_np) // 8:,} unique vertices, "
        f"{len(indices_np) // 3:,} triangles, {len(batches)} batches in {elapsed:.2f}s"
    )

    return GpuMesh(
        name=name,
        vao=vao,
        vbo=vbo,
        ebo=ebo,
        index_count=len(indices_np),
        batches=batches or [DrawBatch(0, len(indices_np), "default")],
        materials=materials,
        bounds=bounds,
        anchor_to_base=anchor,
    )


def build_scene(textures: TextureCache) -> list[SceneObject]:
    ship_textures = ASSET_ROOT / "navio/textures"
    luffy_textures = ASSET_ROOT / "lado_externo/luffy/textures"

    ship = load_obj_mesh(
        "Going Merry",
        ASSET_ROOT / "navio/source/Going Merry.obj",
        textures,
        fallback_texture=textures.from_file(ship_textures / "000.png"),
        force_white_diffuse_when_textured=True,
    )

    luffy = load_obj_mesh(
        "Luffy",
        ASSET_ROOT / "lado_externo/luffy/source/Monkey D. Luffy.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
        material_texture_overrides={
            "24_-Straw_Hat.Hat_Hair_0.2_0_0": luffy_textures / "Scratch.png",
            "Gum": luffy_textures / "IMG_1670.jpeg",
            "Gum.001": luffy_textures / "IMG_1671.png",
            "Lower_shorts": luffy_textures / "IMG_1663.jpeg",
            "Pupil": luffy_textures / "Scratch.png",
            "Ribbon": luffy_textures / "IMG_1670.jpeg",
            "Sandals": luffy_textures / "IMG_0451.jpeg",
            "Sandals.001": luffy_textures / "IMG_0451.jpeg",
            "Shirt": luffy_textures / "IMG_1670.jpeg",
            "Shorts": luffy_textures / "IMG_1663.jpeg",
            "Straw_hat": luffy_textures / "IMG_1674.jpeg",
            "Teeth": luffy_textures / "IMG_1671.png",
            "button": luffy_textures / "IMG_1672.jpeg",
            "eye": luffy_textures / "IMG_1671.png",
            "hair": luffy_textures / "Scratch.png",
            "shock": luffy_textures / "IMG_1671.png",
            "skin": luffy_textures / "IMG_1662.jpeg",
            "tongue": luffy_textures / "IMG_1670.jpeg",
        },
    )
    luffy.batches = [
        batch for batch in luffy.batches if batch.material_name != "Eyebrows_and_scratch"
    ]

    def static_object(mesh: GpuMesh, matrix: np.ndarray, name: str) -> SceneObject:
        return SceneObject(name, mesh, lambda _elapsed, m=matrix: m)

    return [
        static_object(
            ship,
            compose_transform((0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), object_scale=0.01),
            "Ship",
        ),
        static_object(
            luffy,
            compose_transform((0.0, 11.92, 11.75), rotation=(0.0, 0.0, 0.0), object_scale=1.0),
            "Luffy on prow",
        ),
    ]


def framebuffer_size_callback(_window: glfw._GLFWwindow, width: int, height: int) -> None:
    from OpenGL.GL import glViewport

    glViewport(0, 0, width, height)


def process_keyboard(window: glfw._GLFWwindow, camera: Camera, dt: float) -> None:
    velocity = camera.speed * dt
    if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
        velocity *= 2.0

    flat_front = normalize(np.array([camera.front[0], 0.0, camera.front[2]], dtype=np.float32))
    flat_right = normalize(np.array([camera.right[0], 0.0, camera.right[2]], dtype=np.float32))

    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        camera.move(flat_front, velocity)
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        camera.move(-flat_front, velocity)
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        camera.move(-flat_right, velocity)
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        camera.move(flat_right, velocity)
    if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS:
        camera.move(camera.world_up, velocity)
    if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS:
        camera.move(-camera.world_up, velocity)


def init_window() -> glfw._GLFWwindow:
    if not glfw.init():
        raise RuntimeError("Could not initialize GLFW")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Render Piece - Projeto 2", None, None)
    if window is None:
        glfw.terminate()
        raise RuntimeError("Could not create GLFW window")

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    return window


def main() -> None:
    camera = Camera()
    toggles = Toggles()
    window = init_window()

    def mouse_callback(_window: glfw._GLFWwindow, xpos: float, ypos: float) -> None:
        camera.process_mouse(xpos, ypos)

    def key_callback(window_handle: glfw._GLFWwindow, key: int, _scancode: int, action: int, _mods: int) -> None:
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window_handle, True)
        elif key == glfw.KEY_P:
            toggles.wireframe = not toggles.wireframe
            print(f"[input] Wireframe: {toggles.wireframe}")
        elif key == glfw.KEY_R:
            camera.__init__()
            print("[input] Camera reset")

    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_key_callback(window, key_callback)

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.06, 0.12, 0.18, 1.0)

    shader = ShaderProgram(VERTEX_SHADER, FRAGMENT_SHADER)
    textures = TextureCache()
    objects = build_scene(textures)

    previous_time = glfw.get_time()
    while not glfw.window_should_close(window):
        current_time = glfw.get_time()
        dt = current_time - previous_time
        previous_time = current_time

        process_keyboard(window, camera, dt)

        width, height = glfw.get_framebuffer_size(window)
        aspect = width / max(height, 1)
        view = camera.view_matrix()
        projection = perspective(math.radians(60.0), aspect, 0.05, 240.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        shader.use()
        glUniformMatrix4fv(shader.uniforms["u_view"], 1, GL_TRUE, view)
        glUniformMatrix4fv(shader.uniforms["u_projection"], 1, GL_TRUE, projection)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if toggles.wireframe else GL_FILL)

        for scene_object in objects:
            scene_object.mesh.draw(shader, scene_object.model_matrix(current_time), textures.white_texture)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
