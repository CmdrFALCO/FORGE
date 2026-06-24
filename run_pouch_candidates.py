#!/usr/bin/env python3
"""
FORGE supervised production run — NMC111/graphite lab pouch candidates.

Purpose: generate a SET of physics-valid candidate pouch-cell specifications
spanning a small-to-modest lab capacity range, with FULL provenance, to be
offered to the ICSI fabrication partner (Dr. Buga) who will select per line
constraints. This bundle is the ROOT of the validation chain ("spec generated
before fabrication") and must be self-documenting and reproducible.

Run from the FORGE repo root inside the .venv:
    cd /home/cmdrfalco/Projects/CmdrFALCO/FORGE
    source .venv/bin/activate
    python run_pouch_candidates.py

Output: a timestamped bundle under provenance_runs/<run_id>/ containing, per
candidate, the user prompt, system prompt (best-effort), output YAML, sha256,
full result dump, constraint/retry log; plus a run manifest, an assumptions
note, and a bundle hash. The script then git-adds the bundle (does NOT commit
automatically — you review, then commit).
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# --- FORGE import -----------------------------------------------------------
try:
    from forge.axiom import generate_cell_design
except Exception as e:  # noqa: BLE001
    print(f"FATAL: cannot import forge.axiom.generate_cell_design: {e}")
    print("Are you in the repo root with .venv activated?")
    sys.exit(1)

# --- Pinned, cited design inputs (NOT chosen by the model) ------------------
# These are stated literature values the model is instructed to USE, converting
# them from model output into documented design inputs. Cite a standard battery
# reference (or ICSI's own materials data once available) in the thesis.
CHEMISTRY = {
    "cathode_material": "NMC111",
    "cathode_rev_spec_capacity_mahg": 160.0,   # practical reversible, ~150-165 typical
    "anode_material": "Graphite",
    "anode_rev_spec_capacity_mahg": 350.0,     # practical, ~350-360 typical
    "np_ratio_target": 1.10,
    "citation_note": "Specific capacities pinned from standard Li-ion materials "
                     "literature (NMC111 practical ~150-165 mAh/g; graphite "
                     "~350-360 mAh/g). To be reconciled with ICSI materials data "
                     "if/when provided.",
}

MODEL = "qwen3.5:27b"

# --- Candidate envelope: vary SIZE, not chemistry ---------------------------
# Spread across ~0.5-3 Ah by layer count + footprint. Conservative loadings
# (12-16 mg/cm2) for first-cell buildability rather than max energy density.
# 6 candidates to leave margin for >=5 valid.
CANDIDATES = [
    {"id": "C1_xs", "target_ah": 0.5, "footprint_mm": "40x30", "pairs": 4,
     "cathode_loading": 12.0, "note": "smallest coupon, few layers, low loading"},
    {"id": "C2_s",  "target_ah": 1.0, "footprint_mm": "50x40", "pairs": 6,
     "cathode_loading": 13.0, "note": "small validation cell"},
    {"id": "C3_sm", "target_ah": 1.5, "footprint_mm": "50x40", "pairs": 9,
     "cathode_loading": 14.0, "note": "small-modest"},
    {"id": "C4_m",  "target_ah": 2.0, "footprint_mm": "60x40", "pairs": 11,
     "cathode_loading": 14.0, "note": "modest"},
    {"id": "C5_mh", "target_ah": 2.5, "footprint_mm": "60x40", "pairs": 14,
     "cathode_loading": 15.0, "note": "modest-high"},
    {"id": "C6_h",  "target_ah": 3.0, "footprint_mm": "60x45", "pairs": 18,
     "cathode_loading": 16.0, "note": "upper end of lab range"},
]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_json(obj):
    """Best-effort serialize an arbitrary result object's attributes."""
    def default(o):
        try:
            return vars(o)
        except TypeError:
            return repr(o)
    return json.dumps(obj, default=default, indent=2, ensure_ascii=False)


