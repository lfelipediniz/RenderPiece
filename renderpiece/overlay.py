"""HUD 2D em coordenadas normalizadas de tela (NDC)

Inclui o `PauseOverlay` (escurece a tela e escreve "PAUSED" quando ESC
pausa o jogo) e o `MutedIndicator` (badge vermelho com "MUTED" no canto
superior direito quando a musica esta silenciada com M). A fonte e
gerada por software a partir de uma tabela 5x7 de bits em `_GLYPHS`
"""

import ctypes
import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_BLEND,
    GL_COMPILE_STATUS,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FALSE,
    GL_LINK_STATUS,
    GL_NEAREST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_RED,
    GL_SRC_ALPHA,
    GL_STATIC_DRAW,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TRIANGLES,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBindBuffer,
    glBindTexture,
    glBindVertexArray,
    glBlendFunc,
    glBufferData,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glDisable,
    glDrawArrays,
    glEnable,
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
    glShaderSource,
    glTexImage2D,
    glTexParameteri,
    glUniform4f,
    glUseProgram,
    glVertexAttribPointer,
)

_OVERLAY_VS = """
#version 330 core
layout (location = 0) in vec2 a_position;
layout (location = 1) in vec2 a_texcoord;
out vec2 v_texcoord;
void main() {
    v_texcoord = a_texcoord;
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

_OVERLAY_FS = """
#version 330 core
in vec2 v_texcoord;
uniform vec4 u_color;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() {
    float a = texture(u_texture, v_texcoord).r;
    frag_color = vec4(u_color.rgb, u_color.a * a);
}
"""

_GLYPHS = {
    "P": [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    "A": [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "U": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "S": [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    "E": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    "D": [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    "M": [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    "T": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
}


def _make_text_bitmap(text: str) -> tuple[bytes, int, int]:
    char_w, char_h, gap = 5, 7, 2
    w = len(text) * (char_w + gap) - gap
    h = char_h
    buf = bytearray(w * h)
    for ci, ch in enumerate(text):
        glyph = _GLYPHS.get(ch)
        if glyph is None:
            continue
        x0 = ci * (char_w + gap)
        for row in range(char_h):
            for col in range(char_w):
                if glyph[row] & (1 << (char_w - 1 - col)):
                    buf[row * w + x0 + col] = 255
    return bytes(buf), w, h


def _quad_vao(x0: float, y0: float, x1: float, y1: float) -> int:
    vertices = np.array(
        [
            x0, y0, 0.0, 1.0,
            x1, y0, 1.0, 1.0,
            x1, y1, 1.0, 0.0,
            x0, y0, 0.0, 1.0,
            x1, y1, 1.0, 0.0,
            x0, y1, 0.0, 0.0,
        ],
        dtype=np.float32,
    )
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    stride = 4 * 4
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
    glBindVertexArray(0)
    return vao


def _compile_shader(shader_type: int, source: str) -> int:
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    return shader


class PauseOverlay:
    def __init__(self, window_w: int = 1280, window_h: int = 720) -> None:
        vs = _compile_shader(GL_VERTEX_SHADER, _OVERLAY_VS)
        fs = _compile_shader(GL_FRAGMENT_SHADER, _OVERLAY_FS)
        self._program = glCreateProgram()
        glAttachShader(self._program, vs)
        glAttachShader(self._program, fs)
        glLinkProgram(self._program)
        if not glGetProgramiv(self._program, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(self._program).decode())
        glDeleteShader(vs)
        glDeleteShader(fs)

        self._u_color = glGetUniformLocation(self._program, "u_color")

        self._fs_vao = _quad_vao(-1.0, -1.0, 1.0, 1.0)

        self._white_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._white_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 1, 1, 0, GL_RED, GL_UNSIGNED_BYTE, b"\xff")
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        data, tw, th = _make_text_bitmap("PAUSED")
        self._text_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._text_tex)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, tw, th, 0, GL_RED, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        half_h = 0.06
        half_w = half_h * (tw / th) * (window_h / window_w)
        self._text_vao = _quad_vao(-half_w, -half_h, half_w, half_h)

    def draw(self) -> None:
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(self._program)

        glBindTexture(GL_TEXTURE_2D, self._white_tex)
        glUniform4f(self._u_color, 0.0, 0.0, 0.0, 0.5)
        glBindVertexArray(self._fs_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glBindTexture(GL_TEXTURE_2D, self._text_tex)
        glUniform4f(self._u_color, 1.0, 1.0, 1.0, 1.0)
        glBindVertexArray(self._text_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glBindVertexArray(0)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)


class MutedIndicator:
    """Pequeno badge no canto superior direito mostrando 'MUTED'."""

    def __init__(self, window_w: int = 1280, window_h: int = 720) -> None:
        vs = _compile_shader(GL_VERTEX_SHADER, _OVERLAY_VS)
        fs = _compile_shader(GL_FRAGMENT_SHADER, _OVERLAY_FS)
        self._program = glCreateProgram()
        glAttachShader(self._program, vs)
        glAttachShader(self._program, fs)
        glLinkProgram(self._program)
        if not glGetProgramiv(self._program, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(self._program).decode())
        glDeleteShader(vs)
        glDeleteShader(fs)

        self._u_color = glGetUniformLocation(self._program, "u_color")

        self._white_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._white_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 1, 1, 0, GL_RED, GL_UNSIGNED_BYTE, b"\xff")
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        data, tw, th = _make_text_bitmap("MUTED")
        self._text_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._text_tex)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, tw, th, 0, GL_RED, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        text_h = 0.05
        text_w = text_h * (tw / th) * (window_h / window_w)
        right = 0.97
        top = 0.95
        text_x0 = right - text_w
        text_y0 = top - text_h
        self._text_vao = _quad_vao(text_x0, text_y0, right, top)

        pad_x = 0.02 * (window_h / window_w)
        pad_y = 0.015
        self._bg_vao = _quad_vao(
            text_x0 - pad_x,
            text_y0 - pad_y,
            right + pad_x,
            top + pad_y,
        )

    def draw(self) -> None:
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(self._program)

        glBindTexture(GL_TEXTURE_2D, self._white_tex)
        glUniform4f(self._u_color, 0.7, 0.05, 0.05, 0.85)
        glBindVertexArray(self._bg_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glBindTexture(GL_TEXTURE_2D, self._text_tex)
        glUniform4f(self._u_color, 1.0, 1.0, 1.0, 1.0)
        glBindVertexArray(self._text_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glBindVertexArray(0)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
