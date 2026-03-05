"""LG MJ1 18650 Cylindrical Cell Parameters from Heenan et al. 2020.

Source: Heenan et al., JES 167 (2020) 140501
DOI: 10.1149/1945-7111/ab728d
Title: "An Advanced Microstructural and Electrochemical Datasheet on
        18650 Li-Ion Batteries with Nickel-Rich NMC811 Cathodes and
        Graphite-Silicon Anodes"

Cell: LG INR18650-MJ1
Chemistry: NMC811 / Graphite + Silicon
Capacity: 3.5 Ah
Form Factor: Cylindrical 18650

This is the BEST OPEN-SOURCE CYLINDRICAL CELL DATASET due to:
- Complete X-ray tomography data publicly available at rdr.ucl.ac.uk
- Full microstructural characterization
- Academic-quality methodology
- UCL Research Data Repository for reproducibility

Key Parameters:
- Cathode coating: ~66 um (single side)
- Anode coating: ~87 um (single side)
- NMC811 high-nickel cathode for energy density
- Silicon-doped graphite anode for capacity boost
- High energy density: 260 Wh/kg
- Power density: 965 W/kg

Open Data Repository:
- URL: https://rdr.ucl.ac.uk
- Data type: X-ray tomography
- Availability: Public (open access)
"""


