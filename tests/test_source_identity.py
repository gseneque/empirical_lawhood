# SPDX-License-Identifier: MPL-2.0
"""Disclosed source diagnostics; no fixture grants scientific authority."""

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from empirical_lawhood.execution.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS, GENERATED_EXTENSION_BUNDLE_AGGREGATE
from empirical_lawhood.methods.mass_balance_starter.extension import EXTENSION as _extension_owner_1
EXECUTABLE_BINDING_CONTRIBUTION = _extension_owner_1.executable
from empirical_lawhood.methods.mass_balance_starter.extension import EXTENSION as _extension_owner_2
EXTENSION_BUNDLE_CONTRIBUTION = _extension_owner_2.discovery
from empirical_lawhood.api import source_identity as owner
from empirical_lawhood.storage import numerical_provenance
from empirical_lawhood.storage.bounded_io import BoundedFileIOError
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.execution.executable_bindings import compose_executable_binding_aggregate
from empirical_lawhood.execution.extension_bundles import compose_extension_bundle_aggregate


def provenance(*, sources=None, **changes):
    rows = sources or (('disclosed.py', sha256(b'disclosed source fixture').hexdigest()),)
    runtime = dict(python='fixture', numpy='fixture', scipy='fixture', system='fixture', machine='fixture', threadpools=[])
    return replace(NumericalProducingProvenance(canonical_json_bytes(
        numerical_provenance.immutable_json(runtime)).decode(), 'a' * 64,
        rows, sha256(canonical_json_bytes(rows)).hexdigest(), 'b' * 40, False), **changes)


@pytest.fixture(scope='module')
def pair():
    """Extend actual metadata with one disclosed unused static method."""
    contribution = EXTENSION_BUNDLE_CONTRIBUTION
    manifest = replace(contribution.capability_manifests[0], capability_key='unrelated.identity-fixture')
    candidate = replace(contribution.candidate_capability_registrations[0], manifest=manifest,
        provider_key='unrelated.identity-fixture')
    profile = replace(contribution.profile_registrations[0],
        registration_id='profile-registration.unrelated.identity-fixture',
        profile_key='unrelated.identity-fixture')
    extra = replace(contribution, contribution_id='method.unrelated.identity-fixture',
        capability_manifests=(manifest,), candidate_capability_registrations=(candidate,),
        profile_registrations=(profile,))
    original = GENERATED_EXTENSION_BUNDLE_AGGREGATE
    extended = compose_extension_bundle_aggregate(EXTENSION_BUNDLE_CONTRIBUTIONS + (extra,))
    def snapshot(discovery, record):
        return owner.SourceIdentityObservation(record, discovery,
            compose_executable_binding_aggregate((EXECUTABLE_BINDING_CONTRIBUTION,), discovery_aggregate=discovery))
    old = snapshot(original, provenance())
    new = snapshot(extended, provenance(sources=old.provenance.package_sources + (
        ('unrelated.py', sha256(b'disclosed unrelated addition').hexdigest()),)))
    selected = EXECUTABLE_BINDING_CONTRIBUTION.bindings[0]
    return old, new, (selected.capability_key, selected.capability_version)


def forbidden(*args, **kwargs):
    pytest.fail('diagnostic compared by entering scientific, native or current source work')


def test_unrelated_addition_explains_whole_source_and_binding_change_without_execution(pair, monkeypatch):
    old, new, key = pair
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory
    monkeypatch.setattr(RecursiveOperationProviderFactory, 'build_provider', forbidden)
    monkeypatch.setattr(numerical_provenance, 'numerical_runtime_observation', forbidden)
    monkeypatch.setattr(numerical_provenance, 'observe_implementation_source', forbidden)
    report = owner.compare_source_identities(old, new, selected_capabilities=(key,))
    assert report['package']['changed_members'] == ({'path': 'unrelated.py', 'status': 'ADDED',
        'before': None, 'after': sha256(b'disclosed unrelated addition').hexdigest()},)
    assert report['dependency_lock']['status'] == 'UNCHANGED'
    assert report['discovery_aggregate']['status'] == report['executable_aggregate']['status'] == 'CHANGED'
    selected = report['selected_capabilities'][0]
    assert selected['manifest']['status'] == selected['executable']['status'] == 'UNCHANGED'
    assert selected['bundle_binding']['status'] == 'CHANGED'
    assert selected['executable']['declarations']['before'] == EXECUTABLE_BINDING_CONTRIBUTION.bindings[0].to_document()
    assert report['consequences']['pending_execution'] == 'OBSERVED_CHANGE_KEEP_ORIGINAL_COMPATIBLE_INSTALLATION'
    assert not report['custody_authenticated'] and not report['execution_admitted']
    assert report['authority'] == 'NONE' and report['qualification'] == 'NOT_ESTABLISHED'
    assert old.provenance.package_sources == provenance().package_sources
    unchanged = owner.compare_source_identities(old, old, selected_capabilities=(key,))
    assert unchanged['consequences']['pending_execution'] == 'ORDINARY_CURRENT_ADMISSION_REQUIRED'
    assert not unchanged['execution_admitted']


