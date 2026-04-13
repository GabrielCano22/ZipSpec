"""
settings.py
Carga configuración desde .zipspec.yml en el directorio actual o home.
Los valores por defecto se sobrescriben con los del archivo y luego con los
argumentos CLI.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULTS: dict[str, Any] = {
    "fuzzy_threshold": 0.82,
    "default_format": "terminal",
    "strict": False,
    "show_extra": False,
    "ignore_patterns": [
        "__pycache__/",
        ".DS_Store",
        "Thumbs.db",
        ".git/",
        "*.pyc",
    ],
}

_CONFIG_FILENAMES = [".zipspec.yml", ".zipspec.yaml", "zipspec.yml"]


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """
    Busca y carga el archivo de configuración.
    Orden de búsqueda: argumento CLI → directorio actual → home del usuario.
    """
    cfg = dict(DEFAULTS)

    candidates: list[Path] = []
    if config_path:
        candidates.append(Path(config_path))
    for name in _CONFIG_FILENAMES:
        candidates.append(Path.cwd() / name)
        candidates.append(Path.home() / name)

    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
            break

    return cfg


def merge_cli(config: dict[str, Any], **cli_overrides: Any) -> dict[str, Any]:
    """Aplica overrides de CLI sobre la config base (solo si no son None)."""
    merged = dict(config)
    for k, v in cli_overrides.items():
        if v is not None:
            merged[k] = v
    return merged
