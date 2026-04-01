#!/usr/bin/env python3
"""
Corpus B Generator — 250-prompt controlled realism corpus.

Generates 240 core prompts (5 roughness families × 48 canonical combos)
plus 10 hand-written sentinel prompts.

Uses the frozen seed bank (seed_bank.json v1.1-FROZEN) with controlled
transformations to expand 45 seeds into 240 varied prompts.

Usage (from FORGE root):
    .venv/bin/python3 forge/experiments/corpus_b/generate_corpus_b.py

Output:
    forge/experiments/corpus_b/prompt_corpus_b.json
    forge/experiments/corpus_b/generation_log.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from random import Random

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
GENERATOR_VERSION = "1.0"
OUTPUT_DIR = Path(__file__).resolve().parent
SEED_BANK_PATH = OUTPUT_DIR / "seed_bank.json"

CELL_TYPES = ["pouch", "prismatic", "cylindrical"]
CHEMISTRIES = ["NMC-111", "NMC-622", "NMC-811", "LFP"]
APPLICATIONS = ["ev_traction", "consumer_electronics", "grid_storage", "power_tools"]

FAMILIES = ["B1", "B2", "B3", "B4", "B5"]
SURFACE_STYLES = ["note", "conversation", "mixed_fragment"]

# Map family+style to seed bank key
def _seed_key(family: str, style: str) -> str:
    style_map = {"note": "note", "conversation": "conversation", "mixed_fragment": "mixed"}
    return f"{family}_{style_map[style]}"


# ---------------------------------------------------------------------------
# Transforms — the engine that makes seeds feel varied
# ---------------------------------------------------------------------------

class PromptTransformer:
    """Applies controlled transformations to seed templates."""

    def __init__(self, rng: Random, seed_bank: dict):
        self.rng = rng
        self.vars = seed_bank["template_variables"]
        # Typo budget: allow at most ~12% of 240 core prompts = ~29 typos
        self._typo_budget = 29

    def render(self, seed: dict, cell_type: str, chemistry: str,
               application: str, transform_level: int) -> tuple[str, dict]:
        """Render a seed into a final prompt with provenance.

        Args:
            seed: Seed dict from seed bank
            cell_type, chemistry, application: Canonical values
            transform_level: 0=minimal, 1=moderate, 2=heavy transforms

        Returns:
            (prompt_text, provenance_dict)
        """
        text = seed["text"]
        transforms_applied = []

        # --- Step 1: Core variable substitution ---
        # ALWAYS use a human-readable form. Never leave raw underscored names.
        # Casual variants add extra informality on top.
        app_readable = {
            "ev_traction": "EV traction",
            "consumer_electronics": "consumer electronics",
            "grid_storage": "grid storage",
            "power_tools": "power tools",
        }
        # Start with readable baseline, then sometimes swap to casual
        app_str = app_readable.get(application, application)
        if self.rng.random() < 0.5:
            casual_opts = self.vars["application_casual"].get(application, [app_str])
            app_str = self.rng.choice(casual_opts)
            transforms_applied.append(f"casual_application:{app_str}")

        chem_str = chemistry
        if self.rng.random() < 0.5:
            casual_opts = self.vars["chemistry_casual"].get(chemistry, [chemistry])
            chem_str = self.rng.choice(casual_opts)
            if chem_str != chemistry:
                transforms_applied.append(f"casual_chemistry:{chem_str}")

        text = text.replace("{cell_type}", cell_type)
        text = text.replace("{chemistry}", chem_str)
        text = text.replace("{application}", app_str)

        # --- Step 2: B3-specific trap variables ---
        if "{dim_hint}" in text:
            opts = self.vars["dim_hint"].get(cell_type, ["standard size"])
            text = text.replace("{dim_hint}", self.rng.choice(opts))

        if "{dim_unit_trap}" in text:
            text = text.replace("{dim_unit_trap}", self.rng.choice(self.vars["dim_unit_trap"]))

        if "{sep_trap}" in text:
            text = text.replace("{sep_trap}", self.rng.choice(self.vars["sep_trap"]))

        if "{capacity_trap}" in text:
            opts = self.vars["capacity_trap"].get(application, ["moderate"])
            text = text.replace("{capacity_trap}", self.rng.choice(opts))

        if "{loading_trap}" in text:
            text = text.replace("{loading_trap}", self.rng.choice(self.vars["loading_trap"]))

        if "{scale_trap_dim}" in text:
            opts = self.vars["scale_trap_dim"].get(cell_type, ["standard size"])
            text = text.replace("{scale_trap_dim}", self.rng.choice(opts))

        if "{scale_trap_cap}" in text:
            opts = self.vars["scale_trap_cap"].get(application, ["moderate"])
            text = text.replace("{scale_trap_cap}", self.rng.choice(opts))

        if "{thickness_trap}" in text:
            text = text.replace("{thickness_trap}", self.rng.choice(self.vars["thickness_trap"]))

        if "{wall_trap}" in text:
            text = text.replace("{wall_trap}", self.rng.choice(self.vars["wall_trap"]))

        # --- Step 3: B5 stale reference variables ---
        if "{stale_ref}" in text:
            text = text.replace("{stale_ref}", self.rng.choice(self.vars["stale_ref"]))

        if "{stale_cap}" in text:
            text = text.replace("{stale_cap}", self.rng.choice(self.vars["stale_cap"]))

        # --- Step 4: Surface perturbations (based on transform_level) ---
        if transform_level >= 1:
            text = self._apply_clause_reorder(text, transforms_applied)
            text = self._apply_connector_drop(text, transforms_applied)

        if transform_level >= 2:
            # Typo budget: at most 12% of prompts get a typo (tracked externally)
            if self._typo_budget > 0 and self.rng.random() < 0.35:
                text = self._apply_light_typo(text, transforms_applied)
                if any("typo:" in t for t in transforms_applied):
                    self._typo_budget -= 1
            text = self._apply_punctuation_drop(text, transforms_applied)

        # --- Step 5: Post-render cleanup ---
        text = self._dedup_adjacent_words(text)
        text = re.sub(r"  +", " ", text)
        text = re.sub(r" +\n", "\n", text)
        text = text.strip()

        provenance = {
            "seed_exemplar_id": seed["id"],
            "generator_version": GENERATOR_VERSION,
            "rng_seed": SEED,
            "transform_level": transform_level,
            "applied_transforms": transforms_applied,
            "casual_chemistry_used": chem_str != chemistry,
            "casual_application_used": app_str != app_readable.get(application, application),
        }

        return text, provenance

    def _apply_clause_reorder(self, text: str, log: list) -> str:
        """Occasionally reorder clauses in a sentence."""
        if self.rng.random() > 0.35:
            return text
        # Split on period-space or newline, reorder first two clauses
        parts = re.split(r"(?<=\.)\s+", text, maxsplit=2)
        if len(parts) >= 2 and len(parts[0]) < 80:
            parts[0], parts[1] = parts[1], parts[0]
            log.append("clause_reorder")
            return " ".join(parts)
        return text

    def _apply_connector_drop(self, text: str, log: list) -> str:
        """Drop connecting words to make text more clipped."""
        if self.rng.random() > 0.4:
            return text
        connectors = [
            (r"\bPlease\s+", ""),
            (r"\bWe need\s+", "Need "),
            (r"\bI need\s+", "Need "),
            (r"\bCan you\s+", ""),
            (r"\bDesign a\s+", ""),
            (r"\bthat is\s+", ""),
            (r"\bwhich is\s+", ""),
            (r"\bfor the\s+", "for "),
            (r"\bof the\s+", "of "),
        ]
        pattern, repl = self.rng.choice(connectors)
        new_text = re.sub(pattern, repl, text, count=1)
        if new_text != text:
            log.append(f"connector_drop:{pattern}")
            return new_text
        return text

    def _apply_light_typo(self, text: str, log: list) -> str:
        """Inject one light typo — lowercase chemistry, missing letter, etc."""
        if self.rng.random() > 0.25:
            return text
        typo_type = self.rng.choice(["lowercase_chem", "missing_letter", "double_letter"])

        if typo_type == "lowercase_chem":
            for chem in ["NMC-111", "NMC-622", "NMC-811", "NMC111", "NMC622", "NMC811"]:
                if chem in text:
                    text = text.replace(chem, chem.lower(), 1)
                    log.append(f"typo:lowercase_{chem}")
                    return text

        if typo_type == "missing_letter":
            words = text.split()
            candidates = [i for i, w in enumerate(words) if len(w) > 5 and w.isalpha()]
            if candidates:
                idx = self.rng.choice(candidates)
                w = words[idx]
                pos = self.rng.randint(1, len(w) - 2)
                words[idx] = w[:pos] + w[pos + 1:]
                log.append(f"typo:missing_letter:{w}->{words[idx]}")
                return " ".join(words)

        if typo_type == "double_letter":
            words = text.split()
            candidates = [i for i, w in enumerate(words) if len(w) > 4 and w.isalpha()]
            if candidates:
                idx = self.rng.choice(candidates)
                w = words[idx]
                pos = self.rng.randint(1, len(w) - 2)
                words[idx] = w[:pos] + w[pos] + w[pos:]
                log.append(f"typo:double_letter:{w}->{words[idx]}")
                return " ".join(words)

        return text

    def _apply_punctuation_drop(self, text: str, log: list) -> str:
        """Drop a period or comma to make text feel rushed."""
        if self.rng.random() > 0.3:
            return text
        # Drop one period (not the last one)
        periods = [m.start() for m in re.finditer(r"\.\s", text)]
        if periods:
            pos = self.rng.choice(periods)
            text = text[:pos] + text[pos + 1:]
            log.append("punctuation_drop:period")
        return text

    def inject_broken_fragment(self, text: str, log: list) -> str:
        """For B5 mixed: occasionally inject a truly broken fragment."""
        if self.rng.random() > 0.3:
            return text
        fragments = [
            "\n[link: confluence.internal/cell-design/... (broken)]",
            "\n// TODO: check with thermal team",
            "\nRef: see attachment (not included)",
            "\n(copied from Slack — may be incomplete)",
            "\nCapacity: [FIELD MISSING]",
            "\nOld target: ???Ah (check with PM)",
        ]
        frag = self.rng.choice(fragments)
        log.append(f"broken_fragment:{frag.strip()}")
        return text + frag

    @staticmethod
    def _dedup_adjacent_words(text: str) -> str:
        """Remove adjacent duplicate words/phrases that look generator-made.

        Catches: 'thick thick', 'coat coat', 'around about', 'sep sep', etc.
        Preserves intentional repetition in structured content (bullets, headers).
        """
        # Remove exact adjacent duplicate words (case-insensitive)
        text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
        # Remove 'around about' / 'about around' hedger doubling
        text = re.sub(r"\baround about\b", "around", text, flags=re.IGNORECASE)
        text = re.sub(r"\babout around\b", "about", text, flags=re.IGNORECASE)
        return text


# ---------------------------------------------------------------------------
# Difficulty inference
# ---------------------------------------------------------------------------

def _infer_difficulty(seed: dict, transform_level: int) -> str:
    """Infer difficulty tag from seed + transform level."""
    base = seed.get("difficulty_tag", "D2")
    # Transform level can bump difficulty
    if transform_level >= 2 and base == "D1":
        return "D2"
    if transform_level >= 2 and base == "D2":
        return "D3"
    return base


# ---------------------------------------------------------------------------
# Failure mode inference
# ---------------------------------------------------------------------------

def _infer_failure_modes(family: str, seed: dict) -> tuple[str, str | None]:
    """Infer expected failure modes from family and seed metadata.

    Uses seed-level primary_roughness for precision, with family as fallback.
    Distinguishes unit_confusion vs scale_confusion, and
    parse_contamination vs stale_reference_salience.
    """
    # Primary: prefer seed-level roughness type over family default
    primary_roughness = seed.get("primary_roughness", "")
    roughness_to_failure = {
        "incomplete_shorthand": "structural_missing_field",
        "underspecification": "structural_missing_field",
        "unit_ambiguity": "unit_confusion",
        "scale_confusion": "scale_confusion",
        "contradiction_bundle": "consistency_tradeoff",
        "noise_contamination": "stale_reference_salience",
        "sentinel_probe": "sentinel_probe",
    }
    primary = roughness_to_failure.get(primary_roughness)

    # Fallback to family default if seed roughness not mapped
    if primary is None:
        family_primary = {
            "B1": "structural_missing_field",
            "B2": "structural_missing_field",
            "B3": "unit_confusion",
            "B4": "consistency_tradeoff",
            "B5": "stale_reference_salience",
        }
        primary = family_primary.get(family, "structural_missing_field")

    # B5: distinguish parse contamination (broken fragments) from stale salience
    if family == "B5" and "broken_fragment" in str(seed.get("notes", "")):
        primary = "parse_contamination"

    # Secondary: from seed secondary_roughness
    secondary_roughness = seed.get("secondary_roughness")
    secondary_map = {
        "underspecification": "structural_missing_field",
        "unit_ambiguity": "unit_confusion",
        "scale_confusion": "scale_confusion",
        "contradiction_bundle": "consistency_tradeoff",
        "noise_contamination": "stale_reference_salience",
        "incomplete_shorthand": None,
    }
    secondary = secondary_map.get(secondary_roughness)

    return primary, secondary


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_corpus_b() -> tuple[dict, dict]:
    """Generate Corpus B and return (corpus_dict, generation_log)."""
    rng = Random(SEED)

    # Load seed bank
    with open(SEED_BANK_PATH) as f:
        seed_bank = json.load(f)

    transformer = PromptTransformer(rng, seed_bank)

    # Build 48 canonical combinations
    combos = []
    for ct in CELL_TYPES:
        for chem in CHEMISTRIES:
            for app in APPLICATIONS:
                combos.append((ct, chem, app))
    assert len(combos) == 48

    # Assign surface styles: within each family's 48, rotate 16/16/16
    # Shuffle combos per family for variety
    prompts = []
    generation_log_entries = []
    prompt_counter = 0

    for family in FAMILIES:
        # Shuffle combos for this family
        family_combos = list(combos)
        rng.shuffle(family_combos)

        for combo_idx, (ct, chem, app) in enumerate(family_combos):
            # Assign surface style: 0-15=note, 16-31=conversation, 32-47=mixed
            style_idx = combo_idx // 16
            style = SURFACE_STYLES[style_idx]

            # Select seed: rotate among the 3 seeds for this family+style
            sk = _seed_key(family, style)
            seeds = seed_bank["seeds"][sk]
            seed = seeds[combo_idx % len(seeds)]

            # Determine transform level: distribute across 0/1/2
            transform_level = combo_idx % 3

            # Render prompt
            prompt_text, provenance = transformer.render(
                seed, ct, chem, app, transform_level
            )

            # B5 mixed: occasionally inject broken fragments
            if family == "B5" and style == "mixed_fragment":
                prompt_text = transformer.inject_broken_fragment(
                    prompt_text, provenance["applied_transforms"]
                )

            # Infer metadata
            difficulty = _infer_difficulty(seed, transform_level)
            primary_fm, secondary_fm = _infer_failure_modes(family, seed)

            prompt_counter += 1
            prompt_id = f"B-{prompt_counter:03d}"

            prompt_record = {
                "prompt_id": prompt_id,
                "cell_type": ct,
                "chemistry": chem,
                "application": app,
                "roughness_family": family,
                "surface_style": style,
                "difficulty_tag": difficulty,
                "prompt_text": prompt_text,
                "canonical_intent_summary": f"{ct} {chem} cell for {app}",
                "primary_roughness": seed.get("primary_roughness", ""),
                "secondary_roughness": seed.get("secondary_roughness"),
                "omitted_fields": [],
                "unit_traps": family == "B3",
                "scale_traps": family == "B3" and "scale" in seed.get("primary_roughness", ""),
                "contradiction_tags": family == "B4",
                "noise_tags": family == "B5",
                "expected_primary_failure_mode": primary_fm,
                "expected_secondary_failure_mode": secondary_fm,
                "gold_priority_order": None,
                "linked_corpus_a_prompt_id": None,
            }
            prompts.append(prompt_record)

            generation_log_entries.append({
                "prompt_id": prompt_id,
                **provenance,
                "roughness_family": family,
                "surface_style": style,
                "difficulty_tag": difficulty,
                "cell_type": ct,
                "chemistry": chem,
                "application": app,
            })

    assert len(prompts) == 240, f"Expected 240 core prompts, got {len(prompts)}"

    # --- Add 10 sentinel prompts ---
    for sentinel in seed_bank["sentinel_prompts"]:
        prompt_counter += 1
        prompt_id = f"B-{prompt_counter:03d}"

        prompt_record = {
            "prompt_id": prompt_id,
            "cell_type": _sentinel_cell_type(sentinel),
            "chemistry": _sentinel_chemistry(sentinel),
            "application": _sentinel_application(sentinel),
            "roughness_family": "SENT",
            "surface_style": "sentinel",
            "difficulty_tag": "D4",
            "prompt_text": sentinel["text"],
            "canonical_intent_summary": sentinel["target"],
            "primary_roughness": "sentinel_probe",
            "secondary_roughness": None,
            "omitted_fields": [],
            "unit_traps": "unit" in sentinel.get("expected_failure", ""),
            "scale_traps": "scale" in sentinel.get("expected_failure", ""),
            "contradiction_tags": "tradeoff" in sentinel.get("expected_failure", ""),
            "noise_tags": "contamination" in sentinel.get("expected_failure", ""),
            "expected_primary_failure_mode": sentinel.get("expected_failure", ""),
            "expected_secondary_failure_mode": None,
            "gold_priority_order": None,
            "linked_corpus_a_prompt_id": None,
        }
        prompts.append(prompt_record)

        generation_log_entries.append({
            "prompt_id": prompt_id,
            "seed_exemplar_id": sentinel["id"],
            "generator_version": GENERATOR_VERSION,
            "rng_seed": SEED,
            "transform_level": 0,
            "applied_transforms": ["sentinel_verbatim"],
            "roughness_family": "SENT",
            "surface_style": "sentinel",
            "difficulty_tag": "D4",
        })

    assert len(prompts) == 250, f"Expected 250 total prompts, got {len(prompts)}"

    # --- Build corpus dict ---
    corpus = {
        "corpus_version": "B-1.0",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "seed": SEED,
        "generator_version": GENERATOR_VERSION,
        "seed_bank_version": seed_bank["seed_bank_version"],
        "total_prompts": len(prompts),
        "stratification": {
            "cell_types": CELL_TYPES,
            "chemistries": CHEMISTRIES,
            "applications": APPLICATIONS,
            "roughness_families": FAMILIES + ["SENT"],
            "surface_styles": SURFACE_STYLES + ["sentinel"],
            "difficulty_tags": ["D1", "D2", "D3", "D4"],
        },
        "prompts": prompts,
    }

    log = {
        "generator_version": GENERATOR_VERSION,
        "seed_bank_version": seed_bank["seed_bank_version"],
        "rng_seed": SEED,
        "generated_at": corpus["generated_at"],
        "total_prompts": len(prompts),
        "entries": generation_log_entries,
    }

    return corpus, log


def _sentinel_cell_type(s: dict) -> str:
    text = s["text"].lower()
    if "prismatic" in text:
        return "prismatic"
    if "pouch" in text:
        return "pouch"
    if "cylindrical" in text or "21700" in text or "4680" in text:
        return "cylindrical"
    return "prismatic"


def _sentinel_chemistry(s: dict) -> str:
    text = s["text"].upper()
    if "LFP" in text or "IRON PHOSPHATE" in text:
        return "LFP"
    if "NMC811" in text or "NMC-811" in text:
        return "NMC-811"
    if "NMC622" in text or "NMC-622" in text:
        return "NMC-622"
    if "NMC111" in text or "NMC-111" in text:
        return "NMC-111"
    return "NMC-622"


def _sentinel_application(s: dict) -> str:
    text = s["text"].lower()
    if "ev" in text or "traction" in text or "automotive" in text:
        return "ev_traction"
    if "consumer" in text or "phone" in text or "electronics" in text:
        return "consumer_electronics"
    if "grid" in text or "storage" in text or "ess" in text:
        return "grid_storage"
    if "power tool" in text or "drill" in text:
        return "power_tools"
    return "ev_traction"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_corpus(corpus: dict) -> list[str]:
    """Run structural checks on the generated corpus. Returns list of issues."""
    issues = []
    prompts = corpus["prompts"]

    if len(prompts) != 250:
        issues.append(f"Total count: expected 250, got {len(prompts)}")

    # Core prompts balance
    core = [p for p in prompts if p["roughness_family"] != "SENT"]
    if len(core) != 240:
        issues.append(f"Core count: expected 240, got {len(core)}")

    sentinels = [p for p in prompts if p["roughness_family"] == "SENT"]
    if len(sentinels) != 10:
        issues.append(f"Sentinel count: expected 10, got {len(sentinels)}")

    # Family counts
    for fam in FAMILIES:
        count = sum(1 for p in core if p["roughness_family"] == fam)
        if count != 48:
            issues.append(f"Family {fam}: expected 48, got {count}")

    # Surface style counts per family
    for fam in FAMILIES:
        fam_prompts = [p for p in core if p["roughness_family"] == fam]
        for style in SURFACE_STYLES:
            count = sum(1 for p in fam_prompts if p["surface_style"] == style)
            if count != 16:
                issues.append(f"{fam}/{style}: expected 16, got {count}")

    # Cell type balance in core
    for ct in CELL_TYPES:
        count = sum(1 for p in core if p["cell_type"] == ct)
        expected = 80  # 48 combos × 5 families / 3 types
        if count != expected:
            issues.append(f"Cell type {ct}: expected {expected}, got {count}")

    # Chemistry balance in core
    for chem in CHEMISTRIES:
        count = sum(1 for p in core if p["chemistry"] == chem)
        expected = 60  # 48 combos × 5 families / 4 chemistries
        if count != expected:
            issues.append(f"Chemistry {chem}: expected {expected}, got {count}")

    # No empty prompts
    for p in prompts:
        if not p["prompt_text"] or len(p["prompt_text"].strip()) < 10:
            issues.append(f"{p['prompt_id']}: prompt_text too short or empty")

    # No unresolved template variables
    for p in prompts:
        if "{" in p["prompt_text"] and "}" in p["prompt_text"]:
            issues.append(f"{p['prompt_id']}: unresolved template variable in text")

    # Unique IDs
    ids = [p["prompt_id"] for p in prompts]
    if len(ids) != len(set(ids)):
        issues.append("Duplicate prompt IDs found")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("[corpus_b] Generating Corpus B...")
    corpus, log = generate_corpus_b()

    # Validate
    issues = validate_corpus(corpus)
    if issues:
        print(f"[corpus_b] VALIDATION ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print("[corpus_b] Aborting — fix issues before saving.")
        return

    print("[corpus_b] Validation passed.")

    # Save
    corpus_path = OUTPUT_DIR / "prompt_corpus_b.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)
    print(f"[corpus_b] Corpus saved: {corpus_path}")

    log_path = OUTPUT_DIR / "generation_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"[corpus_b] Generation log saved: {log_path}")

    # Summary stats
    prompts = corpus["prompts"]
    core = [p for p in prompts if p["roughness_family"] != "SENT"]
    print("\n[corpus_b] Summary:")
    print(f"  Total: {len(prompts)}")
    print(f"  Core: {len(core)}, Sentinels: {len(prompts) - len(core)}")
    for fam in FAMILIES:
        count = sum(1 for p in core if p["roughness_family"] == fam)
        print(f"  {fam}: {count}")
    for ct in CELL_TYPES:
        count = sum(1 for p in core if p["cell_type"] == ct)
        print(f"  {ct}: {count}")

    # Sample prompts for review
    print("\n[corpus_b] Sample prompts for review:")
    review_ids = ["B-001", "B-049", "B-097", "B-145", "B-193", "B-241"]
    for rid in review_ids:
        p = next((p for p in prompts if p["prompt_id"] == rid), None)
        if p:
            print(f"\n  --- {p['prompt_id']} [{p['roughness_family']}/{p['surface_style']}] "
                  f"{p['cell_type']}/{p['chemistry']}/{p['application']} ---")
            print(f"  {p['prompt_text'][:200]}...")


if __name__ == "__main__":
    main()