def build_prompt(c: dict) -> str:
    """Construct the per-candidate user prompt with pinned chemistry + size."""
    return (
        f"Design a laboratory pouch cell for research validation.\n"
        f"Chemistry (USE THESE EXACT VALUES, do not substitute):\n"
        f"  - Cathode: {CHEMISTRY['cathode_material']}, reversible specific "
        f"capacity {CHEMISTRY['cathode_rev_spec_capacity_mahg']} mAh/g.\n"
        f"  - Anode: {CHEMISTRY['anode_material']}, reversible specific "
        f"capacity {CHEMISTRY['anode_rev_spec_capacity_mahg']} mAh/g.\n"
        f"  - N/P ratio target approximately {CHEMISTRY['np_ratio_target']}.\n"
        f"Target nominal capacity approximately {c['target_ah']} Ah.\n"
        f"Cathode sheet footprint approximately {c['footprint_mm']} mm.\n"
        f"Use approximately {c['pairs']} electrode pairs in a single stack.\n"
        f"Cathode areal loading approximately {c['cathode_loading']} mg/cm2 "
        f"(conservative, for reliable coating on a pilot line — do NOT maximize "
        f"loading or energy density).\n"
        f"Separator PP. Electrolyte LiPF6-based. Produce a complete, "
        f"physics-valid pouch specification."
    )


def extract_system_prompt(result) -> str:
    """Best-effort: find the system prompt on the result object."""
    for attr in ("system_prompt", "system", "prompt_system", "messages"):
        val = getattr(result, attr, None)
        if val:
            return val if isinstance(val, str) else safe_json(val)
    # search attributes for anything that looks like a system prompt
    try:
        for k, v in vars(result).items():
            if "system" in k.lower() and isinstance(v, str) and len(v) > 200:
                return v
    except TypeError:
        pass
    return ""  # caller logs absence


def get(result, *names, default="n/a"):
    for n in names:
        v = getattr(result, n, None)
        if v is not None:
            return v
    return default


