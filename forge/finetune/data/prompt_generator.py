#!/usr/bin/env python3
"""
Stage 2 Part A: Prompt Generator for Fine-Tuning Dataset.

For each valid cell config from Stage 1, generates a natural language
design request that would plausibly produce that config. Includes
decontamination check against Corpus A and B evaluation prompts.

Usage:
    python -m forge.finetune.data.prompt_generator \
        --input forge/finetune/data/output/all_configs.jsonl \
        --corpus-a forge/experiments/prompt_corpus_v1.json \
        --corpus-b forge/experiments/corpus_b/prompt_corpus_b.json \
        --output forge/finetune/data/output/configs_with_prompts.jsonl \
        --seed 42 --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application context pools (avoid exact Corpus A/B phrasing)
# ---------------------------------------------------------------------------

APP_CONTEXTS = {
    "ev_traction": [
        "EV battery pack", "electric vehicle traction system",
        "long-range passenger EV", "electric delivery truck",
        "PHEV powertrain", "high-performance electric car",
        "city EV platform", "electric bus fleet",
        "light electric vehicle", "EV module integration",
    ],
    "consumer_electronics": [
        "smartphone", "laptop battery", "tablet device",
        "wearable electronics", "portable speaker",
        "e-reader device", "handheld gaming device",
        "wireless headphones", "portable medical device",
        "compact IoT sensor",
    ],
    "grid_storage": [
        "residential solar storage", "commercial peak shaving",
        "grid-scale ESS", "backup power system",
        "microgrid installation", "frequency regulation unit",
        "behind-the-meter storage", "renewable integration project",
        "industrial UPS system", "island grid stabilization",
    ],
    "power_tools": [
        "cordless drill", "impact driver",
        "circular saw battery", "angle grinder pack",
        "reciprocating saw", "leaf blower battery",
        "construction site tools", "professional tool platform",
        "portable welder pack", "garden tool system",
    ],
}

CHEMISTRY_MENTIONS = {
    "NMC811": ["NMC811", "NMC-811", "high-nickel NMC", "811 cathode", "nickel-rich NMC"],
    "NMC622": ["NMC622", "NMC-622", "622 chemistry", "mid-nickel NMC"],
    "NMC111": ["NMC111", "NMC-111", "balanced NMC", "111 chemistry"],
    "LFP": ["LFP", "iron phosphate", "lithium iron phosphate", "LiFePO4"],
    "NCA": ["NCA", "nickel-cobalt-aluminum", "NCA chemistry"],
}

CELL_TYPE_MENTIONS = {
    "prismatic": ["prismatic", "prismatic cell"],
    "pouch": ["pouch", "pouch cell"],
    "cylindrical": ["cylindrical", "cylindrical cell"],
}

# Cylindrical format mentions
CYL_FORMAT_MENTIONS = {
    "18650": ["18650", "18650 format", "standard 18650"],
    "21700": ["21700", "21700 format", "2170 cell"],
    "4680": ["4680", "46mm format", "large-format cylindrical"],
    "custom": ["custom cylindrical", "non-standard cylindrical"],
}

# Phrases for parameter approximation
APPROX = ["around", "approximately", "about", "roughly", "targeting", "in the range of", "~"]

# Filler context (occasional)
FILLER = [
    "", "", "", "",  # 40% no filler
    "Our team is evaluating options. ",
    "For a prototype build. ",
    "This is for an upcoming project. ",
    "Preliminary design phase. ",
    "Need a starting point to iterate from. ",
    "Working with a tight timeline. ",
]


# ---------------------------------------------------------------------------
# Parameter extraction helpers
# ---------------------------------------------------------------------------

def _get_key_params(config: dict, cell_type: str) -> dict[str, Any]:
    """Extract the key disclosable parameters from a config."""
    cfg = config.get("config", config)
    echem = cfg.get("electrochemistry", {})
    cat = echem.get("cathode", {})
    ano = echem.get("anode", {})
    sep = echem.get("separator", {})

    params: dict[str, Any] = {
        "chemistry": cat.get("material_name", ""),
        "cathode_loading": cat.get("loading_mg_cm2"),
        "cathode_porosity": cat.get("porosity_pct"),
        "anode_loading": ano.get("loading_mg_cm2"),
        "np_ratio": ano.get("np_ratio"),
        "separator_thickness": sep.get("thickness_um"),
        "separator_porosity": sep.get("porosity_pct"),
    }

    if cell_type == "prismatic":
        env = cfg.get("envelope", {}).get("external", {})
        sc = cfg.get("stack_config", {})
        params["cell_height_mm"] = env.get("cell_height_mm")
        params["cell_width_mm"] = env.get("cell_width_mm")
        params["cell_thickness_mm"] = env.get("cell_thickness_mm")
        params["num_stacks"] = sc.get("architecture", {}).get("num_stacks")
        params["electrode_pairs"] = sc.get("architecture", {}).get("electrode_pairs_per_stack")

    elif cell_type == "pouch":
        geo = cfg.get("geometry", {})
        sc = cfg.get("stack_config", {})
        params["cathode_height_mm"] = geo.get("cathode_height_mm")
        params["cathode_width_mm"] = geo.get("cathode_width_mm")
        params["electrode_pairs"] = sc.get("electrode_pairs_per_stack")

    elif cell_type == "cylindrical":
        geo = cfg.get("geometry", {})
        params["diameter_mm"] = geo.get("diameter_mm")
        params["length_mm"] = geo.get("length_mm")
        params["format"] = cfg.get("_meta", {}).get("format", "custom")

    return params


# ---------------------------------------------------------------------------
# Prompt builders by style
# ---------------------------------------------------------------------------

def _build_terse(rng: np.random.Generator, cell_type: str, chemistry: str,
                 params: dict, disclosed: list[str]) -> str:
    """Build a terse one-liner prompt."""
    ct = rng.choice(CELL_TYPE_MENTIONS[cell_type])
    chem = rng.choice(CHEMISTRY_MENTIONS.get(chemistry, [chemistry]))
    disclosed.extend(["cell_type", "chemistry"])

    parts = [f"{ct} {chem}"]

    # Optionally add a dimension or format
    if cell_type == "cylindrical" and params.get("format", "custom") != "custom":
        if rng.random() < 0.7:
            fmt = rng.choice(CYL_FORMAT_MENTIONS.get(params["format"], [params["format"]]))
            parts = [fmt]  # Replace with format mention
            disclosed.append("format")

    # Optionally add a dimension
    dim_added = False
    if cell_type == "prismatic" and rng.random() < 0.5:
        h = params.get("cell_height_mm")
        if h:
            parts.append(f"{rng.choice(APPROX)} {round(h)}mm tall")
            disclosed.append("cell_height_mm")
            dim_added = True
    elif cell_type == "pouch" and rng.random() < 0.4:
        h = params.get("cathode_height_mm")
        if h:
            parts.append(f"{rng.choice(APPROX)} {round(h)}mm cathode")
            disclosed.append("cathode_height_mm")
            dim_added = True

    # Application context
    app = _pick_application(rng, chemistry, cell_type)
    if rng.random() < 0.7:
        parts.append(f"for {app}")
        disclosed.append("application")

    return ", ".join(parts) + "."


def _build_detailed(rng: np.random.Generator, cell_type: str, chemistry: str,
                    params: dict, disclosed: list[str]) -> str:
    """Build a detailed multi-line prompt with specs."""
    ct = rng.choice(CELL_TYPE_MENTIONS[cell_type])
    chem = rng.choice(CHEMISTRY_MENTIONS.get(chemistry, [chemistry]))
    app = _pick_application(rng, chemistry, cell_type)
    disclosed.extend(["cell_type", "chemistry", "application"])

    lines = [f"Design a {chem} {ct} for {app}."]
    lines.append("")
    lines.append("Specifications:")

    # Disclose 4-8 parameters
    spec_pool: list[tuple[str, str]] = []

    if cell_type == "prismatic":
        h = params.get("cell_height_mm")
        w = params.get("cell_width_mm")
        t = params.get("cell_thickness_mm")
        if h: spec_pool.append(("cell_height_mm", f"Height: {rng.choice(APPROX)} {round(h)} mm"))
        if w: spec_pool.append(("cell_width_mm", f"Width: {rng.choice(APPROX)} {round(w)} mm"))
        if t: spec_pool.append(("cell_thickness_mm", f"Thickness: {rng.choice(APPROX)} {round(t)} mm"))
    elif cell_type == "pouch":
        h = params.get("cathode_height_mm")
        w = params.get("cathode_width_mm")
        if h: spec_pool.append(("cathode_height_mm", f"Cathode height: {rng.choice(APPROX)} {round(h)} mm"))
        if w: spec_pool.append(("cathode_width_mm", f"Cathode width: {rng.choice(APPROX)} {round(w)} mm"))
    elif cell_type == "cylindrical":
        fmt = params.get("format", "custom")
        d = params.get("diameter_mm")
        if fmt != "custom":
            spec_pool.append(("format", f"Format: {fmt}"))
        elif d:
            spec_pool.append(("diameter_mm", f"Diameter: {rng.choice(APPROX)} {round(d)} mm"))

    # Common specs
    cl = params.get("cathode_loading")
    if cl: spec_pool.append(("cathode_loading", f"Cathode loading: {rng.choice(APPROX)} {round(cl, 1)} mg/cm2"))
    st = params.get("separator_thickness")
    if st: spec_pool.append(("separator_thickness", f"Separator: {round(st)} um"))
    ep = params.get("electrode_pairs")
    if ep: spec_pool.append(("electrode_pairs", f"Electrode pairs: {ep}"))

    # Select 3-6 specs to disclose
    n_specs = min(len(spec_pool), int(rng.integers(3, 7)))
    rng.shuffle(spec_pool)
    for key, text in spec_pool[:n_specs]:
        lines.append(f"- {text}")
        disclosed.append(key)

    return "\n".join(lines)


def _build_natural(rng: np.random.Generator, cell_type: str, chemistry: str,
                   params: dict, disclosed: list[str]) -> str:
    """Build a natural language conversational prompt."""
    ct = rng.choice(CELL_TYPE_MENTIONS[cell_type])
    chem = rng.choice(CHEMISTRY_MENTIONS.get(chemistry, [chemistry]))
    app = _pick_application(rng, chemistry, cell_type)
    filler = rng.choice(FILLER)
    disclosed.extend(["cell_type", "chemistry", "application"])

    # Opening
    openers = [
        f"Looking for a {ct} design using {chem} for {app}.",
        f"We need a {chem} {ct} for our {app} project.",
        f"Working on a {app} application, need a {ct} with {chem} chemistry.",
        f"Can you put together a {ct} {chem} cell? It's for {app}.",
        f"Need to spec out a {chem} {ct} for {app} use.",
    ]
    text = rng.choice(openers) + " "

    if filler:
        text += filler

    # Add 1-3 parameter mentions in conversational form
    mentions: list[tuple[str, str]] = []

    if cell_type == "prismatic":
        h = params.get("cell_height_mm")
        if h and rng.random() < 0.5:
            mentions.append(("cell_height_mm", f"Something {rng.choice(APPROX)} {round(h)}mm tall"))
        w = params.get("cell_width_mm")
        if w and rng.random() < 0.3:
            mentions.append(("cell_width_mm", f"width {rng.choice(APPROX)} {round(w)}mm"))
    elif cell_type == "pouch":
        h = params.get("cathode_height_mm")
        if h and rng.random() < 0.4:
            mentions.append(("cathode_height_mm", f"cathode sheet {rng.choice(APPROX)} {round(h)}mm"))
    elif cell_type == "cylindrical":
        fmt = params.get("format", "custom")
        if fmt != "custom" and rng.random() < 0.6:
            mentions.append(("format", f"{fmt} form factor"))

    # Priority/constraint mentions
    priorities = [
        "Energy density is important.",
        "Safety is the top priority.",
        "Cost needs to be competitive.",
        "Good cycle life is essential.",
        "Needs to handle fast charging.",
        "Thermal management is a concern.",
        "Weight should be minimized.",
        "Compact packaging preferred.",
    ]
    n_priorities = int(rng.integers(1, 3))
    rng.shuffle(priorities)

    for key, mention in mentions[:2]:
        text += mention + ". "
        disclosed.append(key)

    for p in priorities[:n_priorities]:
        text += p + " "

    return text.strip()


def _pick_application(rng: np.random.Generator, chemistry: str, cell_type: str) -> str:
    """Pick a plausible application context weighted by chemistry."""
    # Weight toward automotive for NMC, grid for LFP
    if chemistry in ("NMC811", "NMC622", "NCA"):
        weights = [0.50, 0.15, 0.15, 0.20]
    elif chemistry == "LFP":
        weights = [0.25, 0.10, 0.50, 0.15]
    else:
        weights = [0.30, 0.20, 0.30, 0.20]

    apps = list(APP_CONTEXTS.keys())
    app_key = rng.choice(apps, p=weights)
    return rng.choice(APP_CONTEXTS[app_key])


# ---------------------------------------------------------------------------
# Decontamination
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set[str]:
    """Simple whitespace + lowercase tokenizer."""
    return set(text.lower().split())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_eval_prompts(corpus_a_path: Path, corpus_b_path: Path) -> list[set[str]]:
    """Load and tokenize all evaluation prompts for decontamination."""
    tokens_list: list[set[str]] = []

    for path in [corpus_a_path, corpus_b_path]:
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        for p in data.get("prompts", []):
            tokens_list.append(_tokenize(p.get("prompt_text", "")))

    logger.info("Loaded %d evaluation prompts for decontamination", len(tokens_list))
    return tokens_list


def check_contamination(prompt: str, eval_tokens: list[set[str]], threshold: float = 0.6) -> float:
    """Return max Jaccard similarity to any evaluation prompt."""
    pt = _tokenize(prompt)
    return max((_jaccard(pt, et) for et in eval_tokens), default=0.0)


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate_prompts(
    input_path: Path,
    corpus_a_path: Path,
    corpus_b_path: Path,
    output_path: Path,
    seed: int = 42,
    verbose: bool = False,
) -> dict:
    """Generate prompts for all configs and write to JSONL."""
    rng = np.random.default_rng(seed)
    eval_tokens = load_eval_prompts(corpus_a_path, corpus_b_path)

    style_choices = ["terse", "detailed", "natural_language"]
    style_weights = [0.33, 0.33, 0.34]

    stats = {"total": 0, "flagged": 0, "regenerated": 0, "styles": {s: 0 for s in style_choices}}

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(input_path) as fin, open(output_path, "w") as fout:
        for line_no, line in enumerate(fin, 1):
            record = json.loads(line.strip())
            cell_type = record["cell_type"]
            chemistry = record["chemistry"]
            params = _get_key_params(record, cell_type)

            # Choose style
            style = rng.choice(style_choices, p=style_weights)

            # Generate prompt (with retry for decontamination + minimum length)
            MIN_PROMPT_LENGTH = 40
            max_retries = 8
            for attempt in range(max_retries):
                disclosed: list[str] = []

                if style == "terse":
                    prompt = _build_terse(rng, cell_type, chemistry, params, disclosed)
                elif style == "detailed":
                    prompt = _build_detailed(rng, cell_type, chemistry, params, disclosed)
                else:
                    prompt = _build_natural(rng, cell_type, chemistry, params, disclosed)

                # Minimum length check — regenerate with more disclosure
                if len(prompt) < MIN_PROMPT_LENGTH:
                    # Bump to a more verbose style
                    style = "detailed" if style == "terse" else "natural_language"
                    stats["regenerated"] += 1
                    continue

                # Decontamination check
                max_sim = check_contamination(prompt, eval_tokens)
                if max_sim < 0.6:
                    break
                stats["flagged"] += 1
                if attempt < max_retries - 1:
                    stats["regenerated"] += 1
                    style = rng.choice(style_choices, p=style_weights)

            # Compute withheld params
            all_param_keys = set(params.keys()) - {"chemistry"}
            withheld = sorted(all_param_keys - set(disclosed))

            record["prompt"] = prompt
            record["prompt_style"] = style
            record["prompt_params_disclosed"] = sorted(set(disclosed))
            record["prompt_params_withheld"] = withheld

            fout.write(json.dumps(record, default=str) + "\n")

            stats["total"] += 1
            stats["styles"][style] += 1

            if verbose and stats["total"] % 500 == 0:
                print(f"  Generated {stats['total']} prompts "
                      f"(flagged: {stats['flagged']}, regen: {stats['regenerated']})")

    if verbose:
        print(f"\n=== COMPLETE: {stats['total']} prompts generated ===")
        print(f"Styles: {stats['styles']}")
        print(f"Decontamination: {stats['flagged']} flagged, {stats['regenerated']} regenerated")
        print(f"Output: {output_path}")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate prompts for fine-tuning configs")
    parser.add_argument("--input", required=True, type=str)
    parser.add_argument("--corpus-a", required=True, type=str)
    parser.add_argument("--corpus-b", required=True, type=str)
    parser.add_argument("--output", required=True, type=str)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    generate_prompts(
        input_path=Path(args.input),
        corpus_a_path=Path(args.corpus_a),
        corpus_b_path=Path(args.corpus_b),
        output_path=Path(args.output),
        seed=args.seed,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
