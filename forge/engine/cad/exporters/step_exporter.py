"""STEP export utilities and validation.

This module provides utilities for validating and inspecting STEP files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..availability import require_build123d

if TYPE_CHECKING:
    from ..assembly import CADAssembly


@dataclass
class STEPExportResult:
    """Result of STEP export operation.

    Attributes:
        filepath: Path to the exported file
        file_size_bytes: Size of the file in bytes
        body_count: Number of bodies exported
        success: Whether the export was successful
        error_message: Error message if export failed
    """

    filepath: Path
    file_size_bytes: int
    body_count: int
    success: bool
    error_message: str | None = None

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)


def validate_step_file(filepath: Path | str) -> bool:
    """Basic validation that STEP file is readable.

    Checks that the file exists, has content, and contains
    a valid STEP header.

    Args:
        filepath: Path to STEP file

    Returns:
        True if file appears valid
    """
    filepath = Path(filepath)

    if not filepath.exists():
        return False

    # Check file has content
    if filepath.stat().st_size < 100:
        return False

    # Check header
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            header = f.read(200)
            return "ISO-10303-21" in header or "STEP" in header.upper()
    except Exception:
        return False


def get_step_file_info(filepath: Path | str) -> dict[str, object]:
    """Get information about STEP file.

    Args:
        filepath: Path to STEP file

    Returns:
        Dictionary with file information including:
        - filepath: Path as string
        - file_size_bytes: Size in bytes
        - file_size_mb: Size in megabytes
        - valid: Whether file is valid
        - solid_count: Number of solids (if readable)
        - error: Error message (if any)
    """
    filepath = Path(filepath)

    if not filepath.exists():
        return {"error": "File not found", "valid": False}

    info: dict[str, object] = {
        "filepath": str(filepath),
        "file_size_bytes": filepath.stat().st_size,
        "file_size_mb": filepath.stat().st_size / (1024 * 1024),
    }

    # Try to import and count bodies
    try:
        require_build123d()
        import build123d as bd

        imported = bd.import_step(str(filepath))
        if hasattr(imported, "solids"):
            info["solid_count"] = len(imported.solids())
        info["valid"] = True
    except ImportError:
        info["valid"] = validate_step_file(filepath)
        info["note"] = "build123d not available for detailed validation"
    except Exception as e:
        info["valid"] = False
        info["error"] = str(e)

    return info


def count_step_entities(filepath: Path | str) -> dict[str, int]:
    """Count entities in STEP file by parsing text.

    This is a lightweight alternative to full import that
    counts entity types by parsing the STEP file text.

    Args:
        filepath: Path to STEP file

    Returns:
        Dictionary mapping entity type to count
    """
    filepath = Path(filepath)

    if not filepath.exists():
        return {}

    counts: dict[str, int] = {}

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # STEP entities start with #number = ENTITY_NAME(
                if line.strip().startswith("#") and "=" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        entity_part = parts[1].strip()
                        if "(" in entity_part:
                            entity_name = entity_part.split("(")[0].strip()
                            counts[entity_name] = counts.get(entity_name, 0) + 1
    except Exception:
        pass

    return counts
