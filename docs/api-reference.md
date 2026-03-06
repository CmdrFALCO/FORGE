# API Reference

FORGE exposes a REST API via FastAPI for headless operation and workflow integration (e.g., n8n).

*Detailed endpoint documentation will be generated from OpenAPI specs.*

## Base URL

All endpoints are versioned under /api/v1/.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /api/v1/reference-cells | List reference cell archetypes |
| POST | /api/v1/validate | Validate a cell specification |
| POST | /api/v1/calculate | Run calculations on a cell spec |
| POST | /api/v1/generate | Generate a cell design via LLM |
| POST | /api/v1/parse | Parse generated YAML into structured output |
| POST | /api/v1/pipeline | Full supervised pipeline (generate -> validate -> calculate) |
