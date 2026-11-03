"""Pure synthetic doubles; no native import, context, source or QM callback."""

from copy import deepcopy
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import native_coupling as M

PATH = Path(M.__file__)


class NonbondedForce:
    def __init__(self, particles, exceptions):
        self.particles = list(particles)
        self.exceptions = list(exceptions)

    def getNumParticles(self):
        return len(self.particles)

    def getNumExceptions(self):
        return len(self.exceptions)

    def getParticleParameters(self, index):
        return self.particles[index]

    def getExceptionParameters(self, index):
        return self.exceptions[index]

    def setExceptionParameters(self, index, *row):
        self.exceptions[index] = row


class System:
    def __init__(self, force):
        self.force = force

    def getForces(self):
        return [self.force]

    def getNumParticles(self):
        return self.force.getNumParticles()


def fixture():
    f = NonbondedForce(
        ((0.0, 0.3, 0.2), (0.2, 0.4, 0.3), (-0.3, 0.5, 0.4), (0.4, 0.6, 0.5)),
        ((0, 1, 0.031, 0.44, 0.12), (1, 2, -0.02, 0.45, 0.13), (2, 3, 0.0, 0.46, 0.0)),
    )
    return System(f)


def test_independent_exception_products_and_lj_preservation():
    s = fixture()
    old = deepcopy(s.force.exceptions)
    result = M.correct_coulomb_exceptions(
        s, (0,), (0.0, 0.2, -0.3, 0.4), {(1, 2): Fraction(6, 5)}
    )
    assert s.force.exceptions[0][2] == 0.0
    # Independent raw charge-product/scaling oracle; no implementation mirror.
    assert s.force.exceptions[1][2] == pytest.approx(-0.05, abs=1e-17)
    assert s.force.exceptions[2][2] == 0.0
    assert [r[3:] for r in s.force.exceptions] == [r[3:] for r in old]
    assert result["qm_containing_zeroed_count"] == 1
    assert len(result["changed_products"]) == 2


def test_zero_old_charge_product_can_become_active_mm14():
    s = fixture()
    M.correct_coulomb_exceptions(
        s, (0,), (0.0, 0.2, -0.3, 0.4), {(1, 2): Fraction(6, 5), (2, 3): Fraction(6, 5)}
    )
    assert s.force.exceptions[2][2] == pytest.approx(-0.1, abs=1e-17)


@pytest.fixture
def synthetic_unit_quantities():
    """Disclosed source-shaped unit/list double; no actual OpenMM qualification."""
    class Unit:
        def __init__(self, label):
            self.label = label
        def __pow__(self, exponent):
            return Unit(self.label + "^" + str(exponent))

    class Quantity:
        def __init__(self, value, unit):
            self.value, self.unit = value, unit
        def value_in_unit(self, unit):
            assert unit.label == self.unit.label
            return self.value
        def __mul__(self, scale):
            return Quantity(self.value * scale, self.unit)
        def __add__(self, other):
            return Quantity(self.value + other.value_in_unit(self.unit), self.unit)
        def __eq__(self, other):
            return isinstance(other, Quantity) and self.unit.label == other.unit.label and self.value == other.value

    return SimpleNamespace(Quantity=Quantity, elementary_charge=Unit("charge"),
        nanometer=Unit("length"), kilojoule_per_mole=Unit("energy"))


def native_list_fixture(unit, tampered_column=None):
    """Model pinned SWIG get/set wrappers, including fresh unit-bearing lists."""

    class NonbondedForce:
        def __init__(self):
            self.rows = [
                [0, 1, 0.031, 0.44, 0.12],
                [1, 2, -0.02, 0.45, 0.13],
                [2, 3, 0.0, 0.46, 0.0],
            ]
            self.updated = set()

        def getNumParticles(self):
            return 4

        def getNumExceptions(self):
            return len(self.rows)

        def getExceptionParameters(self, index):
            result = list(self.rows[index])
            result[2] = unit.Quantity(result[2], unit.elementary_charge**2)
            result[3] = unit.Quantity(result[3], unit.nanometer)
            result[4] = unit.Quantity(result[4], unit.kilojoule_per_mole)
            if index in self.updated and tampered_column is not None:
                if tampered_column == 0:
                    result[0] = 3
                else:
                    result[tampered_column] *= 2
                    if tampered_column == 2:
                        result[2] += unit.Quantity(0.1, unit.elementary_charge**2)
            return result

        def setExceptionParameters(self, index, a, b, charge_product, sigma, epsilon):
            # Model source wrapper conversion of Quantities to raw doubles.
            self.rows[index] = [
                a,
                b,
                charge_product,
                sigma.value_in_unit(unit.nanometer),
                epsilon.value_in_unit(unit.kilojoule_per_mole),
            ]
            self.updated.add(index)

    return System(NonbondedForce())


