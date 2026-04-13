"""
html_report.py
Genera un reporte HTML autocontenido y estilizado.
No requiere dependencias externas en el navegador.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f0f11; color: #e2e8f0; line-height: 1.6; }
.container { max-width: 900px; margin: 0 auto; padding: 2rem; }
header { text-align: center; padding: 3rem 0 2rem; border-bottom: 1px solid #1e1e2e; }
header h1 { font-size: 2.2rem; font-weight: 800; letter-spacing: -1px;
  background: linear-gradient(135deg, #6366f1, #a855f7, #d946ef);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
header p { color: #64748b; font-size: 0.9rem; margin-top: 0.5rem; }
.meta { display: flex; gap: 1.5rem; flex-wrap: wrap; margin: 1.5rem 0;
  background: #1a1a2e; border-radius: 12px; padding: 1rem 1.5rem; border: 1px solid #2d2d4e; }
.meta-item { display: flex; flex-direction: column; }
.meta-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; }
.meta-value { font-size: 0.9rem; color: #94a3b8; word-break: break-all; }
.verdict { border-radius: 16px; padding: 1.5rem 2rem; margin: 2rem 0; border: 1px solid; }
.verdict.pass  { background: rgba(34,197,94,0.08); border-color: rgba(34,197,94,0.3); }
.verdict.warn  { background: rgba(234,179,8,0.08); border-color: rgba(234,179,8,0.3); }
.verdict.fail  { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.3); }
.verdict-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.8rem; }
.verdict.pass .verdict-title  { color: #4ade80; }
.verdict.warn .verdict-title  { color: #facc15; }
.verdict.fail .verdict-title  { color: #f87171; }
.score-bar-wrap { margin: 0.8rem 0; }
.score-label { font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.4rem; }
.score-bar { background: #1e1e2e; border-radius: 999px; height: 12px; overflow: hidden; }
.score-fill { height: 100%; border-radius: 999px; transition: width 1s ease; }
.score-fill.green { background: linear-gradient(90deg, #4ade80, #22c55e); }
.score-fill.yellow { background: linear-gradient(90deg, #facc15, #eab308); }
.score-fill.red { background: linear-gradient(90deg, #f87171, #ef4444); }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; margin: 2rem 0; }
.stat-card { background: #1a1a2e; border: 1px solid #2d2d4e; border-radius: 12px; padding: 1rem; text-align: center; }
.stat-number { font-size: 2rem; font-weight: 700; }
.stat-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
.green { color: #4ade80; } .yellow { color: #facc15; } .red { color: #f87171; } .blue { color: #60a5fa; } .gray { color: #64748b; }
section { margin: 2rem 0; }
section h2 { font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
  color: #94a3b8; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #1e1e2e; }
.file-list { list-style: none; display: flex; flex-direction: column; gap: 0.4rem; }
.file-list li { display: flex; align-items: center; gap: 0.6rem; padding: 0.5rem 0.8rem;
  border-radius: 8px; font-size: 0.875rem; font-family: 'Cascadia Code', 'Fira Code', monospace; }
.file-list li.present { background: rgba(34,197,94,0.06); color: #4ade80; }
.file-list li.missing { background: rgba(239,68,68,0.06); color: #f87171; }
.file-list li.fuzzy   { background: rgba(234,179,8,0.06); color: #facc15; }
.file-list li.extra   { background: rgba(100,116,139,0.06); color: #64748b; }
.file-list .badge { font-size: 0.7rem; padding: 0.1rem 0.5rem; border-radius: 999px; font-family: sans-serif; }
.badge.exact { background: rgba(34,197,94,0.15); color: #4ade80; }
.badge.name  { background: rgba(234,179,8,0.15); color: #facc15; }
.structure { background: #1a1a2e; border: 1px solid #2d2d4e; border-radius: 12px; padding: 1rem 1.5rem;
  font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 0.8rem; overflow-x: auto; }
.structure div { padding: 2px 0; color: #94a3b8; }
.structure .dir { color: #60a5fa; }
footer { text-align: center; padding: 2rem 0; color: #3d3d5c; font-size: 0.8rem; border-top: 1px solid #1e1e2e; margin-top: 3rem; }
"""


