"""
Tests for CellCAD material cost estimation module.

This module tests:
- Material cost database lookups
- Cost calculation from CellReport
- Cost per kWh calculations
- BOM generation with real costs
"""

import pytest

from forge.engine.cost.cost import (
    CellCostReport,
    ComponentCost,
    calculate_cell_cost,
    calculate_cost_per_kwh,
    enrich_report_with_cost,
    format_cost_report,
)
from forge.engine.cost.material_costs import (
    ANODE_COSTS,
    CATHODE_COSTS,
    ELECTROLYTE_COSTS,
    HOUSING_COSTS,
    SEPARATOR_COSTS,
    TAB_COSTS,
    MaterialCost,
    get_anode_cost,
    get_cathode_cost,
    get_electrolyte_cost,
    get_housing_cost,
    get_material_cost_summary,
    get_separator_cost,
    get_tab_cost,
)
from forge.engine.models.results import CellReport
from forge.export.csv_export import generate_bom_with_real_costs

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_cell_report():
    """Create a sample CellReport for testing."""
    return CellReport(
        cell_name="Test Cell",
        cell_type="Prismatic",
        cell_height_mm=100.0,
        cell_width_mm=200.0,
        cell_thickness_dry_mm=30.0,
        cell_thickness_soc0_mm=30.5,
        cell_thickness_soc100_mm=31.0,
        volume_cell_cm3=600.0,
        volume_stack_cm3=500.0,
        cathode_sheets=50,
        anode_sheets=51,
        separator_sheets=100,
        cathode_coating_mass_g=500.0,
        cathode_collector_mass_g=50.0,
        anode_coating_mass_g=300.0,
        anode_collector_mass_g=100.0,
        separator_mass_g=40.0,
        electrolyte_mass_g=150.0,
        housing_mass_g=200.0,
        tabs_mass_g=20.0,
        capacity_ah=100.0,
        nominal_voltage_v=3.7,
        gravimetric_ed_whkg=250.0,
        volumetric_ed_cell_whl=500.0,
        volumetric_ed_stack_whl=600.0,
        areal_capacity_mahcm2=5.0,
        areal_energy_mwhcm2=18.5,
    )


@pytest.fixture
def pouch_cell_report():
    """Create a sample pouch cell report for testing."""
    return CellReport(
        cell_name="Pouch Test Cell",
        cell_type="Pouch",
        cell_height_mm=150.0,
        cell_width_mm=100.0,
        cell_thickness_dry_mm=10.0,
        cell_thickness_soc0_mm=10.5,
        cell_thickness_soc100_mm=11.0,
        volume_cell_cm3=150.0,
        volume_stack_cm3=130.0,
        cathode_sheets=30,
        anode_sheets=31,
        separator_sheets=60,
        cathode_coating_mass_g=200.0,
        cathode_collector_mass_g=20.0,
        anode_coating_mass_g=120.0,
        anode_collector_mass_g=40.0,
        separator_mass_g=15.0,
        electrolyte_mass_g=60.0,
        housing_mass_g=10.0,
        tabs_mass_g=5.0,
        capacity_ah=50.0,
        nominal_voltage_v=3.7,
        gravimetric_ed_whkg=220.0,
        volumetric_ed_cell_whl=450.0,
        volumetric_ed_stack_whl=550.0,
        areal_capacity_mahcm2=4.5,
        areal_energy_mwhcm2=16.5,
    )


@pytest.fixture
def cylindrical_cell_report():
    """Create a sample cylindrical cell report for testing."""
    return CellReport(
        cell_name="21700 Test Cell",
        cell_type="Cylindrical",
        cell_height_mm=70.0,
        cell_width_mm=21.0,
        cell_thickness_dry_mm=21.0,
        cell_thickness_soc0_mm=21.0,
        cell_thickness_soc100_mm=21.0,
        volume_cell_cm3=24.0,
        volume_stack_cm3=20.0,
        cathode_sheets=1,
        anode_sheets=1,
        separator_sheets=2,
        cathode_coating_mass_g=25.0,
        cathode_collector_mass_g=3.0,
        anode_coating_mass_g=15.0,
        anode_collector_mass_g=5.0,
        separator_mass_g=2.0,
        electrolyte_mass_g=8.0,
        housing_mass_g=10.0,
        tabs_mass_g=1.0,
        capacity_ah=5.0,
        nominal_voltage_v=3.6,
        gravimetric_ed_whkg=260.0,
        volumetric_ed_cell_whl=650.0,
        volumetric_ed_stack_whl=750.0,
        areal_capacity_mahcm2=5.5,
        areal_energy_mwhcm2=20.0,
    )


