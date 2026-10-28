"""Paired workloads and full-precision repeated experiment summaries."""

from collections.abc import Iterable
from statistics import mean, stdev

from .core import ALGORITHMS, generate_page_sequence, positive_integer, simulate


def run_experiment(
    frames: Iterable[int] = (2, 3, 4, 5, 6),
    *,
    length: int = 200,
    page_range: int = 10,
    locality: float = 0.6,
    repetitions: int = 10,
    seed: int = 42,
    sequence: Iterable[int] | None = None,
) -> tuple[list[list[int]], list[dict], list[dict]]:
    capacities = list(frames)
    if not capacities or len(capacities) != len(set(capacities)):
        raise ValueError("frames must contain distinct positive integers")
    for capacity in capacities:
        positive_integer(capacity, "frames")
    positive_integer(repetitions, "repetitions")
    if sequence is None:
        workloads = [
            generate_page_sequence(length, page_range, locality, seed + i)
            for i in range(repetitions)
        ]
    else:
        workload = list(sequence)
        if not workload:
            raise ValueError("input sequence cannot be empty")
        # Repeating the same fixed trace would not provide independent observations.
        workloads = [workload]
    runs = []
    for repetition, workload in enumerate(workloads):
        for capacity in capacities:
            for algorithm in ALGORITHMS:
                result = simulate(workload, capacity, algorithm)
                runs.append(
                    {
                        "repetition": repetition,
                        "frames": capacity,
                        "algorithm": algorithm,
                        "faults": result.page_faults,
                        "hits": result.page_hits,
                        "fault_rate": result.fault_rate,
                    }
                )
    summary = []
    for capacity in capacities:
        for algorithm in ALGORITHMS:
            samples = [r for r in runs if r["frames"] == capacity and r["algorithm"] == algorithm]
            faults = [r["faults"] for r in samples]
            summary.append(
                {
                    "frames": capacity,
                    "algorithm": algorithm,
                    "repetitions": len(samples),
                    "mean_faults": mean(faults),
                    "stdev_faults": stdev(faults) if len(faults) > 1 else 0.0,
                    "mean_fault_rate": mean(r["fault_rate"] for r in samples),
                }
            )
    return workloads, runs, summary
