"""Default material properties and chemistry detection for YAML conversion."""

# Chemistry detection patterns - match against material name (case-insensitive)
CHEMISTRY_PATTERNS = {
    "NCA": ["nca"],
    "NCM": ["ncm", "ncm811", "ncm622", "ncm333"],
    "LFP": ["lfp", "lfo", "lifepo4"],
    "LCO": ["lco", "lco"],
    "NMC": ["nmc"],
    "LMO": ["lmo"],
    "Graphite": ["graphite"],
    "Silicon": ["silicon", "si-c"],
    "Lithium Metal": ["lithium metal", "li metal"],
}


# Cathode coating density defaults by chemistry (mg/cm2)
CATHODE_COATING_DENSITY = {
    "NCA": 2.0,
    "NCM": 1.8,
    "LFP": 0.5,
    "LCO": 2.2,
    "NMC": 1.8,
    "LMO": 1.5,
}


# Anode coating density defaults by chemistry (mg/cm2)
ANODE_COATING_DENSITY = {
    "Graphite": 1.0,
    "Silicon": 1.5,
    "Lithium Metal": 0.0,  # No coating on lithium metal
}


# Separator density defaults by type (g/cm3)
SEPARATOR_DENSITY = {
    "PE": 0.92,
    "PP": 0.90,
    "PE-PP": 0.91,
    "PE-PP-PE": 0.91,
    "Ceramic": 2.4,
    "Glass": 2.5,
}


# Max specific capacity estimates by chemistry (mAh/g)
MAX_SPECIFIC_CAPACITY = {
    "NCA": 200,
    "NCM": 190,
    "LFP": 160,
    "LCO": 140,
    "NMC": 180,
    "LMO": 100,
    "Graphite": 372,
    "Silicon": 3600,
    "Lithium Metal": 3860,
}


def detect_chemistry(material_name: str) -> str | None:
    """
    Detect chemistry type from material name using pattern matching.

    Args:
        material_name: Name of the material (e.g., "NCA", "Graphite_Anode")

    Returns:
        Chemistry type string (e.g., "NCA") or None if not recognized
    """
    if not material_name:
        return None

    name_lower = material_name.lower()

    # Check each chemistry pattern
    for chemistry, patterns in CHEMISTRY_PATTERNS.items():
        for pattern in patterns:
            if pattern in name_lower:
                return chemistry

    return None


def get_cathode_coating_density(chemistry: str | None) -> float:
    """
    Get default cathode coating density for given chemistry.

    Args:
        chemistry: Chemistry type (e.g., "NCA", "NCM")

    Returns:
        Coating density in mg/cm2, or 1.5 as default if chemistry unknown
    """
    if chemistry and chemistry in CATHODE_COATING_DENSITY:
        return CATHODE_COATING_DENSITY[chemistry]
    return 1.5  # Default fallback


def get_anode_coating_density(chemistry: str | None) -> float:
    """
    Get default anode coating density for given chemistry.

    Args:
        chemistry: Chemistry type (e.g., "Graphite", "Silicon")

    Returns:
        Coating density in mg/cm2, or 1.0 as default if chemistry unknown
    """
    if chemistry and chemistry in ANODE_COATING_DENSITY:
        return ANODE_COATING_DENSITY[chemistry]
    return 1.0  # Default fallback


def get_separator_density(separator_type: str | None) -> float:
    """
    Get default separator density for given type.

    Args:
        separator_type: Separator type (e.g., "PE-PP", "Ceramic")

    Returns:
        Density in g/cm3, or 0.91 as default if type unknown
    """
    if separator_type and separator_type in SEPARATOR_DENSITY:
        return SEPARATOR_DENSITY[separator_type]
    return 0.91  # Default PE-PP blend fallback


def get_max_specific_capacity(chemistry: str | None) -> float:
    """
    Get theoretical max specific capacity for given chemistry.

    Args:
        chemistry: Chemistry type (e.g., "NCA", "Graphite")

    Returns:
        Max specific capacity in mAh/g, or 150 as default if chemistry unknown
    """
    if chemistry and chemistry in MAX_SPECIFIC_CAPACITY:
        return MAX_SPECIFIC_CAPACITY[chemistry]
    return 150  # Default fallback
