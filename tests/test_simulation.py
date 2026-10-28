"""Textbook examples, exhaustive OPT oracle, and reproducible experiments."""

import contextlib
import functools
import io
import itertools
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from statistics import mean

from page_replacement import ALGORITHMS, generate_page_sequence, simulate
from page_replacement.cli import main
from page_replacement.experiment import run_experiment

BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


class PolicyTests(unittest.TestCase):
    def test_fifo_belady_anomaly(self):
        self.assertEqual(simulate(BELADY, 3, "FIFO").page_faults, 9)
        self.assertEqual(simulate(BELADY, 4, "FIFO").page_faults, 10)

    def test_known_lru_and_opt_counts(self):
        self.assertEqual(simulate(BELADY, 3, "LRU").page_faults, 10)
        self.assertEqual(simulate(BELADY, 3, "OPT").page_faults, 7)

    def test_fifo_hits_do_not_refresh_load_order(self):
        result = simulate([1, 2, 1, 3], 2, "FIFO", trace=True)
        self.assertEqual(result.trace[-1].evicted, 1)

    def test_lru_hits_refresh_recency(self):
        result = simulate([1, 2, 1, 3], 2, "LRU", trace=True)
        self.assertEqual(result.trace[-1].evicted, 2)

    def test_mfu_evicts_most_used_resident(self):
        result = simulate([1, 1, 2, 3], 2, "MFU", trace=True)
        self.assertEqual(result.trace[-1].evicted, 1)

    def test_mfu_ties_use_earliest_load(self):
        result = simulate([7, 2, 9], 2, "MFU", trace=True)
        self.assertEqual(result.trace[-1].evicted, 7)

    def test_mfu_retains_frequency_after_eviction(self):
        result = simulate([1, 1, 2, 3, 1, 4], 2, "MFU", trace=True)
        self.assertEqual(result.trace[-1].evicted, 1)

    def test_opt_evicts_farthest_next_reference(self):
        result = simulate([1, 2, 3, 1, 2], 2, "OPT", trace=True)
        self.assertEqual(result.trace[2].evicted, 2)

    def test_empty_single_page_and_sufficient_capacity(self):
        for algorithm in ALGORITHMS:
            self.assertEqual(simulate([], 1, algorithm).fault_rate, 0)
            result = simulate([0] * 10, 1, algorithm)
            self.assertEqual((result.page_faults, result.page_hits), (1, 9))
            self.assertEqual(simulate(BELADY, 5, algorithm).page_faults, 5)

    def test_validation(self):
        for frames in [0, -1, 1.5, True]:
            with self.assertRaises(ValueError):
                simulate([1], frames, "FIFO")
        for sequence in [[-1], [1.5], [True]]:
            with self.assertRaises(ValueError):
                simulate(sequence, 2, "FIFO")
        with self.assertRaises(ValueError):
            simulate([1], 2, "unknown")

    def test_invariants_and_opt_lower_bound(self):
        for seed in range(20):
            pages = generate_page_sequence(100, seed=seed)
            for frames in range(1, 7):
                optimum = simulate(pages, frames, "OPT").page_faults
                for algorithm in ALGORITHMS:
                    result = simulate(pages, frames, algorithm, trace=True)
                    self.assertEqual(result.page_faults + result.page_hits, len(pages))
                    self.assertGreaterEqual(result.page_faults, optimum)
                    self.assertTrue(
                        all(len(a.frames) <= frames and a.page in a.frames for a in result.trace)
                    )
                    self.assertEqual(sum(not a.hit for a in result.trace), result.page_faults)

    def test_opt_matches_exhaustive_eviction_oracle(self):
        # Try every possible eviction, independent of the production OPT implementation.
        for pages in itertools.product(range(3), repeat=6):

            @functools.lru_cache(None)
            def minimum_faults(position, residents, pages=pages):
                if position == len(pages):
                    return 0
                memory = set(residents)
                page = pages[position]
                if page in memory:
                    return minimum_faults(position + 1, residents)
                if len(memory) < 2:
                    return 1 + minimum_faults(position + 1, tuple(sorted(memory | {page})))
                return 1 + min(
                    minimum_faults(position + 1, tuple(sorted((memory - {p}) | {page})))
                    for p in memory
                )

            self.assertEqual(simulate(pages, 2, "OPT").page_faults, minimum_faults(0, ()))

    def test_lru_and_opt_faults_do_not_increase_with_capacity(self):
        for seed in range(10):
            pages = generate_page_sequence(100, seed=seed)
            for algorithm in ["LRU", "OPT"]:
                faults = [simulate(pages, n, algorithm).page_faults for n in range(1, 11)]
                self.assertEqual(faults, sorted(faults, reverse=True))

    def test_generator_seed_is_local(self):
        state = random.getstate()
        self.assertEqual(generate_page_sequence(seed=5), generate_page_sequence(seed=5))
        self.assertNotEqual(generate_page_sequence(seed=5), generate_page_sequence(seed=6))
        self.assertEqual(random.getstate(), state)

    def test_generator_bounds_and_validation(self):
        for locality in [0, 0.5, 1]:
            pages = generate_page_sequence(100, 3, locality)
            self.assertEqual(len(pages), 100)
            self.assertTrue(all(0 <= page < 3 for page in pages))
        for kwargs in [
            {"length": 0},
            {"page_range": 0},
            {"locality_factor": -1},
            {"locality_factor": float("nan")},
        ]:
            with self.assertRaises(ValueError):
                generate_page_sequence(**kwargs)


