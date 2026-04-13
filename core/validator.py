"""
validator.py
Compara la estructura del .zip contra los requisitos extraídos del PDF o manifest.
Soporta: coincidencia exacta, fuzzy matching, modo strict.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path


def _normalize(paths: set[str]) -> set[str]:
    return {p.replace("\\", "/").strip().strip("/") for p in paths if p.strip()}


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _find_fuzzy_match(
    target: str,
    candidates: set[str],
    threshold: float,
) -> tuple[str, float] | None:
    """
    Busca la coincidencia más cercana de `target` dentro de `candidates`.
    Compara tanto rutas completas como solo nombres de archivo.
    Retorna (candidato, score) o None si no supera el threshold.
    """
    target_name = Path(target).name.lower()
    best_match: str | None = None
    best_score = 0.0

    for candidate in candidates:
        candidate_name = Path(candidate).name.lower()

        # Comparar nombre de archivo vs nombre de archivo
        score_name = _similarity(target_name, candidate_name)
        # Comparar ruta completa
        score_full = _similarity(target.lower(), candidate.lower())

        score = max(score_name, score_full)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_match and best_score >= threshold:
        return best_match, best_score
    return None


def validate(
    zip_data: dict,
    req_data: dict,
    fuzzy_threshold: float = 0.82,
    strict: bool = False,
    show_extra: bool = False,
) -> dict:
    """
    Compara zip_data (de zip_reader) con req_data (de pdf_reader o yaml_reader).

    Args:
        zip_data: Resultado de zip_reader.read_zip()
        req_data: Resultado de pdf_reader.read_pdf() o yaml_reader.read_manifest()
        fuzzy_threshold: Umbral de similitud para fuzzy matching (0.0 - 1.0)
        strict: Si True, los archivos extra también cuentan como fallo
        show_extra: Si True, incluye archivos no requeridos en el reporte

    Returns:
        Dict con todos los resultados de validación.
    """
    zip_files = _normalize(zip_data["files"])
    zip_folders = _normalize(zip_data["folders"])
    req_files = _normalize(req_data["required_files"])
    req_folders = _normalize(req_data["required_folders"])

    # ── Validación de archivos ──────────────────────────────────────────
    present_files: list[dict] = []
    missing_files: list[str] = []
    fuzzy_matches: list[dict] = []

    for req in sorted(req_files):
        if req in zip_files:
            present_files.append({"required": req, "found": req, "match": "exact"})
            continue

        # Buscar por nombre de archivo solamente
        req_name = Path(req).name.lower()
        name_match = next(
            (f for f in zip_files if Path(f).name.lower() == req_name), None
        )
        if name_match:
            present_files.append({
                "required": req,
                "found": name_match,
                "match": "name_only",
                "note": f"Encontrado en ruta distinta: {name_match}",
            })
            continue

        # Fuzzy matching
        fuzzy = _find_fuzzy_match(req, zip_files, fuzzy_threshold)
        if fuzzy:
            fuzzy_candidate, fuzzy_score = fuzzy
            fuzzy_matches.append({
                "required": req,
                "closest": fuzzy_candidate,
                "score": round(fuzzy_score * 100, 1),
            })
        else:
            missing_files.append(req)

    # ── Validación de carpetas ──────────────────────────────────────────
    present_folders: list[dict] = []
    missing_folders: list[str] = []

    for req in sorted(req_folders):
        if req in zip_folders or any(req in f for f in zip_folders):
            present_folders.append({"required": req, "match": "exact"})
        else:
            fuzzy = _find_fuzzy_match(req, zip_folders, fuzzy_threshold)
            if fuzzy:
                fuzzy_candidate, fuzzy_score = fuzzy
                fuzzy_matches.append({
                    "required": req,
                    "closest": fuzzy_candidate,
                    "score": round(fuzzy_score * 100, 1),
                    "type": "folder",
                })
            else:
                missing_folders.append(req)

    # ── Archivos extra (en zip, no requeridos) ──────────────────────────
    required_found = {item["found"] for item in present_files}
    extra_files = sorted(zip_files - req_files - required_found)

    # ── Score y veredicto ───────────────────────────────────────────────
    total_required = len(req_files) + len(req_folders)
    total_present = len(present_files) + len(present_folders)
    total_missing = len(missing_files) + len(missing_folders)
    total_fuzzy = len([f for f in fuzzy_matches if "type" not in f or f.get("type") != "folder"])

    score = round((total_present / total_required * 100) if total_required > 0 else 100.0, 1)

    hard_pass = total_missing == 0
    strict_pass = hard_pass and (len(extra_files) == 0 if strict else True)

    return {
        "present_files": present_files,
        "missing_files": missing_files,
        "missing_folders": missing_folders,
        "present_folders": present_folders,
        "fuzzy_matches": fuzzy_matches,
        "extra_files": extra_files if show_extra else [],
        "all_extra_files": extra_files,
        "score": score,
        "passed": strict_pass,
        "strict_mode": strict,
        "total_required": total_required,
        "total_present": total_present,
        "total_missing": total_missing,
        "total_fuzzy": total_fuzzy,
        "zip_file_count": len(zip_data["files"]),
        "fuzzy_threshold": fuzzy_threshold,
    }