def test_native_list_shape_preserves_unit_double_lj_and_corrected_products(
    synthetic_unit_quantities,
):
    unit = synthetic_unit_quantities
    system = native_list_fixture(unit)
    before = [
        system.force.getExceptionParameters(i) for i in range(system.force.getNumExceptions())
    ]
    assert all(type(row) is list for row in before)
    # This exact source-shaped container comparison caused the exposed refusal.
    assert before[0][:2] != tuple(before[0][:2])
    result = M.correct_coulomb_exceptions(
        system,
        (0,),
        (0.0, 0.2, -0.3, 0.4),
        {(1, 2): Fraction(6, 5)},
        unit=unit,
    )
    after = [system.force.getExceptionParameters(i) for i in range(len(before))]
    assert [row[:2] for row in after] == [row[:2] for row in before]
    assert [row[3:] for row in after] == [row[3:] for row in before]
    assert after[0][2].value_in_unit(unit.elementary_charge**2) == 0.0
    assert after[1][2].value_in_unit(unit.elementary_charge**2) == pytest.approx(-0.05)
    assert after[2][2].value_in_unit(unit.elementary_charge**2) == 0.0
    assert result["all_exception_lj_preserved"]


@pytest.mark.parametrize(
    ("tampered_column", "message"),
    [
        (0, "altered native LJ or indices"),
        (3, "altered native LJ or indices"),
        (4, "altered native LJ or indices"),
        (2, "Coulomb product was not updated"),
    ],
)
def test_native_list_unit_double_tampering_still_refuses(
    synthetic_unit_quantities, tampered_column, message
):
    unit = synthetic_unit_quantities
    with pytest.raises(ValueError, match=message):
        M.correct_coulomb_exceptions(
            native_list_fixture(unit, tampered_column),
            (0,),
            (0.0, 0.2, -0.3, 0.4),
            {(1, 2): Fraction(6, 5)},
            unit=unit,
        )


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf")])
def test_numeric_refusal(bad):
    with pytest.raises(ValueError):
        M.correct_coulomb_exceptions(
            fixture(), (0,), (0.0, bad, -0.3, 0.4), {(1, 2): Fraction(6, 5)}
        )


def test_source_scale_missing_and_missing_native_pair_refuse():
    with pytest.raises(ValueError, match="no source SCEE"):
        M.correct_coulomb_exceptions(fixture(), (0,), (0.0, 0.2, -0.3, 0.4), {})
    with pytest.raises(ValueError, match="missing from native exceptions"):
        M.correct_coulomb_exceptions(
            fixture(),
            (0,),
            (0.0, 0.2, -0.3, 0.4),
            {(1, 2): Fraction(6, 5), (1, 3): Fraction(6, 5)},
        )


def test_invalid_qm_charge_and_duplicate_pairs_refuse():
    with pytest.raises(ValueError, match="must be zero"):
        M.correct_coulomb_exceptions(
            fixture(), (0,), (0.1, 0.2, -0.3, 0.4), {(1, 2): Fraction(6, 5)}
        )
    s = fixture()
    s.force.exceptions.append(s.force.exceptions[0])
    with pytest.raises(ValueError, match="duplicate"):
        M.correct_coulomb_exceptions(
            s, (0,), (0.0, 0.2, -0.3, 0.4), {(1, 2): Fraction(6, 5)}
        )


def test_mask_oracle_retains_two_qm_boundary_torsion_and_cross_lj():
    before = {
        "force_roster": ("NonbondedForce",),
        "particles": ((0.1, 0.3, 0.2), (0.2, 0.4, 0.3), (-0.3, 0.5, 0.4)),
        "exceptions": ((0, 2, 0.1, 0.5, 0.6),),
        "bonds": ((0, 1, 0.1, 5.0), (1, 2, 0.2, 6.0)),
        "angles": ((0, 1, 2, 1.0, 7.0),),
        "torsions": ((0, 1, 2, 2, 1, 0.0, 8.0),),
    }
    after = deepcopy(before)
    after["particles"] = ((0.0, 0.3, 0.2), (0.0, 0.4, 0.3), (-0.3, 0.5, 0.4))
    after["exceptions"] = ((0, 2, 0.0, 0.5, 0.6), (0, 1, 0.0, 0.0, 0.0))
    after["bonds"] = ((0, 1, 0.1, 0.0), (1, 2, 0.2, 6.0))
    after["angles"] = ((0, 1, 2, 1.0, 0.0),)
    result = M.verify_ash_masks(before, after, (0, 1), (0.0, 0.0, -0.3))
    assert result["masked_bonded_counts"] == {"bonds": 1, "angles": 1, "torsions": 0}
    assert result["cross_exception_lj_preserved_count"] == 1
    after["torsions"] = ((0, 1, 2, 2, 1, 0.0, 0.0),)
    with pytest.raises(ValueError, match="retained boundary term"):
        M.verify_ash_masks(before, after, (0, 1), (0.0, 0.0, -0.3))


class LinkTheory:
    def __init__(self):
        self.boundaryatoms = {0: [1]}
        self.qmatoms = [0]
        self.count = 0

    def create_linkatoms(self, coords):
        self.count += 1
        direction = [coords[1][i] - coords[0][i] for i in range(3)]
        length = math.sqrt(sum(v * v for v in direction))
        return [[coords[0][i] + 1.09 * direction[i] / length for i in range(3)]]


