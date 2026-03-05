"""FreeCAD script generation for CellCAD.

This module generates standalone Python scripts that run inside FreeCAD
to create parametric battery cell models.

No FreeCAD installation required for script generation -
FreeCAD is only needed to execute the generated scripts.

Example Usage:
    >>> from forge.engine.cad.freecad import FreeCADScriptGenerator
    >>> from forge.engine.geometry.loader import ArchetypeLoader
    >>>
    >>> # Load archetype and get geometry
    >>> loader = ArchetypeLoader("docs/byd_blade_138ah_archetype.json")
    >>> geometry = loader.to_detailed_geometry()
    >>>
    >>> # Generate FreeCAD script
    >>> generator = FreeCADScriptGenerator(grouping_mode="by_material")
    >>> result = generator.generate(geometry, "output/byd_blade.py")
    >>> print(f"Generated: {result.filepath}")

    >>> # Or use the convenience function
    >>> from forge.engine.cad.freecad import generate_freecad_script_from_archetype
    >>> result = generate_freecad_script_from_archetype(
    ...     "docs/tesla_4680_archetype.json",
    ...     "output/tesla_4680.py"
    ... )
"""

from .colors import (
    MATERIAL_TRANSPARENCY,
    FreeCADColor,
    FreeCADColorScheme,
)
from .script_generator import (
    FreeCADScriptGenerator,
    ScriptGenerationResult,
    generate_freecad_script_from_archetype,
)


__all__ = [
    "FreeCADScriptGenerator",
    "ScriptGenerationResult",
    "generate_freecad_script_from_archetype",
    "FreeCADColor",
    "FreeCADColorScheme",
    "MATERIAL_TRANSPARENCY",
]
