"""SkyBox via cubemap procedural.

Atende ao requisito 8 do projeto: o ambiente externo possui um céu com textura.
Implementação seguindo o pipeline moderno (sem chamadas obsoletas):
  - Cubemap (GL_TEXTURE_CUBE_MAP) com 6 faces geradas proceduralmente em numpy,
    de modo que o gradiente é contínuo entre as faces (sem costuras).
  - Shader dedicado que remove a translação da matriz view, fazendo o céu
    ficar sempre centrado na câmera, e força gl_Position = clip.xyww para que
    o céu seja desenhado no plano distante (depth = 1.0).
  - Renderizado depois dos objetos opacos com glDepthFunc(GL_LEQUAL) para
    que o early-z descarte os pixels já cobertos pela cena (otimização).
"""

from __future__ import annotations

import ctypes

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_CLAMP_TO_EDGE,
    GL_COMPILE_STATUS,
    GL_FALSE,
    GL_FILL,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FRONT_AND_BACK,
    GL_LEQUAL,
    GL_LESS,
    GL_LINEAR,
    GL_LINK_STATUS,
    GL_RGB,
    GL_STATIC_DRAW,
    GL_TEXTURE0,
    GL_TEXTURE_CUBE_MAP,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_R,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TRIANGLES,
    GL_TRUE,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    GL_VERTEX_SHADER,
    glActiveTexture,
    glAttachShader,
    glBindBuffer,
    glBindTexture,
    glBindVertexArray,
    glBufferData,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glDepthFunc,
    glDrawArrays,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenTextures,
    glGenVertexArrays,
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
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
)


SKYBOX_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 a_position;

uniform mat4 u_view;
uniform mat4 u_projection;

out vec3 v_direction;

void main()
{
    v_direction = a_position;

    // Remove a translação do view (mantém só a rotação) para que o céu
    // permaneça centrado na câmera, dando a impressão de estar no infinito.
    mat4 view_no_translation = mat4(mat3(u_view));

    vec4 clip = u_projection * view_no_translation * vec4(a_position, 1.0);

    // gl_Position.z = w faz com que após a divisão perspectiva (z/w) o depth
    // valha 1.0 (plano distante). Combinado com glDepthFunc(GL_LEQUAL),
    // o céu é desenhado apenas onde nada foi escrito antes.
    gl_Position = clip.xyww;
}
"""


SKYBOX_FRAGMENT_SHADER = """
#version 330 core

in vec3 v_direction;

uniform samplerCube u_cubemap;

out vec4 frag_color;

