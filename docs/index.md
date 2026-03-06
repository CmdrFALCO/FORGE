# FORGE - Formal Output Regulation for Generative Engineering

FORGE is a unified framework for parametric battery cell design, neuro-symbolic AI supervision, and ML-driven predictive modeling.

## Project Overview

FORGE integrates three components:

- **CellCAD** (Engine Layer) - Deterministic parametric CAD engine for lithium-ion battery cells
- **AXIOM** (Supervision Layer) - Neuro-symbolic architecture supervising LLM-generated engineering specifications
- **ML Extensions** (Prediction Layer) - Geometric representation learning and surrogate modeling

## Architecture

FORGE follows a four-layer architecture:

| Layer | Package | Description |
|-------|---------|-------------|
| 1 | orge.engine | Parametric CAD engine (geometry, calculations, validation, export) |
| 2 | orge.axiom | Neuro-symbolic LLM supervision (generate -> validate -> retry) |
| 3 | orge.ml | ML surrogate modeling (sensitivity, dataset, training) |
| 4 | orge.integration | External tool connectors (PyBOP, CFD/FEM - documented stubs) |

## Quick Links

- [Architecture](architecture.md) - Detailed system design
- [Engine](engine.md) - CellCAD parametric engine
- [AXIOM](axiom.md) - Neuro-symbolic supervision
- [ML Layer](ml-layer.md) - Machine learning extensions
- [API Reference](api-reference.md) - REST API endpoints
- [Development](development.md) - Contributing, testing, CI/CD
