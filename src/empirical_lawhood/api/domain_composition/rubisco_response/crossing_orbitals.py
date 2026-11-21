# SPDX-License-Identifier: MPL-2.0
"""Reconstruct original oxygen-path occupied spaces through the funded return's manifest."""

from dataclasses import dataclass
import json
import math
from pathlib import Path

from empirical_lawhood.science.records.serialization import validate_sha256
from empirical_lawhood.storage.checksum_manifest import selected_checksum_members


@dataclass(frozen=True)
class CrossingOrbitalSources:
    root: Path
    manifest_sha256: str

    def __post_init__(self):
        validate_sha256(self.manifest_sha256)


def read_crossing_orbitals(selection: CrossingOrbitalSources):
    """Compare all four original material/hydration paths and every saved converged spin sector."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.crossing_orbitals import (
        compare_crossing_path,
        require_orbital_runtime,
    )

    with selected_checksum_members(selection.root, selection.manifest_sha256) as (
        roster,
        original,
        consumed,
    ):

        def document(name):
            return json.loads(original(name))

        historical = document("orbital-readback-01/finished.json")
        runtime = require_orbital_runtime(historical["threads"])
        closure = document("crossing-results-01/finished.json")
        cases = {
            f"{material}-{water}"
            for material in ("V1-WT", "V1-I95M")
            for water in ("dry", "wet")
        }
        binding = {
            case: roster.get(f"orbital-readback-01/{case}.json") for case in cases
        }
        if (
            closure["completed"] != len(cases)
            or closure["failed"] != 0
            or None in binding.values()
            or historical["returned_sha256"] != binding
        ):
            raise ValueError(
                "the original four assigned crossing paths have an incomplete return"
            )
        cards = json.loads(
            original("prepared-02/states.json", claimed=historical["input_sha256"])
        )["states"]
        by_name = {card["name"]: card for card in cards}
        if len(by_name) != len(cards):
            raise ValueError("the original state table duplicates a material selection")
        paths = {}
        for case in sorted(cases):
            card = by_name[case + "-O-I"]
            prefix = f"crossing-results-01/{case}"
            end = document(prefix + "/completed.json")
            if (
                case != f"{card['case']}-{card['hydration']}"
                or end["case"] != card["case"]
                or end["water"] != card["hydration"]
            ):
                raise ValueError(
                    "original crossing closure names a different material or hydration"
                )
            count = end["evaluated_geometries"]
            if type(count) is not int or not 0 < count <= len(roster):
                raise ValueError(
                    "the native closure needs a positive original point count"
                )
            expected = {
                f"{prefix}/point-{i}/{name}"
                for i in range(count)
                for name in ("point.json", "native.npz")
            }
            observed = {
                key
                for key in roster
                if key.startswith(prefix + "/point-")
                and key.rsplit("/", 1)[-1] in ("point.json", "native.npz")
            }
            if observed != expected:
                raise ValueError(
                    "original path changes the complete recorded point census"
                )
            items = []
            for i in range(count):
                base = f"{prefix}/point-{i}"
                report = document(base + "/point.json")
                f = report["fraction"]
                if (
                    type(f) not in (float, int)
                    or not math.isfinite(f)
                    or not 0 <= f <= 1
                ):
                    raise ValueError("the original point has an invalid path fraction")
                items.append((f, base, report))
            if len({f for f, _, _ in items}) != count:
                raise ValueError("the original path duplicates a sampled fraction")
            points = (
                (
                    row,
                    original(
                        base + "/native.npz",
                        claimed=validate_sha256(row["native_sha256"]),
                    ),
                )
                for _, base, row in sorted(items)
            )
            paths[case] = compare_crossing_path(card, points, end["bracket_fraction"])
        return dict(
            manifest_sha256=selection.manifest_sha256,
            consumed_members=dict(sorted(consumed.items())),
            runtime=runtime,
            original_readback_sha256=historical["returned_sha256"],
            paths=paths,
            scope="Occupied-space continuity of original converged determinants on four sampled paths. No new SCF, force, spin transition or kinetic measurement.",
        )