def _score_color(score: float) -> str:
    if score == 100: return "green"
    if score >= 60: return "yellow"
    return "red"


def _verdict_class(results: dict) -> str:
    if results["passed"]: return "pass"
    if results["total_missing"] == 0: return "warn"
    return "fail"


def _verdict_text(results: dict) -> str:
    if results["passed"]: return "✔ Cumple completamente"
    if results["total_missing"] == 0: return "⚠ Cumple con advertencias"
    return "✘ No cumple — hay elementos faltantes"


def generate_html(
    zip_path: str,
    source_path: str,
    results: dict,
    zip_data: dict,
    req_data: dict,
) -> str:
    score = results["score"]
    color = _score_color(score)
    vc = _verdict_class(results)
    vtext = _verdict_text(results)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_type = "Manifest YAML" if req_data.get("source") == "manifest" else "PDF"

    # Estructura del zip
    tree_html = ""
    for entry in zip_data.get("tree", []):
        is_dir = entry.endswith("/")
        depth = entry.rstrip("/").count("/")
        indent = "&nbsp;" * (depth * 4)
        name = entry.rstrip("/").split("/")[-1]
        icon = "📁" if is_dir else "📄"
        cls = "dir" if is_dir else ""
        tree_html += f'<div class="{cls}">{indent}{icon} {name}</div>\n'

    # Archivos presentes
    present_html = ""
    for r in results["present_files"]:
        badge = '<span class="badge exact">exacto</span>' if r["match"] == "exact" else '<span class="badge name">ruta distinta</span>'
        present_html += f'<li class="present">✔ {r["required"]} {badge}</li>'
    for r in results["present_folders"]:
        present_html += f'<li class="present">✔ 📁 {r["required"]}</li>'

    # Fuzzy
    fuzzy_html = ""
    for fm in results["fuzzy_matches"]:
        fuzzy_html += f'<li class="fuzzy">⚠ {fm["required"]} → {fm["closest"]} ({fm["score"]}%)</li>'

    # Faltantes
    missing_html = ""
    for f in results["missing_files"]:
        missing_html += f'<li class="missing">✘ {f}</li>'
    for f in results["missing_folders"]:
        missing_html += f'<li class="missing">✘ 📁 {f}</li>'

    # Extra
    extra_html = ""
    for f in results.get("all_extra_files", []):
        extra_html += f'<li class="extra">◦ {f}</li>'

    present_section = f"""
    <section>
      <h2>Presentes ({results['total_present']})</h2>
      <ul class="file-list">{present_html}</ul>
    </section>""" if present_html else ""

    fuzzy_section = f"""
    <section>
      <h2>Coincidencias aproximadas — revisar ({results['total_fuzzy']})</h2>
      <ul class="file-list">{fuzzy_html}</ul>
    </section>""" if fuzzy_html else ""

    missing_section = f"""
    <section>
      <h2>Faltantes ({results['total_missing']})</h2>
      <ul class="file-list">{missing_html}</ul>
    </section>""" if missing_html else ""

    extra_section = f"""
    <section>
      <h2>Archivos no requeridos ({len(results.get('all_extra_files', []))})</h2>
      <ul class="file-list">{extra_html}</ul>
    </section>""" if extra_html else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ZipSpec — {Path(zip_path).name}</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>ZipSpec</h1>
      <p>Reporte de validación de archivos comprimidos</p>
    </header>

    <div class="meta">
      <div class="meta-item">
        <span class="meta-label">Archivo ZIP</span>
        <span class="meta-value">{Path(zip_path).name}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Fuente ({source_type})</span>
        <span class="meta-value">{Path(source_path).name}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Generado</span>
        <span class="meta-value">{now}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Modo</span>
        <span class="meta-value">{'Strict' if results['strict_mode'] else 'Normal'}</span>
      </div>
    </div>

    <div class="verdict {vc}">
      <div class="verdict-title">{vtext}</div>
      <div class="score-bar-wrap">
        <div class="score-label">Cumplimiento: {score}%</div>
        <div class="score-bar">
          <div class="score-fill {color}" style="width: {score}%"></div>
        </div>
      </div>
    </div>

    <div class="stats">
      <div class="stat-card">
        <div class="stat-number blue">{results['zip_file_count']}</div>
        <div class="stat-label">En ZIP</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{results['total_required']}</div>
        <div class="stat-label">Requeridos</div>
      </div>
      <div class="stat-card">
        <div class="stat-number green">{results['total_present']}</div>
        <div class="stat-label">Presentes</div>
      </div>
      <div class="stat-card">
        <div class="stat-number red">{results['total_missing']}</div>
        <div class="stat-label">Faltantes</div>
      </div>
      <div class="stat-card">
        <div class="stat-number yellow">{results['total_fuzzy']}</div>
        <div class="stat-label">Fuzzy</div>
      </div>
    </div>

    {present_section}
    {fuzzy_section}
    {missing_section}
    {extra_section}

    <section>
      <h2>Estructura del ZIP</h2>
      <div class="structure">{tree_html}</div>
    </section>

    <footer>Generado por ZipSpec v2.0.0 — {now}</footer>
  </div>
