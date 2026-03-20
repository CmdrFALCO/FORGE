"""Convert DetailedGeometry to Build123d solids.

This module handles the conversion of computed layer geometry from Phase 1
into Build123d solid bodies suitable for STEP export.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .assembly import AssemblyNamer, CADBody, MaterialGroup
from .availability import require_build123d

if TYPE_CHECKING:
    from ..geometry.detailed_geometry import DetailedGeometry
    from ..geometry.layer_stack import (
        Layer,
        LayerStackGeometry,
        LayerType,
        WindingGeometry,
    )
    from ..geometry.tabs.models import Busbar, TabStrip
    from ..geometry.tabs.terminals.models import TerminalAssembly, TerminalPost


class GroupingMode(str, Enum):
    """How to group layers into CAD bodies.

    BY_MATERIAL: One body per material type (default, smaller files)
    INDIVIDUAL: One body per layer (detailed, large files)
    """

    BY_MATERIAL = "by_material"
    INDIVIDUAL = "individual"


class BodyBuilder:
    """Build CAD bodies from DetailedGeometry.

    Converts the computed layer-by-layer geometry into Build123d solids
    with center-origin coordinate system.

    Attributes:
        grouping_mode: How layers are grouped into bodies
    """

    def __init__(self, grouping_mode: GroupingMode = GroupingMode.BY_MATERIAL) -> None:
        """Initialize builder.

        Args:
            grouping_mode: How to group layers into bodies

        Raises:
            ImportError: If build123d is not available
        """
        require_build123d()
        self.grouping_mode = grouping_mode

    def build_stacked_cell(
        self,
        geometry: DetailedGeometry,
    ) -> list[CADBody]:
        """Build bodies for stacked (pouch/prismatic) cell.

        Coordinate system: Center origin
        - X: along cell length
        - Y: along cell width
        - Z: along cell thickness (stack direction)

        Args:
            geometry: DetailedGeometry from Phase 1

        Returns:
            List of CADBody objects with Build123d solids
        """
        bodies: list[CADBody] = []
        stack: LayerStackGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        # Cell dimensions (center origin)
        length = ext.length_mm or 100.0
        width = ext.width_mm or 100.0
        thickness = ext.thickness_mm or ext.height_mm or 20.0
        wall = ext.wall_thickness_mm or 0.5

        # Internal dimensions
        internal_length = length - 2 * wall
        internal_width = width - 2 * wall

        # Stack offset to center in Z
        stack_height_mm = stack.total_thickness_um / 1000.0
        z_offset = -stack_height_mm / 2

        if self.grouping_mode == GroupingMode.BY_MATERIAL:
            bodies.extend(
                self._build_stacked_grouped(stack, internal_length, internal_width, z_offset, geometry)
            )
        else:
            bodies.extend(
                self._build_stacked_individual(stack, internal_length, internal_width, z_offset, geometry)
            )

        # Add casing
        bodies.append(self._build_prismatic_casing(length, width, thickness, wall))

        return bodies

    def _build_stacked_grouped(
        self,
        stack: LayerStackGeometry,
        length: float,
        width: float,
        z_offset: float,
        geometry: DetailedGeometry,
    ) -> list[CADBody]:
        """Build stacked cell with layers grouped by material."""
        import build123d as bd

        from ..geometry.layer_stack import LayerType

        bodies: list[CADBody] = []

        # Group layers by type
        layer_groups: dict[LayerType, list[Layer]] = {}
        for layer in stack.layers:
            if layer.layer_type not in layer_groups:
                layer_groups[layer.layer_type] = []
            layer_groups[layer.layer_type].append(layer)

        # Map LayerType to MaterialGroup
        type_to_group = {
            LayerType.CATHODE_COLLECTOR: MaterialGroup.CATHODE_COLLECTOR,
            LayerType.CATHODE_COATING: MaterialGroup.CATHODE_COATING,
            LayerType.ANODE_COLLECTOR: MaterialGroup.ANODE_COLLECTOR,
            LayerType.ANODE_COATING: MaterialGroup.ANODE_COATING,
            LayerType.SEPARATOR: MaterialGroup.SEPARATOR,
        }

        for layer_type, layers in layer_groups.items():
            material_group = type_to_group.get(layer_type)
            if material_group is None:
                continue

            # Get X/Y dimensions based on layer type (with overhangs)
            layer_length, layer_width = self._get_layer_dimensions(layer_type, length, width, geometry)

            # Create individual boxes for each layer
            solids = []
            for layer in layers:
                z_min = layer.z_bottom_um / 1000.0 + z_offset
                z_height = layer.thickness_um / 1000.0
                z_center = z_min + z_height / 2

                with bd.BuildPart() as part:
                    with bd.BuildSketch():
                        bd.Rectangle(layer_length, layer_width)
                    bd.extrude(amount=z_height)
                box = part.part.moved(bd.Location((0, 0, z_center)))
                solids.append(box)

            # Fuse all solids of same type into one compound
            if solids:
                if len(solids) == 1:
                    combined = solids[0]
                else:
                    combined = bd.Compound(solids)

                body = CADBody(
                    name=AssemblyNamer.body_name(material_group),
                    material_group=material_group,
                )
                body.solid = combined
                bodies.append(body)

        return bodies

    def _build_stacked_individual(
        self,
        stack: LayerStackGeometry,
        length: float,
        width: float,
        z_offset: float,
        geometry: DetailedGeometry,
    ) -> list[CADBody]:
        """Build stacked cell with individual layer bodies."""
        import build123d as bd

        from ..geometry.layer_stack import LayerType

        bodies: list[CADBody] = []

        type_to_group = {
            LayerType.CATHODE_COLLECTOR: MaterialGroup.CATHODE_COLLECTOR,
            LayerType.CATHODE_COATING: MaterialGroup.CATHODE_COATING,
            LayerType.ANODE_COLLECTOR: MaterialGroup.ANODE_COLLECTOR,
            LayerType.ANODE_COATING: MaterialGroup.ANODE_COATING,
            LayerType.SEPARATOR: MaterialGroup.SEPARATOR,
        }

        total_layers = len(stack.layers)

        for layer in stack.layers:
            material_group = type_to_group.get(layer.layer_type)
            if material_group is None:
                continue

            layer_length, layer_width = self._get_layer_dimensions(
                layer.layer_type, length, width, geometry
            )

            z_min = layer.z_bottom_um / 1000.0 + z_offset
            z_height = layer.thickness_um / 1000.0
            z_center = z_min + z_height / 2

            with bd.BuildPart() as part:
                with bd.BuildSketch():
                    bd.Rectangle(layer_length, layer_width)
                bd.extrude(amount=z_height)
            box = part.part.moved(bd.Location((0, 0, z_center)))

            body = CADBody(
                name=AssemblyNamer.body_name(material_group, index=layer.layer_index, total=total_layers),
                material_group=material_group,
                layer_index=layer.layer_index,
            )
            body.solid = box
            bodies.append(body)

        return bodies

    def _get_layer_dimensions(
        self,
        layer_type: LayerType,
        base_length: float,
        base_width: float,
        geometry: DetailedGeometry,
    ) -> tuple[float, float]:
        """Get layer X/Y dimensions accounting for overhangs.

        Cathode is smallest, anode has overhang, separator covers all.

        Args:
            layer_type: Type of layer
            base_length: Base length (internal cathode dimension)
            base_width: Base width (internal cathode dimension)
            geometry: DetailedGeometry for coating zone info

        Returns:
            Tuple of (length, width) in mm
        """
        from ..geometry.layer_stack import LayerType

        # Default overhangs (mm)
        anode_overhang = 1.0
        separator_overhang = 2.0

        # Use coating zones if available
        if geometry.coating_zones:
            zones = geometry.coating_zones
            if zones.anode_overhang_x_mm:
                anode_overhang = zones.anode_overhang_x_mm
            if zones.separator_overhang_mm:
                separator_overhang = zones.separator_overhang_mm

        if layer_type in (LayerType.CATHODE_COLLECTOR, LayerType.CATHODE_COATING):
            return base_length, base_width
        elif layer_type in (LayerType.ANODE_COLLECTOR, LayerType.ANODE_COATING):
            return base_length + anode_overhang, base_width + anode_overhang
        elif layer_type == LayerType.SEPARATOR:
            return base_length + separator_overhang, base_width + separator_overhang
        else:
            return base_length, base_width

    def _build_prismatic_casing(
        self,
        length: float,
        width: float,
        thickness: float,
        wall: float,
    ) -> CADBody:
        """Build prismatic/pouch casing as hollow box.

        Args:
            length: Outer length
            width: Outer width
            thickness: Outer thickness/height
            wall: Wall thickness

        Returns:
            CADBody with casing solid
        """
        import build123d as bd

        # Outer box
        with bd.BuildPart() as outer_part:
            with bd.BuildSketch():
                bd.Rectangle(length, width)
            bd.extrude(amount=thickness)
        outer = outer_part.part.moved(bd.Location((0, 0, 0)))

        # Inner cutout
        inner_length = length - 2 * wall
        inner_width = width - 2 * wall
        inner_thickness = thickness - 2 * wall

        with bd.BuildPart() as inner_part:
            with bd.BuildSketch():
                bd.Rectangle(inner_length, inner_width)
            bd.extrude(amount=inner_thickness)
        inner = inner_part.part.moved(bd.Location((0, 0, wall)))

        # Subtract to create shell
        casing = outer - inner

        body = CADBody(
            name=AssemblyNamer.body_name(MaterialGroup.CASING),
            material_group=MaterialGroup.CASING,
        )
        body.solid = casing
        return body

    def build_wound_cell(
        self,
        geometry: DetailedGeometry,
    ) -> list[CADBody]:
        """Build bodies for wound (cylindrical) cell.

        Coordinate system: Center origin
        - X, Y: radial plane
        - Z: along cell axis (height)

        Args:
            geometry: DetailedGeometry from Phase 1

        Returns:
            List of CADBody objects with Build123d solids
        """
        bodies: list[CADBody] = []
        winding: WindingGeometry = geometry.layer_stack  # type: ignore
        ext = geometry.external_geometry

        diameter = ext.diameter_mm or 46.0
        height = ext.height_mm or 65.0
        wall = ext.wall_thickness_mm or 0.5

        # Z offset to center
        z_offset = -height / 2

        if self.grouping_mode == GroupingMode.BY_MATERIAL:
            bodies.extend(self._build_wound_grouped(winding, height, z_offset, geometry))
        else:
            bodies.extend(self._build_wound_individual(winding, height, z_offset, geometry))

        # Add casing (cylindrical can)
        bodies.append(self._build_cylindrical_casing(diameter, height, wall))

        return bodies

    def _build_wound_grouped(
        self,
        winding: WindingGeometry,
        height: float,
        z_offset: float,
        geometry: DetailedGeometry,
    ) -> list[CADBody]:
        """Build wound cell with concentric material regions."""
        import build123d as bd

        bodies: list[CADBody] = []

        # For wound cells, collect radial extents for each material
        material_radii: dict[MaterialGroup, list[tuple[float, float]]] = {
            MaterialGroup.ANODE_COLLECTOR: [],
            MaterialGroup.ANODE_COATING: [],
            MaterialGroup.SEPARATOR: [],
            MaterialGroup.CATHODE_COATING: [],
            MaterialGroup.CATHODE_COLLECTOR: [],
        }

        for wind in winding.winds:
            # Each wind has sublayers - extract their radii
            material_radii[MaterialGroup.ANODE_COLLECTOR].append(
                (wind.anode_collector_r[0] / 1000.0, wind.anode_collector_r[1] / 1000.0)
            )
            material_radii[MaterialGroup.ANODE_COATING].append(
                (wind.anode_coating_inner_r[0] / 1000.0, wind.anode_coating_inner_r[1] / 1000.0)
            )
            material_radii[MaterialGroup.ANODE_COATING].append(
                (wind.anode_coating_outer_r[0] / 1000.0, wind.anode_coating_outer_r[1] / 1000.0)
            )
            material_radii[MaterialGroup.SEPARATOR].append(
                (wind.separator_inner_r[0] / 1000.0, wind.separator_inner_r[1] / 1000.0)
            )
            material_radii[MaterialGroup.SEPARATOR].append(
                (wind.separator_outer_r[0] / 1000.0, wind.separator_outer_r[1] / 1000.0)
            )
            material_radii[MaterialGroup.CATHODE_COATING].append(
                (wind.cathode_coating_inner_r[0] / 1000.0, wind.cathode_coating_inner_r[1] / 1000.0)
            )
            material_radii[MaterialGroup.CATHODE_COATING].append(
                (wind.cathode_coating_outer_r[0] / 1000.0, wind.cathode_coating_outer_r[1] / 1000.0)
            )
            material_radii[MaterialGroup.CATHODE_COLLECTOR].append(
                (wind.cathode_collector_r[0] / 1000.0, wind.cathode_collector_r[1] / 1000.0)
            )

        # Create fused annular solids for each material
        for material_group, radii_list in material_radii.items():
            if not radii_list:
                continue

            solids = []
            for r_inner, r_outer in radii_list:
                if r_outer <= r_inner or r_inner < 0:
                    continue

                annulus = self._create_annulus(r_inner, r_outer, height, z_offset)
                if annulus is not None:
                    solids.append(annulus)

            if solids:
                combined = bd.Compound(solids) if len(solids) > 1 else solids[0]

                body = CADBody(
                    name=AssemblyNamer.body_name(material_group),
                    material_group=material_group,
                )
                body.solid = combined
                bodies.append(body)

        return bodies

    def _build_wound_individual(
        self,
        winding: WindingGeometry,
        height: float,
        z_offset: float,
        geometry: DetailedGeometry,
    ) -> list[CADBody]:
        """Build wound cell with individual wind bodies."""
        bodies: list[CADBody] = []
        total_winds = winding.num_winds

        for wind in winding.winds:
            # Create single annular body for entire wind
            r_inner = wind.r_inner_um / 1000.0
            r_outer = wind.r_outer_um / 1000.0

            if r_outer <= r_inner:
                continue

            annulus = self._create_annulus(r_inner, r_outer, height, z_offset)
            if annulus is None:
                continue

            # Use generic naming - winds contain mixed materials
            body = CADBody(
                name=AssemblyNamer.wind_name(wind.wind_index, total_winds),
                material_group=MaterialGroup.JELLYROLL,
                layer_index=wind.wind_index,
            )
            body.solid = annulus
            bodies.append(body)

        return bodies

    def _create_annulus(
        self,
        r_inner: float,
        r_outer: float,
        height: float,
        z_offset: float,
    ) -> object | None:
        """Create annular cylinder (hollow cylinder).

        Args:
            r_inner: Inner radius in mm
            r_outer: Outer radius in mm
            height: Height in mm
            z_offset: Z offset to center

        Returns:
            Build123d solid or None if invalid dimensions
        """
        import build123d as bd

        if r_outer <= r_inner or r_outer <= 0:
            return None

        # Create outer cylinder
        outer = bd.Cylinder(r_outer, height)

        if r_inner > 0:
            # Create inner cylinder and subtract
            inner = bd.Cylinder(r_inner, height)
            annulus = outer - inner
        else:
            annulus = outer

        # Move to center origin
        annulus = annulus.moved(bd.Location((0, 0, z_offset + height / 2)))

        return annulus

    def _build_cylindrical_casing(
        self,
        diameter: float,
        height: float,
        wall: float,
    ) -> CADBody:
        """Build cylindrical can as hollow cylinder.

        Args:
            diameter: Outer diameter
            height: Height
            wall: Wall thickness

        Returns:
            CADBody with casing solid
        """
        import build123d as bd

        r_outer = diameter / 2
        r_inner = r_outer - wall

        # Outer cylinder
        outer = bd.Cylinder(r_outer, height)

        # Inner cylinder (with bottom wall)
        inner = bd.Cylinder(r_inner, height - wall)
        inner = inner.moved(bd.Location((0, 0, wall / 2)))

        casing = outer - inner
        casing = casing.moved(bd.Location((0, 0, -height / 2 + height / 2)))

        body = CADBody(
            name=AssemblyNamer.body_name(MaterialGroup.CASING),
            material_group=MaterialGroup.CASING,
        )
        body.solid = casing
        return body

    def build_tabs_and_terminals(
        self,
        geometry: "DetailedGeometry",
    ) -> list[CADBody]:
        """Build CAD bodies for tabs and terminals.

        Args:
            geometry: DetailedGeometry with tab_geometry and terminal_assembly

        Returns:
            List of CADBody for tabs and terminals
        """
        bodies: list[CADBody] = []

        # Ensure tabs are calculated
        tab_geom = geometry.tab_geometry
        if tab_geom is None:
            geometry.calculate_tabs()
            tab_geom = geometry.tab_geometry

        if tab_geom is None:
            return bodies

        if self.grouping_mode == GroupingMode.BY_MATERIAL:
            positive_body = self._build_grouped_tab_strips(
                tab_geom.positive_tabs,
                MaterialGroup.TAB_POSITIVE,
            )
            if positive_body:
                bodies.append(positive_body)

            negative_body = self._build_grouped_tab_strips(
                tab_geom.negative_tabs,
                MaterialGroup.TAB_NEGATIVE,
            )
            if negative_body:
                bodies.append(negative_body)
        else:
            # Build positive tabs
            for i, tab in enumerate(tab_geom.positive_tabs):
                body = self._build_tab_strip(
                    tab, f"Tab_Pos_{i:03d}", MaterialGroup.TAB_POSITIVE
                )
                if body:
                    bodies.append(body)

            # Build negative tabs
            for i, tab in enumerate(tab_geom.negative_tabs):
                body = self._build_tab_strip(
                    tab, f"Tab_Neg_{i:03d}", MaterialGroup.TAB_NEGATIVE
                )
                if body:
                    bodies.append(body)

        # Build busbars
        if tab_geom.positive_busbar:
            body = self._build_busbar(
                tab_geom.positive_busbar, "Busbar_Pos", MaterialGroup.BUSBAR_POSITIVE
            )
            if body:
                bodies.append(body)

        if tab_geom.negative_busbar:
            body = self._build_busbar(
                tab_geom.negative_busbar, "Busbar_Neg", MaterialGroup.BUSBAR_NEGATIVE
            )
            if body:
                bodies.append(body)

        # Stacked cells already expose their connectivity through tab strips and busbars.
        # Exporting coarse terminal posts from tab geometry duplicates those bodies and
        # breaks grouped-material expectations for pouch/prismatic assemblies.
        if geometry.cell_type == "cylindrical":
            if tab_geom.positive_terminal:
                body = self._build_terminal_post(
                    tab_geom.positive_terminal,
                    "Terminal_Pos",
                    MaterialGroup.TERMINAL_POSITIVE,
                )
                if body:
                    bodies.append(body)

            if tab_geom.negative_terminal:
                body = self._build_terminal_post(
                    tab_geom.negative_terminal,
                    "Terminal_Neg",
                    MaterialGroup.TERMINAL_NEGATIVE,
                )
                if body:
                    bodies.append(body)

        # Build terminal assembly components (insulators, gaskets, header)
        terminal_assembly = getattr(geometry, "terminal_assembly", None)
        if terminal_assembly:
            bodies.extend(self._build_terminal_assembly_components(terminal_assembly))

        return bodies

    def _build_grouped_tab_strips(
        self,
        tabs: list["TabStrip"],
        material_group: MaterialGroup,
    ) -> CADBody | None:
        """Build one grouped body per tab polarity."""
        import build123d as bd

        solids = []
        for tab in tabs:
            body = self._build_tab_strip(tab, "unused", material_group)
            if body and body.solid is not None:
                solids.append(body.solid)

        if not solids:
            return None

        combined = solids[0] if len(solids) == 1 else bd.Compound(solids)
        body = CADBody(
            name=AssemblyNamer.body_name(material_group),
            material_group=material_group,
        )
        body.solid = combined
        return body

    def _build_tab_strip(
        self,
        tab: "TabStrip",
        name: str,
        material_group: MaterialGroup,
    ) -> CADBody | None:
        """Build CAD body for tab strip.

        Args:
            tab: TabStrip geometry
            name: Body name
            material_group: Material group

        Returns:
            CADBody with tab solid or None if invalid
        """
        import build123d as bd

        p = tab.attachment_point

        # Determine orientation based on exit direction
        if tab.exit_direction in ("x+", "x-"):
            length = tab.strip_length_mm
            width = tab.strip_width_mm
            height = tab.strip_thickness_mm
            sign = 1 if tab.exit_direction == "x+" else -1
            center_x = p.x + sign * length / 2
            center_y = p.y
            center_z = p.z
        elif tab.exit_direction in ("z+", "z-"):
            length = tab.strip_width_mm
            width = tab.strip_thickness_mm
            height = tab.strip_length_mm
            sign = 1 if tab.exit_direction == "z+" else -1
            center_x = p.x
            center_y = p.y
            center_z = p.z + sign * height / 2
        else:  # y direction
            length = tab.strip_width_mm
            width = tab.strip_length_mm
            height = tab.strip_thickness_mm
            sign = 1 if tab.exit_direction == "y+" else -1
            center_x = p.x
            center_y = p.y + sign * width / 2
            center_z = p.z

        with bd.BuildPart() as part:
            with bd.BuildSketch():
                bd.Rectangle(length, width)
            bd.extrude(amount=height)
        shape = part.part.moved(bd.Location((center_x, center_y, center_z)))

        body = CADBody(name=name, material_group=material_group)
        body.solid = shape
        return body

    def _build_busbar(
        self,
        busbar: "Busbar",
        name: str,
        material_group: MaterialGroup,
    ) -> CADBody | None:
        """Build CAD body for busbar.

        Args:
            busbar: Busbar geometry
            name: Body name
            material_group: Material group

        Returns:
            CADBody with busbar solid or None if invalid
        """
        import build123d as bd

        s = busbar.start_point
        e = busbar.end_point

        # Calculate length and center
        dx = e.x - s.x
        dy = e.y - s.y
        dz = e.z - s.z
        length = (dx**2 + dy**2 + dz**2) ** 0.5

        if length < 0.01:
            return None

        center_x = (s.x + e.x) / 2
        center_y = (s.y + e.y) / 2
        center_z = (s.z + e.z) / 2

        # Determine primary direction
        if abs(dx) >= abs(dy) and abs(dx) >= abs(dz):
            # X-oriented busbar
            with bd.BuildPart() as part:
                with bd.BuildSketch():
                    bd.Rectangle(length, busbar.width_mm)
                bd.extrude(amount=busbar.thickness_mm)
            shape = part.part.moved(bd.Location((center_x, center_y, center_z)))
        elif abs(dy) >= abs(dz):
            # Y-oriented busbar
            with bd.BuildPart() as part:
                with bd.BuildSketch():
                    bd.Rectangle(busbar.width_mm, length)
                bd.extrude(amount=busbar.thickness_mm)
            shape = part.part.moved(bd.Location((center_x, center_y, center_z)))
        else:
            # Z-oriented busbar
            with bd.BuildPart() as part:
                with bd.BuildSketch():
                    bd.Rectangle(busbar.width_mm, busbar.thickness_mm)
                bd.extrude(amount=length)
            shape = part.part.moved(bd.Location((center_x, center_y, center_z)))

        body = CADBody(name=name, material_group=material_group)
        body.solid = shape
        return body

    def _build_terminal_post(
        self,
        terminal: "TerminalPost",
        name: str,
        material_group: MaterialGroup,
    ) -> CADBody | None:
        """Build CAD body for terminal post.

        Args:
            terminal: TerminalPost geometry (from tabs.models)
            name: Body name
            material_group: Material group

        Returns:
            CADBody with terminal solid or None if invalid
        """
        import build123d as bd

        p = terminal.position

        if terminal.diameter_mm:
            # Cylindrical terminal
            shape = bd.Cylinder(
                radius=terminal.diameter_mm / 2,
                height=terminal.height_mm,
            )
        else:
            # Rectangular terminal
            with bd.BuildPart() as part:
                with bd.BuildSketch():
                    bd.Rectangle(terminal.width_mm or 10, terminal.length_mm or 10)
                bd.extrude(amount=terminal.height_mm)
            shape = part.part

        shape = shape.moved(bd.Location((p.x, p.y, p.z + terminal.height_mm / 2)))

        body = CADBody(name=name, material_group=material_group)
        body.solid = shape
        return body

    def _build_terminal_assembly_components(
        self,
        assembly: "TerminalAssembly",
    ) -> list[CADBody]:
        """Build CAD bodies for terminal assembly components.

        Args:
            assembly: TerminalAssembly with detailed components

        Returns:
            List of CADBody for insulators, gaskets, header components
        """
        import build123d as bd

        bodies: list[CADBody] = []

        # Build header assembly for cylindrical cells
        if assembly.header_assembly:
            header = assembly.header_assembly

            # Positive cap
            if header.positive_cap:
                cap = header.positive_cap
                shape = bd.Cylinder(
                    radius=cap.outer_diameter_mm / 2,
                    height=cap.height_mm,
                )
                shape = shape.moved(
                    bd.Location(
                        (
                            cap.position.x,
                            cap.position.y,
                            cap.position.z,
                        )
                    )
                )
                body = CADBody(
                    name="Positive_Cap",
                    material_group=MaterialGroup.HEADER,
                )
                body.solid = shape
                bodies.append(body)

            # Vent disc
            if header.vent_disc:
                vent = header.vent_disc
                shape = bd.Cylinder(
                    radius=vent.diameter_mm / 2,
                    height=vent.thickness_mm,
                )
                shape = shape.moved(
                    bd.Location(
                        (
                            vent.position.x,
                            vent.position.y,
                            vent.position.z,
                        )
                    )
                )
                body = CADBody(
                    name="Vent_Disc",
                    material_group=MaterialGroup.VENT,
                )
                body.solid = shape
                bodies.append(body)

            # CID
            if header.cid:
                cid = header.cid
                shape = bd.Cylinder(
                    radius=cid.diameter_mm / 2,
                    height=cid.thickness_mm,
                )
                shape = shape.moved(
                    bd.Location(
                        (
                            cid.position.x,
                            cid.position.y,
                            cid.position.z,
                        )
                    )
                )
                body = CADBody(
                    name="CID",
                    material_group=MaterialGroup.CID,
                )
                body.solid = shape
                bodies.append(body)

            # Top insulator (ring)
            if header.top_insulator:
                ins = header.top_insulator
                outer = bd.Cylinder(
                    radius=ins.outer_diameter_mm / 2, height=ins.thickness_mm
                )
                inner = bd.Cylinder(
                    radius=ins.inner_diameter_mm / 2, height=ins.thickness_mm + 0.1
                )
                shape = outer - inner
                shape = shape.moved(
                    bd.Location(
                        (
                            ins.position.x,
                            ins.position.y,
                            ins.position.z,
                        )
                    )
                )
                body = CADBody(
                    name="Header_Insulator",
                    material_group=MaterialGroup.INSULATOR,
                )
                body.solid = shape
                bodies.append(body)

            # Gasket
            if header.gasket:
                gasket = header.gasket
                if (
                    gasket.is_circular
                    and gasket.outer_diameter_mm
                    and gasket.inner_diameter_mm
                ):
                    outer = bd.Cylinder(
                        radius=gasket.outer_diameter_mm / 2, height=gasket.thickness_mm
                    )
                    inner = bd.Cylinder(
                        radius=gasket.inner_diameter_mm / 2,
                        height=gasket.thickness_mm + 0.1,
                    )
                    shape = outer - inner
                else:
                    with bd.BuildPart() as part:
                        with bd.BuildSketch():
                            bd.Rectangle(
                                gasket.width_mm or 10, gasket.length_mm or 10
                            )
                        bd.extrude(amount=gasket.thickness_mm)
                    shape = part.part
                shape = shape.moved(
                    bd.Location(
                        (
                            gasket.position.x,
                            gasket.position.y,
                            gasket.position.z,
                        )
                    )
                )
                body = CADBody(
                    name="Header_Gasket",
                    material_group=MaterialGroup.GASKET,
                )
                body.solid = shape
                bodies.append(body)

        # Build insulators and gaskets for terminals
        for terminal, name_prefix in [
            (assembly.positive_terminal, "Pos"),
            (assembly.negative_terminal, "Neg"),
        ]:
            if terminal and terminal.insulator:
                ins = terminal.insulator
                outer = bd.Cylinder(
                    radius=ins.outer_diameter_mm / 2, height=ins.thickness_mm
                )
                inner = bd.Cylinder(
                    radius=ins.inner_diameter_mm / 2, height=ins.thickness_mm + 0.1
                )
                shape = outer - inner
                shape = shape.moved(
                    bd.Location(
                        (
                            ins.position.x,
                            ins.position.y,
                            ins.position.z,
                        )
                    )
                )
                body = CADBody(
                    name=f"Insulator_{name_prefix}",
                    material_group=MaterialGroup.INSULATOR,
                )
                body.solid = shape
                bodies.append(body)

            if terminal and terminal.gasket:
                gasket = terminal.gasket
                if (
                    gasket.is_circular
                    and gasket.outer_diameter_mm
                    and gasket.inner_diameter_mm
                ):
                    outer = bd.Cylinder(
                        radius=gasket.outer_diameter_mm / 2, height=gasket.thickness_mm
                    )
                    inner = bd.Cylinder(
                        radius=gasket.inner_diameter_mm / 2,
                        height=gasket.thickness_mm + 0.1,
                    )
                    shape = outer - inner
                else:
                    with bd.BuildPart() as part:
                        with bd.BuildSketch():
                            bd.Rectangle(
                                gasket.width_mm or 10, gasket.length_mm or 10
                            )
                        bd.extrude(amount=gasket.thickness_mm)
                    shape = part.part
                shape = shape.moved(
                    bd.Location(
                        (
                            gasket.position.x,
                            gasket.position.y,
                            gasket.position.z,
                        )
                    )
                )
                body = CADBody(
                    name=f"Gasket_{name_prefix}",
                    material_group=MaterialGroup.GASKET,
                )
                body.solid = shape
                bodies.append(body)

        return bodies
