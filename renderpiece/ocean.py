"""Oceano animado para o ambiente externo.

Atende ao requisito 1 do projeto (o ambiente externo cita "oceano" como exemplo)
e ao requisito 6 (todo ambiente externo deve ter piso/chão; aqui o piso é a
superfície do mar, distinto do piso interno do navio)

Implementação:
  - Um plano grande é tesselado em uma malha regular de vértices, gerada com
    numpy e enviada para a GPU em um único VAO/VBO/EBO.
  - Um shader dedicado desloca cada vértice no eixo Y somando algumas senóides
    direcionais animadas pelo tempo, criando ondas em movimento.
  - Projeto 3: a agua tem parametros proprios de reflexao ambiente/difusa/
    especular e recebe somente a fonte luminosa externa.
"""

from __future__ import annotations

import ctypes

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COMPILE_STATUS,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FALSE,
    GL_FILL,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FRONT_AND_BACK,
    GL_LINE,
    GL_LINK_STATUS,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_TRUE,
    GL_UNSIGNED_INT,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glDrawElements,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glPolygonMode,
    glShaderSource,
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
)

from .lighting import EXTERNAL_LIGHT_INTENSITY, LightingProfile, LightingState


OCEAN_VERTEX_SHADER = """
#version 330 core

layout (location = 0) in vec3 a_position;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_time;

out float v_height;
out vec3 v_world_position;
out vec3 v_world_normal;

// Soma de uma onda senoidal direcional. `dir` é unitário, `wavelength` em
// unidades de mundo, `amp` em unidades de mundo, `speed` em rad/s.
float wave(vec2 pos, vec2 dir, float wavelength, float amp, float speed, float t)
{
    float k = 6.2831853 / wavelength;
    return amp * sin(dot(pos, dir) * k - speed * t);
}

vec2 wave_slope(vec2 pos, vec2 dir, float wavelength, float amp, float speed, float t)
{
    float k = 6.2831853 / wavelength;
    float phase = dot(pos, dir) * k - speed * t;
    return amp * k * cos(phase) * dir;
}

void main()
{
    vec4 world = u_model * vec4(a_position, 1.0);

    // Várias ondas em direções diferentes para evitar padrões óbvios.
    float h = 0.0;
    vec2 slope = vec2(0.0);

    vec2 d0 = normalize(vec2( 1.00,  0.35));
    vec2 d1 = normalize(vec2(-0.40,  1.00));
    vec2 d2 = normalize(vec2( 0.70, -0.80));
    vec2 d3 = normalize(vec2(-0.95, -0.20));

    h += wave(world.xz, d0, 22.0, 0.45, 0.55, u_time);
    h += wave(world.xz, d1, 13.0, 0.22, 0.85, u_time);
    h += wave(world.xz, d2,  7.5, 0.10, 1.30, u_time);
    h += wave(world.xz, d3,  4.5, 0.05, 1.80, u_time);

    slope += wave_slope(world.xz, d0, 22.0, 0.45, 0.55, u_time);
    slope += wave_slope(world.xz, d1, 13.0, 0.22, 0.85, u_time);
    slope += wave_slope(world.xz, d2,  7.5, 0.10, 1.30, u_time);
    slope += wave_slope(world.xz, d3,  4.5, 0.05, 1.80, u_time);

    world.y += h;
    v_height = h;
    v_world_position = world.xyz;
    v_world_normal = normalize(vec3(-slope.x, 1.0, -slope.y));

    gl_Position = u_projection * u_view * world;
}
"""


