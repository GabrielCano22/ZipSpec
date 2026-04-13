"""
yaml_reader.py
Lee un archivo manifest .yml como fuente de requisitos,
alternativa al PDF cuando los requisitos son controlados por el autor.

Formato del manifest:
    name: "Nombre del proyecto"
    description: "Descripción opcional"
    required_files:
      - main.py
      - src/utils.py
      - README.md
    required_folders:
      - src/
      - tests/
    ignore:
      - "*.DS_Store"
"""
from __future__ import annotations

from pathlib import Path

import yaml


def read_manifest(manifest_path: str) -> dict:
    """
    Lee un manifest YAML y retorna la misma estructura que pdf_reader.read_pdf().
    Esto permite usar yaml_reader y pdf_reader de forma intercambiable.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el manifest: {path}")
    if path.suffix.lower() not in (".yml", ".yaml"):
        raise ValueError(f"El manifest debe ser un archivo .yml o .yaml: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Accept both "files"/"folders" and "required_files"/"required_folders"
    required_files: set[str] = set(data.get("required_files", data.get("files", [])))
    required_folders: set[str] = set(data.get("required_folders", data.get("folders", [])))

    # Limpiar separadores
    required_files = {f.replace("\\", "/").strip() for f in required_files}
    required_folders = {d.replace("\\", "/").strip("/") for d in required_folders}

    return {
        "raw_text": "",
        "required_files": required_files,
        "required_folders": required_folders,
        "lines": list(required_files | required_folders),
        "source": "manifest",
        "manifest_name": data.get("name", path.stem),
        "manifest_description": data.get("description", ""),
    }


def generate_example_manifest(output_path: str = "example_manifest.yml") -> None:
    """Genera un archivo manifest de ejemplo."""
    example = {
        "name": "Mi Proyecto",
        "description": "Requisitos de entrega del proyecto",
        "required_files": [
            "main.py",
            "README.md",
            "requirements.txt",
            "src/utils.py",
            "tests/test_main.py",
        ],
        "required_folders": [
            "src/",
            "tests/",
        ],
        "ignore": [
            "__pycache__/",
            "*.pyc",
            ".DS_Store",
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(example, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