def test_links_keep_native_derivative_formula_and_record_roundoff():
    t = LinkTheory()
    coordinates = ((0.0, 0.0, 0.0), (1.5, 0.0, 0.0), (2.0, 3.0, 4.0))
    held = ("cap", 1, 0, 1, (1.09 + 2e-15, 0.0, 0.0))
    result = M._bind_fixed_links(t, coordinates, (held,))
    generated = t.create_linkatoms(coordinates)
    assert generated == [[1.09, 0.0, 0.0]]
    assert generated[0][0] != held[4][0]
    assert result["native_link_generation_unmodified"]
    assert 0 < result["links"][0][-1] < 1e-10
    changed = ((1e-11, 0.0, 0.0), coordinates[1], coordinates[2])
    with pytest.raises(ValueError, match="endpoint moved"):
        t.create_linkatoms(changed)


def test_inferred_extra_cut_and_large_cap_delta_refuse():
    t = LinkTheory()
    t.boundaryatoms[0].append(2)
    with pytest.raises(ValueError, match="boundary"):
        M._bind_fixed_links(
            t,
            ((0.0, 0.0, 0.0), (1.5, 0.0, 0.0), (2.0, 0.0, 0.0)),
            (("cap", 1, 0, 1, (1.09, 0.0, 0.0)),),
        )
    with pytest.raises(ValueError, match="initial link geometry"):
        M._bind_fixed_links(
            LinkTheory(),
            ((0.0, 0.0, 0.0), (1.5, 0.0, 0.0)),
            (("cap", 1, 0, 1, (1.091, 0.0, 0.0)),),
        )


class TypeList(list):
    def claim(self):
        pass


class Term:
    def delete(self):
        pass


class Bond(Term):
    def __init__(self, a, b, type, order=1.0, qualitative_type=None):
        self.atom1, self.atom2, self.type, self.order, self.qualitative_type = (
            a,
            b,
            type,
            order,
            qualitative_type,
        )


class Angle(Term):
    def __init__(self, a, b, c, type):
        self.atom1, self.atom2, self.atom3, self.type = a, b, c, type


class Dihedral(Term):
    def __init__(self, a, b, c, d, type, improper=False, ignore_end=False):
        self.atom1, self.atom2, self.atom3, self.atom4, self.type = a, b, c, d, type
        self.improper, self.ignore_end = improper, ignore_end


def splice_fixture():
    names = "N H CA HA CB HB2 HB3 CG ND1 HD1 CE1 HE1 NE2 CD2 HD2 C O".split()
    residues = [SimpleNamespace(idx=i, name="OTHER", atoms=[]) for i in range(6)]
    atoms = []

    def atom(name, res):
        a = SimpleNamespace(
            idx=len(atoms),
            name=name,
            residue=res,
            atomic_number=1 if name.startswith("H") else 6,
            mass=1.0 if name.startswith("H") else 12.0,
            type="H" if name.startswith("H") else "C",
            nb_idx=1,
            charge=0.1,
            atom_type=SimpleNamespace(rmin=1.0, epsilon=0.2),
        )
        atoms.append(a)
        res.atoms.append(a)
        return a

    previous = atom("C", residues[0])
    residues[1].name = "HID"
    donor = {n: atom(n, residues[1]) for n in names}
    atom("N", residues[2])
    target_previous = atom("C", residues[3])
    residues[4].name = "HIE"
    target = {n: atom("HE2" if n == "HD1" else n, residues[4]) for n in names}
    atom("N", residues[5])
    b = SimpleNamespace(k=7.0, req=1.2)
    a = SimpleNamespace(k=8.0, theteq=110.0)
    d = SimpleNamespace(phi_k=9.0, per=2, phase=180.0, scee=1.2, scnb=2.0)
    source = SimpleNamespace(
        atoms=atoms,
        residues=residues,
        bonds=[
            Bond(donor["ND1"], donor["HD1"], b),
            Bond(target["NE2"], target["HD1"], b),
        ],
        angles=[
            Angle(donor["CB"], donor["CA"], donor["N"], a),
            Angle(target["CB"], target["CA"], target["N"], a),
        ],
        dihedrals=[
            Dihedral(
                donor["CB"], donor["CA"], donor["N"], previous, d, ignore_end=True
            ),
            Dihedral(target["CB"], target["CA"], target["N"], target_previous, d),
        ],
        bond_types=TypeList([b]),
        angle_types=TypeList([a]),
        dihedral_types=TypeList([d]),
    )
    source.update_dihedral_exclusions = lambda: None
    source.remake_parm = lambda: None
    return (
        source,
        deepcopy(source),
        {donor[n].idx: target[n].idx for n in names},
        SimpleNamespace(Bond=Bond, Angle=Angle, Dihedral=Dihedral),
    )


def test_complete_donor_terms_neighbor_join_and_original_immutable():
    source, dry, mapping, p = splice_fixture()
    source_old = [(a.name, a.type, a.charge) for a in source.atoms]
    result = M.splice_spectator_hid(source, dry, mapping, parmed=p)
    assert result["bonded_parameter_splice_complete"]
    assert len(result["donor_atom_assignments"]) == 17
    assert len(result["outside_neighbor_joins"]) == 1
    assert dry.residues[4].name == "HID"
    assert "HD1" in {a.name for a in dry.residues[4].atoms}
    assert result["transplanted_terms"]["dihedrals"][0][0][-1] is True
    assert result["transplanted_terms"]["dihedrals"][0][1] == (
        9.0,
        2.0,
        180.0,
        1.2,
        2.0,
    )
    assert source_old == [(a.name, a.type, a.charge) for a in source.atoms]
    assert len(dry.bonds) == 2


