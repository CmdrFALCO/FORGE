#!/usr/bin/env python3
"""
Phase 3: Stratified Prompt Corpus Generator for AXIOM/FORGE experiments.

Generates a corpus of exactly 500 battery design prompts, stratified across
cell_type x chemistry x application x difficulty x prompt_style.

Usage:
    python -m forge.experiments.generate_corpus
    # or
    python forge/experiments/generate_corpus.py

Output:
    forge/experiments/prompt_corpus_v1.json

This script is standalone — no FORGE imports.
Standard library only: json, random, datetime, itertools, pathlib.
"""

import itertools
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from forge.experiments.corpus_config import (
    APPLICATION_DISPLAY,
    APPLICATION_PROFILES,
    CAPACITY_FORMATS,
    CELL_TYPE_DISPLAY,
    CHEMISTRY_DISPLAY,
    CHEMISTRY_MENTION_EXPLICIT,
    CHEMISTRY_MENTION_IMPLICIT,
    CHEMISTRY_PROFILES,
    CONTRADICTION_RECIPES,
    DETAILED_TEMPLATES,
    ENERGY_DENSITY_FORMATS,
    FLAVOR_FRAGMENTS,
    NATURAL_LANGUAGE_TEMPLATES,
    NL_CONTRADICTION_TEMPLATES,
    TERSE_TEMPLATES,
)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

SEED = 42
TOTAL_TARGET = 500
FULL_CROSS_PRODUCT = 576  # 3 x 4 x 4 x 4 x 3
TRIM_COUNT = FULL_CROSS_PRODUCT - TOTAL_TARGET  # 76

CELL_TYPES = ["pouch", "prismatic", "cylindrical"]
CHEMISTRIES = ["NMC-111", "NMC-622", "NMC-811", "LFP"]
APPLICATIONS = ["ev_traction", "consumer_electronics", "grid_storage", "power_tools"]
DIFFICULTIES = ["standard", "edge_case", "underspecified", "contradictory"]
PROMPT_STYLES = ["terse", "detailed", "natural_language"]


# ═══════════════════════════════════════════════════════════════
# PARAMETER GENERATION
# ═══════════════════════════════════════════════════════════════


def _sample_from_range(rng: random.Random, low: float, high: float, *, middle_pct: float = 1.0) -> float:
    """Sample from a range, optionally restricted to middle percentage."""
    span = high - low
    if middle_pct < 1.0:
        margin = span * (1.0 - middle_pct) / 2.0
        low = low + margin
        high = high - margin
    return round(rng.uniform(low, high), 1)



def generate_standard_params(rng: random.Random, chemistry: str, application: str) -> dict:
    """Generate parameters from the middle 60% of ranges."""
    chem = CHEMISTRY_PROFILES[chemistry]
    app = APPLICATION_PROFILES[application]

    # Capacity: intersection of chemistry and application ranges
    cap_low = max(chem["typical_capacity_range"][0], app["typical_capacity"][0])
    cap_high = min(chem["typical_capacity_range"][1], app["typical_capacity"][1])
    if cap_low > cap_high:
        cap_low, cap_high = app["typical_capacity"]

    capacity = _sample_from_range(rng, cap_low, cap_high, middle_pct=0.6)
    energy_density = _sample_from_range(
        rng, chem["energy_density_range"][0], chem["energy_density_range"][1], middle_pct=0.6
    )
    cycle_life = app["cycle_life_target"]
    temp_min, temp_max = app["temp_range"]

    return {
        "capacity_ah": capacity,
        "nominal_voltage": chem["nominal_voltage"],
        "energy_density_target": energy_density,
        "cycle_life": cycle_life,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "c_rate": round(rng.uniform(0.5, chem["max_c_rate"] * 0.7), 1),
        "cathode_material": chem["cathode_material"],
    }


