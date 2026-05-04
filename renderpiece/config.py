"""Constantes globais do projeto

Centraliza dimensoes da janela e os limites do "mundo" (usados pelo clamp
de camera em `camera.py` para atender ao requisito 9), alem das extensoes
de imagem aceitas pelo loader de texturas
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = ROOT / "modelos"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Caixa do mundo explorável (req 9): camera fica presa em |x|,|z| < WORLD_HALF_SIZE
# e em OCEAN_Y < y < SKY_CEILING_Y
WORLD_HALF_SIZE = 80.0
TERRAIN_Y = 0.0
SKY_CEILING_Y = 34.0
DECK_Y = 6.85
# Linha d'água do oceano externo. Posicionada um pouco acima do TERRAIN_Y
# para que o casco do Going Merry pareça parcialmente submerso.
OCEAN_Y = 1.5

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tga", ".bmp", ".webp", ".avif")

