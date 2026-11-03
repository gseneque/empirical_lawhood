# SPDX-License-Identifier: MPL-2.0
"""Sampling follow-on composition through existing issued and retained custody.

Current grants are replayed on each invocation. Original scientific products use
the existing original reveal/receipt-closure readers; independent sealed source
gates use the existing prior-execution reader. Nothing here signs, issues,
executes, retries or manufactures scientific evidence.
"""

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_sampling_assessment import MatrixSamplingScope
from empirical_lawhood.adapters.methods.matrix_sampling_bindings import (
    MatrixE3SamplingInputs, MatrixE4SamplingInputs, MatrixSamplingConfig, MatrixSamplingInvocationCustody,
    MatrixSamplingWorker, _reference, sampling_task_id,
)
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody, CurrentIssuedTaskCustodySupplier
from .recursive_qualified_parents import (
    MAX_PARENT_BYTES, _ParentReadScope, _actual_package, _output_payload,
    _replay_parent_authority, _semantic_writer, _verify_receipt_closure,
)
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.scientific_source_qualification import (
    ScientificSourceGateEvidence, ScientificSourceQualificationResult, ScientificSourceQualificationSpec,
)


def _read_input(writer, manifest, kind):
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(manifest.materialization.relative_path, for_write=False),
        maximum_bytes=manifest.materialization.size_bytes)
    record = decode_canonical_bytes(raw, kind, maximum_bytes=manifest.materialization.size_bytes)
    if (record.canonical_bytes() != raw or len(raw) != manifest.materialization.size_bytes
            or sha256(raw).hexdigest() != manifest.logical.content_sha256
            or sha256(raw).hexdigest() != manifest.materialization.physical_sha256):
        raise PermissionError("sampling follow-on changes actual canonical input custody")
    return record


def _original_product(writer, original, expected, codecs, read_scope=None, *, scope_validator=None):
    """Compose original issue/reveal, plan, complete receipt closure and read."""

    package, issued, reveal, receipt, logical, prefixes = _original_product_metadata(writer, original, expected)
    binding = original.prior_execution
    if read_scope is None:
        # Only immutable plan/control reuse needs a finite snapshot. Full
        # receipt and payload verification below uses the original writer.
        from .current_result_custody import CurrentResultPlanReader
        with writer.verification_scope() as plan_writer:
            plan = CurrentResultPlanReader(plan_writer).authenticate(package=package, issued=issued, receipt=receipt,
                logical=logical, capability_prefixes=prefixes)
    else:
        plan = read_scope.plan_reader.authenticate(package=package, issued=issued, receipt=receipt,
            logical=logical, capability_prefixes=prefixes)
    if ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan:
        raise PermissionError("sampling original result changes its actual original plan")
    semantic = _semantic_writer(package, plan, writer, codecs)
    if read_scope is None:
        from .recursive_qualified_parents import _collect_receipt_closure
        closure = _collect_receipt_closure(package, plan, semantic, reveal, prefixes)
    else:
        closure = read_scope.receipt_closure(package, plan, semantic, reveal, prefixes)
    from .configured_e3_retained_read import continued_plan_read
    with continued_plan_read(writer=semantic, plan=plan, receipts=closure.by_task):
        by_task = _verify_receipt_closure(semantic, closure)
        if by_task.get(binding.task_id) != receipt:
            raise PermissionError("sampling original result substitutes a spent or noncurrent attempt")
        if scope_validator is not None:
            if not callable(scope_validator):
                raise TypeError("original scientific producer scope requires its installed callable")
            verdict = scope_validator(binding=binding, package=package, execution_plan=plan,
                receipt=receipt, logical=logical, writer=semantic, read_scope=read_scope)
            if verdict is not None:
                raise PermissionError("original producer scope must refuse by raising and return no authority token")
        return _output_payload(semantic, receipt, logical, MAX_PARENT_BYTES)