def test_missing_or_type_incompatible_donor_boundary_refuses():
    source, dry, mapping, p = splice_fixture()
    dry.residues[3].atoms[0].type = "DIFFERENT"
    with pytest.raises(ValueError, match="neighbor parameter types"):
        M.splice_spectator_hid(source, dry, mapping, parmed=p)
    source, dry, mapping, p = splice_fixture()
    mapping.pop(next(iter(mapping)))
    with pytest.raises(ValueError, match="seventeen"):
        M.splice_spectator_hid(source, dry, mapping, parmed=p)


def test_native_force_extensions_refuse_before_parameter_invention():
    source, dry, mapping, p = splice_fixture()
    source.cmaps = [object()]
    with pytest.raises(ValueError, match="unsupported source force class"):
        M.splice_spectator_hid(source, dry, mapping, parmed=p)


def test_scee_flags_multiplicity_and_ambiguity():
    source, _, _, _ = splice_fixture()
    result = M.source_scee_by_pair(source)
    assert len(result) == 1  # ignore-end donor term is retained but not active1-4.
    extra = deepcopy(source.dihedrals[1])
    extra.type.scee = 2.0
    source.dihedrals.append(extra)
    with pytest.raises(ValueError, match="ambiguous"):
        M.source_scee_by_pair(source)


def test_scratch_refuses_existing_identity(tmp_path):
    with pytest.raises(ValueError, match="new absolute"):
        M._selected_scratch(tmp_path, "a" * 64)


def test_cold_import_and_metadata_only_constructor_refusal():
    code = f"""import importlib.util,sys
p={str(PATH)!r}
s=importlib.util.spec_from_file_location("cold",p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
assert not any(n.split('.')[0] in {{'numpy','openmm','parmed','ash','pyscf','geometric'}} for n in sys.modules)
try:m.build_reference_coupling('/nonexistent',{{}},object(),scratch_directory='/tmp/unselected',protocol_sha256='a'*64)
except ValueError:pass
else:raise AssertionError('unselected manifest accepted')
assert not any(n.split('.')[0] in {{'numpy','openmm','parmed','ash','pyscf','geometric'}} for n in sys.modules)
"""
    subprocess.run(
        [sys.executable, "-I", "-c", code], check=True, capture_output=True, text=True
    )


def test_native_lj_tables_full_lookup_and_coefficients_are_exact():
    s = SimpleNamespace(
        parm_data={
            "NONBONDED_PARM_INDEX": [1, 2, 2, 3],
            "LENNARD_JONES_ACOEF": [1.0, 2.0, 3.0],
            "LENNARD_JONES_BCOEF": [4.0, 5.0, 6.0],
        }
    )
    expected = M.source_lj_tables(s)
    assert M.verify_source_lj_tables(expected, s, stage="mock save/reload")[
        "source_native_lj_tables_exact"
    ]
    s.parm_data["NONBONDED_PARM_INDEX"][1] = 3
    with pytest.raises(ValueError, match="A/B/lookup"):
        M.verify_source_lj_tables(expected, s, stage="corruption")
    s.parm_data["NONBONDED_PARM_INDEX"][1] = 2
    s.parm_data["LENNARD_JONES_BCOEF"][2] += 1e-15
    with pytest.raises(ValueError, match="A/B/lookup"):
        M.verify_source_lj_tables(expected, s, stage="coefficient corruption")


class Callback:
    def __init__(self):
        self.entries = 0

    def run(self, **kwargs):
        self.entries += 1
        return 17.0


class FieldTheory:
    def __init__(self):
        self.boundaryatoms = {0: [1]}
        self.mmatoms = (1, 2)
        self.qm_theory = Callback()
        self.pointcharges = []
        self.prep_entries = 0
        self.runcalls = 0

    def create_linkatoms(self, coords):
        d = [coords[1][i] - coords[0][i] for i in range(3)]
        r = math.sqrt(sum(v * v for v in d))
        return [[coords[0][i] + 1.09 * d[i] / r for i in range(3)]]

    def runprep(self, current_coords):
        self.prep_entries += 1
        self.pointcharges = [0.0, 0.1]
        self.current_qmelems = ["C", "H"]
        self.mm_elems_for_qmprogram = ["C", "H"]

    def run(self, current_coords, **kwargs):
        if self.runcalls == 0:
            self.runprep(current_coords)
        self.runcalls += 1
        return self.qm_theory.run(
            current_coords=(current_coords[0],)
            + tuple(self.create_linkatoms(current_coords)),
            current_MM_coords=(current_coords[1], current_coords[2]),
            MMcharges=self.pointcharges,
            qm_elems=self.current_qmelems,
            mm_elems=self.mm_elems_for_qmprogram,
            PC=True,
        )


