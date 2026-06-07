# RenderPiece

3D scene viewer built with OpenGL 3.3 (core profile) and Python.
Renders a One Piece-themed environment: the Going Merry ship on the open sea, with crew members on deck and personal items inside the cabin.

Projeto 3: the external environment now uses ambient, diffuse, and specular lighting. The keyboard-controlled OBJ sun is the external light source and only affects external objects; a small Firefly swarm and a table lamp are internal light sources and only affect cabin objects.

## Requirements

- Python 3.9+
- macOS / Linux 

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
source venv/bin/activate
python main.py
```

## Project Docs

- Asset catalog: `docs/catalog/assets.md`
- Projeto 2 spec: `docs/project_specs/projeto2.md`
- Projeto 3 spec: `docs/project_specs/projeto3.md`

## Controls

### Global Controls

These commands control navigation, viewing, audio, and app state.

| Key / Input | Action |
|-------------|--------|
| `W` `A` `S` `D` | Move camera on the horizontal plane |
| `Space` | Move camera up |
| `Left Shift` | Move camera down |
| Mouse | Look around |
| `P` | Toggle wireframe mode |
| `R` | Reset camera to starting position |
| `M` | Mute / unmute background music |
| `ESC` | Pause / unpause scene animation and music |

### Projeto 2 Controls

These controls were kept from Projeto 2 even though Projeto 3 no longer requires them. They demonstrate model transformations by keyboard: scale, rotation, and translation.

| Key | Character | Transformation |
|-----|-----------|----------------|
| `1` | Luffy | Increase uniform scale, capped at `3.0x` |
| `2` | Luffy | Decrease uniform scale, capped at `0.3x` |
| `3` | Franky | Rotate around the Y axis counterclockwise |
| `4` | Franky | Rotate around the Y axis clockwise |
| `5` | Tony Tony Chopper | Translate on `+X`, capped at `+3.0` |
| `6` | Tony Tony Chopper | Translate on `-X`, capped at `-3.0` |
| `7` | Tony Tony Chopper | Translate on `+Z`, capped at `+3.0` |
| `8` | Tony Tony Chopper | Translate on `-Z`, capped at `-3.0` |

### Projeto 3 Controls

These commands control the independent light switches and lighting coefficients required by Projeto 3.

| Key | Light / Parameter | Action |
|-----|-------------------|--------|
| `L` | External sun light | Toggle on / off |
| `F` | Internal Firefly swarm light | Toggle on / off |
| `O` | Internal table lamp light | Toggle on / off |
| `I` | Ambient light | Toggle on / off |
| `Z` / `X` | Ambient strength | Decrease / increase |
| `C` / `V` | Diffuse reflection strength | Decrease / increase |
| `B` / `N` | Specular reflection strength | Decrease / increase |
| `J` / `K` | Sun position | Translate the sun around the ship |

### Projeto 3 - Etapa externa

- The procedural sun disk was removed from the skybox.
- `modelos/sun/source/Sun.obj` is rendered as a distant keyboard-controlled external object.
- `modelos/sun/textures/sun_surface.png` is applied to the sun through `Sun.mtl`.
- The sun object stays high above the sea and emits a strong external light. That light affects only objects marked as external: ship, deck characters/items, treasure, barrel, Brook, Franky, and ocean.
- Cabin objects keep their own lighting parameters but do not receive the external sun light in this stage.

### Projeto 3 - Etapa interna

- `modelos/firefly/source/firefly.obj` is instanced as a small swarm floating around Chopper's head inside the cabin.
- Only the abdomen tip of each Firefly is emissive, using an emissive mask around the tail material instead of lighting the whole model.
- `modelos/lamp/source/lamp.obj` is rendered on top of the old wooden table.
- The upper bulb/shade region of the lamp is emissive, using an emissive mask so the base does not glow.
- The swarm emits a green-yellow internal point light toggled with `F`; the table lamp emits a warm internal point light toggled with `O`.
- Both internal lights affect only cabin objects marked as internal: bed, old wooden table, Chopper, the Fireflies, and the lamp.
