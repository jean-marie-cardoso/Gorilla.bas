import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
sys.path.insert(0, str(GAME_DIR))

import config  # noqa: E402

SCRIPT = PROJECT_ROOT / "scripts" / "build_web_archives.py"
SPEC = importlib.util.spec_from_file_location("asset_build_web_archives", SCRIPT)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class AssetContractTests(unittest.TestCase):
    def test_configured_sprites_exist_and_ship(self):
        shipped = set(BUILD.BUNDLE_FILES)
        for sprite_name, filename in config.SPRITES.items():
            with self.subTest(sprite_name=sprite_name):
                path = GAME_DIR / config.ASSETS_DIR / filename
                self.assertTrue(path.is_file(), f"missing sprite: {path}")
                self.assertIn(f"assets/{filename}", shipped)

    def test_menu_background_and_audio_ship(self):
        self.assertIn("audio.py", BUILD.BUNDLE_FILES)
        self.assertIn("assets/menu_background.png", BUILD.BUNDLE_FILES)


if __name__ == "__main__":
    unittest.main()
