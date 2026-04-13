"""
Endpoints de la API de ZipSpec.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from core.zip_reader import read_zip
from core.pdf_reader import read_pdf
from core.yaml_reader import read_manifest
from core.validator import validate
from report.json_report import build_payload

router = APIRouter()

ALLOWED_SOURCE_EXT = {".pdf", ".yml", ".yaml"}


def _save_upload(upload: UploadFile, dest: Path) -> Path:
    """Guarda un UploadFile en disco y retorna su path."""
    target = dest / upload.filename
    with open(target, "wb") as f:
        f.write(upload.file.read())
    return target


def _detect_and_read_source(source_path: Path) -> dict:
    ext = source_path.suffix.lower()
    if ext in (".yml", ".yaml"):
        return read_manifest(str(source_path))
    elif ext == ".pdf":
        return read_pdf(str(source_path))
    raise HTTPException(400, f"Formato de fuente no soportado: {ext}")


@router.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@router.post("/validate")
async def validate_zip(
    zip_file: UploadFile = File(...),
    source_file: UploadFile = File(...),
    strict: bool = Form(False),
    show_extra: bool = Form(True),
    fuzzy_threshold: float = Form(0.82),
    ignore_patterns: str = Form(""),
):
    """Valida un .zip contra un PDF o manifest YAML."""
    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "El archivo debe ser un .zip")

    source_ext = Path(source_file.filename).suffix.lower()
    if source_ext not in ALLOWED_SOURCE_EXT:
        raise HTTPException(400, f"Fuente debe ser .pdf, .yml o .yaml (recibido: {source_ext})")

    tmp_dir = Path(tempfile.mkdtemp(prefix="zipspec_"))
    try:
        zip_path = _save_upload(zip_file, tmp_dir)
        source_path = _save_upload(source_file, tmp_dir)

        patterns = [p.strip() for p in ignore_patterns.split(",") if p.strip()] or None

        zip_data = read_zip(str(zip_path), ignore_patterns=patterns)
        req_data = _detect_and_read_source(source_path)

        results = validate(
            zip_data, req_data,
            fuzzy_threshold=fuzzy_threshold,
            strict=strict,
            show_extra=show_extra,
        )

        payload = build_payload(
            str(zip_path), str(source_path),
            results, zip_data, req_data,
        )
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al procesar: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/validate/batch")
async def validate_batch(
    zip_files: list[UploadFile] = File(...),
    source_file: UploadFile = File(...),
    strict: bool = Form(False),
    fuzzy_threshold: float = Form(0.82),
):
    """Valida multiples .zip contra la misma fuente."""
    source_ext = Path(source_file.filename).suffix.lower()
    if source_ext not in ALLOWED_SOURCE_EXT:
        raise HTTPException(400, f"Fuente debe ser .pdf, .yml o .yaml")

    tmp_dir = Path(tempfile.mkdtemp(prefix="zipspec_batch_"))
    try:
        source_path = _save_upload(source_file, tmp_dir)
        req_data = _detect_and_read_source(source_path)

        results_list = []
        for zf in zip_files:
            if not zf.filename.lower().endswith(".zip"):
                results_list.append({
                    "zip_name": zf.filename,
                    "error": "No es un archivo .zip",
                    "result": None,
                })
                continue

            try:
                zip_path = _save_upload(zf, tmp_dir)
                zip_data = read_zip(str(zip_path))
                result = validate(
                    zip_data, req_data,
                    fuzzy_threshold=fuzzy_threshold,
                    strict=strict,
                    show_extra=True,
                )
                results_list.append({
                    "zip_name": zf.filename,
                    "error": None,
                    "result": result,
                })
            except Exception as e:
                results_list.append({
                    "zip_name": zf.filename,
                    "error": str(e),
                    "result": None,
                })

        # Estadisticas
        valid = [r for r in results_list if r["result"]]
        scores = [r["result"]["score"] for r in valid]
        passed = sum(1 for r in valid if r["result"]["passed"])
        total = len(results_list)

        return {
            "mode": "batch",
            "summary": {
                "total": total,
                "passed": passed,
                "failed": len(valid) - passed,
                "errors": total - len(valid),
                "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "pass_rate": round(passed / total * 100, 1) if total else 0,
            },
            "results": results_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al procesar batch: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
