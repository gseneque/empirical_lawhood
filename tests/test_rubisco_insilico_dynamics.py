# SPDX-License-Identifier: MPL-2.0
"""Exposed parameter/sequence integrity checks, never native dynamics evidence."""

from decimal import Decimal
import re
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import preparation
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.parameter_audit import (
    assigned_parameter_inventory,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.contracts import (
    KCX_ALIASES,
)


def custom_stock():
    prepi = "    0    0    2\n\nExposed fixture\nfixture.res\nKCX INT 0\nCORRECT OMIT DU BEG\n0.0\n"
    prepi += "1 DUMM DU M 0 -1 -2 0.0 0.0 0.0 .00000\n"
    for index, (typ, _) in enumerate(KCX_ALIASES, 2):
        prepi += f"{index} A{index} {typ} M 1 0 -1 1.0 2.0 3.0 -0.{index:05d}\n"
    prepi += "\nIMPROPER\n-M CA N HN1\nDONE\nSTOP\n"
    frcmod = "Exposed fixture\nMASS\n"
    frcmod += "".join(f"{typ:<2} 12.010 source mass\n" for typ, _ in KCX_ALIASES)
    frcmod += "\nBOND\nC -N   427.60 1.379 original custom\n"
    frcmod += "\nANGLE\nCT-C -N  66.800 115.180\n"
    frcmod += "\nDIHE\nN -C -CT-N  1 1.700 180.000 -1.000\nN -C -CT-N  1 2.000 180.000 2.000\n"
    frcmod += "\nIMPROPER\nC -CT-N -H  1.1 180.0 2.0\nNONBON\n"
    frcmod += "".join(f"{typ:<2} 1.8240 0.1700 source LJ\n" for typ, _ in KCX_ALIASES)
    return prepi, frcmod


def baseline_stock():
    mass = "".join(f"{typ:<2} 12.010 source mass\n" for typ, _ in KCX_ALIASES)
    lj = "".join(f"{typ:<2} 1.8240 0.1700 source LJ\n" for typ, _ in KCX_ALIASES)
    parm = (
        "Exposed fixture\n" + mass + "\nC H N\n"
        "C -N   490.0 1.335 standard peptide\n\n"
        "C -N -CT  50.0 120.0\n\n"
        "C -N -CT-H  1 0.850 180.0 -2.0 first\n"
        "C -N -CT-H  1 0.800 0.0 1.0 second\n\n"
        "X -X -N -H  1.1 180.0 2.0\n\n"
        "\nN NA\n\nMOD4 RE\n" + lj + "\nEND\n"
    )
    ff = "Exposed empty overlay\nMASS\nBOND\nANGLE\nDIHE\nIMPROPER\nNONBON\n"
    return parm, ff


def test_scoped_custom_preserves_charges_and_numeric_terms_without_global_override():
    prepi, frcmod = custom_stock()
    result = preparation.scoped_kcx_stock(
        prepi, frcmod, existing_atom_types=("C", "N", "CT")
    )
    assert result.scoped_prepi_utf8.startswith("    0    0    2\n")
    assert "DUMM DU" in result.scoped_prepi_utf8
    assert "-M CA N HN1" in result.scoped_prepi_utf8  # Atom names, not atom types.
    assert len(result.atom_charge_tokens) == 8
    assert sum(Decimal(value) for _, value in result.atom_charge_tokens) == Decimal(
        "-.00044"
    )
    assert re.search(
        r"K2-K0\s+427\.60 1\.379 original custom", result.scoped_custom_frcmod_utf8
    )
    assert "C -N   427.60" not in result.scoped_custom_frcmod_utf8
    assert (
        "K0-K2-K1-K0 1 1.700 180.000 -1.000\nK0-K2-K1-K0 1 2.000 180.000 2.000"
        in result.scoped_custom_frcmod_utf8
    )
    with pytest.raises(ValueError, match="collides"):
        preparation.scoped_kcx_stock(prepi, frcmod, existing_atom_types=("K0",))
    with pytest.raises(ValueError, match="undeclared"):
        preparation.scoped_kcx_stock(
            prepi.replace("A2 C ", "A2 BAD "), frcmod, existing_atom_types=()
        )


def test_boundary_copy_keeps_standard_peptide_and_contiguous_complete_torsion():
    parm, ff = baseline_stock()
    result = preparation.scoped_boundary_stock(parm, ff)
    text = result.scoped_boundary_frcmod_utf8
    assert re.search(r"C -K0\s+490\.0 1\.335 standard peptide", text)
    assert re.search(r"K2-N \s+490\.0 1\.335 standard peptide", text)
    assert "C -N   490.0" not in text
    expected = (
        "C -N -CT-K6 1 0.850 180.0 -2.0 first\nC -N -CT-K6 1 0.800 0.0 1.0 second"
    )
    assert expected in text
    assert "X -X -K0-K6 1.1 180.0 2.0" in text
    with pytest.raises(ValueError, match="continuation"):
        preparation.scoped_boundary_stock(
            parm.replace("C -N -CT-H  1 0.800", "C -N -CT-C  1 0.800"), ff
        )


def sequences():
    return dict(
        gp_lsu="A" * 493,
        gp_ssu_m1="M" + "A" * 93 + "I" + "A" * 43,
        gp_ssu_v1="V" + "A" * 93 + "I" + "A" * 43,
        te_lsu="A" * 414 + "P" + "A" * 60,
        te_ssu="A" * 97 + "V" + "A" * 20,
    )


def test_exact_donor_background_and_full_gp_processing_views_are_controlled():
    originals = sequences()
    rows = preparation.controlled_constructs(**originals)
    preparation.validate_controlled_constructs(rows, originals)
    assert rows[-2].lsu_sequence == rows[-1].lsu_sequence
    assert rows[-2].lsu_sequence[414] == "A"
    assert len(rows[-2].ssu_sequence) == 118
    assert rows[-2].ssu_sequence[97] == "M" and rows[-1].ssu_sequence[97] == "V"
    assert rows[0].lsu_sequence == rows[2].lsu_sequence == originals["gp_lsu"]
    assert rows[0].ssu_sequence[:94] == rows[2].ssu_sequence[:94]
    assert rows[0].ssu_sequence[95:] == rows[2].ssu_sequence[95:]
    with pytest.raises(ValueError, match="incomplete"):
        preparation.controlled_constructs(**(originals | {"te_ssu": "V"}))
    with pytest.raises(ValueError, match="another residue"):
        preparation.controlled_constructs(
            **(originals | {"gp_ssu_v1": "V" + "C" + originals["gp_ssu_v1"][2:]})
        )


def test_actual_parameter_census_keeps_zeros_and_refuses_missing_or_nonfinite_terms():
    class Atom:
        def __init__(self, index):
            self.idx = index
            self.name = "C" if index == 0 else "N"
            self.residue = SimpleNamespace(idx=0, name="KCX", number=210, chain="A")
            self.type = "K2" if index == 0 else "K0"
            self.atomic_number = 6 if index == 0 else 7
            self.mass, self.rmin, self.epsilon, self.charge = 12.01, 1.908, 0.086, -0.5

    atoms = [Atom(0), Atom(1)]
    bond = SimpleNamespace(
        atom1=atoms[0], atom2=atoms[1], type=SimpleNamespace(k=0.0, req=1.379)
    )
    structure = SimpleNamespace(
        atoms=atoms,
        bonds=[bond],
        angles=[],
        dihedrals=[],
        parm_data={
            name: [0]
            for name in (
                "NONBONDED_PARM_INDEX",
                "LENNARD_JONES_ACOEF",
                "LENNARD_JONES_BCOEF",
                "NUMBER_EXCLUDED_ATOMS",
                "EXCLUDED_ATOMS_LIST",
            )
        },
    )
    result = assigned_parameter_inventory(structure)
    assert result["term_census"] == dict(atoms=2, bonds=1, angles=0, dihedrals=0)
    assert result["bonds"][0]["coefficients"] == dict(k="0.0", req="1.379")
    bond.type = None
    with pytest.raises(ValueError, match="unassigned molecular bonds"):
        assigned_parameter_inventory(structure)
    bond.type = SimpleNamespace(k=0.0, req=1.379)
    atoms[0].charge = float("nan")
    with pytest.raises(ValueError, match="nonfinite"):
        assigned_parameter_inventory(structure)


def mock_openmm():
    class Integrator:
        def __init__(self, *args):
            self.steps = 0
            self.seed = None

        def getStepSize(self):
            return "0.005 ps"

        def setRandomNumberSeed(self, seed):
            self.seed = seed

        def getRandomNumberSeed(self):
            return self.seed

        def step(self, count):
            self.steps += count
            if count < 0:
                raise RuntimeError("exposed native integration failure")

    class Context:
        def __init__(self, system, integrator, platform=None):
            self.positions = None
            self.parameters = {}
            self.state = "initial"

        def getPlatform(self):
            return SimpleNamespace(
                getName=lambda: "CPU",
                getPropertyNames=lambda: ("Threads",),
                getPropertyValue=lambda context, name: "1",
            )

        def setPositions(self, positions):
            self.positions = positions

        def setParameter(self, name, value):
            self.parameters[name] = value

        def setState(self, state):
            self.state = state

        def getState(self, **kwargs):
            return self.state

    class Minimizer:
        @staticmethod
        def minimize(context, **kwargs):
            if kwargs.get("fail"):
                raise RuntimeError("exposed native minimizer failure")

    return SimpleNamespace(
        Context=Context,
        LangevinIntegrator=Integrator,
        LocalEnergyMinimizer=Minimizer,
        XmlSerializer=SimpleNamespace(
            serialize=lambda obj: "<native>" + str(type(obj).__name__) + "</native>"
        ),
    )


def test_completion_instrumentation_retains_full_requests_actual_calls_and_restores(
    tmp_path,
):
    import json
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import native

    mm = mock_openmm()
    classes = (mm.Context, mm.LangevinIntegrator, mm.LocalEnergyMinimizer.minimize)
    ledger = native.CallLedger(tmp_path)
    restore = native.instrument_completion(mm, ledger, tmp_path)
    try:
        integrator = mm.LangevinIntegrator("300 K", "10 /ps", "5 fs")
        integrator.setRandomNumberSeed(173)
        context = mm.Context(
            SimpleNamespace(getNumParticles=lambda: 2, getForces=lambda: []),
            integrator,
            "CPU",
        )
        context.setPositions([(1, 2, 3), (4, 5, 6)])
        context.setParameter("C", 0.15)
        mm.LocalEnergyMinimizer.minimize(context)
        integrator.step(200)
        state = context.getState(getPositions=True)
        context.setState(state)
    finally:
        restore()
    assert (
        mm.Context,
        mm.LangevinIntegrator,
        mm.LocalEnergyMinimizer.minimize,
    ) == classes
    assert (
        not set(("getState", "setPositions", "setState", "setParameter"))
        & vars(context).keys()
    )
    assert not {"step", "setRandomNumberSeed"} & vars(integrator).keys()
    assert [row.role for row in ledger.calls] == [
        "completion.integrator",
        "completion.set-random-seed",
        "completion.context",
        "completion.set-positions",
        "completion.set-parameter",
        "completion.minimization",
        "completion.integration",
        "completion.receiver",
        "completion.set-state",
    ]
    request = json.loads(ledger.calls[3].requested_json)
    stored = json.loads(
        (tmp_path / request["full_requested_positions"]["relative_path"]).read_text()
    )
    assert stored["values"] == [["1", "2", "3"], ["4", "5", "6"]]
    assert json.loads(ledger.calls[6].requested_json)["steps"] == 200
    assert json.loads(ledger.calls[2].realized_json)["platform"] == "CPU"
    assert all(row.termination == "COMPLETED" for row in ledger.calls)


def test_completion_failures_keep_original_cause_and_inclusive_parent(tmp_path):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import native

    mm = mock_openmm()
    ledger = native.CallLedger(tmp_path)
    restore = native.instrument_completion(mm, ledger, tmp_path)
    try:
        integrator = mm.LangevinIntegrator("300 K", "10 /ps", "5 fs")
        with pytest.raises(RuntimeError, match="native integration failure"):
            ledger.call(
                "completion.pdbfixer", {"seed": 419}, lambda: integrator.step(-1)
            )
    finally:
        restore()
    child, parent = ledger.calls[-2:]
    assert (
        child.role == "completion.integration"
        and child.parent_call_id == parent.call_id
    )
    assert child.termination == parent.termination == "TECHNICAL_FAILURE"
    assert "exposed native integration failure" in child.error_text
    assert "exposed native integration failure" in parent.error_text
    assert ledger.current_parent is None
    assert "step" not in vars(integrator)


def test_amber_origin_join_refuses_lost_genotype_and_missing_inherited_atoms():
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.parameter_audit import (
        realized_atom_origins,
    )

    residue = SimpleNamespace(idx=0, name="MET", atoms=[])
    atom = SimpleNamespace(idx=0, name="CA", atomic_number=6, residue=residue)
    residue.atoms.append(atom)
    structure = SimpleNamespace(atoms=[atom], residues=[residue], bonds=[])
    plan = dict(
        complete_chains=[dict(chain="A", sequence="M", subunit="ssu")],
        complete_heavy_atoms=[
            dict(
                chain="A",
                position=1,
                atom="CA",
                component="MET",
                element="C",
                source_origin=None,
            )
        ],
        authenticated_disulfides=[],
    )
    result = realized_atom_origins(structure, plan)
    assert result["atoms"][0]["amber_atom_index"] == 0
    residue.name = "VAL"
    with pytest.raises(ValueError, match="genotype"):
        realized_atom_origins(structure, plan)
    residue.name = "MET"
    residue.atoms.clear()
    with pytest.raises(ValueError, match="omits completed/inherited"):
        realized_atom_origins(structure, plan)


def test_source_disulfides_use_named_symmetry_and_never_proximity_only():
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.coordinate_plan import (
        source_disulfides,
    )

    identity = (
        Decimal(1),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(1),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(1),
    )
    symmetry = (
        Decimal(0),
        Decimal(1),
        Decimal(0),
        Decimal(1),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(-1),
    )
    operators = (identity, symmetry)
    headers = (
        ["id", "name"]
        + [f"matrix[{i}][{j}]" for i in range(1, 4) for j in range(1, 4)]
        + [f"vector[{i}]" for i in range(1, 4)]
    )
    text = (
        "data_exposed\nloop_\n"
        + "\n".join("_pdbx_struct_oper_list." + name for name in headers)
        + "\n"
    )
    for index, matrix in enumerate(operators, 1):
        text += (
            str(index)
            + (" 1_555 " if index == 1 else " 7_555 ")
            + " ".join(str(v) for v in matrix)
            + " 0 0 0\n"
        )
    connection_headers = [
        "id",
        "conn_type_id",
        "ptnr1_label_asym_id",
        "ptnr1_label_seq_id",
        "ptnr1_label_atom_id",
        "ptnr1_symmetry",
        "ptnr2_label_asym_id",
        "ptnr2_label_seq_id",
        "ptnr2_label_atom_id",
        "ptnr2_symmetry",
        "pdbx_dist_value",
    ]
    text += (
        "loop_\n"
        + "\n".join("_struct_conn." + name for name in connection_headers)
        + "\n"
    )
    for chain in "ACEG":
        text += (
            f"internal{chain} disulf {chain} 172 SG 1_555 {chain} 192 SG 1_555 2.05\n"
        )
    for left, right in (("A", "E"), ("C", "C"), ("G", "G")):
        text += f"cross{left} disulf {left} 247 SG 1_555 {right} 247 SG 7_555 2.05\n"
    inventory = SimpleNamespace(
        operators=tuple(
            ("3ZXW", str(index), matrix, (Decimal(0),) * 3)
            for index, matrix in enumerate(operators, 1)
        )
    )
    chain_map = {
        f"3ZXW.{op}.{chain}": chr(65 + 4 * (int(op) - 1) + "ACEG".index(chain))
        for op in ("1", "2")
        for chain in "ACEG"
    }
    atoms = []
    for op in ("1", "2"):
        for chain in "ACEG":
            for position, xyz in (
                ("172", (0, 0, 0)),
                ("192", (2.05, 0, 0)),
                ("247", (0, 0, 0) if op == "1" else (2.05, 0, 0)),
            ):
                atoms.append(
                    SimpleNamespace(
                        operator_id=op,
                        label_asym_id=chain,
                        label_seq_id=position,
                        atom_id="SG",
                        component_id="CYS",
                        chain_id=f"3ZXW.{op}.{chain}",
                        xyz_angstrom=tuple(Decimal(str(v)) for v in xyz),
                    )
                )
            # This nearby sulfur has no explicit source connection.
            atoms.append(
                SimpleNamespace(
                    operator_id=op,
                    label_asym_id=chain,
                    label_seq_id="300",
                    atom_id="SG",
                    component_id="CYS",
                    chain_id=f"3ZXW.{op}.{chain}",
                    xyz_angstrom=(Decimal(1), Decimal(0), Decimal(0)),
                )
            )
    result = source_disulfides(text, "3ZXW", inventory, atoms, chain_map)
    assert len(result) == 12
    assert all(position != 300 for row in result for _, position in row["partners"])
    assert any(row["partners"] == (("A", 247), ("G", 247)) for row in result)
    with pytest.raises(KeyError):
        source_disulfides(
            text.replace("7_555 2.05", "unknown_555 2.05"),
            "3ZXW",
            inventory,
            atoms,
            chain_map,
        )
