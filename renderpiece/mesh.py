from __future__ import annotations
import ctypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TRIANGLES,
    GL_TRUE,
    GL_UNSIGNED_INT,
    glActiveTexture,
    glBindTexture,
    glBindVertexArray,
    glDrawElements,
    glUniform1i,
    glUniform3f,
    glUniformMatrix4fv,
)

if TYPE_CHECKING:
    from .shaders import ShaderProgram


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
        shader: ShaderProgram,
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