# =============================================================================
# MATERIAL COST DATABASE TESTS
# =============================================================================


class TestMaterialCostDatabase:
    """Tests for material cost database."""

    def test_cathode_costs_exist(self):
        """Verify cathode cost database has entries."""
        assert len(CATHODE_COSTS) > 0
        assert "NMC811" in CATHODE_COSTS
        assert "LFP" in CATHODE_COSTS
        assert "NCA" in CATHODE_COSTS

    def test_anode_costs_exist(self):
        """Verify anode cost database has entries."""
        assert len(ANODE_COSTS) > 0
        assert "Graphite" in ANODE_COSTS
        assert "LTO" in ANODE_COSTS

    def test_separator_costs_exist(self):
        """Verify separator cost database has entries."""
        assert len(SEPARATOR_COSTS) > 0
        assert "Ceramic_Coated" in SEPARATOR_COSTS

    def test_electrolyte_costs_exist(self):
        """Verify electrolyte cost database has entries."""
        assert len(ELECTROLYTE_COSTS) > 0
        assert "LiPF6_Carbonate" in ELECTROLYTE_COSTS

    def test_housing_costs_exist(self):
        """Verify housing cost database has entries."""
        assert len(HOUSING_COSTS) > 0
        assert "Prismatic_Case" in HOUSING_COSTS
        assert "Aluminum_Laminate" in HOUSING_COSTS
        assert "Steel_Can" in HOUSING_COSTS

    def test_tab_costs_exist(self):
        """Verify tab cost database has entries."""
        assert len(TAB_COSTS) > 0
        assert "Aluminum_Tab" in TAB_COSTS
        assert "Nickel_Tab" in TAB_COSTS

    def test_material_cost_dataclass(self):
        """Test MaterialCost dataclass structure."""
        cost = CATHODE_COSTS["NMC811"]
        assert isinstance(cost, MaterialCost)
        assert cost.price_per_kg > 0
        assert cost.unit == "$/kg"
        assert isinstance(cost.year, int)

    def test_nmc_price_increases_with_nickel(self):
        """Verify NMC prices scale with nickel content."""
        nmc111 = CATHODE_COSTS["NMC111"].price_per_kg
        nmc622 = CATHODE_COSTS["NMC622"].price_per_kg
        nmc811 = CATHODE_COSTS["NMC811"].price_per_kg

        assert nmc111 < nmc622 < nmc811

    def test_lfp_cheaper_than_nmc(self):
        """LFP should be cheaper than NMC variants."""
        lfp_cost = CATHODE_COSTS["LFP"].price_per_kg
        nmc811_cost = CATHODE_COSTS["NMC811"].price_per_kg

        assert lfp_cost < nmc811_cost


