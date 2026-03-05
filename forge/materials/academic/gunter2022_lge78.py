"""LG E78 Pouch Cell Parameters from Gunter & Wassiliadis 2022.

Source: Gunter & Wassiliadis, JES 169 (2022) 030515
DOI: 10.1149/1945-7111/ac4e11
Title: "Introduction to Electrochemical Impedance Spectroscopy as a Measurement
        Method for the Wetting Degree of Lithium-Ion Cells"

Cell: LG E78 from VW ID.3 production
Chemistry: NCM652015 (Ni65 Co20 Mn15) / Graphite
Capacity: 78 Ah
Form Factor: Pouch

This is considered the GOLD STANDARD for pouch cell validation due to:
- Complete electrode teardown with SEM, EDX, ICP-AES analysis
- Mercury porosimetry for porosity characterization
- Detailed electrode dimensions and composition
- Open-access publication with full methodology

Key Parameters from Paper:
- Cathode coating: 87.3 +/- 2.7 um (single side)
- Anode coating: 115.3 +/- 3.5 um (single side)
- Cathode loading: 27.9 mg/cm2
- Anode loading: 18.1 mg/cm2
- Separator: 17.6 +/- 2.1 um
- N/P ratio: 1.04
- Active material mass fraction: 0.757
- Active material volume fraction: 0.816
- Cathode particle distribution: bimodal (3 um, 9.5 um)
"""


def get_parameter_values() -> dict:
    """Get LG E78 parameter values compatible with PyBaMM format.

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
        "chemistry": "positive:NCM652015,negative:Graphite",
        "Reference": "Gunter & Wassiliadis JES 2022",
        "DOI": "10.1149/1945-7111/ac4e11",
        # =======================================================================
        # Negative Electrode (Anode) - Graphite
        # =======================================================================
        # [MEASURED] Coating thickness from paper Table 1: 115.3 +/- 3.5 um
        "Negative electrode thickness [m]": 115.3e-6,
        # [MEASURED] Current collector from paper: 12 um Cu foil
        "Negative current collector thickness [m]": 12e-6,
        # [DERIVED] Active material volume fraction
        # Paper gives mass fraction but volume fraction estimated from coating density
        # coating_density = loading / thickness = 18.1 / (115.3e-4) = 1.57 g/cm3
        # For graphite (2.2 g/cm3): vol_frac = 1.57 / 2.2 * 0.95 (binder factor) ~ 0.68
        "Negative electrode active material volume fraction": 0.68,
        # [DERIVED] Porosity from mercury porosimetry analog
        # Estimated from typical graphite electrodes
        "Negative electrode porosity": 0.30,
        # [TYPICAL] Graphite particle radius - typical value
        "Negative particle radius [m]": 8e-6,
        # [TYPICAL] Graphite particle density
        "Negative electrode active material density [kg.m-3]": 2200.0,
        # [MEASURED] N/P ratio 1.04 means anode has 4% excess capacity
        "Negative electrode areal capacity [mAh.cm-2]": 5.23,
        # =======================================================================
        # Positive Electrode (Cathode) - NCM652015
        # =======================================================================
        # [MEASURED] Coating thickness from paper Table 1: 87.3 +/- 2.7 um
        "Positive electrode thickness [m]": 87.3e-6,
        # [MEASURED] Current collector from paper: 14 um Al foil
        "Positive current collector thickness [m]": 14e-6,
        # [MEASURED] Active material volume fraction from paper: 0.816
        "Positive electrode active material volume fraction": 0.816,
        # [DERIVED] Porosity = 1 - active_vol_frac - inactive_vol_frac
        # Assuming ~5% inactive (binder + conductive additive)
        "Positive electrode porosity": 0.134,
        # [MEASURED] Cathode has bimodal particle distribution: 3 um and 9.5 um
        # Using average weighted by typical distribution
        "Positive particle radius [m]": 6.25e-6,  # Average of bimodal
        # [TYPICAL] NCM particle density
        "Positive electrode active material density [kg.m-3]": 4700.0,
        # [MEASURED] Areal capacity from paper
        "Positive electrode areal capacity [mAh.cm-2]": 5.02,
        # =======================================================================
        # Separator
        # =======================================================================
        # [MEASURED] Separator thickness from paper: 17.6 +/- 2.1 um
        "Separator thickness [m]": 17.6e-6,
        # [TYPICAL] Polyolefin separator porosity
        "Separator porosity": 0.42,
        # [TYPICAL] PE/PP separator density
        "Separator density [kg.m-3]": 950.0,
        # =======================================================================
        # Electrolyte
        # =======================================================================
        # [TYPICAL] LiPF6 in EC:EMC:DMC
        "Electrolyte density [kg.m-3]": 1220.0,
        # =======================================================================
        # Cell Geometry
        # =======================================================================
        # [MEASURED] From cell dimensions
        "Electrode height [m]": 0.570,  # 570 mm cathode height
        "Electrode width [m]": 0.095,  # 95 mm cathode width
        "Number of electrode pairs": 52,
        "Nominal cell capacity [A.h]": 78.0,
        # =======================================================================
        # Electrochemical Properties
        # =======================================================================
        # [MEASURED] From cell specs
        "Nominal voltage [V]": 3.68,
        "Lower voltage cut-off [V]": 2.5,
        "Upper voltage cut-off [V]": 4.2,
        # =======================================================================
        # Derived Loading Values (for CellCAD compatibility)
        # =======================================================================
        # [MEASURED] From paper
        "Negative electrode loading [mg.cm-2]": 18.1,
        "Positive electrode loading [mg.cm-2]": 27.9,
        # =======================================================================
        # Material-Specific Parameters
        # =======================================================================
        # [MEASURED] Active material mass fraction
        "Positive electrode active material mass fraction": 0.757,
        # [TYPICAL] Specific capacities
        "Positive electrode specific capacity [mAh.g-1]": 180.0,  # NCM652015
        "Negative electrode specific capacity [mAh.g-1]": 350.0,  # Graphite
        # [DERIVED] Coating densities
        # cathode: 27.9 / (87.3e-4) = 3.20 g/cm3
        # anode: 18.1 / (115.3e-4) = 1.57 g/cm3
        "Positive electrode coating density [kg.m-3]": 3200.0,
        "Negative electrode coating density [kg.m-3]": 1570.0,
    }


# Cell-level validation targets
VALIDATION_TARGETS = {
    "capacity_ah": 78.0,
    "energy_wh": 287.0,
    "mass_g": 1080.0,
    "gravimetric_ed_whkg": 268.0,
    "volumetric_ed_whl": 629.0,
}

# Confidence levels for parameters
PARAMETER_CONFIDENCE = {
    "Positive electrode thickness [m]": "HIGH - measured",
    "Negative electrode thickness [m]": "HIGH - measured",
    "Separator thickness [m]": "HIGH - measured",
    "Positive electrode active material volume fraction": "HIGH - measured",
    "Positive electrode loading [mg.cm-2]": "HIGH - measured",
    "Negative electrode loading [mg.cm-2]": "HIGH - measured",
    "Negative electrode active material volume fraction": "MEDIUM - derived",
    "Positive electrode porosity": "MEDIUM - derived",
    "Negative electrode porosity": "MEDIUM - typical",
}
