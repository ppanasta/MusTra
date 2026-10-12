import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_web", ROOT / "mobile" / "build_web.py")
build_web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_web)


def test_build_assembles_an_offline_site(tmp_path):
    fake_pyodide = tmp_path / "pyodide"
    fake_pyodide.mkdir()
    for name in build_web.PYODIDE_FILES:
        (fake_pyodide / name).write_text("x")
    out = tmp_path / "site"
    build_web.build(out, fake_pyodide, "9.9.9")

    names = zipfile.ZipFile(out / "app" / "mustra.zip").namelist()
    assert "mustra/webapi.py" in names and "mustra/songs_seed.py" in names
    assert "mustra/gui.py" not in names  # desktop only (tkinter)

    for name in build_web.PYODIDE_FILES:
        assert (out / "pyodide" / name).exists()
    sw = (out / "sw.js").read_text()
    assert "mustra-9.9.9" in sw and "__FILES__" not in sw
    files = json.loads(sw.split("const FILES = ", 1)[1].split(";\n", 1)[0])
    assert "./index.html" in files and "./pyodide/pyodide.asm.wasm" in files
    assert (out / "icons" / "icon-512.png").exists()