def field_fixture(fixed=True):
    t = FieldTheory()
    coords = ((0.0, 0.0, 0.0), (1.5, 0.0, 0.0), (2.0, 3.0, 4.0))
    audit = {}
    M._bind_point_field(
        t, coords, ("C", "C", "H"), (0,), (0.0, 0.1), fixed_mm=fixed, audit=audit
    )
    return t, coords, audit


def test_lazy_runprep_admits_once_only_and_checks_before_callback():
    t, coords, audit = field_fixture()
    assert t.prep_entries == t.qm_theory.entries == 0
    assert not audit["point_field_materialized"]
    assert t.run(current_coords=coords) == 17.0
    assert t.run(current_coords=coords) == 17.0
    assert t.prep_entries == 1 and t.qm_theory.entries == 2
    assert audit["verified_callback_entries"] == 2
    assert audit["realized_nonzero_point_charge_atoms"] == 1
    with pytest.raises(ValueError, match="entered twice"):
        t.runprep(coords)


def test_native_numpy_point_charge_count_survives_stage_json(monkeypatch):
    import numpy as np

    original = FieldTheory.runprep

    def native_array_prep(self, current_coords):
        original(self, current_coords)
        self.pointcharges = np.asarray(self.pointcharges)

    monkeypatch.setattr(FieldTheory, "runprep", native_array_prep)
    theory, coords, audit = field_fixture()
    assert theory.run(current_coords=coords) == 17.0
    assert type(audit["realized_nonzero_point_charge_atoms"]) is int
    assert json.loads(json.dumps(audit, allow_nan=False))[
        "realized_nonzero_point_charge_atoms"
    ] == 1


def test_reference_mm_drift_and_field_cache_tamper_refuse_before_callback():
    t, coords, audit = field_fixture()
    changed = (coords[0], coords[1], (2.0, 3.0, 4.00000000001))
    with pytest.raises(ValueError, match="fixed reference MM"):
        t.run(current_coords=changed)
    assert t.prep_entries == t.qm_theory.entries == 0
    t.run(current_coords=coords)
    t.pointcharges[1] = 0.10000000000000002
    with pytest.raises(ValueError, match="ordering differs"):
        t.run(current_coords=coords)
    assert t.qm_theory.entries == 1


def test_control_mm_coordinate_fd_keeps_dynamic_rows_admitted():
    t, coords, audit = field_fixture(fixed=False)
    changed = (coords[0], coords[1], (2.0, 3.001, 4.0))
    assert t.run(current_coords=changed) == 17.0
    assert audit["verified_callback_entries"] == 1


def test_missing_mm_element_order_refuses_lazy_cache_before_callback():
    t, coords, audit = field_fixture()
    t.runprep.__func__.__closure__
    # Corrupt the source-only first-preparation output, not the guard itself.
    old = FieldTheory.runprep
    try:

        def incorrect(self, current_coords):
            old(self, current_coords)
            self.mm_elems_for_qmprogram = ["H", "C"]

        FieldTheory.runprep = incorrect
        t, coords, audit = field_fixture()
        with pytest.raises(ValueError, match="element ordering"):
            t.run(current_coords=coords)
        assert t.qm_theory.entries == 0
    finally:
        FieldTheory.runprep = old


def test_complete_bonded_roundtrip_multiplicity_is_not_collapsed():
    source, _, _, _ = splice_fixture()
    original = M._bonded_topology_witness(source)
    assert M.verify_bonded_roundtrip(original, source)[
        "complete_term_multiplicity_preserved"
    ]
    source.dihedrals.append(deepcopy(source.dihedrals[0]))
    with pytest.raises(ValueError, match="multiplicity changed"):
        M.verify_bonded_roundtrip(original, source)


class StripOnlyAmberDouble:
    """A destructive library strip double; slicing is forbidden deliberately."""

    def __init__(self):
        residue = SimpleNamespace(idx=0, name="SYNTHETIC")
        self.atoms = [
            SimpleNamespace(
                idx=i,
                name=f"A{i}",
                type=f"T{i % 25 + 1}",
                nb_idx=i % 25 + 1,
                mass=12.0,
                charge=(i - 13) / 100,
                atomic_number=6,
                residue=residue,
            )
            for i in range(26)
        ]
        # Independent closed-form triangular lookup, with 24/25 absent in dry.
        self.parm_data = {
            "POINTERS": [26, 25],
            "ATOM_TYPE_INDEX": [a.nb_idx for a in self.atoms],
            "NONBONDED_PARM_INDEX": [
                max(i, j) * (max(i, j) + 1) // 2 + min(i, j) + 1
                for i in range(25)
                for j in range(25)
            ],
            "LENNARD_JONES_ACOEF": [(i + 1) / 100 for i in range(325)],
            "LENNARD_JONES_BCOEF": [(i + 1) / 200 for i in range(325)],
        }
        self.pointers = {"NATOM": 26, "NTYPES": 25}
        self.box = [10.0, 10.0, 10.0]
        self.bonds, self.angles, self.dihedrals = [], [], []
        self.strip_calls = []
        self.post_strip = None

    def __getitem__(self, selection):
        raise AssertionError("native slice must not rebuild the source lookup")

    def strip(self, selection):
        self.strip_calls.append(selection)
        assert selection == "@24-26"
        assert self.box is None, "clear only the dry box before library remake"
        del self.atoms[23:]
        self.parm_data["POINTERS"][0] = 23
        self.pointers["NATOM"] = 23
        self.parm_data["ATOM_TYPE_INDEX"] = [a.nb_idx for a in self.atoms]
        if self.post_strip is not None:
            self.post_strip(self)

    def remake_parm(self):
        self.parm_data["ATOM_TYPE_INDEX"] = [a.nb_idx for a in self.atoms]

    def save(self, path, *, overwrite):
        assert overwrite is False
        with Path(path).open("xb") as stream:
            stream.write(b"SYNTHETIC-NATIVE-PREPARATION-DOUBLE-NOT-AN-AMBER-TOPOLOGY")


