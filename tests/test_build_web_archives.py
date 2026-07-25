import importlib.util
import ast
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "build_web_archives.py"
SPEC = importlib.util.spec_from_file_location("build_web_archives", SCRIPT)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class ArchiveBuildTests(unittest.TestCase):
    def _source_tree(self, root):
        source = root / "game"
        for index, relative_name in enumerate(BUILD.BUNDLE_FILES):
            path = source / relative_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"file-{index}\n".encode())
        (source / "not-shipped.txt").write_text("secret", encoding="utf-8")
        return source

    def test_build_is_reproducible_and_whitelisted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._source_tree(root)
            first = root / "first"
            second = root / "second"
            BUILD.build_archives(source, first, epoch=1234567890)
            BUILD.build_archives(source, second, epoch=1234567890)

            for suffix in (".tar.gz", ".apk"):
                name = f"{BUILD.ARCHIVE_NAME}{suffix}"
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

            expected = {f"{BUILD.BUNDLE_ROOT}/{name}" for name in BUILD.BUNDLE_FILES}
            with tarfile.open(first / f"{BUILD.ARCHIVE_NAME}.tar.gz", "r:gz") as archive:
                self.assertEqual(expected, set(archive.getnames()))
            with zipfile.ZipFile(first / f"{BUILD.ARCHIVE_NAME}.apk") as archive:
                self.assertEqual(expected, set(archive.namelist()))

            self.assertNotIn("assets/not-shipped.txt", expected)

    def test_local_python_imports_are_shipped(self):
        shipped = set(BUILD.BUNDLE_FILES)
        local_modules = {path.stem for path in (PROJECT_ROOT / "game").glob("*.py")}
        for relative_name in BUILD.BUNDLE_FILES:
            if not relative_name.endswith(".py"):
                continue
            source = (PROJECT_ROOT / "game" / relative_name).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative_name)
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".", 1)[0])
            for module in imported & local_modules:
                self.assertIn(
                    f"{module}.py",
                    shipped,
                    f"{relative_name} imports {module}, but the bundle omits it",
                )


if __name__ == "__main__":
    unittest.main()
