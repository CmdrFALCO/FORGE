"""System routes for FORGE API health and reference-cell metadata."""

from __future__ import annotations

import importlib.metadata
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query, Request

from forge.api.schemas.models import (
    HealthData,
    HealthResponse,
    ReferenceCellMeta,
    ReferenceCellsData,
    ReferenceCellsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_version() -> str:
    """Resolve application version for health responses."""
    try:
        from forge import __version__ as forge_version

        if forge_version:
            return str(forge_version)
    except Exception:
        pass

    try:
        return importlib.metadata.version("forge")
    except Exception:
        return "0.1.0"


def _detect_backends_available() -> list[str]:
    """Detect available LLM backends by optional dependency flags."""
    available: list[str] = []
    try:
        from forge.axiom.backends import backends as backend_module

        if getattr(backend_module, "ANTHROPIC_AVAILABLE", False):
            available.append("anthropic")
        if getattr(backend_module, "REQUESTS_AVAILABLE", False):
            available.append("ollama")
    except Exception:
        logger.debug("Could not import AXIOM backends for health probe.", exc_info=True)
    return available


def build_health_data() -> HealthData:
    """Build health payload shared by /health aliases."""
    return HealthData(
        status="ok",
        version=_resolve_version(),
        backends_available=_detect_backends_available(),
    )


def _normalize_cell_type(raw_value: Any, fallback_id: str) -> str:
    """Normalize cell-type strings to API literals."""
    value = str(raw_value or "").strip().lower()
    if "pouch" in value:
        return "pouch"
    if "prismatic" in value:
        return "prismatic"
    if "cyl" in value:
        return "cylindrical"

    fallback = fallback_id.lower()
    if "pouch" in fallback:
        return "pouch"
    if "prismatic" in fallback:
        return "prismatic"
    if "cyl" in fallback:
        return "cylindrical"
    return "pouch"


def _extract_reference_meta(file_path: Path, include_full: bool) -> ReferenceCellMeta | None:
    """Parse a single reference JSON file into API metadata."""
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Skipping invalid reference JSON '%s': %s", file_path.name, exc)
        return None

    metadata = payload.get("metadata", {})
    ref_id = str(metadata.get("id") or file_path.stem)
    name = str(metadata.get("name") or payload.get("cell_design_name") or ref_id)
    cell_type = _normalize_cell_type(
        metadata.get("cell_type") or payload.get("cell_type"), fallback_id=ref_id
    )

    chemistry = str(
        metadata.get("chemistry")
        or payload.get("cell_specs", {}).get("chemistry")
        or payload.get("chemistry")
        or "unknown"
    )
    tier = str(payload.get("tier") or metadata.get("tier") or ("tier1" if metadata.get("doi") else "community"))
    source = str(
        metadata.get("source") or metadata.get("doi") or payload.get("source") or payload.get("doi") or "unknown"
    )

    return ReferenceCellMeta(
        id=ref_id,
        name=name,
        cell_type=cell_type,  # type: ignore[arg-type]
        chemistry=chemistry,
        tier=tier,
        source=source,
        data=payload if include_full else None,
    )


def list_reference_cells(reference_dir: Path, include_full: bool = False) -> list[ReferenceCellMeta]:
    """Read reference metadata from project-root data/reference JSON files."""
    if not reference_dir.exists():
        logger.warning("Reference data directory does not exist: %s", reference_dir)
        return []

    cells: list[ReferenceCellMeta] = []
    for file_path in sorted(reference_dir.glob("*.json")):
        meta = _extract_reference_meta(file_path, include_full=include_full)
        if meta is not None:
            cells.append(meta)
    return cells


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Versioned health endpoint."""
    return HealthResponse(data=build_health_data())


@router.get("/reference-cells", response_model=ReferenceCellsResponse)
def reference_cells(
    request: Request,
    full: bool = Query(default=False, description="Include full JSON payload for each reference."),
) -> ReferenceCellsResponse:
    """List reference cell metadata, optionally including full specs."""
    reference_dir = getattr(
        request.app.state,
        "reference_data_dir",
        Path(__file__).resolve().parents[3] / "data" / "reference",
    )
    cells = list_reference_cells(Path(reference_dir), include_full=full)
    return ReferenceCellsResponse(data=ReferenceCellsData(cells=cells, count=len(cells)))
