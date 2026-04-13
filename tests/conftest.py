"""Fixtures compartidos para los tests de ZipSpec."""
import zipfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_zip(tmp_path):
    """Crea un .zip de prueba con estructura conocida."""
    zip_path = tmp_path / "proyecto.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("main.py", "print('hola')")
        zf.writestr("README.md", "# Proyecto")
        zf.writestr("requirements.txt", "flask>=3.0")
        zf.writestr("src/utils.py", "def foo(): pass")
        zf.writestr("src/models.py", "class X: pass")
        zf.writestr("tests/test_main.py", "def test(): pass")
    return str(zip_path)


@pytest.fixture
def tmp_manifest(tmp_path):
    """Crea un manifest YAML que coincide con tmp_zip."""
    manifest_path = tmp_path / "requisitos.yml"
    data = {
        "name": "Proyecto de prueba",
        "description": "Para tests",
        "files": [
            "main.py",
            "README.md",
            "requirements.txt",
            "src/utils.py",
            "src/models.py",
            "tests/test_main.py",
        ],
        "folders": ["src", "tests"],
    }
    with open(manifest_path, "w") as f:
        yaml.dump(data, f)
    return str(manifest_path)


@pytest.fixture
def tmp_incomplete_zip(tmp_path):
    """Zip al que le faltan archivos respecto al manifest."""
    zip_path = tmp_path / "incompleto.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("main.py", "print('hola')")
        zf.writestr("src/utils.py", "pass")
    return str(zip_path)


@pytest.fixture
def tmp_typo_zip(tmp_path):
    """Zip con nombres similares pero no exactos (para fuzzy matching)."""
    zip_path = tmp_path / "typos.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("mian.py", "print('hola')")  # main.py -> mian.py
        zf.writestr("README.md", "# Proyecto")
        zf.writestr("requirements.txt", "flask")
        zf.writestr("src/utills.py", "pass")  # utils.py -> utills.py
        zf.writestr("src/models.py", "pass")
        zf.writestr("tests/test_main.py", "pass")
    return str(zip_path)
