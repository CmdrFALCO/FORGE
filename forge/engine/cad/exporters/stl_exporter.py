"""STL mesh export for CAD assemblies.

This module provides STL export functionality with quality presets
for visualization and 3D printing workflows.
"""

from __future__ import annotations

import struct
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from ..availability import require_build123d

if TYPE_CHECKING:
    from ..assembly import CADAssembly


class STLQuality(str, Enum):
    """Mesh quality presets for STL export.

    LOW: Fast export, small files, visible facets
    MEDIUM: Balanced quality and file size (default)
    HIGH: Smooth surfaces, larger files
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class STLQualitySettings:
    """Mesh tessellation parameters.

    Attributes:
        linear_tolerance: Maximum deviation from true surface (mm)
        angular_tolerance: Maximum angle between adjacent facets (radians)
    """

    linear_tolerance: float
    angular_tolerance: float

    @classmethod
    def from_preset(cls, preset: STLQuality) -> STLQualitySettings:
        """Get settings for quality preset.

        Args:
            preset: Quality preset enum value

        Returns:
            STLQualitySettings with appropriate tolerances
        """
        presets = {
            STLQuality.LOW: cls(
                linear_tolerance=0.1,
                angular_tolerance=0.5,
            ),
            STLQuality.MEDIUM: cls(
                linear_tolerance=0.01,
                angular_tolerance=0.1,
            ),
            STLQuality.HIGH: cls(
                linear_tolerance=0.001,
                angular_tolerance=0.05,
            ),
        }
        return presets[preset]


@dataclass
class STLExportResult:
    """Result of STL export operation.

    Attributes:
        filepath: Path to the exported file
        file_size_bytes: Size of the file in bytes
        is_binary: Whether the file is in binary format
        quality: Quality preset used
        body_count: Number of bodies exported
        success: Whether the export was successful
        error_message: Error message if export failed
    """

    filepath: Path
    file_size_bytes: int
    is_binary: bool
    quality: STLQuality
    body_count: int
    success: bool
    error_message: str | None = None

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)


class STLExporter:
    """Export CAD assemblies to STL mesh format.

    Supports binary and ASCII formats with configurable quality presets.

    Usage:
        exporter = STLExporter(quality=STLQuality.MEDIUM)
        result = exporter.export_combined(assembly, "output.stl")

        # Or per-body export
        results = exporter.export_per_body(assembly, output_dir)

    Attributes:
        quality: Quality preset used
        settings: Tessellation settings derived from quality
        binary: Whether to export binary format
    """

    def __init__(
        self,
        quality: STLQuality | str = STLQuality.MEDIUM,
        binary: bool = True,
    ) -> None:
        """Initialize exporter.

        Args:
            quality: Mesh quality preset (low/medium/high)
            binary: If True, export binary STL (smaller). If False, ASCII.

        Raises:
            ImportError: If build123d is not available
        """
        require_build123d()

        if isinstance(quality, str):
            quality = STLQuality(quality)

        self.quality = quality
        self.settings = STLQualitySettings.from_preset(quality)
        self.binary = binary

    def export_combined(
        self,
        assembly: CADAssembly,
        filepath: Path | str,
    ) -> STLExportResult:
        """Export assembly as single combined STL mesh.

        All bodies are merged into one mesh.

        Args:
            assembly: CADAssembly from Build123dGenerator
            filepath: Output file path (.stl)

        Returns:
            STLExportResult with export details
        """
        import build123d as bd

        filepath = Path(filepath)
        if filepath.suffix.lower() != ".stl":
            filepath = filepath.with_suffix(".stl")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Combine all solids
            solids = assembly.get_all_solids()
            if not solids:
                return STLExportResult(
                    filepath=filepath,
                    file_size_bytes=0,
                    is_binary=self.binary,
                    quality=self.quality,
                    body_count=0,
                    success=False,
                    error_message="No solids to export",
                )

            # Create compound of all bodies
            combined = bd.Compound(solids)

            # Export with quality settings
            bd.export_stl(
                combined,
                str(filepath),
                tolerance=self.settings.linear_tolerance,
                angular_tolerance=self.settings.angular_tolerance,
                ascii_format=not self.binary,
            )

            return STLExportResult(
                filepath=filepath,
                file_size_bytes=filepath.stat().st_size,
                is_binary=self.binary,
                quality=self.quality,
                body_count=len(solids),
                success=True,
            )

        except Exception as e:
            return STLExportResult(
                filepath=filepath,
                file_size_bytes=0,
                is_binary=self.binary,
                quality=self.quality,
                body_count=0,
                success=False,
                error_message=str(e),
            )

    def export_per_body(
        self,
        assembly: CADAssembly,
        output_dir: Path | str,
        create_zip: bool = False,
    ) -> list[STLExportResult] | Path:
        """Export each body as separate STL file.

        Creates one STL per body, named by material group.

        Args:
            assembly: CADAssembly from Build123dGenerator
            output_dir: Directory for output files
            create_zip: If True, package all STLs into a ZIP archive

        Returns:
            List of STLExportResult for each body, or Path to ZIP if create_zip=True
        """
        import build123d as bd

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results: list[STLExportResult] = []

        for body in assembly.bodies:
            if body.solid is None:
                continue

            # Sanitize filename
            filename = f"{body.name}.stl"
            filepath = output_dir / filename

            try:
                bd.export_stl(
                    body.solid,
                    str(filepath),
                    tolerance=self.settings.linear_tolerance,
                    angular_tolerance=self.settings.angular_tolerance,
                    ascii_format=not self.binary,
                )

                results.append(
                    STLExportResult(
                        filepath=filepath,
                        file_size_bytes=filepath.stat().st_size,
                        is_binary=self.binary,
                        quality=self.quality,
                        body_count=1,
                        success=True,
                    )
                )

            except Exception as e:
                results.append(
                    STLExportResult(
                        filepath=filepath,
                        file_size_bytes=0,
                        is_binary=self.binary,
                        quality=self.quality,
                        body_count=0,
                        success=False,
                        error_message=str(e),
                    )
                )

        if create_zip:
            return self._create_zip_archive(assembly.name, output_dir, results)

        return results

    def _create_zip_archive(
        self,
        assembly_name: str,
        output_dir: Path,
        results: list[STLExportResult],
    ) -> Path:
        """Create ZIP archive of exported STL files.

        Args:
            assembly_name: Name for the ZIP file
            output_dir: Directory containing STL files
            results: List of export results

        Returns:
            Path to created ZIP file
        """
        zip_path = output_dir / f"{assembly_name}_stl.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for result in results:
                if result.success and result.filepath.exists():
                    zf.write(result.filepath, result.filepath.name)

        return zip_path


def get_stl_file_info(filepath: Path | str) -> dict[str, object]:
    """Get information about STL file.

    Detects format (binary vs ASCII) and counts triangles for binary files.

    Args:
        filepath: Path to STL file

    Returns:
        Dictionary with file information including:
        - filepath: Path as string
        - file_size_bytes: Size in bytes
        - file_size_mb: Size in megabytes
        - format: "binary" or "ASCII"
        - triangle_count: Number of triangles (binary only)
        - error: Error message (if any)
    """
    filepath = Path(filepath)

    if not filepath.exists():
        return {"error": "File not found"}

    info: dict[str, object] = {
        "filepath": str(filepath),
        "file_size_bytes": filepath.stat().st_size,
        "file_size_mb": filepath.stat().st_size / (1024 * 1024),
    }

    # Detect format (binary vs ASCII)
    try:
        with open(filepath, "rb") as f:
            header = f.read(80)
            # ASCII STL starts with "solid"
            if header.strip().startswith(b"solid"):
                # Could still be binary with "solid" in header
                # Check if next content looks like ASCII
                f.seek(0)
                first_lines = f.read(200).decode("utf-8", errors="ignore")
                if "facet normal" in first_lines:
                    info["format"] = "ASCII"
                else:
                    info["format"] = "binary"
            else:
                info["format"] = "binary"
    except Exception:
        info["format"] = "unknown"

    # Count triangles for binary STL
    if info.get("format") == "binary":
        try:
            with open(filepath, "rb") as f:
                f.seek(80)  # Skip header
                triangle_bytes = f.read(4)
                if len(triangle_bytes) == 4:
                    triangle_count = struct.unpack("<I", triangle_bytes)[0]
                    info["triangle_count"] = triangle_count
        except Exception:
            pass

    return info
