import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import qmc

SAMPLED_FEATURES = [
    "electrode_thickness",
    "porosity",
    "separator_thickness",
    "n_tabs",
    "tab_width",
    "can_inner_diameter",
    "can_wall_thickness",
    "cell_height",
]

FEATURE_RANGES = {
    "electrode_thickness": (50.0, 150.0),
    "porosity": (0.20, 0.50),
    "separator_thickness": (10.0, 50.0),
    "n_tabs": (1.0, 6.0),
    "tab_width": (5.0, 30.0),
    "can_inner_diameter": (44.0, 46.0),
    "can_wall_thickness": (0.2, 0.8),
    "cell_height": (65.0, 95.0),
}

DERIVED_FEATURES = [
    "surface_to_volume",
    "tab_conductance_proxy",
    "diffusion_path_proxy",
]

FEATURE_NAMES = SAMPLED_FEATURES + DERIVED_FEATURES
TARGET_NAMES = ["rate_capability_proxy", "max_temp_proxy"]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic L2-B dataset")
    parser.add_argument("--n-samples", type=int, default=2000, help="Total number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser


def _sample_lhs(n_samples: int, seed: int) -> np.ndarray:
    lower = np.array([FEATURE_RANGES[name][0] for name in SAMPLED_FEATURES], dtype=np.float64)
    upper = np.array([FEATURE_RANGES[name][1] for name in SAMPLED_FEATURES], dtype=np.float64)
    sampler = qmc.LatinHypercube(d=len(SAMPLED_FEATURES), seed=seed)
    unit = sampler.random(n=n_samples)
    sampled = qmc.scale(unit, lower, upper)

    n_tabs_idx = SAMPLED_FEATURES.index("n_tabs")
    sampled[:, n_tabs_idx] = np.clip(np.rint(sampled[:, n_tabs_idx]), 1.0, 6.0)
    return sampled


def _compose_features(sampled: np.ndarray) -> np.ndarray:
    electrode_thickness = sampled[:, 0]
    porosity = sampled[:, 1]
    separator_thickness = sampled[:, 2]
    n_tabs = sampled[:, 3]
    tab_width = sampled[:, 4]
    can_inner_diameter = sampled[:, 5]
    can_wall_thickness = sampled[:, 6]
    cell_height = sampled[:, 7]

    surface_to_volume = 2.0 / (can_inner_diameter / 2.0) + 2.0 / cell_height
    tab_conductance_proxy = n_tabs * tab_width
    diffusion_path_proxy = electrode_thickness / np.maximum(porosity, 1e-6)

    features = np.column_stack(
        [
            electrode_thickness,
            porosity,
            separator_thickness,
            n_tabs,
            tab_width,
            can_inner_diameter,
            can_wall_thickness,
            cell_height,
            surface_to_volume,
            tab_conductance_proxy,
            diffusion_path_proxy,
        ]
    )
    return features.astype(np.float32)


def _compute_targets(features: np.ndarray, rng: np.random.Generator, noise: bool = True) -> np.ndarray:
    electrode_thickness = features[:, 0].astype(np.float64)
    porosity = features[:, 1].astype(np.float64)
    separator_thickness = features[:, 2].astype(np.float64)
    n_tabs = features[:, 3].astype(np.float64)
    can_wall_thickness = features[:, 6].astype(np.float64)
    cell_height = features[:, 7].astype(np.float64)
    surface_to_volume = features[:, 8].astype(np.float64)
    tab_conductance_proxy = features[:, 9].astype(np.float64)
    diffusion_path_proxy = features[:, 10].astype(np.float64)

    tab_term = np.tanh(tab_conductance_proxy / 80.0)
    diffusion_term = 1.0 / (1.0 + np.exp((diffusion_path_proxy - 350.0) / 40.0))
    separator_penalty = 0.002 * (separator_thickness - 10.0)
    interaction_penalty = 0.00004 * electrode_thickness * porosity

    rate = 0.15 + 0.55 * tab_term + 0.40 * diffusion_term - separator_penalty - interaction_penalty
    if noise:
        rate = rate + rng.normal(0.0, 0.01, size=rate.shape)
    rate = np.clip(rate, 0.0, 1.0)

    inv_surface_to_volume = 1.0 / np.maximum(surface_to_volume, 1e-6)
    thickness_threshold = np.log1p(np.exp((electrode_thickness - 100.0) / 8.0))
    thermal_mass_proxy = can_wall_thickness * cell_height
    tabs_penalty = 3.0 / np.maximum(n_tabs, 1.0)

    max_temp = (
        30.0
        + 4.0 * inv_surface_to_volume
        + 2.8 * thickness_threshold
        - 0.015 * thermal_mass_proxy
        + tabs_penalty
    )
    if noise:
        max_temp = max_temp + rng.normal(0.0, 0.5, size=max_temp.shape)

    targets = np.column_stack([rate, max_temp]).astype(np.float32)
    return targets


def _run_sanity_assertions() -> None:
    mid = np.array(
        [
            100.0,
            0.35,
            30.0,
            3.0,
            15.0,
            45.0,
            0.5,
            80.0,
        ],
        dtype=np.float32,
    )
    rng = np.random.default_rng(12345)

    thin = mid.copy()
    thin[0] = 60.0
    thick = mid.copy()
    thick[0] = 140.0
    X_pair = _compose_features(np.vstack([thin, thick]))
    y_pair = _compute_targets(X_pair, rng=rng, noise=False)
    if not (y_pair[1, 0] < y_pair[0, 0]):
        raise AssertionError("Sanity check failed: thicker electrode should lower rate_capability_proxy")

    low_mass = mid.copy()
    low_mass[6] = 0.25
    high_mass = mid.copy()
    high_mass[6] = 0.75
    X_pair = _compose_features(np.vstack([low_mass, high_mass]))
    y_pair = _compute_targets(X_pair, rng=rng, noise=False)
    if not (y_pair[1, 1] < y_pair[0, 1]):
        raise AssertionError("Sanity check failed: higher thermal mass should lower max_temp_proxy")

    few_tabs = mid.copy()
    few_tabs[3] = 1.0
    more_tabs = mid.copy()
    more_tabs[3] = 6.0
    X_pair = _compose_features(np.vstack([few_tabs, more_tabs]))
    y_pair = _compute_targets(X_pair, rng=rng, noise=False)
    if not (y_pair[1, 0] > y_pair[0, 0]):
        raise AssertionError("Sanity check failed: more tabs should increase rate_capability_proxy")


def _split_dataset(
    features: np.ndarray,
    targets: np.ndarray,
    seed: int,
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    n_samples = features.shape[0]
    n_train = int(n_samples * 0.70)
    n_val = int(n_samples * 0.15)
    rng = np.random.default_rng(seed)
    indices = rng.permutation(n_samples)

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    return (
        (features[train_idx], targets[train_idx]),
        (features[val_idx], targets[val_idx]),
        (features[test_idx], targets[test_idx]),
    )


def main() -> int:
    args = _build_parser().parse_args()
    if args.n_samples < 10:
        print("n_samples must be at least 10", file=sys.stderr)
        return 1

    try:
        _run_sanity_assertions()
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    sampled = _sample_lhs(n_samples=args.n_samples, seed=args.seed)
    features = _compose_features(sampled)

    noise_rng = np.random.default_rng(args.seed)
    targets = _compute_targets(features, rng=noise_rng, noise=True)

    (X_train, y_train), (X_val, y_val), (X_test, y_test) = _split_dataset(features, targets, seed=args.seed)

    dataset_dir = Path(__file__).resolve().parent / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    train_path = dataset_dir / "train.npz"
    val_path = dataset_dir / "val.npz"
    test_path = dataset_dir / "test.npz"
    metadata_path = dataset_dir / "metadata.json"

    np.savez(train_path, X=X_train.astype(np.float32), y=y_train.astype(np.float32))
    np.savez(val_path, X=X_val.astype(np.float32), y=y_val.astype(np.float32))
    np.savez(test_path, X=X_test.astype(np.float32), y=y_test.astype(np.float32))

    train_hash = _sha256_file(train_path)
    val_hash = _sha256_file(val_path)
    test_hash = _sha256_file(test_path)
    dataset_hash = hashlib.sha256(f"{train_hash}{val_hash}{test_hash}".encode("ascii")).hexdigest()

    target_stds = y_train.std(axis=0, ddof=0)
    target_means = y_train.mean(axis=0)

    metadata = {
        "n_samples": int(args.n_samples),
        "n_features": int(features.shape[1]),
        "n_targets": int(targets.shape[1]),
        "feature_names": FEATURE_NAMES,
        "target_names": TARGET_NAMES,
        "split_sizes": {
            "train": int(X_train.shape[0]),
            "val": int(X_val.shape[0]),
            "test": int(X_test.shape[0]),
        },
        "target_stds": {
            TARGET_NAMES[0]: float(target_stds[0]),
            TARGET_NAMES[1]: float(target_stds[1]),
        },
        "target_means": {
            TARGET_NAMES[0]: float(target_means[0]),
            TARGET_NAMES[1]: float(target_means[1]),
        },
        "feature_ranges": {name: [float(FEATURE_RANGES[name][0]), float(FEATURE_RANGES[name][1])] for name in SAMPLED_FEATURES},
        "seed": int(args.seed),
        "hashes": {
            "train": train_hash,
            "val": val_hash,
            "test": test_hash,
            "dataset": dataset_hash,
        },
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("Dataset generated successfully")
    print(f"train: X={X_train.shape}, y={y_train.shape}")
    print(f"val:   X={X_val.shape}, y={y_val.shape}")
    print(f"test:  X={X_test.shape}, y={y_test.shape}")
    print(
        "target means/stds (train only): "
        f"rate=({target_means[0]:.6f}, {target_stds[0]:.6f}), "
        f"temp=({target_means[1]:.6f}, {target_stds[1]:.6f})"
    )
    print(f"dataset hash: {dataset_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