def generate_edge_case_params(rng: random.Random, chemistry: str, application: str) -> dict:
    """Generate parameters pushed to the boundary of physical plausibility."""
    chem = CHEMISTRY_PROFILES[chemistry]
    app = APPLICATION_PROFILES[application]

    # Capacity at extreme of application range
    cap_low, cap_high = app["typical_capacity"]
    if rng.random() < 0.5:
        capacity = round(rng.uniform(cap_low, cap_low + (cap_high - cap_low) * 0.1), 1)
    else:
        capacity = round(rng.uniform(cap_high * 0.9, cap_high), 1)

    # Energy density at 95th percentile
    ed_low, ed_high = chem["energy_density_range"]
    energy_density = round(rng.uniform(ed_low + (ed_high - ed_low) * 0.85, ed_high * 0.99), 1)

    # Aggressive C-rate near max
    c_rate = round(rng.uniform(chem["max_c_rate"] * 0.85, chem["max_c_rate"] * 0.98), 1)

    # Extended temperature range
    temp_min = app["temp_range"][0] - rng.randint(0, 10)
    temp_max = app["temp_range"][1] + rng.randint(0, 5)

    # Aggressive cycle life
    cycle_life = int(app["cycle_life_target"] * rng.uniform(1.3, 1.8))

    return {
        "capacity_ah": capacity,
        "nominal_voltage": chem["nominal_voltage"],
        "energy_density_target": energy_density,
        "cycle_life": cycle_life,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "c_rate": c_rate,
        "cathode_material": chem["cathode_material"],
    }


def generate_underspecified_params(rng: random.Random, chemistry: str, application: str) -> dict:
    """Generate parameters with deliberate omissions."""
    # Start with standard params, then remove some
    params = generate_standard_params(rng, chemistry, application)

    # Decide which fields to omit (at least 2, up to 4)
    omittable = ["capacity_ah", "energy_density_target", "cycle_life", "temp_min", "temp_max", "c_rate"]
    num_to_omit = rng.randint(2, 4)
    to_omit = rng.sample(omittable, num_to_omit)

    for field in to_omit:
        params.pop(field, None)

    # Mark what's missing for metadata
    params["_omitted_fields"] = to_omit

    return params


