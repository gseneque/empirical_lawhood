# SPDX-License-Identifier: MPL-2.0
"""Actual guarded current ports over literal records; no native acquisition."""

from collections import defaultdict
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_preparation as prep
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3SourcePhase, source_task_id
from empirical_lawhood.infrastructure.execution import _prepare_native_work, prepare_worker_invocation
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.recursive_compiler import RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_e3_response_lifecycle import compiled_response_output
from tests.test_matrix_e3_response_records import case as original_case, forbid_native as forbid_native, error_operands, physical  # noqa: F401
from tests.test_matrix_e3_response_science import store as original_store
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane


@pytest.fixture(scope="module")
def case(original_case):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_science as prefix
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import array_product
    import numpy as np

    result = SimpleNamespace(**vars(original_case))
    native = result.history.native
    receipt = replace(native.receipt, receipt_id="receipt." + native.receipt.attempt_id)
    result.history = replace(result.history, native=replace(native, receipt=receipt))
    arguments = dict(prefix_config=result.config, manifest=result.manifest, specification=result.specification)
    result.numerical = prefix.assess_prefix(result.history, result.native_raw, **arguments)
    result.diagnostic_raw, result.witness = prefix.measure_prefix(result.history, result.numerical, result.native_raw,
        artifact_id="literal.lifecycle.diagnostics", **arguments)
    result.frames = prefix.check_frames(result.history, result.numerical, result.witness, result.native_raw, result.diagnostic_raw, **arguments)
    result.causal_raw, result.causal = prefix.causal_delivery(result.history, result.numerical, result.witness, result.frames,
        result.native_raw, result.diagnostic_raw, artifact_id="literal.lifecycle.causal", **arguments)
    result.physical_raw, result.physical = physical(result, result.causal)
    result.models, result.frozen, result.error = error_operands(result, result.causal)
    result.response_raw, arrays = array_product(result.protocol, {"unentered_branches": np.arange(48, dtype="<i8")}, role="RESPONSES",
        artifact_id="literal.lifecycle.response-arrays", producers=(result.native_config.source.identity, identity(result.selection),
            owner._object(result.physical), identity(result.error), identity(result.profile)), access=Access.EVALUATION_SEALED, visibility=Visibility.PROSPECTIVE)
    result.response = replace(result.response, history=identity(result.history), causal_prefix=identity(result.causal),
        physical_forecast=owner._object(result.physical), error_forecast=identity(result.error), arrays=arrays)
    return result


def literal_publications(plane, config_inputs):
    """Disclosed local composition hook; no real source qualification."""
    assert plane is not None
    assert config_inputs


def literal_root(config, context):
    config.__post_init__()
    assert context.node_id == prep.response_task_id(config.root_id if hasattr(config, "root_id") else config.source.root_id,
        "physical-forecast" if hasattr(config, "root_id") else config.operation)


def declarations():
    return owner.response_declarations(publication_requirement=RegisteredPublicationRequirement(
        "literal.response.actual-original-publications", literal_publications), scientific_root_validator=literal_root)


def inputs(case, operation):
    records = {"specification": case.specification, "protocol": case.protocol, "numerical-profile": case.profile,
        "mathematical-protocol": case.originals.mathematical, "projection": case.originals.projection, "causal": case.causal}
    if operation != "physical-forecast":
        records.update({"manifest": case.manifest, "source": case.config.source, "coordinate": case.source.coordinate,
            "provenance": case.source.provenance, "selection": case.selection, "prefix-config": case.config,
            "history": case.history, "checkpoint": case.history.checkpoint, "physical-config": case.physical_config,
            "physical": case.physical, "error": case.error, "allocation": case.allocation, "models": case.models,
            "frozen": case.frozen, "panels": case.panels,
            "streams": tuple((*case.source.root.streams, *(stream for panel in case.panels
                if panel.role == "INDEPENDENT_FUTURE" for stream in panel.streams)))})
    if operation == "response-score":
        records.update({"native-config": case.native_config, "responses": case.response})
    return records


