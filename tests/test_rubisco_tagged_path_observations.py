# SPDX-License-Identifier: MPL-2.0
"""Clock, original atom roles, reservoir identity and first-passage controls."""

from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import tagged_path_observations as paths
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.val1_flux import VAL1_MEASURE, paired_path_transmission


DYNAMICS = ReferenceDynamicsSettings("software.tagged-path", Decimal("5e-16"), 6)
RESERVOIR = "c" * 64


def geometry(gas="O2", x=20.0):
    atoms = ("Mg", "P", "P", "C", "C", "O", "O")
    positions = [(0, 0, 0), (2, 2, 0), (6, 2, 0), (2, 0, 0), (3.4, 0, 0), (0, 2.1, 0), (0, 4.5, 0)]
    tag = ("O", "O") if gas == "O2" else ("C", "O", "O")
    sites = paths.TaggedPathSites(atoms + tag, (120.0,) * 3, 0, (1, 2), (3, 4),
        tuple(range(len(atoms), len(atoms) + len(tag))), (0, 1, 2, 3, 4), (5, 6), 5)
    positions.extend([(x, 0, 0), (x + 1.2, 0, 0), (x - 1.2, 0, 0)][:len(tag)])
    return sites, np.array(positions, dtype="<f8")


def original_frame(sites, xyz, *, step=0, surface=None, charge=0.0, spin=None):
    oxygen = len(sites.gas_atoms) == 2
    reservoir = "T" if oxygen else "S"
    character = paths.TaggedReservoirCharacter(RESERVOIR, sha256(xyz.tobytes(order="C")).hexdigest(),
        sites.gas_atoms, reservoir, charge, (2.0 if oxygen else 0.0) if spin is None else spin)
    return paths.TaggedPathFrame(step, xyz, surface or reservoir, character)


def endpoint(sites, frames, *, side="forward", residence_steps=4):
    return paths.read_tagged_path_endpoint(sites=sites, frames=frames, dynamics=DYNAMICS, side=side,
        measure=VAL1_MEASURE, reservoir_source_sha256=RESERVOIR, residence_steps=residence_steps)


@pytest.mark.parametrize("gas", ["O2", "CO2"])
def test_periodic_geometry_and_first_bulk_endpoint(gas):
    sites, xyz = geometry(gas)
    xyz[list(sites.gas_atoms[1:]), 0] += 120
    frame = original_frame(sites, xyz, charge=0.35)

    def observed():
        yield frame
        pytest.fail("consumed frames beyond the first physical endpoint")

    result = endpoint(sites, observed(), side="back")
    assert (result["outcome"], result["frames_read"], result["last_step"]) == ("BULK", 1, 0)
    row = result["last_geometry"]
    assert row["gas_intact"] and row["nearest_water_oxygen"] == sites.coordinating_water
    assert row["solute_distance_angstrom"] == pytest.approx(np.hypot(14.0, 2.0))
    assert row["tag_c2_angstrom"] == 18.0 and row["product"] is None
    assert row["coordinate_sha256"] == frame.reservoir.coordinate_sha256
    assert Decimal(result["physical_time_seconds"]) == 0
    assert endpoint(sites, [replace(frame, reservoir=None)])["outcome"] == "DISSOCIATED_ELECTRONIC_STATE_UNRESOLVED"
    assert endpoint(sites, [original_frame(sites, xyz, charge=0.350001)])["outcome"] == "DISSOCIATED_ELECTRONIC_STATE_UNRESOLVED"


def test_recross_horizon_and_truncated_prefix_keep_original_elapsed_time():
    sites, xyz = geometry(x=6.0)
    frame = original_frame(sites, xyz)
    recross = original_frame(sites, geometry(x=5.99)[1], step=2)
    at_radius = replace(frame, step=1)
    result = endpoint(sites, [frame, at_radius, recross], side="back")
    assert (result["outcome"], result["last_step"], Decimal(result["physical_time_seconds"])) == ("RECROSS", 2, Decimal("1e-15"))
    assert paired_path_transmission(result, {"outcome": "HORIZON"}) == "ZERO"
    horizon = endpoint(sites, (replace(frame, step=i) for i in range(7)))
    assert horizon["outcome"] == "HORIZON" and horizon["frames_read"] == 7
    assert endpoint(sites, [frame, at_radius])["outcome"] == "UNRESOLVED"
    assert endpoint(sites, [])["physical_time_seconds"] is None
    with pytest.raises(ValueError, match="physical clock"):
        endpoint(sites, [frame, recross])


def test_original_water_order_and_replacement_precede_bulk():
    sites, xyz = geometry()
    xyz[6] = xyz[5]
    assert endpoint(sites, [original_frame(sites, xyz)])["outcome"] == "BULK"
    xyz[6, 1] = 2.0
    result = endpoint(sites, [original_frame(sites, xyz)])
    assert result["outcome"] == "WATER_PARTITION_UNRESOLVED"
    assert result["last_geometry"]["nearest_water_oxygen"] == 6
    xyz[5, 1], xyz[6, 1] = 4.0, 2.6
    assert endpoint(sites, [original_frame(sites, xyz)])["outcome"] == "BULK"


