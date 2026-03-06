# FORGE n8n Demo Workflows

## Overview

These n8n workflow files demonstrate the AXIOM neuro-symbolic supervision
pipeline as visible, inspectable workflow nodes. The AXIOM pipeline maps 1:1
onto n8n's visual workflow paradigm.

## Workflows

### `axiom_supervised_vs_unsupervised.json`
Side-by-side comparison of supervised (AXIOM loop) vs. unsupervised (raw LLM)
battery cell specification generation. Shows how formal validation and
corrective feedback improve output quality.

### `axiom_batch_evaluation.json`
Batch execution of the AXIOM pipeline across multiple design requests.
Collects statistics on success rates, retry counts, and error categories.

## Prerequisites

1. n8n instance running (local or cloud)
2. FORGE API server running: `uvicorn forge.api.app:app --host 0.0.0.0 --port 8000`
3. LLM backend configured (Claude API key or Ollama running locally)

## Setup

1. Import the workflow JSON into n8n
2. Configure the HTTP Request nodes to point to your FORGE API URL
3. Set environment variables for LLM backend credentials
4. Trigger the workflow manually or via webhook

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Verify FORGE API is running |
| `GET /api/v1/reference-cells` | Load reference cell specifications |
| `POST /api/v1/generate` | Raw LLM generation (unsupervised path) |
| `POST /api/v1/pipeline` | Full AXIOM loop (supervised path) |
| `POST /api/v1/validate` | Standalone validation check |
| `POST /api/v1/calculate` | Run calculations on validated spec |
