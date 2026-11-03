# SPDX-License-Identifier: MPL-2.0
"""Exposed-source software copies of a prospective field; no native execution."""

from dataclasses import FrozenInstanceError, replace
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from fractions import Fraction
import gzip
from hashlib import sha256
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_coupled_preparation as rr


REPO = Path(rr.__file__).resolve().parents[5]
MODULE = Path(__file__).with_name('rr_coupled_embedding.py')
if not MODULE.exists():
    MODULE = REPO / 'src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_coupled_embedding.py'
SPEC = importlib.util.spec_from_file_location(
    'empirical_lawhood.adapters.physical.rubisco_kinetics.rr_coupled_embedding', MODULE)
em = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = em
SPEC.loader.exec_module(em)


@pytest.fixture(scope='module')
def source():
    raw = (REPO / 'tests/fixtures/rubisco/rr_coupled/source-operands.tar.gz').read_bytes()
    assert len(raw) == 1118756
    assert sha256(raw).hexdigest() == 'd1942a3aecd4f629d1ea8dd593f4eed00b0d34da70307e3749a766b26e7e6c98'
    expanded = gzip.decompress(raw)
    assert len(expanded) == 6000640
    with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as archive:
        rows = archive.getmembers()
        assert len(rows) == 7 and all(r.isfile() for r in rows)
        values = {r.name: archive.extractfile(r).read() for r in rows}
    inputs = tuple(values[name] for name, _, _ in rr.SOURCE_BINDINGS)
    return rr.decode_rr_coupled_source(*inputs[:4], inputs[4:])


@pytest.fixture(scope='module')
def fields(source, record_testsuite_property):
    # Six *software* constructions of already exposed sources; no retained run,
    # endpoint inspection, engine, geometry relaxation or native effect.
    result = {(variant, view): em.derive_rr_embedding(rr.construct_rr_initial_context(
        source, variant=variant, proton_view=view)) for variant in rr.VARIANTS for view in rr.PROTON_VIEWS}
    record_testsuite_property('exposed_software_construction_count', 6)
    record_testsuite_property('native_effects', 0)
    return result


def test_exact_charge_and_positive_negative_cut_arithmetic():
    q = em.ExactChargeV1.from_fraction
    zero, positive = em.redistribute_cut_charge(q(Fraction(1, 10)),
        (q(Fraction(-1, 2)), q(Fraction(2, 5)), q(Fraction(1, 5))))
    assert zero.as_fraction() == 0
    assert tuple(v.as_fraction() for v in positive) == (Fraction(-7, 15), Fraction(13, 30), Fraction(7, 30))
    _, negative = em.redistribute_cut_charge(q(Fraction(-3, 20)),
        (q(Fraction(-1, 2)), q(Fraction(2, 5)), q(Fraction(1, 5))))
    assert tuple(v.as_fraction() for v in negative) == (Fraction(-11, 20), Fraction(7, 20), Fraction(3, 20))
    with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
        assert q(Fraction(1, 3)).decimal50 == Decimal('0.' + '3' * 50)
    for args in ((2, 6), (True, 1), (0, 0), (1, -3)):
        with pytest.raises(ValueError, match='canonical exact'):
            em.ExactChargeV1(*args)
    with pytest.raises(ValueError, match='immutable recipients'):
        em.redistribute_cut_charge(q(Fraction(1, 10)), [q(Fraction())] * 3)


