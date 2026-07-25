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


if __name__ == "__main__":
    unittest.main()