@pytest.fixture
def strip_operands(monkeypatch):
    monkeypatch.setattr(M, "FULL_ATOMS", 26)
    monkeypatch.setattr(M, "DRY_ATOMS", 23)
    source = StripOnlyAmberDouble()
    dry = deepcopy(source)
    calls = []

    def load_file(path):
        calls.append(path)
        return dry

    return source, dry, SimpleNamespace(load_file=load_file), calls


def test_native_strip_preserves_all_25_slots_and_pristine_full_source(strip_operands):
    source, dry, parmed, calls = strip_operands
    original = deepcopy(source.__dict__)
    result, audit = M._strip_bound_dry_core(
        Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed
    )
    assert result is dry and result is not source
    assert calls == ["/tmp/synthetic-source.prmtop"]
    assert dry.strip_calls == ["@24-26"]
    assert len(dry.atoms) == 23 and len(source.atoms) == 26
    assert [a.nb_idx for a in dry.atoms] == list(range(1, 24))
    assert dry.pointers["NTYPES"] == dry.parm_data["POINTERS"][1] == 25
    for flag in ("NONBONDED_PARM_INDEX", "LENNARD_JONES_ACOEF", "LENNARD_JONES_BCOEF"):
        assert dry.parm_data[flag] == source.parm_data[flag]
    assert source.__dict__ == original
    assert audit["table_counts"] == {
        "NONBONDED_PARM_INDEX": 625,
        "LENNARD_JONES_ACOEF": 325,
        "LENNARD_JONES_BCOEF": 325,
    }
    assert audit["unused_retained_type_slots"] == (24, 25)
    assert audit["pristine_donor_source_unchanged"]
    assert not audit["table_rebuilding_or_restoration"]


@pytest.mark.parametrize("alias_kind", ("whole-object", "retained-atom"))
def test_dry_reload_alias_refuses_before_any_source_mutation(strip_operands, alias_kind):
    source, dry, parmed, _ = strip_operands
    original = deepcopy(source.__dict__)
    if alias_kind == "whole-object":
        parmed.load_file = lambda path: source
    else:
        dry.atoms[0] = source.atoms[0]
    with pytest.raises(ValueError, match="aliases pristine"):
        M._strip_bound_dry_core(Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed)
    assert source.__dict__ == original
    assert not dry.strip_calls


@pytest.mark.parametrize("pointer", ("array", "dict"))
@pytest.mark.parametrize("stage", ("reload", "strip"))
def test_unused_type_slot_shrink_is_refused_in_both_pointer_representations(
    strip_operands, pointer, stage
):
    source, dry, parmed, _ = strip_operands

    def shrink(obj):
        if pointer == "array":
            obj.parm_data["POINTERS"][1] = 23
        else:
            obj.pointers["NTYPES"] = 23

    if stage == "reload":
        shrink(dry)
    else:
        dry.post_strip = shrink
    with pytest.raises(ValueError, match="complete NTYPES slots"):
        M._strip_bound_dry_core(Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed)
    assert source.pointers["NTYPES"] == source.parm_data["POINTERS"][1] == 25
    assert bool(dry.strip_calls) == (stage == "strip")


@pytest.mark.parametrize(
    "flag", ("NONBONDED_PARM_INDEX", "LENNARD_JONES_ACOEF", "LENNARD_JONES_BCOEF")
)
@pytest.mark.parametrize("stage", ("reload", "strip"))
def test_native_lookup_and_exact_coefficients_still_guarded(strip_operands, flag, stage):
    source, dry, parmed, _ = strip_operands

    def corrupt(obj):
        if flag == "NONBONDED_PARM_INDEX":
            obj.parm_data[flag][-1] -= 1  # An unused 25/25 pair remains protected.
        else:
            obj.parm_data[flag][-1] += 1e-15

    if stage == "reload":
        corrupt(dry)
    else:
        dry.post_strip = corrupt
    with pytest.raises(ValueError, match="A/B/lookup"):
        M._strip_bound_dry_core(Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed)


@pytest.mark.parametrize(
    "flag", ("NONBONDED_PARM_INDEX", "LENNARD_JONES_ACOEF", "LENNARD_JONES_BCOEF")
)
def test_unused_source_table_tail_cannot_be_omitted(strip_operands, flag):
    source, dry, parmed, _ = strip_operands
    dry.post_strip = lambda obj: obj.parm_data[flag].pop()
    with pytest.raises(ValueError, match="denominator differs"):
        M._strip_bound_dry_core(Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed)


