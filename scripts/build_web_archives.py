#!/usr/bin/env python3
"""Construit les deux archives Pygbag de facon reproductible."""

import argparse
import gzip
import io
import os
from pathlib import Path
import tarfile
import tempfile
import time
import zipfile


ARCHIVE_NAME = "gorilla.version.web"
BUNDLE_ROOT = "assets"
BUNDLE_FILES = (
    "action.py",
    "ai.py",
    "audio.py",
    "browser_input.py",
    "config.py",
    "graphics.py",
    "intro.py",
    "main.py",
    "menu.py",
    "movement.py",
    "physics.py",
    "sprites.py",
    "ui.py",
    "utils.py",
    "assets/banana.png",
    "assets/gorilla_idle_v2.png",
    "assets/gorilla_leftup_v2.png",
    "assets/gorilla_rightup_v2.png",
    "assets/menu_background.png",
    "assets/sun_v2.png",
    "assets/sun_surprised_v2.png",
)


def _source_date_epoch():
    value = os.environ.get("SOURCE_DATE_EPOCH", "0")
    try:
        epoch = int(value)
    except ValueError as exc:
        raise ValueError("SOURCE_DATE_EPOCH must be an integer") from exc
    return max(0, epoch)


def _bundle_entries(source_dir):
    source_dir = Path(source_dir).resolve()
    entries = []
    for relative_name in BUNDLE_FILES:
        path = source_dir / relative_name
        if not path.is_file():
            raise FileNotFoundError(f"missing bundle file: {path}")
        if path.is_symlink():
            raise ValueError(f"bundle files cannot be symlinks: {path}")
        entries.append((f"{BUNDLE_ROOT}/{relative_name}", path.read_bytes()))
    return entries


def _tar_gz_bytes(entries, epoch):
    raw_tar = io.BytesIO()
    with tarfile.open(fileobj=raw_tar, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for archive_name, data in entries:
            info = tarfile.TarInfo(archive_name)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = epoch
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(data))

    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=output,
        mtime=epoch,
    ) as compressed:
        compressed.write(raw_tar.getvalue())
    return output.getvalue()


def _apk_bytes(entries, epoch):
    # ZIP ne sait pas encoder une date avant 1980.
    zip_epoch = max(epoch, 315532800)
    date_time = time.gmtime(zip_epoch)[:6]
    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for archive_name, data in entries:
            info = zipfile.ZipInfo(archive_name, date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def _atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary_path = Path(handle.name)
        handle.write(data)
    try:
        os.replace(temporary_path, path)
        path.chmod(0o644)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def build_archives(source_dir, output_dir, archive_name=ARCHIVE_NAME, epoch=None):
    epoch = _source_date_epoch() if epoch is None else max(0, int(epoch))
    entries = _bundle_entries(source_dir)
    output_dir = Path(output_dir)
    outputs = {
        output_dir / f"{archive_name}.tar.gz": _tar_gz_bytes(entries, epoch),
        output_dir / f"{archive_name}.apk": _apk_bytes(entries, epoch),
    }
    for path, data in outputs.items():
        _atomic_write(path, data)
    return tuple(outputs)


def main():
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=project_root / "game")
    parser.add_argument("--output-dir", type=Path, default=project_root)
    parser.add_argument("--archive-name", default=ARCHIVE_NAME)
    args = parser.parse_args()

    paths = build_archives(args.source, args.output_dir, args.archive_name)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
