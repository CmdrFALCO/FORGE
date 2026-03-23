#!/usr/bin/env python3
"""FORGE PyBaMM Pilot — Physics-Based Dataset Generation.

Generates a dataset of battery cell designs with electrochemical/thermal
performance targets from PyBaMM DFN simulations.

Pipeline:
  1. (Optional) Sobol sensitivity screening
  2. Latin Hypercube Sampling of geometric design space
  3. PyBaMM DFN simulation for each sample
  4. Dataset assembly (train/val/test .npz + metadata.json)

Usage:
  # Full pilot (500 samples, ~30-40 min)
  python prepare_pybamm.py --n-samples 500

  # Quick smoke test (20 samples, ~2 min)
  python prepare_pybamm.py --n-samples 20

  # With Sobol screening first
  python prepare_pybamm.py --n-samples 500 --sobol --sobol-n 64
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Ensure forge package is importable when running from experiments/ directory.
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from forge.ml.batch import LHSGenerator  # noqa: E402
from forge.ml.common.types import (  # noqa: E402
    CellType,
    DesignSpace,
    ParameterRange,
    SimulationConfig,
)
from forge.ml.dataset import NpzDatasetBuilder, NpzDatasetLoader  # noqa: E402
from forge.ml.simulation import GeometryTranslator, PyBaMMRunner  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="FORGE PyBaMM Pilot — Dataset Generation"
    )
    p.add_argument(
        "--n-samples", type=int, default=500,
        help="Number of cell designs to simulate",
    )
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    p.add_argument(
        "--output", type=str, default="dataset_pybamm",
        help="Output directory for dataset",
    )
    p.add_argument(
        "--sobol", action="store_true",
        help="Run Sobol screening before dataset generation",
    )
    p.add_argument(
        "--sobol-n", type=int, default=64,
        help="Sobol base sample size (evaluations = N × (D+2))",
    )
    p.add_argument(
        "--sobol-output", type=str, default="sobol_report.json",
        help="Sobol results output file",
    )
    p.add_argument(
        "--log-level", type=str, default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
    )
    return p


def _make_design_space(translator: GeometryTranslator) -> DesignSpace:
    raw = translator.get_design_space()
    return DesignSpace(
        parameters=[
            ParameterRange(name=k, min_value=lo, max_value=hi)
            for k, (lo, hi) in raw.items()
        ],
        cell_type=CellType.CYLINDRICAL,
    )


def main() -> int:
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logger = logging.getLogger(__name__)

    translator = GeometryTranslator()
    runner = PyBaMMRunner(base_parameter_set="Chen2020")
    generator = LHSGenerator()
    builder = NpzDatasetBuilder()

    design_space = _make_design_space(translator)

    # ── Phase 1: Sobol Screening (optional) ──────────────────────
    if args.sobol:
        from forge.ml.sensitivity import SobolScreener

        logger.info("Running Sobol screening with N=%d...", args.sobol_n)
        screener = SobolScreener(runner=runner, translator=translator)

        t0 = time.time()
        sobol_rate = screener.screen(
            design_space, "rate_capability", n_samples=args.sobol_n,
        )
        sobol_temp = screener.screen(
            design_space, "max_temp", n_samples=args.sobol_n,
        )
        t_sobol = time.time() - t0

        logger.info("Sobol screening complete in %.0fs", t_sobol)
        logger.info("\n%s", screener.print_report(sobol_rate))
        logger.info("\n%s", screener.print_report(sobol_temp))

        sobol_output = {
            "rate_capability": {
                "indices": [
                    {
                        "parameter": idx.parameter_name,
                        "S1": idx.first_order,
                        "ST": idx.total_order,
                    }
                    for idx in sobol_rate.indices
                ],
                "important_parameters": screener.rank_parameters(
                    sobol_rate, threshold=0.01,
                ),
            },
            "max_temp": {
                "indices": [
                    {
                        "parameter": idx.parameter_name,
                        "S1": idx.first_order,
                        "ST": idx.total_order,
                    }
                    for idx in sobol_temp.indices
                ],
                "important_parameters": screener.rank_parameters(
                    sobol_temp, threshold=0.01,
                ),
            },
            "n_samples": args.sobol_n,
            "duration_seconds": t_sobol,
        }
        sobol_path = Path(args.sobol_output)
        sobol_path.write_text(json.dumps(sobol_output, indent=2))
        logger.info("Sobol results saved to %s", sobol_path)

    # ── Phase 2: LHS Sampling ────────────────────────────────────
    logger.info(
        "Generating %d cell designs via LHS (seed=%d)...",
        args.n_samples, args.seed,
    )
    specs = generator.generate_with_derived(
        design_space, args.n_samples, translator, seed=args.seed,
    )
    logger.info("Generated %d cell designs", len(specs))

    # ── Phase 3: PyBaMM Simulations ──────────────────────────────
    logger.info("Running PyBaMM DFN simulations...")

    config = SimulationConfig(
        c_rates=[0.2, 3.0],
        parameter_set="Chen2020",
    )

    all_results: list[list] = []
    n_success = 0
    n_fail = 0
    t_start = time.time()

    for i, spec in enumerate(specs):
        t_sim = time.time()
        sim_results = runner.simulate(spec, config)
        dt = time.time() - t_sim

        # Check if at least the discharge results succeeded
        discharge_ok = any(r.success and r.c_rate > 0 for r in sim_results)
        if discharge_ok:
            n_success += 1
            status = "OK"
        else:
            n_fail += 1
            err = next((r.error_message for r in sim_results if not r.success), "")
            status = f"FAIL: {err[:60]}"

        all_results.append(sim_results)

        if (i + 1) % 10 == 0 or not discharge_ok:
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed
            eta = (args.n_samples - i - 1) / rate if rate > 0 else 0
            logger.info(
                "[%d/%d] %s | %.1fs | %d ok, %d fail | ETA: %.0fs",
                i + 1, args.n_samples, status, dt, n_success, n_fail, eta,
            )

    t_total = time.time() - t_start
    logger.info(
        "Simulations complete: %d ok, %d fail in %.0fs",
        n_success, n_fail, t_total,
    )

    fail_rate = n_fail / args.n_samples if args.n_samples > 0 else 0
    if fail_rate > 0.2:
        logger.warning(
            "High failure rate: %.1f%%. Dataset quality may be compromised.",
            fail_rate * 100,
        )
    min_required = min(50, args.n_samples)
    if n_success < min_required:
        logger.error(
            "Only %d successful simulations. Need at least %d.",
            n_success, min_required,
        )
        return 1

    # ── Phase 4: Dataset Assembly ────────────────────────────────
    logger.info("Assembling dataset in '%s'...", args.output)
    meta = builder.build(
        cell_specs=specs,
        simulation_results=all_results,
        output_path=args.output,
        seed=args.seed,
    )

    # Verify round-trip
    loader = NpzDatasetLoader()
    loader.load(args.output)

    logger.info("Dataset assembled:")
    logger.info("  Source: %s", meta.get("source", "unknown"))
    logger.info("  Samples: %d (attempted: %d, failed: %d)",
                meta["n_samples"], meta["attempted"], meta["failed"])
    logger.info("  Train: %d, Val: %d, Test: %d",
                meta["split_sizes"]["train"],
                meta["split_sizes"]["val"],
                meta["split_sizes"]["test"])
    logger.info("  Hashes verified: OK")

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("FORGE PyBaMM Pilot — Complete")
    print("=" * 60)
    print(f"Samples:    {n_success} / {args.n_samples} ({n_fail} failures)")
    print(f"Duration:   {t_total:.0f}s ({t_total / 60:.1f} min)")
    print(f"Rate:       {args.n_samples / max(t_total, 1):.1f} samples/s")
    print(f"Output:     {args.output}/")
    print(f"  train.npz:     {meta['split_sizes']['train']} samples")
    print(f"  val.npz:       {meta['split_sizes']['val']} samples")
    print(f"  test.npz:      {meta['split_sizes']['test']} samples")
    print("  metadata.json: hashes verified")
    print("=" * 60)
    print("\nTo use with autoresearch:")
    print(f"  python surrogate.py --dataset {args.output} --seed 42 --budget-seconds 300")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
