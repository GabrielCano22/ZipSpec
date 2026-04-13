"""
terminal.py
Reporte visual en terminal usando Rich.
Soporta modos: normal, verbose, quiet.
"""
from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Force UTF-8 on Windows so block/check characters render correctly
if sys.platform == "win32":
    import io
    _stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    console = Console(file=_stdout, highlight=True)
else:
    console = Console()


# ── Reporte individual ───────────────────────────────────────────────────────

def print_report(
    zip_path: str,
    source_path: str,
    results: dict,
    zip_data: dict,
    req_data: dict,
    verbose: bool = False,
    quiet: bool = False,
    show_extra: bool = False,
) -> None:
    if not quiet:
        _print_header(zip_path, source_path, req_data)
        _print_zip_structure(zip_data["tree"], zip_data["metadata"])

    if verbose:
        _print_verbose(req_data)

    if not quiet:
        _print_validation(results, show_extra)

    _print_verdict(results)


def _print_header(zip_path: str, source_path: str, req_data: dict) -> None:
    source_type = "Manifest YAML" if req_data.get("source") == "manifest" else "PDF"
    source_name = req_data.get("manifest_name", "") or ""
    name_line = f"\n[dim]Nombre:[/dim] {source_name}" if source_name else ""

    console.print()
    console.print(Panel(
        f"[bold cyan]ZipSpec[/bold cyan] - Validador de Archivos Comprimidos\n"
        f"[dim]ZIP:[/dim]    {zip_path}\n"
        f"[dim]Fuente:[/dim] [{source_type}] {source_path}{name_line}",
        border_style="cyan",
        padding=(1, 2),
    ))


def _print_zip_structure(tree: list[str], metadata: dict) -> None:
    console.print(f"\n[bold white]Estructura del .zip[/bold white]  [dim]({len(tree)} entradas)[/dim]")
    for entry in tree:
        is_dir = entry.endswith("/")
        depth = entry.rstrip("/").count("/")
        indent = "  " * depth
        name = entry.rstrip("/").split("/")[-1]
        icon = "[blue]DIR [/blue]" if is_dir else "[yellow]FILE[/yellow]"

        size_str = ""
        norm = entry.replace("\\", "/").rstrip("/")
        if not is_dir and norm in metadata:
            from core.zip_reader import format_size
            size_str = f" [dim]({format_size(metadata[norm]['size'])})[/dim]"

        console.print(f"  {indent}{icon} {name}{size_str}")


def _print_verbose(req_data: dict) -> None:
    console.print()
    console.print(Rule("[bold yellow]Modo Verbose - Extraccion desde fuente[/bold yellow]"))

    if req_data.get("source") == "pdf":
        details = req_data.get("extraction_details", [])
        if details:
            table = Table(title="Requisitos detectados en el PDF", box=box.SIMPLE, title_style="yellow")
            table.add_column("Estrategia", style="dim")
            table.add_column("Valor detectado", style="cyan")
            for d in details[:40]:
                table.add_row(d.get("strategy", "-"), d.get("value", "-"))
            console.print(table)
        else:
            console.print("[yellow]No se detectaron requisitos en el PDF.[/yellow]")
    else:
        files = req_data.get("required_files", set())
        folders = req_data.get("required_folders", set())
        console.print(f"  Archivos requeridos: [cyan]{len(files)}[/cyan]")
        console.print(f"  Carpetas requeridas: [cyan]{len(folders)}[/cyan]")
        if req_data.get("manifest_description"):
            console.print(f"  Descripcion: [dim]{req_data['manifest_description']}[/dim]")


