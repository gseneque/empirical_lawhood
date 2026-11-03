# SPDX-License-Identifier: MPL-2.0
"""Genuine current and original custody for selected E4 revision E5/E6 work.

Current DEV and issued custody remain distinct. Complete original DEV, CAL and
CONF readers run only at entry; later leaves require that actual successful
entry receipt plus fresh current task/source/grant authentication.
"""
from dataclasses import replace
from functools import partial
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier
from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody, CurrentIssuedTaskCustody
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import is_baseline_recipe
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixRevisionEntryEvidenceV2, MatrixRevisionRootConfigV2
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionRootConfig, MatrixRevisionEntrySeal, entry_seal
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_entry import validate_entry_evidence
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_workers import SelectedRevisionWorker
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import MatrixRevisionProgrammeAssessment
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as public_e4
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4Calibration, SelectedE4DownstreamNomination
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as original_identity
from empirical_lawhood.api.matrix_sampling_runtime import _original_product
from empirical_lawhood.api.matrix_selected_runtime import _current_source_qualifications, _issued_configuration_lane, _published_input
from empirical_lawhood.api.matrix_source_runtime import authenticate_matrix_source_qualification, matrix_source_publication_references
from empirical_lawhood.api.recursive_qualified_parents import MAX_PARENT_BYTES, _output_payload, _semantic_writer
from empirical_lawhood.api.selected_e4_native_runtime import development_products
from empirical_lawhood.api.selected_e4_method_runtime import validate_selected_e4_calibration_producer, validate_selected_e4_downstream_producer
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.metatheory import MetatheoryAggregateDisposition, MetatheoryApplicability
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateKind


def _decode_original(raw, kind, expected):
    record = decode_canonical_bytes(raw, kind, maximum_bytes=MAX_PARENT_BYTES)
    if record.canonical_bytes() != raw or ObjectIdentity.from_record(record.record_id, record) != expected:
        raise PermissionError("revision entry substitutes original scientific record bytes")
    return record


def _source_scope(programme, evidence):
    if programme.phase == "E5_OPPORTUNITY":
        return
    closure = programme.sources.closure
    spec, result = evidence.source_specification, evidence.source_result
    groups = tuple(sorted({source.root.root.independent_group_id for _, source in programme.source_arms()}))
    if (spec.source_identity != closure.identity or spec.preparation != programme.sources.identity
            or spec.observation_operator != programme.assay.identity or spec.numerical_view != closure.numerical_scope
            or spec.physical_unit_ids != groups or spec.expected_physical_unit_count != len(groups)
            or spec.maximum_ordinary_evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
            or spec.outcome_access is not OutcomeAccess.OUTCOME_BLIND or spec.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or result.qualification_spec != ObjectIdentity.from_record(spec.spec_id, spec)
            or spec.source_pipeline_qualification != ObjectIdentity.from_record(evidence.pipeline.receipt.receipt_id, evidence.pipeline.receipt)
            or result.source_pipeline_qualification != spec.source_pipeline_qualification
            or result.disposition is not MetatheoryAggregateDisposition.SUPPORTED
            or result.complete_physical_unit_count != len(groups) or result.invalid_physical_unit_count != 0
            or result.eligible_physical_unit_count != len(groups)):
        raise PermissionError("revision protected entry lacks exact complete genuinely supported source/assay/numerical scope")
    required = set(ScientificSourceGateKind) - {ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE}
    gates = {gate.gate_kind: gate for gate in spec.gates}
    if any(gates[kind].applicability is not MetatheoryApplicability.REQUIRED or closure.identity not in gates[kind].required_operands for kind in required):
        raise PermissionError("revision source omits an independent required scientific gate")
    if (programme.sources.identity not in gates[ScientificSourceGateKind.PREPARATION].required_operands
            or programme.assay.identity not in gates[ScientificSourceGateKind.OBSERVATION_OPERATOR].required_operands
            or closure.numerical_scope not in gates[ScientificSourceGateKind.NUMERICAL_OR_INSTRUMENT_VALIDITY].required_operands):
        raise PermissionError("revision source gates omit actual preparation/observation/numerical operands")


