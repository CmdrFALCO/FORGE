"""Pydantic schemas for archetype JSON validation.

This module defines Pydantic models that validate archetype JSON structure,
providing type-safe access to cell design parameters with confidence tracking.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfidenceLevel(str, Enum):
    """Confidence level for data quality tracking."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# =============================================================================
# Chemistry and Metadata
# =============================================================================


class ChemistryInfo(BaseModel):
    """Chemistry information for the cell."""

    cathode: str  # e.g., "NMC811", "LFP", "NCM712"
    anode: str = "Graphite"  # e.g., "Graphite", "Graphite + Si"
    cathode_composition: str | None = None  # e.g., "81.6% Ni, 12% Co, 6.3% Mn"
    cathode_formula: str | None = None  # e.g., "LiFePO4"
    anode_note: str | None = None
    silicon_content_pct: float | None = None
    silicon_content_pct_estimate: list[float] | None = None
    silicon_content_range_pct: list[float] | None = None


class MetadataInfo(BaseModel):
    """Cell metadata including identification and sources."""

    name: str
    archetype_version: str = "1.0.0"
    created: str | None = None
    cell_type: str  # "Cylindrical", "Prismatic", "Pouch", "Prismatic (Blade)"
    manufacturer: str | None = None
    model: str | None = None
    application: str | None = None
    chemistry: ChemistryInfo
    data_sources: list[str] = Field(default_factory=list)
    research_notes: str | None = None
    vda_standard: str | None = None
    capacity_class_Ah: str | None = None


# =============================================================================
# Geometry
# =============================================================================


class ExternalGeometry(BaseModel):
    """External cell dimensions."""

    # Prismatic/Pouch
    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    thickness_mm: float | None = None  # Pouch cells use thickness

    # Tolerances
    length_tolerance_mm: float | None = None
    width_tolerance_mm: float | None = None
    height_tolerance_mm: float | None = None
    width_range_mm: list[float] | None = None
    height_range_mm: list[float] | None = None
    height_tolerance_plus_mm: float | None = None
    height_tolerance_minus_mm: float | None = None

    # Cylindrical
    diameter_mm: float | None = None
    diameter_max_mm: float | None = None
    height_with_terminal_mm: float | None = None
    height_max_mm: float | None = None

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    notes: str | None = None


class CanGeometry(BaseModel):
    """Can (housing) geometry for cylindrical/prismatic cells."""

    material: str | None = None
    wall_thickness_mm: float | None = None
    wall_thickness_range_mm: list[float] | None = None
    wall_thickness_note: str | None = None
    base_thickness_mm: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


class WallsGeometry(BaseModel):
    """Wall geometry for prismatic cells."""

    wall_thickness_mm: float | None = None
    lid_thickness_mm: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


class JellyrollGeometry(BaseModel):
    """Jellyroll dimensions for cylindrical cells."""

    outer_diameter_mm: float | None = None
    height_mm: float | None = None
    jellyroll_to_can_gap_um: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class CoreGeometry(BaseModel):
    """Core/mandrel geometry for cylindrical cells."""

    type: str | None = None  # "Hollow (no mandrel)"
    void_diameter_mm: float | None = None
    mandrel_diameter_mm: float | None = None
    mandrel_note: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class PositiveTerminalGeometry(BaseModel):
    """Positive terminal geometry."""

    diameter_mm: float | None = None
    protrusion_mm: float | None = None


class PouchFilmGeometry(BaseModel):
    """Pouch film dimensions."""

    total_thickness_um: float | None = None
    structure: dict[str, Any] | None = None  # Flexible structure for layers
    draw_depth_mm: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class SealGeometry(BaseModel):
    """Seal dimensions for pouch cells."""

    perimeter_width_mm: float | None = None
    perimeter_width_range_mm: list[float] | None = None
    tab_seal_width_mm: float | None = None
    tab_seal_width_range_mm: list[float] | None = None


