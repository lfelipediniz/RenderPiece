from dataclasses import dataclass
from typing import Callable

import numpy as np

from .config import ASSET_ROOT
from .math3d import compose_transform
from .mesh import GpuMesh
from .obj_loader import load_obj_mesh
from .textures import TextureCache


@dataclass
class SceneObject:
    name: str
    mesh: GpuMesh
    model_factory: Callable[[float], np.ndarray]

    def model_matrix(self, elapsed: float) -> np.ndarray:
        return self.model_factory(elapsed) @ self.mesh.anchor_to_base


def static_object(mesh: GpuMesh, matrix: np.ndarray, name: str) -> SceneObject:
    return SceneObject(name, mesh, lambda _elapsed, m=matrix: m)


def load_ship(textures: TextureCache) -> GpuMesh:
    ship_textures = ASSET_ROOT / "navio/textures"
    return load_obj_mesh(
        "Going Merry",
        ASSET_ROOT / "navio/source/Going Merry.obj",
        textures,
        fallback_texture=textures.from_file(ship_textures / "000.png"),
        force_white_diffuse_when_textured=True,
    )


def load_luffy(textures: TextureCache) -> GpuMesh:
    luffy_textures = ASSET_ROOT / "lado_externo/luffy/textures"
    luffy = load_obj_mesh(
        "Luffy",
        ASSET_ROOT / "lado_externo/luffy/source/Monkey D. Luffy.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
        material_texture_overrides={
            "24_-Straw_Hat.Hat_Hair_0.2_0_0": luffy_textures / "Scratch.png",
            "Gum": luffy_textures / "IMG_1670.jpeg",
            "Gum.001": luffy_textures / "IMG_1671.png",
            "Lower_shorts": luffy_textures / "IMG_1663.jpeg",
            "Pupil": luffy_textures / "Scratch.png",
            "Ribbon": luffy_textures / "IMG_1670.jpeg",
            "Sandals": luffy_textures / "IMG_0451.jpeg",
            "Sandals.001": luffy_textures / "IMG_0451.jpeg",
            "Shirt": luffy_textures / "IMG_1670.jpeg",
            "Shorts": luffy_textures / "IMG_1663.jpeg",
            "Straw_hat": luffy_textures / "IMG_1674.jpeg",
            "Teeth": luffy_textures / "IMG_1671.png",
            "button": luffy_textures / "IMG_1672.jpeg",
            "eye": luffy_textures / "IMG_1671.png",
            "hair": luffy_textures / "Scratch.png",
            "shock": luffy_textures / "IMG_1671.png",
            "skin": luffy_textures / "IMG_1662.jpeg",
            "tongue": luffy_textures / "IMG_1670.jpeg",
        },
    )
    luffy.batches = [
        batch for batch in luffy.batches if batch.material_name != "Eyebrows_and_scratch"
    ]
    return luffy


def load_bitcoin_pile(textures: TextureCache) -> GpuMesh:
    bitcoin_texture = (
        ASSET_ROOT
        / "lado_externo/bitcoin/textures/golden-concrete-foil-paper-texture_1249-354.avif"
    )
    return load_obj_mesh(
        "Bitcoin pile",
        ASSET_ROOT / "lado_externo/bitcoin/source/coins.obj",
        textures,
        fallback_texture=textures.from_file(bitcoin_texture),
        force_white_diffuse_when_textured=True,
    )


def load_chaves(textures: TextureCache) -> GpuMesh:
    chaves_texture = ASSET_ROOT / "lado_externo/chaves/textures/Chavo.png"
    return load_obj_mesh(
        "Chaves",
        ASSET_ROOT / "lado_externo/chaves/source/Chavo.obj",
        textures,
        fallback_texture=textures.from_file(chaves_texture),
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def load_barrel(textures: TextureCache) -> GpuMesh:
    barrel_texture = (
        ASSET_ROOT
        / "lado_externo/barril/textures/texture-wooden-barrel-background-closeup-600nw-2315911823.webp"
    )
    return load_obj_mesh(
        "Barrel",
        ASSET_ROOT / "lado_externo/barril/source/Barril.obj",
        textures,
        fallback_texture=textures.from_file(barrel_texture),
        force_white_diffuse_when_textured=True,
    )


def build_scene(textures: TextureCache) -> list[SceneObject]:
    ship = load_ship(textures)
    luffy = load_luffy(textures)
    bitcoin_pile = load_bitcoin_pile(textures)
    chaves = load_chaves(textures)
    barrel = load_barrel(textures)

    return [
        static_object(
            ship,
            compose_transform((0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), object_scale=0.01),
            "Ship",
        ),
        static_object(
            luffy,
            compose_transform((0.0, 11.92, 10.60), rotation=(0.0, 0.0, 0.0), object_scale=1.0),
            "Luffy on prow",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.0, 5.80, -1.25), rotation=(0.0, 20.0, 0.0), object_scale=0.038),
            "Bitcoin pile on deck",
        ),
        static_object(
            chaves,
            compose_transform((-3.75, 7.80, -5.05), rotation=(0.0, 55.0, 0.0), object_scale=1.08),
            "Chaves on deck",
        ),
        static_object(
            barrel,
            compose_transform((-2.65, 5.90, -3.00), rotation=(0.0, -18.0, 0.0), object_scale=0.011),
            "Barrel on lower deck",
        ),
    ]
