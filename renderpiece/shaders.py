"""Programa de shader padrao usado pelos modelos da cena

Apenas amostra a textura difusa e multiplica pela cor `Kd` do material
Nao ha calculo de iluminacao, conforme requisito 12 do projeto
"""

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_VERTEX_SHADER,
    glAttachShader,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glUseProgram,
)


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