def _development_nomination(writer, locator, programme, codecs,*,current_access=None):
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_roots
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    locator.__post_init__()
    directory = writer.root.resolve(locator.authoring_relative_path, for_write=False)
    def validate_authored(*, packet, draft, source, payloads, run, plan, index):
        if (ObjectIdentity.from_record(packet.packet_id, packet) != locator.authored_wave
                or ObjectIdentity.from_record(run.run_plan_id, run) != locator.run_plan
                or ObjectIdentity.from_record(plan.execution_plan_id, plan) != locator.execution_plan
                or run.run_plan_id != locator.run_id or draft.development_study is None or draft.prospective_draft is not None):
            raise PermissionError("revision recipe nomination substitutes original DEV packet/run/plan")
        declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.capability_key("assess-programme", "DEVELOPMENT"))
        operations = tuple(value for value in draft.operations if value.node_id == locator.task_id)
        tasks = tuple(value for value in plan.tasks if value.task_id == locator.task_id)
        if len(operations) != 1 or len(tasks) != 1 or operations[0].selection != declaration.registration().selection:
            raise PermissionError("revision recipe nomination lacks its exact original installed complete DEV producer")
        task, manifest = tasks[0], declaration.manifest()
        if ((task.capability.capability_key, task.capability.capability_version, task.capability_implementation_sha256,
                task.capability.requested_outcome_access, task.capability.required_permissions, task.stage) !=
                (manifest.capability_key, manifest.capability_version, manifest.implementation_sha256,
                    declaration.outcome_access, manifest.permissions, declaration.stage)
                or (task.capability.config.config_schema, task.capability.config.config_schema_sha256) !=
                    (manifest.config_schema, manifest.config_schema_sha256)
                or tuple((row.output_id, row.payload_schema, row.profile, row.media_type) for row in task.outputs) !=
                    tuple(sorted((task.task_id + "." + row.output_id, row.payload_schema, row.profile, row.media_type)
                        for row in declaration.outputs))):
            raise PermissionError("revision recipe producer substitutes its exact installed task/output/config/access census")
        config = decode_recursive_config_input(operations[0], declaration.registration()).record
        original = config.programme
        if (config.phase != "assess-programme" or original.phase != "E5_OPPORTUNITY"
                or original.selected_package != programme.selected_package or original.criterion != programme.criterion
                or draft.development_study != owner.development_root(original, draft.development_study.study_id)):
            raise PermissionError("revision recipe nomination changes exact model selection, criterion or complete DEV root")
        from empirical_lawhood.api.selected_e4_native_runtime import development_output_plane
        semantic = development_output_plane(writer, plan, codecs)
        return semantic

    result, roots, _ = _read_recursive_wave_with_roots(directory=directory, artifact_writer=writer,
        include_products=True, terminal_product_format="references", allow_partial=False, validate_authored=validate_authored,read_access=current_access)
    packet, draft, _source, _run, plan, _index = roots
    report, products, actual_draft, actual_plan = result
    receipt = products["receipts"].get(locator.task_id)
    manifest = products["outputs"].get(locator.logical_artifact_id)
    if (actual_draft != draft or actual_plan != plan or report["packet_sha256"] != packet.fingerprint()
            or receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or ObjectIdentity.from_record(receipt.receipt_id, receipt) != locator.receipt
            or manifest is None or (manifest.logical, manifest.materialization) != (locator.publication.logical, locator.publication.materialization)):
        raise PermissionError("revision recipe nomination changes actual complete producing receipt/publication")
    result = products["records"].get(locator.task_id, {}).get(locator.task_id + ".product")
    if type(result) is not MatrixRevisionProgrammeAssessment or ObjectIdentity.from_record(result.record_id, result) != locator.record:
        raise PermissionError("revision recipe nomination changes its actual complete original result")
    nominated = result.functional
    selected = tuple((arm, recipe) for arm, recipe in programme.arms if not is_baseline_recipe(recipe))
    if (nominated.disposition != "NOMINATED" or len(selected) != 1
            or (nominated.selected_arm_id, nominated.selected_recipe) != (selected[0][0], selected[0][1].identity)
            or nominated.hold_recipe != dict(programme.arms)[programme.hold_arm_id].identity
            or set(nominated.development_unit_ids).intersection(source.root.root.independent_group_id for _, source in programme.source_arms())):
        raise PermissionError("revision CONF changes its actual nominated recipe or reuses DEV groups")
    return nominated


