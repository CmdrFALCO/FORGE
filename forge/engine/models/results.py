"""Result data models for FORGE engine.

This module defines dataclasses for calculation results including:
- CellReport: Complete cell calculation results (KPIs)
- BomItem: Single item in Bill of Materials
- BillOfMaterials: Complete BOM with percentage calculations
"""

from dataclasses import dataclass, field


@dataclass
class CellReport:
    """Complete cell calculation results.

    Contains all key performance indicators (KPIs) for a cell design.

    Attributes:
        cell_name: Design name
        cell_type: Cell type ("Pouch", "Prismatic", "Cylindrical")

        # Dimensions [mm]
        cell_height_mm: Cell external height
        cell_width_mm: Cell external width
        cell_thickness_dry_mm: Cell thickness in dry state
        cell_thickness_soc0_mm: Cell thickness at 0% SoC (after formation)
        cell_thickness_soc100_mm: Cell thickness at 100% SoC

        # Volumes [cm³]
        volume_cell_cm3: External cell volume
        volume_stack_cm3: Internal stack volume

        # Sheet counts
        cathode_sheets: Total cathode sheets in cell
        anode_sheets: Total anode sheets in cell
        separator_sheets: Total separator sheets in cell

        # Masses [g]
        cathode_coating_mass_g: Cathode active material mass
        cathode_collector_mass_g: Cathode current collector mass
        anode_coating_mass_g: Anode active material mass
        anode_collector_mass_g: Anode current collector mass
        separator_mass_g: Separator mass
        electrolyte_mass_g: Electrolyte mass
        housing_mass_g: Housing/case mass
        tabs_mass_g: Combined tab mass

        # Electrical
        capacity_ah: Cell capacity [Ah]
        nominal_voltage_v: Nominal voltage [V]

        # Energy density
        gravimetric_ed_whkg: Gravimetric energy density [Wh/kg]
        volumetric_ed_cell_whl: Volumetric energy density (cell) [Wh/L]
        volumetric_ed_stack_whl: Volumetric energy density (stack) [Wh/L]

        # Areal characteristics
        areal_capacity_mahcm2: Areal capacity [mAh/cm²]
        areal_energy_mwhcm2: Areal energy [mWh/cm²]

        # ECU (Electrochemical Unit) metrics
        ecu_thickness_um: ECU thickness (one repeating unit) [um]
        ecu_volume_cm3: Total ECU volume [cm³]
        ecu_energy_density_wh_l: ECU volumetric energy density [Wh/L]

        # Cost metrics
        total_cost_usd: Total material cost [USD]
        cost_per_kwh: Cost per kWh [$/kWh]
        cathode_material: Cathode active material name
        anode_material: Anode active material name
    """

    # Identification
    cell_name: str
    cell_type: str

    # Dimensions [mm]
    cell_height_mm: float
    cell_width_mm: float
    cell_thickness_dry_mm: float
    cell_thickness_soc0_mm: float
    cell_thickness_soc100_mm: float

    # Volumes [cm³]
    volume_cell_cm3: float
    volume_stack_cm3: float

    # Sheet counts
    cathode_sheets: int
    anode_sheets: int
    separator_sheets: int

    # Masses [g]
    cathode_coating_mass_g: float
    cathode_collector_mass_g: float
    anode_coating_mass_g: float
    anode_collector_mass_g: float
    separator_mass_g: float
    electrolyte_mass_g: float
    housing_mass_g: float
    tabs_mass_g: float

    # Electrical
    capacity_ah: float
    nominal_voltage_v: float

    # Energy density
    gravimetric_ed_whkg: float
    volumetric_ed_cell_whl: float
    volumetric_ed_stack_whl: float

    # Areal characteristics
    areal_capacity_mahcm2: float
    areal_energy_mwhcm2: float

    # ECU (Electrochemical Unit) metrics - optional with defaults for backward compatibility
    ecu_thickness_um: float = 0.0
    ecu_volume_cm3: float = 0.0
    ecu_energy_density_wh_l: float = 0.0

    # Separator compression metrics (prismatic cells only)
    # Positive = compression required, Negative = gap exists
    separator_compression_dry_pct: float = 0.0
    separator_compression_soc0_pct: float = 0.0
    separator_compression_soc100_pct: float = 0.0

    # Cost metrics - optional with defaults for backward compatibility
    total_cost_usd: float = 0.0
    cost_per_kwh: float = 0.0
    cathode_material: str = ""
    anode_material: str = ""

    @property
    def cathode_mass_g(self) -> float:
        """Total cathode mass (coating + collector) [g]."""
        return self.cathode_coating_mass_g + self.cathode_collector_mass_g

    @property
    def anode_mass_g(self) -> float:
        """Total anode mass (coating + collector) [g]."""
        return self.anode_coating_mass_g + self.anode_collector_mass_g

    @property
    def total_mass_g(self) -> float:
        """Total cell mass [g]."""
        return (
            self.cathode_mass_g
            + self.anode_mass_g
            + self.separator_mass_g
            + self.electrolyte_mass_g
            + self.housing_mass_g
            + self.tabs_mass_g
        )

    @property
    def energy_wh(self) -> float:
        """Cell energy [Wh]."""
        return self.capacity_ah * self.nominal_voltage_v

    @property
    def all_electrode_sheets(self) -> int:
        """Total electrode sheets (cathode + anode)."""
        return self.cathode_sheets + self.anode_sheets

    @property
    def efficiency_stack_pct(self) -> float:
        """Stack construction efficiency [%]."""
        if self.volume_cell_cm3 == 0:
            return 0.0
        return self.volume_stack_cm3 / self.volume_cell_cm3 * 100

    @property
    def formation_swelling_pct(self) -> float:
        """Formation swelling percentage (dry to SoC0) [%]."""
        if self.cell_thickness_dry_mm == 0:
            return 0.0
        return (
            (self.cell_thickness_soc0_mm - self.cell_thickness_dry_mm)
            / self.cell_thickness_dry_mm
            * 100
        )

    @property
    def soc_breathing_pct(self) -> float:
        """SoC breathing percentage (SoC0 to SoC100) [%]."""
        if self.cell_thickness_soc0_mm == 0:
            return 0.0
        return (
            (self.cell_thickness_soc100_mm - self.cell_thickness_soc0_mm)
            / self.cell_thickness_soc0_mm
            * 100
        )