@pytest.mark.parametrize("field", ("name", "type", "nb_idx", "mass", "charge"))
def test_retained_atom_assignment_tampering_refuses(strip_operands, field):
    source, dry, parmed, _ = strip_operands

    def change(obj):
        atom = obj.atoms[4]
        value = getattr(atom, field)
        setattr(atom, field, value + 1 if isinstance(value, (int, float)) else value + "X")
        if field == "nb_idx":
            obj.parm_data["ATOM_TYPE_INDEX"][4] = atom.nb_idx

    dry.post_strip = change
    with pytest.raises(ValueError, match="retained atom identity/order/types"):
        M._strip_bound_dry_core(Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed)


def test_reordered_atoms_refuse_even_if_indices_are_renumbered(strip_operands):
    source, dry, parmed, _ = strip_operands

    def reorder(obj):
        obj.atoms[0], obj.atoms[1] = obj.atoms[1], obj.atoms[0]
        for i, atom in enumerate(obj.atoms):
            atom.idx = i
        obj.parm_data["ATOM_TYPE_INDEX"] = [a.nb_idx for a in obj.atoms]

    dry.post_strip = reorder
    with pytest.raises(ValueError, match="retained atom identity/order/types"):
        M._strip_bound_dry_core(Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed)


def test_source_atoms_must_remain_pristine_during_destructive_strip(strip_operands):
    source, dry, parmed, _ = strip_operands
    dry.post_strip = lambda obj: setattr(source.atoms[-1], "name", "MUTATED")
    with pytest.raises(ValueError, match="pristine donor source atoms"):
        M._strip_bound_dry_core(Path("/tmp/synthetic-source.prmtop"), source, parmed=parmed)


def test_native_constructor_reloads_bound_path_then_strips_without_slicing(
    strip_operands, monkeypatch
):
    source, dry, _, calls = strip_operands
    operands = iter((source, dry))

    def load_file(path):
        calls.append(path)
        return next(operands)

    monkeypatch.setattr(M, "_validate_reference_manifest", lambda manifest: {"donor_map": {}})
    monkeypatch.setattr(M, "_check_original_source", lambda path: Path(path))
    monkeypatch.setattr(M, "_selected_scratch", lambda path, digest: Path(path))

    def stop_before_further_native_preparation(*args, **kwargs):
        assert args[:2] == (source, dry)
        raise RuntimeError("synthetic-stop-before-donor-preparation")

    monkeypatch.setattr(M, "splice_spectator_hid", stop_before_further_native_preparation)
    with pytest.raises(RuntimeError, match="synthetic-stop-before-donor"):
        M.build_reference_coupling(
            "/tmp/synthetic-source.prmtop",
            {},
            object(),
            scratch_directory="/tmp/synthetic-unused-scratch",
            protocol_sha256="a" * 64,
            native_libraries=SimpleNamespace(
                parmed=SimpleNamespace(load_file=load_file),
                numpy=SimpleNamespace(array=lambda rows: rows),
            ),
        )
    assert calls == ["/tmp/synthetic-source.prmtop"] * 2
    assert dry.strip_calls == ["@24-26"]
    assert source.box == [10.0, 10.0, 10.0] and dry.box is None


def test_after_strip_witness_precedes_type_guard_on_refusal(strip_operands):
    source, dry, parmed, _ = strip_operands
    dry.post_strip = lambda obj: obj.pointers.update(NTYPES=23)
    seen = []

    def observe(stage, obj):
        seen.append((stage, obj.pointers["NTYPES"], len(obj.atoms)))

    with pytest.raises(ValueError, match="complete NTYPES slots"):
        M._strip_bound_dry_core(
            Path("/tmp/synthetic-source.prmtop"),
            source,
            parmed=parmed,
            observe_native=observe,
        )
    assert seen == [
        ("dry-reloaded", 25, 26),
        ("dry-after-strip", 23, 23),
        ("original-after-strip", 25, 26),
    ]


def test_partial_native_strip_exception_still_retains_actual_witness(strip_operands):
    source, dry, parmed, _ = strip_operands

    def fail_after_partial_native_strip(obj):
        obj.parm_data["LENNARD_JONES_BCOEF"][-1] += 1.0
        raise RuntimeError("synthetic-library-strip-error")

    dry.post_strip = fail_after_partial_native_strip
    seen = []

    def observe(stage, obj):
        seen.append((stage, obj.parm_data["LENNARD_JONES_BCOEF"][-1]))

    with pytest.raises(RuntimeError, match="synthetic-library-strip-error"):
        M._strip_bound_dry_core(
            Path("/tmp/synthetic-source.prmtop"),
            source,
            parmed=parmed,
            observe_native=observe,
        )
    assert seen[-2:] == [("dry-after-strip", 2.625), ("original-after-strip", 1.625)]


