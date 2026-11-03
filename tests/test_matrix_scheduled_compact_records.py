# SPDX-License-Identifier: MPL-2.0
"""Compact representation controls over explicitly hypothetical test sources."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import (
    NAMESPACE, ScheduledCompactBank, ScheduledCompactCommitmentConfig,
    authenticate_prior_publications, compact_committed, compact_identity, compact_native_contract,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import committed
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_bindings import require_committed_bank
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from tests.test_matrix_scheduled_history_bindings import (
    bank as bank, provenance as provenance, scheduled as scheduled, stock as stock,
)


def test_shared_bank_preserves_exact_bounded_sources_and_common_commitment(bank):
    original = bank[2]
    shared = ScheduledCompactBank.from_commitment(original)
    decoded = decode_canonical_bytes(shared.canonical_bytes(), ScheduledCompactBank, maximum_bytes=None)
    assert decoded == shared
    assert decoded.commitment_config().canonical_bytes() == original.canonical_bytes()
    assert decoded.sources == original.sources
    assert decoded.selected_root_ids == original.selected_root_ids
    index = ScheduledSourceIndex.from_shared(reservation=decoded.reservation,
        specification=decoded.specification, provenances=decoded.provenances)
    index.require_roster(decoded.sources, expected_root_ids=index.root_ids)
    for reference in decoded.sources:
        resolved = index.resolve(reference)
        assert identity(resolved) == reference.identity
        assert resolved.root == reference.root
        assert resolved.coordinate.coordinate_id == reference.root.root.coordinate_id
        assert len(reference.canonical_bytes()) < len(decoded.canonical_bytes())//10
    config = ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', shared)
    value = compact_committed(config)
    assert value.configuration == identity(config)
    assert value.shared_context == compact_identity(shared)
    assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
    generic = committed(original)
    assert generic.shared_context == generic.configuration == identity(original)
    assert value.sources == tuple(reference.identity for reference in original.sources)
    assert value.root_ids == tuple(reference.root_id for reference in original.sources)


@pytest.mark.parametrize('field', ('allocation', 'reservation', 'selection', 'specification', 'provenance'))
def test_bounded_source_refuses_changed_shared_parent(bank, field):
    shared = ScheduledCompactBank.from_commitment(bank[2])
    descriptor = shared.sources[0]
    changed = replace(descriptor, **{field: replace(getattr(descriptor, field), object_fingerprint='0'*64)})
    index = ScheduledSourceIndex.from_shared(reservation=shared.reservation,
        specification=shared.specification, provenances=shared.provenances)
    with pytest.raises(ValueError, match='root|scientific parents'):
        index.resolve(changed)


def test_shared_native_contract_names_actual_current_custody(bank):
    shared = ScheduledCompactBank.from_commitment(bank[2])
    index = ScheduledSourceIndex.from_shared(reservation=shared.reservation,
        specification=shared.specification, provenances=shared.provenances)
    source = index.resolve(shared.sources[0])
    configuration, task, operation, sources = compact_native_contract(source, 'prefix', bank=shared)
    assert task == NAMESPACE+'.'+source.root_id+'.prefix'
    assert operation == NAMESPACE+'.prefix-before-continuation.v2'
    assert configuration.object_version == '3.0.0'
    assert source.reference.identity in sources
    assert identity(source.allocation) in sources
    assert identity(source.specification.selection) in sources
    assert len(sources) == 6


def test_same_source_census_does_not_admit_a_different_banks_commitment(bank):
    shared = ScheduledCompactBank.from_commitment(bank[2])
    foreign = replace(shared, bank_id=shared.bank_id+'.foreign')
    current = compact_committed(ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', shared))
    substituted = compact_committed(ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', foreign))
    assert current.sources == substituted.sources
    assert current.root_ids == substituted.root_ids
    assert current.allocation == substituted.allocation
    assert current.configuration != substituted.configuration
    assert current.shared_context == compact_identity(shared)
    assert substituted.shared_context == compact_identity(foreign)
    assert current.shared_context != substituted.shared_context
    require_committed_bank(current, shared)
    with pytest.raises(ValueError, match='current shared bank configuration'):
        require_committed_bank(substituted, shared)


@pytest.mark.parametrize('route,damage', (
    ('generic', 'different-configuration'), ('generic', 'wrong-type'),
    ('compact', 'wrong-type'), ('compact', 'wrong-bank-version'), ('compact', 'wrong-kind'),
))
def test_common_commitment_refuses_substituted_shared_context_owner(bank, route, damage):
    original = bank[2]
    if route == 'generic':
        value = committed(original)
    else:
        shared = ScheduledCompactBank.from_commitment(original)
        value = compact_committed(ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', shared))
    if damage == 'different-configuration':
        changed = replace(value.configuration, object_fingerprint='0'*64
            if value.configuration.object_fingerprint != '0'*64 else '1'*64)
    elif damage == 'wrong-type':
        changed = None
    elif damage == 'wrong-bank-version':
        changed = replace(value.shared_context, object_version='2.0.0')
    else:
        changed = identity(original)
    with pytest.raises(ValueError, match='source/configuration closure|shared context owner'):
        replace(value, shared_context=changed)


@pytest.mark.parametrize('operand', ('allocation', 'selection', 'audit', 'training'))
def test_compact_original_publication_hook_refuses_actual_plane_tamper(bank, operand):
    plane, _, original = bank[:3]
    shared = ScheduledCompactBank.from_commitment(original)
    config = ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', shared)
    inputs = (SimpleNamespace(record=config),)
    authenticate_prior_publications(plane, inputs)
    publication = {'allocation': shared.reservation.publication,
        'selection': shared.specification.publication, 'audit': shared.audit_publication,
        'training': shared.forecast_design.training_publication}[operand]
    path = plane.root.resolve(publication.materialization.relative_path, for_write=False)
    original_bytes = path.read_bytes()
    path.write_bytes(original_bytes+b'\n')
    try:
        with pytest.raises(ArtifactIdentityConflict):
            authenticate_prior_publications(plane, inputs)
    finally:
        path.write_bytes(original_bytes)
    authenticate_prior_publications(plane, inputs)