</body>
</html>"""


def save_html(html: str, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def generate_batch_html(batch_results: list[dict], summary: dict, source_path: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rate_color = _score_color(summary["pass_rate"])

    rows = ""
    for r in batch_results:
        if r["error"]:
            rows += f'<tr><td>{r["zip_name"]}</td><td>—</td><td>—</td><td>—</td><td class="red">ERROR</td></tr>'
            continue
        res = r["result"]
        sc = _score_color(res["score"])
        estado = '<span class="green">✔ PASA</span>' if res["passed"] else '<span class="red">✘ FALLA</span>'
        rows += (
            f'<tr>'
            f'<td style="font-family:monospace">{r["zip_name"]}</td>'
            f'<td class="{sc}" style="text-align:center">{res["score"]}%</td>'
            f'<td class="red" style="text-align:center">{res["total_missing"]}</td>'
            f'<td class="yellow" style="text-align:center">{res["total_fuzzy"]}</td>'
            f'<td style="text-align:center">{estado}</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>ZipSpec — Reporte Batch</title>
  <style>
    {_CSS}
    table {{ width:100%; border-collapse:collapse; background:#1a1a2e; border-radius:12px; overflow:hidden; }}
    th {{ background:#2d2d4e; padding:0.75rem 1rem; text-align:left; font-size:0.8rem;
         text-transform:uppercase; letter-spacing:0.5px; color:#94a3b8; }}
    td {{ padding:0.7rem 1rem; border-bottom:1px solid #2d2d4e; font-size:0.875rem; }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:rgba(255,255,255,0.02); }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>ZipSpec — Batch</h1>
      <p>Reporte de validación masiva · {now}</p>
    </header>
    <div class="meta">
      <div class="meta-item"><span class="meta-label">Fuente</span><span class="meta-value">{Path(source_path).name}</span></div>
      <div class="meta-item"><span class="meta-label">Total evaluados</span><span class="meta-value">{summary['total']}</span></div>
      <div class="meta-item"><span class="meta-label">Score promedio</span><span class="meta-value">{summary['avg_score']}%</span></div>
    </div>
    <div class="verdict {'pass' if summary['pass_rate']==100 else ('warn' if summary['pass_rate']>=60 else 'fail')}">
      <div class="verdict-title">Tasa de aprobación: {summary['pass_rate']}%</div>
      <div class="score-bar-wrap">
        <div class="score-bar"><div class="score-fill {rate_color}" style="width:{summary['pass_rate']}%"></div></div>
      </div>
    </div>
    <div class="stats">
      <div class="stat-card"><div class="stat-number blue">{summary['total']}</div><div class="stat-label">Total</div></div>
      <div class="stat-card"><div class="stat-number green">{summary['passed']}</div><div class="stat-label">Aprobados</div></div>
      <div class="stat-card"><div class="stat-number red">{summary['failed']}</div><div class="stat-label">Fallidos</div></div>
      <div class="stat-card"><div class="stat-number gray">{summary['errors']}</div><div class="stat-label">Errores</div></div>
    </div>
    <section>
      <h2>Resultados individuales</h2>
      <table>
        <thead><tr><th>Archivo ZIP</th><th>Score</th><th>Faltantes</th><th>Fuzzy</th><th>Estado</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <footer>Generado por ZipSpec v2.0.0 — {now}</footer>
  </div>
</body>
</html>"""