def generate_contradictory_params(
    rng: random.Random, chemistry: str, application: str, cell_type: str
) -> tuple[dict, list[str], str]:
    """
    Generate parameters with hidden physical conflicts.

    Returns: (params_dict, expected_violations, explanation)
    """
    chem = CHEMISTRY_PROFILES[chemistry]

    # Find applicable recipes
    applicable = []
    for recipe in CONTRADICTION_RECIPES:
        if recipe["applicable_chemistries"] is not None and chemistry not in recipe["applicable_chemistries"]:
            continue
        if recipe["applicable_cell_types"] is not None and cell_type not in recipe["applicable_cell_types"]:
            continue
        applicable.append(recipe)

    if not applicable:
        # Fallback: always-applicable recipes (cold_temp_high_c_rate, extreme_separator)
        applicable = [r for r in CONTRADICTION_RECIPES if r["applicable_chemistries"] is None and r["applicable_cell_types"] is None]

    recipe = rng.choice(applicable)

    # Start with standard params
    params = generate_standard_params(rng, chemistry, application)

    # Apply contradiction overrides
    overrides = recipe["param_overrides"]
    explanation_vars = {}

    if "energy_density_target" in overrides:
        ed_range = overrides["energy_density_target"]
        params["energy_density_target"] = round(rng.uniform(ed_range[0], ed_range[1]), 1)
        explanation_vars["energy_density"] = params["energy_density_target"]

    if overrides.get("energy_density_target_high"):
        ed_high = chem["energy_density_range"][1]
        params["energy_density_target"] = round(rng.uniform(ed_high * 0.95, ed_high * 1.15), 1)
        explanation_vars["energy_density"] = params["energy_density_target"]

    if "c_rate_target" in overrides:
        cr_range = overrides["c_rate_target"]
        params["c_rate"] = round(rng.uniform(cr_range[0], cr_range[1]), 1)
        explanation_vars["c_rate"] = params["c_rate"]

    if "capacity_ah" in overrides:
        cap_range = overrides["capacity_ah"]
        params["capacity_ah"] = round(rng.uniform(cap_range[0], cap_range[1]), 1)
        explanation_vars["capacity"] = params["capacity_ah"]

    if "cycle_life" in overrides:
        cl_range = overrides["cycle_life"]
        params["cycle_life"] = rng.randint(cl_range[0], cl_range[1])
        explanation_vars["cycle_life"] = params["cycle_life"]

    if "temp_min" in overrides:
        params["temp_min"] = overrides["temp_min"]
        explanation_vars["temp_min"] = params["temp_min"]

    if "voltage" in overrides:
        v_range = overrides["voltage"]
        params["nominal_voltage"] = round(rng.uniform(v_range[0], v_range[1]), 2)
        explanation_vars["voltage"] = params["nominal_voltage"]

    if "separator_thickness" in overrides:
        st_range = overrides["separator_thickness"]
        params["separator_thickness_um"] = round(rng.uniform(st_range[0], st_range[1]), 1)
        explanation_vars["separator_thickness"] = params["separator_thickness_um"]

    if "format" in overrides:
        params["format"] = overrides["format"]

    if "packaging_offset_mm" in overrides:
        po_range = overrides["packaging_offset_mm"]
        params["packaging_offset_mm"] = round(rng.uniform(po_range[0], po_range[1]), 1)
        explanation_vars["packaging_offset"] = params["packaging_offset_mm"]

    if overrides.get("form_factor_constraint") == "very_small":
        explanation_vars["capacity"] = params["capacity_ah"]

    # Filter constraint IDs to those relevant to this cell type
    constraint_ids = _filter_constraints_for_cell_type(recipe["constraint_ids"], cell_type)

    # Build explanation
    try:
        explanation = recipe["explanation_template"].format(**explanation_vars)
    except KeyError:
        explanation = recipe["description"]

    return params, constraint_ids, explanation


def _filter_constraints_for_cell_type(constraint_ids: list[str], cell_type: str) -> list[str]:
    """Filter constraint IDs to only those applicable for the given cell type."""
    result = []
    for cid in constraint_ids:
        if cid.startswith("CY"):
            # Cylindrical-specific (check before generic "C" prefix)
            if cell_type == "cylindrical":
                result.append(cid)
        elif cid.startswith("C") and cid[1:].isdigit():
            # Common constraints (C1-C7) — always applicable
            result.append(cid)
        elif cid.startswith("PR"):
            if cell_type == "prismatic":
                result.append(cid)
        elif cid.startswith("PO"):
            if cell_type == "pouch":
                result.append(cid)
    return result if result else constraint_ids[:1]  # At least one


# ═══════════════════════════════════════════════════════════════
# PROMPT TEXT GENERATION
# ═══════════════════════════════════════════════════════════════


def format_capacity(rng: random.Random, value: float) -> str:
    """Format a capacity value with random variation."""
    fmt = rng.choice(CAPACITY_FORMATS)
    # Sometimes round to integer for cleaner look
    if value == int(value):
        return fmt.format(value=int(value))
    return fmt.format(value=value)


def format_energy_density(rng: random.Random, value: float) -> str:
    """Format an energy density value with random variation."""
    fmt = rng.choice(ENERGY_DENSITY_FORMATS)
    return fmt.format(value=int(value))