def test_native_product_labels_require_consecutive_elapsed_intervals(monkeypatch):
    sites, xyz = geometry(x=6.0)
    frame = original_frame(sites, xyz, surface="S")
    labels = iter(["2PG+3PG", None, *(["2PG+3PG"] * 5)])
    monkeypatch.setattr(paths, "bound_products", lambda *_a, **_k: next(labels))
    result = endpoint(sites, (replace(frame, step=i) for i in range(7)))
    assert (result["outcome"], result["last_step"], result["consecutive_product_frames"]) == ("PRODUCT", 6, 5)
    assert paired_path_transmission({"outcome": "BULK"}, result) == "PRODUCT"


@pytest.mark.parametrize("change", ["source", "coordinates", "atom-order", "surface"])
def test_reservoir_measurements_bind_all_original_operands(change):
    sites, xyz = geometry()
    frame = original_frame(sites, xyz)
    fields = {"source": {"source_sha256": "b" * 64}, "coordinates": {"coordinate_sha256": "a" * 64},
              "atom-order": {"gas_atoms": sites.gas_atoms[::-1]}, "surface": {"surface": "S"}}
    with pytest.raises(ValueError, match="geometry, gas and electronic source"):
        endpoint(sites, [replace(frame, reservoir=replace(frame.reservoir, **fields[change]))])


def test_native_surface_integrity_and_original_roles():
    sites, xyz = geometry(x=20.0)
    frame = original_frame(sites, xyz, surface="S")
    assert not paths.observe_tagged_geometry(sites, frame, VAL1_MEASURE)["gas_intact"]
    xyz[8, 0] = xyz[7, 0] + 1.0
    assert not paths.observe_tagged_geometry(sites, original_frame(sites, xyz), VAL1_MEASURE)["gas_intact"]
    with pytest.raises(ValueError, match="water assignments"):
        replace(sites, coordinating_water=sites.gas_atoms[0])
    with pytest.raises(ValueError, match="finite measured"):
        replace(frame.reservoir, spin_e=float("nan"))
    sites, xyz = geometry("CO2")
    with pytest.raises(ValueError, match="selected gas surface"):
        endpoint(sites, [original_frame(sites, xyz, surface="T")])
    xyz[0, 0] = np.nan
    with pytest.raises(ValueError, match="complete finite native geometry"):
        endpoint(sites, [original_frame(sites, xyz)])


@pytest.mark.parametrize("interrupt", [False, True])
def test_public_reader_consumes_original_roles_and_rechecks_engine_on_exit(monkeypatch, tmp_path, interrupt):
    from empirical_lawhood.adapters.rubisco.rubisco_response import construction_engine
    from empirical_lawhood.api.domain_composition.rubisco_response import observed_core

    sites, xyz = geometry()
    selection = observed_core.ObservedCoreSources(tmp_path, "d" * 64, "V1-WT", "O2", tmp_path)
    engine = SimpleNamespace(fingerprint=lambda: "e" * 64)
    events = []

    @contextmanager
    def material(original, *, multiplicity):
        assert original is selection and multiplicity == 3
        events.append("enter-material")
        labels = dict(zip(("magnesium.MG", "ligand.P1", "ligand.P2", "ligand.C2", "ligand.C3"), range(5), strict=True))
        native = dict(atoms=[SimpleNamespace(element=SimpleNamespace(symbol=e)) for e in sites.elements[:7]],
            labels=labels, solute=sites.solute_heavy, water_o=sites.water_oxygens, water=(5,))
        partition = SimpleNamespace(lengths_angstrom=sites.box_angstrom, atomic_numbers=(12, 15, 15, 6, 6, 8, 8, 8, 8),
            material=selection.material, gas=selection.gas, source_digests=(("thermal", "a" * 64),))
        try:
            yield partition, native, [("O",), ("O",)]
        finally:
            events.append("exit-material")

    def frames():
        assert events == ["select-engine", "enter-material"]
        if interrupt:
            raise RuntimeError("capture ended")
        yield original_frame(sites, xyz)

    def authenticate(selected, *, loaded=False):
        assert selected is engine
        events.append("close-engine" if loaded else "select-engine")

    monkeypatch.setattr(observed_core, "_material", material)
    monkeypatch.setattr(construction_engine, "authenticate_numeric_engine", authenticate)
    options = dict(frames=frames(), engine=engine, dynamics=DYNAMICS, side="back", measure=VAL1_MEASURE,
        reservoir_source_sha256=RESERVOIR)
    if interrupt:
        with pytest.raises(RuntimeError, match="capture ended"):
            observed_core.read_observed_tagged_path(selection, **options)
    else:
        result = observed_core.read_observed_tagged_path(selection, **options)
        assert result["outcome"] == "BULK" and result["original_source_digests"] == {"thermal": "a" * 64}
        assert result["native_electronic_calls"] == 0 and result["engine_sha256"] == engine.fingerprint()
    assert events == ["select-engine", "enter-material", "exit-material", "close-engine"]
