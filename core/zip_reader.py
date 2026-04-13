"""
zip_reader.py
Extrae la estructura de archivos y carpetas de un .zip,
con soporte para patrones de ignorado y metadatos por archivo.
"""
from __future__ import annotations

import fnmatch
import zipfile
from pathlib import Path


def _matches_ignore(name: str, patterns: list[str]) -> bool:
    """Retorna True si el nombre coincide con algún patrón de ignorado."""
    base = Path(name).name
    for pattern in patterns:
        pattern_clean = pattern.rstrip("/")
        if fnmatch.fnmatch(base, pattern_clean):
            return True
        if fnmatch.fnmatch(name, pattern_clean):
            return True
        # Ignorar directorios completos
        if pattern.endswith("/") and (name.startswith(pattern_clean + "/") or name == pattern_clean):
            return True
    return False


def read_zip(zip_path: str, ignore_patterns: list[str] | None = None) -> dict:
    """
    Lee un archivo .zip y retorna su estructura con metadatos.

    Args:
        zip_path: Ruta al archivo .zip.
        ignore_patterns: Lista de patrones glob a ignorar (ej: ['*.DS_Store', '__pycache__/']).

    Returns:
        {
            "files": set de rutas relativas (str),
            "folders": set de carpetas (str),
            "tree": lista ordenada de entradas,
            "metadata": dict con info por archivo (tamaño, comprimido)
            "zip_name": nombre del archivo zip
        }
    """
    ignore_patterns = ignore_patterns or []
    zip_path = Path(zip_path)

    if not zip_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {zip_path}")
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"El archivo no es un .zip válido: {zip_path}")

    files: set[str] = set()
    folders: set[str] = set()
    tree: list[str] = []
    metadata: dict[str, dict] = {}

    with zipfile.ZipFile(zip_path, "r") as zf:
        for entry in zf.infolist():
            name = entry.filename.replace("\\", "/").rstrip("/")

            if _matches_ignore(name, ignore_patterns):
                continue

            tree.append(entry.filename)

            if entry.is_dir():
                folders.add(name)
            else:
                files.add(name)
                metadata[name] = {
                    "size": entry.file_size,
                    "compressed_size": entry.compress_size,
                    "compress_type": entry.compress_type,
                    "date_time": entry.date_time,
                }
                # Registrar carpetas intermedias
                parts = Path(name).parts
                for i in range(1, len(parts)):
                    folders.add("/".join(parts[:i]))

    return {
        "files": files,
        "folders": folders,
        "tree": sorted(tree),
        "metadata": metadata,
        "zip_name": zip_path.name,
        "zip_path": str(zip_path),
        "total_size": sum(m["size"] for m in metadata.values()),
    }


def get_filenames_only(files: set[str]) -> set[str]:
    """Retorna solo los nombres de archivo sin ruta."""
    return {Path(f).name for f in files}


def format_size(size_bytes: int) -> str:
    """Formatea bytes a unidad legible."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"
