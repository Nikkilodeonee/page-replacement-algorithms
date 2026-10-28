# Engineering notes

## Experiment design

A local random generator creates one workload per repetition using seed + i.
That workload is shared by every policy and frame capacity. Each run starts
with cold memory and new policy state. Pairing avoids comparing different traces
when the policy or capacity is changed.

The summary reports arithmetic mean faults and mean fault rate. Variability is
sample standard deviation (denominator n − 1). A single observation reports zero
spread as a display convention, not evidence of zero population variance.
Statistics retain full precision; there is no integer truncation of averages.

Adjacent seeds are a convenient reproducible sampling scheme. They do not prove
that this synthetic workload represents real memory access patterns. There are
no significance tests or claims that one online policy always wins.

## Policy details and complexity

Let n be reference count, f frame capacity, and u distinct pages in a trace.

| Policy | Replacement processing | Metadata |
| --- | --- | --- |
| FIFO | O(n) | O(f) |
| LRU | O(n) | O(f) |
| MFU | O(n f) worst case | O(f + u), including lifetime counts |
| OPT | O(n f) worst case after O(n) future indexing | O(n + f) |

The shared API also materializes the input tuple: every policy therefore needs
O(n) input storage. Optional step tracing copies and sorts up to f residents
per reference, adding O(n f log f) time and O(n f) output space in the worst
case. The experiment runner stores all workloads and observations.
These are implementation bounds, not wall-clock measurements.

MFU retains lifetime counts after eviction. Equal frequencies evict the page
loaded earliest in its current residency. OPT ties (including pages never used
again) use that same earliest-load rule. LRU recency changes on every hit;
FIFO insertion order changes only on a miss.

An access trace lists frames in ascending page-ID order for readability. That
display order is not FIFO order or LRU order.

## Correctness evidence

The classic Belady sequence guards against the false assumption that FIFO faults
must fall as capacity grows. LRU/OPT monotonicity is also checked over generated
traces. Every policy must account for every access, respect capacity, and have
at least as many faults as OPT.

OPT is tested against an independent exhaustive solver that tries every possible
eviction for every six-reference trace over three pages (729 workloads with two
frames). The solver does not use future-distance eviction logic.

MFU tests distinguish lifetime counting from residency-only counting and require
a stable tie rule. Experiment tests verify shared inputs, independence from the
order of capacities, and byte-identical CSV/JSON exports on repeat runs.

## Reproduction and output behavior

Retain raw workloads alongside summary statistics. Seeded generation is intended
to repeat on the same Python implementation; exported page references remain
the durable record if random-number generation internals change.

Rerunning into an existing output directory replaces named artifacts. Use a new
directory to preserve an experiment. Exports are not atomic; I/O or plotting
failures can leave partial files. The core does not write files or import
Matplotlib. The CLI returns exit status 2 for invalid input.

## Portfolio and interview talking points

CV wording, after reviewing the implementation:

> Extended a Python page-replacement simulator to compare FIFO, MFU, LRU and an
> optimal baseline using paired seeded experiments, CSV/JSON reports, eviction
> traces and 21 automated tests, including an exhaustive correctness oracle.

Be ready to trace Belady's anomaly by hand, explain the difference between MFU
and LFU, justify frequency/tie semantics, distinguish online policies from OPT,
and explain why standard deviation is not a confidence interval.

Original scope: FIFO/MFU with randomly generated workloads and charts.
Extensions: explicit ties, seeded paired comparisons, full-precision statistics,
LRU/OPT, future-position indexing, per-access traces, CLI input/exports,
packaging, regression tests and CI.

## Background

- [OSTEP: Beyond Physical Memory — Policies](https://pages.cs.wisc.edu/~remzi/OSTEP/vm-beyondphys-policy.pdf)