def get_parameter_values() -> dict:
    """Get LG MJ1 18650 parameter values compatible with PyBaMM format.

    Returns:
        Dictionary of electrode and cell parameters in SI units

    Note:
        PyBaMM uses SI units throughout (meters, kg/m3, etc.)
        Parameters marked with [MEASURED] are directly from the paper/data
        Parameters marked with [DERIVED] are calculated from measured values
        Parameters marked with [TYPICAL] use literature values for the chemistry
    """
    return {
        # =======================================================================
        # Metadata
        # =======================================================================
        "chemistry": "positive:NMC811,negative:Graphite_Si",
        "Reference": "Heenan et al. JES 2020",
        "DOI": "10.1149/1945-7111/ab728d",
        "Open Data Repository": "rdr.ucl.ac.uk",
        # =======================================================================
        # Negative Electrode (Anode) - Graphite + Silicon
        # =======================================================================
        # [MEASURED] Coating thickness from X-ray tomography: ~87 um
        "Negative electrode thickness [m]": 87e-6,
        # [MEASURED] Current collector: ~10 um Cu
        "Negative current collector thickness [m]": 10e-6,
        # [DERIVED] Active material volume fraction from tomography
        # Silicon-doped graphite has slightly higher packing
        "Negative electrode active material volume fraction": 0.72,
        # [MEASURED] Porosity from X-ray tomography: 26%
        "Negative electrode porosity": 0.26,
        # [TYPICAL] Graphite+Si particle radius
        "Negative particle radius [m]": 8e-6,
        # [TYPICAL] Graphite+Si composite density (slightly higher than pure graphite)
        "Negative electrode active material density [kg.m-3]": 2300.0,
        # [DERIVED] Areal capacity
        "Negative electrode areal capacity [mAh.cm-2]": 4.07,  # From loading * capacity
        # =======================================================================
        # Positive Electrode (Cathode) - NMC811
        # =======================================================================
        # [MEASURED] Coating thickness from X-ray tomography: ~66 um
        "Positive electrode thickness [m]": 66e-6,
        # [MEASURED] Current collector: ~14 um Al
        "Positive current collector thickness [m]": 14e-6,
        # [DERIVED] Active material volume fraction
        "Positive electrode active material volume fraction": 0.65,
        # [MEASURED] Porosity from X-ray tomography: 30%
        "Positive electrode porosity": 0.30,
        # [TYPICAL] NMC811 particle radius
        "Positive particle radius [m]": 5e-6,
        # [TYPICAL] NMC811 particle density
        "Positive electrode active material density [kg.m-3]": 4700.0,
        # [DERIVED] Areal capacity: 3.8 mAh/cm2
        "Positive electrode areal capacity [mAh.cm-2]": 3.8,
        # =======================================================================
        # Separator
        # =======================================================================
        # [MEASURED] Separator thickness: 12 um
        "Separator thickness [m]": 12e-6,
        # [MEASURED] Separator porosity: 44%
        "Separator porosity": 0.44,
        # [TYPICAL] Polyolefin separator
        "Separator density [kg.m-3]": 940.0,
        # =======================================================================
        # Electrolyte
        # =======================================================================
        # [TYPICAL] LiPF6 in EC:EMC
        "Electrolyte density [kg.m-3]": 1200.0,
        # =======================================================================
        # Cell Geometry - Cylindrical 18650
        # =======================================================================
        "Cell diameter [m]": 18.4e-3,  # 18.4 mm
        "Cell length [m]": 65.2e-3,  # 65.2 mm
        "Mandrel diameter [m]": 2.2e-3,  # 2.2 mm inner mandrel
        "Can wall thickness [m]": 0.20e-3,  # 0.20 mm
        "Can bottom thickness [m]": 0.35e-3,  # 0.35 mm
        "Header height [m]": 2.8e-3,  # 2.8 mm
        "Nominal cell capacity [A.h]": 3.5,
        # =======================================================================
        # Electrochemical Properties
        # =======================================================================
        "Nominal voltage [V]": 3.635,
        "Lower voltage cut-off [V]": 2.5,
        "Upper voltage cut-off [V]": 4.2,
        # =======================================================================
        # Derived Loading Values (for CellCAD compatibility)
        # =======================================================================
        # [ESTIMATED] From capacity and electrode geometry
        "Negative electrode loading [mg.cm-2]": 11.0,
        "Positive electrode loading [mg.cm-2]": 20.0,
        # =======================================================================
        # Material-Specific Parameters
        # =======================================================================
        # [TYPICAL] Specific capacities
        "Positive electrode specific capacity [mAh.g-1]": 190.0,  # NMC811
        "Negative electrode specific capacity [mAh.g-1]": 370.0,  # Graphite+Si
        # [DERIVED] Coating densities
        # cathode: 20.0 / (66e-4) = 3.03 g/cm3
        # anode: 11.0 / (87e-4) = 1.26 g/cm3
        "Positive electrode coating density [kg.m-3]": 3030.0,
        "Negative electrode coating density [kg.m-3]": 1260.0,
        # =======================================================================
        # Performance Parameters
        # =======================================================================
        # [MEASURED] From datasheet and paper
        "Maximum continuous discharge current [A]": 10.0,
        "Power density [W.kg-1]": 965.0,
        "Power density volumetric [W.L-1]": 2736.0,
        "Cycle life 80% capacity": 400,
        # =======================================================================
        # Winding Parameters (Cylindrical-specific)
        # =======================================================================
        "Winding clearance [m]": 0.12e-3,  # 0.12 mm
        "Winding tension factor": 0.97,
        "Tab type": "traditional",
        "Anode tab width [m]": 5.0e-3,  # 5 mm
        "Cathode tab width [m]": 4.5e-3,  # 4.5 mm
    }


# Cell-level validation targets
VALIDATION_TARGETS = {
    "capacity_ah": 3.5,
    "energy_wh": 12.72,
    "mass_g": 49.0,
    "gravimetric_ed_whkg": 260.0,
    "volumetric_ed_whl": 730.0,
}

# Confidence levels for parameters
PARAMETER_CONFIDENCE = {
    "Positive electrode thickness [m]": "HIGH - X-ray tomography",
    "Negative electrode thickness [m]": "HIGH - X-ray tomography",
    "Separator thickness [m]": "HIGH - measured",
    "Positive electrode porosity": "HIGH - X-ray tomography",
    "Negative electrode porosity": "HIGH - X-ray tomography",
    "Separator porosity": "HIGH - measured",
    "Positive electrode loading [mg.cm-2]": "MEDIUM - estimated",
    "Negative electrode loading [mg.cm-2]": "MEDIUM - estimated",
}

# Open data information
OPEN_DATA = {
    "repository": "rdr.ucl.ac.uk",
    "data_type": "X-ray tomography",
    "availability": "public",
    "access_method": "DOI-based download",
    "note": "Full microstructural data available for validation",
}