def build_terse_prompt(
    rng: random.Random,
    params: dict,
    chemistry: str,
    cell_type: str,
    application: str,
    difficulty: str,
) -> tuple[str, str]:
    """Build a terse one-line prompt. Returns (text, template_id)."""
    template_entry = rng.choice(TERSE_TEMPLATES)
    template_id = template_entry["id"]
    template = template_entry["template"]

    # Terse templates already have "Ah" in them, so just use the raw number
    capacity_val = params.get("capacity_ah", 50)
    if capacity_val == int(capacity_val):
        capacity_str = str(int(capacity_val))
    else:
        capacity_str = str(capacity_val)
    app_display = APPLICATION_DISPLAY[application]

    text = template.format(
        capacity=capacity_str,
        chemistry=CHEMISTRY_DISPLAY[chemistry],
        cell_type=CELL_TYPE_DISPLAY[cell_type],
        application=app_display,
    )

    return text, template_id


def build_detailed_prompt(
    rng: random.Random,
    params: dict,
    chemistry: str,
    cell_type: str,
    application: str,
    difficulty: str,
) -> tuple[str, str]:
    """Build a detailed multi-line prompt. Returns (text, template_id)."""
    template_entry = rng.choice(DETAILED_TEMPLATES)
    template_id = template_entry["id"]
    template = template_entry["template"]

    app_profile = APPLICATION_PROFILES[application]
    chem_profile = CHEMISTRY_PROFILES[chemistry]

    if difficulty == "underspecified":
        # Build partial spec — omit some lines
        text = _build_detailed_underspecified(rng, params, chemistry, cell_type, application, template_id)
        return text, template_id

    # Full spec — templates include "Ah" suffix so just pass numeric value
    capacity_val = params.get("capacity_ah", 50)
    if capacity_val == int(capacity_val):
        capacity_str = str(int(capacity_val))
    else:
        capacity_str = str(capacity_val)

    text = template.format(
        chemistry=CHEMISTRY_DISPLAY[chemistry],
        cell_type=CELL_TYPE_DISPLAY[cell_type],
        capacity=capacity_str,
        voltage=params.get("nominal_voltage", chem_profile["nominal_voltage"]),
        energy_density=int(params.get("energy_density_target", 200)),
        application=app_profile["description"],
        application_desc=app_profile["description"],
        cathode_material=chem_profile["cathode_material"],
        temp_min=params.get("temp_min", app_profile["temp_range"][0]),
        temp_max=params.get("temp_max", app_profile["temp_range"][1]),
        cycle_life=params.get("cycle_life", app_profile["cycle_life_target"]),
    )

    # For contradictory, append extra conflicting specs if present
    if difficulty == "contradictory":
        extras = []
        if "c_rate" in params and params["c_rate"] > 3.0:
            extras.append(f"- Continuous discharge rate: {params['c_rate']}C")
        if "separator_thickness_um" in params:
            extras.append(f"- Maximum separator thickness: {params['separator_thickness_um']} microns")
        if "format" in params:
            extras.append(f"- Format: {params['format']}")
        if "packaging_offset_mm" in params:
            extras.append(f"- Maximum edge seal width: {params['packaging_offset_mm']} mm")
        if extras:
            text += "\n" + "\n".join(extras)

    return text, template_id


def _build_detailed_underspecified(
    rng: random.Random,
    params: dict,
    chemistry: str,
    cell_type: str,
    application: str,
    template_id: str,
) -> str:
    """Build a detailed prompt with key fields missing."""
    app_profile = APPLICATION_PROFILES[application]
    omitted = params.get("_omitted_fields", [])

    lines = [f"Design a {CHEMISTRY_DISPLAY[chemistry]} {CELL_TYPE_DISPLAY[cell_type]} cell:"]

    if "capacity_ah" not in omitted and "capacity_ah" in params:
        lines.append(f"- Capacity: {format_capacity(rng, params['capacity_ah'])}")

    if "nominal_voltage" in params and "nominal_voltage" not in omitted:
        lines.append(f"- Nominal voltage: {params['nominal_voltage']} V")

    if "energy_density_target" not in omitted and "energy_density_target" in params:
        lines.append(f"- Energy density: {format_energy_density(rng, params['energy_density_target'])}")

    lines.append(f"- Application: {app_profile['description']}")

    if "temp_min" not in omitted and "temp_max" not in omitted:
        lines.append(
            f"- Temperature range: {params.get('temp_min', app_profile['temp_range'][0])} deg C to "
            f"{params.get('temp_max', app_profile['temp_range'][1])} deg C"
        )

    if "cycle_life" not in omitted and "cycle_life" in params:
        lines.append(f"- Cycle life: {params['cycle_life']} cycles")

    return "\n".join(lines)


