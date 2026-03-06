# Development Guide

## Setup

`ash
git clone https://github.com/CmdrFALCO/FORGE.git
cd FORGE
pip install -e \".[dev]\"
`

## Running Tests

`ash
pytest --tb=short -q
`

Live integration tests (requires API keys) are deselected by default. Run them with:

`ash
pytest -m live --tb=short
`

## Linting

`ash
ruff check .
`

## Type Checking

`ash
mypy forge/
`

## Documentation

`ash
pip install -e \".[docs]\"
mkdocs serve       # Local preview at http://127.0.0.1:8000
mkdocs build       # Build static site to site/
`

## Optional Dependencies

| Group | Install | Contents |
|-------|---------|----------|
| dev | pip install -e \".[dev]\" | pytest, httpx, ruff, mypy |
| llm | pip install -e \".[llm]\" | anthropic, requests |
| docs | pip install -e \".[docs]\" | mkdocs, mkdocs-material |