def store(case):
    values = original_store(case)
    artifact = case.protocol.templates.array_artifact
    publication = next(row for row in case.selection.template_publications if row.logical.logical_artifact_id == artifact.artifact_id)
    port = case.plane.open(VerifiedArtifactInput(publication.logical, publication.materialization), maximum_bytes=None)
    try:
        values[artifact.artifact_id] = port.read()
    finally:
        port.close()
    return values


def prepared(case, operation="responses", *, damage=None, output_scope=None, qualified_outputs=True):
    """Real artifact-plane publications/ports and original stored receipt owner."""
    counter = getattr(case, "response_lifecycle_counter", 0) + 1
    case.response_lifecycle_counter = counter
    label = "case." + str(counter)
    directory = case.plane.root.resolve("lifecycle-planes/" + label, for_write=True)
    directory.parent.mkdir(exist_ok=True)
    plane = _matrix_plane(directory)
    declaration = next(row for row in declarations() if row.capability_key.endswith("." + operation))
    runner, manifest = declaration.runner_factory(), declaration.manifest()
    config = case.physical_config if operation == "physical-forecast" else case.native_config if operation == "responses" else replace(
        case.native_config, operation=operation, config_id=case.native_config.config_id.removesuffix("responses") + operation)
    selected = inputs(case, operation)
    root = case.source.root_id
    common = (case.specification.identity, case.allocation.identity)
    producers = {"causal": (source_task_id(root, ProtectedE3SourcePhase.PROJECT), "product"),
        "history": (source_task_id(root, ProtectedE3SourcePhase.PREFIX), "product"),
        "checkpoint": (source_task_id(root, ProtectedE3SourcePhase.PREFIX), "checkpoint"),
        "physical": (prep.response_task_id(root, "physical-forecast"), "product"),
        "models": (owner.statistical_task_id(*common, "fit"), "product"),
        "frozen": (owner.statistical_task_id(*common, "freeze", mode="model"), "product"),
        "error": (owner.statistical_task_id(*common, "forecast", mode="calibration", root=case.source.root.root), "product"),
        "responses": (prep.response_task_id(root, "responses"), "product")}
    if damage == "error-producer":
        producers["error"] = (prep.response_task_id(root, "responses") + ".foreign-error", "product")
    rows = []
    for name, values in {"automatic": config, **selected}.items():
        for index, record in enumerate(values if type(values) is tuple else (values,)):
            producer = producers.get(name)
            access = Access.DEVELOPMENT_VISIBLE if name in ("models", "frozen", "error") else Access.OUTCOME_BLIND
            visibility = Visibility.DEVELOPMENT_ONLY if access is Access.DEVELOPMENT_VISIBLE else Visibility.PROSPECTIVE
            if name == "numerical-profile":
                access = record.provenance_publication.logical.outcome_access
                visibility = record.provenance_publication.logical.visibility_ceiling
            alias = config.config_id if name == "automatic" else "ordinary.literal.response." + label + "." + name + "." + str(index)
            if name == "streams":
                alias = (case.source.root.stream_identity(record).object_id if record in case.source.root.streams else
                    next(panel.stream_identity(record).object_id for panel in case.panels if record in panel.streams))
            publication = plane.write(ArtifactWriteRequest(alias, "lifecycle/" + label + "." + name + "." + str(index) + ".json",
                record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "literal-response", "lifecycle",
                record.canonical_bytes(), visibility, (), access))
            rows.append((name, record, publication, producer))
    originals = {"causal-arrays": (case.causal.arrays, producers["causal"][0]),
        "templates-arrays": (case.protocol.templates, None), "prefix-arrays": (case.history.arrays, producers["history"][0]),
        "physical-arrays": (case.physical.arrays, producers["physical"][0]),
        "response-arrays": (case.response.arrays, producers["responses"][0])}
    values = store(case)
    for name in owner._arrays(operation):
        original, producer = originals[name]
        artifact = original.array_artifact
        alias = artifact.artifact_id if damage != "array-alias" or name != "prefix-arrays" else artifact.artifact_id + ".foreign"
        publication = plane.write(ArtifactWriteRequest(alias, "lifecycle/" + label + "." + name + ".npz", artifact.payload_schema,
            ArtifactProfile.MATRIX_ARRAY_NPZ, artifact.media_type, "literal-response", "lifecycle",
            values[artifact.artifact_id], original.visibility_ceiling, (), original.outcome_access))
        rows.append((name, original, publication, None if producer is None else (producer, "arrays")))
    if damage == "missing-stream":
        rows.pop(next(index for index, row in enumerate(rows) if row[0] == "streams"))
    if damage == "duplicate-source":
        # The resolved scientific view has no serialized format. A second real
        # current descriptor must still refuse the exact source-operand census.
        record = case.config.source
        pub = plane.write(ArtifactWriteRequest("literal.duplicate-source." + label, "lifecycle/" + label + ".duplicate-source.json",
            record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "literal-response", "lifecycle",
            record.canonical_bytes(), Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
        rows.append(("duplicate-source", record, pub, None))
    by_alias = {pub.logical.logical_artifact_id: (name, record, pub, producer) for name, record, pub, producer in rows}
    groups = defaultdict(list)
    for _, _, pub, producer in rows:
        if producer:
            groups[producer[0]].append(pub)
    receipt_records, dependencies = {}, []
    for index, (task, publications) in enumerate(sorted(groups.items())):
        receipt = CanonicalTaskReceipt("receipt.literal.response." + label + "." + str(index), case.history.native.definition.parent_contact.run_id, task,
            "attempt.literal.response.parent." + str(index), case.source.provenance.observed_git_head, (),
            tuple(sorted((pub.materialization for pub in publications), key=lambda row: row.materialization_id)),
            tuple(sorted((pub.logical for pub in publications), key=lambda row: row.logical_artifact_id)), (), OperationalStatus.SUCCEEDED, ())
        ExternalTaskReceiptStore(plane).commit(receipt, visibility_ceiling=Visibility.DEVELOPMENT_ONLY, outcome_access=Access.DEVELOPMENT_VISIBLE)
        receipt_records[task] = receipt
        dependencies.append(DependencyReceiptBinding(receipt.receipt_id, task, tuple(sorted(row.materialization_id for row in receipt.output_materializations))))
    dependencies.sort(key=lambda row: row.receipt_id)
    verified = tuple(sorted((VerifiedArtifactInput(pub.logical, pub.materialization) for _, _, pub, _ in rows), key=lambda row: row.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL if by_alias[row.artifact_id][3] is None else WorkerInputKind.DEPENDENCY)
        for row in verified)
    ports = plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    automatic = next(pub for name, _, pub, _ in rows if name == "automatic")
    config_id = config.config_id
    reference = CapabilityConfigRef(config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), automatic.logical.logical_artifact_id)
    task_id = prep.response_task_id(root, operation)
    outputs = tuple(sorted((WorkerOutputPort(task_id + "." + out.output_id, out.payload_schema, out.profile, out.media_type,
        "ordinary.literal.current-response." + label + "." + out.output_id) for out in declaration.outputs), key=lambda row: row.output_id))
    context = TaskContext(case.history.native.definition.parent_contact.run_id, task_id, "attempt.literal.response." + label, reference, bindings, ports, outputs,
        manifest.permissions, declaration.outcome_access, owner.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, tuple(dependencies))
    edges, external = [], []
    for binding in bindings:
        name, _, pub, producer = by_alias[binding.artifact_id]
        if producer is None:
            external.append(ExternalInputSpec("input." + binding.artifact_id, binding.artifact_id, pub.logical.content_sha256, binding.payload_schema,
                binding.media_type, binding.size_bytes, binding.visibility_ceiling, binding.outcome_access, None))
        if name == "automatic":
            continue
        input_name = name + "." + str(len(edges)) if name in ("streams", "panels") else name
        if damage == "edge-output" and name == "physical":
            producer = (producer[0], "foreign-output")
        edges.append(ScientificInputSpec("edge." + label + "." + str(len(edges)), input_name, ScientificInputRole.SOURCE,
            None if producer is None else producer[0],
            None if producer is None else producer[0] + "." + producer[1] if qualified_outputs else producer[1],
            "external." + name if producer is None else None, "scientific." + label + "." + str(len(edges)), binding.artifact_id,
            binding.payload_schema, binding.media_type, binding.size_bytes, binding.outcome_access, binding.visibility_ceiling, BarrierKind.NONE))
    compiled = compiled_response_output(declaration.outcome_access)
    # The physical fixture's original profile is blind, so all its actual
    # operands are blind. Response fixtures include fitted development parents.
    access, visibility = ((Access.OUTCOME_BLIND, Visibility.PROSPECTIVE) if operation == "physical-forecast"
        and case.profile.provenance_publication.logical.outcome_access is Access.OUTCOME_BLIND else
        (compiled.outcome_access, compiled.visibility_ceiling)) if output_scope is None else output_scope
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, reference,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.RESPONSE, declaration.outcome_access, owner.BUDGET)
    task = ExecutionTask(task_id, declaration.stage, requirement, manifest.implementation_sha256,
        tuple(sorted(groups)), tuple(sorted(external, key=lambda row: row.input_id)), tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id,
            "lifecycle/" + label + ".output." + port.output_id.rsplit(".", 1)[-1], port.payload_schema, port.profile, port.media_type,
            visibility, tuple(binding.visibility_ceiling for binding in bindings) if output_scope is None else (), access) for port in outputs), (),
        declaration.execution_properties.barrier, 1, ("literal.complete-response-inputs",), scientific_inputs=tuple(sorted(edges, key=lambda row: row.edge_id)))
    task = freeze_worker_configuration(task)
    implementation = RecursiveImplementationBinding(case.source.provenance.package_sources, case.source.provenance.code_sources_sha256,
        case.source.provenance.dependency_lock_sha256, case.source.provenance.observed_git_head, case.source.provenance.observed_checkout_clean)
    plan = ObjectIdentity("plan.literal.response", "empirical-lawhood/runtime/execution-plan", "1.0.0", "e" * 64)
    parent = NativeEffectContact(context.run_id, task_id, context.attempt_id, plan, ObjectIdentity.from_record(task_id, task),
        implementation.observed_git_head, context.input_materialization_ids, context.dependency_receipt_ids)
    contract = prepare_worker_invocation(runner, context, verified, implementation=implementation, execution_plan=plan,
        execution_task=parent.execution_task, execution_task_record=task, native_effect=operation == "responses",
        native_work_preparer=owner.prepare_native_work if operation == "responses" else None)
    return SimpleNamespace(context=context, bound=replace(context, prepared_invocation=contract), contract=contract,
        runner=runner, declaration=declaration, task=task, parent=parent, verified=verified, rows=rows, plane=plane)


