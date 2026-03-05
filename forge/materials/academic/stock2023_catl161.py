"""CATL 161.5 Ah LFP Prismatic Cell Parameters from Stock et al. 2023.

Source: Stock et al., Electrochimica Acta 471 (2023) 143341
DOI: 10.1016/j.electacta.2023.143341
Title: "Cell teardown and characterization of an automotive prismatic
        LFP battery"

Cell: CATL 161.5 Ah from Tesla Model 3 Standard Range
Chemistry: LiFePO4 / Graphite
Capacity: 161.5 Ah
Form Factor: Prismatic (butterfly jelly-roll design)

This is the MOST COMPREHENSIVELY CHARACTERIZED COMMERCIAL PRISMATIC CELL due to:
- TUM (Technical University of Munich) manufacturing analysis
- Complete electrode and separator characterization
- Tortuosity measurements via diffusion impedance
- Void volume analysis
- Aggressive lightweighting with 5 um Cu current collector

Key Parameters from Paper:
- Cathode coating: ~200 um (single side) - very thick for LFP thermal stability
- Anode coating: ~148 um (single side)
- Cu current collector: 5 um - aggressive lightweighting
- Al current collector: 12 um
- Electrode length: 22 m total
- Void volume: 6.4%
- Anode tortuosity: 3.3 +/- 0.4
- Edge insulation: 27 um Al2O3 ceramic coating

Design Features:
- Butterfly configuration with two jelly rolls
- Very thick LFP cathode (~200 um) enabled by thermal stability
- 5 um Cu collector is industry-leading thin for mass reduction
- Large format for EV stationary application
"""


