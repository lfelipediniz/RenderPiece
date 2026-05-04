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
    luffy_dir = ASSET_ROOT / "lado_externo/luffy-one-piece"
    luffy_texture = luffy_dir / "textures/Luffy1.png"
    return load_obj_mesh(
        "Luffy",
        luffy_dir / "source/fb4b2915893e461ab6e37275163b83fc/Luffy One Piece.obj",
        textures,
        fallback_texture=textures.from_file(luffy_texture),
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
        material_texture_overrides={
            "03___Default": luffy_texture,
        },
    )


def load_nami(textures: TextureCache) -> GpuMesh:
    return load_obj_mesh(
        "Nami",
        ASSET_ROOT / "lado_externo/nami/source/Nami/Nami.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def load_bitcoin_pile(textures: TextureCache) -> GpuMesh:
    bitcoin_texture = (
        ASSET_ROOT
        / "lado_externo/bitcoin/textures/360_F_561618223_L4KBczVuqzGhWBOIvueotLNqduStHNia.png"
    )
    return load_obj_mesh(
        "Bitcoin pile",
        ASSET_ROOT / "lado_externo/bitcoin/source/coins.obj",
        textures,
        fallback_texture=textures.from_file(bitcoin_texture),
        force_white_diffuse_when_textured=True,
    )


def load_bed(textures: TextureCache) -> GpuMesh:
    bed_dir = ASSET_ROOT / "lado_interno/bed-minecraft/source/Bed Minecraft by JDanielHE"
    return load_obj_mesh(
        "Bed Minecraft",
        bed_dir / "Bed.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )



def load_brook(textures: TextureCache) -> GpuMesh:
    return load_obj_mesh(
        "Brook",
        ASSET_ROOT / "lado_interno/one-piece-brook/source/Brook/Brook.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )





def load_tony_chopper(textures: TextureCache) -> GpuMesh:
    return load_obj_mesh(
        "Tony Tony Chopper",
        ASSET_ROOT / "lado_interno/tony-chopper/source/chopper/chopper.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def load_old_wooden_table(textures: TextureCache) -> GpuMesh:
    table_dir = ASSET_ROOT / "lado_interno/old-wooden-table-with-some-dust"
    table_texture = table_dir / "textures/desk_UV02_desk_BaseColor.png"
    return load_obj_mesh(
        "Old wooden table",
        table_dir / "source/desk_UV02.obj",
        textures,
        fallback_texture=textures.from_file(table_texture),
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
    nami = load_nami(textures)
    bitcoin_pile = load_bitcoin_pile(textures)
    bed = load_bed(textures)
    barrel = load_barrel(textures)
    brook = load_brook(textures)
    old_wooden_table = load_old_wooden_table(textures)
    tony_chopper = load_tony_chopper(textures)





    return [
        static_object(
            ship,
            compose_transform((0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), object_scale=0.01),
            "Ship",
        ),
        static_object(
            luffy,
            compose_transform((0.0, 11.92, 10.60), rotation=(0.0, 0.0, 0.0), object_scale=0.013),
            "Luffy on prow",
        ),
        static_object(
            nami,
            compose_transform((0.0, 19.40, 1.00), rotation=(0.0, 0.0, 0.0), object_scale=1.0),
            "Nami on prow",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.0, 5.80, -1.25), rotation=(0.0, 20.0, 0.0), object_scale=0.038),
            "Bitcoin pile 1",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.55, 5.80, -1.50), rotation=(0.0, 75.0, 0.0), object_scale=0.036),
            "Bitcoin pile 2",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.50, 5.80, -0.90), rotation=(0.0, -40.0, 0.0), object_scale=0.037),
            "Bitcoin pile 3",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.20, 5.80, -2.00), rotation=(0.0, 130.0, 0.0), object_scale=0.035),
            "Bitcoin pile 4",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.25, 5.95, -1.30), rotation=(0.0, 55.0, 0.0), object_scale=0.034),
            "Bitcoin pile 5 (top)",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.80, 5.80, -0.70), rotation=(0.0, 10.0, 0.0), object_scale=0.037),
            "Bitcoin pile 6",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.80, 5.80, -1.80), rotation=(0.0, 165.0, 0.0), object_scale=0.036),
            "Bitcoin pile 7",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.40, 5.80, -0.50), rotation=(0.0, -85.0, 0.0), object_scale=0.035),
            "Bitcoin pile 8",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.10, 5.80, -2.40), rotation=(0.0, 200.0, 0.0), object_scale=0.036),
            "Bitcoin pile 9",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((1.00, 5.80, -1.80), rotation=(0.0, 45.0, 0.0), object_scale=0.035),
            "Bitcoin pile 10",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-1.00, 5.80, -0.60), rotation=(0.0, 110.0, 0.0), object_scale=0.036),
            "Bitcoin pile 11",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.65, 5.95, -1.20), rotation=(0.0, 90.0, 0.0), object_scale=0.033),
            "Bitcoin pile 12 (top)",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.55, 5.95, -1.70), rotation=(0.0, -20.0, 0.0), object_scale=0.033),
            "Bitcoin pile 13 (top)",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.10, 6.08, -1.40), rotation=(0.0, 35.0, 0.0), object_scale=0.031),
            "Bitcoin pile 14 (peak)",
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.30, 5.80, -0.30), rotation=(0.0, -60.0, 0.0), object_scale=0.036),
            "Bitcoin pile 15",
        ),
        static_object(
            bed,
            compose_transform((2.10, 7.80, -6.20), rotation=(0.0, 0.0, 0.0), object_scale=0.5),
            "Bed",
        ),
        static_object(
            barrel,
            compose_transform((-2.65, 5.90, -3.00), rotation=(0.0, -18.0, 0.0), object_scale=0.011),
            "Barrel on lower deck",
        ),
        static_object(
            brook,
            compose_transform((-3.75, 7.80, -5.05), rotation=(0.0, 55.0, 0.0), object_scale=1.0),
            "Brook",
        ),
        static_object(
            old_wooden_table,
            compose_transform((0.30, 7.80, -8.30), rotation=(0.0, 0.0, 0.0), object_scale=0.015),
            "Old wooden table",
        ),
        static_object(
            tony_chopper,
            compose_transform((-1.00, 7.80, -7.50), rotation=(0.0, 45.0, 0.0), object_scale=0.02),
            "Tony Chopper next to desk",
        ),
    ]
