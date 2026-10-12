"""Assemble the MusTra web app (iPhone web app, and the Android app's assets).

    python mobile/build_web.py --out mobile/dist [--version 1.0.0]
        [--pyodide-dir DIR]     # folder with the Pyodide files, or
        [--cache DIR]           # where to keep the downloaded Pyodide release

The result is a static site: the front end (mobile/web), the MusTra Python
package as app/mustra.zip, and the Pyodide runtime (Python compiled to
WebAssembly) with the sqlite3 module, so the app works offline.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "mobile" / "web"
PACKAGE = ROOT / "mustra"

PYODIDE_VERSION = "0.26.4"
PYODIDE_URL = ("https://github.com/pyodide/pyodide/releases/download/"
               "{v}/pyodide-{v}.tar.bz2")
PYODIDE_FILES = ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm",
                 "python_stdlib.zip", "pyodide-lock.json", "sqlite3-1.0.0.zip")
# Desktop-only modules the web API never imports.
SKIP_MODULES = {"gui.py", "__main__.py"}


def fetch_pyodide(cache: Path) -> Path:
    """Download the Pyodide release once and extract only the files we ship."""
    target = cache / f"pyodide-{PYODIDE_VERSION}"
    if all((target / f).exists() for f in PYODIDE_FILES):
        return target
    target.mkdir(parents=True, exist_ok=True)
    archive = cache / f"pyodide-{PYODIDE_VERSION}.tar.bz2"
    if not archive.exists():
        url = PYODIDE_URL.format(v=PYODIDE_VERSION)
        print(f"Downloading {url}")
        with urllib.request.urlopen(url) as response, open(archive, "wb") as out:
            shutil.copyfileobj(response, out)
    wanted = {f"pyodide/{f}" for f in PYODIDE_FILES}
    with tarfile.open(archive, "r:bz2") as tar:
        for member in tar:
            if member.name in wanted and member.isfile():
                with tar.extractfile(member) as src, open(target / Path(member.name).name, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    missing = [f for f in PYODIDE_FILES if not (target / f).exists()]
    if missing:
        raise SystemExit(f"Pyodide archive is missing {missing}")
    return target


def build(out: Path, pyodide_dir: Path, version: str) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(WEB, out)

    (out / "app").mkdir()
    with zipfile.ZipFile(out / "app" / "mustra.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PACKAGE.glob("*.py")):
            if path.name not in SKIP_MODULES:
                zf.write(path, f"mustra/{path.name}")

    (out / "pyodide").mkdir()
    for name in PYODIDE_FILES:
        shutil.copy2(pyodide_dir / name, out / "pyodide" / name)

    files = sorted("./" + p.relative_to(out).as_posix() for p in out.rglob("*")
                   if p.is_file() and p.name != "sw.js")
    files.insert(0, "./")
    sw = (out / "sw.js").read_text(encoding="utf-8")
    sw = sw.replace("__VERSION__", version).replace("__FILES__", json.dumps(files, indent=2))
    (out / "sw.js").write_text(sw, encoding="utf-8")
    (out / "version.txt").write_text(version + "\n", encoding="utf-8")
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"Built {out} ({len(files)} files, {size / 1e6:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "mobile" / "dist")
    parser.add_argument("--version", default="dev")
    parser.add_argument("--pyodide-dir", type=Path)
    parser.add_argument("--cache", type=Path, default=ROOT / "mobile" / ".cache")
    args = parser.parse_args()
    pyodide_dir = args.pyodide_dir or fetch_pyodide(args.cache)
    build(args.out, pyodide_dir, args.version)


if __name__ == "__main__":
    main()
