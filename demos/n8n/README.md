# FORGE n8n Demo Workflows

## Overview

These workflows are importable n8n demos for the FORGE AXIOM thesis narrative:
supervised generation (AXIOM loop) versus unsupervised generation (raw LLM flow).

## Environment Variables

- `FORGE_API_URL` (default: `http://localhost:8000`)
- `FORGE_LLM_BACKEND` (default: `ollama`)

All HTTP Request nodes in both workflows use these variables via n8n expressions.

## Prerequisites

1. Start FORGE API:
   `uvicorn forge.api.app:app --host 0.0.0.0 --port 8000`
2. Make sure your LLM backend is available:
   - `ollama` locally, or
   - Anthropic backend credentials/dependencies if you switch backend.
3. Run n8n.

## Import Instructions

1. In n8n, open **Workflows**.
2. Click **Import from File**.
3. Select one of the JSON files in `demos/n8n/`.
4. Run with **Execute workflow** (manual trigger).

## Workflows

### `axiom_supervised_vs_unsupervised.json` (J1)

Single-run side-by-side comparison.

- Supervised branch: `POST /api/v1/pipeline`
- Unsupervised branch: `POST /api/v1/generate` -> `POST /api/v1/parse` ->
  `POST /api/v1/validate` -> conditional `POST /api/v1/calculate`
- End: merge + comparison summary node

### `axiom_batch_evaluation.json` (J2)

Batch evaluation with statistical summary (default 10 iterations).

- Generates N iteration items (configurable via `total_iterations`)
- Runs supervised and unsupervised branches each iteration
- Aggregates pass/fail rates and emits a `thesis_argument` summary
