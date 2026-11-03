# SPDX-License-Identifier: MPL-2.0
"""Exposed E3 continuation contract controls, without execution authority.

Receipt/output literals below are deliberately unexecuted software metadata.
They test full graph and source/alias refusals, never qualify retained science.
"""
from dataclasses import fields, replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_composition as composition
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import (
    lower_protected_matrix_response_error, operation_class, selected_configs, task_id,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import (
    ConfiguredE3RetainedExecution, ConfiguredE3RetainedTaskConfig, require_numerical_source_continuity, source_binding,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import (
    ConfiguredE3ContinuedResponseConfig, original_config,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3FrozenProducts
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, CanonicalTaskReceipt, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, ExecutionPlan, ExecutionTask
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, project_recursive_config_inputs
from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent
from tests.test_matrix_configured_protected_public_preparation import public_case  # noqa: F401


def _pin(label, kind):
    return ObjectIdentity(label, kind.SCHEMA, kind.VERSION, sha256(label.encode()).hexdigest())


def _changed_source(provenance, *, member=None, lock=False):
    sources = dict(provenance.package_sources)
    selected = member or 'adapters/methods/matrix_factor_response/configured_protected_response_records.py'
    sources[selected] = 'd' * 64 if sources.get(selected) != 'd' * 64 else 'e' * 64
    rows = tuple(sorted(sources.items()))
    return replace(provenance, package_sources=rows, code_sources_sha256=sha256(canonical_json_bytes(rows)).hexdigest(),
        observed_git_head='b' * 40, **({'dependency_lock_sha256': 'c' * 64} if lock else {}))


def _unexecuted_receipt(config, declaration, source, run_id):
    """Typed hypothetical controls only; these never enter a result reader."""
    node, manifest = task_id(config), declaration.manifest()
    config_id = getattr(config, 'record_id', getattr(config, 'config_id', None))
    ref = CapabilityConfigRef(config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config_id)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        declaration.evidence_ceiling, declaration.outcome_access, declaration.resources)
    # CAL forecasts retain the development ancestry of their frozen fitted models.
    parents = (VisibilityCeiling.DEVELOPMENT_ONLY,) if operation_class(config) == 'forecast' else ()
    visibility = VisibilityCeiling.DEVELOPMENT_ONLY if parents else declaration.visibility_ceiling
    outputs, logicals, physicals, arrays = [], [], [], []
    for output in declaration.outputs:
        key = 'artifact.' + run_id + '.' + node + '.' + output.output_id
        raw = canonical_json_bytes({'software_only_unexecuted': key})
        digest = sha256(raw).hexdigest()
        relative = 'unexecuted/' + node + '/' + output.output_id + output.filename_suffix
        outputs.append(ArtifactOutputSpec(node + '.' + output.output_id, key, relative, output.payload_schema,
            output.profile, output.media_type, visibility, parents, declaration.outcome_access))
        logicals.append(LogicalArtifactIdentity(key, digest, output.payload_schema, output.profile, output.media_type,
            visibility, parents, declaration.outcome_access,
            ArtifactGenericValidation('validator.unexecuted-software-literal', '1.0.0', 'a' * 64,
                output.payload_schema, output.profile)))
        physicals.append(ArtifactMaterialization(key + '.materialization', key, 'root.unexecuted', relative,
            digest, len(raw), 'none'))
        if output.profile is ArtifactProfile.MATRIX_ARRAY_NPZ:
            arrays.append((node, ArtifactIdentity(key, 'unexecuted-array', output.payload_schema, digest, output.media_type, len(raw))))
    task = ExecutionTask(node, declaration.stage, requirement, manifest.implementation_sha256, (), (),
        tuple(outputs), (), declaration.execution_properties.barrier, 1, ('obligation.' + node,), scientific_inputs=())
    attempt = run_id + '.' + node + '.attempt-001'
    receipt = CanonicalTaskReceipt('receipt.' + attempt, run_id, node, attempt, source.observed_git_head, (),
        tuple(physicals), tuple(logicals), (), OperationalStatus.SUCCEEDED, ())
    return task, receipt, arrays


@pytest.fixture(scope='module')
def continuation_case(public_case):  # noqa: F811
    case = public_case
    original = selected_configs(case.specification, case.allocation, case.selection)
    declarations = {row.capability_key: row for row in composition.operation_declarations()}
    old_source = source_binding(case.manifest.provenances[0])
    current = _changed_source(case.manifest.provenances[0])
    run = 'run.unexecuted-retained-e3.original'
    selected = [config for config in original if operation_class(config) in
        ('prefix', 'numerical', 'measure', 'check', 'project', 'physical-forecast', 'fit', 'model-freeze')]
    features = [config for config in original if operation_class(config) == 'feature']
    selected.extend(features[:-1])
    selected.extend(config for config in original if operation_class(config) == 'forecast' and config.mode == 'calibration')
    selected.sort(key=task_id)
    rows = [_unexecuted_receipt(config, declarations[composition._declaration_key(config)], old_source, run) for config in selected]
    retention = ConfiguredE3RetainedExecution('retention.unexecuted-e3', 'unexecuted/original-e3', run,
        'run.unexecuted-retained-e3.continued',
        ObjectIdentity('package.unexecuted', 'empirical-lawhood/api/experiment-package', '1.0.0', 'a' * 64),
        _pin('plan.unexecuted', ExecutionPlan), _pin('terminal.unexecuted', RunRecoveryTerminalEvent),
        ObjectIdentity('authority.unexecuted', 'empirical-lawhood/planning/study-operation-authority', '1.0.0', 'a' * 64),
        old_source, current, case.specification.identity, case.allocation.identity,
        _pin('freeze.unexecuted', ConfiguredProtectedE3FrozenProducts),
        tuple((task.task_id, ObjectIdentity.from_record(receipt.receipt_id, receipt)) for task, receipt, _ in rows),
        tuple(sorted(row for _, _, arrays in rows for row in arrays)))
    retained = tuple(ConfiguredE3RetainedTaskConfig('config.retained.' + task.task_id, retention.identity, config, task, receipt)
        for config, (task, receipt, _) in zip(selected, rows, strict=True))
    selection = ConfiguredE3ContinuedPreparationSelection(**{
        field.name: getattr(case.selection, field.name) for field in fields(case.selection)
        if field.name not in ('qualifications', 'source_configs')}, qualifications=(), source_configs=(),
        retention=retention, retained_tasks=retained)
    lowered = lower_protected_matrix_response_error(case.specification, case.allocation, selection)
    registrations = {op.node_id: declarations[op.selection.capability_key].registration() for op in lowered.draft.operations}
    decoded = tuple(decode_recursive_config_input(op, registrations[op.node_id]) for op in lowered.draft.operations)
    configs = project_recursive_config_inputs(decoded, registrations)
    return SimpleNamespace(original=case, retention=retention, retained=retained, selection=selection,
        lowered=lowered, configs=configs, registrations=registrations)


def test_continuation_retains_full_graph_original_models_and_separate_effects(continuation_case):
    case = continuation_case
    current = composition.validate_current_configs(case.configs)
    composition.validate_generated_links(case.configs, case.lowered.draft.links)
    assert composition.validate_current_configs(case.configs) is current
    old = case.original.lowered.draft
    assert {op.node_id for op in old.operations} == {op.node_id for op in case.lowered.draft.operations}
    assert current.fit == case.original.fit_config
    queries = sum(len(case.original.allocation.unit_ids(role)) for role in ('calibration', 'evaluation'))
    native = [op for op in case.lowered.draft.operations if case.registrations[op.node_id].native_effect]
    assert len(native) == queries
    assert all(op.selection.capability_key.endswith('.continued-responses') for op in native)
    assert sum(cell.physical_execution_cost for cell in case.lowered.resource_selection.task_cells) == queries
    assert len(case.retained) == len(case.retention.completed_receipts)
    for config in case.retained:
        assert original_config(config).canonical_bytes() == config.original_config.canonical_bytes()
        assert not case.registrations[task_id(config)].native_effect
    cold = decode_canonical_bytes(case.selection.canonical_bytes(), type(case.selection), maximum_bytes=None)
    assert cold == case.selection


def test_continued_response_supplies_exact_direct_producing_provenance(continuation_case):
    """The actual lowered CAL/CONF inputs must satisfy native source custody.

    The original producer stays in the authenticated history/manifest. The
    continued worker needs its own provenance as a direct declared operand.
    """
    case = continuation_case
    records = dict(case.lowered.input_records)
    originals = dict(case.original.lowered.input_records)
    configs = {task_id(config): config for config in selected_configs(
        case.original.specification, case.original.allocation, case.selection)}
    roles = {source.root_id: source.root.root.role.value for source in case.selection.sources}
    seen = set()
    for link in case.lowered.draft.links:
        if link.consumer_input_id != 'provenance':
            continue
        config = configs[link.consumer_node_id]
        if type(config) is not ConfiguredE3ContinuedResponseConfig:
            assert records[link.external_input_id] in case.original.manifest.provenances
            continue
        assert records[link.external_input_id] == case.retention.response_provenance
        assert records[link.external_input_id].identity != case.original.manifest.provenances[0].identity
        seen.add((roles[config.source.root_id], config.operation))
    assert seen == {('CALIBRATION', 'responses'), ('CALIBRATION', 'response-score'),
        ('CONFIRMATION', 'responses'), ('CONFIRMATION', 'response-score')}
    for link in case.original.lowered.draft.links:
        if link.consumer_input_id == 'provenance':
            assert originals[link.external_input_id] in case.original.manifest.provenances


@pytest.fixture(scope='module')
def continued_compiler_inputs(continuation_case):
    """Supply disclosed source metadata to the ordinary complete compiler."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import _source_projection
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import retained_file_versions
    from empirical_lawhood.api.derived_metadata_access import _semantic_access
    from empirical_lawhood.api.recursive_operations import operation_catalog

    case = continuation_case
    original = case.original
    selection = decode_canonical_bytes(case.selection.canonical_bytes(), type(case.selection), maximum_bytes=None)
    lowered = lower_protected_matrix_response_error(original.specification, original.allocation, selection)
    assert lowered.draft.canonical_bytes() == case.lowered.draft.canonical_bytes()
    records = dict(lowered.input_records)
    versions = {key: value.record_version for key, value in original.files.items()}
    versions.update(retained_file_versions(selection))
    source_configs, qualifications = [], []
    operator = ObjectIdentity.from_record(original.specification.specification_id + '.measurement', original.specification.measurement)
    for external in lowered.draft.external_inputs:
        if external.input_id in records:
            versions[external.logical_artifact_id] = records[external.input_id].VERSION
        config, qualification = _semantic_access(external=external, root=lowered.draft.prospective_draft,
            version=versions[external.logical_artifact_id], observation_operator=operator)
        source_configs.append(config)
        qualifications.append(qualification)
    selection = replace(selection, source_configs=tuple(source_configs),
        qualifications=tuple(sorted(qualifications, key=lambda row: row.receipt_id)))
    draft = _source_projection(lowered.draft, selection, versions)
    registrations, registry, codecs = operation_catalog()
    implementation = source_binding(selection.retention.response_provenance)
    options = dict(registrations=registrations, registry=registry, output_codecs=codecs,
        implementation_commit=implementation.observed_git_head,
        implementation_sha256=implementation.fingerprint(), qualifications=selection.qualifications)
    return SimpleNamespace(continuation=case, selection=selection, draft=draft, options=options)


@pytest.fixture
def continued_public_files(continued_compiler_inputs, tmp_path):
    """Bind the disclosed literal outputs through the real public FILE owner."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_bindings import retained_input_id
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import retained_file_versions
    from empirical_lawhood.planning.experiment_inputs import (
        ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding,
    )

    case = continued_compiler_inputs
    original = case.continuation.original
    selection = case.selection
    versions = {key: value.record_version for key, value in original.files.items()}
    versions.update(retained_file_versions(selection))
    payloads = {key: value.path.read_bytes() for key, value in original.files.items()}
    for config in selection.retained_tasks:
        for logical in config.original_receipt.output_logical_artifacts:
            payloads[retained_input_id(logical)] = canonical_json_bytes(
                {'software_only_unexecuted': logical.logical_artifact_id})
    files = []
    for _, artifact in case.continuation.lowered.file_identities:
        raw = payloads[artifact.artifact_id]
        assert (sha256(raw).hexdigest(), len(raw)) == (artifact.sha256, artifact.size_bytes)
        path = tmp_path / sha256(artifact.artifact_id.encode()).hexdigest()
        path.write_bytes(raw)
        files.append(ExperimentFileInputBinding(artifact.artifact_id, artifact,
            versions[artifact.artifact_id], path.name, len(raw)))
    raw = selection.canonical_bytes()
    member = tmp_path / 'protected-selection.json'
    member.write_bytes(raw)
    bindings = (ExperimentInputBinding('protected-selection',
        ObjectIdentity.from_record(selection.selection_id, selection), member.name, len(raw)),)
    selector = ExperimentFileInputSelection('selection.unexecuted-retained-e3.files',
        'matrix.response-error.configured-protected-v2', bindings,
        tuple(sorted(files, key=lambda row: row.key)))
    path = tmp_path / 'sources.json'
    path.write_bytes(selector.canonical_bytes())
    return SimpleNamespace(case=case, selector=selector, path=path)


def _prepare_continued_public_files(selected):
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    specification = selected.case.continuation.original.specification
    bound = load_experiment_inputs(specification, selected.path)
    source = source_binding(selected.case.selection.retention.response_provenance)
    return prepare_experiment(specification, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=ExecutionSelection(workers=4,
            environment_id='environment.unexecuted-retained-e3.files',
            source_snapshot=ObjectIdentity.from_record('recursive-member.implementation', source),
            output_root=str(selected.path.parent)))


def test_continuation_public_files_prepare_complete_retained_graph(continued_public_files):
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation as preparation_owner
    from empirical_lawhood.api.experiment_preparation import _validate_prepared_input_files

    selected = continued_public_files
    case = selected.case.continuation
    result = _prepare_continued_public_files(selected)
    assert result.allocation == case.original.allocation
    assert result.draft == selected.case.draft
    assert tuple(row.code for row in result.dependencies) == (preparation_owner.RESOURCE_BINDING_DEPENDENCY,)
    assert len(result.input_files) == len(case.lowered.file_identities)
    assert {value.identity for _, value in result.input_files} == {
        artifact for _, artifact in case.lowered.file_identities}
    assert len({(row.identity.payload_schema, row.record_version, row.identity.media_type)
        for row in selected.selector.files}) == 15
    queries = sum(len(case.original.allocation.unit_ids(role)) for role in ('calibration', 'evaluation'))
    assert result.census.native_effect_count == queries
    assert dict(result.census.output_counts)['retained-task-copies'] == len(case.retained)
    _validate_prepared_input_files(result)
    cold = decode_canonical_bytes(selected.case.selection.canonical_bytes(),
        type(selected.case.selection), maximum_bytes=None)
    preparation_owner.validate_protected_e3_experiment_instance(specification=case.original.specification,
        allocation=result.allocation, draft=result.draft, source_records=((cold.selection_id, cold),))


@pytest.mark.parametrize('mutation', ('revision', 'media', 'digest', 'missing-file', 'omitted-binding'))
def test_continuation_public_files_keep_exact_contract_refusals(continued_public_files, mutation):
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs

    selected = continued_public_files
    # This retained feature output is revision 3, not the default revision 1.
    binding = next(row for row in selected.selector.files if row.key.startswith('input.retained-e3.')
        and row.record_version == '3.0.0')
    if mutation == 'missing-file':
        (selected.path.parent / binding.relative_path).unlink()
        error, match = FileNotFoundError, None
    elif mutation == 'omitted-binding':
        changed = replace(selected.selector, files=tuple(row for row in selected.selector.files if row != binding))
        selected.path.write_bytes(changed.canonical_bytes())
        result = _prepare_continued_public_files(selected)
        assert result.draft is None and result.input_files == ()
        assert any(row.code == 'matrix.e3.file.' + binding.key for row in result.dependencies)
        return
    else:
        if mutation == 'revision':
            changed_binding = replace(binding, record_version='1.0.0')
            match = 'exact declared schema/revision'
        else:
            identity = replace(binding.identity, **({'media_type': 'application/octet-stream'}
                if mutation == 'media' else {'sha256': '0' * 64}))
            changed_binding = replace(binding, identity=identity)
            match = ('exact declared and installed storage codec/revision' if mutation == 'media'
                else 'selected exact bytes or size')
        changed = replace(selected.selector, files=tuple(changed_binding if row == binding else row
            for row in selected.selector.files))
        selected.path.write_bytes(changed.canonical_bytes())
        error = ValueError
    with pytest.raises(error, match=match):
        load_experiment_inputs(selected.case.continuation.original.specification, selected.path)


def test_continuation_complete_compiler_accepts_original_custody_operands(continued_compiler_inputs):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_bindings import retained_input_id
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

    case = continued_compiler_inputs
    compiled = compile_recursive_wave(draft=case.draft, **case.options,
        known_design_inputs=case.draft.prospective_draft.design_inputs)
    assert compiled.candidate_report.candidate is not None, tuple(sorted({
        (row.code, row.message) for row in compiled.candidate_report.diagnostics}))
    original_operations = case.continuation.original.lowered.draft.operations
    assert len(compiled.candidate_report.candidate.scientific_graph.nodes) == len(original_operations)
    assert {row.node_id for row in compiled.operations} == {row.node_id for row in original_operations}
    forecasts = tuple(row for row in case.continuation.retained if operation_class(row) == 'forecast')
    assert forecasts
    external = {row.logical_artifact_id: row for row in case.draft.external_inputs}
    for retained in forecasts:
        for logical in retained.original_receipt.output_logical_artifacts:
            copied = external[retained_input_id(logical)]
            assert copied.scientific_role == 'HISTORY'
            assert copied.expected_content_sha256 == logical.content_sha256
            assert (copied.outcome_access, copied.visibility_ceiling) == (
                OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY)


@pytest.mark.parametrize('operand', ('original_task', 'original_receipt', 'public_source', 'numerical_profile', 'continuation'))
def test_continuation_compiler_refuses_omitted_original_operands(continued_compiler_inputs, operand):
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

    case = continued_compiler_inputs
    if operand in ('original_task', 'original_receipt'):
        fingerprint = getattr(case.continuation.retained[0], operand).fingerprint()
    elif operand == 'continuation':
        fingerprint = case.continuation.retention.fingerprint()
    else:
        config = next(row.original_config for row in case.continuation.retained if hasattr(row.original_config, operand))
        fingerprint = getattr(config, operand).object_fingerprint
    root = case.draft.prospective_draft
    inputs = tuple(row for row in root.design_inputs if row.object_identity.object_fingerprint != fingerprint)
    assert len(inputs) < len(root.design_inputs)
    root = replace(root, design_inputs=inputs,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(row.input_id for row in inputs)))
    with pytest.raises(ValueError, match='scientific operands differ'):
        compile_recursive_wave(draft=replace(case.draft, prospective_draft=root), **case.options,
            known_design_inputs=inputs)


@pytest.mark.parametrize('phase', ('prefix', 'physical-forecast', 'fit', 'model-freeze'))
def test_continuation_refuses_reacquisition_or_refit_in_full_graph(continuation_case, phase):
    case = continuation_case
    row = next(row for row in case.configs if type(row.record) is ConfiguredE3RetainedTaskConfig and operation_class(row.record) == phase)
    changed = replace(row, record=row.record.original_config, record_type=type(row.record.original_config))
    with pytest.raises(ValueError, match='must retain'):
        composition.validate_current_configs(tuple(changed if item is row else item for item in case.configs))


def test_continuation_refuses_missing_receipts_and_bypassed_freezes(continuation_case):
    case = continuation_case
    with pytest.raises(ValueError, match='every original completed task'):
        replace(case.selection, retained_tasks=case.retained[:-1])
    edge = next(edge for edge in case.lowered.draft.links if edge.consumer_input_id == 'frozen'
        and edge.consumer_node_id.endswith('.responses'))
    changed = replace(edge, producer_node_id='matrix-e3-configured-protected.foreign-freeze')
    with pytest.raises(ValueError, match='producer'):
        composition.validate_generated_links(case.configs, tuple(changed if row is edge else row for row in case.lowered.draft.links))
    config = next(row.record for row in case.configs if type(row.record) is ConfiguredE3ContinuedResponseConfig)
    assert config.continuation == case.retention.identity


@pytest.mark.parametrize('member,lock', (
    ('adapters/methods/matrix_scheduled_history/response_native.py', False),
    ('adapters/methods/matrix_factor_response/configured_protected_methods.py', False),
    (None, True),
))
def test_continuation_refuses_changed_numerical_owners_or_lock(continuation_case, member, lock):
    retention = continuation_case.retention
    current = _changed_source(retention.response_provenance, member=member, lock=lock)
    with pytest.raises(ValueError, match='numerical owner|dependency lock'):
        require_numerical_source_continuity(retention.original_source, source_binding(current))


@pytest.mark.parametrize('revoke_at', (None, 1, 2))
def test_pure_retention_projection_refreshes_access_without_rehashing(continuation_case, monkeypatch, revoke_at):
    from empirical_lawhood.api import configured_e3_retained_custody as owner

    case, expected = continuation_case, continuation_case.retention
    # Reuse the disclosed typed task/config/receipt fixture. The outer issued
    # selectors are supplied pins here; this tests projection, not file custody.
    values = {field.name: None for field in fields(owner.RetainedE3Custody)}
    pins = {}
    for name, field, pin in (
            ('package', 'package_id', expected.original_package),
            ('plan', 'execution_plan_id', expected.original_plan),
            ('terminal', 'terminal_event_id', expected.original_terminal),
            ('reveal', 'authority_id', expected.original_reveal_authority),
            ('model_freeze', 'record_id', expected.model_freeze)):
        record = SimpleNamespace(**{field: pin.object_id})
        values[name] = record
        pins[id(record)] = pin
    original_pin = owner._pin
    def supplied_pin(record, field='record_id'):
        if id(record) in pins:
            assert getattr(record, field) == pins[id(record)].object_id
            return pins[id(record)]
        return original_pin(record, field)
    monkeypatch.setattr(owner, '_pin', supplied_pin)
    values['package'].run_plan_id = expected.original_run_id
    values['plan'].tasks = tuple(row.original_task for row in case.retained)
    accesses = []
    def access():
        accesses.append(1)
        if len(accesses) == revoke_at:
            raise PermissionError('disclosed current access revoked')
    values.update(directory=expected.original_authoring_directory,
        selection=case.original.selection, specification=case.original.specification,
        allocation=case.original.allocation, arrays=expected.retained_arrays,
        receipts={row.original_task.task_id: row.original_receipt for row in case.retained},
        configurations={row.original_task.task_id: row.original_config for row in case.retained},
        require_access=access, require_current=lambda: pytest.fail('pure projection rehashed the whole read'))
    custody = owner.RetainedE3Custody(**values)
    def project():
        return custody.continuation(record_id=expected.record_id,
            continued_run_id=expected.continued_run_id, response_provenance=expected.response_provenance)
    if revoke_at is not None:
        with pytest.raises(PermissionError, match='revoked'):
            project()
    else:
        actual, tasks = project()
        assert actual.canonical_bytes() == expected.canonical_bytes()
        assert tasks == case.retained
        assert len(accesses) == 2
