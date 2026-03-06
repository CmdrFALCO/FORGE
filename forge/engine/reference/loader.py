"""Reference-cell JSON loading helpers.

This module centralizes access to project-root ``data/reference`` files.
"""

from pathlib import Path
from typing import Any

from forge.engine.validation import result_validation as _result_validation

REFERENCE_DIR = Path(__file__).resolve().parents[3] / "data" / "reference"
"""Default reference-cell directory at project root."""


def load_reference_cell(
    cell_id: str, reference_dir: Path | None = None
) -> _result_validation.ReferenceCell:
    """Load a single reference cell by ID."""
    active_dir = reference_dir if reference_dir is not None else REFERENCE_DIR
    return _result_validation.load_reference_cell(cell_id, active_dir)


def list_reference_cells(reference_dir: Path | None = None, cell_type: str | None = None) -> list[str]:
    """List available reference cell IDs, optionally filtered by cell type."""
    active_dir = reference_dir if reference_dir is not None else REFERENCE_DIR
    return _result_validation.list_reference_cells(active_dir, cell_type=cell_type)


def get_reference_info(cell_id: str, reference_dir: Path | None = None) -> dict[str, Any]:
    """Get summary metadata for one reference cell."""
    active_dir = reference_dir if reference_dir is not None else REFERENCE_DIR
    return _result_validation.get_reference_info(cell_id, active_dir)


__all__ = ["REFERENCE_DIR", "load_reference_cell", "list_reference_cells", "get_reference_info"]