def _original_product_metadata(writer, original, expected, *, _control_reader=None, _issued_reader=None):
    """Replay each exact package, live grant and producing receipt afresh."""

    from .retained_e3_evidence import current_e3_evidence, recorded_product_kinds
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    active = current_e3_evidence(writer)
    if (active is not None and not scientific_reconstruction_enabled()
            and (expected.object_schema, expected.object_version) in {
                (kind.SCHEMA, kind.VERSION) for kind in recorded_product_kinds()}):
        return active.product_metadata(original, expected)

    original.__post_init__()
    binding = original.prior_execution
    if binding.record != expected:
        raise PermissionError("sampling original result substitutes its exact retained scientific product")
    package = _actual_package(writer, binding.run_id, control_reader=_control_reader)
    issued, reveal = _replay_parent_authority(original, package, writer, _issued_reader=_issued_reader)
    if ObjectIdentity.from_record(package.package_id, package) != binding.package:
        raise PermissionError("sampling original result substitutes its actual issued package")
    receipt = ExternalTaskReceiptStore(writer).read_by_receipt_id(binding.run_id, binding.task_id, binding.receipt.object_id)
    if (receipt is None or ObjectIdentity.from_record(receipt.receipt_id, receipt) != binding.receipt
            or receipt.operational_status is not OperationalStatus.SUCCEEDED):
        raise PermissionError("sampling original result lacks its actual successful original producing receipt")
    logicals = tuple(value for value in receipt.output_logical_artifacts if value.logical_artifact_id == binding.logical_artifact_id)
    if len(logicals) != 1 or (logicals[0].payload_schema, logicals[0].content_sha256) != (expected.object_schema, expected.object_fingerprint):
        raise PermissionError("sampling original result substitutes its exact receipt-bound output")
    logical, = logicals
    prefixes = tuple(sorted(value.capability_key for value in package.registry.capabilities))
    return package, issued, reveal, receipt, logical, prefixes


def _original_products(writer, originals, codecs, *, scope_validator=None):
    """Read one actual original run's bounded products with one payload pass.

    Control/receipt traversal stays outside the growing payload snapshot. Plan
    reuse has a separate small lifetime; fresh grants and complete metadata are
    replayed after all products, while the bulk byte snapshot is still active.
    No custody or authorization survives this call.
    """
    from .recursive_qualified_parents import (
        MAX_PRIOR_EXECUTIONS, _collect_receipt_closure, _consume_receipt_closure,
        _require_parent_authorities_current,
    )


    if (type(originals) is not tuple or not originals or len(originals) > MAX_PRIOR_EXECUTIONS
            or any(type(row) is not tuple or len(row) != 2 for row in originals)):
        raise ValueError("original product batch requires its owning bounded exact locator/pin census")
    if scope_validator is not None and not callable(scope_validator):
        raise TypeError("original scientific producer scope requires its installed callable")
    for original, expected in originals:
        original.__post_init__()
        expected.__post_init__()
    if len({expected for _, expected in originals}) != len(originals):
        raise PermissionError("original product batch aliases records or combines different actual runs or grants")
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    from .retained_e3_evidence import recorded_product_kinds
    if (not scientific_reconstruction_enabled() and len(originals) == 4
            and all((pin.object_schema, pin.object_version) in {
                (kind.SCHEMA, kind.VERSION) for kind in recorded_product_kinds()} for _, pin in originals)):
        from .recorded_e3_products import read_recorded_original_products
        return read_recorded_original_products(writer, originals, codecs, scope_validator=scope_validator)
    keys = {(row.prior_execution.run_id, row.prior_execution.package, row.prior_execution.execution_plan,
        row.issued_study, row.execution_authority, row.reveal_authority) for row, _ in originals}
    if len(keys) != 1:
        from .configured_e3_imported_products import read_imported_e3_products
        return read_imported_e3_products(writer, originals, codecs, scope_validator=scope_validator)
    with writer.read_context() as plan_writer:
        read_scope = _ParentReadScope(plan_writer)
        entries = tuple(_original_product_metadata(plan_writer, original, expected, _control_reader=read_scope.plan_reader) for original, expected in originals)
        package, issued, reveal, receipt, logical, prefixes = entries[0]
        if any((value[0], value[1], value[2], value[5]) != (package, issued, reveal, prefixes) for value in entries[1:]):
            raise PermissionError("original product batch changes its actual package, authority or capability census")
        plans = tuple(read_scope.plan_reader.authenticate(package=value[0], issued=value[1], receipt=value[3],
            logical=value[4], capability_prefixes=value[5]) for value in entries)
        plan = plans[0]
        if any(value is not plan for value in plans) or any(
                ObjectIdentity.from_record(value.execution_plan_id, value) != original.prior_execution.execution_plan
                for (original, _), value in zip(originals, plans, strict=True)):
            raise PermissionError("original product batch changes its actual original plan")
        semantic = _semantic_writer(package, plan, writer, codecs)
        closure = _collect_receipt_closure(package, plan, semantic, reveal, prefixes)

        def consume(payload_writer, by_task):
            raw_products = []
            for (original, _), value in zip(originals, entries, strict=True):
                _, _, _, producing, output, _ = value
                if by_task.get(original.prior_execution.task_id) != producing:
                    raise PermissionError("sampling original result substitutes a spent or noncurrent attempt")
                if scope_validator is not None:
                    verdict = scope_validator(binding=original.prior_execution, package=package,
                        execution_plan=plan, receipt=producing, logical=output, writer=payload_writer,
                        read_scope=read_scope)
                    if verdict is not None:
                        raise PermissionError("original producer scope must refuse by raising and return no authority token")
                raw_products.append(_output_payload(payload_writer, producing, output, MAX_PARENT_BYTES))
            # This is a metadata-only second traversal, not a second retained
            # payload hash pass. It catches changed/missing terminal, receipt,
            # input and manifest joins while the bulk mutation guard stays live.
            if _collect_receipt_closure(package, plan, semantic, reveal, prefixes) != closure:
                raise PermissionError("original product batch complete receipt closure changed during the read")
            for (original, expected), before in zip(originals, entries, strict=True):
                current = _original_product_metadata(plan_writer, original, expected, _control_reader=read_scope.plan_reader)
                if current != before:
                    raise PermissionError("original product batch current grants or producing custody changed")
                current_plan = read_scope.plan_reader.authenticate(package=current[0], issued=current[1],
                    receipt=current[3], logical=current[4], capability_prefixes=current[5])
                if current_plan is not plan:
                    raise PermissionError("original product batch actual plan changed during the read")
            return tuple(raw_products)

        from .configured_e3_retained_read import continued_plan_read
        with continued_plan_read(writer=semantic, plan=plan, receipts=closure.by_task):
            result = _consume_receipt_closure(semantic, closure, consume)

    # Final physical checks can take time. Reload and sample the actual grants
    # after both bounded read contexts close, immediately before returning.
    _require_parent_authorities_current(tuple((original, entry[0])
        for (original, _), entry in zip(originals, entries, strict=True)), writer)
    return result