def close(selected):
    for port in selected.context.input_ports:
        port.close()


def test_exact_initial_and_bound_work_share_original_closure_without_payload_reads(case):
    selected = prepared(case)
    try:
        first = _prepare_native_work(owner.prepare_native_work, selected.runner, selected.context, selected.parent)
        bound = _prepare_native_work(owner.prepare_native_work, selected.runner, selected.bound, selected.parent)
        assert first == bound == selected.contract.native_work
        definition, = first.definitions
        assert len(definition.sources) == 15 and len(definition.streams) == 8
        assert definition.configuration == owner._object(case.native_config)
        assert first.scientific_unit_ids == (case.source.root.root.independent_group_id,)
        assert case.config.source == case.source.reference
        descriptor, = (row for row in selected.verified if row.logical.payload_schema == case.config.source.SCHEMA)
        assert descriptor.logical.content_sha256 == case.config.source.fingerprint()
        assert all(row.logical.payload_schema != case.source.reservation.allocation.SCHEMA for row in selected.verified)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        close(selected)


def test_nonuse_worker_retains_all48_unentered_slots_and_actual_inherited_lane_without_begin(case):
    selected = prepared(case)
    class NoEffects:
        parent_contact = selected.parent

        def __getattr__(self, name):
            raise AssertionError("nonuse entered native " + name)
    result = selected.runner.execute_with_native_subwork(selected.bound, NoEffects())
    payload = next(row.payload for row in result.outputs if row.output_id.endswith(".product"))
    record = decode_canonical_bytes(payload, owner.ProtectedE3NativeResponse, maximum_bytes=None)
    assert record.disposition == "UNEVALUABLE" and not record.native and len(record.branch_ids) == 48
    assert record.arrays.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
    assert record.arrays.outcome_access is Access.EVALUATION_SEALED
    assert record.arrays.array_artifact.artifact_id == next(port.logical_artifact_id for port in selected.bound.output_ports if port.payload_schema == MATRIX_ARRAY_SCHEMA)


