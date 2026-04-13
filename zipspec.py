"""
zipspec.py — Entry point principal
Uso:
    python zipspec.py archivo.zip requisitos.pdf
    python zipspec.py archivo.zip manifiesto.yml --format json
    python zipspec.py --batch carpeta/ requisitos.pdf --format html --save reporte.html
    python zipspec.py archivo.zip requisitos.pdf --strict --verbose
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config.settings import load_config, merge_cli
from core.zip_reader import read_zip
from core.validator import validate
from core.batch import run_batch, batch_summary
from report.terminal import print_report, print_batch_report, batch_progress, console


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_source(source_path: str) -> str:
    """Determina el tipo de fuente según la extensión."""
    ext = Path(source_path).suffix.lower()
    if ext in (".yml", ".yaml"):
        return "manifest"
    if ext == ".pdf":
        return "pdf"
    return "unknown"


def _read_source(source_path: str, source_type: str) -> dict:
    """Lee el archivo fuente (PDF o YAML manifest)."""
    if source_type == "manifest":
        from core.yaml_reader import read_manifest
        return read_manifest(source_path)
    elif source_type == "pdf":
        from core.pdf_reader import read_pdf
        return read_pdf(source_path)
    else:
        raise ValueError(
            f"Formato de fuente no reconocido: '{Path(source_path).suffix}'. "
            "Use un archivo .pdf o .yml/.yaml"
        )


def _emit_report(
    fmt: str,
    zip_path: str,
    source_path: str,
    results: dict,
    zip_data: dict,
    req_data: dict,
    verbose: bool,
    quiet: bool,
    show_extra: bool,
    save_path: str | None,
) -> None:
    """Emite el reporte en el formato indicado."""
    if fmt == "json":
        from report.json_report import build_payload, print_json
        payload = build_payload(zip_path, source_path, results, zip_data, req_data)
        print_json(payload, save_path)

    elif fmt == "html":
        from report.html_report import generate_html
        html = generate_html(zip_path, source_path, results, zip_data, req_data)
        if save_path:
            Path(save_path).write_text(html, encoding="utf-8")
            console.print(f"[green]Reporte HTML guardado en:[/green] {save_path}")
        else:
            print(html)

    else:  # terminal (default)
        print_report(
            zip_path, source_path, results, zip_data, req_data,
            verbose=verbose, quiet=quiet, show_extra=show_extra,
        )
        if save_path:
            console.print(
                "[yellow]Advertencia:[/yellow] --save solo guarda en formatos json/html. "
                "Usa --format json o --format html para guardar."
            )


def _emit_batch_report(
    fmt: str,
    batch_results: list[dict],
    summary: dict,
    source_path: str,
    save_path: str | None,
) -> None:
    """Emite el reporte batch en el formato indicado."""
    if fmt == "json":
        from report.json_report import build_batch_payload, print_json
        payload = build_batch_payload(batch_results, summary, source_path)
        print_json(payload, save_path)

    elif fmt == "html":
        from report.html_report import generate_batch_html
        html = generate_batch_html(batch_results, summary, source_path)
        if save_path:
            Path(save_path).write_text(html, encoding="utf-8")
            console.print(f"[green]Reporte HTML batch guardado en:[/green] {save_path}")
        else:
            print(html)

    else:
        print_batch_report(batch_results, summary)


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zipspec",
        description=(
            "ZipSpec — Validador de archivos .zip contra requisitos.\n"
            "Compara la estructura de un .zip contra un PDF de instrucciones o un manifiesto YAML."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ejemplos:
  python zipspec.py tarea.zip enunciado.pdf
  python zipspec.py tarea.zip manifiesto.yml --format json --save resultado.json
  python zipspec.py tarea.zip enunciado.pdf --strict --verbose
  python zipspec.py tarea.zip enunciado.pdf --show-extra --fuzzy-threshold 0.75
  python zipspec.py --batch entregas/ enunciado.pdf --format html --save reporte.html
  python zipspec.py --generate-manifest  # crea un ejemplo de manifiesto YAML
        """,
    )

    # ── Posicionales ─────────────────────────────────────────────────────────
    parser.add_argument(
        "zip",
        nargs="?",
        help="Ruta al archivo .zip a validar (omitir en modo --batch o --generate-manifest)",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Ruta al PDF o manifest YAML con los requisitos",
    )

    # ── Modo batch ────────────────────────────────────────────────────────────
    batch_group = parser.add_argument_group("Modo batch")
    batch_group.add_argument(
        "--batch",
        metavar="CARPETA",
        help="Valida todos los .zip dentro de CARPETA contra la misma fuente",
    )

    # ── Formato de salida ─────────────────────────────────────────────────────
    output_group = parser.add_argument_group("Formato y salida")
    output_group.add_argument(
        "--format", "-f",
        choices=["terminal", "json", "html"],
        default=None,
        metavar="FORMAT",
        help="Formato de salida: terminal (default), json, html",
    )
    output_group.add_argument(
        "--save", "-o",
        metavar="RUTA",
        help="Guardar la salida en un archivo (para formatos json y html)",
    )
    output_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=None,
        help="Solo muestra el veredicto final (sin detalles de estructura)",
    )
    output_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=None,
        help="Muestra detalles de la extracción desde el PDF o manifest",
    )

    # ── Validación ────────────────────────────────────────────────────────────
    validation_group = parser.add_argument_group("Opciones de validación")
    validation_group.add_argument(
        "--strict",
        action="store_true",
        default=None,
        help="Modo estricto: falla si hay archivos extra no requeridos",
    )
    validation_group.add_argument(
        "--show-extra",
        action="store_true",
        default=None,
        help="Mostrar archivos presentes en el zip pero no requeridos",
    )
    validation_group.add_argument(
        "--fuzzy-threshold",
        type=float,
        metavar="0.0-1.0",
        default=None,
        help="Umbral de similitud para fuzzy matching (default: 0.82)",
    )
    validation_group.add_argument(
        "--ignore",
        nargs="+",
        metavar="PATRÓN",
        help="Patrones de archivos a ignorar dentro del zip (ej: *.pyc __pycache__/*)",
    )

    # ── Configuración ─────────────────────────────────────────────────────────
    config_group = parser.add_argument_group("Configuración")
    config_group.add_argument(
        "--config",
        metavar="RUTA",
        help="Ruta a archivo de configuración .zipspec.yml",
    )
    config_group.add_argument(
        "--generate-manifest",
        action="store_true",
        help="Genera un archivo de ejemplo example_manifest.yml en el directorio actual",
    )

    return parser


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Generar manifest de ejemplo ───────────────────────────────────────────
    if args.generate_manifest:
        from core.yaml_reader import generate_example_manifest
        generate_example_manifest()
        console.print("[green]Archivo[/green] example_manifest.yml [green]creado correctamente.[/green]")
        sys.exit(0)

    # ── Cargar configuración ──────────────────────────────────────────────────
    try:
        config = load_config(args.config)
    except Exception as e:
        console.print(f"[yellow]Advertencia al cargar config:[/yellow] {e}")
        config = {}

    settings = merge_cli(
        config,
        default_format=args.format,
        strict=args.strict if args.strict else None,
        show_extra=args.show_extra if args.show_extra else None,
        fuzzy_threshold=args.fuzzy_threshold,
        ignore_patterns=args.ignore,
        quiet=args.quiet if args.quiet else None,
        verbose=args.verbose if args.verbose else None,
    )

    fmt = settings["default_format"]
    strict = settings["strict"]
    show_extra = settings["show_extra"]
    fuzzy_threshold = settings["fuzzy_threshold"]
    ignore_patterns = settings["ignore_patterns"]
    quiet = settings.get("quiet", False)
    verbose = settings.get("verbose", False)

    # ── Modo batch ────────────────────────────────────────────────────────────
    if args.batch:
        source_path = args.source or args.zip  # zip puede ser la fuente si no se especificó source
        if not source_path:
            parser.error("En modo --batch debes especificar la fuente (PDF o manifest YAML).")

        source_type = _detect_source(source_path)
        try:
            req_data = _read_source(source_path, source_type)
        except Exception as e:
            console.print(f"[bold red]Error al leer fuente:[/bold red] {e}")
            sys.exit(1)

        try:
            with batch_progress() as progress:
                task = progress.add_task("Procesando zips...", total=None)

                def on_progress(zip_name: str, current: int, total: int) -> None:
                    progress.update(task, total=total, completed=current, description=f"[cyan]{zip_name}[/cyan]")

                batch_results = run_batch(
                    args.batch,
                    req_data,
                    ignore_patterns=ignore_patterns,
                    fuzzy_threshold=fuzzy_threshold,
                    strict=strict,
                    on_progress=on_progress,
                )
        except (NotADirectoryError, FileNotFoundError) as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

        summary = batch_summary(batch_results)
        _emit_batch_report(fmt, batch_results, summary, source_path, args.save)

        any_failed = any(r["result"] and not r["result"]["passed"] for r in batch_results)
        sys.exit(1 if any_failed else 0)

    # ── Modo individual ───────────────────────────────────────────────────────
    if not args.zip:
        parser.print_help()
        sys.exit(1)

    if not args.source:
        parser.error("Debes especificar la fuente de requisitos (PDF o manifest YAML).")

    source_type = _detect_source(args.source)

    try:
        zip_data = read_zip(args.zip, ignore_patterns=ignore_patterns)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[bold red]Error al leer .zip:[/bold red] {e}")
        sys.exit(1)

    try:
        req_data = _read_source(args.source, source_type)
    except Exception as e:
        console.print(f"[bold red]Error al leer fuente:[/bold red] {e}")
        sys.exit(1)

    results = validate(
        zip_data,
        req_data,
        fuzzy_threshold=fuzzy_threshold,
        strict=strict,
        show_extra=show_extra,
    )

    _emit_report(
        fmt, args.zip, args.source, results, zip_data, req_data,
        verbose=verbose, quiet=quiet, show_extra=show_extra, save_path=args.save,
    )

    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