def _selected_control(owner, task, manifest, kind):
    declared = tuple(value for value in task.external_inputs
        if value.logical_artifact_id == manifest.logical.logical_artifact_id)
    if (len(declared) != 1 or type(declared[0].expected_outcome_access) is not OutcomeAccess
            or type(declared[0].expected_visibility_ceiling) is not VisibilityCeiling):
        raise PermissionError("sampling control lacks its exact actual issued input access and visibility")
    spec, = declared
    return owner.control_record(manifest, kind, manifest.materialization.size_bytes,
        expected_outcome_access=spec.expected_outcome_access,
        expected_visibility_ceiling=spec.expected_visibility_ceiling)


def _sampling_evidence(writer, request, evidence, custody, codecs, read_scope):
    from .matrix_source_runtime import authenticate_matrix_source_qualification

    custody.__post_init__()
    if custody.evidence != evidence.identity:
        raise PermissionError("sampling evidence custody substitutes its actual source qualification")
    # Applicability to the named premise is replayed independently by the pure
    # scientific consumer. This owner authenticates the original complete source
    # pipeline and every independently produced gate before any protected use.
    executions = tuple(sorted((custody.pipeline_execution, custody.qualification_execution,
        *custody.gate_executions), key=lambda value: value.record.object_id))
    authenticate_matrix_source_qualification(writer=writer,
        specification=evidence.qualification_specification, result=evidence.qualification_result,
        pipeline=custody.pipeline, executions=executions, publications=custody.publications,
        codecs=codecs, read_scope=read_scope)


