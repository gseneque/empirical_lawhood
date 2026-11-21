# SPDX-License-Identifier: MPL-2.0
"""Original parent custody, conditional material selection and native lifetimes."""

from dataclasses import replace
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.domain_composition.rubisco_response import observed_core
from empirical_lawhood.domains.rubisco.rubisco_response.observed_core_partition import (
    ObservedCorePartition,
)


ROLES = (
    "completion",
    "construction",
    "manifest",
    "material",
    "states",
    "thermal",
    "thermal-series",
    "topology",
)


def partition():
    return ObservedCorePartition(
        material="V1-WT",
        gas=None,
        source_digests=tuple((name, "0" * 64) for name in ROLES),
        atomic_numbers=(6,) * 8 + (1,) * 113 + (6,) * 7,
        masses_dalton=(12.0,) * 8 + (1.0,) * 113 + (12.0,) * 7,
        charges_electron=(0.0,) * 128,
        qm_atom_indices=tuple(range(121)),
        bonds=tuple((i, 121 + i) for i in range(7)),
        links=tuple((i, 121 + i, 1.09) for i in range(7)),
        lengths_angstrom=(50.0, 50.0, 50.0),
        qm_formal_charge=-2,
        spin_multiplicity=1,
    )


@pytest.mark.parametrize(
    "change",
    [
        {"source_digests": (("material", "0" * 64),)},
        {"qm_atom_indices": tuple(range(1, 122))},
        {"gas": "CO2"},
        {"lengths_angstrom": [50.0, 50.0, 50.0]},
        {"qm_formal_charge": -2.0},
        {"spin_multiplicity": 2},
        {"bonds": ((0, 121),) * 7},
        {"links": tuple((i, 121 + i, 1.10) for i in range(7))},
        {"charges_electron": (float("nan"),) * 128},
        {"masses_dalton": (True,) * 128},
    ],
)
def test_partition_rejects_substituted_population_cut_charge_or_parent(change):
    with pytest.raises(ValueError):
        replace(partition(), **change)


def _write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else json.dumps(value).encode()
    path.write_bytes(data)
    return sha256(data).hexdigest()


def source(root):
    original = {
        "prepared-02/states.json": b"states",
        "water-inputs-01/V1-WT/model.prmtop": b"topology",
        "water-inputs-01/V1-WT/final.npz": b"construction",
    }
    thermal = "water-results-01/V1-WT-wet/11031/"
    original.update(
        {
            thermal + "final.npz": b"original thermal",
            thermal + "series.jsonl": b"original series",
        }
    )
    files = {name: _write(root, name, body) for name, body in original.items()}
    material = dict(
        topology_sha256=files["water-inputs-01/V1-WT/model.prmtop"],
        final_sha256=files["water-inputs-01/V1-WT/final.npz"],
    )
    files["water-inputs-01/V1-WT.json"] = _write(
        root, "water-inputs-01/V1-WT.json", material
    )
    completed = {
        "final_sha256": files[thermal + "final.npz"],
        "series_sha256": files[thermal + "series.jsonl"],
    }
    files[thermal + "completed.json"] = _write(
        root, thermal + "completed.json", completed
    )
    seal = "".join(
        f"{digest}  {name}\n" for name, digest in sorted(files.items())
    ).encode()
    return observed_core.ObservedCoreSources(
        root, _write(root, "SHA256SUMS", seal), "V1-WT"
    )


@pytest.mark.parametrize("interrupt", [False, True])
def test_parent_mutation_is_refused_through_consumption_and_errors(
    tmp_path, monkeypatch, interrupt
):
    from empirical_lawhood.adapters.rubisco.rubisco_response import val1_reactive

    selection = source(tmp_path)
    monkeypatch.setattr(
        val1_reactive, "bind_material", lambda *args: "original material"
    )
    with pytest.raises(ValueError, match="original topology member changed"):
        with observed_core._material(selection, multiplicity=1) as material:
            assert material == "original material"
            (tmp_path / "water-inputs-01/V1-WT/model.prmtop").write_bytes(
                b"mutated topology"
            )
            if interrupt:
                raise RuntimeError("interrupted native comparison")


def test_missing_crossed_parent_or_unbound_gas_refused(tmp_path):
    selection = source(tmp_path)
    with pytest.raises(ValueError, match="missing an original native parent"):
        with observed_core._material(
            replace(selection, material="V1-I95M"), multiplicity=1
        ):
            pytest.fail("entered different material")
    with pytest.raises(ValueError, match="gas parameter stock"):
        replace(selection, gas="O2")


def test_closed_operator_releases_context_and_cached_density():
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import (
        ObservedCorePeriodicOperator,
    )

    op = SimpleNamespace(
        context=object(), integrator=object(), _converged_density_guess=object()
    )
    ObservedCorePeriodicOperator.close(op)
    assert (op.context, op.integrator, op._converged_density_guess) == (
        None,
        None,
        None,
    )