class InternalClearances(BaseModel):
    """Internal clearances within the cell."""

    stack_to_sidewall_mm: float | None = None
    stack_to_top_mm: float | None = None
    notes: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class CornerRadii(BaseModel):
    """Corner radii for prismatic cells."""

    external_mm: float | None = None
    internal_mm: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class HeaderGeometry(BaseModel):
    """Header assembly geometry."""

    assembly_height_mm: float | None = None
    assembly_height_range_mm: list[float] | None = None
    crimp_height_mm: float | None = None
    crimp_height_range_mm: list[float] | None = None


class GeometryInfo(BaseModel):
    """Complete geometry information."""

    external: ExternalGeometry
    can: CanGeometry | None = None
    walls: WallsGeometry | None = None
    jellyroll: JellyrollGeometry | None = None
    core: CoreGeometry | None = None
    positive_terminal: PositiveTerminalGeometry | None = None
    pouch_film: PouchFilmGeometry | None = None
    seal: SealGeometry | None = None
    internal_clearances: InternalClearances | None = None
    corner_radii: CornerRadii | None = None
    header: HeaderGeometry | None = None


# =============================================================================
# Electrical
# =============================================================================


class ElectricalInfo(BaseModel):
    """Electrical specifications."""

    nominal_voltage_V: float
    capacity_Ah: float | None = None
    capacity_typical_mAh: float | None = None
    capacity_min_mAh: float | None = None
    capacity_min_Ah: float | None = None
    capacity_min_range_mAh: list[float] | None = None
    capacity_measured_C20_Ah: float | None = None
    capacity_std_dev_mAh: float | None = None
    capacity_C3_Ah: float | None = None
    capacity_range_Ah: list[float] | None = None
    energy_Wh: float | None = None
    energy_min_Wh: float | None = None
    gravimetric_energy_density_Wh_kg: float | None = None
    gravimetric_ed_range_Wh_kg: list[float] | None = None
    volumetric_energy_density_Wh_L: float | None = None
    volumetric_ed_range_Wh_L: list[float] | None = None
    volumetric_ed_note: str | None = None
    power_density_W_kg: float | None = None
    power_density_W_L: float | None = None
    dcir_mOhm: float | None = None
    dcir_range_mOhm: list[float] | None = None
    dcir_note: str | None = None
    dc_resistance_mOhm: float | None = None
    dc_resistance_tolerance_mOhm: float | None = None
    ac_impedance_1kHz_mOhm: float | None = None
    ac_impedance_tolerance_mOhm: float | None = None
    cycle_life_80pct: int | None = None
    fast_charge_capability: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Mass
# =============================================================================


class MassInfo(BaseModel):
    """Mass specifications."""

    total_mass_g: float
    mass_range_g: list[float] | None = None
    tolerance_pct: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None
    sources: list[str] | None = None
    notes: str | None = None


# =============================================================================
# Electrode Stack
# =============================================================================


