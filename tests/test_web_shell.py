import json
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WebShellTests(unittest.TestCase):
    def test_index_and_template_keep_responsive_contract(self):
        for relative_name in ("index.html", "game/fullscreen.tmpl"):
            content = (PROJECT_ROOT / relative_name).read_text(encoding="utf-8")
            with self.subTest(relative_name=relative_name):
                self.assertIn('<html lang="fr">', content)
                self.assertIn("--game-ratio: 1.6", content)
                self.assertIn('id="rotate-device"', content)
                self.assertIn("requestAnimationFrame", content)
                self.assertNotIn("setInterval(", content)
                self.assertEqual(1, content.count('name="viewport"'))
                self.assertIn('rel="manifest"', content)
                self.assertIn('rel="apple-touch-icon"', content)
                self.assertIn("mobile-shell.css?v=31", content)
                self.assertIn("mobile-shell.js?v=31", content)
                self.assertNotIn(" async defer>", content)
                self.assertIn('"stableSince", 0', content)

    def test_mobile_fullscreen_files_and_manifest(self):
        required = (
            "mobile-shell.css",
            "mobile-shell.js",
            "manifest.webmanifest",
            "sw.js",
            "icon-192.png",
            "apple-touch-icon.png",
        )
        for relative_name in required:
            with self.subTest(relative_name=relative_name):
                self.assertTrue((PROJECT_ROOT / relative_name).is_file())

        script = (PROJECT_ROOT / "mobile-shell.js").read_text(encoding="utf-8")
        self.assertIn("requestFullscreen", script)
        self.assertIn("window.GorillaViewport", script)
        self.assertIn("logicalWidth", script)
        self.assertIn("stableSince", script)
        self.assertIn('screen.orientation.lock("landscape")', script)
        self.assertIn("window.visualViewport", script)
        self.assertIn("repairCanvasBackingStore", script)
        self.assertIn("canvas.width / canvas.height", script)
        self.assertIn("window.Module?.setCanvasSize", script)
        self.assertIn("serviceWorker.register", script)
        self.assertIn("Sur l’écran d’accueil", script)

        stylesheet = (PROJECT_ROOT / "mobile-shell.css").read_text(encoding="utf-8")
        self.assertIn("safe-area-inset-left", stylesheet)
        self.assertIn("compact-landscape", stylesheet)
        self.assertIn("--game-width", stylesheet)
        self.assertIn("--game-width: 100vw", stylesheet)

        browser_input = (
            PROJECT_ROOT / "game" / "browser_input.py"
        ).read_text(encoding="utf-8")
        self.assertIn('move.textContent = "BOUGER"', browser_input)
        self.assertIn("moveRequested()", browser_input)

        manifest = json.loads(
            (PROJECT_ROOT / "manifest.webmanifest").read_text(encoding="utf-8")
        )
        self.assertEqual("fullscreen", manifest["display"])
        self.assertEqual("landscape", manifest["orientation"])
        self.assertIn("standalone", manifest["display_override"])

    def test_pages_workflow_ships_mobile_shell(self):
        workflow = (
            PROJECT_ROOT / ".github" / "workflows" / "pages.yml"
        ).read_text(encoding="utf-8")
        for relative_name in (
            "manifest.webmanifest",
            "mobile-shell.css",
            "mobile-shell.js",
            "sw.js",
            "icon-192.png",
            "apple-touch-icon.png",
        ):
            with self.subTest(relative_name=relative_name):
                self.assertIn(relative_name, workflow)


if __name__ == "__main__":
    unittest.main()
