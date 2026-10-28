"""CLI, machine-readable artifacts, and optional headless charts."""

import argparse
import csv
import json
import re
from dataclasses import asdict
from pathlib import Path

from .core import ALGORITHMS, simulate
from .experiment import run_experiment


def read_sequence(path: Path) -> list[int]:
    tokens = re.split(r"[\s,]+", path.read_text(encoding="utf-8-sig").strip())
    try:
        pages = [int(token) for token in tokens if token]
    except ValueError as exc:
        raise ValueError(
            "input must contain integer page IDs separated by commas or whitespace"
        ) from exc
    if not pages:
        raise ValueError("input sequence cannot be empty")
    return pages


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_results(summary: list[dict], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with plt.rc_context({"font.family": "DejaVu Sans", "svg.hashsalt": "page-replacement"}):
        fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
        colors = ["#2563eb", "#d97706", "#0f766e", "#7c3aed"]
        for algorithm, color in zip(ALGORITHMS, colors, strict=True):
            rows = sorted(
                (r for r in summary if r["algorithm"] == algorithm), key=lambda r: r["frames"]
            )
            ax.errorbar(
                [r["frames"] for r in rows],
                [r["mean_faults"] for r in rows],
                yerr=[r["stdev_faults"] for r in rows],
                marker="o",
                capsize=4,
                color=color,
                label=algorithm,
            )
        ax.set(
            xlabel="Available frames",
            ylabel="Page faults",
            title="Replacement policies on identical page-reference sequences",
        )
        ax.set_xticks(sorted({r["frames"] for r in summary}))
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False)
        fig.suptitle(
            "Points: mean · error bars: sample standard deviation", fontsize=10, color="#475569"
        )
        fig.savefig(output, metadata={"Date": None})
        plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare FIFO, MFU, LRU, and OPT on paired workloads."
    )
    parser.add_argument("--input", type=Path, help="page IDs separated by whitespace or commas")
    parser.add_argument("--frames", type=int, nargs="+", default=[2, 3, 4, 5, 6])
    parser.add_argument("--length", type=int, default=200)
    parser.add_argument("--pages", type=int, default=10)
    parser.add_argument("--locality", type=float, default=0.6)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--trace",
        action="store_true",
        help="export each access for the first workload and frame count",
    )
    parser.add_argument(
        "--plot", action="store_true", help="save comparison.svg (requires plotting extra)"
    )
    args = parser.parse_args(argv)
    try:
        fixed = read_sequence(args.input) if args.input else None
        workloads, runs, summary = run_experiment(
            args.frames,
            length=args.length,
            page_range=args.pages,
            locality=args.locality,
            repetitions=args.repetitions,
            seed=args.seed,
            sequence=fixed,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(args.output_dir / "runs.csv", runs)
        write_csv(
            args.output_dir / "workloads.csv",
            [
                {"repetition": i, "position": position, "page": page}
                for i, workload in enumerate(workloads)
                for position, page in enumerate(workload)
            ],
        )
        report = {
            "schema_version": 1,
            "parameters": {
                "source": str(args.input) if args.input else "generated",
                "frames": args.frames,
                "length": len(workloads[0]),
                "repetitions": len(workloads),
                "seed": None if fixed is not None else args.seed,
                "pages": None if fixed is not None else args.pages,
                "locality": None if fixed is not None else args.locality,
            },
            "summary": summary,
        }
        (args.output_dir / "summary.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        if args.trace:
            rows = []
            for algorithm in ALGORITHMS:
                result = simulate(workloads[0], args.frames[0], algorithm, trace=True)
                for access in result.trace:
                    row = {"algorithm": algorithm, **asdict(access)}
                    row["frames"] = " ".join(map(str, access.frames))
                    rows.append(row)
            write_csv(args.output_dir / "trace.csv", rows)
        if args.plot:
            plot_results(summary, args.output_dir / "comparison.svg")
    except ImportError:
        parser.error('plotting requires: python -m pip install ".[plot]"')
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"{'Frames':>6} {'Algorithm':<10} {'Mean faults':>12} {'Std dev':>10} {'Fault rate':>12}")
    for row in summary:
        print(
            f"{row['frames']:>6} {row['algorithm']:<10} {row['mean_faults']:>12.2f} "
            f"{row['stdev_faults']:>10.2f} {row['mean_fault_rate']:>11.1%}"
        )
    print(f"Results saved to {args.output_dir}")
    return 0
