"""CAD generation module for CellCAD.

This module provides Build123d-based CAD generation and STEP export
for battery cell geometry computed by the Internal Geometry Engine.

Requires optional dependency: pip install cellcad[cad]

Example Usage:
    >>> from forge.engine.cad import BUILD123D_AVAILABLE, get_cad_status
    >>> print(get_cad_status())
    {'build123d_available': True, 'build123d_version': '0.10.0'}

    >>> if BUILD123D_AVAILABLE:
    ...     from forge.engine.cad import Build123dGenerator, generate_step_from_archetype
    ...     # Generate STEP from archetype
    ...     generate_step_from_archetype(
    ...         "docs/byd_blade_138ah_archetype.json",
    ...         "output/byd_blade.step"
    ...     )

    >>> # FreeCAD script generation (always available)
    >>> from forge.engine.cad import generate_freecad_script_from_archetype
    >>> generate_freecad_script_from_archetype(
    ...     "docs/tesla_4680_archetype.json",
    ...     "output/tesla_4680_freecad.py"
    ... )

The module uses an optional dependency pattern - core CellCAD functionality
works without build123d installed. CAD export features are only available
when build123d is installed. FreeCAD script generation is always available.
"""

from .assembly import AssemblyNamer, CADAssembly, CADBody, MaterialGroup
from .availability import (
    BUILD123D_AVAILABLE,
    BUILD123D_VERSION,
    get_cad_status,
    require_build123d,
)
from .body_builders import GroupingMode

# FreeCAD script generation (always available - no build123d needed)
from .freecad import (
    MATERIAL_TRANSPARENCY,
    FreeCADColor,
    FreeCADColorScheme,
    FreeCADScriptGenerator,
    ScriptGenerationResult,
    generate_freecad_script_from_archetype,
)

# Conditionally export generator classes if build123d is available
if BUILD123D_AVAILABLE:
    from .build123d_generator import (
        Build123dGenerator,
        generate_step_from_archetype,
        generate_stl_from_archetype,
    )
    from .exporters.step_exporter import (
        STEPExportResult,
        get_step_file_info,
        validate_step_file,
    )
    from .exporters.stl_exporter import (
        STLExporter,
        STLExportResult,
        STLQuality,
        STLQualitySettings,
        get_stl_file_info,
    )

    __all__ = [
        # Always available
        "BUILD123D_AVAILABLE",
        "BUILD123D_VERSION",
        "get_cad_status",
        "require_build123d",
        "MaterialGroup",
        "CADBody",
        "CADAssembly",
        "AssemblyNamer",
        "GroupingMode",
        # FreeCAD (always available)
        "FreeCADScriptGenerator",
        "ScriptGenerationResult",
        "generate_freecad_script_from_archetype",
        "FreeCADColor",
        "FreeCADColorScheme",
        "MATERIAL_TRANSPARENCY",
        # Conditionally available (build123d required)
        "Build123dGenerator",
        "generate_step_from_archetype",
        "generate_stl_from_archetype",
        "STEPExportResult",
        "validate_step_file",
        "get_step_file_info",
        # STL exports
        "STLExporter",
        "STLQuality",
        "STLQualitySettings",
        "STLExportResult",
        "get_stl_file_info",
    ]
else:
    __all__ = [
        # Always available
        "BUILD123D_AVAILABLE",
        "BUILD123D_VERSION",
        "get_cad_status",
        "require_build123d",
        "MaterialGroup",
        "CADBody",
        "CADAssembly",
        "AssemblyNamer",
        "GroupingMode",
        # FreeCAD (always available)
        "FreeCADScriptGenerator",
        "ScriptGenerationResult",
        "generate_freecad_script_from_archetype",
        "FreeCADColor",
        "FreeCADColorScheme",
        "MATERIAL_TRANSPARENCY",
    ]
