# SPDX-License-Identifier: MPL-2.0
"""Actual native TRAIN custody for the new future-relative instrument certificate.

The certificate is deliberately reconstructed from real public development
products. Publishing a same-schema record does not satisfy this boundary.
No native execution, fit, new receipt or authority is created here.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import contracts, entry_task_id, task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_request
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census, validate_response_native_evidence
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.native_training_banks import _read_instance, _receipt_product
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_roots
from empirical_lawhood.api.recursive_operations import development_output_contracts, operation_catalog
from empirical_lawhood.api.recursive_qualified_parents import _output_payload
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan


def _named_score(writer, products, plan, root_id):
    selected_task_id = task_id(root_id, "response-score")
    task, = (value for value in plan.tasks if value.task_id == selected_task_id)
    receipt = products["receipts"].get(selected_task_id)
    output, = (value for value in task.outputs if value.output_id == selected_task_id + ".score"
        and value.payload_schema == train.NativeTrainingScore.SCHEMA)
    if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or receipt.task_id != selected_task_id or receipt.run_id != plan.source_plan.object_id):
        raise PermissionError("finite-dt instrument omits actual response control receipt")
    logical, = (value for value in receipt.output_logical_artifacts if value.logical_artifact_id == output.logical_artifact_id)
    physical, = (value for value in receipt.output_materializations if value.logical_artifact_id == output.logical_artifact_id)
    retained = products["outputs"].get(output.logical_artifact_id)
    if (retained is None or (retained.logical, retained.materialization) != (logical, physical)
            or logical.payload_schema != train.NativeTrainingScore.SCHEMA
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != "application/json"
            or logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise PermissionError("finite-dt instrument changes actual response score custody/exposure")
    raw = _output_payload(writer, receipt, logical, physical.size_bytes)
    score = decode_canonical_bytes(raw, train.NativeTrainingScore, maximum_bytes=len(raw))
    if raw != score.canonical_bytes() or score.fingerprint() != logical.content_sha256:
        raise PermissionError("finite-dt instrument substitutes actual original response controls")
    return score


def _certify_native_training_instrument(*, writer, locator, future_bank, future_group_ids, original_future_reservation,
        cutoff, record_id, expected_census=None):
    """Read once at an owned boundary; return a pure future-relative certificate.

    Callers may publish this value, but subsequent author/load/read/run owners
    reconstruct it again. This call grants no source, issue or reveal authority.
    """
    if type(locator) is not r.MatrixFiniteDtTrainingLocator:
        raise TypeError("finite-dt certification requires the exact original public TRAIN locator")
    locator.__post_init__()
    directory = writer.root.resolve(locator.authored_directory, for_write=False)
    def validate_authored(*, packet, draft, source, payloads, run, plan, index):
        specification, request, _ = _read_instance(payloads)
        if (type(plan) is not DevelopmentExecutionPlan or r.pin(packet, "packet_id") != locator.packet
                or r.pin(plan, "execution_plan_id") != locator.execution_plan or run.run_plan_id != locator.run_id
                or draft.development_study is None or draft.prospective_draft is not None
                or request.future_manifest.reservation != original_future_reservation):
            raise PermissionError("finite-dt instrument substitutes original TRAIN plan, development lane or prior future reservation")
        future_selections = authenticate_request(writer, request)
        if expected_census is not None and request.future_manifest.audit.census != expected_census:
            raise PermissionError("finite-dt future source changes its authenticated pre-TRAIN exposure census")
        _, _, codecs = operation_catalog()
        development_output_contracts(plan, codecs)
        return specification, request, future_selections
    # Ordinary DEV published no capability semantic flag; authenticate the
    # installed contracts without replacing those original manifest semantics.
    semantic = writer
    selected, roots, (specification, request, future_selections) = _read_recursive_wave_with_roots(
        directory=directory, artifact_writer=semantic, include_products=True,
        terminal_product_format="documents", allow_partial=False, validate_authored=validate_authored)
    report, products, actual_draft, actual_plan = selected
    packet, draft, _, run, plan, _ = roots
    if (actual_draft != draft or actual_plan != plan or report["run_id"] != run.run_plan_id
            or report["packet_sha256"] != packet.fingerprint() or report["status"] != "SUCCEEDED"
            or set(products["receipts"]) != {value.task_id for value in plan.tasks}
            or report.get("scientific_result", {}).get("scientific_completion") != "COMPLETE_NATIVE_TRAIN_ARRAY_REPLAY"):
        raise PermissionError("finite-dt instrument requires the unchanged complete successful public TRAIN acquisition")
    acquisition, entry_receipt = _receipt_product(semantic, products, plan, entry_task_id(specification),
        train.NativeTrainingAcquisitionSeal)
    if acquisition != train.acquisition_seal(specification, request):
        raise PermissionError("finite-dt instrument changes its actual pre-acquisition original reservation seal")
    configured = dict(contracts(specification, request)[0])
    source_index = ScheduledSourceIndex.from_shared(reservation=request.train_manifest.reservation,
        specification=request.train_manifest.native_specification, provenances=request.train_manifest.provenances)
    source_index.require_roster(request.sources, expected_root_ids=specification.root_ids)
    rows = []
    provenances, factor_designs = set(), set()
    for root_id in specification.root_ids:
        source = train.source_for(request, root_id, index=source_index)
        provenances.add(source.provenance.identity)
        factor_designs.add(scheduled.identity(source.policy.factor_numerical_design))
        protocol, = (value for value in request.protocols if value.public_source.root.root_id == root_id)
        panels = train.panels_for(request, source)
        selected = {}
        receipts = [entry_receipt]
        for phase, kind in (("prefix", train.NativeTrainingPrefixHistory),
                ("numerical", train.NativeTrainingNumericalAssessment),
                ("check", train.NativeTrainingFrameAssessment), ("project", train.NativeTrainingCausalPrefix),
                ("physical-forecast", train.NativeTrainingPhysicalForecast), ("responses", train.NativeTrainingResponse)):
            selected[phase], receipt = _receipt_product(semantic, products, plan, task_id(root_id, phase), kind)
            receipts.append(receipt)
        history, numerical, frames, causal, physical, responses = (selected[name]
            for name in ("prefix", "numerical", "check", "project", "physical-forecast", "responses"))
        history.validate_source(source)
        score = _named_score(semantic, products, plan, root_id)
        for phase in train.PHASES:
            receipt = products["receipts"].get(task_id(root_id, phase))
            if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or receipt.task_id != task_id(root_id, phase) or receipt.run_id != plan.source_plan.object_id):
                raise PermissionError("finite-dt instrument loses an actual complete native TRAIN producer")
            receipts.append(receipt)
        source_pin = scheduled.identity(source)
        if (history.acquisition != acquisition.identity or history.configuration != train.identity(configured[task_id(root_id, "prefix")])
                or numerical.source != source_pin or numerical.history != train.identity(history)
                or numerical.numerical_design != scheduled.identity(source.numerical_design)
                or frames.source != source_pin or frames.witness != causal.witness
                or frames.numerical_design != scheduled.identity(source.policy.factor_numerical_design)
                or causal.source != source_pin or causal.history != train.identity(history)
                or causal.numerical != train.identity(numerical) or causal.frame_assessment != train.identity(frames)
                or causal.policy != scheduled.identity(source.policy) or causal.root != source.root.root
                or causal.cutoff_tick != source.policy.cutoff_tick
                or physical.source != source_pin or physical.causal_prefix != train.identity(causal)
                or physical.protocol != train.identity(protocol) or responses.source != source_pin
                or responses.causal_prefix != train.identity(causal) or responses.physical_forecast != train.identity(physical)
                or responses.acquisition_seal != acquisition.identity or responses.protocol != train.identity(protocol)
                or responses.branch_ids != tuple(value[0] for value in branch_census(protocol, panels))
                or (score.source, score.causal_prefix, score.physical_forecast, score.responses,
                    score.acquisition_seal, score.root_id, score.independent_group_id, score.role, score.criterion) !=
                   (source_pin, train.identity(causal), train.identity(physical), train.identity(responses), acquisition.identity,
                    root_id, source.root.root.independent_group_id, source.root.root.role.value, protocol.criterion)):
            raise PermissionError("finite-dt instrument changes actual original source/control/causal/assay/producer joins")
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_science import admit_response
        admit_response(source, protocol, panels, acquisition, causal, physical, responses)
        if responses.native:
            validate_response_native_evidence(responses, source, specification.identity, history, causal, physical, acquisition,
                configuration=train.identity(configured[task_id(root_id, "responses")]),
                parent_task=task_id(root_id, "responses"), operation=train.NAMESPACE + ".paired-responses.v1",
                shared_sources=train.native_source_pins(source), panels=panels, protocol=protocol)
        expected = {"control.scheduled." + root_id + "." + branch: (1 if view == "PRIMARY" else 2) * protocol.horizon_steps[-1]
            for branch, view, *_ in branch_census(protocol, panels)}
        if responses.disposition == "COMPLETED":
            if (causal.disposition != "AVAILABLE" or physical.disposition != "AVAILABLE"
                    or {value.control_id for value in score.controls} != set(expected) or len(score.controls) != len(expected)
                    or any(value.denominator_steps != expected[value.control_id]
                        or value.tolerance != protocol.native_reference_tolerance for value in score.controls)):
                raise PermissionError("finite-dt instrument thins actually exercised independent native response controls")
        elif score.controls or score.numerical_pass:
            raise PermissionError("finite-dt nonuse invents exercised native response controls")
        for value in (*numerical.controls, *frames.controls, *score.controls):
            value.__post_init__()
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import paired_response_view_values
        paired_response_view_values(specification, source, protocol, panels, score)
        rows.append(r.MatrixFiniteDtRootControl(root_id, source.root.root.independent_group_id, source_pin,
            train.identity(history), train.identity(numerical), train.identity(causal), train.identity(frames),
            train.identity(physical), train.identity(responses), train.identity(score),
            tuple(sorted({r.pin(value, "receipt_id") for value in receipts}, key=lambda value: value.object_id)),
            numerical.numerical_pass, frames.numerical_pass, any(value.disposition == "VIOLATED" for value in frames.controls),
            score.numerical_pass, len(score.controls), causal.disposition, responses.disposition))
    numerical = scheduled.identity(request.train_manifest.native_specification.selection.numerical_design)
    templates = {value.templates.array_artifact for value in request.protocols}
    seeds = {stream.effective_seed for value in request.train_manifest.reservation.allocation.roots for stream in value.streams}
    seeds.update(stream.effective_seed for panel in request.panels for stream in panel.streams)
    reserved = {stream.effective_seed for value in request.future_manifest.reservation.allocation.roots for stream in value.streams}
    reserved.update(stream.effective_seed for _, selection in future_selections
        for _, panels in selection.panels for panel in panels if panel.role == "INDEPENDENT_FUTURE" for stream in panel.streams)
    signatures = {r.instrument_signature(protocol) for protocol in request.protocols}
    if len(factor_designs) != 1 or len(signatures) != 1:
        raise PermissionError("finite-dt source changes the one actual checked factor/instrument protocol")
    result = r.MatrixFiniteDtInstrumentCertificate(record_id=record_id, locator=locator,
        specification=specification.identity, request=request.identity, acquisition=acquisition.identity,
        original_future_reservation=scheduled.identity(original_future_reservation), measurement=specification.measurement,
        numerical=numerical, factor_numerical=next(iter(factor_designs)), instrument_sha256=next(iter(signatures)),
        criterion=request.mathematical_protocol.identity,
        provenances=tuple(sorted(provenances, key=lambda value: value.object_id)),
        templates=tuple(sorted(templates, key=lambda value: value.artifact_id)), training_effective_seeds=tuple(sorted(seeds)),
        reserved_future_effective_seeds=tuple(sorted(reserved)), controls=tuple(rows), future_bank=future_bank, future_group_ids=future_group_ids, cutoff=cutoff)
    # Reuse the exact scientific operand guard without manufacturing a pipeline
    # receipt merely to return this certificate. The source protocol checks the
    # complete source/assay/profile/cutoff join before publishing or issuing.
    return result



def certify_native_training_instrument(*, writer, locator, programme, bank, original_future_reservation,
        cutoff, record_id):
    """Reconstruct actual controls, after the real future source scope is validated."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import validate_selected_phase_bank
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import require_e4_reserved_physical_exclusion
    validate_selected_phase_bank(programme, bank)
    require_e4_reserved_physical_exclusion(bank.reservation.allocation.coordinates, original_future_reservation)
    _authenticate_bank_publications(writer, bank)
    return _certify_native_training_instrument(writer=writer, locator=locator, future_bank=bank.identity,
        future_group_ids=programme.group_ids, original_future_reservation=original_future_reservation,
        cutoff=cutoff, record_id=record_id, expected_census=bank.audit.census)