class CurrentCollectorInfo(BaseModel):
    """Current collector specifications."""

    material: str  # "Aluminum", "Copper"
    thickness_um: float | None = None
    thickness_range_um: list[float] | None = None
    end_disc_thickness_um: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class SheetDimensions(BaseModel):
    """Electrode sheet dimensions for stacked cells."""

    length_mm: float | None = None
    width_mm: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class CathodeLayer(BaseModel):
    """Cathode electrode specifications."""

    active_material: str  # e.g., "NMC811", "LiFePO4"
    coating_thickness_um: float | None = None
    coating_thickness_range_um: list[float] | None = None
    coating_thickness_note: str | None = None
    total_thickness_um: float | None = None
    current_collector: CurrentCollectorInfo | None = None

    # Wound cells
    total_length_mm: float | None = None
    width_mm: float | None = None
    width_range_mm: list[float] | None = None
    strip_length_mm: float | None = None
    strip_length_range_mm: list[float] | None = None

    # Stacked cells
    sheet_dimensions: SheetDimensions | None = None

    # Loading and capacity
    areal_capacity_mAh_cm2: float | None = None
    loading_mg_cm2: float | None = None
    loading_range_mg_cm2: list[float] | None = None
    total_electrode_thickness_um: float | None = None
    porosity_pct: float | None = None
    porosity_range_pct: list[float] | None = None

    # Process info
    coating_process: str | None = None

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class AnodeLayer(BaseModel):
    """Anode electrode specifications."""

    active_material: str  # e.g., "Graphite", "Graphite + SiOx"
    silicon_content_pct: float | None = None
    silicon_content_range_pct: list[float] | None = None
    silicon_note: str | None = None
    coating_thickness_um: float | None = None
    coating_thickness_range_um: list[float] | None = None
    total_thickness_um: float | None = None
    current_collector: CurrentCollectorInfo | None = None

    # Wound cells
    total_length_mm: float | None = None
    overhang_total_mm: float | None = None
    width_mm: float | None = None
    width_range_mm: list[float] | None = None

    # Stacked cells
    sheet_dimensions: SheetDimensions | None = None

    # Loading and capacity
    areal_capacity_mAh_cm2: float | None = None
    loading_mg_cm2: float | None = None
    loading_range_mg_cm2: list[float] | None = None
    total_electrode_thickness_um: float | None = None

    # Particle and process info
    graphite_particle_size_um: float | None = None
    binder: str | None = None
    coating_process: str | None = None
    anode_note: str | None = None

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class SeparatorDimensions(BaseModel):
    """Separator dimensions for stacked cells."""

    length_mm: float | None = None
    width_mm: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class SeparatorInfo(BaseModel):
    """Separator specifications."""

    type: str | None = None  # e.g., "Ceramic-coated PE", "PP/PE/PP"
    thickness_um: float | None = None
    thickness_range_um: list[float] | None = None
    thickness_note: str | None = None
    base_thickness_um: float | None = None
    coating_thickness_um: float | None = None
    total_thickness_um: float | None = None
    porosity_pct: float | None = None
    width_mm: float | None = None
    heat_resistance_C: float | None = None
    configuration: str | None = None

    # For stacked cells
    dimensions: SeparatorDimensions | None = None

    # For wound cells
    count: int | None = None
    count_note: str | None = None

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


class LayerCount(BaseModel):
    """Layer count for stacked cells."""

    cathode_layers: int
    anode_layers: int | None = None
    separator_layers: int | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


class CurrentCollectorsInfo(BaseModel):
    """Current collectors info (alternative format in some archetypes)."""

    aluminum_um: float | None = None
    copper_um: float | None = None
    copper_range_um: list[float] | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


class ElectrodeStackInfo(BaseModel):
    """Complete electrode stack information."""

    assembly_method: str  # "Wound jellyroll", "Z-fold stacking", etc.

    # For wound cells
    winding_turns_estimate: int | None = None
    winding_turns_range: list[int] | None = None
    winding_turns: int | None = None
    winding_count: int | None = None
    winding_notes: str | None = None
    internal_rolls: str | None = None

    # For stacked cells
    layer_count: LayerCount | None = None
    layer_count_estimate: int | None = None
    layer_count_range: list[int] | None = None
    layer_count_note: str | None = None

    cathode: CathodeLayer
    anode: AnodeLayer
    separator: SeparatorInfo

    # Alternative current collector info
    current_collectors: CurrentCollectorsInfo | None = None

    # Area calculations
    active_area_m2: float | None = None
    active_area_notes: str | None = None
    total_cathode_area_m2: float | None = None
    total_cathode_area_note: str | None = None
    total_electrode_area_m2_estimate: float | None = None
    total_electrode_area_range_m2: list[float] | None = None

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Safety Geometry
# =============================================================================


class AnodeOverhang(BaseModel):
    """Anode overhang specifications for stacked cells."""

    length_direction_mm: float | None = None
    width_direction_mm: float | None = None
    calculation: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class SafetyGeometryInfo(BaseModel):
    """Safety-related geometry specifications."""

    anode_overhang: AnodeOverhang | None = None
    anode_overhang_mm: float | None = None
    anode_overhang_range_mm: list[float] | None = None
    anode_overhang_total_mm: float | None = None
    anode_overhang_per_side_mm: float | None = None
    anode_overhang_note: str | None = None

    separator_overhang_mm: float | None = None
    separator_overhang_range_mm: list[float] | None = None
    separator_overhang_note: str | None = None

    np_ratio: float | None = None
    np_ratio_range: list[float] | None = None
    np_ratio_confidence: ConfidenceLevel | None = None

    alignment_tolerance_mm: float | None = None
    anode_cathode_area_ratio: float | None = None
    anode_cathode_ratio_range: list[float] | None = None

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