class TestCostHelperFunctions:
    """Tests for cost lookup helper functions."""

    def test_get_cathode_cost_direct_lookup(self):
        """Test direct cathode cost lookup."""
        cost = get_cathode_cost("NMC811")
        assert cost == CATHODE_COSTS["NMC811"].price_per_kg

    def test_get_cathode_cost_case_insensitive(self):
        """Test case-insensitive cathode lookup."""
        cost_upper = get_cathode_cost("NMC811")
        cost_lower = get_cathode_cost("nmc811")
        assert cost_upper == cost_lower

    def test_get_cathode_cost_fallback(self):
        """Test fallback for unknown cathode material."""
        cost = get_cathode_cost("Unknown_Material")
        assert cost == 25.0  # Default fallback

    def test_get_anode_cost_direct_lookup(self):
        """Test direct anode cost lookup."""
        cost = get_anode_cost("Graphite")
        assert cost == ANODE_COSTS["Graphite"].price_per_kg

    def test_get_anode_cost_graphite_substring(self):
        """Test graphite detection by substring."""
        cost = get_anode_cost("synthetic_graphite")
        assert cost == ANODE_COSTS["Graphite"].price_per_kg

    def test_get_separator_cost(self):
        """Test separator cost lookup."""
        cost = get_separator_cost("Ceramic_Coated")
        assert cost == SEPARATOR_COSTS["Ceramic_Coated"].price_per_kg

    def test_get_electrolyte_cost(self):
        """Test electrolyte cost lookup."""
        cost = get_electrolyte_cost("LiPF6_Carbonate")
        assert cost == ELECTROLYTE_COSTS["LiPF6_Carbonate"].price_per_kg

    def test_get_housing_cost_by_type(self):
        """Test housing cost lookup by housing type."""
        cost = get_housing_cost("Prismatic_Case", "prismatic")
        assert cost == HOUSING_COSTS["Prismatic_Case"].price_per_kg

    def test_get_housing_cost_default_by_cell_type(self):
        """Test housing cost default by cell type."""
        cost_prismatic = get_housing_cost("unknown", "prismatic")
        cost_pouch = get_housing_cost("unknown", "pouch")
        cost_cylindrical = get_housing_cost("unknown", "cylindrical")

        assert cost_prismatic == 5.0
        assert cost_pouch == 8.0
        assert cost_cylindrical == 3.5

    def test_get_tab_cost_aluminum(self):
        """Test aluminum tab cost lookup."""
        cost = get_tab_cost("Aluminum_Tab")
        assert cost == TAB_COSTS["Aluminum_Tab"].price_per_kg

    def test_get_tab_cost_infer_from_name(self):
        """Test tab cost inference from material name."""
        cost_al = get_tab_cost("aluminum_tab_custom")
        cost_ni = get_tab_cost("nickel_custom_tab")
        cost_cu = get_tab_cost("copper_heavy_tab")

        assert cost_al == TAB_COSTS["Aluminum_Tab"].price_per_kg
        assert cost_ni == TAB_COSTS["Nickel_Tab"].price_per_kg
        assert cost_cu == TAB_COSTS["Copper_Tab"].price_per_kg

    def test_get_material_cost_summary(self):
        """Test material cost summary generation."""
        summary = get_material_cost_summary()

        assert "cathode" in summary
        assert "anode" in summary
        assert "separator" in summary
        assert "electrolyte" in summary
        assert "housing" in summary
        assert "tab" in summary
        assert "other" in summary

        # Verify structure
        assert "NMC811" in summary["cathode"]
        assert summary["cathode"]["NMC811"] > 0


# =============================================================================
# COST CALCULATION TESTS
# =============================================================================


class TestCostCalculation:
    """Tests for cost calculation functions."""

    def test_calculate_cell_cost_returns_report(self, sample_cell_report):
        """Test that calculate_cell_cost returns CellCostReport."""
        cost_report = calculate_cell_cost(sample_cell_report)

        assert isinstance(cost_report, CellCostReport)
        assert cost_report.cell_name == "Test Cell"
        assert cost_report.cell_type == "Prismatic"

    def test_calculate_cell_cost_has_components(self, sample_cell_report):
        """Test that cost report has component breakdown."""
        cost_report = calculate_cell_cost(sample_cell_report)

        assert len(cost_report.component_costs) > 0

        # Check expected components exist
        component_names = [c.component for c in cost_report.component_costs]
        assert "Cathode Active Material" in component_names
        assert "Anode Active Material" in component_names
        assert "Separator" in component_names
        assert "Electrolyte" in component_names
        assert "Housing" in component_names

    def test_calculate_cell_cost_total(self, sample_cell_report):
        """Test total cost calculation."""
        cost_report = calculate_cell_cost(sample_cell_report)

        assert cost_report.total_cost_usd > 0

        # Total should equal sum of components
        expected_total = sum(c.cost_usd for c in cost_report.component_costs)
        assert abs(cost_report.total_cost_usd - expected_total) < 0.001

    def test_calculate_cell_cost_energy(self, sample_cell_report):
        """Test energy field in cost report."""
        cost_report = calculate_cell_cost(sample_cell_report)

        expected_energy = 100.0 * 3.7  # 370 Wh
        assert abs(cost_report.energy_wh - expected_energy) < 0.1

    def test_cost_per_kwh_property(self, sample_cell_report):
        """Test cost per kWh calculation."""
        cost_report = calculate_cell_cost(sample_cell_report)

        # cost_per_kwh = (total_cost / energy_wh) * 1000
        expected_cost_per_kwh = (cost_report.total_cost_usd / cost_report.energy_wh) * 1000
        assert abs(cost_report.cost_per_kwh - expected_cost_per_kwh) < 0.1

    def test_cost_per_kwh_zero_energy(self):
        """Test cost per kWh when energy is zero."""
        cost_report = CellCostReport(
            cell_name="Zero Energy",
            cell_type="Test",
            energy_wh=0.0,
            total_cost_usd=10.0,
        )

        assert cost_report.cost_per_kwh == 0.0

    def test_different_cathode_materials(self, sample_cell_report):
        """Test cost varies with cathode material."""
        cost_nmc811 = calculate_cell_cost(sample_cell_report, cathode_material="NMC811")
        cost_lfp = calculate_cell_cost(sample_cell_report, cathode_material="LFP")

        # LFP should be cheaper
        assert cost_lfp.total_cost_usd < cost_nmc811.total_cost_usd

    def test_different_anode_materials(self, sample_cell_report):
        """Test cost varies with anode material."""
        cost_graphite = calculate_cell_cost(sample_cell_report, anode_material="Graphite")
        cost_silicon = calculate_cell_cost(sample_cell_report, anode_material="Silicon_Graphite_20")

        # Silicon-enhanced should be more expensive
        assert cost_silicon.total_cost_usd > cost_graphite.total_cost_usd

    def test_calculate_cost_per_kwh_convenience(self, sample_cell_report):
        """Test convenience function for cost per kWh."""
        cost_per_kwh = calculate_cost_per_kwh(sample_cell_report)

        full_report = calculate_cell_cost(sample_cell_report)
        assert abs(cost_per_kwh - full_report.cost_per_kwh) < 0.01


