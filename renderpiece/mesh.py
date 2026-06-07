"""Estruturas de geometria/material residentes na GPU

`GpuMesh` segura o trio VAO/VBO/EBO de um modelo, sua lista de `DrawBatch`
(um trecho de indices por material) e os `Material`s ja resolvidos. O
`draw` faz um `glDrawElements` por batch, trocando textura/`u_tint` e
enviando os parametros de iluminacao do objeto.
"""

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
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUniformMatrix4fv,
)

if TYPE_CHECKING:
    from .lighting import LightingProfile
    from .shaders import ShaderProgram


@dataclass
class Material:
    name: str
    diffuse: tuple[float, float, float] = (1.0, 1.0, 1.0)
    emissive: tuple[float, float, float] = (0.0, 0.0, 0.0)
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
    batches: list[DrawBatch]
    materials: dict[str, Material]
    bounds: Bounds
    anchor_to_base: np.ndarray = field(default_factory=lambda: np.identity(4, dtype=np.float32))

    def draw(
        self,
        shader: ShaderProgram,
        model_matrix: np.ndarray,
        white_texture: int,
        lighting: LightingProfile,
        receives_external_light: bool,
        receives_internal_light: bool,
        emissive: tuple[float, float, float] | None = None,
        emissive_region: tuple[tuple[float, float, float], float] | None = None,
        material_emissive_scale: float = 1.0,
    ) -> None:
        if emissive is None:
            emissive = lighting.emissive

        glUniformMatrix4fv(shader.uniforms["u_model"], 1, GL_TRUE, model_matrix)
        glUniform3f(shader.uniforms["u_material_ambient"], *lighting.ambient)
        glUniform3f(shader.uniforms["u_material_diffuse"], *lighting.diffuse)
        glUniform3f(shader.uniforms["u_material_specular"], *lighting.specular)
        glUniform1f(shader.uniforms["u_material_shininess"], lighting.shininess)
        glUniform1i(shader.uniforms["u_receives_external_light"], int(receives_external_light))
        glUniform1i(shader.uniforms["u_receives_internal_light"], int(receives_internal_light))

        if emissive_region is None:
            glUniform1i(shader.uniforms["u_emissive_region_enabled"], 0)
            glUniform3f(shader.uniforms["u_emissive_region_center"], 0.0, 0.0, 0.0)
            glUniform1f(shader.uniforms["u_emissive_region_radius"], 0.0)
        else:
            center, radius = emissive_region
            glUniform1i(shader.uniforms["u_emissive_region_enabled"], 1)
            glUniform3f(shader.uniforms["u_emissive_region_center"], *center)
            glUniform1f(shader.uniforms["u_emissive_region_radius"], radius)

        glBindVertexArray(self.vao)

        for batch in self.batches:
            material = self.materials.get(batch.material_name) or self.materials["default"]
            texture_id = material.texture_id or white_texture

            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glUniform1i(shader.uniforms["u_texture"], 0)
            glUniform3f(shader.uniforms["u_tint"], *material.diffuse)
            material_emissive = tuple(channel * material_emissive_scale for channel in material.emissive)
            batch_emissive = tuple(emissive[index] + material_emissive[index] for index in range(3))
            glUniform3f(shader.uniforms["u_material_emissive"], *batch_emissive)

            byte_offset = ctypes.c_void_p(batch.start_index * np.dtype(np.uint32).itemsize)
            glDrawElements(GL_TRIANGLES, batch.index_count, GL_UNSIGNED_INT, byte_offset)

        glBindVertexArray(0)
