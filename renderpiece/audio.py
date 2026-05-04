from __future__ import annotations

import os
from pathlib import Path

# Evita que o pygame imprima sua mensagem de boas-vindas no terminal.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

try:
    import pygame
except ImportError:
    pygame = None  # type: ignore[assignment]


class BackgroundMusic:
    """Música de fundo em loop com suporte a pause/resume.

    Usa apenas `pygame.mixer` (subsistema de áudio), sem inicializar a janela
    ou o loop de eventos do pygame, então convive bem com o GLFW.
    """

    def __init__(self, path: Path, volume: float = 0.5) -> None:
        self.available = False
        self._is_paused = False

        if pygame is None:
            print("[audio] pygame não está instalado; música de fundo desativada.")
            return
        if not path.exists():
            print(f"[audio] Arquivo de música não encontrado: {path}")
            return

        try:
            pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(volume)
            self.available = True
            print(f"[audio] Música carregada: {path.name}")
        except Exception as exc:
            print(f"[audio] Falha ao inicializar mixer: {exc}")

    def play(self) -> None:
        """Inicia a reprodução em loop infinito."""
        if not self.available:
            return
        try:
            pygame.mixer.music.play(loops=-1)
            self._is_paused = False
        except Exception as exc:
            print(f"[audio] Falha ao tocar música: {exc}")

    def pause(self) -> None:
        if not self.available or self._is_paused:
            return
        pygame.mixer.music.pause()
        self._is_paused = True

    def resume(self) -> None:
        """Retoma de onde parou."""
        if not self.available or not self._is_paused:
            return
        pygame.mixer.music.unpause()
        self._is_paused = False

    def shutdown(self) -> None:
        if not self.available:
            return
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
