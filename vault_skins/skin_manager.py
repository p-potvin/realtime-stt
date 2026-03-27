from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class VaultTheme:
    name: str
    mode: str
    primary: str
    accent: str

class VaultSkinManager:
    """
    Centralized Skin/Theme manager for VaultWares projects.
    Handles theme definitions, color extraction, and glass-ui style generation.
    """
    def __init__(self):
        self._themes = [
            VaultTheme("Vintage Velvet", "light", "#F5F5DC", "#800020"),
            VaultTheme("Cyberpunk Cinder", "dark", "#073642", "#CB4B16"),
            VaultTheme("Golden Slate", "dark", "#4A5459", "#D4AF37"),
            VaultTheme("Modern Monolith", "light", "#FAF9F6", "#333333"),
            VaultTheme("Crimson Bloom", "dark", "#8B0000", "#FFC0CB"),
            VaultTheme("Ocean Mist", "light", "#D3D3D3", "#006994"),
            VaultTheme("Neon Void", "dark", "#222222", "#00FFFF"),
            VaultTheme("Royal Tangerine", "dark", "#4B0082", "#F28500"),
            VaultTheme("Amethyst Frost", "light", "#FDFDFD", "#800080"),
        ]

    def get_themes(self) -> List[VaultTheme]:
        return self._themes

    def get_theme(self, index: int) -> VaultTheme:
        if 0 <= index < len(self._themes):
            return self._themes[index]
        return self._themes[1]  # Default to Cyberpunk Cinder (index 1)

    @staticmethod
    def get_glass_rgba(hex_color: str, alpha: int) -> str:
        """Converts hex to rgba for glass-ui elements."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {alpha})"
