# RenderPiece

3D scene viewer built with OpenGL 3.3 (core profile) and Python.
Renders a One Piece-themed environment: the Going Merry ship on the open sea, with crew members on deck and personal items inside the cabin.

Projeto 3: the external environment now uses ambient, diffuse, and specular lighting. The keyboard-controlled OBJ sun is the external light source and only affects external objects; a small Firefly swarm is the internal light source around Chopper and only affects cabin objects.

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

| Key / Input  | Action                                                       |
|--------------|--------------------------------------------------------------|
| `W` `A` `S` `D` | Move camera (horizontal plane)                            |
| `Space`      | Move camera up                                               |
| `Left Shift` | Move camera down                                             |
| Mouse        | Look around                                                  |
| `P`          | Toggle wireframe mode                                        |
| `R`          | Reset camera to starting position                            |
| `M`          | Mute / unmute background music (red badge appears when muted)|
| `ESC`        | Pause / unpause (also pauses music)                          |
| `L`          | Toggle the external sun light                                |
| `F`          | Toggle the internal Firefly light                            |
| `I`          | Toggle ambient light                                         |
| `Z` / `X`    | Decrease / increase ambient light intensity                  |
| `C` / `V`    | Decrease / increase diffuse reflection                       |
| `B` / `N`    | Decrease / increase specular reflection                      |
| `J` / `K`    | Translate the sun manually around the ship                   |

### Projeto 3 - Etapa externa

- The procedural sun disk was removed from the skybox.
- `modelos/sun/source/Sun.obj` is rendered as a distant keyboard-controlled external object.
- `modelos/sun/textures/sun_surface.png` is applied to the sun through `Sun.mtl`.
- The sun object stays high above the sea and emits a strong external light. That light affects only objects marked as external: ship, deck characters/items, treasure, barrel, Brook, Franky, and ocean.
- Cabin objects keep their own lighting parameters but do not receive the external sun light in this stage.

### Projeto 3 - Etapa interna

- `modelos/firefly/source/firefly.obj` is instanced as a small swarm floating around Chopper's head inside the cabin.
- Only the abdomen tip of each Firefly is emissive, using an emissive mask around the tail material instead of lighting the whole model.
- The swarm emits a green-yellow internal point light toggled with `F`.
- The swarm light affects only cabin objects marked as internal: bed, old wooden table, Chopper, and the Fireflies themselves.
