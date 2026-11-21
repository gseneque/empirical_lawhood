# SPDX-License-Identifier: MPL-2.0
"""Prepare or evaluate one original Val1 periodic core from the caller's authenticated return."""

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.gas_amber_stock import PINS
from empirical_lawhood.science.records.serialization import validate_sha256
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.checksum_manifest import checksum_manifest
from empirical_lawhood.storage.file_census import FileHashCensus
from empirical_lawhood.storage.native_installation import real_path


@dataclass(frozen=True)
class ObservedCoreSources:
    """The caller selects an original return root and independently retained checksum manifest identity."""

    root: Path
    manifest_sha256: str
    material: str
    gas: str | None = None
    gas_stock: Path | None = None

    def __post_init__(self):
        validate_sha256(self.manifest_sha256)
        if self.material not in ("V1-WT", "V1-I95M") or self.gas not in (
            None,
            "O2",
            "CO2",
        ):
            raise ValueError("unknown observed Val1 material or gas")
        if (self.gas is None) != (self.gas_stock is None):
            raise ValueError(
                "select original gas parameter stock exactly when a gas is present"
            )


def _bindings(selection):
    root = real_path(selection.root)
    manifest = root / "SHA256SUMS"
    raw = read_bounded_bytes(manifest, maximum_bytes=16 * 1024**2)
    roster = checksum_manifest(raw, selection.manifest_sha256)
    case = selection.material
    # Both materials used the first seed and the WT-origin water placement in the original matched protocol.
    group = "water-results-01" if case == "V1-WT" else "water-crossed-results-01"
    thermal = f"{group}/{case}-wet/11031"
    original = {
        "states": "prepared-02/states.json",
        "material": f"water-inputs-01/{case}.json",
        "topology": f"water-inputs-01/{case}/model.prmtop",
        "construction": f"water-inputs-01/{case}/final.npz",
        "thermal": thermal + "/final.npz",
        "completion": thermal + "/completed.json",
        "thermal-series": thermal + "/series.jsonl",
    }
    if not set(original.values()) <= roster.keys():
        raise ValueError("observed core is missing an original native parent")
    paths = {key: real_path(root / name) for key, name in original.items()}
    identities = {key: roster[name] for key, name in original.items()}
    paths["manifest"], identities["manifest"] = manifest, selection.manifest_sha256
    if selection.gas is not None:
        for suffix, digest in zip(
            ("prepi", "frcmod"), PINS[selection.gas], strict=True
        ):
            paths["gas-" + suffix] = real_path(
                selection.gas_stock / (selection.gas.lower() + "." + suffix)
            )
            identities["gas-" + suffix] = digest
    return paths, identities


def _verify(paths, identities):
    with FileHashCensus() as census:
        for role, path in paths.items():
            if (
                census.sha256(real_path(path), maximum_bytes=None)[1]
                != identities[role]
            ):
                raise ValueError(f"observed core original {role} member changed")


@contextmanager
def _material(selection, *, multiplicity):
    from empirical_lawhood.adapters.rubisco.rubisco_response.val1_reactive import (
        bind_material,
    )

    paths, identities = _bindings(selection)
    _verify(paths, identities)
    try:
        material = json.loads(
            read_bounded_bytes(paths["material"], maximum_bytes=32 * 1024**2)
        )
        completion = json.loads(
            read_bounded_bytes(paths["completion"], maximum_bytes=1024**2)
        )
        if (material["topology_sha256"], material["final_sha256"]) != (
            identities["topology"],
            identities["construction"],
        ) or (completion["final_sha256"], completion["series_sha256"]) != (
            identities["thermal"],
            identities["thermal-series"],
        ):
            raise ValueError(
                "observed core selection substitutes a material topology, coordinate parent or trajectory"
            )
        yield bind_material(
            paths,
            identities,
            selection.material,
            selection.gas,
            multiplicity,
            material,
            completion,
        )
    finally:
        _verify(paths, identities)