class ExperimentTests(unittest.TestCase):
    def test_all_policies_and_capacities_share_each_workload(self):
        workloads, runs, summary = run_experiment([2, 3], repetitions=3)
        for row in runs:
            expected = simulate(workloads[row["repetition"]], row["frames"], row["algorithm"])
            self.assertEqual(row["faults"], expected.page_faults)
        for row in summary:
            samples = [
                r["faults"]
                for r in runs
                if r["frames"] == row["frames"] and r["algorithm"] == row["algorithm"]
            ]
            self.assertEqual(row["mean_faults"], mean(samples))

    def test_frame_order_does_not_change_workloads_or_results(self):
        first = run_experiment([2, 3])
        second = run_experiment([3, 2])
        self.assertEqual(first[0], second[0])

        def key(row):
            return (row["repetition"], row["frames"], row["algorithm"])

        self.assertEqual(sorted(first[1], key=key), sorted(second[1], key=key))

    def test_fixed_input_runs_once(self):
        workloads, runs, summary = run_experiment([3], repetitions=30, sequence=BELADY)
        self.assertEqual(workloads, [BELADY])
        self.assertEqual(len(runs), 4)
        self.assertTrue(all(r["repetitions"] == 1 and r["stdev_faults"] == 0 for r in summary))

    def test_invalid_parameters(self):
        for kwargs in [{"frames": []}, {"frames": [2, 2]}, {"repetitions": 0}, {"sequence": []}]:
            with self.assertRaises(ValueError):
                run_experiment(**kwargs)

    def test_cli_exports_reproducibly(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temporary)
            for name in ["one", "two"]:
                main(
                    [
                        "--frames",
                        "3",
                        "4",
                        "--repetitions",
                        "3",
                        "--trace",
                        "--output-dir",
                        str(root / name),
                    ]
                )
            for name in ["summary.json", "runs.csv", "workloads.csv", "trace.csv"]:
                self.assertEqual(
                    (root / "one" / name).read_bytes(), (root / "two" / name).read_bytes()
                )
            report = json.loads((root / "one/summary.json").read_text())
            self.assertEqual(report["parameters"]["repetitions"], 3)
            self.assertEqual(len(report["summary"]), 8)

    def test_cli_rejects_invalid_values_without_traceback(self):
        for args in [["--frames", "0"], ["--locality", "nan"]]:
            result = subprocess.run(
                [sys.executable, "main.py", *args], capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