@dataclass
class BomItem:
    """Single item in Bill of Materials.

    Attributes:
        type: Component type (e.g., "Anode Actives", "Cathode Collector")
        name: Material name
        mass_g: Component mass [g]
        volume_ml: Component volume [ml]
        cost_eur: Component cost [EUR]
        mass_pct: Percentage of total mass [%]
        volume_pct: Percentage of total volume [%]
        cost_pct: Percentage of total cost [%]
    """

    type: str
    name: str
    mass_g: float
    volume_ml: float
    cost_eur: float
    mass_pct: float = 0.0
    volume_pct: float = 0.0
    cost_pct: float = 0.0


@dataclass
class BillOfMaterials:
    """Complete Bill of Materials with automatic percentage calculations.

    Attributes:
        items: List of BOM items
        cell_name: Design name
        cell_type: Cell type
    """

    items: list[BomItem] = field(default_factory=list)
    cell_name: str = ""
    cell_type: str = ""

    @property
    def total_mass_g(self) -> float:
        """Total mass of all items [g]."""
        return sum(item.mass_g for item in self.items)

    @property
    def total_volume_ml(self) -> float:
        """Total volume of all items [ml]."""
        return sum(item.volume_ml for item in self.items)

    @property
    def total_cost_eur(self) -> float:
        """Total cost of all items [EUR]."""
        return sum(item.cost_eur for item in self.items)

    def calculate_percentages(self) -> None:
        """Calculate and update percentages for all items."""
        total_mass = self.total_mass_g
        total_volume = self.total_volume_ml
        total_cost = self.total_cost_eur

        for item in self.items:
            item.mass_pct = (item.mass_g / total_mass * 100) if total_mass > 0 else 0.0
            item.volume_pct = (item.volume_ml / total_volume * 100) if total_volume > 0 else 0.0
            item.cost_pct = (item.cost_eur / total_cost * 100) if total_cost > 0 else 0.0

    def add_item(
        self, type: str, name: str, mass_g: float, volume_ml: float, cost_eur: float
    ) -> None:
        """Add an item to the BOM.

        Args:
            type: Component type
            name: Material name
            mass_g: Component mass [g]
            volume_ml: Component volume [ml]
            cost_eur: Component cost [EUR]
        """
        self.items.append(
            BomItem(type=type, name=name, mass_g=mass_g, volume_ml=volume_ml, cost_eur=cost_eur)
        )
