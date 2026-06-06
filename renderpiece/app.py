"""Loop principal: inicializa GLFW + OpenGL, monta a cena e desenha.

Ordem de desenho por frame: limpa color/depth, desenha os modelos da cena
(cada `SceneObject` com sua matriz de modelo), depois o oceano (que usa
o depth ja preenchido) e por fim o skybox com `glDepthFunc(GL_LEQUAL)`
para preencher so o que sobrou. Overlays 2D vem por ultimo (sem depth)

Mapa de teclas:
  WASD/Space/Shift -> camera; Mouse -> olhar;
  P -> wireframe; R -> reseta camera; M -> muta musica; ESC -> pausa
  L -> liga/desliga fonte externa (sol); I -> liga/desliga luz ambiente
  Z/X -> decrementa/incrementa ambiente
  C/V -> decrementa/incrementa reflexao difusa
  B/N -> decrementa/incrementa reflexao especular
  J/K -> translada o sol manualmente em torno do navio
"""

import math
import glfw
import numpy as np
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FILL,
    GL_FRONT_AND_BACK,
    GL_LINE,
    GL_TRUE,
    glClear,
    glClearColor,
    glEnable,
    glPolygonMode,
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUniformMatrix4fv,
    glViewport,
)

from .audio import BackgroundMusic
from .camera import Camera
from .config import ASSET_ROOT, OCEAN_Y, WINDOW_HEIGHT, WINDOW_WIDTH
from .lighting import EXTERNAL_LIGHT_INTENSITY, LightingState, sun_light_position
from .math3d import normalize, perspective
from .ocean import Ocean
from .overlay import MutedIndicator, PauseOverlay
from .scene import build_scene
from .shaders import FRAGMENT_SHADER, VERTEX_SHADER, ShaderProgram
from .skybox import SkyBox
from .state import Toggles
from .textures import TextureCache

LIGHT_ADJUST_SPEED = 0.55
SUN_TRANSLATION_SPEED = math.radians(38.0)

BACKGROUND_MUSIC_PATH = ASSET_ROOT / "audio/One Piece - Bink's Sake _ Piano [SeDyYtIuhsA].mp3"


def framebuffer_size_callback(_window: glfw._GLFWwindow, width: int, height: int) -> None:
    glViewport(0, 0, width, height)


def process_keyboard(
    window: glfw._GLFWwindow,
    camera: Camera,
    lighting: LightingState,
    dt: float,
) -> None:
    velocity = camera.speed * dt

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
    if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
        camera.move(-camera.world_up, velocity)

    if glfw.get_key(window, glfw.KEY_Z) == glfw.PRESS:
        lighting.adjust_ambient(-LIGHT_ADJUST_SPEED * dt)
    if glfw.get_key(window, glfw.KEY_X) == glfw.PRESS:
        lighting.adjust_ambient(LIGHT_ADJUST_SPEED * dt)
    if glfw.get_key(window, glfw.KEY_C) == glfw.PRESS:
        lighting.adjust_diffuse(-LIGHT_ADJUST_SPEED * dt)
    if glfw.get_key(window, glfw.KEY_V) == glfw.PRESS:
        lighting.adjust_diffuse(LIGHT_ADJUST_SPEED * dt)
    if glfw.get_key(window, glfw.KEY_B) == glfw.PRESS:
        lighting.adjust_specular(-LIGHT_ADJUST_SPEED * dt)
    if glfw.get_key(window, glfw.KEY_N) == glfw.PRESS:
        lighting.adjust_specular(LIGHT_ADJUST_SPEED * dt)
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        lighting.translate_sun(-SUN_TRANSLATION_SPEED * dt)
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        lighting.translate_sun(SUN_TRANSLATION_SPEED * dt)


def upload_lighting_uniforms(
    shader: ShaderProgram,
    lighting: LightingState,
    camera_position: np.ndarray,
    external_light_position: np.ndarray,
) -> None:
    glUniform3f(shader.uniforms["u_camera_position"], *camera_position)

    glUniform1i(shader.uniforms["u_ambient_enabled"], int(lighting.ambient_enabled))
    glUniform3f(shader.uniforms["u_ambient_color"], 0.95, 0.98, 1.00)
    glUniform1f(shader.uniforms["u_ambient_strength"], lighting.ambient_strength)

    glUniform1i(shader.uniforms["u_external_light_enabled"], int(lighting.external_light_enabled))
    glUniform3f(shader.uniforms["u_external_light_position"], *external_light_position)
    glUniform3f(shader.uniforms["u_external_light_color"], 1.00, 0.86, 0.54)
    glUniform1f(shader.uniforms["u_external_light_intensity"], EXTERNAL_LIGHT_INTENSITY)

    glUniform1f(shader.uniforms["u_diffuse_strength"], lighting.diffuse_strength)
    glUniform1f(shader.uniforms["u_specular_strength"], lighting.specular_strength)


