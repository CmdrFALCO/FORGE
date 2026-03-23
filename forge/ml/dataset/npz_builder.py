"""Dataset builder and loader using .npz files and metadata.json.

Assembles simulation results into train/val/test splits compatible with
``surrogate.py`` and the autoresearch loop.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from forge.ml.common.types import CellSpec, GeometricRepresentation, SimulationResult
from forge.ml.dataset.builder import DatasetBuilder, DatasetLoader

logger = logging.getLogger(__name__)

# Column order must match prepare.py exactly so surrogate.py works unchanged.
FEATURE_NAMES = [
    "electrode_thickness",
    "porosity",
    "separator_thickness",
    "n_tabs",
    "tab_width",
    "can_inner_diameter",
    "can_wall_thickness",
    "cell_height",
    "surface_to_volume",
    "tab_conductance_proxy",
    "diffusion_path_proxy",
]

# Keep _proxy suffix for backward compatibility with surrogate.py metadata lookup.
TARGET_NAMES = ["rate_capability_proxy", "max_temp_proxy"]


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NpzDatasetBuilder(DatasetBuilder):
    """Build a .npz + metadata.json dataset from simulation results."""

    def build(
        self,
        cell_specs: list[CellSpec],
        simulation_results: list[list[SimulationResult]],
        representations: list[GeometricRepresentation] | None = None,
        output_path: Path | str = "dataset",
        seed: int = 42,
    ) -> dict[str, Any]:
        """Assemble dataset from specs and their simulation results.

        Each entry in *simulation_results* is the list returned by
        ``PyBaMMRunner.simulate()`` for the corresponding spec.
        """
        output = Path(output_path)
        output.mkdir(parents=True, exist_ok=True)

        # ---- extract successful samples ----------------------------------
        features_list: list[list[float]] = []
        targets_list: list[list[float]] = []
        n_failed = 0

        for spec, results in zip(cell_specs, simulation_results):
            # Check if any result in the list failed critically
            discharge_ok = [r for r in results if r.c_rate > 0 and r.success]
            thermal = [r for r in results if r.c_rate == 0.0 and r.success]

            if not discharge_ok:
                n_failed += 1
                continue

            # Rate capability = Q_high / Q_low
            caps = {r.c_rate: r.capacity_ah for r in discharge_ok}
            q_low = caps.get(0.2, 0.0)
            q_high = max(
                (c for rate, c in caps.items() if rate > 1.0), default=0.0
            )
            rate_capability = q_high / max(q_low, 1e-10) if q_low > 0 else 0.0

            # Max temperature from thermal experiment
            max_temp = thermal[0].max_temperature_celsius if thermal else 0.0
            if max_temp <= 0:
                n_failed += 1
                continue

            # Feature vector (11 columns)
            row = [float(spec.parameters.get(name, 0.0)) for name in FEATURE_NAMES]
            features_list.append(row)
            targets_list.append([rate_capability, max_temp])

        if n_failed:
            logger.warning(
                "Dropped %d / %d samples (failed or incomplete simulations)",
                n_failed,
                len(cell_specs),
            )

        X = np.array(features_list, dtype=np.float32)
        y = np.array(targets_list, dtype=np.float32)
        n_total = len(X)

        # ---- shuffle and split -------------------------------------------
        rng = np.random.default_rng(seed=seed)
        idx = rng.permutation(n_total)

        n_train = int(n_total * 0.7)
        n_val = int(n_total * 0.15)

        train_idx = idx[:n_train]
        val_idx = idx[n_train : n_train + n_val]
        test_idx = idx[n_train + n_val :]

        np.savez(output / "train.npz", X=X[train_idx], y=y[train_idx])
        np.savez(output / "val.npz", X=X[val_idx], y=y[val_idx])
        np.savez(output / "test.npz", X=X[test_idx], y=y[test_idx])

        # ---- metadata ----------------------------------------------------
        metadata: dict[str, Any] = {
            "n_samples": n_total,
            "n_features": len(FEATURE_NAMES),
            "n_targets": len(TARGET_NAMES),
            "feature_names": FEATURE_NAMES,
            "target_names": TARGET_NAMES,
            "split_sizes": {
                "train": int(len(train_idx)),
                "val": int(len(val_idx)),
                "test": int(len(test_idx)),
            },
            "target_stds": {
                TARGET_NAMES[0]: float(y[:, 0].std()),
                TARGET_NAMES[1]: float(y[:, 1].std()),
            },
            "target_means": {
                TARGET_NAMES[0]: float(y[:, 0].mean()),
                TARGET_NAMES[1]: float(y[:, 1].mean()),
            },
            "feature_ranges": {
                name: [float(X[:, i].min()), float(X[:, i].max())]
                for i, name in enumerate(FEATURE_NAMES)
            },
            "hashes": {
                "train": _hash_file(output / "train.npz"),
                "val": _hash_file(output / "val.npz"),
                "test": _hash_file(output / "test.npz"),
            },
            "seed": seed,
            "source": "pybamm_dfn",
            "attempted": len(cell_specs),
            "failed": n_failed,
        }

        (output / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        return metadata


class NpzDatasetLoader(DatasetLoader):
    """Load a .npz dataset and verify integrity via SHA-256 hashes."""

    def load(self, dataset_path: Path | str) -> dict[str, Any]:
        """Load train/val/test splits and metadata, verifying hashes."""
        path = Path(dataset_path)
        metadata = json.loads(
            (path / "metadata.json").read_text(encoding="utf-8")
        )

        for split in ("train", "val", "test"):
            npz_path = path / f"{split}.npz"
            actual = _hash_file(npz_path)
            expected = metadata["hashes"][split]
            if actual != expected:
                raise ValueError(
                    f"Hash mismatch for {split}.npz: "
                    f"{actual} != {expected}"
                )

        data: dict[str, Any] = {}
        for split in ("train", "val", "test"):
            npz = np.load(path / f"{split}.npz")
            data[split] = {"X": npz["X"], "y": npz["y"]}

        data["metadata"] = metadata
        return data