def prepare_matrix_sampling(supplier, context, runner):
    """Fresh genuine grants and original-source custody before protected reads."""
    if type(runner) is not MatrixSamplingWorker or runner.prepared_scope is not None:
        raise PermissionError("sampling follow-on requires its unprepared installed worker")
    custody_owner = getattr(supplier, "custody", None)
    if custody_owner is None:
        custody_owner = CurrentIssuedTaskCustody(writer=supplier.writer, reveal_authority_id=supplier.reveal_authority_id)
    elif (type(custody_owner) is not CurrentIssuedTaskCustody or custody_owner.writer is not supplier.writer
            or custody_owner.reveal_authority_id != supplier.reveal_authority_id):
        raise TypeError("shared Matrix custody changes its exact writer or reveal selection")
    package, plan, task = custody_owner.current_task(context, runner)
    _, controls = custody_owner.task_inputs(context, task)
    config = _selected_control(custody_owner, task, controls[context.config.artifact_id], MatrixSamplingConfig)
    if (config.programme != runner.programme or context.task_id != sampling_task_id(config.programme, config.inputs, config.custody)
            or context.dependency_receipts):
        raise PermissionError("sampling follow-on changes its exact retained-input lifecycle")
    by_reference = {(manifest.logical.payload_schema, manifest.logical.content_sha256): manifest for manifest in controls.values()}
    expected = {(value.object_schema, value.object_fingerprint) for value in (config.inputs, config.custody)}
    expected.add((config.SCHEMA, config.fingerprint()))
    if set(by_reference) != expected or len(controls) != 3:
        raise PermissionError("sampling follow-on omits or substitutes its exact persisted input census")
    input_kind = MatrixE3SamplingInputs if config.programme == "E3" else MatrixE4SamplingInputs
    inputs_manifest = by_reference[(config.inputs.object_schema, config.inputs.object_fingerprint)]
    if (inputs_manifest.logical.outcome_access, inputs_manifest.logical.visibility_ceiling) not in (
            (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE),
            (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)):
        raise PermissionError("sampling follow-on substitutes protected original outcomes with exposed development inputs")
    inputs = _read_input(supplier.writer, inputs_manifest, input_kind)
    custody = _selected_control(custody_owner, task,
        by_reference[(config.custody.object_schema, config.custody.object_fingerprint)], MatrixSamplingInvocationCustody)
    if _reference(inputs) != config.inputs or _reference(custody) != config.custody or inputs.unit_ids != config.unit_ids:
        raise PermissionError("sampling follow-on changes its actual original science or complete units")
    if tuple(value.record for value in custody.original_products) != inputs.original_products:
        raise PermissionError("sampling follow-on omits actual original scientific product custody")
    from empirical_lawhood.api.recursive_operations import operation_catalog
    _, _, installed = operation_catalog()
    codecs = {**installed, ScientificSourceGateEvidence.SCHEMA: ScientificSourceGateEvidence,
        ScientificSourceQualificationResult.SCHEMA: ScientificSourceQualificationResult,
        ScientificSourceQualificationSpec.SCHEMA: ScientificSourceQualificationSpec, MatrixSamplingScope.SCHEMA: MatrixSamplingScope}
    original_records = ((inputs.assessment, inputs.calibrated_freeze, inputs.model_freeze) if config.programme == "E3"
        else (inputs.readout,))
    by_ref = {_reference(value): value for value in original_records}
    with custody_owner.original_read_scope() as (writer, read_scope):
        for original in custody.original_products:
            raw = _original_product(writer, original, original.record, codecs, read_scope)
            if raw != by_ref[original.record].canonical_bytes():
                raise PermissionError("sampling follow-on changes its actual original scientific result bytes")
        pairs = {evidence.identity: (request, evidence) for request, evidence in inputs.sampling_pairs if evidence is not None}
        if tuple(value.evidence for value in custody.sampling_evidence) != tuple(sorted(pairs, key=lambda value: value.object_id)):
            raise PermissionError("sampling follow-on changes its complete independently produced evidence custody")
        for original in custody.sampling_evidence:
            _sampling_evidence(writer, *pairs[original.evidence], original, codecs, read_scope)
        writer.require_verification_snapshot()
    if custody_owner.current_task(context, runner) != (package, plan, task):
        raise PermissionError("sampling follow-on current authority or source drifted during original evidence authentication")
    return MatrixSamplingWorker(config.programme, prepared_scope=(context.run_id, context.task_id,
        context.input_materialization_ids, ObjectIdentity.from_record(plan.execution_plan_id, plan)))


class MatrixSamplingRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    """Domain-scoped parent preparation beside the original exact-input owner."""

    def __init__(self, supplier, *, writer, reveal_authority_id=None, custody=None):
        self.supplier = supplier
        self.writer = writer
        self.reveal_authority_id = reveal_authority_id
        if custody is not None and (type(custody) is not CurrentIssuedTaskCustody
                or custody.writer is not writer or custody.reveal_authority_id != reveal_authority_id):
            raise TypeError("sampling custody changes its exact writer or reveal selection")
        self.custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id) if custody is None else custody

    def resolve_input(self, spec):
        return self.supplier.resolve_input(spec)

    def prepare_matrix_sampling(self, context, runner):
        with self.custody.preparation_scope():
            return prepare_matrix_sampling(self, context, runner)


def bind_matrix_sampling_handoff(handoff, *, writer, reveal_authority_id=None):
    """Attach the registered follow-on to the existing public prospective API.

    Author the selected scientific input/custody bundle through the existing
    prospective application service, then bind this exact returned handoff.
    Actual current and original grants are checked again at worker admission.
    """
    from .recursive_prospective_authoring import RecursiveProspectiveApplicationHandoff
    from empirical_lawhood.kernel.serialization import validate_stable_id
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort

    if type(handoff) is not RecursiveProspectiveApplicationHandoff:
        raise TypeError("sampling follow-on requires the exact public prospective application handoff")
    if reveal_authority_id is not None:
        validate_stable_id(reveal_authority_id)
    configs = handoff.compilation.config_inputs
    if not configs or any(type(row.record) is not MatrixSamplingConfig for row in configs):
        raise ValueError("sampling follow-on handoff mixes an unrelated scientific operation or lifecycle")
    ports = []
    custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id)
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("sampling follow-on replaces its original exact-input provider")
        supplier = MatrixSamplingRuntimeInputSupplier(platform.port.supplier, writer=writer,
            reveal_authority_id=reveal_authority_id, custody=custody)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))