def test_full_two_chain_census_exclusion_and_all_five_zero_sites(fields):
    sizes = {'unedited-reference': (13752, 13747, -6), 'D263N': (13754, 13749, -5), 'H287N': (13749, 13744, -6)}
    for (variant, _), field in fields.items():
        count, nonzero, q = sizes[variant]
        ids = {r.atom.atom_id for r in field.field_atoms}
        assert len(ids) == count and field.nonzero_charge_count == nonzero
        assert not ids & set(field.real_qm_atom_ids + field.cap_atom_ids)
        assert ids | set(field.real_qm_atom_ids) == {a.atom_id for a in field.context.physical_atoms}
        zeros = [r.atom for r in field.field_atoms if r.field_charge.numerator == 0]
        assert {(a.chain, a.author_position, a.name) for a in zeros} == {
            ('A', position, 'CA') for position in (191, 193, 194, 263, 287)}
        assert len(field.source_excluded_parent_indices) == 76
        assert field.context.formal_quantum_charge == q
        assert field.context.status == 'GEOMETRY_UNREADY'
        assert field.native_effects == 0 and not field.executable_native_hamiltonian


def test_full_spectator_residue_reassignment_and_active_backbone_policy(fields, source):
    donor = {(a.chain, a.author_position, a.name): a for a in source.atoms}
    for (variant, _), field in fields.items():
        for assignment in field.residue_assignments:
            rows = [r for r in field.field_atoms if (r.atom.chain, r.atom.author_position) ==
                    (assignment.chain, assignment.author_position)]
            assert len(rows) == (14 if assignment.target_component == 'ASN' else 17)
            assert set(assignment.atom_joins) == {(r.atom.atom_id, r.source_charge_atom_index) for r in rows}
            for r in rows:
                expected = donor['B', assignment.donor_author_position, r.atom.name]
                assert r.source_charge_atom_index == expected.index
                assert r.source_amber_atom_type == expected.native_tokens[5]
                assert r.source_scaled_charge_token == expected.native_tokens[8]
                assert r.field_charge.as_fraction() == Fraction(expected.native_tokens[8]) / Fraction('18.2223')
        active = [r for r in field.field_atoms if r.atom.chain == 'A' and r.atom.author_position in (263, 287)]
        for r in active:
            assert r.assignment_role == 'active-A-fixed-parent-backbone'
            assert r.source_charge_atom_index == r.atom.parent_atom_index
        if variant == 'D263N':
            # In particular, avoid donating the ASN backbone to active A: that
            # would add an unintended +0.14660000055 field charge alongside +1 QM.
            n = next(r for r in active if r.atom.author_position == 263 and r.atom.name == 'N')
            assert n.source_charge_decimal50 == Decimal('-.5163')
            assert n.charge_before_boundary.decimal50 != Decimal('-.4157')
        if variant != 'H287N':
            h = next(r for r in field.field_atoms if (r.atom.chain, r.atom.author_position, r.atom.name) == ('B', 287, 'HD1'))
            assert h.atom.parent_atom_index != h.source_charge_atom_index
            assert h.source_charge_atom_index == 8258 and h.field_charge.decimal50 == Decimal('.3649')


def test_native_token_totals_relative_formal_contrasts_and_shared_fragment_offset(fields):
    reference = fields['unedited-reference', 'V2']
    # Independent fixed-source Decimal values are comparisons, not obtained by
    # reproducing the implementation's donor/exclusion loops.
    expected = {
        'unedited-reference': Decimal('-24.507098484867442638964345883889519983756166894410'),
        'D263N': Decimal('-23.507098482123551911668669706897592510275870773722'),
        'H287N': Decimal('-24.507098482123551911668669706897592510275870773722'),
    }
    for (variant, _), field in fields.items():
        assert abs(Fraction(field.mm_charge.decimal50) - Fraction(expected[variant])) < Fraction(1, 10**47)
        assert field.mm_charge == field.mm_charge_before_boundary
        assert field.source_core_charge.decimal50 == Decimal('-29.999996494493011310317577912777201560725045685781')
        assert field.source_excluded_partial_charge.decimal50 == Decimal('-5.4928980090767905258940967934892960822728195672336')
        assert field.nominal_source_formal_charge == -30
        assert field.nominal_context_formal_charge == (-28 if variant == 'D263N' else -30)
        assert Fraction('-0.5072') < field.hybrid_minus_nominal_formal_charge.as_fraction() < Fraction('-0.5070')
        assert abs(field.decimal50_field_rounding_residual.as_fraction()) < Fraction(1, 10**45)
        assert abs(field.binary64_field_rounding_residual.as_fraction()) < Fraction(1, 10**12)
    d = fields['D263N', 'V2'].hybrid_charge.as_fraction() - reference.hybrid_charge.as_fraction()
    h = fields['H287N', 'V2'].hybrid_charge.as_fraction() - reference.hybrid_charge.as_fraction()
    assert Fraction(2) < d < Fraction('2.00000001')
    assert Fraction() < h < Fraction('0.00000001')