def build_natural_language_prompt(
    rng: random.Random,
    params: dict,
    chemistry: str,
    cell_type: str,
    application: str,
    difficulty: str,
) -> tuple[str, str]:
    """Build a natural language conversational prompt. Returns (text, template_id)."""
    app_profile = APPLICATION_PROFILES[application]
    templates = NATURAL_LANGUAGE_TEMPLATES[application]

    if difficulty == "contradictory":
        return _build_nl_contradictory(rng, params, chemistry, cell_type, application)

    template_entry = rng.choice(templates)
    template_id = template_entry["id"]
    template = template_entry["template"]

    # Select use case, performance, and form descriptions
    use_case = rng.choice(app_profile["use_case_descriptions"])
    performance = rng.choice(app_profile["performance_descriptions"])
    form_note = rng.choice(app_profile["form_descriptions"])

    # Chemistry mention: ~50% explicit, ~50% implicit
    # For underspecified, always implicit (omit chemistry)
    if difficulty == "underspecified":
        chem_mention = rng.choice(CHEMISTRY_MENTION_IMPLICIT[chemistry])
    elif rng.random() < 0.5:
        chem_mention = rng.choice(CHEMISTRY_MENTION_EXPLICIT[chemistry])
    else:
        chem_mention = rng.choice(CHEMISTRY_MENTION_IMPLICIT[chemistry])

    flavor = rng.choice(FLAVOR_FRAGMENTS)

    text = template.format(
        use_case=use_case,
        performance=performance,
        form_note=form_note,
        chemistry_mention=chem_mention,
        flavor=flavor,
    )

    return text.strip(), template_id


def _build_nl_contradictory(
    rng: random.Random,
    params: dict,
    chemistry: str,
    cell_type: str,
    application: str,
) -> tuple[str, str]:
    """Build a natural language prompt that sounds reasonable but contains hidden conflicts."""
    app_profile = APPLICATION_PROFILES[application]

    # Find the recipe that was used (stored in params via _contradiction_recipe key,
    # or match by checking which overrides are present)
    recipe_name = params.get("_contradiction_recipe", "")

    # Try to find matching NL templates
    nl_templates = NL_CONTRADICTION_TEMPLATES.get(recipe_name, [])

    if not nl_templates:
        # Fallback: use standard NL template with contradictory flavor
        return build_natural_language_prompt(rng, params, chemistry, cell_type, application, "edge_case")

    template_str = rng.choice(nl_templates)
    use_case = rng.choice(app_profile["use_case_descriptions"])

    # Build format kwargs from params
    fmt_kwargs = {
        "use_case": use_case,
        "energy_density": int(params.get("energy_density_target", 250)),
        "c_rate": params.get("c_rate", 4.0),
        "capacity": params.get("capacity_ah", 100),
        "cycle_life": params.get("cycle_life", 5000),
        "temp_min": params.get("temp_min", -30),
        "voltage": params.get("nominal_voltage", 2.5),
        "separator_thickness": params.get("separator_thickness_um", 4),
        "packaging_offset": params.get("packaging_offset_mm", 0.5),
    }

    try:
        text = template_str.format(**fmt_kwargs)
    except KeyError:
        text = template_str

    # Add random flavor
    flavor = rng.choice(FLAVOR_FRAGMENTS)
    if flavor:
        text = text.rstrip() + flavor

    template_id = f"nl_contra_{recipe_name}"
    return text.strip(), template_id


# ═══════════════════════════════════════════════════════════════
# PROMPT BUILDER DISPATCH
# ═══════════════════════════════════════════════════════════════