class TestCostReportMethods:
    """Tests for CellCostReport methods."""

    def test_get_component_breakdown(self, sample_cell_report):
        """Test component breakdown dictionary."""
        cost_report = calculate_cell_cost(sample_cell_report)
        breakdown = cost_report.get_component_breakdown()

        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0
        assert all(isinstance(v, float) for v in breakdown.values())

    def test_get_percentage_breakdown(self, sample_cell_report):
        """Test percentage breakdown calculation."""
        cost_report = calculate_cell_cost(sample_cell_report)
        pct_breakdown = cost_report.get_percentage_breakdown()

        # Percentages should sum to ~100%
        total_pct = sum(pct_breakdown.values())
        assert abs(total_pct - 100.0) < 0.1

    def test_percentage_breakdown_zero_cost(self):
        """Test percentage breakdown when total cost is zero."""
        cost_report = CellCostReport(
            cell_name="Zero Cost",
            cell_type="Test",
            total_cost_usd=0.0,
        )

        pct_breakdown = cost_report.get_percentage_breakdown()
        assert all(v == 0.0 for v in pct_breakdown.values())


class TestEnrichReportWithCost:
    """Tests for enrich_report_with_cost function."""

    def test_enrich_adds_cost_fields(self, sample_cell_report):
        """Test that enrich adds cost fields to report."""
        # Before enrichment
        assert sample_cell_report.total_cost_usd == 0.0
        assert sample_cell_report.cost_per_kwh == 0.0

        # Enrich
        enrich_report_with_cost(sample_cell_report, cathode_material="NMC811")

        # After enrichment
        assert sample_cell_report.total_cost_usd > 0
        assert sample_cell_report.cost_per_kwh > 0
        assert sample_cell_report.cathode_material == "NMC811"
        assert sample_cell_report.anode_material == "Graphite"

    def test_enrich_returns_same_report(self, sample_cell_report):
        """Test that enrich returns the same report object."""
        result = enrich_report_with_cost(sample_cell_report)
        assert result is sample_cell_report


class TestFormatCostReport:
    """Tests for cost report formatting."""

    def test_format_produces_string(self, sample_cell_report):
        """Test that format produces a string."""
        cost_report = calculate_cell_cost(sample_cell_report)
        formatted = format_cost_report(cost_report)

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_includes_cell_name(self, sample_cell_report):
        """Test that format includes cell name."""
        cost_report = calculate_cell_cost(sample_cell_report)
        formatted = format_cost_report(cost_report)

        assert sample_cell_report.cell_name in formatted

    def test_format_includes_cost_per_kwh(self, sample_cell_report):
        """Test that format includes cost per kWh."""
        cost_report = calculate_cell_cost(sample_cell_report)
        formatted = format_cost_report(cost_report)

        assert "/kWh" in formatted
        assert "Cost per kWh" in formatted


