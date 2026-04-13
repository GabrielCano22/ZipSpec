"""Tests para core/zip_reader.py"""
import zipfile

from core.zip_reader import read_zip, format_size


def test_read_zip_detecta_archivos(tmp_zip):
    data = read_zip(tmp_zip)
    assert "main.py" in data["files"]
    assert "src/utils.py" in data["files"]
    assert len(data["files"]) == 6


def test_read_zip_detecta_carpetas(tmp_zip):
    data = read_zip(tmp_zip)
    assert "src" in data["folders"] or "src/" in data["folders"]


def test_read_zip_genera_tree(tmp_zip):
    data = read_zip(tmp_zip)
    assert len(data["tree"]) > 0


def test_read_zip_incluye_metadata(tmp_zip):
    data = read_zip(tmp_zip)
    assert isinstance(data["metadata"], dict)
    assert data["total_size"] >= 0


def test_read_zip_ignore_patterns(tmp_path):
    zip_path = tmp_path / "con_basura.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("main.py", "pass")
        zf.writestr("__pycache__/main.cpython-313.pyc", "bytes")
        zf.writestr(".DS_Store", "x")

    data = read_zip(str(zip_path), ignore_patterns=["__pycache__/*", ".DS_Store"])
    assert "main.py" in data["files"]
    assert not any("pycache" in f for f in data["files"])
    assert ".DS_Store" not in data["files"]


def test_read_zip_archivo_no_existe():
    import pytest
    with pytest.raises(FileNotFoundError):
        read_zip("/ruta/que/no/existe.zip")


def test_format_size():
    assert format_size(0) == "0.0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1048576) == "1.0 MB"
