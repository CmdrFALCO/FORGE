"""Result dataclasses and TSV persistence for autoresearch runs."""

import csv
from dataclasses import dataclass
from pathlib import Path

from .constants import PRIMARY_SCORE, REQUIRED_KEYS

_METRIC_COLUMNS = sorted(REQUIRED_KEYS)
_FIXED_COLUMNS = ["experiment_id", PRIMARY_SCORE, "accepted", "reason", "timestamp", "git_hash"]
_ALL_COLUMNS = _FIXED_COLUMNS + _METRIC_COLUMNS


@dataclass(slots=True)
class RunResult:
    """One experiment result row."""

    experiment_id: int
    metrics: dict[str, float]
    primary_score: float
    accepted: bool
    reason: str
    timestamp: str
    git_hash: str = ""


class ResultsLog:
    """TSV-backed result log with leaderboard helpers."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, result: RunResult) -> None:
        """Append a run result to TSV, creating file and header if needed."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.path.exists()

        row: dict[str, str] = {
            "experiment_id": str(result.experiment_id),
            PRIMARY_SCORE: f"{result.primary_score:.12g}",
            "accepted": str(result.accepted),
            "reason": result.reason,
            "timestamp": result.timestamp,
            "git_hash": result.git_hash,
        }
        for key in _METRIC_COLUMNS:
            value = result.metrics.get(key)
            row[key] = "" if value is None else f"{value:.12g}"

        with self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=_ALL_COLUMNS, delimiter="\t")
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    def load(self) -> list[RunResult]:
        """Load all rows from TSV as RunResult objects."""
        if not self.path.exists():
            return []

        results: list[RunResult] = []
        with self.path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                metrics: dict[str, float] = {}
                for key in _METRIC_COLUMNS:
                    raw = row.get(key, "")
                    if raw:
                        metrics[key] = float(raw)

                accepted_raw = (row.get("accepted") or "").strip().lower()
                accepted = accepted_raw in {"true", "1", "yes"}

                results.append(
                    RunResult(
                        experiment_id=int(row["experiment_id"]),
                        metrics=metrics,
                        primary_score=float(row[PRIMARY_SCORE]),
                        accepted=accepted,
                        reason=row.get("reason", ""),
                        timestamp=row.get("timestamp", ""),
                        git_hash=row.get("git_hash", ""),
                    )
                )
        return results

    def get_best(self) -> RunResult | None:
        """Return the best accepted result by primary score."""
        accepted = [result for result in self.load() if result.accepted]
        if not accepted:
            return None
        return min(accepted, key=lambda item: item.primary_score)

    def get_leaderboard(self, top_n: int = 10) -> list[RunResult]:
        """Return top N accepted results sorted by primary score ascending."""
        accepted = [result for result in self.load() if result.accepted]
        accepted.sort(key=lambda item: item.primary_score)
        return accepted[:top_n]

