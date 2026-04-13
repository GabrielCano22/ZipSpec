"""
batch.py
Procesa múltiples archivos .zip de una carpeta contra el mismo PDF o manifest.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.zip_reader import read_zip
from core.validator import validate


def run_batch(
    folder: str,
    req_data: dict,
    ignore_patterns: list[str] | None = None,
    fuzzy_threshold: float = 0.82,
    strict: bool = False,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> list[dict]:
    """
    Valida todos los .zip encontrados en `folder`.

    Args:
        folder: Ruta a la carpeta con archivos .zip.
        req_data: Resultado de pdf_reader o yaml_reader (requisitos).
        ignore_patterns: Patrones de archivos a ignorar dentro de cada zip.
        fuzzy_threshold: Umbral para fuzzy matching.
        strict: Modo estricto.
        on_progress: Callback(zip_name, current, total) para reportar progreso.

    Returns:
        Lista de dicts, uno por zip, con keys:
            zip_path, zip_name, result, error
    """
    folder_path = Path(folder)
    if not folder_path.exists() or not folder_path.is_dir():
        raise NotADirectoryError(f"No es una carpeta válida: {folder}")

    zip_files = sorted(folder_path.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No se encontraron archivos .zip en: {folder}")

    results: list[dict] = []
    total = len(zip_files)

    for i, zip_path in enumerate(zip_files, 1):
        if on_progress:
            on_progress(zip_path.name, i, total)

        try:
            zip_data = read_zip(str(zip_path), ignore_patterns=ignore_patterns)
            result = validate(
                zip_data,
                req_data,
                fuzzy_threshold=fuzzy_threshold,
                strict=strict,
                show_extra=True,
            )
            results.append({
                "zip_path": str(zip_path),
                "zip_name": zip_path.name,
                "result": result,
                "zip_data": zip_data,
                "error": None,
            })
        except Exception as e:
            results.append({
                "zip_path": str(zip_path),
                "zip_name": zip_path.name,
                "result": None,
                "zip_data": None,
                "error": str(e),
            })

    return results


def batch_summary(batch_results: list[dict]) -> dict:
    """Genera un resumen estadístico del batch."""
    total = len(batch_results)
    passed = sum(1 for r in batch_results if r["result"] and r["result"]["passed"])
    failed = sum(1 for r in batch_results if r["result"] and not r["result"]["passed"])
    errors = sum(1 for r in batch_results if r["error"])
    scores = [r["result"]["score"] for r in batch_results if r["result"]]

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "min_score": min(scores) if scores else 0.0,
        "max_score": max(scores) if scores else 0.0,
        "pass_rate": round(passed / total * 100, 1) if total > 0 else 0.0,
    }
