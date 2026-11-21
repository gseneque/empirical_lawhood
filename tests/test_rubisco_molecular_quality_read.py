# SPDX-License-Identifier: MPL-2.0
"""Independent read composition over authentic raw topology and numeric arrays."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import io
import math
from types import SimpleNamespace as NS

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import MolecularGeometryPolicy
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality_read import RetainedGeometryReader, RetainedMolecularGeometryAssessment
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.test_rubisco_preparation_integrity import topology, amber_text


def prepared(*, compressed=False):
    fields = topology()
    fields['BOND_FORCE_CONSTANT'] = [D(100)]
    fields['ANGLE_EQUIL_VALUE'] = [D('1.5')]
    raw = amber_text(fields).encode('ascii')
    pin = ObjectIdentity('source.test.geometry', 'empirical-lawhood/test/source', '1.0.0', sha256(raw).hexdigest())
    model = NS(identity=ObjectIdentity('model.test.geometry', 'empirical-lawhood/test/model', '1.0.0', '1'*64), raw_topology=pin,
        atoms=tuple(NS(atomic_number=z) for z in (6, 7, 6, 1)),
        bonds=(NS(first=0, second=1), NS(first=2, second=3)))
    a = 1.379
    xyz = np.asarray(((a, 0., 0.), (0., 0., 0.), (a*math.cos(1.5), a*math.sin(1.5), 0.),
        (a*math.cos(1.5)+(0.5 if compressed else a), a*math.sin(1.5), 0.)), dtype='<f8')
    stream = io.BytesIO(); np.save(stream, xyz, allow_pickle=False)
    reader = RetainedGeometryReader(representation=model, policy=MolecularGeometryPolicy(),
        cell=NS(lengths_angstrom=(D(20),)*3), qm_atoms=(), expected_coordinate_sha256=sha256(xyz.tobytes()).hexdigest())
    return reader, raw, stream.getvalue()


def returned(names, *, failed=False):
    return NS(error='retained failure' if failed else None,
        files=NS(files=tuple(NS(relative_path='call/'+name) for name in names)))


@pytest.mark.parametrize('compressed', (False, True))
def test_independent_read_assesses_original_arrays_and_ignores_producer_pass(compressed):
    reader, topology_raw, coordinates = prepared(compressed=compressed)
    # A producer's JSON verdict is deliberately present and never inspected.
    selected = returned(('original.prmtop', 'coordinate-array.npy', 'whole-molecule-quality.json'))
    observed = []
    validators = reader.validators(selected, {'coordinate-array.npy': (10000, observed.append)})
    assert set(validators) == {'original.prmtop', 'coordinate-array.npy'}
    validators['original.prmtop'][1](topology_raw)
    validators['coordinate-array.npy'][1](coordinates)
    assert observed == [coordinates]
    report = reader.assess()
    assert report.disposition == ('REJECTED' if compressed else 'SCREEN_PASSED')
    assert dict(report.census)['atoms'] == 4
    assert ('whole-molecule-bond-deviation' in report.findings) is compressed
    assert decode_canonical_bytes(report.canonical_bytes(), RetainedMolecularGeometryAssessment, maximum_bytes=65536) == report


def test_known_failed_missing_geometry_stays_unevaluable_successful_omission_refuses():
    reader, _, _ = prepared()
    assert not reader.validators(returned((), failed=True))
    assert reader.assess().disposition == 'UNEVALUABLE'
    with pytest.raises(ValueError, match='omits complete geometry'):
        reader.validators(returned(()))


def test_retained_read_preserves_explicit_reactive_pair_policy_and_complete_census():
    reader, raw, original = prepared()
    xyz = np.load(io.BytesIO(original), allow_pickle=False)
    xyz[3] = (0., -.98, 0.)  # Declared N1-H3 bond replaces the original C2-H3 host.
    stream = io.BytesIO(); np.save(stream, xyz, allow_pickle=False)
    reader.expected_coordinate_sha256 = sha256(xyz.tobytes()).hexdigest()
    reader.qm_atoms = (0, 1, 2, 3)
    reader.members = {'original.prmtop': raw, 'coordinate-array.npy': stream.getvalue()}
    assert reader.assess().disposition == 'REJECTED'
    reader.policy = replace(reader.policy, reactive_hydrogen_bond_pairs=((1, 3),))
    report = reader.assess()
    assert report.disposition == 'SCREEN_PASSED'
    assert report.policy.reactive_hydrogen_bond_pairs == ((1, 3),)
    assert dict(report.census)['reactive_hydrogen_bonds'] == 1
    assert decode_canonical_bytes(report.canonical_bytes(), RetainedMolecularGeometryAssessment, maximum_bytes=65536) == report


def test_retained_coordinate_or_topology_substitution_refuses_independently():
    reader, raw, coordinates = prepared()
    reader.members = {'original.prmtop': raw+b'\n', 'coordinate-array.npy': coordinates}
    with pytest.raises(ValueError, match='topology bytes'):
        reader.assess()
    other, _, wrong_coordinates = prepared(compressed=True)
    reader.members = {'original.prmtop': raw, 'coordinate-array.npy': wrong_coordinates}
    with pytest.raises(ValueError, match='selected physical coordinates'):
        reader.assess()
    other.members = {'original.prmtop': raw, 'coordinate-array.npy': wrong_coordinates+b'EXTRA'}
    with pytest.raises(ValueError, match='complete finite physical coordinates'):
        other.assess()


def test_rejected_geometry_cannot_supply_finite_numeric_operands_to_response():
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_read import _values
    from empirical_lawhood.science.records.status import OperationalStatus
    from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
    reader, raw, coordinates = prepared(compressed=True)
    reader.members = {'original.prmtop': raw, 'coordinate-array.npy': coordinates}
    report = NS(original_result=NS(completion=NS(operational_status=OperationalStatus.SUCCEEDED),
        returned=NS(error=None)), numerical_integrity=NS(disposition=AssessmentDisposition.SATISFIED),
        geometry_quality=reader.assess())
    assert _values(report, NS(), include_gradient=True) is None
