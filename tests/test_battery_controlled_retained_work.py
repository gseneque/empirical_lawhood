# SPDX-License-Identifier: MPL-2.0
"""Exposed state/identity adversaries; no authentic custody or native readiness."""
from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import controlled_forecast_config_v1_1 as candidate
from empirical_lawhood.adapters.methods.battery_refined_inquiry import controlled_retained_work as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryAttempt, InquiryAttemptStatus
from empirical_lawhood.kernel.recursive_inquiry_policy import InquiryAttemptWorkBinding
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile
from tests.test_battery_forecast_step_control import selected as selected, config as config
from tests.test_battery_controlled_binding import cold_scope as cold_scope
from tests.test_battery_segmented_graph import stock as stock


def exposed_condition():
    witness = ObjectIdentity('event.exposed-unknown', owner.TaskRecoveryEvent.SCHEMA, '1.0.0', '2' * 64)
    configuration = ObjectIdentity('config.exposed-original', owner.original.SegmentedOperationConfig.SCHEMA, '1.0.0', '1' * 64)
    attempt = InquiryAttempt('attempt.exposed-unknown', configuration, InquiryAttemptStatus.UNCERTAIN_CONTACT,
        witness, (), 'Exposed state conformance only; no real receipt or authority is asserted.')
    binding = InquiryAttemptWorkBinding(attempt.attempt_id, configuration, None, None, None, None, witness)
    return owner.RetainedForecastWorkCondition('condition.exposed-unknown',
        ObjectIdentity('selection.exposed-primary', owner.RetainedForecastRootSelection.SCHEMA, '1.0.0', '3' * 64),
        attempt, binding, '4' * 64)


def exposed_selection():
    records = tuple((role, ObjectIdentity('unresolved.' + role, kind.SCHEMA, kind.VERSION, '1' * 64))
        for role, kind in sorted(owner.PRIMARY_TYPES.items()))
    paths = tuple((role, 'unpublished/' + role + '.json') for role in owner.PATH_ROLES)
    storage = ExternalRootContract('exposed.unpublished-primary', 'Exposed closed metadata only', '/tmp/unpublished-original-primary',
        '/', OperatorStorageProfile.SCHEMA, 0)
    return owner.RetainedForecastRootSelection('selection.exposed-primary', storage, paths, records)


def test_same_physical_request_excludes_cosmetic_config_and_method_labels(selected, config):
    expected = owner.selected_work(config, selected[2])
    renamed = replace(config, config_id='config.cosmetic-other', method=replace(config.method, method_id='method.cosmetic-other'))
    assert owner.selected_work(renamed, replace(selected[2], policy_id='policy.cosmetic-other')) == expected
    shortened = replace(config, method=replace(config.method, maximum_segment_horizon_s=Decimal(30)))
    assert owner.selected_work(shortened, selected[2]) != expected


@pytest.mark.parametrize('new_id', ('config.new-wrapper', 'config.new-seed-label', 'config.new-encoding-label'))
def test_unknown_work_cannot_be_cleared_by_a_new_operational_label(selected, config, new_id):
    with pytest.raises(ValueError, match='UNKNOWN.*recovery'):
        owner.require_no_uncertain_replay(exposed_condition(), config, selected[2],
            ObjectIdentity(new_id, candidate.ControlledForecastConfig.SCHEMA, candidate.ControlledForecastConfig.VERSION, '9' * 64))


@pytest.mark.parametrize('damage', ('completion', 'failed', 'products', 'different-witness', 'different-config', 'invented-wave'))
def test_unknown_condition_cannot_claim_completion_or_new_custody(damage):
    condition = exposed_condition()
    if damage in {'completion', 'failed'}:
        changed = replace(condition.attempt, status=InquiryAttemptStatus.COMPLETED if damage == 'completion' else InquiryAttemptStatus.FAILED)
        with pytest.raises(ValueError):
            replace(condition, attempt=changed)
    elif damage == 'products':
        with pytest.raises(ValueError):
            replace(condition.attempt, products=(condition.attempt.operation,))
    else:
        change = {'different-witness': {'witness': replace(condition.binding.witness, object_fingerprint='8' * 64)},
            'different-config': {'configuration': replace(condition.binding.configuration, object_fingerprint='8' * 64)},
            'invented-wave': {'authored_wave': ObjectIdentity('wave.invented', 'empirical-lawhood/runtime/authored-recursive-wave', '1.0.0', '8' * 64)}}[damage]
        with pytest.raises(ValueError):
            replace(condition, binding=replace(condition.binding, **change))