def _authenticate_bank_publications(writer, bank, exposure_support=None):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import _authenticate_artifact
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    required = {artifact for artifact, _ in current_exposure_support(bank.audit)}
    if exposure_support is not None and ({value for value, _ in exposure_support} != required or len(exposure_support) != len(required)):
        raise PermissionError("finite-dt source omits its actual complete exposure supporting bytes")
    for artifact, custody in exposure_support or ():
        _authenticate_artifact(writer, artifact, custody)
    for publication, value in ((bank.reservation.publication, bank.reservation.allocation),
            (bank.specification.publication, bank.specification.selection), (bank.audit_publication, bank.audit),
            (bank.response_selection_publication, bank.response_selection)):
        authenticate_publication(writer, publication, value)
    originals = (bank.audit.census, *bank.audit.prior_scheduled_coordinates)
    for publication in bank.audit.prior_corpus:
        rows = tuple(value for value in originals if (value.SCHEMA, value.fingerprint()) ==
            (publication.logical.payload_schema, publication.logical.content_sha256))
        if len(rows) != 1:
            raise PermissionError("finite-dt source changes its exact original prior-corpus publication")
        authenticate_publication(writer, publication, rows[0])


def _native_training_file_supports(writer, locator, request_pin):
    """Capture exact authored FILE handles before expensive TRAIN reconstruction.

    A cache miss reads only the actual request metadata and joins its authored
    packet and request pin to the supplied certificate. The independent full
    reconstruction must still reproduce that exact certificate before use.
    """
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    directory = writer.root.resolve(locator.authored_directory, for_write=False)
    packet, _, _, payloads = load_authored_wave(directory=directory, artifact_writer=writer, lazy_payloads=True)
    _, request, _ = _read_instance(payloads)
    if r.pin(packet, "packet_id") != locator.packet or request.identity != request_pin:
        raise PermissionError("instrument FILE support changes its authenticated original request")
    return tuple((artifact, custody) for artifact, custody in request.exposure_support
        if type(custody) is ExperimentFileInputBinding)