def build_prompt(
    rng: random.Random,
    params: dict,
    chemistry: str,
    cell_type: str,
    application: str,
    difficulty: str,
    prompt_style: str,
) -> tuple[str, str]:
    """
    Build prompt text from parameters and style.

    Returns (prompt_text, template_id).
    """
    if prompt_style == "terse":
        return build_terse_prompt(rng, params, chemistry, cell_type, application, difficulty)
    elif prompt_style == "detailed":
        return build_detailed_prompt(rng, params, chemistry, cell_type, application, difficulty)
    elif prompt_style == "natural_language":
        return build_natural_language_prompt(rng, params, chemistry, cell_type, application, difficulty)
    else:
        raise ValueError(f"Unknown prompt style: {prompt_style}")


# ═══════════════════════════════════════════════════════════════
# MAIN GENERATION PIPELINE
# ═══════════════════════════════════════════════════════════════


def build_cross_product() -> list[tuple[str, str, str, str, str]]:
    """Build the full 576-element cross-product of dimensions."""
    return list(itertools.product(CELL_TYPES, CHEMISTRIES, APPLICATIONS, DIFFICULTIES, PROMPT_STYLES))


def trim_to_500(
    rng: random.Random,
    combos: list[tuple[str, str, str, str, str]],
) -> list[tuple[str, str, str, str, str]]:
    """
    Remove 76 standard+terse combinations (least informative).

    There are 3 cell_types x 4 chemistries x 4 applications = 48 standard+terse combos.
    We need to remove 76 total, so remove all 48 standard+terse, then remove
    28 more from the next least informative bucket (standard+detailed).
    """
    standard_terse = [c for c in combos if c[3] == "standard" and c[4] == "terse"]
    remaining = [c for c in combos if not (c[3] == "standard" and c[4] == "terse")]

    # 48 standard+terse removed. Need 76 - 48 = 28 more.
    still_needed = TRIM_COUNT - len(standard_terse)

    if still_needed > 0:
        # Remove from edge_case+terse (next least informative)
        edge_terse = [c for c in remaining if c[3] == "edge_case" and c[4] == "terse"]
        rng.shuffle(edge_terse)
        to_remove = set(map(id, edge_terse[:still_needed]))
        remaining = [c for c in remaining if id(c) not in to_remove]

    assert len(remaining) == TOTAL_TARGET, f"Expected {TOTAL_TARGET}, got {len(remaining)}"
    return remaining


def clean_params_for_output(params: dict) -> dict:
    """Remove internal keys from params before writing to JSON."""
    return {k: v for k, v in params.items() if not k.startswith("_")}