# =============================================================================
# BOM WITH REAL COSTS TESTS
# =============================================================================


class TestBOMWithRealCosts:
    """Tests for BOM generation with real costs."""

    def test_generate_bom_returns_bill_of_materials(self, sample_cell_report):
        """Test that generate_bom_with_real_costs returns BillOfMaterials."""
        from forge.engine.models.results import BillOfMaterials

        bom = generate_bom_with_real_costs(sample_cell_report)

        assert isinstance(bom, BillOfMaterials)
        assert bom.cell_name == "Test Cell"
        assert bom.cell_type == "Prismatic"

    def test_generate_bom_has_items(self, sample_cell_report):
        """Test that BOM has items."""
        bom = generate_bom_with_real_costs(sample_cell_report)

        assert len(bom.items) > 0

    def test_generate_bom_has_expected_components(self, sample_cell_report):
        """Test that BOM has expected component types."""
        bom = generate_bom_with_real_costs(sample_cell_report)

        item_types = [item.type for item in bom.items]

        assert "Cathode Actives" in item_types
        assert "Cathode Collector" in item_types
        assert "Anode Actives" in item_types
        assert "Anode Collector" in item_types
        assert "Separator" in item_types
        assert "Electrolyte" in item_types
        assert "Housing" in item_types

    def test_generate_bom_has_tabs_when_present(self, sample_cell_report):
        """Test that BOM includes tabs when present in report."""
        bom = generate_bom_with_real_costs(sample_cell_report)

        item_types = [item.type for item in bom.items]

        assert "Cathode Tab" in item_types
        assert "Anode Tab" in item_types

    def test_generate_bom_percentages_sum_to_100(self, sample_cell_report):
        """Test that BOM percentages sum to 100%."""
        bom = generate_bom_with_real_costs(sample_cell_report)

        mass_pct_total = sum(item.mass_pct for item in bom.items)
        cost_pct_total = sum(item.cost_pct for item in bom.items)

        assert abs(mass_pct_total - 100.0) < 0.1
        assert abs(cost_pct_total - 100.0) < 0.1

    def test_generate_bom_auto_detects_housing_type(self, pouch_cell_report):
        """Test housing type auto-detection for pouch cell."""
        bom = generate_bom_with_real_costs(pouch_cell_report)

        housing_item = next(item for item in bom.items if item.type == "Housing")
        assert housing_item.name == "Aluminum_Laminate"

    def test_generate_bom_cylindrical_housing(self, cylindrical_cell_report):
        """Test housing type auto-detection for cylindrical cell."""
        bom = generate_bom_with_real_costs(cylindrical_cell_report)

        housing_item = next(item for item in bom.items if item.type == "Housing")
        assert housing_item.name == "Steel_Can"


# =============================================================================
# CELL TYPE SPECIFIC TESTS
# =============================================================================


class TestPouchCellCosts:
    """Tests specific to pouch cell cost calculations."""

    def test_pouch_cell_cost_calculation(self, pouch_cell_report):
        """Test cost calculation for pouch cell."""
        cost_report = calculate_cell_cost(pouch_cell_report)

        assert cost_report.total_cost_usd > 0
        assert cost_report.cost_per_kwh > 0

    def test_pouch_cell_housing_uses_laminate_cost(self, pouch_cell_report):
        """Test pouch cell uses laminate housing cost."""
        cost_report = calculate_cell_cost(pouch_cell_report)

        housing_component = next(c for c in cost_report.component_costs if c.component == "Housing")
        assert housing_component.material == "Aluminum_Laminate"


class TestCylindricalCellCosts:
    """Tests specific to cylindrical cell cost calculations."""

    def test_cylindrical_cell_cost_calculation(self, cylindrical_cell_report):
        """Test cost calculation for cylindrical cell."""
        cost_report = calculate_cell_cost(cylindrical_cell_report)

        assert cost_report.total_cost_usd > 0
        assert cost_report.cost_per_kwh > 0

    def test_cylindrical_cell_housing_uses_steel_cost(self, cylindrical_cell_report):
        """Test cylindrical cell uses steel housing cost."""
        cost_report = calculate_cell_cost(cylindrical_cell_report)

        housing_component = next(c for c in cost_report.component_costs if c.component == "Housing")
        assert housing_component.material == "Steel_Can"