@pytest.fixture
def preparation_operands(strip_operands, monkeypatch):
    source, dry, _, calls = strip_operands
    manifest = {
        "plan_id": "synthetic-no-scientific-authority",
        "physical_atoms": [
            [f"amber:{i + 1}", "C", [i / 10, 0.0, 0.0], "X", 1, "SYNTHETIC", a.name]
            for i, a in enumerate(source.atoms[:23])
        ],
        "physical_parameters": [
            [
                f"amber:{i + 1}",
                i + 1,
                i + 1,
                a.type,
                a.nb_idx,
                str(a.mass),
                str(Fraction(str(a.charge)) * Fraction("18.2223")),
            ]
            for i, a in enumerate(source.atoms[:23])
        ],
        "physical_bonds_full_indices_0based": [],
        "spectator_target_original_external_bond_witnesses": [],
        "spectator_target_prepared_external_bonds": [],
        "qm_lj_type_policy": "SYNTHETIC-ONLY",
    }
    selected = {
        "elements": ("C",) * 23,
        "donor_map": {},
        "charges": (0.0,) * 23,
        "coordinates": tuple(tuple(r[2]) for r in manifest["physical_atoms"]),
        "qm_indices": tuple(range(23)),
    }
    monkeypatch.setattr(M, "_validate_reference_manifest", lambda value: selected)
    monkeypatch.setattr(M, "_check_original_source", lambda value: Path(value))
    monkeypatch.setattr(M, "splice_spectator_hid", lambda *args, **kwargs: {"synthetic": True})

    def load_file(path):
        calls.append(path)
        if len(calls) == 1:
            return source
        if len(calls) == 2:
            return dry
        if len(calls) == 3:
            return deepcopy(dry)
        raise AssertionError("undeclared fourth native topology load")

    return source, dry, manifest, selected, SimpleNamespace(load_file=load_file), calls


def test_factored_preparation_completes_without_context_or_ash(
    preparation_operands, tmp_path, monkeypatch
):
    source, dry, manifest, selected, parmed, calls = preparation_operands
    original = deepcopy(source.__dict__)

    def forbid_native_model(*args, **kwargs):
        raise AssertionError("preparation must not construct ASH/OpenMM")

    monkeypatch.setattr(M, "_construct_ash", forbid_native_model)
    seen = []
    prepared = M.prepare_reference_topology(
        Path("/tmp/synthetic-source.prmtop"),
        manifest,
        scratch_directory=tmp_path / "new-preparation",
        protocol_sha256="a" * 64,
        parmed=parmed,
        native_numpy=SimpleNamespace(array=lambda rows: rows),
        observe_native=lambda stage, obj: seen.append(stage),
    )
    assert seen == [
        "original-loaded",
        "dry-reloaded",
        "dry-after-strip",
        "original-after-strip",
        "dry-after-donor-splice",
        "dry-after-charge-remake",
        "dry-after-save",
        "derived-reloaded",
        "original-preparation-complete",
    ]
    assert len(calls) == 3 and calls[:2] == ["/tmp/synthetic-source.prmtop"] * 2
    assert source.__dict__ == original
    assert prepared.source is source and prepared.dry is dry
    assert prepared.selected is selected
    assert prepared.audit["pristine_full_source_after_preparation"]
    assert prepared.audit["native_contexts"] == prepared.audit["qm_callbacks"] == 0


def test_full_constructor_calls_same_factored_preparation(
    preparation_operands, tmp_path, monkeypatch
):
    _, _, manifest, _, parmed, _ = preparation_operands
    actual = M.prepare_reference_topology
    entries = []

    def observed_prepare(*args, **kwargs):
        entries.append((args, kwargs))
        return actual(*args, **kwargs)

    def stop_before_ash(*args, **kwargs):
        raise RuntimeError("synthetic-stop-before-ash")

    monkeypatch.setattr(M, "prepare_reference_topology", observed_prepare)
    monkeypatch.setattr(M, "_construct_ash", stop_before_ash)
    with pytest.raises(RuntimeError, match="synthetic-stop-before-ash"):
        M.build_reference_coupling(
            "/tmp/synthetic-source.prmtop",
            manifest,
            object(),
            scratch_directory=tmp_path / "new-full-preparation",
            protocol_sha256="a" * 64,
            native_libraries=SimpleNamespace(
                parmed=parmed, numpy=SimpleNamespace(array=lambda rows: rows)
            ),
        )
    assert len(entries) == 1
    assert entries[0][1]["parmed"] is parmed


def test_explicit_profile_selection_precedes_scratch_or_native_import(tmp_path, monkeypatch):
    def forbid_scratch(*args, **kwargs):
        raise AssertionError("unselected native environment cannot create scratch")
    monkeypatch.setattr(M, "_selected_scratch", forbid_scratch)
    with pytest.raises(ValueError, match="explicit selected native"):
        M.build_ethane_control(object(), scratch_directory=tmp_path / "unentered", protocol_sha256="a" * 64)
    with pytest.raises(ValueError, match="not both"):
        M.build_ethane_control(object(), scratch_directory=tmp_path / "unentered", protocol_sha256="a" * 64,
            native_libraries=object(), site_packages=tmp_path)
    with pytest.raises(ValueError, match="absolute selected native"):
        M.load_bound_native_libraries(protocol_sha256="a" * 64, site_packages="relative-profile")
