#!/usr/bin/env python3
"""
Stage 1: Cell Configuration Generator for Fine-Tuning Dataset.

Generates valid battery cell configurations via Latin Hypercube Sampling
within schema-valid ranges, validated against the full FORGE 29-constraint
pipeline.

Strategy:
- Cylindrical + Pouch: Pure LHS within schema ranges → validate → keep valid
- Prismatic: LHS + v1_prismatic centroid perturbation as secondary source
- Schema ranges are NOT modified — configs must pass the same validation
  used in Corpus A/B experiments

Usage:
    python -m forge.finetune.data.config_generator --target 5000 --seed 42 --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from forge.engine.validation.pipeline import validate_cell_definition

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REFERENCE_DIR = Path(__file__).resolve().parents[3] / "data" / "reference"
TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "data" / "templates"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"

CELL_TYPES = ["prismatic", "pouch", "cylindrical"]

CHEMISTRY_BUCKET = {
    "LFP": "LFP", "LiFePO4": "LFP",
    "NMC": "NMC", "NMC111": "NMC", "NMC622": "NMC", "NMC811": "NMC",
    "NCM": "NMC", "NCM111": "NMC", "NCM652015": "NMC", "NMC712": "NMC",
    "NMCA": "NMC", "NCA": "NCA", "LMO": "LMO",
}

# Chemistry presets: cathode material_name, rev_spec_capacity, nominal_voltage
CHEMISTRY_PRESETS = {
    "NMC811": {"material_name": "NMC811", "rev_spec_capacity_mahg": 195.0, "voltage": 3.65},
    "NMC622": {"material_name": "NMC622", "rev_spec_capacity_mahg": 175.0, "voltage": 3.60},
    "NMC111": {"material_name": "NMC111", "rev_spec_capacity_mahg": 155.0, "voltage": 3.70},
    "LFP":    {"material_name": "LFP",    "rev_spec_capacity_mahg": 160.0, "voltage": 3.20},
    "NCA":    {"material_name": "NCA",     "rev_spec_capacity_mahg": 200.0, "voltage": 3.65},
}

# Target chemistry distribution (by bucket)
CHEMISTRY_TARGETS = {"NMC": 0.45, "LFP": 0.40, "NCA": 0.10, "LMO": 0.05}

# Available chemistry options per bucket for sampling
CHEMISTRY_OPTIONS = {
    "NMC": ["NMC811", "NMC622", "NMC111"],
    "LFP": ["LFP"],
    "NCA": ["NCA"],
}


# ---------------------------------------------------------------------------
# Schema range extraction
# ---------------------------------------------------------------------------

_SCHEMA_RANGES: dict[str, dict[str, tuple[float, float]]] = {}
_SCHEMA_ENUMS: dict[str, dict[str, list[str]]] = {}


def _load_schemas() -> None:
    """Extract numeric ranges and enum values from JSON schemas."""
    for ct, fname in [
        ("prismatic", "prismatic_master.schema.json"),
        ("pouch", "pouch_master.schema.json"),
        ("cylindrical", "cylindrical_master.schema.json"),
    ]:
        path = TEMPLATES_DIR / fname
        if not path.exists():
            continue
        with open(path) as f:
            schema = json.load(f)
        ranges: dict[str, tuple[float, float]] = {}
        enums: dict[str, list[str]] = {}
        _extract_schema_info(schema, "", ranges, enums)
        _SCHEMA_RANGES[ct] = ranges
        _SCHEMA_ENUMS[ct] = enums
        logger.info("%s: extracted %d numeric ranges, %d enums", ct, len(ranges), len(enums))


def _extract_schema_info(
    obj: Any, prefix: str,
    ranges: dict[str, tuple[float, float]],
    enums: dict[str, list[str]],
) -> None:
    if not isinstance(obj, dict):
        return
    if "oneOf" in obj:
        for sub in obj["oneOf"]:
            if sub.get("type") == "number":
                lo, hi = sub.get("minimum"), sub.get("maximum")
                if lo is not None and hi is not None:
                    ranges[prefix] = (float(lo), float(hi))
                return
            if sub.get("type") == "string" and "enum" in sub:
                enums[prefix] = sub["enum"]
                return
    if "minimum" in obj and "maximum" in obj:
        ranges[prefix] = (float(obj["minimum"]), float(obj["maximum"]))
        return
    if "enum" in obj:
        enums[prefix] = obj["enum"]
        return
    if "properties" in obj:
        for key, val in obj["properties"].items():
            child = f"{prefix}.{key}" if prefix else key
            _extract_schema_info(val, child, ranges, enums)


def get_schema_ranges(cell_type: str) -> dict[str, tuple[float, float]]:
    if not _SCHEMA_RANGES:
        _load_schemas()
    return _SCHEMA_RANGES.get(cell_type, {})


# ---------------------------------------------------------------------------
# LHS-based template generation
# ---------------------------------------------------------------------------

def generate_lhs_template(
    cell_type: str,
    rng: np.random.Generator,
    chemistry: str,
) -> dict:
    """Generate a single cell config template by sampling within schema ranges.

    Returns a dict in the exact YAML template format that validate_cell_definition() expects.
    """
    ranges = get_schema_ranges(cell_type)
    preset = CHEMISTRY_PRESETS.get(chemistry, CHEMISTRY_PRESETS["NMC811"])

    def sample(field: str, default_lo: float, default_hi: float) -> float:
        lo, hi = ranges.get(field, (default_lo, default_hi))
        return round(float(rng.uniform(lo, hi)), 2)

    def sample_int(field: str, default_lo: int, default_hi: int) -> int:
        lo, hi = ranges.get(field, (default_lo, default_hi))
        return int(rng.integers(int(lo), int(hi) + 1))

    # Build electrochemistry (common to all types)
    # N/P ratio: sample first, then derive anode loading to be consistent
    np_ratio = sample("electrochemistry.anode.np_ratio", 1.05, 1.25)
    cathode_rev_cap = preset["rev_spec_capacity_mahg"] * float(rng.uniform(0.95, 1.05))
    cathode_rev_cap = round(max(140.0, min(220.0, cathode_rev_cap)), 1)
    cathode_loading = sample("electrochemistry.cathode.loading_mg_cm2", 10.0, 25.0)

    anode_rev_cap = sample("electrochemistry.anode.rev_spec_capacity_mahg", 300.0, 450.0)
    # Derive anode loading from N/P ratio: np = (anode_loading * anode_cap) / (cathode_loading * cathode_cap)
    anode_loading = round(np_ratio * cathode_loading * cathode_rev_cap / anode_rev_cap, 2)
    anode_loading = max(5.0, min(20.0, anode_loading))

    cathode_coating_0 = sample("electrochemistry.cathode.coating_thickness_0pct_um", 40.0, 90.0)
    cathode_coating_100 = round(cathode_coating_0 * float(rng.uniform(1.0, 1.05)), 2)
    cathode_coating_100 = max(cathode_coating_0, min(100.0, cathode_coating_100))

    anode_coating_0 = sample("electrochemistry.anode.coating_thickness_0pct_um", 50.0, 95.0)
    anode_coating_100 = round(anode_coating_0 * float(rng.uniform(1.0, 1.08)), 2)
    anode_coating_100 = max(anode_coating_0, min(100.0, anode_coating_100))

    echem = {
        "cathode": {
            "material_name": preset["material_name"],
            "loading_mg_cm2": round(cathode_loading, 2),
            "rev_spec_capacity_mahg": cathode_rev_cap,
            "collector_thickness_um": sample("electrochemistry.cathode.collector_thickness_um", 10.0, 20.0),
            "coating_thickness_0pct_um": cathode_coating_0,
            "coating_thickness_100pct_um": cathode_coating_100,
            "porosity_pct": sample("electrochemistry.cathode.porosity_pct", 20.0, 35.0),
        },
        "anode": {
            "material_name": "Graphite",
            "loading_mg_cm2": anode_loading,
            "rev_spec_capacity_mahg": round(anode_rev_cap, 1),
            "collector_thickness_um": sample("electrochemistry.anode.collector_thickness_um", 6.0, 12.0),
            "coating_thickness_0pct_um": anode_coating_0,
            "coating_thickness_100pct_um": anode_coating_100,
            "porosity_pct": sample("electrochemistry.anode.porosity_pct", 25.0, 40.0),
            "np_ratio": round(np_ratio, 3),
        },
        "separator": {
            "material_name": "Ceramic-coated PE",
            "thickness_um": sample("electrochemistry.separator.thickness_um", 10.0, 20.0),
            "porosity_pct": sample("electrochemistry.separator.porosity_pct", 35.0, 50.0),
            "areal_weight_mgcm2": sample("electrochemistry.separator.areal_weight_mgcm2", 1.0, 2.0),
        },
        "electrolyte": {
            "material_name": "LiPF6 in EC:EMC",
            "density_g_cm3": round(float(rng.uniform(1.18, 1.28)), 2),
            "excess_factor": sample("electrochemistry.electrolyte.excess_factor", 1.0, 1.15),
        },
    }

    if cell_type == "prismatic":
        return _build_prismatic_template(rng, ranges, echem, preset)
    if cell_type == "pouch":
        return _build_pouch_template(rng, ranges, echem, preset)
    if cell_type == "cylindrical":
        return _build_cylindrical_template(rng, ranges, echem, preset)
    raise ValueError(f"Unknown cell type: {cell_type}")


def _build_prismatic_template(rng, ranges, echem, preset) -> dict:
    def s(f, lo, hi): return round(float(rng.uniform(*ranges.get(f, (lo, hi)))), 2)
    def si(f, lo, hi): return int(rng.integers(int(ranges.get(f, (lo, hi))[0]), int(ranges.get(f, (lo, hi))[1]) + 1))

    cell_h = s("envelope.external.cell_height_mm", 60.0, 180.0)
    cell_w = s("envelope.external.cell_width_mm", 120.0, 350.0)
    cell_t = s("envelope.external.cell_thickness_mm", 12.0, 60.0)
    wall_top = s("envelope.walls.wall_top_mm", 0.5, 4.0)
    wall_bot = s("envelope.walls.wall_bottom_mm", 0.5, 2.0)
    wall_fb = s("envelope.walls.wall_front_back_mm", 0.3, 1.0)
    wall_s = s("envelope.walls.wall_sides_mm", 0.5, 1.5)

    # Cathode must fit inside cavity
    internal_h = cell_h - wall_top - wall_bot
    internal_w = cell_w - 2 * wall_s
    cat_h = round(float(rng.uniform(max(50.0, internal_h * 0.8), internal_h * 0.95)), 2)
    cat_h = max(50.0, min(ranges.get("stack_config.sheet_geometry.cathode_height_mm", (50, 150))[1], cat_h))
    cat_w = round(float(rng.uniform(max(100.0, internal_w * 0.85), internal_w * 0.97)), 2)
    cat_w = max(100.0, min(ranges.get("stack_config.sheet_geometry.cathode_width_mm", (100, 350))[1], cat_w))

    offset = round(float(rng.uniform(1.0, 3.0)), 2)

    # Add salt_concentration_m for prismatic only
    echem["electrolyte"]["salt_concentration_m"] = round(float(rng.uniform(0.9, 1.4)), 2)

    return {
        "_meta": {"cell_type": "prismatic", "design_intent": "Generated training config"},
        "envelope": {
            "external": {"cell_height_mm": cell_h, "cell_width_mm": cell_w, "cell_thickness_mm": cell_t},
            "walls": {"wall_top_mm": wall_top, "wall_bottom_mm": wall_bot,
                      "wall_front_back_mm": wall_fb, "wall_sides_mm": wall_s},
            "internals": {"insulation_coating_um": s("envelope.internals.insulation_coating_um", 60.0, 180.0),
                          "external_corner_radius_mm": round(float(rng.uniform(1.0, 3.0)), 2),
                          "internal_corner_radius_mm": round(float(rng.uniform(0.5, 2.0)), 2)},
        },
        "stack_config": {
            "architecture": {
                "num_stacks": si("stack_config.architecture.num_stacks", 1, 4),
                "electrode_pairs_per_stack": si("stack_config.architecture.electrode_pairs_per_stack", 10, 50),
                "end_electrode_config": rng.choice(["BothNegative", "BothPositive", "PositiveNegative"]),
            },
            "sheet_geometry": {
                "cathode_height_mm": cat_h, "cathode_width_mm": cat_w,
                "anode_offset_top_mm": offset, "anode_offset_bottom_mm": offset,
                "anode_offset_left_mm": offset, "anode_offset_right_mm": offset,
                "separator_offset_top_mm": offset + 0.5, "separator_offset_bottom_mm": offset + 0.5,
                "separator_offset_left_mm": offset + 0.5, "separator_offset_right_mm": offset + 0.5,
            },
        },
        "electrochemistry": echem,
        "current_collection": {
            "tabs": {
                "cathode": {"material": "Aluminum", "height_mm": round(float(rng.uniform(20.0, 60.0)), 1),
                            "width_mm": round(float(rng.uniform(30.0, 80.0)), 1), "thickness_mm": 0.3},
                "anode": {"material": "Nickel-plated copper", "height_mm": round(float(rng.uniform(20.0, 60.0)), 1),
                          "width_mm": round(float(rng.uniform(30.0, 80.0)), 1), "thickness_mm": 0.2},
            },
        },
        "packaging": {
            "housing": {"case_material": "Aluminum", "case_density_g_cm3": 2.70,
                        "lid_thickness_mm": round(float(rng.uniform(1.0, 3.0)), 2)},
            "insulation": {
                "shell_thickness_um": s("packaging.insulation.shell_thickness_um", 80.0, 180.0),
                "shell_count": si("packaging.insulation.shell_count", 1, 3),
                "fixing_tape_width_mm": s("packaging.insulation.fixing_tape_width_mm", 5.0, 20.0),
                "fixing_tape_count": si("packaging.insulation.fixing_tape_count", 2, 6),
            },
        },
    }


def _build_pouch_template(rng, ranges, echem, preset) -> dict:
    def s(f, lo, hi): return round(float(rng.uniform(*ranges.get(f, (lo, hi)))), 2)
    def si(f, lo, hi): return int(rng.integers(int(ranges.get(f, (lo, hi))[0]), int(ranges.get(f, (lo, hi))[1]) + 1))

    anode_off = s("geometry.anode_offset_mm", 1.0, 4.0)
    sep_off = round(anode_off + float(rng.uniform(0.3, 1.5)), 2)

    return {
        "_meta": {"cell_type": "pouch", "design_intent": "Generated training config"},
        "geometry": {
            "cathode_height_mm": s("geometry.cathode_height_mm", 50.0, 400.0),
            "cathode_width_mm": s("geometry.cathode_width_mm", 50.0, 350.0),
            "anode_offset_mm": anode_off,
            "separator_offset_mm": sep_off,
        },
        "stack_config": {
            "num_stacks": si("stack_config.num_stacks", 1, 4),
            "electrode_pairs_per_stack": si("stack_config.electrode_pairs_per_stack", 5, 40),
            "end_electrode_config": rng.choice(["BothNegative", "BothPositive", "PositiveNegative"]),
            "separator_overwraps": si("stack_config.separator_overwraps", 1, 3),
        },
        "electrochemistry": echem,
        "tabs": {
            "cathode": {"material": "Aluminum", "height_mm": round(float(rng.uniform(15.0, 40.0)), 1),
                        "width_mm": round(float(rng.uniform(20.0, 50.0)), 1), "thickness_mm": 0.3},
            "anode": {"material": "Nickel-plated Copper", "height_mm": round(float(rng.uniform(15.0, 40.0)), 1),
                      "width_mm": round(float(rng.uniform(15.0, 40.0)), 1), "thickness_mm": 0.2},
        },
        "packaging": {
            "pouch_thickness_mm": round(float(rng.uniform(0.08, 0.15)), 3),
            "offset_top_mm": s("packaging.offset_top_mm", 3.0, 12.0),
            "offset_bottom_mm": s("packaging.offset_bottom_mm", 2.0, 8.0),
            "offset_sides_mm": s("packaging.offset_sides_mm", 2.0, 8.0),
        },
    }


def _build_cylindrical_template(rng, ranges, echem, preset) -> dict:
    def s(f, lo, hi): return round(float(rng.uniform(*ranges.get(f, (lo, hi)))), 2)

    # Pick a standard format or custom
    fmt = rng.choice(["18650", "21700", "4680", "custom"], p=[0.2, 0.35, 0.35, 0.1])
    if fmt == "18650":
        dia, length = 18.0, 65.0
    elif fmt == "21700":
        dia, length = 21.0, 70.0
    elif fmt == "4680":
        dia, length = 46.0, 80.0
    else:
        dia = s("geometry.diameter_mm", 14.0, 50.0)
        length = s("geometry.length_mm", 40.0, 90.0)

    # Add small variation to standard formats
    if fmt != "custom":
        dia = round(dia + float(rng.uniform(-0.5, 0.5)), 2)
        dia = max(10.0, min(60.0, dia))
        length = round(length + float(rng.uniform(-2.0, 2.0)), 2)
        length = max(30.0, min(100.0, length))

    tab_type = "tabless" if fmt == "4680" and rng.random() > 0.3 else "traditional"
    winding: dict[str, Any] = {
        "mandrel_diameter_mm": s("winding.mandrel_diameter_mm", 2.0, 6.0),
        "winding_clearance_mm": s("winding.winding_clearance_mm", 0.05, 0.3),
        "winding_tension_factor": s("winding.winding_tension_factor", 0.8, 1.0),
        "tab_type": tab_type,
    }
    if tab_type == "tabless":
        winding["anode_foil_extension_mm"] = round(float(rng.uniform(2.0, 5.0)), 2)
        winding["cathode_foil_extension_mm"] = round(float(rng.uniform(2.0, 5.0)), 2)
    else:
        winding["anode_tab_width_mm"] = round(float(rng.uniform(3.0, 8.0)), 2)
        winding["anode_tab_thickness_mm"] = round(float(rng.uniform(0.05, 0.2)), 3)
        winding["cathode_tab_width_mm"] = round(float(rng.uniform(3.0, 7.0)), 2)
        winding["cathode_tab_thickness_mm"] = round(float(rng.uniform(0.08, 0.25)), 3)

    can_mat = "nickel_plated_steel" if dia < 30 else rng.choice(["nickel_plated_steel", "aluminum"])

    return {
        "_meta": {"cell_type": "cylindrical", "format": fmt, "design_intent": "Generated training config"},
        "geometry": {
            "diameter_mm": dia, "length_mm": length,
            "can_wall_thickness_mm": s("geometry.can_wall_thickness_mm", 0.15, 0.5),
            "can_bottom_thickness_mm": s("geometry.can_bottom_thickness_mm", 0.2, 0.8),
            "header_height_mm": s("geometry.header_height_mm", 2.0, 6.0),
        },
        "winding": winding,
        "electrochemistry": echem,
        "housing": {
            "can_material": can_mat,
            "header_mass_g": round(float(rng.uniform(1.0, 8.0)), 2),
            "bottom_insulator_mass_g": round(float(rng.uniform(0.05, 0.5)), 3),
            "top_insulator_mass_g": round(float(rng.uniform(0.05, 0.5)), 3),
        },
    }


# ---------------------------------------------------------------------------
# Generation loop
# ---------------------------------------------------------------------------

def generate_configs(
    target: int,
    sigma: float,
    seed: int,
    output_dir: Path,
    max_attempts_multiplier: int = 10,
    verbose: bool = False,
) -> dict:
    """Generate valid cell configs via LHS and write to JSONL files."""
    rng = np.random.default_rng(seed)

    per_type_target = target // len(CELL_TYPES)
    remainder = target % len(CELL_TYPES)

    output_dir.mkdir(parents=True, exist_ok=True)
    all_path = output_dir / "all_configs.jsonl"

    metadata: dict[str, Any] = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "seed": seed, "sigma": sigma, "target": target,
        "strategy": "LHS within schema ranges, 29-constraint validation",
        "generated": {}, "attempts": {}, "pass_rate": {},
        "chemistry_distribution": {}, "centroid_distribution": {},
        "schema": "v1", "constraints_version": "29_checks",
    }

    global_chem: dict[str, int] = {}
    # Build chemistry sampling weights (no LMO available)
    effective_targets = {k: v for k, v in CHEMISTRY_TARGETS.items() if k in CHEMISTRY_OPTIONS}
    total_weight = sum(effective_targets.values())
    chem_buckets = list(effective_targets.keys())
    chem_weights = np.array([effective_targets[b] / total_weight for b in chem_buckets])

    with open(all_path, "w") as all_fh:
        for ct_idx, cell_type in enumerate(CELL_TYPES):
            ct_target = per_type_target + (1 if ct_idx < remainder else 0)
            ct_path = output_dir / f"{cell_type}_configs.jsonl"
            generated = 0
            attempts = 0
            max_attempts = ct_target * max_attempts_multiplier

            if verbose:
                print(f"\n[{cell_type}] Target: {ct_target}, max_attempts: {max_attempts}")

            with open(ct_path, "w") as ct_fh:
                while generated < ct_target and attempts < max_attempts:
                    # Sample chemistry
                    bucket = rng.choice(chem_buckets, p=chem_weights)
                    options = CHEMISTRY_OPTIONS[bucket]
                    chemistry = rng.choice(options)

                    # Generate candidate
                    candidate = generate_lhs_template(cell_type, rng, chemistry)
                    attempts += 1

                    # Validate
                    result = validate_cell_definition(candidate, cell_type=cell_type)
                    if not result.valid:
                        continue

                    generated += 1
                    global_chem[bucket] = global_chem.get(bucket, 0) + 1

                    config_id = f"{cell_type[:3].upper()}_{generated:05d}"
                    record = {
                        "config_id": config_id,
                        "cell_type": cell_type,
                        "chemistry": chemistry,
                        "chemistry_bucket": bucket,
                        "source_reference": "lhs_sampling",
                        "config": candidate,
                        "validation_summary": {
                            "constraints_total": len(result.constraint_results),
                            "constraints_passed": sum(1 for cr in result.constraint_results if cr.passed),
                            "constraints_failed": sum(1 for cr in result.constraint_results if not cr.passed),
                        },
                    }

                    line = json.dumps(record, default=str) + "\n"
                    ct_fh.write(line)
                    all_fh.write(line)

                    if verbose and generated % 100 == 0:
                        rate = generated / attempts if attempts else 0
                        print(f"  [{cell_type}] {generated}/{ct_target} "
                              f"({attempts} attempts, {rate:.1%} pass rate)")

            pass_rate = generated / attempts if attempts else 0
            metadata["generated"][cell_type] = generated
            metadata["attempts"][cell_type] = attempts
            metadata["pass_rate"][cell_type] = round(pass_rate, 3)

            if verbose:
                print(f"  [{cell_type}] DONE: {generated}/{ct_target} "
                      f"({attempts} attempts, {pass_rate:.1%} pass rate)")

            if generated < ct_target:
                logger.warning(
                    "%s: only generated %d/%d (pass rate %.1f%%).",
                    cell_type, generated, ct_target, pass_rate * 100,
                )

    metadata["chemistry_distribution"] = global_chem

    meta_path = output_dir / "generation_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    if verbose:
        total = sum(metadata["generated"].values())
        print(f"\n=== COMPLETE: {total}/{target} configs generated ===")
        print(f"Chemistry: {global_chem}")
        print(f"Pass rates: {metadata['pass_rate']}")
        print(f"Metadata: {meta_path}")

    return metadata


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate valid cell configs for fine-tuning dataset"
    )
    parser.add_argument("--target", type=int, default=5000)
    parser.add_argument("--sigma", type=float, default=0.15,
                        help="Not used in LHS mode, kept for API compat")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-attempts-multiplier", type=int, default=10)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    generate_configs(
        target=args.target, sigma=args.sigma, seed=args.seed,
        output_dir=Path(args.output_dir),
        max_attempts_multiplier=args.max_attempts_multiplier,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
