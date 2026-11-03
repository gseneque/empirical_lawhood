# SPDX-License-Identifier: MPL-2.0
"""Original E4 revision calibration from genuine issued acquisition custody.

All protected reads reuse existing current/prior issue and reveal readers. The
domain replays the installed producer scope and reconstructs actual paired
records. No source eligibility, missing native effect or authority is inferred.
"""

from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactBank, compact_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition import (
    ScheduledProgrammeAcquisitionAdmissionConfig, ScheduledProgrammeAcquisitionCollectorConfig, validate_acquisition_root,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_custody import validate_acquisition_operation_census
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_parent import authenticate_global_parent
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import validate_programme_bank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_reduction import ScheduledProgrammeWaveResult, reduce_programme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionCaseData, ScheduledRevisionDataBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledCausalPrefix, identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration import ScheduledRevisionCalibration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_bindings import (
    BLIND, MAXIMUM_RECORD_BYTES, PreparedRevisionCalibration, RevisionCalibrationInputs,
    ScheduledRevisionCalibrationConfig, ScheduledRevisionCalibrationScope, ScheduledRevisionCalibrationSources,
    ScheduledRevisionCalibrationWorker, calibration_task_id, pin,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_custody import (
    ScheduledRevisionCalibrationCustody, validate_calibration_producer,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_future_bindings import (
    ScheduledRevisionFutureScope,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_public import ScheduledRevisionPublicCalibration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_seal_custody import prior_seal_scope_validator
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody, issued_custody_for_supplier
from empirical_lawhood.api.matrix_sampling_runtime import _original_product, _selected_control
from empirical_lawhood.api.matrix_scheduled_factorial_runtime import _ordinary_execution, _original_external
from empirical_lawhood.api.recursive_qualified_parents import (
    _authenticate_prior_execution, _output_payload, _prior_native_subwork, _replay_parent_authority,
    _semantic_writer, _verify_receipt_closure,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.plans import ExecutionPlan
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorNativeBinding


def _record_input(writer, run_id, task, name, kind):
    """Read only the exact issued operand, after its caller authenticates grants."""
    if name == "config":
        logical_id = task.capability.config.artifact_id
    else:
        edges = tuple(value for value in task.scientific_inputs if value.consumer_input_id == name)
        if len(edges) != 1 or edges[0].producer_task_id is not None or edges[0].external_input_id is None:
            raise PermissionError("revision calibration omits an exact original external prerequisite")
        logical_id = edges[0].operational_logical_artifact_id
    specs = tuple(value for value in task.external_inputs if value.logical_artifact_id == logical_id)
    if len(specs) != 1:
        raise PermissionError("revision calibration aliases its actual original input")
    spec, = specs
    if (spec.expected_payload_schema != kind.SCHEMA or spec.expected_content_sha256 is None
            or spec.expected_size_bytes is None or not 0 < spec.expected_size_bytes <= MAXIMUM_RECORD_BYTES
            or spec.expected_media_type != "application/json"
            or type(spec.expected_outcome_access) is not OutcomeAccess
            or type(spec.expected_visibility_ceiling) is not VisibilityCeiling):
        raise PermissionError("revision calibration lacks its exact bounded original record contract")
    manifest = _original_external(writer, run_id, spec)
    return CurrentIssuedTaskCustody(writer=writer).control_record(manifest, kind, MAXIMUM_RECORD_BYTES,
        expected_outcome_access=spec.expected_outcome_access, expected_visibility_ceiling=spec.expected_visibility_ceiling)


def _genuine_calibration_scope(scope, bank):
    if type(scope) is not ScheduledRevisionCalibrationScope or type(bank) is not ScheduledCompactBank:
        raise TypeError("revision calibration requires its actual closed scientific scope/bank")
    scope.__post_init__()
    validate_programme_bank(scope.future.programme, bank)
    if compact_identity(bank) != scope.future.programme.bank:
        raise PermissionError("revision calibration changes its actual original bank")


def _authenticate_global(writer, binding, codecs, read_scope):
    """Use the actual original issued global preparation, without qualification."""
    authenticate_global_parent(writer, binding)
    package, plan = _ordinary_execution(writer, binding.receipt.run_id)
    if type(binding.execution_plan) is not ExecutionPlan or plan != binding.execution_plan:
        raise PermissionError("revision calibration cannot substitute a candidate/software global parent")
    stored = ExternalTaskReceiptStore(writer).read_by_receipt_id(binding.receipt.run_id,
        binding.receipt.task_id, binding.receipt.receipt_id)
    semantic = _semantic_writer(package, plan, writer, codecs)
    prefixes = tuple(sorted(value.capability_key for value in package.registry.capabilities))
    closure = read_scope.receipt_closure(package, plan, semantic, None, prefixes)
    if stored != binding.receipt or _verify_receipt_closure(semantic, closure).get(stored.task_id) != stored:
        raise PermissionError("revision calibration global parent changes its actual original successful producer")
    task, = (value for value in plan.tasks if value.task_id == stored.task_id)
    if _record_input(writer, stored.run_id, task, "config", type(binding.configuration)) != binding.configuration:
        raise PermissionError("revision calibration global parent substitutes its actual original configuration")


def _wave_scope(*, scope, sources, bank, wave_id, codecs, binding, package, execution_plan, receipt, logical, writer, read_scope):
    """Require the actual native wave to have consumed these original seals."""
    programme = scope.future.programme
    wave, = (value for value in programme.waves if value.wave_id == wave_id)
    root = package.issued_study.candidate.authoring_package.base.draft
    if (root.system is None or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or any(getattr(value, "fixture_scope_id", None) is not None or getattr(value, "plumbing_only", False)
                for value in (package, execution_plan))
            or binding.task_id != wave.wave_id + ".collect" or binding.record_id_field != "result_id"
            or logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise PermissionError("revision calibration original wave is outside its actual sealed scientific scope")
    opening, = (value for value in execution_plan.tasks if value.task_id == wave.wave_id + ".open")
    admission = _record_input(writer, binding.run_id, opening, "config", ScheduledProgrammeAcquisitionAdmissionConfig)
    original = admission.scope
    if original.programme != programme or original.bank != compact_identity(bank) or original.wave != wave:
        raise PermissionError("revision calibration changes its original acquisition population/source/bank")
    validate_acquisition_root(original, root, bank, execution_plan=execution_plan,
        protocol=package.issued_study.candidate.base_candidate.base_candidate.protocol, revision_scope=scope.future)
    _authenticate_global(writer, admission.global_parent_binding, codecs, read_scope)
    collector, = (value for value in execution_plan.tasks if value.task_id == binding.task_id)
    config = _record_input(writer, binding.run_id, collector, "config", ScheduledProgrammeAcquisitionCollectorConfig)
    if (config.programme != programme.identity or config.scope != original.identity or config.bank != programme.bank
            or config.wave != wave or config.mode != "E4_REVISION_CALIBRATION"):
        raise PermissionError("revision calibration substitutes its actual original collector scope/configuration")
    validate_acquisition_operation_census(programme, wave, config.operation, execution_plan, revision_scope=scope.future)
    by_case = {value.forecast.case_id: value for value in sources.forecasts}
    by_native_task = {COMPACT_NAMESPACE + "." + case_id + "." + role: value
        for case_id, value in by_case.items() for role in ("continue", "responses")}
    native_tasks = tuple(value for value in execution_plan.tasks if value.task_id.rsplit(".", 1)[-1] in ("continue", "responses"))
    if len(native_tasks) != 2 * len(wave.root_ids):
        raise PermissionError("revision calibration omits an original native forecast prerequisite")
    for task in native_tasks:
        prior = by_native_task.get(task.task_id)
        if prior is None:
            raise PermissionError("revision calibration native task loses its exact original case")
        case_id = prior.forecast.case_id
        if case_id not in wave.root_ids or by_case[case_id] != prior:
            raise PermissionError("revision calibration substitutes its original assigned native case")
        expected = (("revision-scope", scope.future), ("revision-seal", prior.forecast),
            ("revision-custody", prior), ("revision-seal-receipt", prior.receipt))
        for name, record in expected:
            if _record_input(writer, binding.run_id, task, name, type(record)) != record:
                raise PermissionError("revision calibration seal was not the exact original native precondition")


def _codecs():
    from empirical_lawhood.api.recursive_operations import operation_catalog
    return operation_catalog()[2]


def reconstruct_revision_calibration(*, writer, config, scope, sources, bank, codecs, read_scope):
    """Reconstruct original complete outcomes; incomplete scores stay missing."""
    _genuine_calibration_scope(scope, bank)
    sources.validate_scope(scope)
    if (config.scope, config.sources, config.bank, config.unit_ids) != (scope.identity, sources.identity,
            compact_identity(bank), scope.future.programme.group_ids):
        raise PermissionError("revision calibration changes exact configured scientific inputs")
    forecasts, forecast_runs = [], set()
    for original in sources.forecasts:
        prior = _authenticate_prior_execution(original.prior_execution, writer, codecs,
            scope_validator=prior_seal_scope_validator, parent_evidence=(scope.future, original),
            read_scope=read_scope, required_outcome_access=BLIND)
        if prior.product.payload != original.forecast.canonical_bytes():
            raise PermissionError("revision calibration substitutes its actual original frozen forecast")
        authenticate_publication(writer, original.publication, original.forecast)
        authenticate_publication(writer, original.receipt_publication, original.receipt)
        forecasts.append(original.forecast)
        forecast_runs.add(prior.package.run_plan_id)
    results, payloads, wave_packages = [], {}, []
    for original in sources.waves:
        seen = {}
        def validate(**values):
            _wave_scope(scope=scope, sources=sources, bank=bank, wave_id=original.wave_id, codecs=codecs, **values)
            seen.update(values)
        raw = _original_product(writer, original.original, original.original.record, codecs, read_scope, scope_validator=validate)
        result = decode_canonical_bytes(raw, ScheduledProgrammeWaveResult, maximum_bytes=MAXIMUM_RECORD_BYTES)
        if result.identity != original.original.record or result.wave_id != original.wave_id or result.programme != scope.future.programme.identity:
            raise PermissionError("revision calibration original collector substitutes its exact assigned wave result")
        results.append(result)
        package, plan = seen["package"], seen["execution_plan"]
        semantic = _semantic_writer(package, plan, writer, codecs)
        prefixes = tuple(sorted(value.capability_key for value in package.registry.capabilities))
        # The original-product reader already authenticated this reveal before
        # protected bytes. Reuse that exact invocation-local closure.
        _, reveal = _replay_parent_authority(original.original, package, writer)
        wave_packages.append((original.original, package))
        closure = read_scope.receipt_closure(package, plan, semantic, reveal, prefixes)
        receipts = _verify_receipt_closure(semantic, closure)
        natives = tuple(RecursivePriorNativeBinding(COMPACT_NAMESPACE + "." + row.root_id + "." + native.phase,
            native.definition, native.completion, native.receipt)
            for row in result.cases for native in row.native if native.disposition == "COMPLETED")
        if original.original.prior_execution.native_subwork != natives:
            raise PermissionError("revision calibration omits or substitutes original native completion custody")
        _prior_native_subwork(semantic, original.original.prior_execution, plan, receipts)
        for row in result.cases:
            for header in row.ordinary_receipts:
                if not hasattr(header, "task_id"):
                    raise PermissionError("revision calibration original wave lacks actual ordinary dependency headers")
                producing = receipts.get(header.task_id)
                if producing is None or producing.receipt_id != header.receipt_id or not set(header.output_materialization_ids) <= {
                        value.materialization_id for value in producing.output_materializations}:
                    raise PermissionError("revision calibration changes actual original per-case ordinary receipt lineage")
        for receipt in receipts.values():
            for logical in receipt.output_logical_artifacts:
                kind = {ScheduledCausalPrefix.SCHEMA: ScheduledCausalPrefix, ScheduledResponseScore.SCHEMA: ScheduledResponseScore}.get(logical.payload_schema)
                if kind is None:
                    continue
                record = decode_canonical_bytes(_output_payload(semantic, receipt, logical, MAXIMUM_RECORD_BYTES), kind,
                    maximum_bytes=MAXIMUM_RECORD_BYTES)
                reference = identity(record)
                if reference in payloads:
                    raise PermissionError("revision calibration duplicates an original prefix/score producer")
                payloads[reference] = record
    programme = scope.future.programme
    reduction = reduce_programme(programme, tuple(results), reduction_id=config.reduction_id, authenticate_wave=lambda value: None)
    coordinates = {source.root_id: source.coordinate for source in bank.sources}
    prefixes_by_root = {}
    for value in payloads.values():
        if type(value) is ScheduledCausalPrefix:
            root_id = value.root.root_id
            if root_id in prefixes_by_root:
                raise PermissionError("revision calibration aliases an actual original causal prefix")
            prefixes_by_root[root_id] = value
    rows = []
    for case, result in zip(programme.cases, reduction.cases, strict=True):
        prefix = prefixes_by_root.get(case.root_id)
        score = None if result.score is None else payloads.get(result.score)
        if result.score is not None and score is None:
            raise PermissionError("revision calibration replaces a missing original declared score by a new label")
        rows.append(ScheduledRevisionCaseData(case.root_id, coordinates[case.root_id], prefix, score))
    data = ScheduledRevisionDataBank(config.data_id, programme.identity, pin(reduction, "reduction_id"), tuple(rows))
    inputs = RevisionCalibrationInputs(reduction, data, tuple(forecasts))
    inputs.assess(config, scope)
    for original, package in wave_packages:
        _replay_parent_authority(original, package, writer)
    for run_id in sorted(forecast_runs):
        _ordinary_execution(writer, run_id)
    return inputs


def prepare_revision_calibration(supplier, context, runner):
    if type(runner) is not ScheduledRevisionCalibrationWorker or runner.prepared is not None:
        raise PermissionError("revision calibration requires its unprepared installed original producer")
    current = issued_custody_for_supplier(supplier)
    package, plan, task = current.current_task(context, runner)
    _, controls = current.task_inputs(context, task)
    if task.dependency_task_ids or len(controls) != 4:
        raise PermissionError("revision calibration changes its closed actual external-input census")
    config = _selected_control(current, task, controls[context.config.artifact_id], ScheduledRevisionCalibrationConfig)
    values = {}
    for name, kind in (("scope", ScheduledRevisionCalibrationScope), ("sources", ScheduledRevisionCalibrationSources), ("bank", ScheduledCompactBank)):
        reference = getattr(config, name)
        selected = tuple(value for value in controls.values()
            if (value.logical.payload_schema, value.logical.content_sha256) == (reference.object_schema, reference.object_fingerprint))
        if len(selected) != 1 or selected[0].logical.outcome_access is not BLIND or selected[0].logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise PermissionError("revision calibration changes exact original blind source metadata")
        values[name] = _selected_control(current, task, selected[0], kind)
    if context.task_id != calibration_task_id(config.scope):
        raise PermissionError("revision calibration substitutes its actual current producer")
    with current.original_read_scope() as (writer, read_scope):
        inputs = reconstruct_revision_calibration(writer=writer, config=config, **values, codecs=_codecs(), read_scope=read_scope)
        writer.require_verification_snapshot()
    if current.current_task(context, runner) != (package, plan, task):
        raise PermissionError("revision calibration current issue/grants changed during original source replay")
    prepared = PreparedRevisionCalibration(context.run_id, context.task_id, pin(plan, "execution_plan_id"),
        context.input_materialization_ids, config.identity, config.scope, config.sources, inputs)
    return ScheduledRevisionCalibrationWorker(runner.manifest, prepared)


def authenticate_revision_calibration(*, writer, custody, future, codecs, read_scope):
    """Replay the actual original sealed producer before dependent CONF entry."""
    if type(custody) is not ScheduledRevisionCalibrationCustody or type(future) is not ScheduledRevisionFutureScope:
        raise TypeError("revision confirmation requires actual original calibration custody and frozen future scope")
    custody.__post_init__()
    future.__post_init__()
    if future.calibration is None or custody.calibration != future.calibration:
        raise PermissionError("revision confirmation substitutes its original public calibration projection")
    selected = {}
    def validate(**values):
        config = _record_input(values["writer"], values["binding"].run_id,
            next(task for task in values["execution_plan"].tasks if task.task_id == values["binding"].task_id),
            "config", ScheduledRevisionCalibrationConfig)
        if config != custody.configuration:
            raise PermissionError("revision calibration custody substitutes the actual original configuration")
        validate_calibration_producer(config=config, **{key: values[key] for key in
            ("binding", "package", "execution_plan", "receipt", "logical")})
        task, = values["execution_plan"].tasks
        selected.update(config=config, scope=_record_input(values["writer"], values["binding"].run_id, task, "scope", ScheduledRevisionCalibrationScope),
            sources=_record_input(values["writer"], values["binding"].run_id, task, "sources", ScheduledRevisionCalibrationSources),
            bank=_record_input(values["writer"], values["binding"].run_id, task, "bank", ScheduledCompactBank))
        original = selected["scope"].future
        if ((original.development, original.nomination, original.frozen, original.programme) !=
                (future.development, future.nomination, future.frozen, future.calibration_programme)):
            raise PermissionError("revision confirmation changes original calibrated populations, source or frozen models")
    raw = _original_product(writer, custody.original, custody.calibration.original, codecs, read_scope, scope_validator=validate)
    actual = decode_canonical_bytes(raw, ScheduledRevisionCalibration, maximum_bytes=MAXIMUM_RECORD_BYTES)
    inputs = reconstruct_revision_calibration(writer=writer, **selected, codecs=codecs, read_scope=read_scope)
    if actual != inputs.assess(selected["config"], selected["scope"]) or ScheduledRevisionPublicCalibration.from_calibration(actual) != custody.calibration:
        raise PermissionError("revision calibration changes actual original scores, complete denominator or public metadata")
    authenticate_publication(writer, custody.publication, actual)
    authenticate_publication(writer, custody.receipt_publication, custody.receipt)
    from empirical_lawhood.api.recursive_qualified_parents import _actual_package
    _replay_parent_authority(custody.original, _actual_package(writer, custody.original.prior_execution.run_id), writer)
    return actual


def bind_revision_calibration_handoff(handoff, *, writer, reveal_authority_id=None):
    """Bind the registered producer to the ordinary public prospective handoff."""
    from empirical_lawhood.api.recursive_prospective_authoring import RecursiveProspectiveApplicationHandoff
    from empirical_lawhood.api.matrix_scheduled_programme_runtime import ProgrammeRuntimeInputSupplier
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    if type(handoff) is not RecursiveProspectiveApplicationHandoff or not handoff.compilation.config_inputs or any(
            type(value.record) is not ScheduledRevisionCalibrationConfig for value in handoff.compilation.config_inputs):
        raise TypeError("revision calibration requires its exact public prospective producer handoff")
    ports = []
    custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id)
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("revision calibration replaces its original exact-input provider")
        supplier = ProgrammeRuntimeInputSupplier(platform.port.supplier, writer=writer, output_codecs=_codecs(), reveal_authority_id=reveal_authority_id, custody=custody)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))
