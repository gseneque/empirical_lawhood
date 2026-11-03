# SPDX-License-Identifier: MPL-2.0
"""Pure complete-window integrity and conditional reweighting; no native entry."""

from dataclasses import dataclass
from decimal import Decimal
import math
import re

from . import contracts as c


def supplementary_xyz_blocks(text):
    """Retain all original SI coordinate tokens without assigning residue names.

    This finite parser accepts the oxygenase supplementary coordinate section,
    including its page footers. Ordinal source atoms are not authenticated
    residue/assembly correspondence. No energies or chemical states are chosen.
    """
    marker = "Optimized coordinates"
    if text.count(marker) != 1:
        raise ValueError("supplementary optimized coordinate section is not exact")
    lines = text.split(marker, 1)[1].splitlines()
    blocks = []
    index = 0
    heading = ""
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line or re.fullmatch(r"S\d+", line):
            continue
        if not line.isdigit():
            if len(line.split()) == 4 and line.split()[0] in c.ATOMIC_NUMBERS:
                raise ValueError("supplementary atom exceeds declared full denominator")
            heading = line
            continue
        count = int(line)
        if count <= 0 or index >= len(lines):
            raise ValueError("supplementary full atom denominator missing")
        title = lines[index].strip()
        index += 1
        if not title:
            raise ValueError("supplementary geometry title missing")
        atoms = []
        while len(atoms) < count and index < len(lines):
            row = lines[index].strip()
            index += 1
            if not row or re.fullmatch(r"S\d+", row):
                continue
            fields = row.split()
            if len(fields) != 4 or fields[0] not in c.ATOMIC_NUMBERS:
                raise ValueError("supplementary coordinate atom census malformed")
            try:
                xyz = tuple(Decimal(x) for x in fields[1:])
            except Exception as exc:
                raise ValueError("supplementary coordinate token malformed") from exc
            if any(not x.is_finite() for x in xyz):
                raise ValueError("supplementary coordinate is nonfinite")
            atoms.append(tuple(fields))
        if len(atoms) != count:
            raise ValueError("supplementary full atom denominator truncated")
        blocks.append((heading, title, tuple(atoms)))
    if not blocks:
        raise ValueError("supplementary coordinate census empty")
    return tuple(blocks)


@dataclass(frozen=True, slots=True)
class ReweightingResult:
    converged: bool
    iterations: int
    free_energies_reduced: tuple[float, ...]
    normalized_weights: tuple[tuple[float, ...], ...]
    effective_samples: tuple[float, ...]
    overlap: tuple[tuple[float, ...], ...]


def _logsumexp(values):
    largest = max(values)
    return largest + math.log(math.fsum(math.exp(x - largest) for x in values))


def reweighting(reduced_potentials, counts, *, tolerance, maximum_iterations):
    """MBAR self-consistency with explicit numerical settings and full census.

    Rows are selected windows, columns ALL retained production samples. Counts
    bind sample origins and remain essential in the denominator. This function
    does not certify decorrelation, reaction-coordinate adequacy or a barrier.
    """
    if not counts or any(type(n) is not int or n <= 0 for n in counts):
        raise ValueError("reweighting cannot omit failed/empty selected windows")
    if len(reduced_potentials) != len(counts) or any(
        len(row) != sum(counts) for row in reduced_potentials
    ):
        raise ValueError("reweighting changes complete window/sample denominator")
    if any(not math.isfinite(x) for row in reduced_potentials for x in row):
        raise ValueError("reweighting has unknown/nonfinite actual potential")
    c.positive(tolerance, "MBAR tolerance")
    if type(maximum_iterations) is not int or maximum_iterations <= 0:
        raise ValueError("numerical iteration declaration must be explicit")
    rows = tuple(tuple(float(x) for x in row) for row in reduced_potentials)
    totals = tuple(math.log(n) for n in counts)
    f = [0.0] * len(counts)
    converged = False
    for iteration in range(1, maximum_iterations + 1):
        denominator = [
            _logsumexp(tuple(totals[k] + f[k] - rows[k][n] for k in range(len(counts))))
            for n in range(sum(counts))
        ]
        nextf = [
            -_logsumexp(tuple(-row[n] - denominator[n] for n in range(sum(counts))))
            for row in rows
        ]
        reference = nextf[0]
        nextf = [x - reference for x in nextf]
        converged = max(abs(x - y) for x, y in zip(nextf, f, strict=True)) <= float(
            tolerance
        )
        f = nextf
        if converged:
            break
    denominator = [
        _logsumexp(tuple(totals[k] + f[k] - rows[k][n] for k in range(len(counts))))
        for n in range(sum(counts))
    ]
    weights = []
    for k in range(len(counts)):
        column = [
            math.exp(f[k] - rows[k][n] - denominator[n]) for n in range(sum(counts))
        ]
        scale = math.fsum(column)
        weights.append(tuple(x / scale for x in column))
    ess = tuple(1 / math.fsum(x * x for x in column) for column in weights)
    # MBAR overlap O_ij=N_j sum_n W_ni W_nj. It is NOT biological replication.
    overlap = tuple(
        tuple(
            counts[j]
            * math.fsum(a * b for a, b in zip(weights[i], weights[j], strict=True))
            for j in range(len(counts))
        )
        for i in range(len(counts))
    )
    return ReweightingResult(
        converged, iteration, tuple(f), tuple(weights), ess, overlap
    )


def complete_window_census(selection, traces):
    from .current_admission import validate_complete_window_census

    return validate_complete_window_census(selection, traces)


def retained_expense(traces):
    """Supplied per-window expense sums; unknown stays unknown.

    Inclusive/nested calls are not separately added here. A sum of parallel wall
    windows is not campaign elapsed time, and unique actual calls require a ledger.
    """
    values = {}
    for field in ("cpu_seconds", "wall_seconds"):
        costs = tuple(getattr(row, field) for row in traces)
        values[field] = (
            None if any(x is None for x in costs) else sum(costs, Decimal(0))
        )
    return values


def preliminary_sampling_disposition(selection, traces):
    """Producer-reported window integrity; no independent sampling/PMF grant."""
    from .current_admission import reduce_reported_dispositions

    ordered = complete_window_census(selection, traces)
    return reduce_reported_dispositions(tuple(trace.disposition for trace in ordered))