@pytest.mark.parametrize('damage', ('missing-path', 'extra-path', 'alias', 'traversal', 'missing-record', 'wrong-schema', 'wrong-revision'))
def test_selected_original_primary_metadata_is_closed_typed_and_role_specific(damage):
    selection = exposed_selection()
    if damage == 'missing-path':
        changes = {'paths': selection.paths[:-1]}
    elif damage == 'extra-path':
        changes = {'paths': selection.paths + (('undeclared', 'unpublished/extra.json'),)}
    elif damage == 'alias':
        changes = {'paths': tuple((role, selection.paths[0][1]) for role, _ in selection.paths)}
    elif damage == 'traversal':
        changes = {'paths': tuple((role, '../outside.json' if n == 0 else path) for n, (role, path) in enumerate(selection.paths))}
    elif damage == 'missing-record':
        changes = {'records': selection.records[:-1]}
    else:
        changes = {'records': tuple((role, replace(ref, **({'object_schema': owner.TaskRecoveryEvent.SCHEMA} if damage == 'wrong-schema'
            else {'object_version': '99.0.0'}))) if role == 'contact' else (role, ref) for role, ref in selection.records)}
    with pytest.raises(ValueError):
        replace(selection, **changes)


def test_missing_original_primary_custody_refuses_instead_of_supplying_authority():
    with pytest.raises((ValueError, FileNotFoundError)):
        owner.authenticate_primary(exposed_selection())


def test_current_closed_roles_add_only_the_eight_original_retained_work_roles():
    assert set(candidate.ROLE_TYPES) - set(candidate.ORIGINAL_ROLE_TYPES) == {
        'retained-root-selection', 'retained-condition', 'retained-contact', 'retained-event', 'retained-plan',
        'retained-task', 'retained-config', 'retained-step-evidence'}
    assert len(candidate.ROLE_TYPES) == 35
    assert candidate.HistoricalControlledForecastConfig.VERSION == '1.0.0'
    assert candidate.ControlledForecastConfig.VERSION == '1.1.0'


def test_retained_work_condition_canonical_roundtrip_does_not_make_unknown_known():
    condition = exposed_condition()
    assert decode_canonical_bytes(condition.canonical_bytes(), type(condition), maximum_bytes=None) == condition
    assert condition.binding.work is condition.binding.authored_wave is None


def candidate_arguments(cold_scope):
    """Unpublished closed metadata only; deliberately remains UNKNOWN."""
    from hashlib import sha256
    previous = cold_scope.config
    selection = exposed_selection()
    expected = dict(selection.records)
    witness = expected['event']
    attempt = InquiryAttempt('attempt.exposed-current-held', expected['config'], InquiryAttemptStatus.UNCERTAIN_CONTACT,
        witness, (), 'Exposed UNKNOWN condition; no genuine receipt claimed.')
    condition = owner.RetainedForecastWorkCondition('condition.exposed-current-held', selection.identity, attempt,
        InquiryAttemptWorkBinding(attempt.attempt_id, expected['config'], None, None, expected['plan'], expected['task'], witness), '7' * 64)
    refs = dict(previous.role_bindings)
    refs.update((role, ObjectIdentity('unresolved.' + role, kind.SCHEMA, kind.VERSION, sha256(role.encode()).hexdigest()))
        for role, kind in candidate.ROLE_TYPES.items() if role not in refs)
    refs['retained-root-selection'] = selection.identity
    refs['retained-condition'] = condition.identity
    for role, ref in selection.records:
        if role not in {'assignment-receipt', 'assignment-definition'}:
            refs['retained-step-evidence' if role == 'assignment' else 'retained-' + role] = ref
    root_refs = {ref.object_id: ref for ref in previous.development_root.scientific_operands}
    root_refs.update((ref.object_id, ref) for role, ref in refs.items() if role != 'original-roster')
    root = replace(previous.development_root, scientific_operands=tuple(root_refs[key] for key in sorted(root_refs)))
    return (previous.config_id, previous.index, tuple(sorted(refs.items())), previous.native_request_sha256,
        root, previous.history_requirement, previous.history_connection, selection, condition)


def test_historical_config_bytes_keep_the_explicit_1_0_reader(cold_scope):
    raw = cold_scope.config.canonical_bytes()
    historical = decode_canonical_bytes(raw, candidate.HistoricalControlledForecastConfig, maximum_bytes=None)
    assert historical.canonical_bytes() == raw
    with pytest.raises(ValueError):
        decode_canonical_bytes(raw, candidate.ControlledForecastConfig, maximum_bytes=None)


def test_current_config_refuses_unknown_with_the_shared_recovery_reason(cold_scope):
    with pytest.raises(ValueError, match='UNCERTAIN_CONTACT_RECOVERY_REQUIRED'):
        candidate.ControlledForecastConfig(*candidate_arguments(cold_scope))


def test_root_rechecks_the_shared_predicate_even_for_an_unvalidated_object(cold_scope):
    """Adversarial raw object cannot bypass the constructor's refusal."""
    from dataclasses import fields
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import controlled_operation_bindings_v1_1 as declaration
    raw = object.__new__(candidate.ControlledForecastConfig)
    for field, value in zip(fields(candidate.ControlledForecastConfig), candidate_arguments(cold_scope), strict=True):
        object.__setattr__(raw, field.name, value)
    with pytest.raises(ValueError, match='UNCERTAIN_CONTACT_RECOVERY_REQUIRED'):
        declaration.scientific_root_validator(raw, None)
