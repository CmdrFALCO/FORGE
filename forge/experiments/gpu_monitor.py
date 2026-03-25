"""
GPU power monitoring for AXIOM experiment cost calculation.

Spawned as a subprocess during Exp 3 runs (Ollama / local inference).
Polls nvidia-smi at regular intervals and writes CSV output for
post-hoc energy-cost analysis in Phase 5.

Usage (standalone):
    python -m forge.experiments.gpu_monitor \
        --output forge/experiments/results/gpu_logs/exp3a_gpu.csv \
        --interval 5 \
        --gpu 0

The experiment runner starts/stops this automatically for exp3a and exp3b.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CSV_HEADER = [
    "timestamp",
    "gpu_index",
    "power_draw_w",
    "gpu_util_pct",
    "memory_used_mb",
    "memory_total_mb",
    "temperature_c",
]

# nvidia-smi query fields matching the CSV columns above
_QUERY_FIELDS = (
    "index,"
    "power.draw,"
    "utilization.gpu,"
    "memory.used,"
    "memory.total,"
    "temperature.gpu"
)


def _query_nvidia_smi(gpu_index: int) -> dict[str, str | float | int] | None:
    """Run nvidia-smi and parse one row of GPU metrics.

    Returns None if nvidia-smi is unavailable or the query fails.
    """
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                f"--id={gpu_index}",
                f"--query-gpu={_QUERY_FIELDS}",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None

    if proc.returncode != 0:
        return None

    parts = [p.strip() for p in proc.stdout.strip().split(",")]
    if len(parts) != 6:
        return None

    try:
        return {
            "gpu_index": int(parts[0]),
            "power_draw_w": float(parts[1]),
            "gpu_util_pct": int(parts[2]),
            "memory_used_mb": int(parts[3]),
            "memory_total_mb": int(parts[4]),
            "temperature_c": int(parts[5]),
        }
    except (ValueError, IndexError):
        return None


def run_monitor(
    output_path: str | Path,
    interval: float = 5.0,
    gpu_index: int = 0,
) -> None:
    """Blocking loop: poll nvidia-smi and append rows to *output_path*.

    Designed to run in a subprocess. Terminates on SIGTERM / SIGINT / EOF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_path.exists() and output_path.stat().st_size > 0

    with open(output_path, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
            fh.flush()

        print(
            f"[gpu_monitor] Logging GPU {gpu_index} every {interval}s "
            f"-> {output_path}",
            flush=True,
        )

        try:
            while True:
                row = _query_nvidia_smi(gpu_index)
                if row is not None:
                    row["timestamp"] = (
                        datetime.now(tz=timezone.utc)
                        .isoformat(timespec="milliseconds")
                        .replace("+00:00", "Z")
                    )
                    writer.writerow(row)
                    fh.flush()
                time.sleep(interval)
        except KeyboardInterrupt:
            pass

    print("[gpu_monitor] Stopped.", flush=True)


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GPU power / utilisation logger for AXIOM experiments.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output CSV file.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Polling interval in seconds (default: 5).",
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=0,
        dest="gpu_index",
        help="GPU index to monitor (default: 0).",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    run_monitor(
        output_path=args.output,
        interval=args.interval,
        gpu_index=args.gpu_index,
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