def _verify_file_supports(writer, supports):
    """FILE custody has no publication snapshot; its actual bytes stay fresh."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import _authenticate_artifact
    for artifact, custody in supports:
        _authenticate_artifact(writer, artifact, custody)


def authenticate_instrument_certificate(*, writer, certificate, programme, bank, original_future_reservation,
        control_reader=None):
    """No authority verdict is cached; only immutable completed TRAIN facts.

    The existing scoped writer guards every actual original member/manifest on
    hits and expiry. Outside that explicit lifetime all original custody is read.
    """
    from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
    from empirical_lawhood.kernel.decoding import decimal_context_key
    if type(certificate) is not r.MatrixFiniteDtInstrumentCertificate:
        raise TypeError("finite-dt source requires its exact receipt-backed instrument certificate")
    certificate.__post_init__()
    reader = control_reader
    if reader is not None:
        if type(reader) is not CurrentResultPlanReader or reader.writer.root is not writer.root:
            raise PermissionError("finite-dt source changes its current immutable verification lifetime")
        reader.writer.require_verification_snapshot()
        writer = reader.writer
    key = (certificate.locator.fingerprint(), certificate.record_id, certificate.cutoff.fingerprint(),
        programme.fingerprint(), bank.fingerprint(), original_future_reservation.fingerprint(), decimal_context_key())
    cache = None if reader is None else getattr(reader, "_matrix_finite_dt_certificates", None)
    cached = None if cache is None else cache.get(key)
    file_supports = ()
    expected = None if cached is None else cached[0]
    if cached is not None:
        file_supports = cached[1]
        _verify_file_supports(writer, file_supports)
    if expected is None:
        file_supports = _native_training_file_supports(writer, certificate.locator, certificate.request)
        _verify_file_supports(writer, file_supports)
        expected = certify_native_training_instrument(writer=writer, locator=certificate.locator,
            programme=programme, bank=bank, original_future_reservation=original_future_reservation,
            cutoff=certificate.cutoff, record_id=certificate.record_id)
        if reader is not None:
            if cache is None:
                cache = reader._matrix_finite_dt_certificates = {}
            # Two immutable phase projections, owned by the existing lifetime;
            # no process-global cache, input/grant/output receipt is supplied.
            if len(cache) >= 2:
                cache.pop(next(iter(cache)))
            cache[key] = (expected, file_supports)
    if expected != certificate:
        raise PermissionError("finite-dt source refuses a caller-asserted, altered or incomplete instrument certificate")
    _verify_file_supports(writer, file_supports)
    if reader is not None:
        reader.writer.require_verification_snapshot()


class MatrixFiniteDtRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    """Fresh actual issue/grant/input checks before every parent-prepared gate."""
    def __init__(self, supplier, *, custody):
        from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
        if type(custody) is not CurrentIssuedTaskCustody:
            raise TypeError("finite-dt source requires its exact shared current task custody")
        self.supplier, self.custody = supplier, custody

    def resolve_input(self, spec):
        return self.supplier.resolve_input(spec)

    def prepare_matrix_finite_dt_gate(self, context, runner):
        with self.custody.preparation_scope():
            return self._prepare_matrix_finite_dt_gate(context, runner)

    def _prepare_matrix_finite_dt_gate(self, context, runner):
        from empirical_lawhood.adapters.methods import matrix_finite_dt_source_bindings as bindings
        if type(runner) is not bindings.MatrixFiniteDtGateWorker:
            raise PermissionError("finite-dt source refuses a foreign prepared runner")
        _, _, task = self.custody.current_task(context, runner)
        _, manifests = self.custody.task_inputs(context, task)
        manifest = manifests[context.config.artifact_id]
        config = self.custody.control_record(manifest, runner.config_kind, manifest.materialization.size_bytes)
        if config.gate_kind is not runner.kind or config.resource_budget != context.resource_budget:
            raise PermissionError("finite-dt source changes its actual selected gate or resources")
        records = {}
        for name, kind in bindings.input_kinds().items():
            edges = tuple(value for value in task.scientific_inputs if value.consumer_input_id == name)
            if len(edges) != 1 or edges[0].producer_task_id is not None:
                raise PermissionError("finite-dt source changes its exact original external input ownership")
            manifest = manifests.get(edges[0].operational_logical_artifact_id)
            if manifest is None or manifest.logical.payload_schema != kind.SCHEMA:
                raise PermissionError("finite-dt source substitutes a current original scientific input")
            read = self.custody.control_record if name in ("numerical", "cutoff") else self.custody.immutable_control_record
            records[name] = read(manifest, kind, manifest.materialization.size_bytes)
        if len(task.scientific_inputs) != len(records):
            raise PermissionError("finite-dt source changes its complete original gate operand census")
        r.validate_gate_operands(config, records["scope"], records)
        authenticate_instrument_certificate(writer=self.custody.writer, certificate=records["certificate"],
            programme=records["programme"], bank=records["bank"],
            original_future_reservation=records["original-reservation"], control_reader=self.custody._control_reader)
        return runner.with_prepared_scope(bindings.PreparedFiniteDtGateScope(context.run_id, context.task_id,
            config.identity, records["scope"].identity, records["certificate"].identity))


def bind_finite_dt_source_handoff(handoff, *, writer, reveal_authority_id=None):
    from dataclasses import replace
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id)
    ports = []
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("finite-dt source changes its exact installed public input port")
        supplier = MatrixFiniteDtRuntimeInputSupplier(platform.port.supplier, custody=custody)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))


def authenticate_installed_source_prerequisite(*, writer, result, pipeline, publications, read_scope):
    """Reconstruct original TRAIN at the actual E4 consumer, including direct SDK use."""
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_bindings as bindings
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    declared = {bindings.gate_declaration(kind).capability_key: kind for kind in r.GATES}
    selected_keys = {gate.method.capability_key for gate in result.gate_evidence}
    scope_kind = r.MatrixFiniteDtSourceScope
    input_kinds = bindings.input_kinds()
    if (len(result.gate_evidence) != len(declared)
            or selected_keys != set(declared)):
        raise PermissionError("finite-dt source mixes or omits its actual installed independent predicates")
    supplied = dict(publications)
    scope_pins = {pin for gate in result.gate_evidence for pin in gate.input_operands
        if pin.object_schema == scope_kind.SCHEMA}
    if len(scope_pins) != 1:
        raise PermissionError("finite-dt source loses its one exact original complete source scope")
    # Some selected E5/E6 consumers deliberately authenticate ordinary
    # originals without a shared verification lifetime. Re-read every control
    # and the actual TRAIN closure on that path; never invent a live reader.
    reader = None if read_scope is None else read_scope.plan_reader

    def original(pin, kind):
        publication = supplied.get(pin)
        if publication is None or (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
            raise PermissionError("finite-dt source omits an exact original published scientific operand")
        authenticate_publication(writer, publication)
        manifest = writer.read_manifest(publication.materialization.relative_path)
        if (manifest.logical, manifest.materialization) != (publication.logical, publication.materialization):
            raise PermissionError("finite-dt source substitutes its actual original publication member")
        # Seven large/shared records plus the current package fit the existing
        # bounded control reader. Small policy/cutoff records remain ordinary.
        if reader is None or kind in (input_kinds["numerical"], input_kinds["cutoff"]):
            value = CurrentIssuedTaskCustody(writer=writer).control_record(manifest, kind, manifest.materialization.size_bytes)
        else:
            value = reader.read_control(manifest, kind, manifest.materialization.size_bytes)
        actual = (r.pin(value, "cutoff_id") if kind is input_kinds["cutoff"] else
            scheduled.identity(value) if kind in (input_kinds["reservation"], input_kinds["numerical"])
            else value.identity)
        if actual != pin:
            raise PermissionError("finite-dt source changes the actual original record identifier or bytes")
        return value

    scope = original(next(iter(scope_pins)), scope_kind)
    pins = {"scope": scope.identity, "programme": scope.programme, "bank": scope.bank,
        "reservation": scope.reservation, "original-reservation": scope.original_future_reservation,
        "assay": scope.assay, "numerical": scope.numerical, "cutoff": r.pin(scope.cutoff, "cutoff_id"),
        "certificate": scope.certificate}
    records = {name: scope if name == "scope" else original(pins[name], kind)
        for name, kind in input_kinds.items()}
    for gate in result.gate_evidence:
        kind = declared[gate.method.capability_key]
        config, = (value for value in r.gate_configs(scope) if value.gate_kind is kind)
        declaration = bindings.gate_declaration(kind)
        if ((gate.method.capability_version, gate.method.implementation_sha256) !=
                (declaration.capability_version, declaration.manifest().implementation_sha256)
                or r.validate_gate_operands(config, scope, records) != gate):
            raise PermissionError("finite-dt source changes an actual original independently installed gate")
    if (scope.profile != pipeline.pipeline_config.profile or scope.pipeline_receipt != pipeline.receipt
            or scope.publication != scope.recovery or scope.recovery != pipeline.pipeline_config.execution_evidence.recovery):
        raise PermissionError("finite-dt source substitutes the actual original pipeline, semantic verification or recovery")
    verification_publication = supplied.get(scope.recovery)
    if verification_publication is None:
        raise PermissionError("finite-dt source omits its actual original semantic verification publication")
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import authenticate_installed_finite_dt_source_materialization
    authenticate_installed_finite_dt_source_materialization(writer=writer, programme=records["programme"],
        bank=records["bank"], pipeline=pipeline, verification_publication=verification_publication)
    authenticate_instrument_certificate(writer=writer, certificate=records["certificate"],
        programme=records["programme"], bank=records["bank"],
        original_future_reservation=records["original-reservation"], control_reader=reader)