# =============================================================================
# Tabless Design (4680)
# =============================================================================


class NotchingInfo(BaseModel):
    """Notching specifications for tabless design."""

    cathode_not_notched_pct: float | None = None
    anode_not_notched_pct: float | None = None
    design: str | None = None


class TabDiscInfo(BaseModel):
    """Tab disc specifications for tabless design."""

    material_positive: str | None = None
    material_negative: str | None = None
    thickness_mm: float | None = None


class TablessDesignInfo(BaseModel):
    """Tabless design specifications (e.g., Tesla 4680)."""

    type: str | None = None
    notching: NotchingInfo | None = None
    tab_disc: TabDiscInfo | None = None
    connection: str | None = None
    current_path_length_mm: float | None = None
    current_path_traditional_mm: float | None = None
    resistance_reduction: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Header Assembly
# =============================================================================


class HeaderAssemblyInfo(BaseModel):
    """Header assembly specifications for cylindrical cells."""

    vent_location: str | None = None
    electrolyte_fill: str | None = None
    fill_closure: str | None = None
    jellyroll_fixation: str | None = None
    can_closure: str | None = None
    cid_present: bool | None = None
    cid_activation_pressure_MPa: float | None = None
    cid_activation_range_MPa: list[float] | None = None
    vent_present: bool | None = None
    insulation_ring: bool | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Casing
# =============================================================================


class VentInfo(BaseModel):
    """Vent specifications."""

    location: str | None = None
    type: str | None = None
    burst_pressure_MPa: float | None = None
    burst_pressure_range_MPa: list[float] | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class CasingInfo(BaseModel):
    """Casing specifications for prismatic cells."""

    material: str | None = None
    construction: str | None = None
    internal_insulation: str | None = None
    features: str | None = None
    vent: VentInfo | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


# =============================================================================
# Terminals
# =============================================================================


class TerminalSpec(BaseModel):
    """Individual terminal specifications."""

    material: str | None = None
    thread: str | None = None
    torque_Nm: float | None = None
    torque_range_Nm: list[float] | None = None
    width_mm: float | None = None
    thickness_mm: float | None = None


class TerminalInfo(BaseModel):
    """Terminal specifications."""

    configuration: str | None = None  # "Same side (top)", "Bi-directional"
    configuration_note: str | None = None
    type: str | None = None
    tabs_per_polarity: int | None = None
    positive: TerminalSpec | None = None
    negative: TerminalSpec | None = None
    positive_terminal: str | None = None
    negative_terminal: str | None = None
    tab_welding: str | None = None
    tab_connection: str | None = None
    tab_design: str | None = None
    thread: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str | None = None


# =============================================================================
# Dry Electrode
# =============================================================================


class DryElectrodeInfo(BaseModel):
    """Dry electrode process information."""

    status: str | None = None
    cathode_process: str | None = None
    anode_process: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Operating Conditions
# =============================================================================


class OperatingConditionsInfo(BaseModel):
    """Operating conditions specifications."""

    temperature_range_C: list[float] | None = None
    swelling_pct_over_life: float | None = None
    breathing_foam_allowance_mm: float | None = None
    compression_pressure_MPa: float | None = None
    compression_pressure_range_MPa: list[float] | None = None
    recommended_compression_kN: list[float] | None = None
    cooling: str | None = None
    notes: str | None = None


# =============================================================================
# Thermal Management
# =============================================================================


class CoolingPlateInfo(BaseModel):
    """Cooling plate specifications."""

    location: str | None = None
    thickness_mm: float | None = None
    thickness_range_mm: list[float] | None = None
    material: str | None = None


class ThermalManagementInfo(BaseModel):
    """Thermal management specifications."""

    cooling_interface: str | None = None
    cooling_plate: CoolingPlateInfo | None = None
    micron_bridge: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Validation
# =============================================================================


