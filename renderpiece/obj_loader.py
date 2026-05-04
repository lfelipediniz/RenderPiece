from __future__ import annotations
import ctypes
import math
import time
from pathlib import Path

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FALSE,
    GL_FLOAT,
    GL_STATIC_DRAW,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glVertexAttribPointer,
)

from .config import IMAGE_EXTENSIONS
from .math3d import translate
from .mesh import Bounds, DrawBatch, GpuMesh, Material
from .textures import TextureCache


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
            if not line.strip():
                continue
            parts = line.split(None, 1)
            if parts and parts[0].lower() == "mtllib" and len(parts) > 1:
                mtl_files.append(obj_path.parent / parts[1].strip())

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
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            keyword = parts[0].lower()
            if keyword == "v":
                position = (float(parts[1]), float(parts[2]), float(parts[3]))
                positions.append(position)
                min_bound = np.minimum(min_bound, np.array(position, dtype=np.float32))
                max_bound = np.maximum(max_bound, np.array(position, dtype=np.float32))
            elif keyword == "vt":
                texcoords.append((float(parts[1]), float(parts[2])))
            elif keyword == "vn":
                normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif keyword == "usemtl":
                flush_batch()
                current_material = line.split(None, 1)[1].strip()
                material_for(current_material)
            elif keyword == "f":
                face_tokens = parts[1:]
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
