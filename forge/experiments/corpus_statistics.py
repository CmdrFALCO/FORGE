#!/usr/bin/env python3
"""
Corpus Statistics Printer for the Stratified Prompt Corpus.

Reads prompt_corpus_v1.json and prints a comprehensive distribution summary
to verify the corpus meets all requirements.

Usage:
    python -m forge.experiments.corpus_statistics
    # or
    python forge/experiments/corpus_statistics.py
"""

import json
import sys
from pathlib import Path

DIMENSIONS = [
    ("Cell Type", "cell_type"),
    ("Chemistry", "chemistry"),
    ("Application", "application"),
    ("Difficulty", "difficulty"),
    ("Prompt Style", "prompt_style"),
]

DIFFICULTIES = ["standard", "edge_case", "underspecified", "contradictory"]
PROMPT_STYLES = ["terse", "detailed", "natural_language"]


def load_corpus(path: Path) -> dict:
    """Load and return the corpus JSON."""
    with open(path) as f:
        return json.load(f)


def print_header(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_dimension_distribution(prompts: list[dict]) -> None:
    """Print per-dimension level counts."""
    print_header("DIMENSION DISTRIBUTION")

    for dim_name, dim_key in DIMENSIONS:
        counts: dict[str, int] = {}
        for p in prompts:
            val = p[dim_key]
            counts[val] = counts.get(val, 0) + 1

        print(f"\n  {dim_name}:")
        total = len(prompts)
        for level in sorted(counts.keys()):
            count = counts[level]
            bar = "#" * (count // 5)
            print(f"    {level:25s} {count:4d}  ({100 * count / total:5.1f}%)  {bar}")


def print_cross_tabulation(prompts: list[dict]) -> None:
    """Print the difficulty x style cross-tabulation matrix."""
    print_header("DIFFICULTY x STYLE CROSS-TABULATION")

    matrix: dict[str, dict[str, int]] = {}
    for p in prompts:
        d = p["difficulty"]
        s = p["prompt_style"]
        if d not in matrix:
            matrix[d] = {}
        matrix[d][s] = matrix[d].get(s, 0) + 1

    # Header
    print()
    header = f"    {'Difficulty':20s}"
    for style in PROMPT_STYLES:
        header += f"  {style:>16s}"
    header += f"  {'TOTAL':>8s}"
    print(header)
    print("    " + "-" * (20 + 3 * 18 + 10))

    for diff in DIFFICULTIES:
        row = f"    {diff:20s}"
        row_total = 0
        for style in PROMPT_STYLES:
            count = matrix.get(diff, {}).get(style, 0)
            row += f"  {count:>16d}"
            row_total += count
        row += f"  {row_total:>8d}"
        print(row)

    # Column totals
    row = f"    {'TOTAL':20s}"
    grand_total = 0
    for style in PROMPT_STYLES:
        col_total = sum(matrix.get(d, {}).get(style, 0) for d in DIFFICULTIES)
        row += f"  {col_total:>16d}"
        grand_total += col_total
    row += f"  {grand_total:>8d}"
    print("    " + "-" * (20 + 3 * 18 + 10))
    print(row)


def print_cell_chemistry_matrix(prompts: list[dict]) -> None:
    """Print cell_type x chemistry cross-tabulation."""
    print_header("CELL TYPE x CHEMISTRY")

    cell_types = sorted({p["cell_type"] for p in prompts})
    chemistries = sorted({p["chemistry"] for p in prompts})

    matrix: dict[str, dict[str, int]] = {}
    for p in prompts:
        ct = p["cell_type"]
        ch = p["chemistry"]
        if ct not in matrix:
            matrix[ct] = {}
        matrix[ct][ch] = matrix[ct].get(ch, 0) + 1

    print()
    header = f"    {'Cell Type':15s}"
    for chem in chemistries:
        header += f"  {chem:>10s}"
    header += f"  {'TOTAL':>8s}"
    print(header)
    print("    " + "-" * (15 + len(chemistries) * 12 + 10))

    for ct in cell_types:
        row = f"    {ct:15s}"
        row_total = 0
        for chem in chemistries:
            count = matrix.get(ct, {}).get(chem, 0)
            row += f"  {count:>10d}"
            row_total += count
        row += f"  {row_total:>8d}"
        print(row)


def print_contradiction_analysis(prompts: list[dict]) -> None:
    """Print analysis of contradictory prompts."""
    print_header("CONTRADICTORY PROMPT ANALYSIS")

    contra = [p for p in prompts if p["difficulty"] == "contradictory"]
    total_contra = len(contra)

    print(f"\n  Total contradictory prompts: {total_contra}")

    # Check all have violations
    have_violations = sum(1 for p in contra if p["expected_violations"] != "none" and p["expected_violations"])
    print(f"  With expected_violations:    {have_violations}")
    missing = total_contra - have_violations
    if missing > 0:
        print(f"  MISSING violations:          {missing}  *** WARNING ***")

    # Violation ID distribution
    violation_counts: dict[str, int] = {}
    for p in contra:
        ev = p["expected_violations"]
        if isinstance(ev, list):
            for v in ev:
                violation_counts[v] = violation_counts.get(v, 0) + 1

    if violation_counts:
        print("\n  Constraint violation distribution:")
        for vid in sorted(violation_counts.keys()):
            count = violation_counts[vid]
            bar = "#" * count
            print(f"    {vid:10s} {count:4d}  {bar}")

    # By prompt style
    print("\n  Contradictory prompts by style:")
    style_counts: dict[str, int] = {}
    for p in contra:
        s = p["prompt_style"]
        style_counts[s] = style_counts.get(s, 0) + 1
    for style in PROMPT_STYLES:
        print(f"    {style:20s} {style_counts.get(style, 0):4d}")

    # Check NL contradictory quality
    nl_contra = [p for p in contra if p["prompt_style"] == "natural_language"]
    print(f"\n  Natural language contradictory prompts: {len(nl_contra)}")
    if nl_contra:
        print("  Sample (first 3):")
        for p in nl_contra[:3]:
            text_preview = p["prompt_text"][:120].replace("\n", " ")
            print(f"    [{p['prompt_id']}] {text_preview}...")


def print_underspecified_analysis(prompts: list[dict]) -> None:
    """Print analysis of underspecified prompts."""
    print_header("UNDERSPECIFIED PROMPT ANALYSIS")

    under = [p for p in prompts if p["difficulty"] == "underspecified"]
    print(f"\n  Total underspecified prompts: {len(under)}")

    # Check what fields are missing
    standard_fields = {"capacity_ah", "energy_density_target", "cycle_life", "temp_min", "temp_max", "c_rate"}
    field_missing_counts: dict[str, int] = {}
    for p in under:
        present = standard_fields & set(p["parameters_used"].keys())
        missing = standard_fields - present
        for f in missing:
            field_missing_counts[f] = field_missing_counts.get(f, 0) + 1

    print("\n  Missing field distribution:")
    for field in sorted(field_missing_counts.keys()):
        count = field_missing_counts[field]
        print(f"    {field:25s} {count:4d}")

    # Average number of missing fields
    missing_counts = []
    for p in under:
        present = standard_fields & set(p["parameters_used"].keys())
        missing_counts.append(len(standard_fields) - len(present))
    if missing_counts:
        avg = sum(missing_counts) / len(missing_counts)
        print(f"\n  Average fields missing: {avg:.1f}")


def print_verification_checklist(corpus: dict) -> None:
    """Print the full verification checklist."""
    print_header("VERIFICATION CHECKLIST")
    prompts = corpus["prompts"]

    checks = []

    # 1. Exactly 500
    count = len(prompts)
    checks.append(("Exactly 500 prompts", count == 500, f"Got {count}"))

    # 2. No duplicate IDs
    ids = [p["prompt_id"] for p in prompts]
    unique_ids = len(set(ids))
    checks.append(("No duplicate prompt_ids", unique_ids == count, f"{count - unique_ids} duplicates"))

    # 3. No duplicate texts
    texts = [p["prompt_text"] for p in prompts]
    unique_texts = len(set(texts))
    checks.append(("No duplicate prompt_text", unique_texts == count, f"{count - unique_texts} duplicates"))

    # 4. Minimum representation
    min_ok = True
    min_details = []
    for dim_name, dim_key in DIMENSIONS:
        counts: dict[str, int] = {}
        for p in prompts:
            counts[p[dim_key]] = counts.get(p[dim_key], 0) + 1
        for level, c in counts.items():
            if c < 10:  # Very lenient minimum
                min_ok = False
                min_details.append(f"{dim_key}={level}: {c}")
    checks.append(("All levels adequately represented", min_ok, "; ".join(min_details) if min_details else "OK"))

    # 5. All contradictory have violations
    contra = [p for p in prompts if p["difficulty"] == "contradictory"]
    all_have = all(p["expected_violations"] != "none" and p["expected_violations"] for p in contra)
    checks.append(("All contradictory have violations", all_have, f"{len(contra)} contradictory prompts"))

    # 6. All underspecified missing params
    under = [p for p in prompts if p["difficulty"] == "underspecified"]
    standard_fields = {"capacity_ah", "energy_density_target", "cycle_life", "temp_min", "temp_max", "c_rate"}
    all_missing = all(len(standard_fields - set(p["parameters_used"].keys())) >= 2 for p in under)
    checks.append(("All underspecified missing >= 2 fields", all_missing, f"{len(under)} underspecified prompts"))

    # 7. No standard/edge_case with violations
    clean = [p for p in prompts if p["difficulty"] in ("standard", "edge_case")]
    all_clean = all(p["expected_violations"] == "none" for p in clean)
    checks.append(("No standard/edge_case with violations", all_clean, f"{len(clean)} prompts checked"))

    # Print
    print()
    all_pass = True
    for label, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {label}")
        if not passed:
            print(f"         Detail: {detail}")

    print()
    if all_pass:
        print("  All checks PASSED.")
    else:
        print("  Some checks FAILED. Review above.")


def print_sample_prompts(prompts: list[dict]) -> None:
    """Print sample prompts from each difficulty x style combination."""
    print_header("SAMPLE PROMPTS")

    for diff in DIFFICULTIES:
        for style in PROMPT_STYLES:
            matching = [p for p in prompts if p["difficulty"] == diff and p["prompt_style"] == style]
            if not matching:
                print(f"\n  [{diff} + {style}] NO PROMPTS")
                continue

            sample = matching[0]
            print(f"\n  [{diff} + {style}] {sample['prompt_id']}")
            print(f"  Chemistry: {sample['chemistry']}  Cell: {sample['cell_type']}  App: {sample['application']}")

            # Show first 200 chars of prompt text
            text = sample["prompt_text"]
            if len(text) > 200:
                text = text[:200] + "..."
            for line in text.split("\n"):
                print(f"    > {line}")

            if sample["expected_violations"] != "none":
                print(f"  Violations: {sample['expected_violations']}")


def main() -> None:
    corpus_path = Path(__file__).parent / "prompt_corpus_v1.json"

    if not corpus_path.exists():
        print(f"ERROR: Corpus file not found: {corpus_path}")
        print("Run generate_corpus.py first.")
        sys.exit(1)

    corpus = load_corpus(corpus_path)
    prompts = corpus["prompts"]

    print()
    print("#" * 70)
    print("#  AXIOM Prompt Corpus Statistics")
    print(f"#  File: {corpus_path.name}")
    print(f"#  Version: {corpus.get('corpus_version', '?')}")
    print(f"#  Generated: {corpus.get('generated_at', '?')}")
    print(f"#  Seed: {corpus.get('seed', '?')}")
    print(f"#  Total prompts: {corpus.get('total_prompts', '?')}")
    print(f"#  Trimming: {corpus.get('trimming_strategy', '?')}")
    print("#" * 70)

    print_dimension_distribution(prompts)
    print_cross_tabulation(prompts)
    print_cell_chemistry_matrix(prompts)
    print_contradiction_analysis(prompts)
    print_underspecified_analysis(prompts)
    print_verification_checklist(corpus)
    print_sample_prompts(prompts)

    print()


if __name__ == "__main__":
    main()