@pytest.mark.parametrize("qualified_outputs", (False, True))
def test_seedless_physical_worker_uses_actual_ports_and_ordinary_output_alias(case, qualified_outputs):
    selected = prepared(case, "physical-forecast", qualified_outputs=qualified_outputs)
    result = selected.runner.execute(selected.bound)
    by_name = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
    record = decode_canonical_bytes(by_name["product"], owner.ProtectedE3PhysicalForecast, maximum_bytes=None)
    assert record.disposition == "UNEVALUABLE" and by_name["arrays"] == case.physical_raw
    assert record.arrays.array_artifact.artifact_id == next(port.logical_artifact_id for port in selected.bound.output_ports if port.payload_schema == MATRIX_ARRAY_SCHEMA)
    assert {row[0] for row in selected.rows}.isdisjoint(("manifest", "streams", "history", "models", "error", "allocation"))


def test_independent_score_worker_publishes_full_score_and_both_paired_targets_in_same_task(case):
    selected = prepared(case, "response-score")
    result = selected.runner.execute(selected.bound)
    by_name = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
    score = decode_canonical_bytes(by_name["score"], owner.ScheduledResponseScore, maximum_bytes=None)
    outcome = decode_canonical_bytes(by_name["outcome"], owner.ProtectedE3PairedOutcome, maximum_bytes=None)
    assert score.disposition == "UNEVALUABLE" and len(score.cells) == 240
    assert len(outcome.views) == 2 and all(view.errors == (None,) * 15 for view in outcome.views)
    assert {port.output_id.rsplit(".", 1)[-1] for port in selected.bound.output_ports} == {"score", "outcome"}