def _print_validation(results: dict, show_extra: bool = False) -> None:
    console.print()

    # Presentes (exactos)
    exact = [r for r in results["present_files"] if r["match"] == "exact"]
    name_only = [r for r in results["present_files"] if r["match"] == "name_only"]

    if exact:
        table = Table(
            title=f"Archivos Requeridos - Presentes ({len(exact)})",
            box=box.SIMPLE,
            title_style="bold green",
        )
        table.add_column("[OK]  Archivo", style="green")
        for r in exact:
            table.add_row(r["required"])
        console.print(table)

    if name_only:
        table = Table(
            title=f"Archivos - Encontrados (ruta distinta) ({len(name_only)})",
            box=box.SIMPLE,
            title_style="yellow",
        )
        table.add_column("Requerido", style="yellow")
        table.add_column("Encontrado en", style="dim")
        for r in name_only:
            table.add_row(r["required"], r["found"])
        console.print(table)

    # Carpetas presentes
    if results["present_folders"]:
        table = Table(
            title=f"Carpetas Requeridas - Presentes ({len(results['present_folders'])})",
            box=box.SIMPLE,
            title_style="bold green",
        )
        table.add_column("[OK]  Carpeta", style="green")
        for r in results["present_folders"]:
            table.add_row(r["required"])
        console.print(table)

    # Fuzzy matches (advertencia)
    if results["fuzzy_matches"]:
        table = Table(
            title=f"Coincidencias Aproximadas - Revisar ({len(results['fuzzy_matches'])})",
            box=box.SIMPLE,
            title_style="bold yellow",
        )
        table.add_column("Requerido", style="yellow")
        table.add_column("Mas cercano en zip", style="cyan")
        table.add_column("Similitud", justify="right")
        for fm in results["fuzzy_matches"]:
            score_color = "green" if fm["score"] >= 90 else "yellow"
            table.add_row(
                fm["required"],
                fm["closest"],
                f"[{score_color}]{fm['score']}%[/{score_color}]",
            )
        console.print(table)

    # Faltantes
    if results["missing_files"]:
        table = Table(
            title=f"Archivos Requeridos - FALTANTES ({len(results['missing_files'])})",
            box=box.SIMPLE,
            title_style="bold red",
        )
        table.add_column("[!!] Archivo faltante", style="red")
        for f in results["missing_files"]:
            table.add_row(f)
        console.print(table)

    if results["missing_folders"]:
        table = Table(
            title=f"Carpetas Requeridas - FALTANTES ({len(results['missing_folders'])})",
            box=box.SIMPLE,
            title_style="bold red",
        )
        table.add_column("[!!] Carpeta faltante", style="red")
        for f in results["missing_folders"]:
            table.add_row(f)
        console.print(table)

    # Extra (opcional)
    if show_extra and results["extra_files"]:
        table = Table(
            title=f"Archivos No Requeridos ({len(results['extra_files'])})",
            box=box.SIMPLE,
            title_style="dim",
        )
        table.add_column("Archivo extra en zip", style="dim")
        for f in results["extra_files"]:
            table.add_row(f)
        console.print(table)


def _print_verdict(results: dict) -> None:
    score = results["score"]
    passed = results["passed"]

    bar_filled = int(score / 5)
    bar = "#" * bar_filled + "." * (20 - bar_filled)
    color = "green" if score == 100 else ("yellow" if score >= 60 else "red")

    if passed:
        verdict = "[OK] CUMPLE COMPLETAMENTE"
        verdict_style = "bold green"
    elif results["total_missing"] == 0 and results["total_fuzzy"] > 0:
        verdict = "[!]  CUMPLE CON ADVERTENCIAS - Revisar coincidencias aproximadas"
        verdict_style = "bold yellow"
    else:
        verdict = "[!!] NO CUMPLE - Hay elementos faltantes"
        verdict_style = "bold red"

    strict_note = "  [dim](modo strict activado)[/dim]" if results["strict_mode"] else ""

    console.print(Panel(
        f"[{verdict_style}]{verdict}[/{verdict_style}]{strict_note}\n\n"
        f"Cumplimiento: [{color}]{bar}[/{color}] {score}%\n"
        f"[dim]Archivos en zip: {results['zip_file_count']} | "
        f"Requeridos: {results['total_required']} | "
        f"Presentes: {results['total_present']} | "
        f"Faltantes: {results['total_missing']} | "
        f"Fuzzy: {results['total_fuzzy']}[/dim]",
        border_style=color,
        padding=(1, 2),
    ))
    console.print()


# ── Reporte batch ────────────────────────────────────────────────────────────

def print_batch_report(batch_results: list[dict], summary: dict) -> None:
    console.print()
    console.print(Rule("[bold cyan]ZipSpec - Reporte Batch[/bold cyan]"))

    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Archivo ZIP", style="white", min_width=25)
    table.add_column("Score", justify="center", min_width=8)
    table.add_column("Faltantes", justify="center")
    table.add_column("Fuzzy", justify="center")
    table.add_column("Estado", justify="center", min_width=10)

    for r in batch_results:
        if r["error"]:
            table.add_row(r["zip_name"], "-", "-", "-", "[red]ERROR[/red]")
            continue

        result = r["result"]
        score = result["score"]
        score_color = "green" if score == 100 else ("yellow" if score >= 60 else "red")
        estado = "[green]PASA[/green]" if result["passed"] else "[red]FALLA[/red]"

        table.add_row(
            r["zip_name"],
            f"[{score_color}]{score}%[/{score_color}]",
            str(result["total_missing"]),
            str(result["total_fuzzy"]),
            estado,
        )

    console.print(table)

    rate_color = "green" if summary["pass_rate"] == 100 else ("yellow" if summary["pass_rate"] >= 60 else "red")
    console.print(Panel(
        f"[bold]Resumen Batch[/bold]\n\n"
        f"Total evaluados : {summary['total']}\n"
        f"[green]Aprobados[/green]       : {summary['passed']}\n"
        f"[red]Fallidos[/red]        : {summary['failed']}\n"
        f"[dim]Errores[/dim]         : {summary['errors']}\n\n"
        f"Tasa de aprobacion : [{rate_color}]{summary['pass_rate']}%[/{rate_color}]\n"
        f"Score promedio     : {summary['avg_score']}%  "
        f"[dim](min: {summary['min_score']}% / max: {summary['max_score']}%)[/dim]",
        border_style=rate_color,
        padding=(1, 2),
    ))
    console.print()


def batch_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}[/cyan]"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
