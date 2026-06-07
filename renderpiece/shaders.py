"""Programa de shader padrao usado pelos modelos da cena.

Projeto 3: aplica iluminacao ambiente, difusa e especular pelo pipeline
moderno. Os coeficientes de iluminacao sao enviados por objeto, nao lidos do
`.mtl`; o material do OBJ fica restrito a textura/tint visual.
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
out vec3 v_world_position;
out vec3 v_world_normal;

void main()
{
    v_texcoord = a_texcoord;

    vec4 world_position = u_model * vec4(a_position, 1.0);
    v_world_position = world_position.xyz;
    v_world_normal = mat3(transpose(inverse(u_model))) * a_normal;

    gl_Position = u_projection * u_view * world_position;
}
"""


FRAGMENT_SHADER = """
#version 330 core

in vec2 v_texcoord;
in vec3 v_world_position;
in vec3 v_world_normal;

uniform sampler2D u_texture;
uniform vec3 u_tint;

uniform vec3 u_camera_position;

uniform bool u_ambient_enabled;
uniform vec3 u_ambient_color;
uniform float u_ambient_strength;

uniform bool u_external_light_enabled;
uniform bool u_receives_external_light;
uniform vec3 u_external_light_position;
uniform vec3 u_external_light_color;
uniform float u_external_light_intensity;

uniform bool u_internal_light_enabled;
uniform bool u_receives_internal_light;
uniform vec3 u_internal_light_position;
uniform vec3 u_internal_light_color;
uniform float u_internal_light_intensity;

uniform float u_diffuse_strength;
uniform float u_specular_strength;

uniform vec3 u_material_ambient;
uniform vec3 u_material_diffuse;
uniform vec3 u_material_specular;
uniform float u_material_shininess;
uniform vec3 u_material_emissive;

uniform bool u_emissive_region_enabled;
uniform vec3 u_emissive_region_center;
uniform float u_emissive_region_radius;

out vec4 frag_color;

vec3 point_light(
    bool enabled,
    bool receives_light,
    vec3 light_position,
    vec3 light_color,
    float light_intensity,
    float attenuation_quadratic,
    vec3 albedo,
    vec3 normal
) {
    if (!enabled || !receives_light) {
        return vec3(0.0);
    }

    vec3 to_light = light_position - v_world_position;
    float distance_to_light = length(to_light);
    vec3 light_dir = normalize(to_light);
    vec3 view_dir = normalize(u_camera_position - v_world_position);
    vec3 halfway_dir = normalize(light_dir + view_dir);

    float attenuation = light_intensity /
        (1.0 + attenuation_quadratic * distance_to_light * distance_to_light);

    float diffuse_factor = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = albedo * u_material_diffuse * light_color *
        diffuse_factor * u_diffuse_strength;

    float specular_factor = pow(
        max(dot(normal, halfway_dir), 0.0),
        u_material_shininess
    );
    vec3 specular = u_material_specular * light_color *
        specular_factor * u_specular_strength;

    return (diffuse + specular) * attenuation;
}

void main()
{
    vec4 texel = texture(u_texture, v_texcoord);
    vec3 albedo = texel.rgb * u_tint;
    vec3 normal = normalize(v_world_normal);

    vec3 emissive = u_material_emissive;
    if (u_emissive_region_enabled) {
        float emissive_distance = length(v_world_position - u_emissive_region_center);
        float emissive_mask = 1.0 - smoothstep(
            u_emissive_region_radius * 0.45,
            u_emissive_region_radius,
            emissive_distance
        );
        emissive *= emissive_mask;
    }

    vec3 color = emissive;

    if (u_ambient_enabled) {
        color += albedo * u_material_ambient * u_ambient_color * u_ambient_strength;
    }

    color += point_light(
        u_external_light_enabled,
        u_receives_external_light,
        u_external_light_position,
        u_external_light_color,
        u_external_light_intensity,
        0.0015,
        albedo,
        normal
    );

    color += point_light(
        u_internal_light_enabled,
        u_receives_internal_light,
        u_internal_light_position,
        u_internal_light_color,
        u_internal_light_intensity,
        0.28,
        albedo,
        normal
    );

    frag_color = vec4(color, texel.a);
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
            "u_tint": glGetUniformLocation(self.program, "u_tint"),
            "u_camera_position": glGetUniformLocation(self.program, "u_camera_position"),
            "u_ambient_enabled": glGetUniformLocation(self.program, "u_ambient_enabled"),
            "u_ambient_color": glGetUniformLocation(self.program, "u_ambient_color"),
            "u_ambient_strength": glGetUniformLocation(self.program, "u_ambient_strength"),
            "u_external_light_enabled": glGetUniformLocation(self.program, "u_external_light_enabled"),
            "u_receives_external_light": glGetUniformLocation(self.program, "u_receives_external_light"),
            "u_external_light_position": glGetUniformLocation(self.program, "u_external_light_position"),
            "u_external_light_color": glGetUniformLocation(self.program, "u_external_light_color"),
            "u_external_light_intensity": glGetUniformLocation(self.program, "u_external_light_intensity"),
            "u_internal_light_enabled": glGetUniformLocation(self.program, "u_internal_light_enabled"),
            "u_receives_internal_light": glGetUniformLocation(self.program, "u_receives_internal_light"),
            "u_internal_light_position": glGetUniformLocation(self.program, "u_internal_light_position"),
            "u_internal_light_color": glGetUniformLocation(self.program, "u_internal_light_color"),
            "u_internal_light_intensity": glGetUniformLocation(self.program, "u_internal_light_intensity"),
            "u_diffuse_strength": glGetUniformLocation(self.program, "u_diffuse_strength"),
            "u_specular_strength": glGetUniformLocation(self.program, "u_specular_strength"),
            "u_material_ambient": glGetUniformLocation(self.program, "u_material_ambient"),
            "u_material_diffuse": glGetUniformLocation(self.program, "u_material_diffuse"),
            "u_material_specular": glGetUniformLocation(self.program, "u_material_specular"),
            "u_material_shininess": glGetUniformLocation(self.program, "u_material_shininess"),
            "u_material_emissive": glGetUniformLocation(self.program, "u_material_emissive"),
            "u_emissive_region_enabled": glGetUniformLocation(self.program, "u_emissive_region_enabled"),
            "u_emissive_region_center": glGetUniformLocation(self.program, "u_emissive_region_center"),
            "u_emissive_region_radius": glGetUniformLocation(self.program, "u_emissive_region_radius"),
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
