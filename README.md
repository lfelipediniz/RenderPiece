# RenderPiece

3D scene viewer built with OpenGL 3.3 (core profile) and Python. 
Renders a One Piece-themed environment: the Going Merry ship on the open sea, with crew members on deck and personal items inside the cabin

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

### Transformações dos Personagens

| Tecla | Personagem | Transformação |
|-------|------------|---------------|
| `1` | **Luffy** | Aumentar escala (uniforme, máx. 3.0×) |
| `2` | **Luffy** | Diminuir escala (uniforme, mín. 0.3×) |
| `3` | **Franky** | Rotação no eixo Y (sentido anti-horário) |
| `4` | **Franky** | Rotação no eixo Y (sentido horário) |
| `5` | **Tony Tony Chopper** | Translação +X (máx. +3.0) |
| `6` | **Tony Tony Chopper** | Translação −X (mín. −3.0) |
| `7` | **Tony Tony Chopper** | Translação +Z (máx. +3.0) |
| `8` | **Tony Tony Chopper** | Translação −Z (mín. −3.0) |