class TestPrismaticCellCosts:
    """Tests specific to prismatic cell cost calculations."""

    def test_prismatic_cell_cost_calculation(self, sample_cell_report):
        """Test cost calculation for prismatic cell."""
        cost_report = calculate_cell_cost(sample_cell_report)

        assert cost_report.total_cost_usd > 0
        assert cost_report.cost_per_kwh > 0

    def test_prismatic_cell_housing_uses_case_cost(self, sample_cell_report):
        """Test prismatic cell uses case housing cost."""
        cost_report = calculate_cell_cost(sample_cell_report)

        housing_component = next(c for c in cost_report.component_costs if c.component == "Housing")
        assert housing_component.material == "Prismatic_Case"


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_zero_mass_components(self):
        """Test handling of zero mass components."""
        report = CellReport(
            cell_name="Zero Mass Test",
            cell_type="Test",
            cell_height_mm=100.0,
            cell_width_mm=100.0,
            cell_thickness_dry_mm=10.0,
            cell_thickness_soc0_mm=10.0,
            cell_thickness_soc100_mm=10.0,
            volume_cell_cm3=100.0,
            volume_stack_cm3=90.0,
            cathode_sheets=1,
            anode_sheets=1,
            separator_sheets=2,
            cathode_coating_mass_g=0.0,  # Zero
            cathode_collector_mass_g=0.0,  # Zero
            anode_coating_mass_g=0.0,  # Zero
            anode_collector_mass_g=0.0,  # Zero
            separator_mass_g=0.0,  # Zero
            electrolyte_mass_g=0.0,  # Zero
            housing_mass_g=0.0,  # Zero
            tabs_mass_g=0.0,  # Zero
            capacity_ah=1.0,
            nominal_voltage_v=3.7,
            gravimetric_ed_whkg=0.0,
            volumetric_ed_cell_whl=0.0,
            volumetric_ed_stack_whl=0.0,
            areal_capacity_mahcm2=0.0,
            areal_energy_mwhcm2=0.0,
        )

        cost_report = calculate_cell_cost(report)

        # Should not raise, just have zero costs
        assert cost_report.total_cost_usd == 0.0

    def test_very_large_cell(self):
        """Test handling of very large cell."""
        report = CellReport(
            cell_name="Large Cell",
            cell_type="Prismatic",
            cell_height_mm=500.0,
            cell_width_mm=1000.0,
            cell_thickness_dry_mm=100.0,
            cell_thickness_soc0_mm=100.0,
            cell_thickness_soc100_mm=100.0,
            volume_cell_cm3=50000.0,
            volume_stack_cm3=45000.0,
            cathode_sheets=500,
            anode_sheets=501,
            separator_sheets=1000,
            cathode_coating_mass_g=50000.0,  # 50 kg
            cathode_collector_mass_g=5000.0,
            anode_coating_mass_g=30000.0,
            anode_collector_mass_g=10000.0,
            separator_mass_g=4000.0,
            electrolyte_mass_g=15000.0,
            housing_mass_g=20000.0,
            tabs_mass_g=2000.0,
            capacity_ah=1000.0,
            nominal_voltage_v=3.7,
            gravimetric_ed_whkg=250.0,
            volumetric_ed_cell_whl=500.0,
            volumetric_ed_stack_whl=600.0,
            areal_capacity_mahcm2=5.0,
            areal_energy_mwhcm2=18.5,
        )

        cost_report = calculate_cell_cost(report)

        # Should handle large values
        assert cost_report.total_cost_usd > 1000  # At least $1000 for such a large cell


class TestComponentCostDataclass:
    """Tests for ComponentCost dataclass."""

    def test_component_cost_fields(self):
        """Test ComponentCost has expected fields."""
        component = ComponentCost(
            component="Test Component",
            material="Test Material",
            mass_g=100.0,
            cost_per_kg=50.0,
            cost_usd=5.0,
        )

        assert component.component == "Test Component"
        assert component.material == "Test Material"
        assert component.mass_g == 100.0
        assert component.cost_per_kg == 50.0
        assert component.cost_usd == 5.0

    def test_component_cost_per_gram_property(self):
        """Test cost_per_g property calculation."""
        component = ComponentCost(
            component="Test",
            material="Test",
            mass_g=100.0,
            cost_per_kg=50.0,
            cost_usd=5.0,
        )

        assert abs(component.cost_per_g - 0.05) < 0.001  # 50 $/kg = 0.05 $/g

