# Prismatic Master Template - Phase 1

## Purpose

The **Prismatic Master Template** (`prismatic_master.yaml`) is the **API contract** between the Driver Layer (LLMs, optimization algorithms, humans) and the CellCAD Engine.

It documents:
1. **Complete parameter schema** - Every input that CellCAD accepts
2. **Semantic documentation** - What each parameter means and why it matters
3. **Realistic bounds** - Valid ranges with typical automotive values
4. **Design trade-offs** - How parameters affect energy, power, and cycle life
5. **Parameter couplings** - Which parameters must change together

## What is the Master Template For?

### For LLM Drivers
An LLM reading this template can:
- Understand design intent ("make a high-energy cell" → modify loading parameters)
- Generate valid parameter sets without trial-and-error
- Understand trade-offs ("more cathode loading" → N/P ratio constraint → modify anode loading)
- Respond to natural language prompts with appropriate parameter choices

Example:
```yaml
cathode:
  loading_mg_cm2: 19.674
    # TRADE-OFF: ↑ loading = ↑ energy density, ↓ power capability, ↓ cycle life
    # COUPLED_WITH: anode.loading_mg_cm2 (maintain N/P ratio 1.05-1.25)
```

An LLM sees this and understands: "If the user wants more energy, increase cathode loading, but then must increase anode loading proportionally to maintain N/P ratio."

### For Human Users
Users can:
- Understand parameter meaning and constraints
- See industry-typical ranges
- Know which parameters affect design outcomes
- Reference defaults from a validated cell design (V1 Prismatic)

### For CellCAD Engine
The template defines:
- Input validation constraints
- Parameter types and units
- Derived property calculations
- Coupling rules between parameters

---

## File Structure

### Header (`_meta`)
Metadata about the template:
```yaml
_meta:
  template_version: "1.0"
  cell_type: "prismatic"
  base_reference: "v1_prismatic"
  purpose: "API contract for LLM-driven prismatic cell design"
```

### Core Parameters (Phase 1)

**5 main domains:**

1. **envelope** - Physical dimensions
   - External: cell_height_mm, cell_width_mm, cell_thickness_mm
   - Walls: wall_top_mm, wall_bottom_mm, wall_front_back_mm, wall_sides_mm
   - Internals: insulation_coating_um, corner_radii

2. **stack_config** - Electrode arrangement
   - Architecture: num_stacks, electrode_pairs_per_stack, end_electrode_config
   - Sheet geometry: cathode dimensions, anode offsets, separator offsets

3. **electrochemistry** - Active materials
   - Cathode: material_name, loading_mg_cm2, capacity, porosity, collector thickness
   - Anode: material_name, loading_mg_cm2, capacity, porosity, N/P ratio, collector thickness
   - Separator: material, thickness, porosity, areal_weight
   - Electrolyte: composition, density, excess_factor

4. **current_collection** - Electron pathways
   - Tabs: cathode and anode tab dimensions and materials

5. **packaging** - Non-active components
   - Housing: case material and lid thickness
   - Insulation: shell, fixing tape parameters

### Extended Parameters (Phase 2 - Placeholders)
These sections are documented but not implemented yet:
- `thermal_properties` - Anisotropic conductivity
- `mechanical_properties` - Young's modulus, Poisson's ratio, CTE
- `electrical_properties` - Conductivity, contact resistances

### Validation Rules (`_validation`)
Constraints that CellCAD enforces:
```yaml
_validation:
  geometry_fit:
    - "cathode_height_mm < cell_height_mm - wall_top_mm - wall_bottom_mm"
  electrochemistry:
    - "np_ratio >= 1.05  # Prevent lithium plating"
```

### Defaults Reference (`_defaults_source`)
All defaults come from V1 Prismatic (validated):
```yaml
_defaults_source:
  cell_reference: "V1 Prismatic"
  reference_outputs:
    capacity_ah: 120.866
    energy_wh: 440.467
    gravimetric_energy_density_wh_kg: 261.151
```

---

## Documentation Format

Each parameter includes:

```yaml
cathode:
  loading_mg_cm2:
    default: 19.674
    # WHAT: Cathode active material coating loading (areal weight) [mg/cm²]
    # RANGE: [5.0 - 30.0] Typical automotive: 15-25 mg/cm²
    # TRADE-OFF: ↑ loading = ↑ energy density, ↓ power capability, ↓ cycle life
    # COUPLED_WITH: anode.loading_mg_cm2 (must maintain N/P ratio 1.05-1.25)
    type: float
    min: 5.0
    max: 30.0
    unit: "mg/cm²"
```

**Fields:**
- `default` - Industry-standard starting value (from V1 Prismatic)
- `WHAT` - Definition, units, and meaning
- `RANGE` - [min - max] with typical values in parentheses
- `TRADE-OFF` - (Optional) Design implications for key parameters
- `COUPLED_WITH` - (Optional) Related parameters that should change together
- `type`, `min`, `max`, `unit` - Technical constraints for validation

**Not every parameter needs all fields:**
- `WHAT` and `RANGE` → Always
- `TRADE-OFF` → Only for key design parameters where LLM needs trade-off understanding
- `COUPLED_WITH` → Only where physics couples parameters

---

## Key Parameters for LLM Drivers

These are the parameters an LLM will most likely want to modify:

| Parameter | Why | Trade-off |
|-----------|-----|-----------|
| `cathode.loading_mg_cm2` | Primary energy density lever | More energy → lower power |
| `cathode.material_name` | Chemistry choice (NMC vs LFP) | Energy vs safety |
| `anode.loading_mg_cm2` | Capacity balance (must track N/P) | More capacity → lithium plating risk |
| `envelope.cell_*` | Physical size | Larger cell → more energy |
| `stack_config.electrode_pairs_per_stack` | Scales capacity | More pairs → thicker stack |
| `electrolyte.excess_factor` | Safety margin | More electrolyte → better safety, more weight |

