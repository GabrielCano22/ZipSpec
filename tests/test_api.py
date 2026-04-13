"""Tests para la API REST (api/routes.py)"""
import zipfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _make_zip(tmp_path: Path, name: str = "test.zip", files: dict | None = None) -> Path:
    files = files or {"main.py": "pass", "README.md": "# Hola"}
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
    return path


def _make_manifest(tmp_path: Path, files: list | None = None) -> Path:
    files = files or ["main.py", "README.md"]
    path = tmp_path / "req.yml"
    yaml.dump({"name": "Test", "files": files, "folders": []}, open(path, "w"))
    return path


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_validate_ok(tmp_path):
    zip_path = _make_zip(tmp_path)
    manifest_path = _make_manifest(tmp_path)

    with open(zip_path, "rb") as zf, open(manifest_path, "rb") as sf:
        res = client.post("/api/validate", files={
            "zip_file": ("test.zip", zf, "application/zip"),
            "source_file": ("req.yml", sf, "application/x-yaml"),
        })

    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["passed"] is True
    assert data["summary"]["score"] == 100.0


def test_validate_con_faltantes(tmp_path):
    zip_path = _make_zip(tmp_path, files={"main.py": "pass"})
    manifest_path = _make_manifest(tmp_path, files=["main.py", "README.md", "setup.py"])

    with open(zip_path, "rb") as zf, open(manifest_path, "rb") as sf:
        res = client.post("/api/validate", files={
            "zip_file": ("test.zip", zf, "application/zip"),
            "source_file": ("req.yml", sf, "application/x-yaml"),
        })

    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["passed"] is False
    assert data["summary"]["total_missing"] > 0


def test_validate_rechaza_extension_invalida(tmp_path):
    zip_path = _make_zip(tmp_path)
    txt_path = tmp_path / "datos.txt"
    txt_path.write_text("hola")

    with open(zip_path, "rb") as zf, open(txt_path, "rb") as sf:
        res = client.post("/api/validate", files={
            "zip_file": ("test.zip", zf, "application/zip"),
            "source_file": ("datos.txt", sf, "text/plain"),
        })

    assert res.status_code == 400


def test_validate_rechaza_no_zip(tmp_path):
    txt = tmp_path / "no_es.txt"
    txt.write_text("hola")
    manifest = _make_manifest(tmp_path)

    with open(txt, "rb") as zf, open(manifest, "rb") as sf:
        res = client.post("/api/validate", files={
            "zip_file": ("no_es.txt", zf, "text/plain"),
            "source_file": ("req.yml", sf, "application/x-yaml"),
        })

    assert res.status_code == 400


def test_batch(tmp_path):
    z1 = _make_zip(tmp_path, "a.zip", {"main.py": "pass", "README.md": "x"})
    z2 = _make_zip(tmp_path, "b.zip", {"main.py": "pass"})
    manifest = _make_manifest(tmp_path)

    with open(z1, "rb") as f1, open(z2, "rb") as f2, open(manifest, "rb") as sf:
        res = client.post("/api/validate/batch", files=[
            ("zip_files", ("a.zip", f1, "application/zip")),
            ("zip_files", ("b.zip", f2, "application/zip")),
            ("source_file", ("req.yml", sf, "application/x-yaml")),
        ])

    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["total"] == 2
    assert data["summary"]["passed"] >= 1
