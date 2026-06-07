"""Montagem da cena One Piece (Projeto 2 + primeira etapa do Projeto 3).

Cada `load_*` carrega um `.obj` distinto via `load_obj_mesh` (req 4) e
`build_scene` posiciona os modelos com `compose_transform`, separando o
ambiente externo (proa/conves do Going Merry sobre o oceano) do interno
(cabine: cama, mesa, Chopper).

Projeto 3: objetos externos recebem a fonte de luz do sol; objetos internos
nao recebem essa fonte. Cada objeto tem perfil proprio de reflexao difusa e
especular, independente dos parametros vindos dos arquivos `.mtl`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import numpy as np
from .config import ASSET_ROOT
from .lighting import LightingProfile, LightingState, SUN_MODEL_SCALE, sun_base_position
from .math3d import compose_transform
from .mesh import GpuMesh
from .obj_loader import load_obj_mesh
from .textures import TextureCache


@dataclass
class SceneObject:
    """Modelo da cena com sua matriz de mundo dependente do tempo

    `model_factory(elapsed)` permite animacoes futuras sem mudar a API.
    `mesh.anchor_to_base` re-centraliza o modelo no XZ e apoia o piso
    do bbox em y=0 antes da matriz do mundo ser aplicada
    """

    name: str
    mesh: GpuMesh
    model_factory: Callable[[float], np.ndarray]
    lighting: LightingProfile
    receives_external_light: bool
    receives_internal_light: bool = False
    external_light_source: bool = False
    internal_light_source: bool = False
    emissive_region_local_position: tuple[float, float, float] | None = None
    emissive_region_local_radius: float = 0.0

    def model_matrix(self, elapsed: float) -> np.ndarray:
        return self.model_factory(elapsed) @ self.mesh.anchor_to_base

    def emissive(self, external_light_enabled: bool) -> tuple[float, float, float]:
        if self.external_light_source and not external_light_enabled:
            return self.lighting.emissive_off
        return self.lighting.emissive

    def emissive_region(self, elapsed: float) -> tuple[tuple[float, float, float], float] | None:
        if self.emissive_region_local_position is None or self.emissive_region_local_radius <= 0.0:
            return None

        matrix = self.model_matrix(elapsed)
        center = matrix @ np.array([*self.emissive_region_local_position, 1.0], dtype=np.float32)
        edge = matrix @ np.array(
            [
                self.emissive_region_local_position[0] + self.emissive_region_local_radius,
                self.emissive_region_local_position[1],
                self.emissive_region_local_position[2],
                1.0,
            ],
            dtype=np.float32,
        )
        radius = float(np.linalg.norm(edge[:3] - center[:3]))
        return (float(center[0]), float(center[1]), float(center[2])), radius


def static_object(
    mesh: GpuMesh,
    matrix: np.ndarray,
    name: str,
    lighting: LightingProfile,
    receives_external_light: bool,
    receives_internal_light: bool = False,
    internal_light_source: bool = False,
    emissive_region_local_position: tuple[float, float, float] | None = None,
    emissive_region_local_radius: float = 0.0,
) -> SceneObject:
    return SceneObject(
        name,
        mesh,
        lambda _elapsed, m=matrix: m,
        lighting,
        receives_external_light,
        receives_internal_light=receives_internal_light,
        internal_light_source=internal_light_source,
        emissive_region_local_position=emissive_region_local_position,
        emissive_region_local_radius=emissive_region_local_radius,
    )


SHIP_LIGHTING = LightingProfile(
    ambient=(0.70, 0.66, 0.58),
    diffuse=(0.88, 0.80, 0.70),
    specular=(0.34, 0.30, 0.24),
    shininess=28.0,
)
SKIN_LIGHTING = LightingProfile(
    ambient=(0.72, 0.62, 0.56),
    diffuse=(0.96, 0.82, 0.72),
    specular=(0.22, 0.18, 0.16),
    shininess=18.0,
)
NAMI_LIGHTING = LightingProfile(
    ambient=(0.70, 0.60, 0.56),
    diffuse=(0.94, 0.78, 0.68),
    specular=(0.30, 0.24, 0.20),
    shininess=22.0,
)
FRANKY_LIGHTING = LightingProfile(
    ambient=(0.64, 0.68, 0.72),
    diffuse=(0.80, 0.84, 0.90),
    specular=(0.64, 0.66, 0.70),
    shininess=44.0,
)
GOLD_LIGHTING = LightingProfile(
    ambient=(0.84, 0.70, 0.34),
    diffuse=(1.00, 0.82, 0.32),
    specular=(1.00, 0.86, 0.44),
    shininess=70.0,
)
WOOD_LIGHTING = LightingProfile(
    ambient=(0.62, 0.46, 0.30),
    diffuse=(0.76, 0.52, 0.34),
    specular=(0.20, 0.15, 0.10),
    shininess=18.0,
)
BED_LIGHTING = LightingProfile(
    ambient=(0.64, 0.58, 0.52),
    diffuse=(0.72, 0.64, 0.58),
    specular=(0.10, 0.10, 0.10),
    shininess=12.0,
)
BROOK_LIGHTING = LightingProfile(
    ambient=(0.66, 0.66, 0.62),
    diffuse=(0.82, 0.82, 0.76),
    specular=(0.35, 0.35, 0.32),
    shininess=34.0,
)
TABLE_LIGHTING = LightingProfile(
    ambient=(0.58, 0.42, 0.27),
    diffuse=(0.70, 0.46, 0.28),
    specular=(0.18, 0.13, 0.08),
    shininess=16.0,
)
CHOPPER_LIGHTING = LightingProfile(
    ambient=(0.72, 0.58, 0.56),
    diffuse=(0.90, 0.68, 0.64),
    specular=(0.20, 0.16, 0.16),
    shininess=20.0,
)
FIREFLY_LIGHTING = LightingProfile(
    ambient=(0.66, 0.60, 0.46),
    diffuse=(0.82, 0.74, 0.52),
    specular=(0.28, 0.24, 0.16),
    shininess=24.0,
)
FIREFLY_TAIL_LOCAL_POSITION = (0.0, -0.0053, 0.0032)
FIREFLY_TAIL_LOCAL_RADIUS = 0.0078
FIREFLY_SWARM_CENTER = (-0.18, 9.20, -7.20)
FIREFLY_SWARM_SPECS = [
    ((0.00, 0.00, 0.00), 6.5, -30.0, 0.0),
    ((-0.14, 0.10, 0.12), 5.8, 20.0, 0.7),
    ((0.28, 0.14, -0.10), 6.2, -65.0, 1.3),
    ((-0.22, 0.30, -0.16), 5.5, 80.0, 2.1),
    ((0.45, 0.28, 0.06), 5.9, -115.0, 2.8),
    ((-0.06, 0.42, 0.24), 5.2, 135.0, 3.6),
    ((0.16, -0.12, -0.24), 6.0, -10.0, 4.2),
    ((-0.24, -0.06, -0.30), 5.4, 55.0, 5.0),
    ((0.52, 0.02, -0.26), 5.6, -145.0, 5.8),
    ((-0.06, 0.24, -0.46), 5.1, 165.0, 6.4),
    ((0.32, 0.48, 0.22), 5.0, -85.0, 7.1),
    ((-0.18, 0.52, 0.02), 5.3, 105.0, 7.8),
]
SUN_LIGHTING = LightingProfile(
    ambient=(1.00, 0.72, 0.30),
    diffuse=(1.00, 0.86, 0.36),
    specular=(0.00, 0.00, 0.00),
    shininess=1.0,
    emissive=(1.65, 0.86, 0.18),
    emissive_off=(0.12, 0.06, 0.02),
)


def load_ship(textures: TextureCache) -> GpuMesh:
    ship_textures = ASSET_ROOT / "going-merry/textures"
    return load_obj_mesh(
        "Going Merry",
        ASSET_ROOT / "going-merry/source/Going Merry.obj",
        textures,
        fallback_texture=textures.from_file(ship_textures / "000.png"),
        force_white_diffuse_when_textured=True,
    )


def load_luffy(textures: TextureCache) -> GpuMesh:
    luffy_dir = ASSET_ROOT / "luffy"
    luffy_texture = luffy_dir / "textures/Luffy1.png"
    return load_obj_mesh(
        "Luffy",
        luffy_dir / "source/luffy.obj",
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
        ASSET_ROOT / "nami/source/Nami.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def load_franky(textures: TextureCache) -> GpuMesh:
    return load_obj_mesh(
        "Franky",
        ASSET_ROOT / "franky/source/franky.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def load_bitcoin_pile(textures: TextureCache) -> GpuMesh:
    bitcoin_texture = (
        ASSET_ROOT
        / "bitcoin-pile/textures/360_F_561618223_L4KBczVuqzGhWBOIvueotLNqduStHNia.png"
    )
    return load_obj_mesh(
        "Bitcoin pile",
        ASSET_ROOT / "bitcoin-pile/source/coins.obj",
        textures,
        fallback_texture=textures.from_file(bitcoin_texture),
        force_white_diffuse_when_textured=True,
    )


def load_bed(textures: TextureCache) -> GpuMesh:
    return load_obj_mesh(
        "Bed Minecraft",
        ASSET_ROOT / "bed/source/Bed.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def load_brook(textures: TextureCache) -> GpuMesh:
    return load_obj_mesh(
        "Brook",
        ASSET_ROOT / "brook/source/Brook.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )



def load_tony_chopper(textures: TextureCache) -> GpuMesh:
    return load_obj_mesh(
        "Tony Tony Chopper",
        ASSET_ROOT / "chopper/source/chopper.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def load_firefly(textures: TextureCache) -> GpuMesh:
    mesh = load_obj_mesh(
        "Firefly",
        ASSET_ROOT / "firefly/source/firefly.obj",
        textures,
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )
    tail_material = mesh.materials.get("Material.003")
    if tail_material is not None:
        tail_material.emissive = (2.75, 2.45, 0.38)
    return mesh


def make_firefly_swarm(firefly: GpuMesh) -> list[SceneObject]:
    swarm: list[SceneObject] = []
    for index, (offset, firefly_scale, base_yaw, phase) in enumerate(FIREFLY_SWARM_SPECS, start=1):
        def model_factory(
            elapsed: float,
            offset: tuple[float, float, float] = offset,
            firefly_scale: float = firefly_scale,
            base_yaw: float = base_yaw,
            phase: float = phase,
        ) -> np.ndarray:
            sway_x = 0.055 * np.sin(elapsed * 0.95 + phase * 1.7)
            bob_y = 0.075 * np.sin(elapsed * 1.45 + phase)
            sway_z = 0.050 * np.cos(elapsed * 1.05 + phase * 1.3)
            position = (
                FIREFLY_SWARM_CENTER[0] + offset[0] + sway_x,
                FIREFLY_SWARM_CENTER[1] + offset[1] + bob_y,
                FIREFLY_SWARM_CENTER[2] + offset[2] + sway_z,
            )
            return compose_transform(
                position,
                rotation=(
                    6.0 * np.sin(elapsed * 1.25 + phase),
                    base_yaw + 12.0 * np.sin(elapsed * 0.75 + phase),
                    5.0 * np.cos(elapsed * 1.10 + phase),
                ),
                object_scale=firefly_scale,
            )

        swarm.append(
            SceneObject(
                f"Firefly swarm {index}",
                firefly,
                model_factory,
                FIREFLY_LIGHTING,
                False,
                receives_internal_light=True,
                internal_light_source=True,
                emissive_region_local_position=FIREFLY_TAIL_LOCAL_POSITION,
                emissive_region_local_radius=FIREFLY_TAIL_LOCAL_RADIUS,
            )
        )
    return swarm


def load_old_wooden_table(textures: TextureCache) -> GpuMesh:
    table_dir = ASSET_ROOT / "wooden-table"
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
        / "barrel/textures/texture-wooden-barrel-background-closeup-600nw-2315911823.webp"
    )
    return load_obj_mesh(
        "Barrel",
        ASSET_ROOT / "barrel/source/Barril.obj",
        textures,
        fallback_texture=textures.from_file(barrel_texture),
        force_white_diffuse_when_textured=True,
    )


def load_sun(textures: TextureCache) -> GpuMesh:
    sun_texture = ASSET_ROOT / "sun/textures/sun_surface.png"
    return load_obj_mesh(
        "External sun light source",
        ASSET_ROOT / "sun/source/Sun.obj",
        textures,
        fallback_texture=textures.from_file(sun_texture),
        fallback_diffuse=(1.0, 1.0, 1.0),
        force_white_diffuse_when_textured=True,
    )


def build_scene(textures: TextureCache, lighting_state: LightingState) -> list[SceneObject]:
    ship = load_ship(textures)
    luffy = load_luffy(textures)
    nami = load_nami(textures)
    franky = load_franky(textures)
    bitcoin_pile = load_bitcoin_pile(textures)
    bed = load_bed(textures)
    barrel = load_barrel(textures)
    brook = load_brook(textures)
    old_wooden_table = load_old_wooden_table(textures)
    tony_chopper = load_tony_chopper(textures)
    firefly = load_firefly(textures)
    sun = load_sun(textures)

    # bitcoin_pile e instanciado varias vezes para encher o tesouro do navio;
    # conta como UM modelo (req 2: repeticoes nao somam)

    return [
        SceneObject(
            "Translating sun light source",
            sun,
            lambda _elapsed: compose_transform(
                tuple(sun_base_position(lighting_state.sun_orbit_angle)),
                rotation=(0.0, 0.0, 0.0),
                object_scale=SUN_MODEL_SCALE,
            ),
            SUN_LIGHTING,
            False,
            external_light_source=True,
        ),
        static_object(
            ship,
            compose_transform((0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), object_scale=0.01),
            "Ship",
            SHIP_LIGHTING,
            True,
        ),
        SceneObject(
            "Luffy on prow",
            luffy,
            lambda _elapsed: compose_transform(
                (0.0, 11.92, 10.60),
                rotation=(0.0, 0.0, 0.0),
                object_scale=0.013,
            ),
            SKIN_LIGHTING,
            True,
        ),
        static_object(
            nami,
            compose_transform((0.0, 19.40, 1.00), rotation=(0.0, 0.0, 0.0), object_scale=1.0),
            "Nami on prow",
            NAMI_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.0, 5.80, -1.25), rotation=(0.0, 20.0, 0.0), object_scale=0.038),
            "Bitcoin pile 1",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.55, 5.80, -1.50), rotation=(0.0, 75.0, 0.0), object_scale=0.036),
            "Bitcoin pile 2",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.50, 5.80, -0.90), rotation=(0.0, -40.0, 0.0), object_scale=0.037),
            "Bitcoin pile 3",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.20, 5.80, -2.00), rotation=(0.0, 130.0, 0.0), object_scale=0.035),
            "Bitcoin pile 4",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.25, 5.95, -1.30), rotation=(0.0, 55.0, 0.0), object_scale=0.034),
            "Bitcoin pile 5 (top)",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.80, 5.80, -0.70), rotation=(0.0, 10.0, 0.0), object_scale=0.037),
            "Bitcoin pile 6",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.80, 5.80, -1.80), rotation=(0.0, 165.0, 0.0), object_scale=0.036),
            "Bitcoin pile 7",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.40, 5.80, -0.50), rotation=(0.0, -85.0, 0.0), object_scale=0.035),
            "Bitcoin pile 8",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.10, 5.80, -2.40), rotation=(0.0, 200.0, 0.0), object_scale=0.036),
            "Bitcoin pile 9",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((1.00, 5.80, -1.80), rotation=(0.0, 45.0, 0.0), object_scale=0.035),
            "Bitcoin pile 10",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-1.00, 5.80, -0.60), rotation=(0.0, 110.0, 0.0), object_scale=0.036),
            "Bitcoin pile 11",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.65, 5.95, -1.20), rotation=(0.0, 90.0, 0.0), object_scale=0.033),
            "Bitcoin pile 12 (top)",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.55, 5.95, -1.70), rotation=(0.0, -20.0, 0.0), object_scale=0.033),
            "Bitcoin pile 13 (top)",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((0.10, 6.08, -1.40), rotation=(0.0, 35.0, 0.0), object_scale=0.031),
            "Bitcoin pile 14 (peak)",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bitcoin_pile,
            compose_transform((-0.30, 5.80, -0.30), rotation=(0.0, -60.0, 0.0), object_scale=0.036),
            "Bitcoin pile 15",
            GOLD_LIGHTING,
            True,
        ),
        static_object(
            bed,
            compose_transform((2.10, 7.80, -6.20), rotation=(0.0, 0.0, 0.0), object_scale=0.5),
            "Bed",
            BED_LIGHTING,
            False,
            receives_internal_light=True,
        ),
        static_object(
            barrel,
            compose_transform((-2.65, 5.90, -3.00), rotation=(0.0, -18.0, 0.0), object_scale=0.011),
            "Barrel on lower deck",
            WOOD_LIGHTING,
            True,
        ),
        static_object(
            franky,
            compose_transform((3.00, 5.90, -1.00), rotation=(0.0, -108.0, 0.0), object_scale=0.011),
            "Franky",
            FRANKY_LIGHTING,
            True,
        ),
        static_object(
            brook,
            compose_transform((-3.75, 7.80, -5.05), rotation=(0.0, 55.0, 0.0), object_scale=1.0),
            "Brook",
            BROOK_LIGHTING,
            True,
        ),
        static_object(
            old_wooden_table,
            compose_transform((0.30, 7.80, -8.30), rotation=(0.0, 0.0, 0.0), object_scale=0.015),
            "Old wooden table",
            TABLE_LIGHTING,
            False,
            receives_internal_light=True,
        ),
        static_object(
            tony_chopper,
            compose_transform((-1.00, 7.80, -7.50), rotation=(0.0, 45.0, 0.0), object_scale=0.02),
            "Tony Chopper next to desk",
            CHOPPER_LIGHTING,
            False,
            receives_internal_light=True,
        ),
        *make_firefly_swarm(firefly),
    ]
