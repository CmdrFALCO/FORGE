"""Main CAD generator using Build123d.

This module provides the main interface for generating CAD geometry
from DetailedGeometry and exporting to various formats.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .assembly import AssemblyNamer, CADAssembly
from .availability import require_build123d
from .body_builders import BodyBuilder, GroupingMode

if TYPE_CHECKING:
    from ..geometry.detailed_geometry import DetailedGeometry
    from .exporters.stl_exporter import STLExportResult


class Build123dGenerator:
    """Generate CAD geometry from DetailedGeometry using Build123d.

    This class provides the main interface for converting computed layer
    geometry into Build123d solids and exporting to CAD formats.

    Usage:
        generator = Build123dGenerator()
        assembly = generator.generate(detailed_geometry)
        generator.export_step(assembly, "output.step")

    Requires: pip install cellcad[cad]

    Attributes:
        grouping_mode: How layers are grouped into bodies
        include_tabs_terminals: Whether to include tabs and terminals
        builder: BodyBuilder instance for geometry conversion
    """

    def __init__(
        self,
        grouping_mode: GroupingMode | str = GroupingMode.BY_MATERIAL,
        include_tabs_terminals: bool = True,
    ) -> None:
        """Initialize generator.

        Args:
            grouping_mode: How to group layers into bodies
                - "by_material": One body per material type (default, smaller files)
                - "individual": One body per layer (detailed, large files)
            include_tabs_terminals: Include tabs and terminals in CAD output

        Raises:
            ImportError: If build123d is not available
        """
        require_build123d()

        if isinstance(grouping_mode, str):
            grouping_mode = GroupingMode(grouping_mode)

        self.grouping_mode = grouping_mode
        self.include_tabs_terminals = include_tabs_terminals
        self.builder = BodyBuilder(grouping_mode)

    def generate(
        self,
        geometry: "DetailedGeometry",
    ) -> CADAssembly:
        """Generate CAD assembly from DetailedGeometry.

        Args:
            geometry: DetailedGeometry from Phase 1

        Returns:
            CADAssembly with Build123d solids

        Raises:
            ValueError: If cell type is not supported
        """
        # Determine cell type and build appropriate geometry
        if geometry.cell_type in ("pouch", "prismatic"):
            bodies = self.builder.build_stacked_cell(geometry)
        elif geometry.cell_type == "cylindrical":
            bodies = self.builder.build_wound_cell(geometry)
        else:
            raise ValueError(f"Unsupported cell type: {geometry.cell_type}")

        # Add tabs and terminals if requested
        if self.include_tabs_terminals:
            tab_bodies = self.builder.build_tabs_and_terminals(geometry)
            bodies.extend(tab_bodies)

        # Create assembly
        assembly = CADAssembly(
            name=AssemblyNamer.assembly_name(geometry.cell_type, geometry.chemistry),
            bodies=bodies,
            cell_type=geometry.cell_type,
            chemistry=geometry.chemistry,
            grouped_by_material=(self.grouping_mode == GroupingMode.BY_MATERIAL),
        )

        return assembly

    def export_step(
        self,
        assembly: CADAssembly,
        filepath: Path | str,
        include_assembly_structure: bool = True,
    ) -> Path:
        """Export assembly to STEP file.

        Args:
            assembly: CADAssembly from generate()
            filepath: Output file path (.step or .stp)
            include_assembly_structure: If True, export as assembly with named parts
                                        If False, export as single compound

        Returns:
            Path to exported file
        """
        import build123d as bd

        filepath = Path(filepath)

        # Ensure correct extension
        if filepath.suffix.lower() not in (".step", ".stp"):
            filepath = filepath.with_suffix(".step")

        # Create parent directories if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if include_assembly_structure:
            # Export as assembly with named compounds
            compounds = []
            for body in assembly.bodies:
                if body.solid is not None:
                    # Label the solid for identification in CAD software
                    body.solid.label = body.name
                    compounds.append(body.solid)

            if compounds:
                # Create assembly compound
                combined = bd.Compound(compounds)
                combined.label = assembly.name
                bd.export_step(combined, str(filepath))
        else:
            # Export as single fused solid
            solids = assembly.get_all_solids()
            if solids:
                combined = bd.Compound(solids)
                bd.export_step(combined, str(filepath))

        return filepath

    def export_brep(
        self,
        assembly: CADAssembly,
        filepath: Path | str,
    ) -> Path:
        """Export assembly to BREP file (OpenCASCADE native format).

        Args:
            assembly: CADAssembly from generate()
            filepath: Output file path (.brep)

        Returns:
            Path to exported file
        """
        import build123d as bd

        filepath = Path(filepath)
        if filepath.suffix.lower() != ".brep":
            filepath = filepath.with_suffix(".brep")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        solids = assembly.get_all_solids()
        if solids:
            combined = bd.Compound(solids)
            bd.export_brep(combined, str(filepath))

        return filepath

    def export_stl(
        self,
        assembly: CADAssembly,
        filepath: Path | str,
        quality: str = "medium",
        binary: bool = True,
    ) -> "STLExportResult":
        """Export assembly to STL mesh file.

        Args:
            assembly: CADAssembly from generate()
            filepath: Output file path (.stl)
            quality: Mesh quality preset ("low", "medium", "high")
            binary: If True, export binary STL (smaller files)

        Returns:
            STLExportResult with export details
        """
        from .exporters.stl_exporter import STLExporter

        exporter = STLExporter(quality=quality, binary=binary)
        return exporter.export_combined(assembly, filepath)

    def export_stl_per_body(
        self,
        assembly: CADAssembly,
        output_dir: Path | str,
        quality: str = "medium",
        binary: bool = True,
        create_zip: bool = False,
    ) -> "list[STLExportResult] | Path":
        """Export each body as separate STL file.

        Args:
            assembly: CADAssembly from generate()
            output_dir: Directory for output files
            quality: Mesh quality preset ("low", "medium", "high")
            binary: If True, export binary STL (smaller files)
            create_zip: If True, package into ZIP archive

        Returns:
            List of STLExportResult, or Path to ZIP if create_zip=True
        """
        from .exporters.stl_exporter import STLExporter

        exporter = STLExporter(quality=quality, binary=binary)
        return exporter.export_per_body(assembly, output_dir, create_zip=create_zip)


def generate_step_from_archetype(
    archetype_path: Path | str,
    output_path: Path | str,
    grouping_mode: str = "by_material",
    apply_swelling: bool = True,
    include_tabs_terminals: bool = True,
) -> Path:
    """Convenience function to generate STEP from archetype JSON.

    Args:
        archetype_path: Path to archetype JSON file
        output_path: Output STEP file path
        grouping_mode: "by_material" or "individual"
        apply_swelling: Apply EOL swelling to geometry
        include_tabs_terminals: Include tabs and terminals in output

    Returns:
        Path to exported STEP file

    Example:
        >>> from forge.engine.cad import generate_step_from_archetype
        >>> generate_step_from_archetype(
        ...     "docs/byd_blade_138ah_archetype.json",
        ...     "output/byd_blade.step"
        ... )
    """
    from ..geometry.loader import ArchetypeLoader

    # Load archetype
    loader = ArchetypeLoader(archetype_path)
    geometry = loader.to_detailed_geometry(apply_swelling=apply_swelling)

    # Generate and export
    generator = Build123dGenerator(
        grouping_mode=grouping_mode,
        include_tabs_terminals=include_tabs_terminals,
    )
    assembly = generator.generate(geometry)
    return generator.export_step(assembly, output_path)


def generate_stl_from_archetype(
    archetype_path: Path | str,
    output_path: Path | str,
    grouping_mode: str = "by_material",
    quality: str = "medium",
    apply_swelling: bool = True,
    include_tabs_terminals: bool = True,
) -> "STLExportResult":
    """Convenience function to generate STL from archetype JSON.

    Args:
        archetype_path: Path to archetype JSON file
        output_path: Output STL file path
        grouping_mode: "by_material" or "individual"
        quality: Mesh quality preset ("low", "medium", "high")
        apply_swelling: Apply EOL swelling to geometry
        include_tabs_terminals: Include tabs and terminals in output

    Returns:
        STLExportResult with export details

    Example:
        >>> from forge.engine.cad import generate_stl_from_archetype
        >>> result = generate_stl_from_archetype(
        ...     "docs/byd_blade_138ah_archetype.json",
        ...     "output/byd_blade.stl",
        ...     quality="medium"
        ... )
    """
    from ..geometry.loader import ArchetypeLoader

    # Load archetype
    loader = ArchetypeLoader(archetype_path)
    geometry = loader.to_detailed_geometry(apply_swelling=apply_swelling)

    # Generate and export
    generator = Build123dGenerator(
        grouping_mode=grouping_mode,
        include_tabs_terminals=include_tabs_terminals,
    )
    assembly = generator.generate(geometry)
    return generator.export_stl(assembly, output_path, quality=quality)
