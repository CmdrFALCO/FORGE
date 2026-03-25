"""
Configuration data for the Stratified Prompt Corpus Generator.

Contains chemistry profiles, application profiles, prompt templates,
contradiction recipes, and flavor fragments used by generate_corpus.py.

This module is standalone — no FORGE imports.
"""

# ═══════════════════════════════════════════════════════════════
# CHEMISTRY PROFILES
# ═══════════════════════════════════════════════════════════════

CHEMISTRY_PROFILES = {
    "NMC-111": {
        "nominal_voltage": 3.7,
        "energy_density_range": (150, 220),  # Wh/kg
        "typical_capacity_range": (10, 100),  # Ah
        "max_c_rate": 2.0,
        "cathode_material": "LiNi0.33Mn0.33Co0.33O2",
        "chemistry_descriptions": [
            "a balanced nickel-manganese-cobalt chemistry",
            "a well-proven NMC cathode with equal proportions of Ni, Mn, and Co",
            "a mature oxide cathode offering a good balance of cost and performance",
        ],
    },
    "NMC-622": {
        "nominal_voltage": 3.65,
        "energy_density_range": (180, 260),  # Wh/kg
        "typical_capacity_range": (20, 120),  # Ah
        "max_c_rate": 2.5,
        "cathode_material": "LiNi0.6Mn0.2Co0.2O2",
        "chemistry_descriptions": [
            "a nickel-rich NMC with higher energy density",
            "an NMC cathode biased toward nickel for improved gravimetric performance",
            "a mid-nickel-content oxide cathode",
        ],
    },
    "NMC-811": {
        "nominal_voltage": 3.65,
        "energy_density_range": (220, 300),  # Wh/kg
        "typical_capacity_range": (30, 150),  # Ah
        "max_c_rate": 1.5,
        "cathode_material": "LiNi0.8Mn0.1Co0.1O2",
        "chemistry_descriptions": [
            "a high-nickel NMC offering best-in-class energy density",
            "an 811 cathode maximizing nickel content for range applications",
            "a high-energy-density nickel-rich oxide cathode",
        ],
    },
    "LFP": {
        "nominal_voltage": 3.2,
        "energy_density_range": (120, 180),  # Wh/kg
        "typical_capacity_range": (20, 300),  # Ah
        "max_c_rate": 3.0,
        "cathode_material": "LiFePO4",
        "chemistry_descriptions": [
            "lithium iron phosphate for long life and safety",
            "an LFP cathode optimized for cycle durability",
            "a phosphate-based chemistry known for thermal stability and longevity",
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# APPLICATION PROFILES
# ═══════════════════════════════════════════════════════════════

APPLICATION_PROFILES = {
    "ev_traction": {
        "description": "electric vehicle traction battery",
        "typical_capacity": (40, 150),  # Ah
        "energy_density_target": "high",
        "cycle_life_target": 1500,
        "temp_range": (-20, 45),
        "use_case_descriptions": [
            "a long-range electric sedan",
            "an electric SUV with 500 km range target",
            "a commercial electric delivery van",
            "a high-performance electric sports car",
            "a mid-size EV platform for a European OEM",
            "an urban electric bus with daily fast-charge cycles",
        ],
        "performance_descriptions": [
            "provide reliable range over 400 km on a single charge",
            "handle DC fast charging at up to 2C without excessive degradation",
            "maintain at least 80% capacity after 1500 full cycles",
            "deliver consistent power in both highway cruise and stop-and-go driving",
            "support regenerative braking at moderate C-rates",
        ],
        "form_descriptions": [
            "fit within a standard skateboard platform",
            "not exceed 250 kg for the full module",
            "use a form factor compatible with CTP (cell-to-pack) architecture",
            "be compact enough for a structural battery pack design",
        ],
    },
    "consumer_electronics": {
        "description": "consumer electronics battery",
        "typical_capacity": (2, 15),  # Ah
        "energy_density_target": "very_high",
        "cycle_life_target": 500,
        "temp_range": (0, 40),
        "use_case_descriptions": [
            "a premium smartphone with all-day battery life",
            "a laptop that needs to last 12 hours",
            "a tablet for professional use",
            "a portable gaming device",
            "a wireless earbud charging case",
            "a next-generation foldable phone",
        ],
        "performance_descriptions": [
            "last a full day of heavy use without recharging",
            "support fast charging from 0 to 80% in under 30 minutes",
            "retain at least 80% health after 500 charge cycles",
            "keep surface temperature below 42 degrees C during fast charge",
            "deliver stable voltage throughout the discharge curve",
        ],
        "form_descriptions": [
            "fit in a phone body under 8 mm thick",
            "weigh under 50 grams for a phone-class cell",
            "be as thin as possible for a slim laptop design",
            "conform to a non-rectangular cavity inside the device",
        ],
    },
    "grid_storage": {
        "description": "stationary grid energy storage",
        "typical_capacity": (100, 300),  # Ah
        "energy_density_target": "moderate",
        "cycle_life_target": 5000,
        "temp_range": (-10, 50),
        "use_case_descriptions": [
            "a residential solar energy storage system",
            "a commercial peak-shaving installation",
            "a grid-scale frequency regulation unit",
            "a backup power system for a data center",
            "a utility-scale renewable integration project",
            "a microgrid for an off-grid community",
        ],
        "performance_descriptions": [
            "last at least 10 years of daily cycling",
            "handle 5000+ deep discharge cycles without significant degradation",
            "operate reliably in an unconditioned outdoor enclosure",
            "deliver consistent round-trip efficiency above 92%",
            "tolerate extended float-charge periods without calendar aging issues",
        ],
        "form_descriptions": [
            "prioritize cost per kWh over weight or volume",
            "use a standard module form factor for rack mounting",
            "minimize cooling requirements for passive thermal management",
            "be designed for easy field replacement of individual cells",
        ],
    },
    "power_tools": {
        "description": "cordless power tool battery",
        "typical_capacity": (2, 10),  # Ah
        "energy_density_target": "moderate",
        "cycle_life_target": 1000,
        "temp_range": (-10, 50),
        "use_case_descriptions": [
            "a professional cordless drill",
            "an industrial-grade impact wrench",
            "a cordless circular saw",
            "a landscaping leaf blower",
            "a contractor's reciprocating saw used on job sites",
            "a heavy-duty angle grinder for metalwork",
        ],
        "performance_descriptions": [
            "deliver sustained high current draw for burst torque",
            "run a high-torque drill for at least 45 minutes continuously",
            "handle the vibration and shock of professional job site use",
            "charge from dead to full in under an hour",
            "not overheat during continuous heavy-load operation",
        ],
        "form_descriptions": [
            "keep total pack weight under 800 grams",
            "fit the standard battery bay of our existing tool platform",
            "be robust enough to survive drops from a 2-meter height",
            "use a compact form factor that doesn't unbalance the tool",
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# PROMPT TEMPLATES — TERSE
# ═══════════════════════════════════════════════════════════════

TERSE_TEMPLATES = [
    {
        "id": "terse_v1",
        "template": "Design a {capacity} Ah {chemistry} {cell_type} cell for {application}.",
    },
    {
        "id": "terse_v2",
        "template": "Specify a {chemistry} {cell_type} battery: {capacity} Ah, {application} use.",
    },
    {
        "id": "terse_v3",
        "template": "Generate parameters for a {cell_type} {chemistry} cell, {capacity} Ah, targeting {application}.",
    },
    {
        "id": "terse_v4",
        "template": "{chemistry} {cell_type}, {capacity} Ah for {application}. Full design please.",
    },
    {
        "id": "terse_v5",
        "template": "Need a {cell_type} cell: {chemistry}, around {capacity} Ah, for {application} application.",
    },
]

# ═══════════════════════════════════════════════════════════════
# PROMPT TEMPLATES — DETAILED
# ═══════════════════════════════════════════════════════════════

DETAILED_TEMPLATES = [
    {
        "id": "detailed_v1",
        "template": (
            "Design a {chemistry} {cell_type} cell with the following requirements:\n"
            "- Capacity: {capacity} Ah\n"
            "- Nominal voltage: {voltage} V\n"
            "- Target energy density: {energy_density} Wh/kg\n"
            "- Application: {application_desc}\n"
            "- Operating temperature: {temp_min} deg C to {temp_max} deg C\n"
            "- Target cycle life: {cycle_life} cycles"
        ),
    },
    {
        "id": "detailed_v2",
        "template": (
            "Please generate a complete {cell_type} cell design for {application_desc}.\n\n"
            "Key specifications:\n"
            "  Chemistry: {chemistry} ({cathode_material})\n"
            "  Cell capacity: {capacity} Ah\n"
            "  Voltage: {voltage} V nominal\n"
            "  Energy density target: {energy_density} Wh/kg\n"
            "  Temperature range: {temp_min} deg C to {temp_max} deg C\n"
            "  Cycle life requirement: {cycle_life} cycles minimum"
        ),
    },
    {
        "id": "detailed_v3",
        "template": (
            "I need a full parametric design for a {chemistry} {cell_type} battery cell.\n\n"
            "Requirements:\n"
            "* Target capacity: {capacity} Ah\n"
            "* Nominal voltage: {voltage} V\n"
            "* Energy density: at least {energy_density} Wh/kg\n"
            "* End use: {application_desc}\n"
            "* Must operate between {temp_min} deg C and {temp_max} deg C\n"
            "* Cycle life goal: {cycle_life}+"
        ),
    },
]

# ═══════════════════════════════════════════════════════════════
# PROMPT TEMPLATES — NATURAL LANGUAGE (per application)
# ═══════════════════════════════════════════════════════════════

# Each entry is a template string that uses {use_case}, {performance}, {form},
# {chemistry_mention}, and {flavor} placeholders.

NATURAL_LANGUAGE_TEMPLATES = {
    "ev_traction": [
        {
            "id": "nl_ev_v1",
            "template": (
                "We're building {use_case} and need a battery cell design.{chemistry_mention} "
                "The cell should {performance}.{form_note}{flavor}"
            ),
        },
        {
            "id": "nl_ev_v2",
            "template": (
                "Our team is working on {use_case}.{chemistry_mention} "
                "We need cells that can {performance}. {form_note}{flavor}"
            ),
        },
        {
            "id": "nl_ev_v3",
            "template": (
                "I'm looking for a battery design for {use_case}.{chemistry_mention} "
                "Key priorities: the cell must {performance}, and {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_ev_v4",
            "template": (
                "Can you help design a cell for {use_case}?{chemistry_mention} "
                "It needs to {performance}. We'd like it to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_ev_v5",
            "template": (
                "We've got a project for {use_case} and we need a complete cell spec.{chemistry_mention} "
                "The cell has to {performance}. Also, it should {form_note}.{flavor}"
            ),
        },
    ],
    "consumer_electronics": [
        {
            "id": "nl_ce_v1",
            "template": (
                "We're developing {use_case} and need a battery cell.{chemistry_mention} "
                "It should {performance}. Ideally it would {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_ce_v2",
            "template": (
                "I need a cell design for {use_case}.{chemistry_mention} "
                "Main requirement: {performance}. For form factor, it should {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_ce_v3",
            "template": (
                "Our product team needs a battery for {use_case}.{chemistry_mention} "
                "The battery must {performance}, and we need it to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_ce_v4",
            "template": (
                "Can you spec a cell for {use_case}?{chemistry_mention} "
                "It has to {performance}. Also needs to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_ce_v5",
            "template": (
                "We need a battery solution for {use_case}.{chemistry_mention} "
                "Performance-wise, it should {performance}. "
                "Size-wise, it needs to {form_note}.{flavor}"
            ),
        },
    ],
    "grid_storage": [
        {
            "id": "nl_gs_v1",
            "template": (
                "We're designing {use_case} and need cells that can {performance}.{chemistry_mention} "
                "For the installation, we want to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_gs_v2",
            "template": (
                "Our client wants {use_case}.{chemistry_mention} The cells need to {performance}. "
                "We'd prefer to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_gs_v3",
            "template": (
                "I'm working on {use_case}.{chemistry_mention} "
                "Key requirement: {performance}. The cells should {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_gs_v4",
            "template": (
                "We've been asked to source cells for {use_case}.{chemistry_mention} "
                "They have to {performance}. Cost-wise we want to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_gs_v5",
            "template": (
                "Need a cell design for {use_case}.{chemistry_mention} "
                "The deployment requires cells that {performance}, and we need to {form_note}.{flavor}"
            ),
        },
    ],
    "power_tools": [
        {
            "id": "nl_pt_v1",
            "template": (
                "We're making {use_case} and need battery cells.{chemistry_mention} "
                "They need to {performance}. Form factor should {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_pt_v2",
            "template": (
                "I need a cell design for {use_case}.{chemistry_mention} "
                "The cell must {performance}. It also has to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_pt_v3",
            "template": (
                "Our engineering team needs cells for {use_case}.{chemistry_mention} "
                "Main concern: {performance}. Additionally, {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_pt_v4",
            "template": (
                "Can you design a cell for {use_case}?{chemistry_mention} "
                "It should {performance}, and needs to {form_note}.{flavor}"
            ),
        },
        {
            "id": "nl_pt_v5",
            "template": (
                "Looking for a battery cell for {use_case}.{chemistry_mention} "
                "Priority is a cell that can {performance}. As for size, it should {form_note}.{flavor}"
            ),
        },
    ],
}

# ═══════════════════════════════════════════════════════════════
# FLAVOR FRAGMENTS (randomly inserted for variety)
# ═══════════════════════════════════════════════════════════════

FLAVOR_FRAGMENTS = [
    "",  # no flavor (most common)
    "",
    "",
    " We're on a tight timeline for this.",
    " The client is flexible on dimensions but firm on weight.",
    " Budget is not the primary concern here — performance is.",
    " This is a prototype, so cost is secondary to getting the specs right.",
    " We may iterate on this, so give us a good starting point.",
    " Safety certification is a top priority.",
    " The customer has asked for a conservative design.",
    " We need to hit a specific price point, so don't over-engineer it.",
    " This is for a Tier-1 automotive OEM, so quality standards are non-negotiable.",
    " We've already locked in the module architecture, so the cell needs to fit.",
    " Thermal management is handled at the pack level, so focus on the cell.",
    " The R&D team wants to push boundaries on this one.",
    " Our manufacturing partner has experience with this form factor.",
    " Reliability over the full warranty period is essential.",
    " We need this design finalized by end of quarter.",
]

# ═══════════════════════════════════════════════════════════════
# CHEMISTRY MENTION FRAGMENTS (for natural language ~50/50)
# ═══════════════════════════════════════════════════════════════

CHEMISTRY_MENTION_EXPLICIT = {
    "NMC-111": [
        " We're planning on NMC-111 chemistry.",
        " We've decided on NMC-111 for the cathode.",
        " Please use NMC-111.",
    ],
    "NMC-622": [
        " We're going with NMC-622.",
        " The cathode should be NMC-622.",
        " Use NMC-622 chemistry.",
    ],
    "NMC-811": [
        " We want NMC-811 for maximum energy density.",
        " Please design around NMC-811 chemistry.",
        " We've selected NMC-811.",
    ],
    "LFP": [
        " We prefer LFP for safety and longevity.",
        " Please use LFP chemistry.",
        " We want iron phosphate for this application.",
    ],
}

CHEMISTRY_MENTION_IMPLICIT = {
    "NMC-111": [
        " We want a good balance of cost, safety, and performance.",
        " A proven, cost-effective cathode chemistry would be ideal.",
        "",
    ],
    "NMC-622": [
        " We're looking for better-than-average energy density without going too aggressive.",
        " A mid-range energy density chemistry would work well.",
        "",
    ],
    "NMC-811": [
        " We need the highest energy density we can get.",
        " Gravimetric energy density is our top priority.",
        " Range is everything here — maximize energy per kilogram.",
    ],
    "LFP": [
        " Longevity and safety matter more than energy density.",
        " We want something that will last thousands of cycles.",
        " Safety and thermal stability are paramount.",
    ],
}

# ═══════════════════════════════════════════════════════════════
# CONTRADICTION RECIPES
# ═══════════════════════════════════════════════════════════════
#
# Each recipe defines:
#   - name: short description
#   - modifier: function signature (str) for how to modify params
#   - constraint_ids: list of CONSTRAINT_REGISTRY IDs expected to be violated
#   - explanation_template: human-readable explanation
#
# Constraint IDs from constraint_validator.py:
#   Common: C1 (np_ratio), C2 (cathode_loading), C3 (anode_loading),
#           C4 (separator_porosity), C5 (electrolyte_concentration),
#           C6 (cathode_material), C7 (anode_material)
#   Prismatic: PR1-PR7 (geometry, stack, electrode config)
#   Pouch: PO1-PO7 (offsets, stack, electrode config, packaging)
#   Cylindrical: CY1-CY8 (mandrel, winding, tab, geometry, housing)

CONTRADICTION_RECIPES = [
    {
        "name": "lfp_high_energy_density",
        "description": "LFP chemistry cannot achieve >200 Wh/kg at cell level",
        "applicable_chemistries": ["LFP"],
        "applicable_cell_types": None,  # any
        "param_overrides": {"energy_density_target": (210, 280)},
        "constraint_ids": ["C2", "C6"],
        "explanation_template": (
            "LFP chemistry physically cannot achieve {energy_density} Wh/kg "
            "at cell level (practical max ~180 Wh/kg). The energy density "
            "target is incompatible with the LFP cathode material limits."
        ),
    },
    {
        "name": "extreme_c_rate_with_high_energy",
        "description": "High energy density + very high C-rate is thermally impossible",
        "applicable_chemistries": ["NMC-811", "NMC-622"],
        "applicable_cell_types": None,
        "param_overrides": {
            "energy_density_target_high": True,
            "c_rate_target": (4.0, 6.0),
        },
        "constraint_ids": ["C1", "C2"],
        "explanation_template": (
            "Requesting {energy_density} Wh/kg energy density with {c_rate}C "
            "continuous discharge creates an impossible thermal management "
            "scenario. High energy density requires thick electrodes which "
            "cannot sustain high C-rates without severe degradation."
        ),
    },
    {
        "name": "tiny_form_large_capacity",
        "description": "Large capacity in a very small form factor is volumetrically impossible",
        "applicable_chemistries": None,
        "applicable_cell_types": ["pouch", "prismatic"],
        "param_overrides": {
            "capacity_ah": (80, 200),
            "form_factor_constraint": "very_small",
        },
        "constraint_ids": ["PR1", "PR3", "PO1", "PO5"],
        "explanation_template": (
            "Requesting {capacity} Ah in a very compact form factor is "
            "volumetrically impossible. The required electrode area cannot "
            "fit within the specified dimensions."
        ),
    },
    {
        "name": "max_cycle_life_max_energy",
        "description": "Maximum cycle life conflicts with maximum energy density",
        "applicable_chemistries": ["NMC-811"],
        "applicable_cell_types": None,
        "param_overrides": {
            "energy_density_target_high": True,
            "cycle_life": (8000, 12000),
        },
        "constraint_ids": ["C1", "C2"],
        "explanation_template": (
            "Targeting {energy_density} Wh/kg energy density with {cycle_life} "
            "cycle life is a fundamental tradeoff conflict. High energy density "
            "NMC-811 cathodes degrade faster due to structural instability "
            "at high states of charge."
        ),
    },
    {
        "name": "cold_temp_high_c_rate",
        "description": "Very cold operating temperature with high C-rate charging",
        "applicable_chemistries": None,
        "applicable_cell_types": None,
        "param_overrides": {
            "temp_min": -40,
            "c_rate_target": (3.0, 5.0),
        },
        "constraint_ids": ["C1", "C4"],
        "explanation_template": (
            "Operating at {temp_min} deg C with {c_rate}C charging rate is "
            "physically dangerous. At extreme cold, lithium ion diffusion "
            "slows dramatically, causing lithium plating on the anode even "
            "at moderate charge rates."
        ),
    },
    {
        "name": "cylindrical_small_diameter_large_capacity",
        "description": "Small cylindrical format with large capacity is impossible",
        "applicable_chemistries": None,
        "applicable_cell_types": ["cylindrical"],
        "param_overrides": {
            "capacity_ah": (50, 100),
            "format": "18650",
        },
        "constraint_ids": ["CY1", "CY5"],
        "explanation_template": (
            "Requesting {capacity} Ah from an 18650 cylindrical format is "
            "volumetrically impossible. Even with the highest energy density "
            "cathodes, an 18650 can hold at most ~5 Ah."
        ),
    },
    {
        "name": "low_voltage_high_energy_density",
        "description": "Very low nominal voltage with high energy density is impossible",
        "applicable_chemistries": ["NMC-111", "NMC-622", "NMC-811"],
        "applicable_cell_types": None,
        "param_overrides": {
            "voltage": (2.0, 2.5),
            "energy_density_target_high": True,
        },
        "constraint_ids": ["C1", "C6"],
        "explanation_template": (
            "Requesting {voltage} V nominal voltage with {energy_density} Wh/kg "
            "is chemically impossible. NMC cathodes inherently operate at "
            "3.6-3.7 V. A lower voltage would require a different cathode "
            "that cannot achieve the specified energy density."
        ),
    },
    {
        "name": "extreme_separator_with_high_rate",
        "description": "Very thin separator with high C-rate creates safety conflict",
        "applicable_chemistries": None,
        "applicable_cell_types": None,
        "param_overrides": {
            "separator_thickness": (3, 5),
            "c_rate_target": (4.0, 6.0),
        },
        "constraint_ids": ["C4", "C1"],
        "explanation_template": (
            "Using a {separator_thickness} micron separator with {c_rate}C "
            "discharge rate is a serious safety risk. The extreme C-rate "
            "generates heat that can cause thermal runaway with such thin "
            "separators, and dendrite penetration risk is greatly elevated."
        ),
    },
    {
        "name": "pouch_huge_capacity_small_packaging",
        "description": "Pouch cell with huge capacity but tiny packaging offsets",
        "applicable_chemistries": None,
        "applicable_cell_types": ["pouch"],
        "param_overrides": {
            "capacity_ah": (100, 200),
            "packaging_offset_mm": (0.5, 1.0),
        },
        "constraint_ids": ["PO5", "PO7"],
        "explanation_template": (
            "A {capacity} Ah pouch cell with packaging offsets under 1 mm "
            "is not manufacturable. The seal width is insufficient for "
            "reliable hermeticity at this cell size."
        ),
    },
    {
        "name": "nmc811_extreme_cold_high_cycle",
        "description": "NMC-811 at extreme cold with high cycle life",
        "applicable_chemistries": ["NMC-811"],
        "applicable_cell_types": None,
        "param_overrides": {
            "temp_min": -35,
            "cycle_life": (6000, 10000),
        },
        "constraint_ids": ["C1", "C2"],
        "explanation_template": (
            "NMC-811 cycling at {temp_min} deg C with a {cycle_life}-cycle "
            "life target is contradictory. The high-nickel cathode suffers "
            "accelerated capacity fade at low temperatures due to kinetic "
            "limitations and SEI growth."
        ),
    },
]

# ═══════════════════════════════════════════════════════════════
# NATURAL LANGUAGE CONTRADICTION TEMPLATES
# ═══════════════════════════════════════════════════════════════
#
# These are carefully crafted to sound like a non-expert who
# doesn't realize the requirements conflict.

NL_CONTRADICTION_TEMPLATES = {
    "lfp_high_energy_density": [
        (
            "We need a battery for {use_case} that's extremely lightweight "
            "and energy-dense — at least {energy_density} Wh/kg. But safety "
            "is non-negotiable, so we want to stick with iron phosphate "
            "chemistry. Can you make that work?"
        ),
        (
            "Our client is building {use_case} and insists on an LFP cell "
            "for fire safety reasons, but they also want class-leading energy "
            "density — north of {energy_density} Wh/kg. Is that doable?"
        ),
        (
            "I need a cell for {use_case} with the safety profile of LFP "
            "but the energy density of a high-nickel cell — something "
            "around {energy_density} Wh/kg. What can you come up with?"
        ),
    ],
    "extreme_c_rate_with_high_energy": [
        (
            "We're designing {use_case} that needs maximum range but also "
            "needs to handle very fast charging — at least {c_rate}C "
            "continuous. Energy density should be above {energy_density} Wh/kg. "
            "Weight is absolutely critical."
        ),
        (
            "For {use_case}, we need a cell that can do {c_rate}C sustained "
            "discharge for burst performance, but we also can't compromise on "
            "energy density — we're targeting {energy_density} Wh/kg minimum. "
            "Is there a design that can do both?"
        ),
    ],
    "tiny_form_large_capacity": [
        (
            "We need {capacity} Ah of capacity in the smallest possible "
            "package for {use_case}. Think credit-card-sized if possible. "
            "The device has very limited internal volume."
        ),
        (
            "Can we get a {capacity} Ah cell that fits in a pocket-sized "
            "enclosure? It's for {use_case} and portability is everything. "
            "We want it as compact as physically possible."
        ),
    ],
    "max_cycle_life_max_energy": [
        (
            "For {use_case}, we need the absolute maximum energy density — "
            "we're talking {energy_density} Wh/kg or better — combined with "
            "a {cycle_life}-cycle warranty target. It's a 20-year product, "
            "so longevity is just as important as range."
        ),
        (
            "We're designing {use_case} that needs to maximize both range "
            "and lifespan. Target {energy_density} Wh/kg with at least "
            "{cycle_life} full cycles before end of life. The customer "
            "won't accept tradeoffs on either metric."
        ),
    ],
    "cold_temp_high_c_rate": [
        (
            "Our application is {use_case} that operates in Arctic "
            "conditions — we need reliable performance down to {temp_min} deg C. "
            "It also needs to accept fast charging at {c_rate}C when "
            "plugged in at a remote charging station. Is that feasible?"
        ),
        (
            "We're deploying {use_case} in northern Canada where "
            "temperatures regularly drop to {temp_min} deg C. The vehicles still "
            "need to fast-charge at {c_rate}C at those temperatures. "
            "What cell design would work here?"
        ),
    ],
    "cylindrical_small_diameter_large_capacity": [
        (
            "We want to use standard 18650 cells for {use_case} to keep "
            "costs down, but we need at least {capacity} Ah per cell. "
            "Our pack design is optimized for that form factor. Can it "
            "be done?"
        ),
        (
            "Is it possible to design an 18650-format cell with "
            "{capacity} Ah capacity for {use_case}? We want to leverage "
            "the existing supply chain for that format."
        ),
    ],
    "low_voltage_high_energy_density": [
        (
            "We need a cell for {use_case} with a nominal voltage around "
            "{voltage} V to match our legacy power electronics, but we "
            "still want best-in-class energy density — above "
            "{energy_density} Wh/kg. Can you design something?"
        ),
        (
            "Our system operates at {voltage} V per cell. For {use_case}, "
            "we also need at least {energy_density} Wh/kg. We can't change "
            "the voltage — the BMS firmware is locked to that range."
        ),
    ],
    "extreme_separator_with_high_rate": [
        (
            "For {use_case}, we want the thinnest possible separator to "
            "maximize active material volume — ideally {separator_thickness} "
            "microns. We also need the cell to handle {c_rate}C continuous "
            "discharge for high-power bursts."
        ),
        (
            "We're trying to squeeze every bit of energy out of each cell "
            "for {use_case}. Can we go down to {separator_thickness}-micron "
            "separator and still handle {c_rate}C discharge rates safely?"
        ),
    ],
    "pouch_huge_capacity_small_packaging": [
        (
            "We need a high-capacity pouch cell — around {capacity} Ah — "
            "but the packaging needs to be as slim as possible for "
            "{use_case}. Can we minimize the edge sealing area to under "
            "a millimeter?"
        ),
        (
            "For {use_case}, we want a {capacity} Ah pouch cell with "
            "minimal dead space around the edges. Ideally the seal width "
            "would be well under a millimeter to maximize the active area "
            "ratio."
        ),
    ],
    "nmc811_extreme_cold_high_cycle": [
        (
            "We're designing {use_case} for deployment in Scandinavian "
            "winters — ambient can hit {temp_min} deg C. We also need "
            "{cycle_life} full cycles over the product lifetime. "
            "We'd like NMC-811 for the energy density advantage."
        ),
        (
            "Our project involves {use_case} operating year-round in "
            "subarctic conditions (down to {temp_min} deg C). The customer "
            "expects {cycle_life} cycles minimum. We're leaning toward "
            "high-nickel NMC for range."
        ),
    ],
}

# ═══════════════════════════════════════════════════════════════
# PARAMETER FORMATTING VARIANTS
# ═══════════════════════════════════════════════════════════════

CAPACITY_FORMATS = [
    "{value} Ah",
    "{value} amp-hours",
    "around {value} Ah",
    "approximately {value} Ah",
    "{value} Ah (nominal)",
]

ENERGY_DENSITY_FORMATS = [
    "{value} Wh/kg",
    "{value} watt-hours per kilogram",
    "at least {value} Wh/kg",
    "above {value} Wh/kg",
    "targeting {value} Wh/kg",
]

CELL_TYPE_DISPLAY = {
    "pouch": "pouch",
    "prismatic": "prismatic",
    "cylindrical": "cylindrical",
}

APPLICATION_DISPLAY = {
    "ev_traction": "EV traction",
    "consumer_electronics": "consumer electronics",
    "grid_storage": "grid storage",
    "power_tools": "power tools",
}

CHEMISTRY_DISPLAY = {
    "NMC-111": "NMC-111",
    "NMC-622": "NMC-622",
    "NMC-811": "NMC-811",
    "LFP": "LFP",
}