def test_identical_field_for_paired_proton_views_and_distinct_mutant_fields(fields):
    for variant in rr.VARIANTS:
        first, second = fields[variant, 'V2'], fields[variant, 'V3']
        assert first.field_atoms == second.field_atoms
        assert first.field_sha256 == second.field_sha256
        assert first.mm_charge == second.mm_charge
        assert first.real_qm_atom_ids != ()
    assert len({fields[v, 'V2'].field_sha256 for v in rr.VARIANTS}) == 3


def test_whole_cut_transfer_scope_exact_charge_and_deep_immutability(fields):
    f = fields['D263N', 'V2']; rows = {r.atom.atom_id: r for r in f.field_atoms}
    assert len(f.boundary_transfers) == 5
    used = set()
    for t in f.boundary_transfers:
        ids = (t.ca_atom_id,) + t.recipient_atom_ids
        assert not used.intersection(ids)
        used.update(ids)
        assert tuple(rows[i].atom.name for i in t.recipient_atom_ids) == ('N', 'C', 'HA')
        assert all(rows[i].atom.chain == 'A' and rows[i].atom.author_position == t.author_position for i in ids)
        before = sum((rows[i].charge_before_boundary.as_fraction() for i in ids), Fraction())
        after = sum((rows[i].field_charge.as_fraction() for i in ids), Fraction())
        assert before == after
        for i in t.recipient_atom_ids:
            assert rows[i].field_charge.as_fraction() - rows[i].charge_before_boundary.as_fraction() == t.equal_increment.as_fraction()
    with pytest.raises(FrozenInstanceError):
        f.field_atoms = ()
    with pytest.raises(ValueError, match='init=False'):
        replace(f, mm_charge=em.ExactChargeV1(0, 1))
    with pytest.raises(TypeError):
        em.RrEmbeddingFieldV1(f.context, field_atoms=())


def test_field_rows_refuse_nonfinite_unbounded_and_false_source_witness(fields):
    r = fields['unedited-reference', 'V2'].field_atoms[0]
    for coords in ((Decimal('NaN'), Decimal(0), Decimal(0)), (Decimal(10001), Decimal(0), Decimal(0))):
        with pytest.raises(ValueError, match='finite|bounded immutable'):
            replace(r, atom=replace(r.atom, coordinates=coords))
    with pytest.raises(ValueError, match='source charge witnesses'):
        replace(r, source_scaled_charge_token='0')
    with pytest.raises(ValueError, match='bounded immutable'):
        replace(r, boundary_transfer_ids=[])


def test_cold_import_without_native_or_numerical_families():
    code = '''
import importlib.abc, importlib.util, sys
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','pyscf','openmm','pyarrow','h5py','onnx','safetensors'}:
            raise AssertionError('cold import entered '+fullname)
sys.meta_path.insert(0, Guard())
spec=importlib.util.spec_from_file_location('empirical_lawhood.adapters.physical.rubisco_kinetics.rr_coupled_embedding',sys.argv[1])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
assert module.MODEL_ID=='rr-coupled-source-charge-embedding-proposal-v1'
'''
    run = subprocess.run([sys.executable, '-c', code, str(MODULE)], capture_output=True,
                         text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=15)
    assert run.returncode == 0, run.stderr
