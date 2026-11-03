# SPDX-License-Identifier: MPL-2.0
"""Cold acquisition declarations over exposed synthetic metadata, no authority."""

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_acquisition as owner, programme_records
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.obligations import ObligationStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_matrix_scheduled_programme_reduction import declared as declared


def declared_root(programme):
    root, _ = _fixture()
    operands = {programme.identity, programme.bank, programme.reservation, programme.allocation,
        programme.specification, programme.forecast_design, programme.response_selection, programme.criterion,
        *programme.source_census}
    inputs = tuple(DesignInputRecord('design.synthetic.acquisition.'+str(index), pin, pin.object_fingerprint,
        root.design_inputs[0].information_cutoff, DesignInputRole.READINESS_METADATA,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, 'human.synthetic')
        for index, pin in enumerate(sorted(operands, key=lambda value: value.object_id)))
    return replace(root, system=replace(root.system, world=replace(root.system.world, kind=WorldKind.NUMERICAL_SIMULATOR,
        unrepresented_physics=('physical-transfer',))),
        experiment=replace(root.experiment, information_cutoffs=tuple(case.information_cutoff for case in programme.cases),
            obligations=replace(root.experiment.obligations, support=replace(root.experiment.obligations.support,
                information_cutoff_id=programme.cases[0].information_cutoff.cutoff_id))),
        design_inputs=tuple(sorted(inputs, key=lambda value: value.input_id)),
        design_origin=replace(root.design_origin, declared_input_ids=tuple(sorted(value.input_id for value in inputs))),
        development_unit_ids=(), evaluation_unit_ids=programme.group_ids)


def test_scope_cold_constructor_preserves_complete_original_global_root_and_refuses_subset_or_missing_parent(declared):
    programme, _ = declared
    root = declared_root(programme)
    original = root.canonical_bytes()
    scope = owner.ScheduledProgrammeAcquisitionScope('acquisition.'+programme.waves[0].wave_id,
        programme, programme.bank, programme.waves[0], root)
    assert decode_canonical_bytes(scope.canonical_bytes(), owner.ScheduledProgrammeAcquisitionScope,
        maximum_bytes=owner.MAXIMUM_ACQUISITION_BYTES) == scope
    assert root.canonical_bytes() == original
    assert len(scope.global_root.evaluation_unit_ids) == 64 and len(scope.wave.group_ids) == 4
    assert len(scope.global_root.experiment.information_cutoffs) == 576 and len(scope.wave.root_ids) == 36
    with pytest.raises(ValueError, match='global scientific root'):
        replace(scope, global_root=replace(root, evaluation_unit_ids=scope.wave.group_ids))
    with pytest.raises(ValueError, match='global scientific root'):
        replace(scope, global_root=replace(root, experiment=replace(root.experiment,
            information_cutoffs=root.experiment.information_cutoffs[:36])))
    with pytest.raises(ValueError, match='qualified-parent'):
        replace(scope, qualified_parent=object())


def test_local_acquisition_root_has_new_data_obligations_and_preserves_global_scientific_inputs(declared):
    programme, _ = declared
    root = declared_root(programme)
    scope = owner.ScheduledProgrammeAcquisitionScope('acquisition.'+programme.waves[0].wave_id,
        programme, programme.bank, programme.waves[0], root)
    views = tuple(value.view_id for value in root.system.numerical_views)
    local = owner._local_root(scope, views)
    owner._validate_local_root(scope, local, owner._local_root(scope, views))
    assert local.system == root.system and local.experiment != root.experiment
    assert local.evaluation_unit_ids == scope.wave.group_ids and len(local.experiment.information_cutoffs) == 36
    assert len(root.evaluation_unit_ids) == 64 and len(root.experiment.information_cutoffs) == 576
    assert local.experiment.obligations.uncertainty.status is ObligationStatus.NOT_APPLICABLE
    assert local.experiment.obligations.closure.status is ObligationStatus.NOT_APPLICABLE
    assert local.experiment.obligations.support.status is ObligationStatus.REQUIRED
    assert local.experiment.obligations.structural_convergence.status is ObligationStatus.REQUIRED
    assert local.experiment.claims[0].requested_rung is None
    assert {scope.identity, scope.global_root_identity, scope.global_experiment_identity} <= {
        value.object_identity for value in local.design_inputs}
    with pytest.raises(ValueError, match='local data obligations'):
        owner._validate_local_root(scope, replace(local, evaluation_unit_ids=programme.group_ids),
            owner._local_root(scope, views))


def test_new_acquisition_factories_select_new_controls_and_literal_v2_native_configs(monkeypatch):
    import numpy as np
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_acquisition_bindings as bindings

    def blocked(*args, **kwargs):
        pytest.fail('acquisition static discovery entered numerical science')

    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    factories = bindings.operation_factories()
    assert len(factories) == 19 and sum(value.registration.native_effect for value in factories) == 5
    for factory in factories:
        assert factory.registration.selection.capability_key.startswith(owner.NAMESPACE+'.')
        assert factory.runner_factory().manifest == factory.manifest
        if factory.registration.native_effect:
            assert any(port.payload_schema == owner.ScheduledProgrammeAcquisitionAdmission.SCHEMA
                for port in factory.registration.input_ports)
    calibrated, = (value for value in factories if value.manifest.capability_key.endswith('.forecast-calibrated'))
    assert calibrated.registration.qualified_parent_evidence_schema_ids
    assert calibrated.registration.qualified_parent_prior_execution_scope_validator is not None


def test_confirmation_requires_closed_parent_and_development_does_not_alias_fresh_sealed_schema(declared):
    """Synthetic declarations exercise refusal, without claiming a valid bank."""
    programme, _ = declared
    confirmation = replace(programme, mode='E4_CONFIRMATION',
        cases=tuple(replace(case, role='CONFIRMATION') for case in programme.cases))
    with pytest.raises(ValueError, match='qualified-parent'):
        owner.ScheduledProgrammeAcquisitionScope('acquisition.'+confirmation.waves[0].wave_id,
            confirmation, confirmation.bank, confirmation.waves[0], declared_root(confirmation))
    families = sorted({case.family_id for case in programme.cases})
    groups = tuple(sorted({group for family in families for group in sorted({case.independent_group_id
        for case in programme.cases if case.family_id == family})[:8]}))
    cases = tuple(replace(case, role='DEVELOPMENT') for case in programme.cases if case.independent_group_id in groups)
    waves = tuple(programme_records.ScheduledProgrammeWave('synthetic.development.wave.'+str(index).zfill(3),
        groups[index:index+4], tuple(case.root_id for case in cases if case.independent_group_id in groups[index:index+4]))
        for index in range(0, len(groups), 4))
    development = replace(programme, programme_id='synthetic.development', mode='E4_DEVELOPMENT',
        cases=cases, waves=waves, minimum_group_count=32)
    global_root = declared_root(development)
    global_root = replace(global_root, development_unit_ids=groups, evaluation_unit_ids=())
    scope = owner.ScheduledProgrammeAcquisitionScope('acquisition.'+waves[0].wave_id,
        development, development.bank, waves[0], global_root)
    assert len(scope.programme.group_ids) == 32 and len(scope.programme.cases) == 288
    with pytest.raises(ValueError, match='sealed evaluation outcomes'):
        owner._local_root(scope, tuple(view.view_id for view in global_root.system.numerical_views))
