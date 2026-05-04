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
    glUniformMatrix4fv,
)

from .audio import BackgroundMusic
from .camera import Camera
from .config import ASSET_ROOT, OCEAN_Y, WINDOW_HEIGHT, WINDOW_WIDTH
from .math3d import normalize, perspective
from .ocean import Ocean
from .overlay import PauseOverlay
from .scene import build_scene
from .shaders import FRAGMENT_SHADER, VERTEX_SHADER, ShaderProgram
from .skybox import SkyBox
from .state import Toggles
from .textures import TextureCache

BACKGROUND_MUSIC_PATH = ASSET_ROOT / "One Piece - Bink's Sake _ Piano [SeDyYtIuhsA].mp3"


def framebuffer_size_callback(_window: glfw._GLFWwindow, width: int, height: int) -> None:
    from OpenGL.GL import glViewport

    glViewport(0, 0, width, height)


def process_keyboard(window: glfw._GLFWwindow, camera: Camera, dt: float) -> None:
    velocity = camera.speed * dt
    if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS:
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
    if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
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


def run() -> None:
    camera = Camera()
    toggles = Toggles()
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
            camera.__init__()
            print("[input] Camera reset")

    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_key_callback(window, key_callback)

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.06, 0.12, 0.18, 1.0)

    shader = ShaderProgram(VERTEX_SHADER, FRAGMENT_SHADER)
    textures = TextureCache()
    objects = build_scene(textures)
    skybox = SkyBox()
    ocean = Ocean(surface_y=OCEAN_Y)
    pause_overlay = PauseOverlay(WINDOW_WIDTH, WINDOW_HEIGHT)

    music.play()

    previous_time = glfw.get_time()
    while not glfw.window_should_close(window):
        current_time = glfw.get_time()
        dt = current_time - previous_time
        previous_time = current_time

        if not toggles.paused:
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

        # Oceano desenhado depois dos objetos opacos para aproveitar o depth
        # buffer já preenchido, e antes do skybox (que cobre o restante).
        ocean.draw(view, projection, current_time, toggles.wireframe)

        skybox.draw(view, projection)

        if toggles.paused:
            pause_overlay.draw()

        glfw.swap_buffers(window)
        glfw.poll_events()

    music.shutdown()
    glfw.terminate()

