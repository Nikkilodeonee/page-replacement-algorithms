"""Replacement policies with explicit, deterministic eviction semantics."""

from collections import Counter, OrderedDict, defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from random import Random

ALGORITHMS = ("FIFO", "MFU", "LRU", "OPT")


def positive_integer(value: int, name: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class Access:
    position: int
    page: int
    hit: bool
    evicted: int | None
    frames: tuple[int, ...]


@dataclass(frozen=True)
class SimulationResult:
    algorithm: str
    num_frames: int
    page_faults: int
    page_hits: int
    trace: tuple[Access, ...]

    @property
    def fault_rate(self) -> float:
        accesses = self.page_faults + self.page_hits
        return self.page_faults / accesses if accesses else 0.0


def simulate(
    sequence: Iterable[int],
    num_frames: int,
    algorithm: str,
    *,
    trace: bool = False,
) -> SimulationResult:
    """Run one policy with fresh state. OPT requires the complete future trace.

    MFU counts references over the whole run (including previous residencies).
    MFU/OPT ties evict the earliest-loaded resident page.
    """
    positive_integer(num_frames, "num_frames")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"algorithm must be one of {', '.join(ALGORITHMS)}")
    pages = tuple(sequence)
    if any(type(page) is not int or page < 0 for page in pages):
        raise ValueError("page IDs must be non-negative integers")
    memory: OrderedDict[int, int] = OrderedDict()
    frequency: Counter[int] = Counter()
    future: dict[int, deque[int]] = defaultdict(deque)
    if algorithm == "OPT":
        for position, page in enumerate(pages):
            future[page].append(position)
    faults = hits = 0
    accesses = []
    for position, page in enumerate(pages):
        if algorithm == "MFU":
            frequency[page] += 1
        if algorithm == "OPT":
            future[page].popleft()
        hit = page in memory
        evicted = None
        if hit:
            hits += 1
            if algorithm == "LRU":
                memory.move_to_end(page)
        else:
            faults += 1
            if len(memory) == num_frames:
                if algorithm in ("FIFO", "LRU"):
                    evicted = next(iter(memory))
                elif algorithm == "MFU":
                    evicted = max(memory, key=lambda p: (frequency[p], -memory[p]))
                else:
                    evicted = max(
                        memory,
                        key=lambda p: (
                            future[p][0] if future[p] else float("inf"),
                            -memory[p],
                        ),
                    )
                del memory[evicted]
            memory[page] = position
        if trace:
            accesses.append(Access(position, page, hit, evicted, tuple(sorted(memory))))
    return SimulationResult(algorithm, num_frames, faults, hits, tuple(accesses))


def generate_page_sequence(
    length: int = 200,
    page_range: int = 10,
    locality_factor: float = 0.6,
    seed: int = 42,
) -> list[int]:
    """Locality is the probability of a clamped step in {-1, 0, +1}."""
    positive_integer(length, "length")
    positive_integer(page_range, "page_range")
    if not 0 <= locality_factor <= 1:
        raise ValueError("locality_factor must be between 0 and 1")
    rng = Random(seed)
    current = rng.randrange(page_range)
    sequence = []
    for _ in range(length):
        if rng.random() < locality_factor:
            current = max(0, min(page_range - 1, current + rng.choice((-1, 0, 1))))
        else:
            current = rng.randrange(page_range)
        sequence.append(current)
    return sequence
