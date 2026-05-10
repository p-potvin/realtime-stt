import unittest
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.getcwd())

from vault_themes.theme_manager import VaultThemeManager, VaultTheme

class TestVaultThemeManager(unittest.TestCase):
    def setUp(self):
        self.manager = VaultThemeManager()

    def test_get_theme_by_name_success(self):
        theme = self.manager.get_theme_by_name("Golden Slate")
        self.assertIsInstance(theme, VaultTheme)
        self.assertEqual(theme.name, "Golden Slate")

    def test_get_theme_by_name_fallback(self):
        # Should fall back to the first theme (Golden Slate)
        theme = self.manager.get_theme_by_name("Non Existent Theme")
        self.assertEqual(theme.name, "Golden Slate")

    def test_get_theme_with_name(self):
        theme = self.manager.get_theme(name="Cyberpunk Cinder")
        self.assertEqual(theme.name, "Cyberpunk Cinder")

    def test_get_theme_with_index(self):
        # Index 1 should be Codex Solarized Light Revisited
        theme = self.manager.get_theme(index=1)
        self.assertEqual(theme.name, "Codex Solarized Light Revisited")

    def test_get_theme_fallback(self):
        theme = self.manager.get_theme(name="Invalid", index=999)
        self.assertEqual(theme.name, "Golden Slate")

if __name__ == "__main__":
    unittest.main()