@pytest.mark.parametrize("damage", ("error-producer", "missing-stream", "duplicate-source", "array-alias", "edge-output"))
def test_current_preparation_refuses_foreign_producers_direct_inputs_aliases_and_output_edges(case, damage):
    selected = prepared(case, damage=damage)
    try:
        refusal = ("drops or duplicates an exact scientific operand: source" if damage == "duplicate-source"
            else "produc|undeclared|stream|array|port|preparation")
        with pytest.raises((ValueError, TypeError), match=refusal):
            _prepare_native_work(owner.prepare_native_work, selected.runner, selected.bound, selected.parent)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        close(selected)


@pytest.mark.parametrize("change", ("run", "attempt", "commit", "plan", "task", "inputs", "dependencies"))
def test_bound_work_preserves_every_actual_parent_field(case, change):
    selected = prepared(case)
    changes = {"run": {"run_id": "run.foreign"}, "attempt": {"attempt_id": "attempt.foreign"}, "commit": {"implementation_commit": "a" * 40},
        "plan": {"execution_plan": replace(selected.parent.execution_plan, object_fingerprint="a" * 64)},
        "task": {"execution_task": replace(selected.parent.execution_task, object_fingerprint="a" * 64)},
        "inputs": {"input_materialization_ids": ("materialization.foreign",)}, "dependencies": {"dependency_receipt_ids": ("receipt.foreign",)}}
    try:
        with pytest.raises(ValueError, match="parent"):
            _prepare_native_work(owner.prepare_native_work, selected.runner, selected.bound, replace(selected.parent, **changes[change]))
    finally:
        close(selected)


