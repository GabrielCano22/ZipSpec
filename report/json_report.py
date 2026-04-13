"""
json_report.py
Genera salida en formato JSON estructurado.
Útil para integración en pipelines CI/CD o procesamiento programático.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def build_payload(
    zip_path: str,
    source_path: str,
    results: dict,
    zip_data: dict,
    req_data: dict,
) -> dict:
    """Construye el payload JSON completo."""
    return {
        "zipspec_version": "2.0.0",
        "generated_at": datetime.now().isoformat(),
        "input": {
            "zip": zip_path,
            "zip_name": Path(zip_path).name,
            "source": source_path,
            "source_type": req_data.get("source", "unknown"),
        },
        "summary": {
            "passed": results["passed"],
            "score": results["score"],
            "strict_mode": results["strict_mode"],
            "total_required": results["total_required"],
            "total_present": results["total_present"],
            "total_missing": results["total_missing"],
            "total_fuzzy": results["total_fuzzy"],
            "zip_file_count": results["zip_file_count"],
        },
        "details": {
            "present_files": results["present_files"],
            "missing_files": results["missing_files"],
            "present_folders": results["present_folders"],
            "missing_folders": results["missing_folders"],
            "fuzzy_matches": results["fuzzy_matches"],
            "extra_files": results.get("all_extra_files", []),
        },
        "zip_structure": zip_data.get("tree", []),
    }


def build_batch_payload(batch_results: list[dict], summary: dict, source_path: str) -> dict:
    """Construye el payload JSON para un reporte batch."""
    items = []
    for r in batch_results:
        if r["error"]:
            items.append({"zip": r["zip_name"], "error": r["error"]})
        else:
            items.append({
                "zip": r["zip_name"],
                "passed": r["result"]["passed"],
                "score": r["result"]["score"],
                "missing_files": r["result"]["missing_files"],
                "missing_folders": r["result"]["missing_folders"],
                "fuzzy_matches": r["result"]["fuzzy_matches"],
            })

    return {
        "zipspec_version": "2.0.0",
        "generated_at": datetime.now().isoformat(),
        "mode": "batch",
        "source": source_path,
        "summary": summary,
        "results": items,
    }


def print_json(payload: dict, save_path: str | None = None) -> None:
    output = json.dumps(payload, indent=2, ensure_ascii=False)
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)