class ValidationTargets(BaseModel):
    """Validation targets for the archetype."""

    mass_target_g: float | None = None
    mass_tolerance_pct: float | None = None
    capacity_target_Ah: float | None = None
    capacity_target_mAh: float | None = None
    capacity_tolerance_pct: float | None = None
    gravimetric_ed_target_Wh_kg: float | None = None
    gravimetric_ed_tolerance_pct: float | None = None
    volumetric_ed_target_Wh_L: float | None = None
    volumetric_ed_tolerance_pct: float | None = None
    note: str | None = None


# =============================================================================
# Root Schema
# =============================================================================


class ArchetypeSchema(BaseModel):
    """Root schema for archetype JSON files.

    This schema validates the complete archetype structure with support for
    different cell types (Cylindrical, Prismatic, Pouch).
    """

    metadata: MetadataInfo
    geometry: GeometryInfo
    electrical: ElectricalInfo
    mass: MassInfo
    electrode_stack: ElectrodeStackInfo
    safety_geometry: SafetyGeometryInfo

    # Optional format-specific sections
    tabless_design: TablessDesignInfo | None = None
    header_assembly: HeaderAssemblyInfo | None = None
    dry_electrode: DryElectrodeInfo | None = None
    casing: CasingInfo | None = None
    terminals: TerminalInfo | None = None
    operating_conditions: OperatingConditionsInfo | None = None
    thermal_management: ThermalManagementInfo | None = None

    # Validation and quality
    validation: ValidationTargets
    data_gaps: list[str] = Field(default_factory=list)
    confidence_summary: dict[str, str] = Field(default_factory=dict)
    action_required: str | None = None

    model_config = ConfigDict(extra="allow")  # Allow extra fields for forward compatibility

    @model_validator(mode="after")
    def validate_cell_type_fields(self) -> "ArchetypeSchema":
        """Validate that required fields are present based on cell type."""
        cell_type = self.metadata.cell_type.lower()

        if cell_type == "cylindrical":
            if self.geometry.external.diameter_mm is None:
                raise ValueError("Cylindrical cells must have diameter_mm")
        elif cell_type in ("prismatic", "prismatic (blade)"):
            ext = self.geometry.external
            if ext.length_mm is None or ext.width_mm is None:
                raise ValueError("Prismatic cells must have length_mm and width_mm")
        elif cell_type == "pouch":
            ext = self.geometry.external
            if ext.length_mm is None or ext.width_mm is None:
                raise ValueError("Pouch cells must have length_mm and width_mm")

        return self

    def get_cell_type_normalized(self) -> str:
        """Get normalized cell type string.

        Returns:
            One of: "cylindrical", "prismatic", "pouch"
        """
        cell_type = self.metadata.cell_type.lower()
        if "cylindrical" in cell_type:
            return "cylindrical"
        elif "prismatic" in cell_type or "blade" in cell_type:
            return "prismatic"
        elif "pouch" in cell_type:
            return "pouch"
        return cell_type

    def get_chemistry(self) -> str:
        """Get the cathode chemistry, normalized.

        Returns:
            Normalized chemistry string (e.g., "NMC811", "LFP")
        """
        chemistry = self.metadata.chemistry.cathode
        # Normalize NCM to NMC
        return chemistry.upper().replace("NCM", "NMC")

    def get_separator_thickness_um(self) -> float | None:
        """Get separator thickness, handling various field locations.

        Returns:
            Separator thickness in um, or None if not available
        """
        sep = self.electrode_stack.separator
        if sep.thickness_um is not None:
            return sep.thickness_um
        if sep.total_thickness_um is not None:
            return sep.total_thickness_um
        return None

    def get_num_electrode_pairs(self) -> int | None:
        """Get number of electrode pairs for stacked cells.

        Returns:
            Number of electrode pairs (cathode layers), or None if not available
        """
        stack = self.electrode_stack
        if stack.layer_count is not None:
            return stack.layer_count.cathode_layers
        if stack.layer_count_estimate is not None:
            return stack.layer_count_estimate
        return None

    def get_num_winds(self) -> int | None:
        """Get number of winding turns for wound cells.

        Returns:
            Number of turns, or None if not available
        """
        stack = self.electrode_stack
        if stack.winding_turns is not None:
            return stack.winding_turns
        if stack.winding_turns_estimate is not None:
            return stack.winding_turns_estimate
        return None
