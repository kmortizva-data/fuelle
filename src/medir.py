"""Timing something once is not measuring it. The one way this project measures.

Module 3 taught this the expensive way: the first version of `donde_viven.py`
timed each query once, and two consecutive runs of the same code reported 203.7x
and 143.8x between the extremes. The conclusion held, but the number about to be
published was not reproducible.

At millisecond scale what dominates is whatever the machine is doing on its own:
the antivirus, the indexer, another process asking for disk. A single clock
reading measures that as much as it measures the code.

Two functions, and the second is the one that really matters:

  `measure()` returns the median of seven runs with its minimum and maximum.
  Median because one isolated spike must not move the result, and the range
  because hiding it would fake a precision that is not there.

  `distinguishable()` answers whether two measurements can be compared at all.
  If their ranges overlap there is no difference to report, however far apart
  the medians land. That is what separates a finding from an anecdote, and it
  gets applied before claiming any speedup factor.

Import it from any script under src/:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from medir import measure, distinguishable
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

RUNS = 7


@dataclass
class Measurement:
    """What comes out of timing something seven times."""

    median: float
    minimum: float
    maximum: float
    runs: int
    result: object = None

    def as_json(self, places: int = 3) -> dict:
        """For writing into results/. The range always travels with the median."""
        return {
            "mediana_s": round(self.median, places),
            "min_s": round(self.minimum, places),
            "max_s": round(self.maximum, places),
            "corridas": self.runs,
        }

    def __str__(self) -> str:
        return f"{self.median:.3f} s (from {self.minimum:.3f} to {self.maximum:.3f})"


def measure(action: Callable[[], object], runs: int = RUNS,
            setup: Callable[[], object] | None = None) -> Measurement:
    """Run `action` several times and return the median with its range.

    `action` takes no arguments and may return anything: the last run's return
    value is kept, which is what lets a caller check that every layout being
    compared answers the same thing.

    `setup` runs before each repetition and is NOT timed. It exists for the one
    case that would otherwise be unmeasurable: timing a write means deleting
    what the previous run wrote, and charging that deletion to the write would
    measure the filesystem cleaning up rather than the code doing the work.
    """
    times = []
    result = None
    for _ in range(runs):
        if setup is not None:
            setup()
        started = time.perf_counter()
        result = action()
        times.append(time.perf_counter() - started)
    times.sort()
    return Measurement(
        median=times[len(times) // 2],
        minimum=times[0],
        maximum=times[-1],
        runs=runs,
        result=result,
    )


def distinguishable(a: Measurement, b: Measurement) -> bool:
    """If the ranges overlap, there is no difference to report.

    Two different medians are not enough. If the fast one's maximum lands above
    the slow one's minimum, both could be the same thing measured at two
    different moments of the machine, and the speedup factor would be noise with
    decimals.
    """
    fast, slow = (a, b) if a.median <= b.median else (b, a)
    return fast.maximum < slow.minimum


def times_slower(slow: Measurement, fast: Measurement) -> float | None:
    """How many times slower, or None when the ranges forbid the claim."""
    if not distinguishable(slow, fast):
        return None
    return slow.median / fast.median