def inspect_observed_core(selection: ObservedCoreSources, *, engine, multiplicity=1):
    """Reconstruct the physical selection, coordinates, cell and seven boundary links without an SCF call."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import (
        authenticate_numeric_engine,
    )

    authenticate_numeric_engine(engine)
    try:
        import numpy as np

        with _material(selection, multiplicity=multiplicity) as (
            partition,
            material,
            _,
        ):
            return dict(
                material=partition.material,
                gas=partition.gas,
                source_digests=dict(partition.source_digests),
                atom_count=len(partition.atomic_numbers),
                qm_atom_indices=partition.qm_atom_indices,
                links=partition.links,
                lengths_angstrom=partition.lengths_angstrom,
                qm_formal_charge=partition.qm_formal_charge,
                spin_multiplicity=partition.spin_multiplicity,
                observed_host_coordinates_sha256=sha256(
                    np.asarray(material["xyz"], dtype="<f8").tobytes()
                ).hexdigest(),
                engine_sha256=engine.fingerprint(),
                independent_assemblies=1,
                native_electronic_calls=0,
            )
    finally:
        authenticate_numeric_engine(engine, loaded=True)


def read_observed_tagged_path(selection: ObservedCoreSources, *, frames, engine, dynamics, side,
                              measure, reservoir_source_sha256, residence_steps=4):
    """Read original tagged frames using the atom and bath selections of the authenticated Val1 return."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
    from empirical_lawhood.domains.rubisco.rubisco_response.tagged_path_observations import TaggedPathSites, read_tagged_path_endpoint

    if type(selection) is not ObservedCoreSources or selection.gas not in ("CO2", "O2"):
        raise ValueError("select an observed Val1 parent and its tagged gas")
    authenticate_numeric_engine(engine)
    try:
        with _material(selection, multiplicity=3 if selection.gas == "O2" else 1) as (partition, material, gas):
            elements = tuple(atom.element.symbol for atom in material["atoms"])
            labels = material["labels"]
            sites = TaggedPathSites(elements=elements + tuple(row[0] for row in gas),
                box_angstrom=partition.lengths_angstrom, magnesium=int(labels["magnesium.MG"]),
                phosphorus=(int(labels["ligand.P1"]), int(labels["ligand.P2"])),
                backbone=(int(labels["ligand.C2"]), int(labels["ligand.C3"])),
                gas_atoms=tuple(range(len(elements), len(partition.atomic_numbers))),
                solute_heavy=tuple(map(int, material["solute"])), water_oxygens=tuple(map(int, material["water_o"])),
                coordinating_water=int(material["water"][0]))
            result = read_tagged_path_endpoint(sites=sites, frames=frames, dynamics=dynamics, side=side,
                measure=measure, reservoir_source_sha256=reservoir_source_sha256, residence_steps=residence_steps)
            return dict(result, material=partition.material, gas=partition.gas, engine_sha256=engine.fingerprint(),
                        original_source_digests=dict(partition.source_digests), native_electronic_calls=0)
    finally:
        authenticate_numeric_engine(engine, loaded=True)


def evaluate_observed_core(
    selection: ObservedCoreSources,
    *,
    engine,
    multiplicity,
    settings,
    observe,
    gas_coordinates_angstrom=None,
):
    """Evaluate the selected conditional geometry with the common periodic numerical operator."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import (
        authenticate_periodic_engine,
        periodic_operator_options,
    )
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import (
        validate_periodic_force_settings,
    )

    validate_periodic_force_settings(settings)
    authenticate_periodic_engine(engine)
    try:
        import numpy as np
        from empirical_lawhood.adapters.rubisco.rubisco_response.val1_reactive import (
            make_operator,
        )

        with _material(selection, multiplicity=multiplicity) as (
            partition,
            material,
            extra,
        ):
            xyz = material["xyz"]
            if extra:
                gas = np.asarray(gas_coordinates_angstrom, dtype=float)
                if gas.shape != (len(extra), 3) or not np.isfinite(gas).all():
                    raise ValueError(
                        "selected gas requires all its physical coordinates in angstrom"
                    )
                xyz = np.vstack((xyz, gas))
            elif gas_coordinates_angstrom is not None:
                raise ValueError(
                    "gas-free observation received coordinates for an unselected gas"
                )
            operator = make_operator(
                partition,
                material,
                extra,
                settings=settings,
                observe=observe,
                **periodic_operator_options(engine),
            )
            try:
                return dict(
                    operator.evaluate(xyz),
                    engine_sha256=engine.fingerprint(),
                    original_source_digests=dict(partition.source_digests),
                )
            finally:
                operator.close()
    finally:
        authenticate_periodic_engine(engine, loaded=True)
