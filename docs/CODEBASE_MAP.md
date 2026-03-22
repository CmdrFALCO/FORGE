# FORGE Codebase Map

## Snapshot

- Project: FORGE
- Current branch: `main`
- Latest committed GUI refactor: `3dd5fd4` (`refactor(gui): move calculator into Cell Calculator page, polish landing, retire legacy app`)
- Latest verified test baseline: `1516 passed, 3 skipped, 18 deselected`
- Python package modules under `forge/`: `156`
- Python test files under `tests/`: `78`
- Markdown docs under `docs/`: `12`

## Top-Level Structure

| Path | Purpose |
|---|---|
| `forge/` | Main Python package |
| `tests/` | Pytest suite for engine, API, AXIOM, GUI, materials, and ML |
| `docs/` | Published project docs, archetype JSON examples, and project assets |
| `docs/_temp/` | Working notes, prompts, and temporary planning artifacts |
| `experiments/` | Research-oriented ML/autoresearch scripts and outputs |
| `demos/` | n8n workflow demos |
| `data/` | Runtime data inputs such as reference cells and recorded AXIOM demos |
| `Dockerfile` | Multi-stage Python 3.11 image for Streamlit + API (no torch/scipy/pybamm) |
| `docker-compose.yml` | Orchestrates nginx, streamlit, api, certbot services |
| `.dockerignore` | Excludes .git, __pycache__, .venv311, experiments, tests from Docker context |
| `docker/` | Deployment configs: nginx reverse proxy, landing page, SSL |
| `start_forge_app.cmd` | Local Streamlit launcher |
| `start_forge_api.cmd` | Local FastAPI launcher |
| `setup_forge_env.cmd` | Python 3.11 local environment bootstrap |

## Docker / Web Deployment

### `docker/nginx/`

Reverse proxy and static landing page for `forge.cristian-leu.de`.

- `nginx-http-only.conf`: HTTP-only config for initial deploy and certbot cert acquisition
- `nginx-ssl.conf`: Full SSL config, swapped in after certbot succeeds
- `.htpasswd`: Basic auth credentials (generated on rig, not in git)
- `landing/index.html`: Portfolio-grade landing page (dark theme, DAEDALUS tabs, nav cards)
- `landing/style.css`: Landing page styles

### `Dockerfile`

Two-stage build: `base` (python:3.11-slim + `pip install -e ".[gui]"`) → `app` (Streamlit config, ports 8501/8000). Excludes torch, scipy, and pybamm — web services don't need them.

### `docker-compose.yml`

Four services on `forge-net` bridge network:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `nginx` | nginx:alpine | 80, 443 | Reverse proxy, basic auth, rate limiting, static landing |
| `streamlit` | built from Dockerfile | 8501 | Streamlit GUI at `/app/` |
| `api` | built from Dockerfile | 8000 | FastAPI at `/api/` (root_path via `FORGE_API_ROOT_PATH` env var) |
| `certbot` | certbot/certbot | — | SSL cert acquisition and auto-renewal |

## Package Map

### `forge/api/`

FastAPI service layer for headless use and n8n integration.

- `app.py`: FastAPI app construction and router registration; reads `FORGE_API_ROOT_PATH` env var for reverse-proxy subpath
- `deps.py`: backend dependency selection helpers
- `routes/`
  - `system.py`: `/health`, `/reference-cells`
  - `validation.py`: validation endpoint
  - `calculation.py`: calculation endpoint
  - `generation.py`: raw LLM generation / parse endpoint surface
  - `pipeline.py`: AXIOM end-to-end pipeline endpoint
- `schemas/models.py`: Pydantic request/response models

### `forge/axiom/`

Neuro-symbolic supervision layer for LLM-assisted cell design.

- `generator/`
  - `prompt_builder.py`
  - `parser.py`
- `supervisor/`
  - `driver.py`
  - `result.py`
- `backends/backends.py`: Claude/Ollama/backend adapters
- `validator/`, `feedback/`: typed scaffolding stubs

### `forge/cli/`

Command-line entrypoints and utility functions.

- `main.py`: CLI interface and reference/PyBaMM helpers

### `forge/engine/`

Core deterministic engineering layer.

- `calculations/`: mass, energy, stack, winding, housing calculations
- `calculators/`: pouch, prismatic, cylindrical calculators plus `BaseCalculator`
- `conversion/`: template and reference mapping to engine input objects
- `cost/`: material and cell cost estimation
- `geometry/`: archetype loading, detailed geometry generation, tabs, terminals, validation
- `models/`: pouch, prismatic, cylindrical, materials, geometry, stack, and results dataclasses
- `reference/`: runtime reference-cell loading API
- `validation/`: schema, constraints, result validation, and validation pipeline
- `cad/`: Build123d/FreeCAD generators and export helpers

### `forge/export/`

Structured export helpers.

- `csv_export.py`
- `json_export.py`

### `forge/gui/`

Streamlit GUI layer.

