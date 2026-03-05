# n8n AXIOM Demo

Workflow demos comparing supervised (AXIOM) vs. unsupervised LLM battery cell design generation.

## Workflows

- **axiom_supervised_vs_unsupervised.json** — Main demo: side-by-side comparison of supervised and unsupervised generation with validation and calculation
- **axiom_batch_evaluation.json** — Batch evaluation: N iterations with aggregate pass/fail statistics

## Prerequisites

- FORGE API running (`uvicorn forge.api.app:app` on localhost:8000)
- Ollama backend running on AI Rig (or configured LLM backend)
- n8n instance (local or company server)

## Setup

Import the workflow JSON files into your n8n instance and configure the HTTP Request nodes to point to your FORGE API endpoint.