def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ") + "_nmc111_pouch"
    base = os.path.join("provenance_runs", run_id)
    os.makedirs(base, exist_ok=True)
    print(f"Run bundle: {base}")

    # Run-level: capture ollama model digest
    try:
        ollama_show = subprocess.run(
            ["ollama", "show", MODEL, "--modelfile"],
            capture_output=True, text=True, timeout=30,
        ).stdout
    except Exception as e:  # noqa: BLE001
        ollama_show = f"(could not capture ollama show: {e})"
    model_digest = sha256_text(ollama_show) if ollama_show else "n/a"

    manifest = {
        "run_id": run_id,
        "started_utc": utcnow_iso(),
        "model": MODEL,
        "ollama_modelfile_sha256": model_digest,
        "chemistry_pinned": CHEMISTRY,
        "selection_policy": "No selection made at generation time. Valid "
            "candidates span a lab capacity range and will be offered (2-3) to "
            "the ICSI fabrication partner; final selection joint, per line "
            "constraints.",
        "partner_constraints_status": "No ICSI line constraints available as of "
            "2026-06-24. Lab-scale targets and conservative loadings are OUR "
            "stated design assumptions, to be reconciled on partner response.",
        "candidates": [],
    }

    valid_count = 0
    for c in CANDIDATES:
        cdir = os.path.join(base, c["id"])
        os.makedirs(cdir, exist_ok=True)
        prompt = build_prompt(c)
        ts = utcnow_iso()
        print(f"\n[{c['id']}] target ~{c['target_ah']} Ah ... ", end="", flush=True)

        try:
            result = generate_cell_design(
                request=prompt,
                backend="ollama",
                model=MODEL,            # explicit — never rely on class default
                cell_type="pouch",
                calculate=True,
                think=False,
                num_predict=2000,
                append_yaml_suffix=True,
            )
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {e}")
            with open(os.path.join(cdir, "ERROR.txt"), "w") as f:
                f.write(f"{ts}\n{e}\n")
            manifest["candidates"].append(
                {"id": c["id"], "timestamp_utc": ts, "status": "error", "error": str(e)})
            continue

        success = bool(get(result, "success", default=False))
        yaml_content = get(result, "yaml_content", default="") or ""
        yaml_sha = sha256_text(yaml_content) if yaml_content else "n/a"
        sysprompt = extract_system_prompt(result)

        # Persist everything
        with open(os.path.join(cdir, "user_prompt.txt"), "w") as f:
            f.write(prompt)
        with open(os.path.join(cdir, "system_prompt.txt"), "w") as f:
            f.write(sysprompt if sysprompt else "(system prompt not exposed by result object)")
        with open(os.path.join(cdir, "spec.yaml"), "w") as f:
            f.write(yaml_content)
        with open(os.path.join(cdir, "result_full.json"), "w") as f:
            f.write(safe_json(result))

        summary = None
        try:
            summary = result.summary()
        except Exception:  # noqa: BLE001
            summary = "(no summary())"

        crow = {
            "id": c["id"],
            "timestamp_utc": ts,
            "status": "valid" if success else "invalid",
            "target_ah": c["target_ah"],
            "design_note": c["note"],
            "success": success,
            "attempts": get(result, "attempts"),
            "retry_reasons": get(result, "retry_reasons", default=[]),
            "spec_yaml_sha256": yaml_sha,
            "system_prompt_captured": bool(sysprompt),
            "summary": str(summary),
        }
        manifest["candidates"].append(crow)
        if success:
            valid_count += 1
        print("VALID" if success else "INVALID",
              f"(attempts={crow['attempts']})")

    manifest["finished_utc"] = utcnow_iso()
    manifest["valid_count"] = valid_count
    manifest["total_candidates"] = len(CANDIDATES)

    with open(os.path.join(base, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Human-readable assumptions note
    with open(os.path.join(base, "design_assumptions.md"), "w") as f:
        f.write(
            f"# Design Assumptions — {run_id}\n\n"
            f"Generated {manifest['finished_utc']} on local rig, supervised "
            f"`{MODEL}` under AXIOM (polymorphic pouch constraints PO1-PO7 + "
            f"common C1-C7).\n\n"
            f"**No fabrication-partner (ICSI) line constraints were available at "
            f"generation time (as of 2026-06-24).** The capacity range "
            f"(~0.5-3 Ah), footprints, layer counts, and conservative cathode "
            f"loadings (12-16 mg/cm2) are OUR stated lab-scale design "
            f"assumptions, chosen for first-cell buildability rather than "
            f"maximized energy density.\n\n"
            f"Material specific capacities were PINNED as cited design inputs "
            f"(NMC111 {CHEMISTRY['cathode_rev_spec_capacity_mahg']} mAh/g, "
            f"graphite {CHEMISTRY['anode_rev_spec_capacity_mahg']} mAh/g), not "
            f"chosen by the model. {CHEMISTRY['citation_note']}\n\n"
            f"**No final candidate was selected at generation.** {valid_count} of "
            f"{len(CANDIDATES)} candidates were physics-valid. A subset (2-3) "
            f"spanning the range will be offered to ICSI; final selection is "
            f"joint, per line constraints. The fabricated cell's spec — whichever "
            f"is ultimately built — is the one that anchors the measured-vs-"
            f"predicted validation, and was generated prior to fabrication.\n"
        )

    # Bundle hash (hash of manifest + all spec.yaml + assumptions)
    hasher = hashlib.sha256()
    for root, _, files in os.walk(base):
        for fn in sorted(files):
            if fn in ("spec.yaml", "manifest.json", "design_assumptions.md"):
                with open(os.path.join(root, fn), "rb") as fh:
                    hasher.update(fh.read())
    bundle_hash = hasher.hexdigest()
    with open(os.path.join(base, "BUNDLE_SHA256.txt"), "w") as f:
        f.write(bundle_hash + "\n")

    print(f"\n=== DONE: {valid_count}/{len(CANDIDATES)} valid ===")
    print(f"Bundle: {base}")
    print(f"Bundle SHA256: {bundle_hash}")

    # git add (NOT commit — you review first)
    try:
        subprocess.run(["git", "add", base], check=False)
        print("git add staged. Review, then commit:")
        print(f'  git commit -m "provenance: NMC111 pouch candidate run {run_id}"')
    except Exception as e:  # noqa: BLE001
        print(f"(git add skipped: {e})")


if __name__ == "__main__":
    main()
