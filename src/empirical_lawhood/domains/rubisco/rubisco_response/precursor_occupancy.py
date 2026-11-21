# SPDX-License-Identifier: MPL-2.0
"""Finite gas-free precursor occupancy conditional on the two prepared origins."""

from collections import Counter
from dataclasses import dataclass
import math

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_response.precursor_geometry import joint, summarize
from empirical_lawhood.methods.model_free.events import assess_first_passage


ORIGINS = ("coupled", "outer")
CUTOFF_A = 2.7
PASSAGE_FIELDS = ("first_entry_fs", "first_loss_after_entry_fs", "return_after_loss_fs", "sustained_entry_fs")
COUNT_FIELDS = ("occupied", "frames", "second_half_occupied", "second_half_frames", "geometry_frames",
                "unique_proton_assignment_frames", "precursor_frames", "water_intact_frames", "entry",
                "endpoint", "sustained_round_trips")


@dataclass(frozen=True, slots=True)
class PrecursorReleasePath:
    """One assigned seed and its measured prefix, including the entry configuration."""

    seed: int
    assigned_frames: int
    interval_fs: float
    status: str
    frames: tuple
    joint_summary: dict | None

    @classmethod
    def from_release(cls, row):
        frames = tuple(row["frames"])
        summary = row.get("cutoffs_A", {}).get(str(CUTOFF_A))
        if summary is None and frames:
            summary = summarize(frames, CUTOFF_A)
        return cls(row["seed"], row["assigned_post_entry_frames"], row["frame_interval_fs"],
                   row["status"], frames, summary)

    def __post_init__(self):
        if (type(self.seed) is not int or type(self.assigned_frames) is not int or self.assigned_frames <= 0
                or not math.isfinite(self.interval_fs) or self.interval_fs <= 0
                or self.status not in ("complete", "truncated", "native failure")):
            raise ValueError("invalid precursor release assignment or native status")
        if len(self.frames) > self.assigned_frames + 1 or (
                self.status == "complete" and len(self.frames) != self.assigned_frames + 1):
            raise ValueError("observed precursor frames differ from their assigned grid")
        for index, frame in enumerate(self.frames):
            if frame["time_fs"] != index * self.interval_fs:
                raise ValueError("precursor frames change their original sampling clock")
            if any(not math.isfinite(frame[k]) or frame[k] < 0 for k in ("maximum_contact_A", "nearest_water_A")):
                raise ValueError("precursor frames require finite nonnegative distances")
        if self.frames:
            if (self.joint_summary is None or self.joint_summary["frames"] != len(self.frames) - 1
                    or self.joint_summary["occupied"] != sum(joint(frame, CUTOFF_A) for frame in self.frames[1:])):
                raise ValueError("precursor occupancy differs from its measured post-entry frames")
        elif self.joint_summary is not None:
            raise ValueError("an empty native prefix cannot carry a measured precursor summary")


def _history(material, paths):
    summaries = [path.joint_summary for path in paths if path.frames]
    assigned = sum(path.assigned_frames for path in paths)
    observed = sum(row["frames"] for row in summaries)
    hits = sum(row["occupied"] for row in summaries)
    history = dict(assigned_frames=assigned, prefix_frames=observed, prefix_occupied=hits,
                   conditional_completion_bounds=[hits / assigned, (hits + assigned - observed) / assigned],
                   outcome_census=dict(Counter(path.status for path in paths)))
    if any(path.status != "complete" for path in paths):
        return dict(status="incomplete", **history)

    totals = {key: sum(row[key] for row in summaries) for key in COUNT_FIELDS}
    passages = [{key: row[key] for key in PASSAGE_FIELDS} for row in summaries]
    horizons = {path.assigned_frames * path.interval_fs for path in paths}
    first_change = None
    if len(horizons) == 1:
        horizon = horizons.pop()
        events = []
        for row in summaries:
            time = row["first_loss_after_entry_fs"] if row["entry"] else row["first_entry_fs"]
            events.append(dict(root_id=material, status="administrative_censor" if time is None else "event",
                               observed_until=horizon, event=None if time is None else "passage", event_time=time))
        first_change = assess_first_passage(events, horizon=horizon, target_event="passage", time_grid=[0, horizon])
    return dict(status="complete", **history, **totals, conditional_fraction=hits / observed,
                late_fraction=totals["second_half_occupied"] / totals["second_half_frames"],
                passages=passages, first_change_from_initial=first_change)


def _water_histogram(samples):
    # Match half-open 0.1 Å bins, including values exactly on a floating-point bin edge.
    counts = Counter()
    for value in samples:
        index = math.floor(value / 0.1)
        if value < index * 0.1:
            index -= 1
        elif value >= (index + 1) * 0.1:
            index += 1
        counts[index] += 1
    return {index: count / len(samples) for index, count in counts.items()}


