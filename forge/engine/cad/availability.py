"""Check for optional CAD dependencies.

This module provides graceful handling of optional CAD dependencies,
allowing the core CellCAD package to work without build123d installed.
"""

from __future__ import annotations

BUILD123D_AVAILABLE: bool = False
BUILD123D_VERSION: str | None = None

try:
    import build123d as bd

    BUILD123D_AVAILABLE = True
    BUILD123D_VERSION = getattr(bd, "__version__", "unknown")
except ImportError:
    pass


def require_build123d() -> None:
    """Raise ImportError with helpful message if build123d not available.

    Raises:
        ImportError: If build123d is not installed
    """
    if not BUILD123D_AVAILABLE:
        raise ImportError(
            "Build123d is required for CAD export but not installed.\n"
            "Install with: pip install cellcad[cad]\n"
            "Or directly: pip install build123d"
        )


def get_cad_status() -> dict[str, bool | str | None]:
    """Get status of CAD dependencies.

    Returns:
        Dictionary with availability and version information
    """
    return {
        "build123d_available": BUILD123D_AVAILABLE,
        "build123d_version": BUILD123D_VERSION,
    }