void main()
{
    frag_color = texture(u_cubemap, v_direction);
}
"""


_SKYBOX_VERTICES = np.array(
    [
        # +X
         1.0, -1.0, -1.0,   1.0,  1.0, -1.0,   1.0,  1.0,  1.0,
         1.0, -1.0, -1.0,   1.0,  1.0,  1.0,   1.0, -1.0,  1.0,
        # -X
        -1.0, -1.0,  1.0,  -1.0,  1.0,  1.0,  -1.0,  1.0, -1.0,
        -1.0, -1.0,  1.0,  -1.0,  1.0, -1.0,  -1.0, -1.0, -1.0,
        # +Y
        -1.0,  1.0, -1.0,  -1.0,  1.0,  1.0,   1.0,  1.0,  1.0,
        -1.0,  1.0, -1.0,   1.0,  1.0,  1.0,   1.0,  1.0, -1.0,
        # -Y
        -1.0, -1.0,  1.0,  -1.0, -1.0, -1.0,   1.0, -1.0, -1.0,
        -1.0, -1.0,  1.0,   1.0, -1.0, -1.0,   1.0, -1.0,  1.0,
        # +Z
         1.0, -1.0,  1.0,   1.0,  1.0,  1.0,  -1.0,  1.0,  1.0,
         1.0, -1.0,  1.0,  -1.0,  1.0,  1.0,  -1.0, -1.0,  1.0,
        # -Z
        -1.0, -1.0, -1.0,  -1.0,  1.0, -1.0,   1.0,  1.0, -1.0,
        -1.0, -1.0, -1.0,   1.0,  1.0, -1.0,   1.0, -1.0, -1.0,
    ],
    dtype=np.float32,
)


def _face_directions(face_index: int, size: int) -> np.ndarray:
    """Calcula vetores de direção 3D para cada texel de uma face do cubemap.

    Segue a convenção de orientação do OpenGL para cubemaps (a primeira linha
    enviada via glTexImage2D corresponde ao topo da face).
    """
    coords = np.linspace(-1.0, 1.0, size, dtype=np.float32)
    u, v = np.meshgrid(coords, coords)
    ones = np.ones_like(u)

    if face_index == 0:  # +X
        return np.stack([ones, -v, -u], axis=-1)
    if face_index == 1:  # -X
        return np.stack([-ones, -v, u], axis=-1)
    if face_index == 2:  # +Y
        return np.stack([u, ones, v], axis=-1)
    if face_index == 3:  # -Y
        return np.stack([u, -ones, -v], axis=-1)
    if face_index == 4:  # +Z
        return np.stack([u, -v, ones], axis=-1)
    if face_index == 5:  # -Z
        return np.stack([-u, -v, -ones], axis=-1)
    raise ValueError(f"Face inválida: {face_index}")


def _sky_color(directions: np.ndarray) -> np.ndarray:
    """Atribui uma cor RGB (em [0, 1]) a cada direção 3D normalizada.

    A cor depende apenas da direção, então o gradiente é contínuo entre faces.
    """
    norms = np.linalg.norm(directions, axis=-1, keepdims=True)
    norms = np.maximum(norms, 1e-8)
    dirs = directions / norms

    y = dirs[..., 1:2]

    zenith = np.array([0.18, 0.42, 0.80], dtype=np.float32)
    horizon = np.array([0.78, 0.88, 0.97], dtype=np.float32)
    ocean = np.array([0.04, 0.18, 0.38], dtype=np.float32)

    above = y > 0.0
    t_above = np.clip(y, 0.0, 1.0)
    t_below = np.clip(-y, 0.0, 1.0)

    upper = horizon + (zenith - horizon) * (t_above ** 0.7)
    lower = horizon + (ocean - horizon) * (t_below ** 0.6)
    color = np.where(above, upper, lower)

    return np.clip(color, 0.0, 1.0)


def _generate_face(face_index: int, size: int) -> bytes:
    directions = _face_directions(face_index, size)
    rgb = _sky_color(directions)
    return (rgb * 255.0).astype(np.uint8).tobytes()


def _compile_shader(shader_type: int, source: str) -> int:
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader).decode("utf-8"))
    return shader


class SkyBox:
    """Encapsula o cubemap, a geometria do cubo e o shader do céu."""

    def __init__(self, face_size: int = 256) -> None:
        self.cubemap = self._build_cubemap(face_size)
        self.program = self._build_program()
        self.vao, self.vbo = self._build_geometry()

        self._u_view = glGetUniformLocation(self.program, "u_view")
        self._u_projection = glGetUniformLocation(self.program, "u_projection")
        self._u_cubemap = glGetUniformLocation(self.program, "u_cubemap")

    @staticmethod
    def _build_cubemap(face_size: int) -> int:
        cubemap = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_CUBE_MAP, cubemap)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        face_targets = (
            GL_TEXTURE_CUBE_MAP_POSITIVE_X,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
            GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
            GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
        )
        for face_index, target in enumerate(face_targets):
            data = _generate_face(face_index, face_size)
            glTexImage2D(
                target,
                0,
                GL_RGB,
                face_size,
                face_size,
                0,
                GL_RGB,
                GL_UNSIGNED_BYTE,
                data,
            )

        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
        return cubemap

    @staticmethod
    def _build_program() -> int:
        vertex = _compile_shader(GL_VERTEX_SHADER, SKYBOX_VERTEX_SHADER)
        fragment = _compile_shader(GL_FRAGMENT_SHADER, SKYBOX_FRAGMENT_SHADER)
        program = glCreateProgram()
        glAttachShader(program, vertex)
        glAttachShader(program, fragment)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(program).decode("utf-8"))
        glDeleteShader(vertex)
        glDeleteShader(fragment)
        return program

    @staticmethod
    def _build_geometry() -> tuple[int, int]:
        vao = int(glGenVertexArrays(1))
        vbo = int(glGenBuffers(1))
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            _SKYBOX_VERTICES.nbytes,
            _SKYBOX_VERTICES,
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        glBindVertexArray(0)
        return vao, vbo

    def draw(self, view: np.ndarray, projection: np.ndarray) -> None:
        """Desenha o céu. Deve ser chamado depois dos objetos opacos da cena."""
        # O céu sempre deve ser preenchido (mesmo no modo wireframe dos modelos)
        # para não atrapalhar a leitura visual do horizonte.
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glDepthFunc(GL_LEQUAL)
        glUseProgram(self.program)
        glUniformMatrix4fv(self._u_view, 1, GL_TRUE, view)
        glUniformMatrix4fv(self._u_projection, 1, GL_TRUE, projection)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.cubemap)
        glUniform1i(self._u_cubemap, 0)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 36)
        glBindVertexArray(0)

        glDepthFunc(GL_LESS)