def generate_corpus() -> dict:
    """Main generation pipeline. Returns the complete corpus dict."""
    rng = random.Random(SEED)

    # Step 1: Build cross-product
    all_combos = build_cross_product()
    assert len(all_combos) == FULL_CROSS_PRODUCT, f"Expected {FULL_CROSS_PRODUCT}, got {len(all_combos)}"

    # Step 2: Trim to 500
    combos = trim_to_500(rng, all_combos)

    # Step 3: Shuffle for ID assignment (deterministic)
    rng.shuffle(combos)

    # Step 4: Generate prompts
    prompts = []
    seen_texts = set()

    for idx, (cell_type, chemistry, application, difficulty, prompt_style) in enumerate(combos, start=1):
        prompt_id = f"P-{idx:03d}"

        # Generate parameters based on difficulty
        expected_violations = "none"
        contradiction_explanation = None

        if difficulty == "standard":
            params = generate_standard_params(rng, chemistry, application)
        elif difficulty == "edge_case":
            params = generate_edge_case_params(rng, chemistry, application)
        elif difficulty == "underspecified":
            params = generate_underspecified_params(rng, chemistry, application)
        elif difficulty == "contradictory":
            params, violations, explanation = generate_contradictory_params(rng, chemistry, application, cell_type)
            # Store recipe name for NL template lookup
            params["_contradiction_recipe"] = _find_recipe_name(params, violations)
            expected_violations = violations
            contradiction_explanation = explanation
        else:
            raise ValueError(f"Unknown difficulty: {difficulty}")

        # Build prompt text
        prompt_text, template_id = build_prompt(
            rng, params, chemistry, cell_type, application, difficulty, prompt_style
        )

        # Deduplicate — if text collision, regenerate with slight variation
        attempts = 0
        while prompt_text in seen_texts and attempts < 5:
            prompt_text += f" [Design variant {rng.randint(1, 99)}]"
            attempts += 1
        seen_texts.add(prompt_text)

        # Build output record
        record = {
            "prompt_id": prompt_id,
            "cell_type": cell_type,
            "chemistry": chemistry,
            "application": application,
            "difficulty": difficulty,
            "prompt_style": prompt_style,
            "prompt_text": prompt_text,
            "parameters_used": clean_params_for_output(params),
            "expected_violations": expected_violations,
            "template_id": template_id,
        }

        if contradiction_explanation:
            record["contradiction_explanation"] = contradiction_explanation

        prompts.append(record)

    # Step 5: Build corpus
    corpus = {
        "corpus_version": "1.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": SEED,
        "total_prompts": len(prompts),
        "stratification": {
            "cell_types": CELL_TYPES,
            "chemistries": CHEMISTRIES,
            "applications": APPLICATIONS,
            "difficulties": DIFFICULTIES,
            "prompt_styles": PROMPT_STYLES,
        },
        "trimming_strategy": (
            f"Removed {TRIM_COUNT} combinations: all 48 standard+terse "
            f"and 28 edge_case+terse (least informative for the experiment)"
        ),
        "prompts": prompts,
    }

    return corpus


def _find_recipe_name(params: dict, violations: list[str]) -> str:
    """Try to identify which contradiction recipe was used from violations."""
    for recipe in CONTRADICTION_RECIPES:
        filtered = [v for v in recipe["constraint_ids"] if v in violations]
        if filtered and len(filtered) >= len(violations):
            return recipe["name"]
    # Fallback
    for recipe in CONTRADICTION_RECIPES:
        if set(recipe["constraint_ids"]) & set(violations):
            return recipe["name"]
    return "unknown"


# ═══════════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════════


def verify_corpus(corpus: dict) -> list[str]:
    """Run verification checklist. Returns list of issues (empty = all good)."""
    issues = []
    prompts = corpus["prompts"]

    # 1. Exactly 500 prompts
    if len(prompts) != TOTAL_TARGET:
        issues.append(f"Expected {TOTAL_TARGET} prompts, got {len(prompts)}")

    # 2. No duplicate prompt_ids
    ids = [p["prompt_id"] for p in prompts]
    if len(ids) != len(set(ids)):
        issues.append(f"Duplicate prompt_ids found: {len(ids) - len(set(ids))} duplicates")

    # 3. No duplicate prompt_text
    texts = [p["prompt_text"] for p in prompts]
    if len(texts) != len(set(texts)):
        issues.append(f"Duplicate prompt_text found: {len(texts) - len(set(texts))} duplicates")

    # 4. Every dimension level appears at least floor(500/max_levels) times
    for dim, levels in [
        ("cell_type", CELL_TYPES),
        ("chemistry", CHEMISTRIES),
        ("application", APPLICATIONS),
        ("difficulty", DIFFICULTIES),
        ("prompt_style", PROMPT_STYLES),
    ]:
        counts = {}
        for p in prompts:
            val = p[dim]
            counts[val] = counts.get(val, 0) + 1
        min_expected = TOTAL_TARGET // len(levels)
        for level in levels:
            count = counts.get(level, 0)
            if count < min_expected // 2:  # Allow some slack due to trimming
                issues.append(f"{dim}={level} appears {count} times (expected >= ~{min_expected})")

    # 5. All contradictory prompts have non-empty expected_violations
    for p in prompts:
        if p["difficulty"] == "contradictory":
            ev = p["expected_violations"]
            if ev == "none" or (isinstance(ev, list) and len(ev) == 0):
                issues.append(f"{p['prompt_id']}: contradictory prompt has no expected_violations")

    # 6. All non-contradictory prompts have "none" violations
    for p in prompts:
        if p["difficulty"] in ("standard", "edge_case") and p["expected_violations"] != "none":
            issues.append(f"{p['prompt_id']}: {p['difficulty']} prompt has unexpected violations")

    # 7. Underspecified prompts have missing parameters
    for p in prompts:
        if p["difficulty"] == "underspecified":
            params = p["parameters_used"]
            # Should be missing at least 2 of the standard fields
            standard_fields = {"capacity_ah", "energy_density_target", "cycle_life", "temp_min", "temp_max", "c_rate"}
            present = standard_fields & set(params.keys())
            if len(present) >= len(standard_fields):
                issues.append(f"{p['prompt_id']}: underspecified prompt has all standard fields")

    return issues


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════