OCEAN_FRAGMENT_SHADER = """
#version 330 core

in float v_height;
in vec3 v_world_position;
in vec3 v_world_normal;

uniform vec3 u_camera_position;

uniform bool u_ambient_enabled;
uniform vec3 u_ambient_color;
uniform float u_ambient_strength;

uniform bool u_external_light_enabled;
uniform vec3 u_external_light_position;
uniform vec3 u_external_light_color;
uniform float u_external_light_intensity;

uniform float u_diffuse_strength;
uniform float u_specular_strength;

uniform vec3 u_material_ambient;
uniform vec3 u_material_diffuse;
uniform vec3 u_material_specular;
uniform float u_material_shininess;

out vec4 frag_color;

void main()
{
    vec3 base  = vec3(0.070, 0.32, 0.52);
    vec3 crest = vec3(0.78, 0.92, 0.98);

    float crest_strength = smoothstep(0.55, 0.80, v_height) * 0.35;
    vec3 albedo = mix(base, crest, crest_strength);

    vec3 normal = normalize(v_world_normal);
    vec3 color = vec3(0.0);

    if (u_ambient_enabled) {
        color += albedo * u_material_ambient * u_ambient_color * u_ambient_strength;
    }

    if (u_external_light_enabled) {
        vec3 to_light = u_external_light_position - v_world_position;
        float distance_to_light = length(to_light);
        vec3 light_dir = normalize(to_light);
        vec3 view_dir = normalize(u_camera_position - v_world_position);
        vec3 halfway_dir = normalize(light_dir + view_dir);

        float attenuation = u_external_light_intensity /
            (1.0 + 0.0010 * distance_to_light * distance_to_light);

        float diffuse_factor = max(dot(normal, light_dir), 0.0);
        vec3 diffuse = albedo * u_material_diffuse * u_external_light_color *
            diffuse_factor * u_diffuse_strength;

        float specular_factor = pow(
            max(dot(normal, halfway_dir), 0.0),
            u_material_shininess
        );
        vec3 specular = u_material_specular * u_external_light_color *
            specular_factor * u_specular_strength;

        color += (diffuse + specular) * attenuation;
    }

    frag_color = vec4(color, 1.0);
}
"""


OCEAN_LIGHTING = LightingProfile(
    ambient=(0.45, 0.60, 0.68),
    diffuse=(0.64, 0.78, 0.88),
    specular=(0.82, 0.92, 1.00),
    shininess=96.0,
)


def _compile_shader(shader_type: int, source: str) -> int:
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader).decode("utf-8"))
    return shader


def _build_grid(half_size: float, divisions: int) -> tuple[np.ndarray, np.ndarray]:
    """Constrói um plano XZ centrado na origem, com `(divisions + 1)^2` vértices.

    Retorna `(positions, indices)`. As posições têm Y=0; o deslocamento das ondas
    é aplicado no vertex shader.
    """
    coords = np.linspace(-half_size, half_size, divisions + 1, dtype=np.float32)
    xs, zs = np.meshgrid(coords, coords, indexing="xy")
    positions = np.stack([xs, np.zeros_like(xs), zs], axis=-1).reshape(-1, 3)

    # Índices dos triângulos (dois por célula da grade).
    n = divisions + 1
    i = np.arange(divisions, dtype=np.uint32)
    j = np.arange(divisions, dtype=np.uint32)
    jj, ii = np.meshgrid(j, i, indexing="xy")
    a = (ii * n + jj).ravel()
    b = (ii * n + jj + 1).ravel()
    c = ((ii + 1) * n + jj).ravel()
    d = ((ii + 1) * n + jj + 1).ravel()
    # Dois triângulos por quad: (a, c, b) e (b, c, d).
    tris = np.empty((a.size * 6,), dtype=np.uint32)
    tris[0::6] = a
    tris[1::6] = c
    tris[2::6] = b
    tris[3::6] = b
    tris[4::6] = c
    tris[5::6] = d

    return positions.astype(np.float32), tris