def test_missing_history_is_unknown_and_known_absence_is_explicit(pair):
    old, new, key = pair
    missing = owner.SourceIdentityObservation(old.provenance)
    report = owner.compare_source_identities(missing, new, selected_capabilities=(key,))
    assert report['discovery_aggregate']['status'] == report['executable_aggregate']['status'] == 'UNKNOWN'
    assert all(report['selected_capabilities'][0][name]['status'] == 'UNKNOWN'
        for name in ('manifest', 'bundle_binding', 'executable'))
    absent_key = ('absent.identity-fixture', '1.0.0')
    result = owner.compare_source_identities(old, new, selected_capabilities=(absent_key,))
    assert all(result['selected_capabilities'][0][name]['status'] == 'ABSENT'
        for name in ('manifest', 'bundle_binding', 'executable'))
    added = ('unrelated.identity-fixture', '1.0.0')
    forward = owner.compare_source_identities(old, new, selected_capabilities=(added,))
    backward = owner.compare_source_identities(new, old, selected_capabilities=(added,))
    assert forward['selected_capabilities'][0]['manifest']['status'] == 'ADDED'
    assert backward['selected_capabilities'][0]['manifest']['status'] == 'REMOVED'
    assert forward['selected_capabilities'][0]['executable']['status'] == 'ABSENT'


def test_package_changes_lock_runtime_and_commit_keep_exact_observations():
    old = owner.SourceIdentityObservation(provenance(sources=(('changed.py', 'a' * 64), ('removed.py', 'b' * 64))))
    runtime = json.loads(old.provenance.runtime_observation_json)
    runtime.update(numpy='other', optional=None, threadpools=[{'vendor': 'literal', 'threads': 7}])
    new = owner.SourceIdentityObservation(provenance(sources=(('added.py', 'c' * 64), ('changed.py', 'd' * 64)),
        dependency_lock_sha256='e' * 64, runtime_observation_json=canonical_json_bytes(
            numerical_provenance.immutable_json(runtime)).decode(), observed_git_head='f' * 40))
    result = owner.compare_source_identities(old, new)
    assert [row['status'] for row in result['package']['changed_members']] == ['ADDED', 'CHANGED', 'REMOVED']
    assert result['dependency_lock']['status'] == result['source_commit']['status'] == 'CHANGED'
    assert result['runtime']['numpy']['status'] == 'CHANGED'
    assert result['runtime']['threadpools']['after'] == runtime['threadpools']
    assert result['runtime']['optional'] == dict(status='ADDED', before=None, after=None)
    reverse = owner.compare_source_identities(new, old)
    assert reverse['runtime']['optional']['status'] == 'REMOVED'
    unchanged = owner.compare_source_identities(old, old)
    assert unchanged['package']['changed_members'] == ()
    assert not unchanged['execution_admitted']
    assert unchanged['consequences']['pending_execution'] == 'INCOMPLETE_OBSERVATION_ORDINARY_CURRENT_ADMISSION_REQUIRED'


def test_exact_executable_changes_are_reported_and_mismatched_aggregate_refuses(pair):
    old, new, key = pair
    changed = replace(EXECUTABLE_BINDING_CONTRIBUTION, bindings=tuple(replace(binding,
        provider_implementation_sha256='f' * 64) if (binding.capability_key, binding.capability_version) == key
        else binding for binding in EXECUTABLE_BINDING_CONTRIBUTION.bindings))
    executable = compose_executable_binding_aggregate((changed,), discovery_aggregate=old.discovery)
    result = owner.compare_source_identities(old, replace(old, executables=executable), selected_capabilities=(key,))
    assert result['selected_capabilities'][0]['executable']['status'] == 'CHANGED'
    assert result['selected_capabilities'][0]['manifest']['status'] == 'UNCHANGED'
    assert result['consequences']['pending_execution'] == 'OBSERVED_CHANGE_KEEP_ORIGINAL_COMPATIBLE_INSTALLATION'
    with pytest.raises(ValueError, match='substitutes'):
        owner.SourceIdentityObservation(old.provenance, new.discovery, old.executables)


@pytest.mark.parametrize('selection', ((), (('mass', 'bad'),), (('mass', '1.0.0'),) * 2,
    tuple((f'mass.{number}', '1.0.0') for number in range(33))))
def test_selected_census_is_explicit_and_bounded(selection):
    value = owner.SourceIdentityObservation(provenance())
    if not selection:
        assert owner.compare_source_identities(value, value)['selected_capabilities'] == ()
    else:
        with pytest.raises(ValueError):
            owner.compare_source_identities(value, value, selected_capabilities=selection)


def test_bounded_roundtrip_keeps_original_canonical_bytes(pair, tmp_path):
    old, _, _ = pair
    originals = dict(old.members())
    for name, raw in originals.items():
        (tmp_path / name).write_bytes(raw)
    assert owner.read_source_identity(tmp_path) == old
    assert dict(owner.read_source_identity(tmp_path).members()) == originals
    (tmp_path / 'discovery.json').unlink()
    assert owner.read_source_identity(tmp_path).discovery is None
    (tmp_path / 'executables.json').unlink()
    assert owner.read_source_identity(tmp_path) == owner.SourceIdentityObservation(old.provenance)


@pytest.mark.parametrize('damage', ('revision', 'duplicate', 'symlink'))
def test_diagnostic_read_refuses_bad_bytes_before_comparison(tmp_path, damage, monkeypatch):
    raw = provenance().canonical_bytes()
    if damage == 'revision':
        raw = raw.replace(b'"version":"1.0.0"', b'"version":"2.0.0"')
    elif damage == 'duplicate':
        raw = raw.replace(b'{"schema":', b'{"schema":"duplicate","schema":', 1)
    path = tmp_path / 'provenance.json'
    if damage == 'symlink':
        target = tmp_path / 'target.json'
        target.write_bytes(raw)
        path.symlink_to(target)
    else:
        path.write_bytes(raw)
    with pytest.raises((ValueError, OSError, BoundedFileIOError)):
        owner.read_source_identity(tmp_path)