---

## How an LLM Should Use This Template

### 1. Read the Meta Section
```python
meta = yaml.load()["_meta"]
print(f"Template: {meta['template_version']}")
print(f"Base reference: {meta['base_reference']}")
```

### 2. Extract Parameter Bounds
```python
cathode = yaml.load()["electrochemistry"]["cathode"]["loading_mg_cm2"]
print(f"Range: [{cathode['min']} - {cathode['max']}]")
print(f"Typical: 15-25 mg/cm²")  # From RANGE comment
```

### 3. Understand Trade-offs
```python
# LLM reads: "TRADE-OFF: ↑ loading = ↑ energy density, ↓ power capability"
# LLM understands: If user wants more energy, increase loading (within range)
```

### 4. Check Couplings
```python
# LLM reads: "COUPLED_WITH: anode.loading_mg_cm2 (maintain N/P ratio 1.05-1.25)"
# LLM understands: Can't just change cathode loading; must adjust anode too
```

### 5. Generate Valid Parameters
```python
# Constraint: N/P = anode_capacity / cathode_capacity >= 1.05
# If user wants higher cathode loading:
#   1. Increase cathode.loading_mg_cm2 ✓
#   2. Increase anode.loading_mg_cm2 proportionally
#   3. Verify N/P ratio >= 1.05
```

---

## Example: LLM Prompt Response

**User asks:** "Create a high-energy-density prismatic cell"

**LLM workflow using this template:**
1. Read cathode loading range: 5-30 mg/cm² (typical: 15-25)
2. Read TRADE-OFF: higher loading → higher energy but lower power
3. Read COUPLED_WITH: maintain N/P ratio 1.05-1.25
4. Read defaults: cathode=19.674, anode=11.478 (N/P = 1.225)
5. Generate new parameters:
   - Increase cathode loading: 19.674 → 25.0 mg/cm² (high but within range)
   - Adjust anode loading: 11.478 → 14.4 mg/cm² (maintain N/P = 1.225 × 25/19.674)
   - Keep other parameters at defaults
6. Validate N/P = 1.225 ✓, within ranges ✓
7. Return parameter set to CellCAD Engine

---

## What CellCAD Does With These Parameters

1. **Validates** - Checks all constraints from `_validation` section
2. **Derives** - Calculates:
   - Sheet areas (cathode_area = height × width)
   - Total capacity (loading × area × count)
   - Stack dimensions (sum of coating thicknesses)
   - Cell mass (material × volume + electrode masses)
   - Energy density (capacity × voltage / mass)
3. **Generates CAD** - Creates 3D STEP model with parametric geometry
4. **Exports** - BOM, FEM mesh, simulation inputs
5. **Reports** - Validation results, outputs, metrics

**This template only defines inputs; CellCAD computes the outputs.**

---

## What's NOT in Phase 1

**Phase 2 (Future)** will add:
- Thermal properties (k_inplane, k_throughplane, Cp)
- Mechanical properties (Young's modulus, Poisson's ratio, CTE)
- Electrical properties (conductivity, contact resistances)
- FEM/CFD simulation zone definitions
- Boundary condition templates

Currently these are placeholders only. CellCAD doesn't validate them yet.

---

## Validation & Reference Data

All defaults are from **V1 Prismatic**, a real validated cell:
- Source: `V1_Prismatic_Reference_Data.md`
- Capacity: 120.866 Ah
- Energy: 440.467 Wh
- Energy density: 261.15 Wh/kg (gravimetric), 629.29 Wh/L (volumetric)
- Mass: 1686.64 g

Using these defaults, CellCAD produces the reference outputs with <1% error.

---

## How to Use This File

### Python/YAML:
```python
import yaml

template = yaml.safe_load(open("prismatic_master.yaml"))

# Get all envelope parameters
print(template["envelope"])

# Get cathode loading range
cathode_loading = template["electrochemistry"]["cathode"]["loading_mg_cm2"]
print(f"Cathode loading range: {cathode_loading['min']}-{cathode_loading['max']} mg/cm²")

# Check validation rules
print(template["_validation"]["electrochemistry"])
```

### For Documentation:
This file is the authoritative specification for prismatic cell inputs. Use it to:
- Document what parameters CellCAD accepts
- Explain constraints to users
- Train LLM drivers
- Generate API documentation

### For Testing:
```python
# Generate random valid parameter set
def random_params():
    return {
        "envelope": {
            "external": {
                "cell_height_mm": random.uniform(50, 130),
                # ... etc
            }
        }
    }
```

---

## File Location
```
data/templates/
├── prismatic_master.yaml           # Master template (this file)
└── README_PRISMATIC_MASTER.md      # This documentation
```

---

## Version History

**v1.0 (2025-12-12)** - Initial Phase 1 release
- Complete envelope, stack_config, electrochemistry, current_collection, packaging
- All 100+ core parameters documented
- Extended parameters as Phase 2 placeholders
- Validation rules for geometry, electrochemistry, stack config
- Defaults from V1 Prismatic reference cell

---

## Related Documentation

- `CellCAD_Vision_and_Role.md` - Architectural philosophy
- `V1_Prismatic_Reference_Data.md` - Reference cell values
- `cellcad/models/prismatic.py` - Python dataclass implementation
- `create_fem_template.py` - FEM/CFD extended parameters (Phase 2)

---

**Status:** Phase 1 complete, Phase 2 in progress
**Maintained by:** CellCAD Development Team
**Last updated:** 2025-12-12