def _require_original_transfer_reserve(original_e3, programme):
    if programme.phase != "E6_TRANSFER":
        return
    closure = programme.sources.closure
    reservation = original_identity(closure.reservation)
    if (closure.reservation != programme.reservation
            or reservation != original_e3.prefit.reservation
            or original_identity(closure.reservation.allocation) != original_e3.prefit.original_allocation):
        raise PermissionError("revision transfer substitutes the original pre-fit reservation or allocation")
    rows = programme.source_arms()
    groups = tuple(sorted(source.root.root.independent_group_id for _, source in rows))
    try:
        original_e3.require_reserved_transfer_groups(groups, reservation=reservation)
    except ValueError as error:
        raise PermissionError("revision transfer changes the complete original pre-fit reserve") from error
    regimes = {}
    for _, source in rows:
        root = source.root.root
        regimes.setdefault(root.regime_id, set()).add(root.independent_group_id)
    partitions = tuple(frozenset(original_e3.allocation.unit_ids(role))
        for role in ("transfer_nearby", "transfer_shifted"))
    if (any(len(groups) != programme.expected_groups for groups in partitions)
            or len(regimes) != 2 or len(set(partitions)) != 2
            or {frozenset(groups) for groups in regimes.values()} != set(partitions)):
        raise PermissionError("revision transfer changes its original nearby and shifted whole-group partitions")


def revision_original_operands(writer, programme, evidence, codecs, *, include_original_allocation=False,current_access=None):
    """Authenticate actual prior producers and derive their complete used groups.

    This projection creates no current source/entry authority or producer claim.
    """
    if type(include_original_allocation) is not bool:
        raise TypeError("revision original allocation selection must be a boolean")
    validate_entry_evidence(evidence, programme)
    from .selected_prepared_access import _selected
    selected={value.record:value for value in _selected(tuple(sorted((evidence.calibration,evidence.downstream_nomination),key=lambda value:value.record.object_id)),current_access)}
    development_access=None if current_access is None else current_access.development_access()
    (development, nomination, original_bank), (frozen_development, frozen, frozen_bank) = development_products(writer,
        ((evidence.revision_fit, 'revision-fit'), (evidence.revision_freeze, 'revision-freeze')),
        codecs, include_bank=True, read_access=development_access)
    original_e3 = original_bank.forecast_design.package
    if (frozen_development != development or frozen_bank != original_bank or original_bank.identity != development.bank
            or original_e3.original_package != evidence.original_e3_package):
        raise PermissionError("revision entry mixes original DEV or E3 source programmes")
    _require_original_transfer_reserve(original_e3, programme)
    export = public_e4.SelectedE4RevisionExport.from_products(development, nomination, frozen, record_id=evidence.revision_export.object_id)
    if export.identity != evidence.revision_export or export.models is None:
        raise PermissionError("revision entry changes the actual frozen DEV model export or invents an unentered branch")
    payload = SelectedE4PointModels.from_models(export.models, record_id=programme.selected_package.models.record_id)
    if (payload != programme.selected_package.models or payload.relation_fit is not None
            and programme.selected_package.reference_package != original_e3):
        raise PermissionError("revision entry changes actual fitted coefficients or their exact public projection")
    scope = None
    raw = _original_product(writer, selected[evidence.calibration.record], evidence.calibration.record, codecs, scope,
        scope_validator=partial(validate_selected_e4_calibration_producer, expected_public=evidence.public_calibration))
    calibration = _decode_original(raw, SelectedE4Calibration, evidence.calibration.record)
    public_calibration = public_e4.SelectedE4PublicCalibration.from_calibration(calibration, record_id=evidence.public_calibration.record_id)
    if (public_calibration != evidence.public_calibration
            or payload.relation_fit is not None and programme.selected_package.frozen_calibration != public_calibration):
        raise PermissionError("revision entry changes the actual original CAL summary")
    raw = _original_product(writer, selected[evidence.downstream_nomination.record], evidence.downstream_nomination.record, codecs, scope,
        scope_validator=partial(validate_selected_e4_downstream_producer, expected_revision=export,
            expected_calibration=public_calibration, expected_e3_package=evidence.original_e3_package))
    selected = _decode_original(raw, SelectedE4DownstreamNomination, evidence.downstream_nomination.record)
    if (selected.selected != "REVISION" or selected.frozen_revision != payload.frozen
            or selected.calibration != programme.selected_package.original_calibration
            or selected.calibration_product != public_calibration or selected.frozen_product != export.decision):
        raise PermissionError("revision entry substitutes the actual complete CONF nomination or E3 fallback")
    used = {*original_e3.training_unit_ids, *original_e3.selection_unit_ids,
        *development.group_ids, *public_calibration.group_ids,
        *(row.independent_group_id for row in selected.confirmation_product.groups)}
    if programme.phase == "E5_CONFIRMATION":
        nomination = _development_nomination(writer, evidence.preparation_nomination, programme, codecs,current_access=current_access)
        used.update(nomination.development_unit_ids)
    used = tuple(sorted(used))
    return (used, original_e3.allocation) if include_original_allocation else used


