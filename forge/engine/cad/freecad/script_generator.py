"""FreeCAD script generator for DetailedGeometry."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, select_autoescape

from ..body_builders import GroupingMode
from .colors import MATERIAL_TRANSPARENCY, FreeCADColorScheme


if TYPE_CHECKING:
    from ...geometry.detailed_geometry import DetailedGeometry


@dataclass
class ScriptGenerationResult:
    """Result of script generation."""

    filepath: Path
    cell_type: str
    grouped_by_material: bool
    line_count: int
    success: bool
    error_message: str | None = None


class FreeCADScriptGenerator:
    """Generate standalone FreeCAD Python scripts from DetailedGeometry.

    Generated scripts:
    - Are self-contained (no CellCAD dependency when run)
    - Have editable parameter section at top
    - Include verbose comments
    - Set view colors matching CellCAD visualization
    - Use FreeCAD Part module for geometry creation

    Usage:
        generator = FreeCADScriptGenerator()
        result = generator.generate(detailed_geometry, "output.py")

        # User then runs output.py in FreeCAD
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        grouping_mode: GroupingMode | str = GroupingMode.BY_MATERIAL,
    ):
        """Initialize generator.

        Args:
            grouping_mode: How to organize bodies in FreeCAD
                - "by_material": Fewer bodies, cleaner tree (default)
                - "individual": One body per layer, detailed tree
        """
        if isinstance(grouping_mode, str):
            grouping_mode = GroupingMode(grouping_mode)

        self.grouping_mode = grouping_mode

        # Setup Jinja2 environment
        self.env = Environment(
            loader=PackageLoader("forge.engine.cad.freecad", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        geometry: "DetailedGeometry",
        filepath: Path | str,
    ) -> ScriptGenerationResult:
        """Generate FreeCAD script from DetailedGeometry.

        Args:
            geometry: DetailedGeometry from Phase 1
            filepath: Output Python script path (.py)

        Returns:
            ScriptGenerationResult with generation details
        """
        filepath = Path(filepath)
        if filepath.suffix.lower() != ".py":
            filepath = filepath.with_suffix(".py")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Select template based on cell type
            if geometry.cell_type in ("pouch", "prismatic"):
                template = self.env.get_template("stacked.py.jinja2")
            elif geometry.cell_type == "cylindrical":
                template = self.env.get_template("cylindrical.py.jinja2")
            else:
                raise ValueError(f"Unsupported cell type: {geometry.cell_type}")

            # Build template context
            context = self._build_context(geometry)

            # Render template
            script_content = template.render(**context)

            # Write to file
            filepath.write_text(script_content, encoding="utf-8")

            line_count = len(script_content.splitlines())

            return ScriptGenerationResult(
                filepath=filepath,
                cell_type=geometry.cell_type,
                grouped_by_material=(self.grouping_mode == GroupingMode.BY_MATERIAL),
                line_count=line_count,
                success=True,
            )

        except Exception as e:
            return ScriptGenerationResult(
                filepath=filepath,
                cell_type=geometry.cell_type,
                grouped_by_material=(self.grouping_mode == GroupingMode.BY_MATERIAL),
                line_count=0,
                success=False,
                error_message=str(e),
            )

    def _build_context(self, geometry: "DetailedGeometry") -> dict:
        """Build Jinja2 template context from DetailedGeometry."""
        ext = geometry.external_geometry
        stack = geometry.layer_stack
        zones = geometry.coating_zones

        # Header comment
        header_comment = f"""
FreeCAD Parametric Battery Cell Model
=====================================
Archetype: {geometry.archetype_name}
Cell Type: {geometry.cell_type.title()}
Chemistry: {geometry.chemistry}

This script generates a 3D model of the battery cell with:
- Editable parameters (modify values in PARAMETERS section)
- Proper material organization
- Color-coded components

To use:
1. Open FreeCAD (0.21 or later recommended)
2. Go to Macro > Execute (or press F6)
3. Select this script
4. The model will be created in the active document
""".strip()

        # Build parameter lists
        external_params = []
        wall_params = []
        stack_params = []
        thickness_params = []
        overhang_params = []

        # External dimensions based on cell type
        if geometry.cell_type in ("pouch", "prismatic"):
            external_params.extend(
                [
                    {
                        "name": "CELL_LENGTH",
                        "value": ext.length_mm or 100.0,
                        "description": "Cell length in mm (X direction)",
                    },
                    {
                        "name": "CELL_WIDTH",
                        "value": ext.width_mm or 100.0,
                        "description": "Cell width in mm (Y direction)",
                    },
                    {
                        "name": "CELL_THICKNESS",
                        "value": ext.thickness_mm or ext.height_mm or 20.0,
                        "description": "Cell thickness in mm (Z direction, stack direction)",
                    },
                ]
            )
            wall_params.append(
                {
                    "name": "WALL_THICKNESS",
                    "value": ext.wall_thickness_mm or 0.5,
                    "description": "Casing wall thickness in mm",
                }
            )
        else:  # Cylindrical
            external_params.extend(
                [
                    {
                        "name": "CELL_DIAMETER",
                        "value": ext.diameter_mm or 46.0,
                        "description": "Cell outer diameter in mm",
                    },
                    {
                        "name": "CELL_HEIGHT",
                        "value": ext.height_mm or 65.0,
                        "description": "Cell height in mm",
                    },
                ]
            )
            wall_params.extend(
                [
                    {
                        "name": "CAN_WALL_THICKNESS",
                        "value": ext.wall_thickness_mm or 0.5,
                        "description": "Can wall thickness in mm",
                    },
                    {
                        "name": "CAN_BOTTOM_THICKNESS",
                        "value": 0.8,
                        "description": "Can bottom thickness in mm",
                    },
                    {
                        "name": "HEADER_HEIGHT",
                        "value": 5.0,
                        "description": "Header assembly height in mm",
                    },
                    {
                        "name": "MANDREL_RADIUS",
                        "value": getattr(stack, "mandrel_diameter_mm", 5.0) / 2,
                        "description": "Inner mandrel radius in mm",
                    },
                ]
            )

        # Stack parameters
        if hasattr(stack, "num_electrode_pairs"):
            stack_params.append(
                {
                    "name": "NUM_ELECTRODE_PAIRS",
                    "value": stack.num_electrode_pairs,
                    "description": "Number of electrode pairs in stack",
                }
            )
        if hasattr(stack, "num_winds"):
            stack_params.append(
                {
                    "name": "NUM_WINDS",
                    "value": stack.num_winds,
                    "description": "Number of winds in jellyroll (0 = auto-calculate)",
                }
            )

        # Layer thicknesses (extract from layers or use defaults)
        thickness_params.extend(
            [
                {
                    "name": "CATHODE_COATING_THICKNESS",
                    "value": self._get_layer_thickness(stack, "cathode_coating", 70),
                    "description": "Cathode coating thickness in um (per side)",
                },
                {
                    "name": "CATHODE_COLLECTOR_THICKNESS",
                    "value": self._get_layer_thickness(stack, "cathode_collector", 15),
                    "description": "Cathode current collector (Al) thickness in um",
                },
                {
                    "name": "ANODE_COATING_THICKNESS",
                    "value": self._get_layer_thickness(stack, "anode_coating", 80),
                    "description": "Anode coating thickness in um (per side)",
                },
                {
                    "name": "ANODE_COLLECTOR_THICKNESS",
                    "value": self._get_layer_thickness(stack, "anode_collector", 10),
                    "description": "Anode current collector (Cu) thickness in um",
                },
                {
                    "name": "SEPARATOR_THICKNESS",
                    "value": self._get_layer_thickness(stack, "separator", 20),
                    "description": "Separator thickness in um",
                },
            ]
        )

        # Overhang dimensions
        anode_overhang = 1.0
        separator_overhang = 2.0
        if zones:
            anode_overhang = zones.anode_overhang_x_mm or 1.0
            separator_overhang = zones.separator_overhang_mm or 2.0

        overhang_params.extend(
            [
                {
                    "name": "ANODE_OVERHANG",
                    "value": anode_overhang,
                    "description": "Anode overhang beyond cathode in mm (each side)",
                },
                {
                    "name": "SEPARATOR_OVERHANG",
                    "value": separator_overhang,
                    "description": "Separator overhang beyond anode in mm (each side)",
                },
            ]
        )

        # Materials info
        materials = {
            "Cathode_Coating": geometry.chemistry,
            "Cathode_Collector": "Aluminum (Al)",
            "Anode_Coating": "Graphite",
            "Anode_Collector": "Copper (Cu)",
            "Separator": "PP/PE/PP or Ceramic-coated",
            "Casing": "Aluminum (pouch/prismatic) or Steel (cylindrical)",
        }

        # Colors (FreeCAD format)
        colors = {}
        transparency = {}
        for material_group in [
            "Cathode_Coating",
            "Cathode_Collector",
            "Anode_Coating",
            "Anode_Collector",
            "Separator",
            "Casing",
        ]:
            color = FreeCADColorScheme.get_color_for_material(material_group, geometry.chemistry)
            colors[material_group] = color.to_freecad_string()
            transparency[material_group] = MATERIAL_TRANSPARENCY.get(material_group, 0)

        return {
            "header_comment": header_comment,
            "cellcad_version": self.VERSION,
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cell_type": geometry.cell_type.title(),
            "chemistry": geometry.chemistry,
            "archetype_name": geometry.archetype_name,
            "document_name": geometry.archetype_name.replace(" ", "_").replace("-", "_"),
            "grouped_by_material": (self.grouping_mode == GroupingMode.BY_MATERIAL),
            "external_params": external_params,
            "wall_params": wall_params,
            "stack_params": stack_params,
            "thickness_params": thickness_params,
            "overhang_params": overhang_params,
            "materials": materials,
            "colors": colors,
            "transparency": transparency,
        }

    def _get_layer_thickness(self, stack, layer_type: str, default: float) -> float:
        """Extract layer thickness from stack geometry."""
        if not hasattr(stack, "layers"):
            return default

        for layer in stack.layers:
            if layer_type in layer.layer_type.value:
                return layer.thickness_um

        return default


def generate_freecad_script_from_archetype(
    archetype_path: Path | str,
    output_path: Path | str,
    grouping_mode: str = "by_material",
    apply_swelling: bool = True,
) -> ScriptGenerationResult:
    """Convenience function to generate FreeCAD script from archetype.

    Args:
        archetype_path: Path to archetype JSON file
        output_path: Output Python script path
        grouping_mode: "by_material" or "individual"
        apply_swelling: Apply EOL swelling to geometry

    Returns:
        ScriptGenerationResult with generation details
    """
    from ...geometry.loader import ArchetypeLoader

    loader = ArchetypeLoader(archetype_path)
    geometry = loader.to_detailed_geometry(apply_swelling=apply_swelling)

    generator = FreeCADScriptGenerator(grouping_mode=grouping_mode)
    return generator.generate(geometry, output_path)
