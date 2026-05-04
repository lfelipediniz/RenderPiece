"""Cache de texturas 2D

Le imagens via PIL, sobe para a GPU como `GL_TEXTURE_2D` com mipmaps e
guarda o handle em um dicionario para evitar recarregar o mesmo arquivo

Tambem expoe `white_texture`, usada como fallback quando um material do
`.obj`/`.mtl` nao tem `map_Kd`
"""

from pathlib import Path
from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_REPEAT,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    glBindTexture,
    glGenTextures,
    glGenerateMipmap,
    glPixelStorei,
    glTexImage2D,
    glTexParameteri,
)
from PIL import Image


class TextureCache:
    def __init__(self) -> None:
        self.cache: dict[str, int] = {}
        self.white_texture = self.create_solid("white", (255, 255, 255, 255))

    def create_solid(self, name: str, color: tuple[int, int, int, int]) -> int:
        image = Image.new("RGBA", (1, 1), color)
        return self.from_image(name, image, repeat=False)

    def from_image(self, name: str, image: Image.Image, repeat: bool = True) -> int:
        if name in self.cache:
            return self.cache[name]

        # Inverte verticalmente porque OpenGL trata v=0 como base e PIL como topo
        image = image.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        width, height = image.size
        data = image.tobytes()

        texture_id = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT if repeat else GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT if repeat else GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            data,
        )
        glGenerateMipmap(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)

        self.cache[name] = texture_id
        return texture_id

    def from_file(self, path: Path, repeat: bool = True) -> int:
        key = str(path.resolve())
        if key in self.cache:
            return self.cache[key]

        try:
            image = Image.open(path)
        except Exception as exc:
            print(f"[texture] Could not load {path}: {exc}. Using white texture.")
            return self.white_texture

        return self.from_image(key, image, repeat=repeat)