- `app.py`: landing page and multipage entrypoint
- `axiom_pipeline.py`: tracked AXIOM wrapper for GUI execution and replay
- `pages/1_Cell_Calculator.py`: full calculator UI
- `pages/2_CAD_Export.py`: CAD export page
- `pages/3_Geometry_Viewer.py`: geometry viewer page
- `pages/4_AXIOM_Designer.py`: AXIOM pipeline designer and flow visualization page
- `components/axiom_flow.py`: AXIOM flow renderer
- `utils/`: Streamlit utility helpers
- `visualization/`: Plotly geometry visualization

### `forge/integration/`

Integration scaffolding and future extension notes.

- `README.md`

### `forge/materials/`

Material parameter repositories and academic parameter-set adapters.

- `academic/`: literature-backed material parameter definitions
- `repositories/`: base, Excel, hybrid, and PyBaMM-backed repositories

### `forge/ml/`

ML and autoresearch layer.

- `autoresearch/`: reusable autoresearch engine (`config`, `metrics`, `runner`, `results`, `git_ops`)
- `common/types.py`: decoupled ML dataclasses/enums
- `batch/`, `simulation/`, `sensitivity/`, `dataset/`, `representations/`, `models/`, `training/`: typed interface/ABC scaffolding

## GUI State

The GUI is now a four-page multipage Streamlit app.

- Deleted: `forge/gui/streamlit_app.py`
- Active multipage entrypoint: `forge/gui/app.py`
- Active pages:
  - `1_Cell_Calculator.py`
  - `2_CAD_Export.py`
  - `3_Geometry_Viewer.py`
  - `4_AXIOM_Designer.py`

Current GUI behavior:

- `app.py` is the landing page
- page 1 contains the real calculator
- page 4 exposes AXIOM directly through the GUI
- pouch supports full manual entry
- prismatic and cylindrical remain reference-driven only in the calculator page

## AXIOM GUI Layer

### `forge/gui/axiom_pipeline.py`

Tracked wrapper around the AXIOM driver sequence:

- `Build Prompt`
- `LLM Generate`
- `Parse YAML`
- `Schema Validate`
- `Physics Validate`
- `Convert`
- `Calculate`
- `Retry Feedback` loop capture when validation fails

### `data/demos/axiom/`

Recorded GUI replay assets:

- `successful_first_try.json`
- `retry_success.json`

These mirror the serialized `PipelineRun` structure used by the GUI page.

## Experiment Layer

### `experiments/ml/autoresearch/`

Current surrogate/autoresearch workspace.

- `prepare.py`: synthetic dataset generation
- `surrogate.py`: baseline PyTorch surrogate script
- `run.py`: loop runner wrapper around `forge.ml.autoresearch`
- `analysis.py`: results plotting and leaderboard view
- `program.md`: autonomous experiment playbook
- `README.md`: setup and usage

## Demo Layer

### `demos/n8n/`

- `axiom_supervised_vs_unsupervised.json`
- `axiom_batch_evaluation.json`
- `README.md`

## Test Layout

| Area | Location |
|---|---|
| API | `tests/api/` |
| AXIOM | `tests/axiom/` |
| Engine core | `tests/engine/` |
| CAD | `tests/engine/cad/` |
| Geometry | `tests/engine/geometry/` |
| Validation | `tests/engine/validation/` |
| GUI | `tests/gui/` |
| Materials | `tests/materials/` |
| ML autoresearch | `tests/ml/autoresearch/` |

Latest verified suite result:

```text
1516 passed, 3 skipped, 18 deselected
```

## Recent Milestones

| Commit | Summary |
|---|---|
| `3dd5fd4` | GUI refactor: calculator moved into multipage page 1, landing page polished, legacy app removed |
| `ffc2aa2` | CAD grouped-tab fix and default pytest base temp |
| `7d95b99` | Stable local Python 3.11 launchers and Plotly viewer import fix |
| `8c5d7b4` | L3 autoresearch program guide |
| `896f3ee` | L2-B synthetic dataset and baseline surrogate |
| `459ef38` | L2-A autoresearch engine |
| `4c01ec5` | K1-K2 calculator interface and reference-loading cleanup |

## Key Entry Commands

### Streamlit GUI

```powershell
.\start_forge_app.cmd
```

### FastAPI API

```powershell
.\start_forge_api.cmd
```

### Full test suite

```powershell
.\.venv311\Scripts\pytest.exe tests/ -x --tb=short -q
```

### Environment bootstrap

```powershell
.\setup_forge_env.cmd
```

## Known Notes

- The local environment is designed around Python 3.11 because PyBaMM support on Python 3.14 is unreliable.
- Pytest defaults to a repo-local base temp (`.pytest_tmp`) to avoid Windows temp-directory permission issues.
- `docs/FORGE_v1.jpg` is the landing-page image asset in the current working tree.
- `pybamm` is an **optional** dependency in the `[ml]` group, not a core dependency. The native venv installs `.[all]` which includes it; Docker web containers install `.[gui]` which excludes it. All code that uses pybamm handles its absence gracefully (`PYBAMM_AVAILABLE` flag, `pytest.importorskip`).
- Web deployment target: `https://forge.cristian-leu.de` — tiered deploy (Tier 1: static landing + auth, Tier 2: + backends, Tier 3: + SSL).
