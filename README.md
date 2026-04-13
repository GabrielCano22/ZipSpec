# ZipSpec

Herramienta full-stack para validar la estructura de archivos `.zip` contra requisitos definidos en un PDF de instrucciones o un manifiesto YAML. Pensada para profesores que necesitan verificar entregas de estudiantes, o para cualquier flujo de trabajo donde se necesite asegurar que un comprimido contiene exactamente lo que debe contener.

---

## Que hace

Sube un `.zip` y un archivo de requisitos (PDF o YAML), y ZipSpec te dice:

- Que archivos y carpetas estan presentes
- Cuales faltan
- Si hay archivos con nombres similares (fuzzy matching)
- Archivos extra que no fueron solicitados
- Un puntaje de cumplimiento de 0 a 100%

Disponible como **CLI en terminal**, **API REST**, o **interfaz web**.

---

## Stack

| Capa | Tecnologias |
|------|-------------|
| **Frontend** | React, TypeScript, Vite, Framer Motion |
| **Backend/API** | Python, FastAPI, Uvicorn |
| **Core** | pdfplumber, PyYAML, difflib |
| **Reportes** | Rich (terminal), JSON, HTML autocontenido |
| **Infra** | Docker, Docker Compose |

---

## Estructura del proyecto

```
ZipSpec/
├── api/                  # API REST (FastAPI)
│   ├── main.py           # App y middlewares
│   └── routes.py         # Endpoints: /validate, /validate/batch, /health
├── core/                 # Logica de negocio
│   ├── zip_reader.py     # Lee y parsea archivos .zip
│   ├── pdf_reader.py     # Extrae requisitos desde PDFs
│   ├── yaml_reader.py    # Lee manifiestos YAML
│   ├── validator.py      # Comparacion y fuzzy matching
│   └── batch.py          # Procesamiento por lotes
├── report/               # Generacion de reportes
│   ├── terminal.py       # Reporte en terminal con Rich
│   ├── json_report.py    # Salida JSON estructurada
│   └── html_report.py    # Reporte HTML autocontenido
├── config/
│   └── settings.py       # Carga de .zipspec.yml
├── frontend/             # Interfaz web (React + Vite)
│   └── src/
│       ├── components/   # DropZone, ScoreRing, ResultPanel, FileTree...
│       ├── lib/api.ts    # Cliente HTTP para la API
│       └── types/        # Tipos TypeScript
├── tests/                # Tests con pytest
├── zipspec.py            # Entry point CLI
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Instalacion

### Opcion 1: Docker (recomendado)

```bash
git clone https://github.com/tu-usuario/zipspec.git
cd zipspec
docker-compose up --build
```

Esto levanta el backend en `http://localhost:8000` y el frontend en `http://localhost:5173`.

### Opcion 2: Manual

**Backend:**

```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## Uso por CLI

```bash
# Validacion basica
python zipspec.py tarea.zip enunciado.pdf

# Contra un manifiesto YAML
python zipspec.py tarea.zip requisitos.yml

# Modo estricto (falla si hay archivos extra)
python zipspec.py tarea.zip enunciado.pdf --strict

# Salida en JSON
python zipspec.py tarea.zip enunciado.pdf --format json --save resultado.json

# Reporte HTML
python zipspec.py tarea.zip enunciado.pdf --format html --save reporte.html

# Validar todos los .zip de una carpeta
python zipspec.py --batch entregas/ enunciado.pdf

# Solo el veredicto
python zipspec.py tarea.zip enunciado.pdf --quiet

# Ver archivos extra y detalles de extraccion
python zipspec.py tarea.zip enunciado.pdf --show-extra --verbose

# Generar un manifiesto YAML de ejemplo
python zipspec.py --generate-manifest
```

### Flags disponibles

| Flag | Descripcion |
|------|-------------|
| `--format` | `terminal`, `json`, o `html` |
| `--save` | Ruta donde guardar el reporte |
| `--strict` | Falla si hay archivos no requeridos |
| `--show-extra` | Muestra archivos extra en el zip |
| `--quiet` | Solo imprime el veredicto |
| `--verbose` | Detalla la extraccion del PDF |
| `--fuzzy-threshold` | Umbral de similitud (default: 0.82) |
| `--ignore` | Patrones a ignorar (ej: `*.pyc`) |
| `--batch` | Carpeta con multiples .zip |
| `--config` | Ruta a `.zipspec.yml` personalizado |
| `--generate-manifest` | Crea un `example_manifest.yml` |

---

## API REST

La API expone tres endpoints:

**GET /api/health** — Estado del servicio

**POST /api/validate** — Valida un .zip contra una fuente
- `zip_file`: archivo .zip (multipart)
- `source_file`: archivo .pdf, .yml o .yaml (multipart)
- `strict`, `show_extra`, `fuzzy_threshold`: opciones (form fields)

**POST /api/validate/batch** — Valida multiples .zip
- `zip_files`: lista de archivos .zip (multipart)
- `source_file`: fuente unica (multipart)

---

## Formato del manifiesto YAML

```yaml
name: "Proyecto Final"
description: "Entrega del modulo de programacion"

files:
  - main.py
  - requirements.txt
  - README.md
  - src/utils.py
  - tests/test_main.py

folders:
  - src
  - tests
```

---

## Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Configuracion

Puedes crear un `.zipspec.yml` en el directorio de trabajo o en tu home para definir valores por defecto:

```yaml
default_format: terminal
fuzzy_threshold: 0.82
strict: false
show_extra: false
ignore_patterns:
  - "__pycache__/"
  - ".DS_Store"
  - "*.pyc"
```

---

## Licencia

MIT