def _range(values):
    return [min(values), max(values)]


def _exchange_statistics(origins):
    shell = np.zeros((2, 2), dtype=int)
    contacts = np.zeros((4, 4), dtype=int)
    samples = {}
    late_ranges, quarter_ranges = {}, {}
    for origin, paths in origins.items():
        distances, late = [], []
        quarters = {3: [], 4: []}
        for path in paths:
            frames = path.frames
            wet = [int(frame["nearest_water_A"] <= CUTOFF_A) for frame in frames]
            states = [2 * int(frame["maximum_contact_A"] <= CUTOFF_A)
                      + int(frame["precursor"] and frame["water_intact"]) for frame in frames]
            np.add.at(shell, (wet[:-1], wet[1:]), 1)
            np.add.at(contacts, (states[:-1], states[1:]), 1)
            distances.extend(frame["nearest_water_A"] for frame in frames[1:])
            summary = path.joint_summary
            late.append(summary["second_half_occupied"] / summary["second_half_frames"])
            horizon = frames[-1]["time_fs"]
            for quarter in quarters:
                block = [joint(frame, CUTOFF_A) for frame in frames
                         if (quarter - 1) * horizon / 4 < frame["time_fs"] <= quarter * horizon / 4]
                if block:
                    quarters[quarter].append(sum(block) / len(block))
        samples[origin] = distances
        late_ranges[origin] = _range(late)
        for quarter, fractions in quarters.items():
            if len(fractions) == len(paths):
                quarter_ranges[f"{origin}_quarter_{quarter}"] = _range(fractions)

    coupled, outer = (_water_histogram(samples[key]) for key in ORIGINS)
    overlap = sum(min(value, outer.get(index, 0.)) for index, value in sorted(coupled.items()))
    reciprocal = bool(shell[0, 1] and shell[1, 0])
    wet_fraction = None
    if reciprocal:
        into, out = shell[0, 1] / shell[0].sum(), shell[1, 0] / shell[1].sum()
        wet_fraction = float(into / (into + out))
    return dict(shell_order=["outside", "inside"], shell_pairs=shell.tolist(), reciprocal=reciprocal,
                empirical_wet_stationary_fraction_if_reciprocal=wet_fraction,
                state_order=["outside_other", "outside_precursor", "six_contacts_other", "six_contacts_precursor"],
                joint_pairs=contacts.tolist(), water_distance_overlap_0p1A_bins=overlap,
                water_distance_ranges_A={k: _range(v) for k, v in samples.items()},
                outer_min_minus_inner_max_water_A=min(samples["outer"]) - max(samples["coupled"]),
                late_joint_fraction_by_origin_range=late_ranges, late_quarter_joint_ranges=quarter_ranges)


def assess_precursor_origins(material, *, seeds, coupled, outer):
    """Compare selected finite paths from one material and its paired preparation origins."""
    if not isinstance(material, str) or not material or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("select one material and its complete distinct seed roster")
    origins = dict(coupled=coupled, outer=outer)
    for paths in origins.values():
        if (any(type(path) is not PrecursorReleasePath for path in paths)
                or tuple(path.seed for path in paths) != tuple(seeds)):
            raise ValueError("both precursor origins must match the full assigned seed roster")
    histories = {origin: _history(material, paths) for origin, paths in origins.items()}
    grids = {(path.assigned_frames, path.interval_fs) for paths in origins.values() for path in paths}
    comparable = len(grids) == 1 and all(row["status"] == "complete" for row in histories.values())
    mixture, counts, mixed, weight = [0., 1.], None, False, None
    if comparable:
        mixture = _range([row["conditional_fraction"] for row in histories.values()])
        counts = _exchange_statistics(origins)
        ranges = counts["late_quarter_joint_ranges"]
        overlap = len(ranges) == 4 and max(r[0] for r in ranges.values()) <= min(r[1] for r in ranges.values())
        mixed = (counts["reciprocal"] and counts["water_distance_overlap_0p1A_bins"] > 0 and overlap
                 and all(row["sustained_round_trips"] >= 3 for row in histories.values()))
        if mixed:
            weight = sum(row["second_half_occupied"] for row in histories.values()) / sum(
                row["second_half_frames"] for row in histories.values())
    return dict(histories=histories, observed_mixture_range=mixture, observed_transitions=counts,
                exchange_screen_evaluable=comparable, exchange_screen_passed=mixed,
                candidate_model_joint_weight_if_mixed=weight, biological_natural_weight_identified_set=[0., 1.],
                independent_assemblies=1)