def authenticate_revision_source_custody(writer, programme, evidence, codecs, *, current_access=None):
    """Replay exact current source custody after caller-owned prior-producer joins.

    This returns no authority or cached producer verdict. Public composition
    must independently authenticate the actual original used-group census.
    """
    validate_entry_evidence(evidence, programme)
    _source_scope(programme, evidence)
    if programme.phase != "E5_OPPORTUNITY":
        references = matrix_source_publication_references(evidence.source_specification, evidence.source_result, evidence.pipeline)
        from .prepared_source_replay import is_prepared_source_result, partition_prepared_source_publications
        if is_prepared_source_result(evidence.source_result):
            scientific, bootstrap = partition_prepared_source_publications(writer=writer,
                publications=evidence.publications)
        else:
            scientific, bootstrap = evidence.publications, ()
        publications = dict(scientific)
        if set(publications) != set(references):
            raise PermissionError("revision source custody drops or adds an original publication")
        authenticate_matrix_source_qualification(writer=writer, specification=evidence.source_specification,
            result=evidence.source_result, pipeline=evidence.pipeline, executions=evidence.qualification_executions,
            publications=tuple(sorted((*scientific, *bootstrap), key=lambda row: row[0].object_id)),
            codecs=codecs, read_scope=None, consumer_programme=programme,
            prepared_source_current_access=current_access)


def authenticate_revision_entry(writer, programme, evidence, codecs, *, source_scan_bytes, include_original_allocation=False,current_access=None):
    if type(include_original_allocation) is not bool:
        raise TypeError("revision original allocation selection must be a boolean")
    from empirical_lawhood.api.matrix_prepared_original_commitments import authenticate_prepared_original_commitments
    authenticate_prepared_original_commitments(writer=writer, programme=programme, evidence=evidence, source_scan_bytes=source_scan_bytes,
            **({} if current_access is None else {"current_access":current_access}))
    used, allocation = revision_original_operands(writer, programme, evidence, codecs, include_original_allocation=True,current_access=current_access)
    if programme.excluded_group_ids != used:
        raise PermissionError("revision entry substitutes the complete actual prior DEV/CAL/CONF group census")
    authenticate_revision_source_custody(writer, programme, evidence, codecs, current_access=current_access)
    seal = entry_seal(programme)
    return (seal, allocation) if include_original_allocation else seal


class RevisionRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self, supplier, *, writer, output_codecs, directory=None, plan=None, reveal_authority_id=None, custody=None,payloads=None,read_access=None,original_input_access=None):
        if custody is not None and (directory is not None or type(custody) is not CurrentIssuedTaskCustody
                or custody.writer is not writer or custody.reveal_authority_id != reveal_authority_id):
            raise TypeError("revision custody changes its exact issued lifecycle, writer or reveal selection")
        if custody is not None and getattr(custody,"original_input_access",None) is not original_input_access:
            raise TypeError("revision custody substitutes its actual original input scope")
        self.supplier, self.writer, self.output_codecs = supplier, writer, dict(output_codecs)
        self.current_access=read_access if original_input_access is None else original_input_access.current_access
        self.original_input_access=original_input_access
        if directory is not None:
            if payloads is None:
                from .recursive_authoring import load_authored_wave
                _,_,_,payloads=load_authored_wave(directory=directory,artifact_writer=writer,lazy_payloads=True,read_access=read_access)
            self.original_input_access=getattr(payloads,'original_input_access',None)
            if self.original_input_access is None:raise PermissionError("revision DEV lacks its actual original-parent bootstrap")
            self.original_input_access.require_current()
        self.development_custody = None if directory is None else CurrentDevelopmentTaskCustody(writer=writer, directory=directory, plan=plan,
            payloads=payloads,original_input_access=self.original_input_access,read_access=read_access)
        self.reveal_authority_id = reveal_authority_id
        self.custody = None if self.development_custody is not None else (
            custody if custody is not None else CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id,original_input_access=self.original_input_access))

    def resolve_input(self, spec):
        return self.supplier.resolve_input(spec)

    def resolve(self, logical_artifact_ids):
        return self.supplier.resolve(logical_artifact_ids)

    def require_original_input_access(self,task,value):
        if self.development_custody is None:raise PermissionError("issued original-parent custody requires its explicit shared admission owner")
        return self.development_custody.require_original_input_access(task,value)

    def require_native_entry(self,context,runner,*,prepared_contract):
        custody=self.development_custody or self.custody
        return custody.require_native_entry(context,runner,prepared_contract=prepared_contract)

    def prepare_selected_revision(self, context, runner):
        if self.development_custody is not None:
            return self._prepare_selected_revision(context, runner)
        with self.custody.preparation_scope():
            return self._prepare_selected_revision(context, runner)

    def _prepare_selected_revision(self, context, runner):
        if type(runner) is not SelectedRevisionWorker or runner.prepared_scope is not None:
            raise PermissionError("revision preparation requires its exact installed unprepared worker")
        if (runner.lane == "DEVELOPMENT") != (self.development_custody is not None):
            raise PermissionError("revision preparation cannot coerce DEV and issued custody")
        custody = self.development_custody or self.custody
        if self.original_input_access is not None:self.original_input_access.require_current()
        current = custody.current_task(context, runner)
        package, plan, task = current
        receipts, controls = custody.task_inputs(context, task)
        kinds = {row.config_record_type.SCHEMA: row.config_record_type for row in owner.operation_declarations()}
        manifest = controls.get(context.config.artifact_id)
        kind = None if manifest is None else kinds.get(manifest.logical.payload_schema)
        if kind is None:
            raise PermissionError("revision task changes its registered configuration codec")
        config = custody.control_record(manifest, kind, manifest.materialization.size_bytes,
            **({} if runner.lane=='DEVELOPMENT' else _issued_configuration_lane(task)))
        if config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id:
            raise PermissionError("revision task changes the actual selected immutable configuration")
        entries = tuple(row for row in plan.tasks if row.capability.capability_key == owner.capability_key("entry", runner.lane, "2.0.0"))
        if len(entries) != 1:
            raise PermissionError("revision plan needs one exact installed entry task")
        entry, = entries
        original_allocation = None
        if runner.phase == "entry":
            if type(config) is not MatrixRevisionRootConfigV2 or task != entry or owner.lane_of(config.programme) != runner.lane:
                raise PermissionError("revision entry changes the actual complete programme/lifecycle")
            if runner.lane == "PROTECTED":
                _current_source_qualifications(package, task)
            evidence_kind = MatrixRevisionEntryEvidenceV2
            values = tuple(value for value in controls.values() if value.logical.payload_schema == evidence_kind.SCHEMA)
            if len(values) != 1:
                raise PermissionError("revision entry omits its exact original producer/source evidence")
            if runner.lane == "DEVELOPMENT":
                evidence = custody.control_record(values[0], evidence_kind, values[0].materialization.size_bytes)
            else:
                evidence_specs=tuple(spec for spec in task.external_inputs
                    if (spec.expected_payload_schema,spec.expected_content_sha256)==(
                        evidence_kind.SCHEMA,config.entry_evidence.object_fingerprint))
                if len(evidence_specs)!=1:
                    raise PermissionError("revision entry omits its exact frozen original evidence input")
                evidence=_published_input(self.writer,context.run_id,evidence_specs[0],evidence_kind,custody=custody)
            if evidence.identity != config.entry_evidence:
                raise PermissionError("revision entry changes its selected original evidence")
            _, original_allocation = authenticate_revision_entry(self.writer, config.programme, evidence, self.output_codecs,
                source_scan_bytes=context.resource_budget.source_scan_bytes, include_original_allocation=True,current_access=self.current_access)
            from .domain_composition.matrix_selected_declarative.derivation import require_evidence_produced_input_parents
            require_evidence_produced_input_parents(self.writer, config.produced_input_parents, evidence,read_access=self.current_access)
        else:
            with self.writer.verification_scope() as writer:
                receipt = receipts.get(entry.task_id)
                if entry.task_id not in task.dependency_task_ids or receipt is None:
                    raise PermissionError("revision leaf lacks its actual successful entry dependency")
                logicals = tuple(value for value in receipt.output_logical_artifacts if value.payload_schema == MatrixRevisionEntrySeal.SCHEMA)
                if len(logicals) != 1:
                    raise PermissionError("revision entry lacks its exact one actual seal output")
                semantic = writer if runner.lane == "DEVELOPMENT" else _semantic_writer(package, plan, writer, self.output_codecs)
                if self.original_input_access is None:
                    raw = _output_payload(semantic, receipt, logicals[0], MAX_PARENT_BYTES)
                else:
                    from .selected_prepared_access import guarded_output_payload
                    raw=guarded_output_payload(semantic,receipt,logicals[0],MAX_PARENT_BYTES,self.original_input_access)
                seal = decode_canonical_bytes(raw, MatrixRevisionEntrySeal, maximum_bytes=MAX_PARENT_BYTES)
                if seal.canonical_bytes() != raw:
                    raise PermissionError("revision entry seal changes its original canonical bytes")
                programme_pin = config.programme.identity if type(config) is MatrixRevisionRootConfig else getattr(config, "programme", None)
                source = getattr(config, "source", getattr(config, "public_source", None))
                if programme_pin is not None and programme_pin != seal.programme:
                    raise PermissionError("revision leaf substitutes its original entry-bound programme")
                if source is not None and (source.source_id if hasattr(source, "source_id") else source.source.object_id) not in seal.source_ids:
                    raise PermissionError("revision leaf substitutes an unselected original prepared source")
                selected = getattr(config, "selected_package", None)
                if selected is not None and (selected if type(selected) is ObjectIdentity else selected.identity) != seal.selected_package:
                    raise PermissionError("revision leaf substitutes its actual admitted E4 model package")
                writer.require_verification_snapshot()
        if custody.current_task(context, runner) != current:
            raise PermissionError("revision current grant/source/packet changed during parent preparation")
        if self.original_input_access is not None:self.original_input_access.require_current()
        return runner.with_prepared_scope((context.run_id, context.task_id, context.input_materialization_ids,
            ObjectIdentity.from_record(plan.execution_plan_id, plan)), original_allocation=original_allocation)