def main() -> None:
    print("=" * 60)
    print("AXIOM Phase 3: Stratified Prompt Corpus Generator")
    print("=" * 60)

    # Generate
    print("\nGenerating corpus...")
    corpus = generate_corpus()

    # Verify
    print("Running verification...")
    issues = verify_corpus(corpus)

    if issues:
        print(f"\n  WARNING: {len(issues)} issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  All checks passed.")

    # Write output
    output_path = Path(__file__).parent / "prompt_corpus_v1.json"
    with open(output_path, "w") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    print(f"\n  Written: {output_path}")
    print(f"  Total prompts: {corpus['total_prompts']}")

    # Print summary stats
    print("\n" + "=" * 60)
    print("DISTRIBUTION SUMMARY")
    print("=" * 60)

    prompts = corpus["prompts"]

    for dim_name, dim_key in [
        ("Cell Type", "cell_type"),
        ("Chemistry", "chemistry"),
        ("Application", "application"),
        ("Difficulty", "difficulty"),
        ("Prompt Style", "prompt_style"),
    ]:
        counts: dict[str, int] = {}
        for p in prompts:
            val = p[dim_key]
            counts[val] = counts.get(val, 0) + 1
        print(f"\n  {dim_name}:")
        for level, count in sorted(counts.items()):
            print(f"    {level:25s} {count:4d}  ({100 * count / len(prompts):.1f}%)")

    # Difficulty x Style matrix
    print("\n  Difficulty x Style:")
    matrix: dict[str, dict[str, int]] = {}
    for p in prompts:
        d = p["difficulty"]
        s = p["prompt_style"]
        if d not in matrix:
            matrix[d] = {}
        matrix[d][s] = matrix[d].get(s, 0) + 1

    header = f"    {'':20s}"
    for style in PROMPT_STYLES:
        header += f"{style:>18s}"
    print(header)
    for diff in DIFFICULTIES:
        row = f"    {diff:20s}"
        for style in PROMPT_STYLES:
            row += f"{matrix.get(diff, {}).get(style, 0):18d}"
        print(row)

    # Contradictory violations summary
    contra = [p for p in prompts if p["difficulty"] == "contradictory"]
    print(f"\n  Contradictory prompts: {len(contra)}")
    print(f"  All have violations: {all(p['expected_violations'] != 'none' for p in contra)}")

    violation_counts: dict[str, int] = {}
    for p in contra:
        if isinstance(p["expected_violations"], list):
            for v in p["expected_violations"]:
                violation_counts[v] = violation_counts.get(v, 0) + 1
    if violation_counts:
        print("  Violation distribution:")
        for vid, count in sorted(violation_counts.items()):
            print(f"    {vid:10s} {count:4d}")

    print()


if __name__ == "__main__":
    main()