class Ocean:
    """Encapsula geometria, shader e desenho da superfície do oceano."""

    def __init__(self, half_size: float = 320.0, divisions: int = 240, surface_y: float = 0.0) -> None:
        self.surface_y = float(surface_y)

        positions, indices = _build_grid(half_size, divisions)
        self.index_count = int(indices.size)

        self.program = self._build_program()
        self.vao, self.vbo, self.ebo = self._build_buffers(positions, indices)

        self._u_model = glGetUniformLocation(self.program, "u_model")
        self._u_view = glGetUniformLocation(self.program, "u_view")
        self._u_projection = glGetUniformLocation(self.program, "u_projection")
        self._u_time = glGetUniformLocation(self.program, "u_time")
        self._u_camera_position = glGetUniformLocation(self.program, "u_camera_position")
        self._u_ambient_enabled = glGetUniformLocation(self.program, "u_ambient_enabled")
        self._u_ambient_color = glGetUniformLocation(self.program, "u_ambient_color")
        self._u_ambient_strength = glGetUniformLocation(self.program, "u_ambient_strength")
        self._u_external_light_enabled = glGetUniformLocation(self.program, "u_external_light_enabled")
        self._u_external_light_position = glGetUniformLocation(self.program, "u_external_light_position")
        self._u_external_light_color = glGetUniformLocation(self.program, "u_external_light_color")
        self._u_external_light_intensity = glGetUniformLocation(self.program, "u_external_light_intensity")
        self._u_diffuse_strength = glGetUniformLocation(self.program, "u_diffuse_strength")
        self._u_specular_strength = glGetUniformLocation(self.program, "u_specular_strength")
        self._u_material_ambient = glGetUniformLocation(self.program, "u_material_ambient")
        self._u_material_diffuse = glGetUniformLocation(self.program, "u_material_diffuse")
        self._u_material_specular = glGetUniformLocation(self.program, "u_material_specular")
        self._u_material_shininess = glGetUniformLocation(self.program, "u_material_shininess")

        # O modelo é simplesmente uma translação para a linha d'água.
        model = np.identity(4, dtype=np.float32)
        model[1, 3] = self.surface_y
        self._model = model

    @staticmethod
    def _build_program() -> int:
        vertex = _compile_shader(GL_VERTEX_SHADER, OCEAN_VERTEX_SHADER)
        fragment = _compile_shader(GL_FRAGMENT_SHADER, OCEAN_FRAGMENT_SHADER)
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
    def _build_buffers(positions: np.ndarray, indices: np.ndarray) -> tuple[int, int, int]:
        vao = int(glGenVertexArrays(1))
        vbo = int(glGenBuffers(1))
        ebo = int(glGenBuffers(1))

        glBindVertexArray(vao)

        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glBindVertexArray(0)
        return vao, vbo, ebo

    def draw(
        self,
        view: np.ndarray,
        projection: np.ndarray,
        time_seconds: float,
        wireframe: bool,
        lighting: LightingState,
        camera_position: np.ndarray,
        external_light_position: np.ndarray,
    ) -> None:
        """Desenha o oceano. Deve ser chamado depois dos objetos opacos da cena
        e antes do skybox (para que o skybox preencha apenas o que sobrar)."""
        glUseProgram(self.program)

        # Acompanha o modo wireframe global (tecla P) — assim a malha do oceano
        # também aparece quando o usuário pedir para inspecionar a geometria.
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)

        glUniformMatrix4fv(self._u_model, 1, GL_TRUE, self._model)
        glUniformMatrix4fv(self._u_view, 1, GL_TRUE, view)
        glUniformMatrix4fv(self._u_projection, 1, GL_TRUE, projection)
        glUniform1f(self._u_time, float(time_seconds))
        glUniform3f(self._u_camera_position, *camera_position)

        glUniform1i(self._u_ambient_enabled, int(lighting.ambient_enabled))
        glUniform3f(self._u_ambient_color, 0.95, 0.98, 1.00)
        glUniform1f(self._u_ambient_strength, lighting.ambient_strength)

        glUniform1i(self._u_external_light_enabled, int(lighting.external_light_enabled))
        glUniform3f(self._u_external_light_position, *external_light_position)
        glUniform3f(self._u_external_light_color, 1.00, 0.86, 0.54)
        glUniform1f(self._u_external_light_intensity, EXTERNAL_LIGHT_INTENSITY)

        glUniform1f(self._u_diffuse_strength, lighting.diffuse_strength)
        glUniform1f(self._u_specular_strength, lighting.specular_strength)
        glUniform3f(self._u_material_ambient, *OCEAN_LIGHTING.ambient)
        glUniform3f(self._u_material_diffuse, *OCEAN_LIGHTING.diffuse)
        glUniform3f(self._u_material_specular, *OCEAN_LIGHTING.specular)
        glUniform1f(self._u_material_shininess, OCEAN_LIGHTING.shininess)

        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        glBindVertexArray(0)
