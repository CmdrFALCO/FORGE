"""Tests for NpzDatasetBuilder and NpzDatasetLoader using mock data."""

from __future__ import annotations

import numpy as np
import pytest

from forge.ml.common.types import CellSpec, CellType, SimulationResult
from forge.ml.dataset.npz_builder import (
    FEATURE_NAMES,
    TARGET_NAMES,
    NpzDatasetBuilder,
    NpzDatasetLoader,
)


def _make_mock_data(
    n: int = 100, n_fail: int = 0
) -> tuple[list[CellSpec], list[list[SimulationResult]]]:
    """Create n mock specs + simulation result lists (n_fail with empty results)."""
    rng = np.random.default_rng(42)
    specs: list[CellSpec] = []
    all_results: list[list[SimulationResult]] = []

    for i in range(n):
        params = {
            "electrode_thickness": rng.uniform(50, 150),
            "porosity": rng.uniform(0.20, 0.50),
            "separator_thickness": rng.uniform(10, 50),
            "n_tabs": float(rng.integers(1, 7)),
            "tab_width": rng.uniform(5, 30),
            "can_inner_diameter": rng.uniform(44, 46),
            "can_wall_thickness": rng.uniform(0.2, 0.8),
            "cell_height": rng.uniform(65, 95),
            "surface_to_volume": rng.uniform(0.05, 0.12),
            "tab_conductance_proxy": rng.uniform(5, 180),
            "diffusion_path_proxy": rng.uniform(100, 750),
        }
        spec = CellSpec(cell_type=CellType.CYLINDRICAL, parameters=params)
        specs.append(spec)

        if i < n_fail:
            # Failed simulation
            all_results.append([
                SimulationResult(cell_spec=spec, c_rate=0.2, success=False,
                                 error_message="solver diverged"),
            ])
        else:
            # Successful simulation results
            q_02 = rng.uniform(3.0, 5.0)
            q_3c = rng.uniform(1.5, 4.5)
            t_max = rng.uniform(30.0, 75.0)
            results = [
                SimulationResult(cell_spec=spec, c_rate=0.2,
                                 capacity_ah=q_02, success=True),
                SimulationResult(cell_spec=spec, c_rate=3.0,
                                 capacity_ah=q_3c, success=True),
                SimulationResult(cell_spec=spec, c_rate=0.0,
                                 max_temperature_celsius=t_max, success=True),
            ]
            all_results.append(results)

    return specs, all_results


class TestBuildBasic:
    def test_files_created(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(100)
        builder = NpzDatasetBuilder()
        builder.build(specs, results, output_path=tmp_path / "ds")

        for f in ("train.npz", "val.npz", "test.npz", "metadata.json"):
            assert (tmp_path / "ds" / f).exists()

    def test_split_sizes_sum(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(100)
        builder = NpzDatasetBuilder()
        meta = builder.build(specs, results, output_path=tmp_path / "ds")

        total = (
            meta["split_sizes"]["train"]
            + meta["split_sizes"]["val"]
            + meta["split_sizes"]["test"]
        )
        assert total == meta["n_samples"]

    def test_split_ratio(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(100)
        builder = NpzDatasetBuilder()
        meta = builder.build(specs, results, output_path=tmp_path / "ds")

        n = meta["n_samples"]
        assert meta["split_sizes"]["train"] == int(n * 0.7)
        assert meta["split_sizes"]["val"] == int(n * 0.15)


class TestBuildWithFailures:
    def test_failures_dropped(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(100, n_fail=10)
        builder = NpzDatasetBuilder()
        meta = builder.build(specs, results, output_path=tmp_path / "ds")

        assert meta["n_samples"] == 90
        assert meta["failed"] == 10
        assert meta["attempted"] == 100


class TestFeatureColumns:
    def test_feature_count(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        meta = builder.build(specs, results, output_path=tmp_path / "ds")

        assert len(meta["feature_names"]) == 11
        data = np.load(tmp_path / "ds" / "train.npz")
        assert data["X"].shape[1] == 11

    def test_feature_names_match(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        meta = builder.build(specs, results, output_path=tmp_path / "ds")

        assert meta["feature_names"] == FEATURE_NAMES


class TestTargetColumns:
    def test_target_count(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        meta = builder.build(specs, results, output_path=tmp_path / "ds")

        assert len(meta["target_names"]) == 2
        data = np.load(tmp_path / "ds" / "train.npz")
        assert data["y"].shape[1] == 2

    def test_target_stds_positive(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        meta = builder.build(specs, results, output_path=tmp_path / "ds")

        for name in TARGET_NAMES:
            assert meta["target_stds"][name] > 0


class TestHashIntegrity:
    def test_load_verifies_ok(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        builder.build(specs, results, output_path=tmp_path / "ds")

        loader = NpzDatasetLoader()
        data = loader.load(tmp_path / "ds")
        assert "train" in data
        assert "metadata" in data

    def test_corrupted_file_raises(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        builder.build(specs, results, output_path=tmp_path / "ds")

        # Corrupt the train file
        train_path = tmp_path / "ds" / "train.npz"
        content = bytearray(train_path.read_bytes())
        content[100] ^= 0xFF
        train_path.write_bytes(bytes(content))

        loader = NpzDatasetLoader()
        with pytest.raises(ValueError, match="Hash mismatch"):
            loader.load(tmp_path / "ds")


class TestReproducibility:
    def test_same_seed_same_hashes(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        m1 = builder.build(specs, results, output_path=tmp_path / "ds1", seed=42)
        m2 = builder.build(specs, results, output_path=tmp_path / "ds2", seed=42)

        assert m1["hashes"] == m2["hashes"]


class TestLoaderRoundTrip:
    def test_arrays_match(self, tmp_path: "pytest.TempPathFactory") -> None:
        specs, results = _make_mock_data(50)
        builder = NpzDatasetBuilder()
        builder.build(specs, results, output_path=tmp_path / "ds")

        loader = NpzDatasetLoader()
        data = loader.load(tmp_path / "ds")

        # Verify shapes
        for split in ("train", "val", "test"):
            assert data[split]["X"].shape[1] == 11
            assert data[split]["y"].shape[1] == 2
