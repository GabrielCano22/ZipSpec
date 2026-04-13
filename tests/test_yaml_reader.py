"""Tests para core/yaml_reader.py"""
import pytest
import yaml

from core.yaml_reader import read_manifest, generate_example_manifest


def test_read_manifest_archivos(tmp_manifest):
    data = read_manifest(tmp_manifest)
    assert "main.py" in data["required_files"]
    assert "src/utils.py" in data["required_files"]
    assert len(data["required_files"]) == 6


def test_read_manifest_carpetas(tmp_manifest):
    data = read_manifest(tmp_manifest)
    assert "src" in data["required_folders"]
    assert "tests" in data["required_folders"]


def test_read_manifest_metadata(tmp_manifest):
    data = read_manifest(tmp_manifest)
    assert data["source"] == "manifest"
    assert data["manifest_name"] == "Proyecto de prueba"


def test_read_manifest_acepta_required_files_key(tmp_path):
    """Acepta tanto 'files' como 'required_files' como clave."""
    manifest = tmp_path / "alt.yml"
    yaml.dump({"required_files": ["app.py"], "required_folders": ["lib"]}, open(manifest, "w"))
    data = read_manifest(str(manifest))
    assert "app.py" in data["required_files"]
    assert "lib" in data["required_folders"]


def test_read_manifest_archivo_no_existe():
    with pytest.raises(FileNotFoundError):
        read_manifest("/no/existe.yml")


def test_read_manifest_extension_invalida(tmp_path):
    txt = tmp_path / "datos.txt"
    txt.write_text("hola")
    with pytest.raises(ValueError):
        read_manifest(str(txt))


def test_generate_example_manifest(tmp_path):
    out = str(tmp_path / "ejemplo.yml")
    generate_example_manifest(out)
    data = yaml.safe_load(open(out))
    assert "required_files" in data
    assert isinstance(data["required_files"], list)