def test_unsealed_worker_entry_and_installation_without_real_hooks_refuse(case):
    selected = prepared(case)
    with pytest.raises(ValueError, match="native-subwork"):
        selected.runner.execute(selected.bound)
    with pytest.raises(TypeError, match="registered"):
        owner.response_declarations(publication_requirement=None, scientific_root_validator=literal_root)
    with pytest.raises(TypeError, match="module-global"):
        owner.response_declarations(publication_requirement=RegisteredPublicationRequirement("literal", literal_publications),
            scientific_root_validator=lambda *_: True)


def test_decoder_refuses_caller_invented_statistical_task_projection_before_reads(case):
    selected = prepared(case)
    try:
        with pytest.raises(TypeError, match="code-owned"):
            prep.decode_response_inputs(selected.bound, capability=selected.runner.manifest, operation="responses",
                statistical_task_id=lambda *_args, **_kwargs: "task.invented")
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        close(selected)


def test_actual_compiled_sealed_development_lane_cannot_be_falsely_promoted(case):
    selected = prepared(case, output_scope=(Access.EVALUATION_SEALED, Visibility.PROSPECTIVE))
    try:
        with pytest.raises(ValueError, match="compiler-derived"):
            _prepare_native_work(owner.prepare_native_work, selected.runner, selected.bound, selected.parent)
    finally:
        close(selected)


def test_shared_native_begin_validator_accepts_all15_sources_eight_streams_and_original_mixed_boundaries(case):
    from empirical_lawhood.infrastructure.native_subwork_inputs import validate_native_subwork_inputs
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest

    selected = prepared(case)
    try:
        manifests = tuple(decode_artifact_manifest(selected.plane.root.resolve(row.materialization.relative_path + ".manifest.json",
            for_write=False).read_bytes()) for row in selected.verified)
        work = _prepare_native_work(owner.prepare_native_work, selected.runner, selected.bound, selected.parent)
        validate_native_subwork_inputs(selected.plane, work.definitions[0], manifests,
            visibility=Visibility.DEVELOPMENT_ONLY, access=Access.EVALUATION_SEALED, frozen_parent_inputs=manifests)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        close(selected)


def test_seedless_worker_preserves_development_original_profile_publication(case):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import project_protected_e3_response_numerics
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
    from tests.test_matrix_e3_response_records import publication, qualification

    altered = SimpleNamespace(**vars(case))
    pub = publication(case, case.selection, "lifecycle.original.development", access=Access.DEVELOPMENT_VISIBLE,
        visibility=Visibility.DEVELOPMENT_ONLY)
    q = qualification(case.selection, pub, "lifecycle.original.development")
    altered.profile = project_protected_e3_response_numerics(case.protocol, provenance=case.selection, publication=pub, qualification=q)
    altered.physical_config = replace(case.physical_config, numerical_profile=identity(altered.profile))
    selected = prepared(altered, "physical-forecast")
    case.response_lifecycle_counter = altered.response_lifecycle_counter
    result = selected.runner.execute(selected.bound)
    record = decode_canonical_bytes(next(row.payload for row in result.outputs if row.output_id.endswith(".product")), owner.ProtectedE3PhysicalForecast, maximum_bytes=None)
    assert record.arrays.outcome_access is Access.DEVELOPMENT_VISIBLE
    assert record.arrays.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
    assert record.disposition == "UNEVALUABLE"
