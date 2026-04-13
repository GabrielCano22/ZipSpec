"""Tests para core/validator.py"""
from core.zip_reader import read_zip
from core.yaml_reader import read_manifest
from core.validator import validate


def test_validacion_completa_pasa(tmp_zip, tmp_manifest):
    zip_data = read_zip(tmp_zip)
    req_data = read_manifest(tmp_manifest)
    result = validate(zip_data, req_data)

    assert result["passed"] is True
    assert result["score"] == 100.0
    assert result["total_missing"] == 0


def test_validacion_incompleta_falla(tmp_incomplete_zip, tmp_manifest):
    zip_data = read_zip(tmp_incomplete_zip)
    req_data = read_manifest(tmp_manifest)
    result = validate(zip_data, req_data)

    assert result["passed"] is False
    assert result["score"] < 100
    assert result["total_missing"] > 0
    assert "README.md" in result["missing_files"]


def test_fuzzy_matching_detecta_typos(tmp_typo_zip, tmp_manifest):
    zip_data = read_zip(tmp_typo_zip)
    req_data = read_manifest(tmp_manifest)
    result = validate(zip_data, req_data, fuzzy_threshold=0.7)

    # mian.py deberia hacer fuzzy match con main.py
    fuzzy_names = [fm["required"] for fm in result["fuzzy_matches"]]
    assert any("main.py" in n for n in fuzzy_names)


def test_modo_strict_falla_con_extras(tmp_zip, tmp_manifest):
    """En modo strict, archivos extra hacen fallar la validacion."""
    zip_data = read_zip(tmp_zip)
    # Manifest que no pide todos los archivos del zip
    req_data = read_manifest(tmp_manifest)
    req_data["required_files"] = {"main.py"}  # Solo pide uno
    req_data["required_folders"] = set()

    result = validate(zip_data, req_data, strict=True, show_extra=True)
    assert result["strict_mode"] is True
    # Hay archivos extra, entonces strict falla
    assert result["passed"] is False


def test_score_proporcional(tmp_incomplete_zip, tmp_manifest):
    """El score refleja el porcentaje de requisitos presentes."""
    zip_data = read_zip(tmp_incomplete_zip)
    req_data = read_manifest(tmp_manifest)
    result = validate(zip_data, req_data)

    # Solo tiene main.py y src/utils.py de 6+2=8 requeridos
    assert 0 < result["score"] < 100
    assert result["total_present"] < result["total_required"]


def test_show_extra_lista_archivos(tmp_zip, tmp_manifest):
    zip_data = read_zip(tmp_zip)
    req_data = read_manifest(tmp_manifest)
    req_data["required_files"] = {"main.py"}
    req_data["required_folders"] = set()

    result = validate(zip_data, req_data, show_extra=True)
    assert len(result["extra_files"]) > 0
