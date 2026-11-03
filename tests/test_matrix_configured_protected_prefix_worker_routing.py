# SPDX-License-Identifier: MPL-2.0
"""Configured declaration consumers over disclosed literal metadata and arrays.

Reuse the existing no-native prefix fixture, genuine typed metadata constructors,
ordinary byte ports and prepared invocation owner. There are no study inputs,
RNG calls, native operations, qualification, issue or outcome-access grants.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_bindings as declarations
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_science as science
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_workers as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_science as legacy_science
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_source_records import (
    ConfiguredProtectedE3SourceConfig, ProtectedE3SourcePhase as Phase, identity, source_task_id,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from tests.test_matrix_configured_e3_v2 import configured_case
from tests import test_matrix_e3_protected_prefix_workers as literal_workers
from tests.test_matrix_e3_prefix_records import literal_history
from tests.test_matrix_e3_protected_prefix_workers import (
    case as legacy_case, original_case as original_case, forbid_native as forbid_native,  # noqa: F401
)


@pytest.fixture(scope="module")
def configured_prefix_case(legacy_case):  # noqa: F811
    original = legacy_case.originals.inputs
    selected, _ = configured_case()
    coordinates = tuple((role, coordinate_identity(original.nearby if role == "TRANSFER_NEARBY" else
        original.shifted if role == "TRANSFER_SHIFTED" else original.nominal)) for role, _ in selected.role_coordinates)
    specification = ConfiguredProtectedE3Specification("experiment.configured-prefix.literal",
        selected.question, selected.protocol, original.specification.populations, selected.methods,
        replace(selected.assessment, minimum_usable_units=min(8,
            original.specification.population("EVALUATION").expected_units)), selected.calibration_alpha,
        coordinates, evidence_scope="PROSPECTIVE_REQUIRED", calibration_target_view="MAX_PAIRED_VIEWS")
    config = ConfiguredProtectedE3SourceConfig("config." + source_task_id(legacy_case.source.root_id, Phase.PREFIX),
        Phase.PREFIX, specification.identity, identity(legacy_case.manifest), legacy_case.config.source)
    source, configuration, task, operation, closure, _ = records.protected_prefix_native_contract(
        config, legacy_case.manifest, specification=specification)
    raw, arrays, checkpoint, native = literal_history(legacy_case.plane, source,
        configuration=configuration, task=task, operation=operation, sources=closure)
    native = replace(native, receipt=replace(native.receipt,
        receipt_id="receipt." + native.receipt.attempt_id))
    arrays = replace(arrays, array_artifact=replace(arrays.array_artifact,
        artifact_id=literal_workers.array_alias(Phase.PREFIX)))
    history = records.ConfiguredProtectedE3PrefixHistory("history.configured-prefix.literal",
        source=legacy_case.history.source, configuration=configuration, arrays=arrays,
        checkpoint=checkpoint, native=native)
    assert history.validate_source(config, legacy_case.manifest, specification=specification) == source
    arguments = dict(prefix_config=config, manifest=legacy_case.manifest, specification=specification)
    numerical = science.assess_prefix(history, raw, **arguments)
    diagnostic_raw, witness = science.measure_prefix(history, numerical, raw,
        artifact_id=literal_workers.array_alias(Phase.MEASURE), **arguments)
    assessment = science.check_frames(history, numerical, witness, raw, diagnostic_raw, **arguments)
    causal_raw, causal = science.causal_delivery(history, numerical, witness, assessment, raw, diagnostic_raw,
        artifact_id=literal_workers.array_alias(Phase.PROJECT), **arguments)
    return SimpleNamespace(source=source, history=history, config=config, manifest=legacy_case.manifest,
        specification=specification, native_raw=raw, numerical=numerical, witness=witness,
        assessment=assessment, causal=causal, diagnostic_raw=diagnostic_raw, causal_raw=causal_raw)


def prepare_literal_case(case, phase, monkeypatch, tmp_path, *, qualified_outputs=False):
    # Parameterize only the existing test fixture's declaration/record owners.
    # Every production decoder, prepared-context, receipt, source and port guard
    # remains intact and observes the genuine configured typed records above.
    monkeypatch.setattr(literal_workers, "owner", owner)
    monkeypatch.setattr(literal_workers, "declarations", declarations)
    monkeypatch.setattr(literal_workers, "source_task_id", source_task_id)
    return literal_workers.prepared_case(case, phase, directory=tmp_path, qualified_outputs=qualified_outputs)


def close(selected):
    for port in selected.context.input_ports:
        port.close()
    selected.bundle.close()


@pytest.mark.parametrize("phase", tuple(row.phase for row in owner.PURE_PREFIX_PHASES))
def test_configured_declaration_runner_consumes_configured_history_and_keeps_exact_math(
        configured_prefix_case, phase, monkeypatch, tmp_path):
    case = configured_prefix_case
    selected = prepare_literal_case(case, phase, monkeypatch, tmp_path)
    expected = {Phase.NUMERICAL: case.numerical, Phase.MEASURE: case.witness,
        Phase.CHECK: case.assessment, Phase.PROJECT: case.causal}[phase]
    try:
        result = selected.runner.execute(selected.context)
        outputs = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
        product = decode_canonical_bytes(outputs["product"], owner.prefix_worker_phase(phase).product_type,
            maximum_bytes=None)
        assert product.canonical_bytes() == expected.canonical_bytes()
        assert all(row.passed for row in result.checks)
        if phase in (Phase.MEASURE, Phase.PROJECT):
            assert outputs["arrays"] == (case.diagnostic_raw if phase is Phase.MEASURE else case.causal_raw)
        assert not declarations.prefix_pure_declaration(phase).execution_properties.native_effect
    finally:
        close(selected)


def test_old_science_owner_reproduces_actual_type_failure_before_array_read(
        configured_prefix_case, monkeypatch, tmp_path):
    selected = prepare_literal_case(configured_prefix_case, Phase.NUMERICAL, monkeypatch, tmp_path)
    # Reintroduce precisely the old module-routing defect; do not replace any
    # scientific validator or bypass a record/receipt/preparation contract.
    monkeypatch.setattr(owner, "science", legacy_science)
    try:
        with pytest.raises(TypeError, match="exact current scientific records"):
            selected.runner.execute(selected.context)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports
            if port.payload_schema == MATRIX_ARRAY_SCHEMA)
    finally:
        close(selected)


def test_configured_reader_still_rejects_legacy_record_type_before_arrays(configured_prefix_case, legacy_case):  # noqa: F811
    case = configured_prefix_case
    with pytest.raises(TypeError, match="exact current scientific records"):
        science.assess_prefix(legacy_case.history, case.native_raw, prefix_config=case.config,
            manifest=case.manifest, specification=case.specification)


def _configured_native_direct_inputs(case, plane, *, damage=None):
    from hashlib import sha256
    from empirical_lawhood.infrastructure.prepared_native_invocation import (
        NativeInputPublication, prepare_native_invocation,
    )
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
    from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile, WorkerOutputPort
    from empirical_lawhood.runtime.plans import (
        ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec,
    )
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding

    declaration = declarations.prefix_declaration()
    manifest = declaration.manifest()
    config, source = case.config, case.source
    rows = ((config.record_id, config), (case.manifest.record_id, case.manifest),
        (case.specification.specification_id, case.specification),
        (config.source.source_id, config.source),
        (source.coordinate.coordinate_id, source.coordinate),
        (source.provenance.identity.object_id, source.provenance),
        *((source.root.stream_identity(stream).object_id, stream) for stream in source.root.streams))
    assert len(rows) == 10 and len({identity for identity, _ in rows}) == 10
    if damage == 'missing-stream':
        rows = rows[:-1]
    bundle = prepare_native_invocation(plane,
        publications=tuple(NativeInputPublication(identity, record) for identity, record in rows),
        relative_root='disclosed-configured-native-operands',
        visibility=VisibilityCeiling.PROSPECTIVE, access=OutcomeAccess.OUTCOME_BLIND)
    task_id = source_task_id(source.root_id, Phase.PREFIX)
    outputs = tuple(sorted((WorkerOutputPort(task_id + '.' + row.output_id,
        row.payload_schema, row.profile, row.media_type,
        'disclosed.ordinary.' + task_id + '.' + row.output_id)
        for row in declaration.outputs), key=lambda row: row.output_id))
    reference = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config.record_id)
    context = TaskContext('run.disclosed.configured-native-preparation', task_id,
        'attempt.disclosed.configured-native-preparation', reference,
        bundle.input_bindings, bundle.input_ports, outputs, manifest.permissions,
        OutcomeAccess.OUTCOME_BLIND, declarations.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version,
        manifest.kind, reference, manifest.input_schema_ids, manifest.output_schema_ids,
        manifest.permissions, manifest.maximum_evidence_ceiling, OutcomeAccess.OUTCOME_BLIND,
        declarations.BUDGET)
    external = tuple(sorted((ExternalInputSpec('input.' + row.artifact_id, row.artifact_id,
        row.logical.content_sha256, row.logical.payload_schema, row.logical.media_type,
        row.materialization.size_bytes, VisibilityCeiling.PROSPECTIVE,
        OutcomeAccess.OUTCOME_BLIND, None) for row in bundle.verified_inputs),
        key=lambda row: row.input_id))
    task = ExecutionTask(task_id, declaration.stage, requirement, manifest.implementation_sha256,
        (), external, tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id,
            'disclosed-native-output/' + port.output_id, port.payload_schema, port.profile,
            port.media_type, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
            for port in outputs), (), BarrierKind.NONE, 1,
        ('obligation.disclosed.configured-native-direct-operands',), scientific_inputs=())
    provenance = source.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources,
        provenance.code_sources_sha256, provenance.dependency_lock_sha256,
        ('b' * 40 if damage == 'foreign-source' else provenance.observed_git_head),
        provenance.observed_checkout_clean)
    plan = ObjectIdentity('plan.disclosed.configured-native-preparation',
        'empirical-lawhood/runtime/execution-plan', '1.0.0', sha256(b'disclosed metadata plan').hexdigest())
    return SimpleNamespace(bundle=bundle, context=context, task=task,
        implementation=implementation, plan=plan, declaration=declaration,
        runner=declarations.ConfiguredProtectedE3PrefixRunner())


@pytest.mark.parametrize('damage', (None, 'missing-stream', 'foreign-source'))
def test_configured_native_preparer_uses_direct_operands_without_current_result_reader(
        configured_prefix_case, monkeypatch, tmp_path, damage):
    from empirical_lawhood.api import current_result_custody
    from empirical_lawhood.infrastructure import recursive_custody
    from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments
    from tests.test_matrix_e3_protected_prefix_workers import _matrix_plane

    def forbidden(*_args, **_kwargs):
        pytest.fail('native/current-result/execution-products route reached during PURE native preparation')

    monkeypatch.setattr(current_result_custody, '_require_current_task_receipt_outputs', forbidden)
    monkeypatch.setattr(recursive_custody, 'read_execution_products', forbidden)
    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', forbidden)
    plane = _matrix_plane(tmp_path / 'configured-direct-operands')
    selected = _configured_native_direct_inputs(configured_prefix_case, plane, damage=damage)
    declaration = selected.declaration
    assert declaration.execution_properties.native_effect is True
    assert declaration.execution_properties.native_work_preparer is declarations.prepare_native_work
    try:
        contract = prepare_worker_invocation(selected.runner, selected.context,
            selected.bundle.verified_inputs, implementation=selected.implementation,
            execution_plan=selected.plan,
            execution_task=ObjectIdentity.from_record(selected.task.task_id, selected.task),
            execution_task_record=selected.task, native_effect=True,
            native_work_preparer=declaration.execution_properties.native_work_preparer)
        if damage is not None:
            assert contract.native_preparation_error is not None
            assert contract.native_work is None
        else:
            assert contract.native_preparation_error is None
            assert contract.native_effect is True and contract.native_work is not None
            assert len(contract.inputs) == 10
            assert len(contract.native_work.definitions) == len(contract.native_work.rosters) == 1
            definition, = contract.native_work.definitions
            assert definition.configuration == identity(configured_prefix_case.config)
            assert definition.streams == tuple(sorted((
                configured_prefix_case.source.root.stream_identity(stream)
                for stream in configured_prefix_case.source.root.streams), key=lambda row: row.object_id))
            assert contract.native_work.expected_parent == contract.expected_parent_contact
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        selected.bundle.close()
