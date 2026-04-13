"""
pdf_reader.py
Extrae los archivos/carpetas requeridos desde un PDF de instrucciones.
Soporta múltiples estrategias de extracción: regex, listas, tablas.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

# Extensiones reconocidas
_EXTENSIONS = (
    "py|js|ts|jsx|tsx|html|htm|css|scss|sass|json|yaml|yml|txt|md|"
    "csv|xml|sql|sh|bash|bat|cmd|java|cpp|c|h|hpp|cs|php|rb|go|rs|"
    "kt|swift|env|cfg|ini|toml|zip|pdf|png|jpg|jpeg|gif|svg|ico|"
    "dockerfile|makefile|gitignore|editorconfig"
)

FILE_PATTERN = re.compile(
    rf"\b([\w\-. /]+\.(?:{_EXTENSIONS}))\b",
    re.IGNORECASE,
)

FOLDER_PATTERN = re.compile(
    r"\b((?:[\w\-]+/)+[\w\-]*|[\w\-]+/)\b"
)

# Ítems de lista
LIST_ITEM = re.compile(r"^[\s]*[-•*▪►✓✔◦→]\s+(.+)$|^[\s]*\d+[.)]\s+(.+)$")

# Código inline o bloques de código (ej: `archivo.py`, `src/main.py`)
INLINE_CODE = re.compile(r"`([^`]+)`")


def read_pdf(pdf_path: str) -> dict:
    """
    Lee un PDF y extrae requisitos usando múltiples estrategias.

    Estrategias (en orden de prioridad):
      1. Código inline entre backticks
      2. Patrones de archivo con extensión conocida
      3. Patrones de carpeta (ruta con slash)
      4. Tablas del PDF (pdfplumber)

    Returns:
        {
            "raw_text": str,
            "required_files": set[str],
            "required_folders": set[str],
            "lines": list[str],
            "source": "pdf",
            "page_count": int,
            "extraction_details": list[dict]  ← para modo verbose
        }
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"No se encontró el PDF: {pdf_path}")

    raw_text = ""
    table_data: list[list[str]] = []
    page_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text() or ""
            raw_text += text + "\n"

            # Extraer tablas
            for table in page.extract_tables():
                for row in table:
                    clean_row = [cell.strip() if cell else "" for cell in row]
                    table_data.append(clean_row)

    required_files: set[str] = set()
    required_folders: set[str] = set()
    relevant_lines: list[str] = []
    extraction_details: list[dict] = []

    # --- Estrategia 1: código inline ---
    for m in INLINE_CODE.finditer(raw_text):
        content = m.group(1).strip()
        if FILE_PATTERN.search(content):
            required_files.add(content)
            extraction_details.append({"strategy": "inline_code", "value": content})
        elif "/" in content or "\\" in content:
            required_folders.add(content.replace("\\", "/").strip("/"))
            extraction_details.append({"strategy": "inline_code_folder", "value": content})

    # --- Estrategia 2: regex línea por línea ---
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        found_anything = False

        for m in FILE_PATTERN.finditer(stripped):
            val = m.group(0).strip()
            if val not in required_files:
                required_files.add(val)
                extraction_details.append({"strategy": "regex_file", "value": val, "line": stripped})
            found_anything = True

        for m in FOLDER_PATTERN.finditer(stripped):
            val = m.group(0).replace("\\", "/").strip("/")
            if len(val) > 1 and val not in required_folders:
                # Evitar falsos positivos como URLs
                if not val.startswith(("http", "www")):
                    required_folders.add(val)
                    extraction_details.append({"strategy": "regex_folder", "value": val, "line": stripped})
            found_anything = True

        if found_anything:
            relevant_lines.append(stripped)

    # --- Estrategia 3: tablas ---
    for row in table_data:
        for cell in row:
            for m in FILE_PATTERN.finditer(cell):
                val = m.group(0).strip()
                required_files.add(val)
                extraction_details.append({"strategy": "table", "value": val})

    return {
        "raw_text": raw_text,
        "required_files": required_files,
        "required_folders": required_folders,
        "lines": relevant_lines,
        "source": "pdf",
        "page_count": page_count,
        "extraction_details": extraction_details,
    }