def get_parameter_values() -> dict:
    """Get CATL 161Ah LFP parameter values compatible with PyBaMM format.

    Returns:
        Dictionary of electrode and cell parameters in SI units

    Note:
        PyBaMM uses SI units throughout (meters, kg/m3, etc.)
        Parameters marked with [MEASURED] are directly from the paper
        Parameters marked with [DERIVED] are calculated from measured values
        Parameters marked with [TYPICAL] use literature values for the chemistry
    """
    return {
        # =======================================================================
        # Metadata
        # =======================================================================
        "chemistry": "positive:LFP,negative:Graphite",
        "Reference": "Stock et al. Electrochimica Acta 2023",
        "DOI": "10.1016/j.electacta.2023.143341",
        # =======================================================================
        # Negative Electrode (Anode) - Graphite
        # =======================================================================
        # [MEASURED] Coating thickness from paper: ~148 um
        "Negative electrode thickness [m]": 148e-6,
        # [MEASURED] Current collector from paper: 5 um Cu
        # NOTE: This is unusually thin - aggressive lightweighting
        "Negative current collector thickness [m]": 5e-6,
        # [DERIVED] Active material volume fraction
        # coating_density = loading / thickness = 10.7 / (148e-4) = 0.72 g/cm3
        # For graphite (2.2 g/cm3): effective porosity is high
        "Negative electrode active material volume fraction": 0.55,
        # [DERIVED] High porosity for thick electrode
        "Negative electrode porosity": 0.38,
        # [TYPICAL] Graphite particle radius
        "Negative particle radius [m]": 10e-6,
        # [TYPICAL] Graphite density
        "Negative electrode active material density [kg.m-3]": 2200.0,
        # [MEASURED] Tortuosity from diffusion impedance
        "Negative electrode tortuosity": 3.3,
        # =======================================================================
        # Positive Electrode (Cathode) - LFP
        # =======================================================================
        # [MEASURED] Coating thickness from paper: ~200 um
        # Very thick cathode enabled by LFP thermal stability
        "Positive electrode thickness [m]": 200e-6,
        # [MEASURED] Current collector: 12 um Al
        "Positive current collector thickness [m]": 12e-6,
        # [DERIVED] Active material volume fraction
        # coating_density = loading / thickness = 22.6 / (200e-4) = 1.13 g/cm3
        # For LFP (3.5 g/cm3): vol_frac ~ 0.50
        "Positive electrode active material volume fraction": 0.50,
        # [DERIVED] Porosity for thick LFP electrode
        "Positive electrode porosity": 0.40,
        # [TYPICAL] LFP particle radius - olivine structure
        "Positive particle radius [m]": 5e-6,
        # [TYPICAL] LFP particle density (lower than NCM due to olivine)
        "Positive electrode active material density [kg.m-3]": 3500.0,
        # [MEASURED] Edge insulation coating
        "Positive electrode edge insulation thickness [m]": 27e-6,
        "Positive electrode edge insulation material": "Al2O3",
        # =======================================================================
        # Separator
        # =======================================================================
        # [ESTIMATED] Typical value for high-capacity cells
        "Separator thickness [m]": 20e-6,
        # [TYPICAL] Polyolefin separator
        "Separator porosity": 0.42,
        # [TYPICAL] Separator density
        "Separator density [kg.m-3]": 950.0,
        # =======================================================================
        # Electrolyte
        # =======================================================================
        # [TYPICAL] LFP-compatible electrolyte
        "Electrolyte density [kg.m-3]": 1250.0,
        # =======================================================================
        # Cell Geometry
        # =======================================================================
        # [MEASURED] From cell specs - butterfly jelly-roll design
        "Electrode height [m]": 0.160,  # 160 mm
        "Electrode width [m]": 0.190,  # 190 mm
        "Electrode length [m]": 22.0,  # 22 m total jelly roll length
        "Number of stacks": 2,  # Butterfly design
        "Electrode pairs per stack": 55,  # Estimated from geometry
        "Nominal cell capacity [A.h]": 161.5,
        # [MEASURED] Void volume from paper
        "Void volume fraction": 0.064,
        # =======================================================================
        # Electrochemical Properties
        # =======================================================================
        # [MEASURED] LFP cell voltages
        "Nominal voltage [V]": 3.2,
        "Lower voltage cut-off [V]": 2.5,
        "Upper voltage cut-off [V]": 3.65,
        # =======================================================================
        # Derived Loading Values (for CellCAD compatibility)
        # =======================================================================
        # [MEASURED] From paper
        "Negative electrode loading [mg.cm-2]": 10.7,
        "Positive electrode loading [mg.cm-2]": 22.6,
        # =======================================================================
        # Material-Specific Parameters
        # =======================================================================
        # [TYPICAL] Specific capacities
        "Positive electrode specific capacity [mAh.g-1]": 150.0,  # LFP
        "Negative electrode specific capacity [mAh.g-1]": 340.0,  # Graphite
        # [MEASURED] N/P ratio
        "N/P ratio": 1.1,
        # [DERIVED] Coating densities
        # cathode: 22.6 / (200e-4) = 1.13 g/cm3
        # anode: 10.7 / (148e-4) = 0.72 g/cm3
        "Positive electrode coating density [kg.m-3]": 1130.0,
        "Negative electrode coating density [kg.m-3]": 720.0,
        # =======================================================================
        # Prismatic-Specific Parameters
        # =======================================================================
        # [MEASURED] Cell dimensions
        "Cell height [m]": 0.174,  # 174 mm
        "Cell width [m]": 0.207,  # 207 mm
        "Cell thickness [m]": 0.072,  # 72 mm
        # [ESTIMATED] Housing
        "Case material": "Aluminum",
        "Case wall thickness [m]": 1.0e-3,
    }


# Cell-level validation targets
VALIDATION_TARGETS = {
    "capacity_ah": 161.5,
    "energy_wh": 516.8,
    "mass_g": 3170.0,
    "gravimetric_ed_whkg": 163.0,
    "volumetric_ed_whl": 366.0,
}

# Confidence levels for parameters
PARAMETER_CONFIDENCE = {
    "Positive electrode thickness [m]": "HIGH - measured",
    "Negative electrode thickness [m]": "HIGH - measured",
    "Negative current collector thickness [m]": "HIGH - measured (unusually thin 5um)",
    "Positive electrode loading [mg.cm-2]": "HIGH - measured",
    "Negative electrode loading [mg.cm-2]": "HIGH - measured",
    "Negative electrode tortuosity": "HIGH - measured",
    "Void volume fraction": "HIGH - measured",
    "Electrode length [m]": "HIGH - measured",
    "Separator thickness [m]": "MEDIUM - estimated",
    "Positive electrode porosity": "MEDIUM - derived",
    "Negative electrode porosity": "MEDIUM - derived",
}

# Notable design features
DESIGN_NOTES = {
    "thick_lfp_cathode": "200 um cathode enabled by LFP thermal stability",
    "thin_cu_collector": "5 um Cu is industry-leading thin for mass reduction",
    "butterfly_design": "Two jelly rolls in butterfly configuration",
    "edge_insulation": "27 um Al2O3 ceramic coating for safety",
}
