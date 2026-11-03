# SPDX-License-Identifier: MPL-2.0
"""Source-independent mathematical controls; no science or authority produced."""
from dataclasses import fields, replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

EXAMPLES = Path(__file__).parents[1]/'programmes/foundations/emergent-structure/workflows/matrix-response-experiment'


def scientific_inputs():
    return tuple(decode_canonical_bytes((EXAMPLES/name).read_bytes(), kind, maximum_bytes=None)
        for name, kind in (('native-training-scientific-protocol.example.json', NativeTrainingScientificProtocol),
            ('native-training-assay.example.json', ScheduledResponseAssay)))


def test_direct_protocol_and_assay_have_no_historical_source_or_study_operand():
    protocol, assay = scientific_inputs()
    assert {field.name for field in fields(protocol)} == {'protocol_id', 'mathematical_protocol',
        'scalar_definition', 'coordinates', 'numerical_design', 'prefix_policies', 'coordinate_policies'}
    assert not {'public_source', 'templates', 'allocation', 'reservation', 'producers'} & {field.name for field in fields(assay)}
    for value in (protocol, assay):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
    assert protocol.scalar_artifact.sha256 == protocol.scalar_definition.fingerprint()
    assert protocol.scalar_artifact != protocol.full_factor_rule.scalar_closure.normalization_owner
    assert protocol.mathematical_protocol.identity == assay.criterion


def test_direct_protocol_requires_complete_coordinate_policies_and_exact_scalar():
    protocol, _ = scientific_inputs()
    with pytest.raises(ValueError, match='coordinate/prefix coverage'):
        replace(protocol, coordinate_policies=protocol.coordinate_policies[:-1])
    with pytest.raises(ValueError, match='coordinate/prefix coverage'):
        replace(protocol, coordinate_policies=((replace(protocol.coordinate_policies[0][0],
            object_fingerprint='f'*64), protocol.coordinate_policies[0][1]), *protocol.coordinate_policies[1:]))
    with pytest.raises(ValueError, match='typed scalar bytes'):
        replace(protocol, scalar_definition=replace(protocol.scalar_definition, definition_id='scalar.foreign'))
    full=protocol.full_factor_rule
    foreign=replace(full, scalar_closure=replace(full.scalar_closure,
        normalization_owner=replace(full.scalar_closure.normalization_owner, sha256='f'*64)))
    mathematical=replace(protocol.mathematical_protocol, factor_rule=foreign.identity,
        factor_rule_compatibilities=tuple(replace(row, target=foreign)
            for row in protocol.mathematical_protocol.factor_rule_compatibilities))
    with pytest.raises(ValueError, match='original scalar normalization source'):
        replace(protocol, mathematical_protocol=mathematical)


def test_unbound_assay_requires_all_exact_instrument_coefficients_and_numerical_controls():
    _, assay = scientific_inputs()
    with pytest.raises(ValueError, match='complete declared instrument coefficients'):
        replace(assay, members=assay.members[:-1])
    changed=tuple(replace(member, finite_required=False) if member.name=='receiver_coefficients' else member
        for member in assay.members)
    with pytest.raises(ValueError, match='complete declared instrument coefficients'):
        replace(assay, members=changed)
    with pytest.raises(ValueError, match='positive numerical references'):
        replace(assay, native_reference_tolerance=Decimal(0))