def init_window() -> glfw._GLFWwindow:
    if not glfw.init():
        raise RuntimeError("Could not initialize GLFW")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Render Piece - Projeto 3", None, None)
    if window is None:
        glfw.terminate()
        raise RuntimeError("Could not create GLFW window")

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    return window


def run() -> None:
    camera = Camera()
    toggles = Toggles()
    lighting = LightingState()
    window = init_window()
    music = BackgroundMusic(BACKGROUND_MUSIC_PATH)

    def mouse_callback(_window: glfw._GLFWwindow, xpos: float, ypos: float) -> None:
        if toggles.paused:
            return
        camera.process_mouse(xpos, ypos)

    def key_callback(window_handle: glfw._GLFWwindow, key: int, _scancode: int, action: int, _mods: int) -> None:
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_ESCAPE:
            toggles.paused = not toggles.paused
            if toggles.paused:
                glfw.set_input_mode(window_handle, glfw.CURSOR, glfw.CURSOR_NORMAL)
                music.pause()
                print("[input] Paused")
            else:
                glfw.set_input_mode(window_handle, glfw.CURSOR, glfw.CURSOR_DISABLED)
                camera.first_mouse = True
                music.resume()
                print("[input] Unpaused")
        elif key == glfw.KEY_P:
            toggles.wireframe = not toggles.wireframe
            print(f"[input] Wireframe: {toggles.wireframe}")
        elif key == glfw.KEY_R:
            camera.reset()
            print("[input] Camera reset")
        elif key == glfw.KEY_M:
            toggles.muted = music.toggle_mute()
            print(f"[input] Music {'muted' if toggles.muted else 'unmuted'}")
        elif key == glfw.KEY_L:
            lighting.external_light_enabled = not lighting.external_light_enabled
            print(f"[input] External sun light: {lighting.external_light_enabled}")
        elif key == glfw.KEY_I:
            lighting.ambient_enabled = not lighting.ambient_enabled
            print(f"[input] Ambient light: {lighting.ambient_enabled}")

    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_key_callback(window, key_callback)

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.06, 0.12, 0.18, 1.0)

    shader = ShaderProgram(VERTEX_SHADER, FRAGMENT_SHADER)
    textures = TextureCache()
    objects = build_scene(textures, lighting)
    skybox = SkyBox()
    ocean = Ocean(surface_y=OCEAN_Y)
    pause_overlay = PauseOverlay(WINDOW_WIDTH, WINDOW_HEIGHT)
    muted_indicator = MutedIndicator(WINDOW_WIDTH, WINDOW_HEIGHT)

    music.play()

    previous_time = glfw.get_time()
    while not glfw.window_should_close(window):
        current_time = glfw.get_time()
        dt = current_time - previous_time
        previous_time = current_time

        if not toggles.paused:
            process_keyboard(window, camera, lighting, dt)

        width, height = glfw.get_framebuffer_size(window)
        aspect = width / max(height, 1)
        view = camera.view_matrix()
        projection = perspective(math.radians(60.0), aspect, 0.05, 420.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        shader.use()
        glUniformMatrix4fv(shader.uniforms["u_view"], 1, GL_TRUE, view)
        glUniformMatrix4fv(shader.uniforms["u_projection"], 1, GL_TRUE, projection)
        external_light_position = sun_light_position(lighting.sun_orbit_angle)
        upload_lighting_uniforms(shader, lighting, camera.position, external_light_position)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if toggles.wireframe else GL_FILL)

        for scene_object in objects:
            scene_object.mesh.draw(
                shader,
                scene_object.model_matrix(current_time),
                textures.white_texture,
                scene_object.lighting,
                scene_object.receives_external_light,
                scene_object.emissive(lighting.external_light_enabled),
            )

        # Oceano desenhado depois dos objetos opacos para aproveitar o depth
        # buffer já preenchido, e antes do skybox (que cobre o restante).
        ocean.draw(
            view,
            projection,
            current_time,
            toggles.wireframe,
            lighting,
            camera.position,
            external_light_position,
        )

        skybox.draw(view, projection)

        if toggles.muted:
            muted_indicator.draw()

        if toggles.paused:
            pause_overlay.draw()

        glfw.swap_buffers(window)
        glfw.poll_events()

    music.shutdown()
    glfw.terminate()