def bind_revision_handoff(handoff, *, writer, output_codecs, reveal_authority_id=None,original_input_access=None,read_access=None):
    from empirical_lawhood.api.recursive_prospective_authoring import RecursiveProspectiveApplicationHandoff
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    if type(handoff) is not RecursiveProspectiveApplicationHandoff:
        raise TypeError("revision protected binding requires its exact actual prospective handoff")
    if not any(type(row.record) is MatrixRevisionRootConfigV2 and row.record.phase == "entry" and owner.lane_of(row.record.programme) == "PROTECTED"
            for row in handoff.compilation.config_inputs):
        raise PermissionError("revision protected handoff lacks its actual complete programme entry")
    custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id,original_input_access=original_input_access)
    ports = []
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("revision handoff changes its actual registered input port")
        supplier = RevisionRuntimeInputSupplier(platform.port.supplier, writer=writer, output_codecs=output_codecs,
            reveal_authority_id=reveal_authority_id, custody=custody,original_input_access=original_input_access,read_access=read_access)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))


def bind_revision_development(*, supplier, writer, directory, plan, output_codecs,payloads=None,read_access=None):
    return RevisionRuntimeInputSupplier(supplier, writer=writer, directory=directory, plan=plan, output_codecs=output_codecs,payloads=payloads,read_access=read_access)
