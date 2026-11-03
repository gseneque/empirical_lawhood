# SPDX-License-Identifier: MPL-2.0
"""Fresh issued selected E4 custody; children receive bounded exact projections."""

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier

from functools import partial
from contextlib import contextmanager

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_protected_workers import SelectedE4ProtectedWorker
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody, CurrentDevelopmentTaskCustody
from .matrix_sampling_runtime import _original_product, _selected_control
from .matrix_selected_runtime import _published_input, _current_source_qualifications
from empirical_lawhood.api.recursive_qualified_parents import MAX_PARENT_BYTES, _ParentReadScope, _output_payload, _semantic_writer
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.kernel.status import OperationalStatus


def development_output_plane(writer,plan,codecs):
    """Validate producers while preserving ordinary development publication.

    Its actual writer owns any semantic registrations present at publication;
    a retained read must not add issued-output requirements retrospectively.
    """
    from empirical_lawhood.api.recursive_operations import development_output_contracts
    development_output_contracts(plan,codecs)
    return writer


def development_product(writer,locator,operation,codecs,*,include_bank=False,read_access=None,_secondary_readout=None):
    return development_products(writer, ((locator, operation),), codecs, include_bank=include_bank,
        read_access=read_access, _secondary_readout=_secondary_readout)[0]


@contextmanager
def _development_replay(writer):
    """Share one complete acquisition replay inside its live custody context."""
    from .selected_e4_method_runtime import original_development_products
    active, cached, accesses = True, [], []

    def current():
        if not active:
            raise PermissionError('selected E4 DEV replay escaped its read lifetime')
        for access in accesses:
            access.require_current(artifact_writer=writer)
        writer.require_verification_snapshot()
        for access in accesses:
            access.require_current(artifact_writer=writer)

    def read(**options):
        current()
        if options['writer'] is not writer:
            raise PermissionError('selected E4 DEV replay changes its custody reader')
        if options['locator'].allow_partial:
            # Partial reads retain their separate original custody route.
            return original_development_products(**options)
        if not cached:
            value = original_development_products(**options, _observe_original_access=accesses.append)
            cached.append((options, value))
        else:
            original, value = cached[0]
            if original != options:
                raise PermissionError('selected E4 DEV replay changes its original acquisition or operands')
        current()
        return value

    try:
        yield read
        current()
    finally:
        active = False


def development_products(writer, requests, codecs, *, include_bank=False, read_access=None, _secondary_readout=None):
    """Authenticate fit/freeze producers together, preserving every local check."""
    requests = tuple(requests)
    if not requests:
        raise ValueError('selected E4 DEV product read needs an explicit producer roster')
    if type(include_bank) is not bool:
        raise TypeError('original DEV bank projection requires explicit bool')
    for locator, _ in requests:
        locator.__post_init__()
    original = requests[0][0]
    if any((locator.authored_directory, locator.run_id, locator.execution_plan) !=
            (original.authored_directory, original.run_id, original.execution_plan) for locator, _ in requests):
        raise PermissionError('selected E4 DEV products change their common original authored run/plan')
    with writer.read_context() as view, _development_replay(view) as replay:
        return _development_products(view, requests, codecs, include_bank=include_bank,
            read_access=read_access, secondary_readout=_secondary_readout, replay=replay)


def _development_products(writer, requests, codecs, *, include_bank, read_access, secondary_readout, replay):
    from .recursive_execution import _read_recursive_wave_with_roots
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    from .selected_e4_method_runtime import authenticate_selected_e4_development_operands
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    directory=writer.root.resolve(requests[0][0].authored_directory,for_write=False)
    retained_payloads = []
    def validate_producer(locator, operation, *, draft, run, plan):
        if (run.run_plan_id!=locator.run_id or r.pin(plan,"execution_plan_id")!=locator.execution_plan
                or draft.development_study is None or draft.prospective_draft is not None):
            raise PermissionError("selected E4 DEV locator changes original authored exposed plan")
        declaration=next(v for v in methods.operation_declarations() if v.capability_key=="matrix-selected-e4."+operation)
        operations=tuple(v for v in draft.operations if v.node_id==locator.task_id)
        tasks=tuple(v for v in plan.tasks if v.task_id==locator.task_id)
        if len(operations)!=1 or len(tasks)!=1 or operations[0].selection!=declaration.registration().selection:
            raise PermissionError("selected E4 DEV product lacks its actual exact original producer")
        task=tasks[0]
        manifest=declaration.manifest()
        if (task.capability.capability_key,task.capability.capability_version,task.capability_implementation_sha256,
                task.capability.requested_outcome_access,task.capability.required_permissions)!=(
                manifest.capability_key,manifest.capability_version,manifest.implementation_sha256,
                OutcomeAccess.DEVELOPMENT_VISIBLE,manifest.permissions):
            raise PermissionError("selected E4 DEV product substitutes original method/config/access")
        actual_outputs=tuple((v.output_id,v.payload_schema,v.profile,v.media_type) for v in task.outputs)
        expected_outputs=tuple(sorted((task.task_id+"."+v.output_id,v.payload_schema,v.profile,v.media_type) for v in declaration.outputs))
        if (actual_outputs!=expected_outputs or task.stage is not declaration.stage
                or (task.capability.config.config_schema,task.capability.config.config_schema_sha256)!=(manifest.config_schema,manifest.config_schema_sha256)):
            raise PermissionError("selected E4 DEV producer changes actual declared output/stage/config census")
        config=decode_recursive_config_input(operations[0],declaration.registration()).record
        return task,config
    def validate_authored(*,packet,draft,source,payloads,run,plan,index):
        prepared = tuple(validate_producer(locator, operation, draft=draft, run=run, plan=plan)
            for locator, operation in requests)
        semantic = development_output_plane(writer, plan, codecs)
        retained_payloads.append(payloads)
        return prepared, semantic
    # The existing contract validator returns this same ordinary writer.
    result,roots,(prepared,semantic)=_read_recursive_wave_with_roots(directory=directory,artifact_writer=writer,
        include_products=True,terminal_product_format="compact",allow_partial=False,validate_authored=validate_authored,read_access=read_access)
    report,products,actual_draft,actual_plan=result
    packet,draft,_,run,plan,_=roots
    if actual_draft!=draft or actual_plan!=plan or report["packet_sha256"]!=packet.fingerprint():
        raise PermissionError("selected E4 DEV product changes its original authored roots")
    payloads, = retained_payloads
    access=getattr(payloads,"original_input_access",None)
    custody=CurrentDevelopmentTaskCustody(writer=semantic,directory=directory,plan=plan,payloads=payloads,
        original_input_access=access,read_access=read_access)
    controls={key:custody._manifest(value.materialization.relative_path,
        expected=ArtifactManifest(value.logical, value.materialization)) for key,value in custody.inputs.items()}
    results = []
    for (locator, _), (task, config) in zip(requests, prepared, strict=True):
        receipt=products["receipts"].get(locator.task_id)
        logical_id=locator.publication.logical.logical_artifact_id
        output=products["outputs"].get(logical_id)
        if (receipt is None or r.pin(receipt,"receipt_id")!=locator.receipt
                or receipt.operational_status is not OperationalStatus.SUCCEEDED or output is None
                or (output.logical,output.materialization)!=(locator.publication.logical,locator.publication.materialization)
                or not any(v.output_id==locator.task_id+".product" and v.logical_artifact_id==logical_id for v in task.outputs)
                or (output.logical.payload_schema,output.logical.content_sha256)!=(locator.record.object_schema,locator.record.object_fingerprint)):
            raise PermissionError("selected E4 DEV product changes exact original receipt/output bytes")
        if access is not None:access.require_current()
        actual_inputs=authenticate_selected_e4_development_operands(writer=semantic,draft=draft,plan=plan,task=task,config=config,
            controls=controls,codecs=codecs,receipts=products["receipts"],_secondary_readout=secondary_readout,
            _original_development_reader=replay)
        programme=actual_inputs["programme"]
        if config.programme!=programme.identity or config.group_ids!=programme.group_ids or draft.development_study.system!=programme.identity:
            raise PermissionError("selected E4 DEV producer changes whole-group programme scope")
        kind=codecs.get(locator.record.object_schema)
        if kind is None:raise PermissionError("selected E4 DEV product lacks its installed original codec")
        if access is not None:access.require_current()
        raw=read_bounded_bytes(semantic.root.resolve(output.materialization.relative_path,for_write=False),maximum_bytes=MAX_PARENT_BYTES)
        record=decode_canonical_bytes(raw,kind,maximum_bytes=MAX_PARENT_BYTES)
        if record.canonical_bytes()!=raw or record.identity!=locator.record:
            raise PermissionError("selected E4 DEV product changes canonical original record")
        authenticate_publication(semantic,locator.publication,record)
        if access is not None:access.require_current()
        results.append((programme,record,actual_inputs["bank"]) if include_bank else (programme,record))
    return tuple(results)


def validate_original_calibration_phase(*,expected_public,confirmation,**kwargs):
    """Existing CAL producer admission plus complete CAL/CONF source separation."""
    from .selected_e4_method_runtime import validate_selected_e4_calibration_producer
    from empirical_lawhood.api.matrix_selected_producer_scope import _read_config
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    validate_selected_e4_calibration_producer(expected_public=expected_public,**kwargs)
    tasks=tuple(v for v in kwargs["execution_plan"].tasks if v.task_id==kwargs["binding"].task_id)
    config=_read_config(kwargs["writer"],kwargs["binding"],tasks[0],methods.SelectedE4MethodConfig)
    entries=tuple(v for v in kwargs["execution_plan"].tasks if v.task_id==config.entry_node_id)
    if len(entries)!=1:raise PermissionError("selected E4 CAL omits actual full source entry")
    original=_read_config(kwargs["writer"],kwargs["binding"],entries[0],owner.SelectedE4ProtectedEntryConfig).programme
    validate_calibration_confirmation_separation(original,confirmation)


def validate_calibration_confirmation_separation(calibration,confirmation):
    if (type(calibration) is not p.SelectedE4PhaseProgramme or type(confirmation) is not p.SelectedE4PhaseProgramme
            or calibration.mode!="E4_REVISION_CALIBRATION" or confirmation.mode!="E4_CONFIRMATION"):
        raise PermissionError("selected E4 requires truthful original CAL and CONF phase types")
    if (calibration.reservation!=confirmation.reservation or calibration.specification!=confirmation.specification
            or calibration.criterion!=confirmation.criterion or calibration.forecast_design!=confirmation.forecast_design
            or calibration.factors!=confirmation.factors or calibration.confidence!=confirmation.confidence
            or set(calibration.group_ids)&set(confirmation.group_ids)
            or {v.root_id for v in calibration.cases}&{v.root_id for v in confirmation.cases}
            or {v.source for v in calibration.cases}&{v.source for v in confirmation.cases}
            or {v.streams_sha256 for v in calibration.cases}&{v.streams_sha256 for v in confirmation.cases}):
        raise PermissionError("selected E4 confirmation changes original CAL target/reservation or reuses groups/sources/streams")

def authenticate_entry(writer,entry,evidence,codecs,*,wave_evidence=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4Calibration
    from .matrix_selected_e3_e4_runtime import authenticate_selected_e3_public_package
    from .matrix_source_runtime import authenticate_matrix_source_qualification
    r.validate_evidence(evidence,entry.programme,entry.bank,entry.decision,entry.models,entry.calibration)
    authenticate_publication(writer,entry.declaration_publication,entry.declaration)
    authenticate_publication(writer,entry.declaration.bank_publication,entry.bank)
    from .matrix_full_factor_secondary import authenticate_e4_secondary_target
    authenticate_e4_secondary_target(writer=writer, selection=entry.secondary_readout, bank=entry.bank)
    public=entry.bank.forecast_design.package
    summary=authenticate_selected_e3_public_package(writer=writer,public=public,
        upstream_products=evidence.upstream_products,codecs=codecs,
        summary_record_id=entry.declaration.original_summary.record_id,
        response_criterion=entry.bank.forecast_design.criterion_record,
        prefix_policies=entry.bank.specification.selection.prefix_policies,
        downstream_coordinates=entry.bank.reservation.allocation.coordinates)
    scope=_ParentReadScope(writer)
    if summary!=entry.declaration.original_summary:
        raise PermissionError("selected E4 changes actual original calibration rank/radius/model/freeze or applicability")
    (development,nomination),(frozen_development,frozen)=development_products(writer,
        ((evidence.development_nomination,'revision-fit'),(evidence.development_freeze,'revision-freeze')),
        codecs,_secondary_readout=entry.secondary_readout)
    p.validate_phase_separation(development,entry.programme)
    if frozen_development!=development:
        raise PermissionError("selected E4 combines revision selection and freeze from different original DEV programmes")
    decision=p.SelectedE4PublicRevisionDecision.from_products(development,nomination,frozen,record_id=entry.decision.record_id)
    models=None if entry.models is None else p.SelectedE4PublicModels.from_products(development,nomination,frozen,record_id=entry.models.record_id)
    if (decision,models)!=(entry.decision,entry.models):
        raise PermissionError("selected E4 entry substitutes original DEV selection/freeze coefficients or disposition")
    if entry.calibration is not None:
        original=evidence.calibration_product
        raw=_original_product(writer,original,original.record,codecs,scope,
            scope_validator=partial(validate_original_calibration_phase,expected_public=entry.calibration,confirmation=entry.programme))
        cal=decode_canonical_bytes(raw,SelectedE4Calibration,maximum_bytes=MAX_PARENT_BYTES)
        if cal.canonical_bytes()!=raw or p.SelectedE4PublicCalibration.from_calibration(cal,record_id=entry.calibration.record_id)!=entry.calibration:
            raise PermissionError("selected E4 CONF changes actual original complete CAL radius/rank/scores")
    source=evidence.source
    authenticate_matrix_source_qualification(writer=writer,specification=source.specification,result=source.result,
        pipeline=source.pipeline,executions=source.executions,publications=source.publications,codecs=codecs,read_scope=scope)

    if entry.wave_id is None:
        from empirical_lawhood.api.selected_e4_native_read import read_selected_e4_wave
        if (type(wave_evidence) is not r.SelectedE4PhaseCollectionEvidence or wave_evidence.identity!=entry.wave_evidence
                or wave_evidence.declaration!=entry.declaration.identity
                or tuple(v.locator.wave_id for v in wave_evidence.waves)!=tuple(v.wave_id for v in entry.programme.waves)):
            raise PermissionError("selected E4 full phase omits original complete wave custody")
        for operand in wave_evidence.waves:
            observation,_=read_selected_e4_wave(writer=writer,declaration=entry.declaration,locator=operand.locator,codecs=codecs)
            if observation.identity!=operand.observation or len(observation.canonical_bytes())!=operand.size_bytes:
                raise PermissionError("selected E4 full phase substitutes original complete/adverse wave observation bytes")
    elif wave_evidence is not None:
        raise PermissionError("selected E4 native wave cannot masquerade as full phase evidence")
    for record,publication in ((entry.bank.reservation.allocation,entry.bank.reservation.publication),
            (entry.bank.specification.selection,entry.bank.specification.publication),(entry.bank.audit,entry.bank.audit_publication),
            (entry.bank.response_selection,entry.bank.response_selection_publication),
            (entry.bank.forecast_design.criterion_record,entry.bank.forecast_design.criterion_publication)):
        authenticate_publication(writer,publication,record)
    for publication in (*entry.bank.audit.prior_corpus,*entry.bank.response_selection.template_publications):
        authenticate_publication(writer,publication)


def expected_entry_seal(entry):
    return r.SelectedE4ProtectedEntrySeal("entry."+entry.programme.programme_id+("" if entry.wave_id is None else "."+entry.wave_id),entry.programme.identity,entry.programme.bank,
        entry.programme.forecast_design,entry.evidence,entry.scope_group_ids,tuple(v.source for v in entry.scope_cases),
        entry.declaration.bank_phase,entry.wave_id,entry.wave_evidence,entry.decision.identity,None if entry.models is None else entry.models.identity,
        None if entry.calibration is None else entry.calibration.identity,entry.secondary_readout.identity)


class SelectedE4ParentEntry:
    """Current local facts composed from exact control and original bank bytes."""
    def __init__(self,configuration,bank):
        if configuration.bank!=bank.identity or configuration.declaration.bank!=bank.identity:
            raise PermissionError("selected E4 current control changes actual whole source bank")
        p.validate_selected_phase_bank(configuration.programme,bank)
        self.configuration,self.bank=configuration,bank
    def __getattr__(self,name):return getattr(self.configuration,name)


def require_selected_e4_native_plan_budget(*,package,plan,entry):
    """Actual issued native cells must equal the frozen full-phase declaration."""
    if package.execution_resource_envelope_spec.maximum_parallel_tasks!=entry.declaration.maximum_parallel_tasks:
        raise PermissionError("selected E4 actual issued concurrency changes frozen operational selection")
    planned=dict(entry.declaration.planned_task_budgets)
    if entry.wave_id is None:
        expected={owner.global_node(entry.programme,v) for v in ("phase-entry","phase-collect")}
    else:
        expected={owner.global_node(entry.programme,v,entry.wave_id) for v in ("entry","reduce","adjudicate")}
        expected.update(owner.local_node(c.root_id,v) for c in entry.scope_cases for v in owner.PHASES if v not in ("entry","reduce"))
    actual={v.task_id:v for v in plan.tasks if v.capability.capability_key.startswith(owner.NAMESPACE+".")}
    if set(actual)!=expected or any(actual[n].capability.requested_resources!=planned[n] for n in expected):
        raise PermissionError("selected E4 actual native task budget/census changes frozen full-phase declaration")

def authenticate_selected_e4_parent(supplier,context,runner):
    """Fresh issue/grants and actual successful entry; returns facts, no token."""
    custody=supplier.custody
    current=custody.current_task(context,runner)
    package,plan,task=current
    receipts,controls=custody.task_inputs(context,task)
    entries=tuple(v for v in plan.tasks if v.capability.capability_key in (owner.NAMESPACE+".entry",owner.NAMESPACE+".phase-entry"))
    if len(entries)!=1:raise PermissionError("selected E4 phase requires exact one current installed source entry")
    entry_task=entries[0]
    specs=tuple(v for v in entry_task.external_inputs if v.logical_artifact_id==entry_task.capability.config.artifact_id)
    if len(specs)!=1:raise PermissionError("selected E4 entry omits automatic exact current configuration")
    entry=_published_input(supplier.writer,context.run_id,specs[0],owner.SelectedE4ProtectedEntryConfig,custody=custody)
    if entry.fingerprint()!=entry_task.capability.config.content_sha256:
        raise PermissionError("selected E4 current original entry changes immutable configuration")
    banks=tuple(v for v in entry_task.external_inputs if v.expected_payload_schema==p.SelectedE4PhaseBank.SCHEMA)
    if len(banks)!=1:raise PermissionError("selected E4 entry lacks exact complete original bank source")
    bank=_published_input(supplier.writer,context.run_id,banks[0],p.SelectedE4PhaseBank,custody=custody)
    entry=SelectedE4ParentEntry(entry,bank)
    require_selected_e4_native_plan_budget(package=package,plan=plan,entry=entry)
    with supplier.writer.verification_scope() as writer:
        if task.task_id==entry_task.task_id:
            _current_source_qualifications(package,task)
            values=tuple(v for v in controls.values() if v.logical.payload_schema==r.SelectedE4ProtectedEvidence.SCHEMA)
            if len(values)!=1:raise PermissionError("selected E4 entry omits original producer/source custody evidence")
            evidence=_selected_control(custody,task,values[0],r.SelectedE4ProtectedEvidence)
            if evidence.identity!=entry.evidence or len(evidence.canonical_bytes())!=entry.evidence_size_bytes:
                raise PermissionError("selected E4 current evidence changes original pin or bounded bytes")
            wave_evidence=None
            if entry.wave_id is None:
                rows=tuple(v for v in controls.values() if v.logical.payload_schema==r.SelectedE4PhaseCollectionEvidence.SCHEMA)
                if len(rows)!=1:raise PermissionError("selected E4 full phase omits current exact wave evidence control")
                wave_evidence=_selected_control(custody,task,rows[0],r.SelectedE4PhaseCollectionEvidence)
                if len(wave_evidence.canonical_bytes())!=entry.wave_evidence_size_bytes:
                    raise PermissionError("selected E4 full phase changes bounded wave evidence size")
            authenticate_entry(writer,entry,evidence,supplier.output_codecs,wave_evidence=wave_evidence)
        else:
            receipt=receipts.get(entry_task.task_id)
            if entry_task.task_id not in task.dependency_task_ids or receipt is None:
                raise PermissionError("selected E4 leaf bypasses actual successful current source entry")
            logicals=tuple(v for v in receipt.output_logical_artifacts if v.payload_schema==r.SelectedE4ProtectedEntrySeal.SCHEMA)
            if len(logicals)!=1 or (logicals[0].outcome_access,logicals[0].visibility_ceiling)!=(r.BLIND,r.PROSPECTIVE):
                raise PermissionError("selected E4 leaf substitutes actual original public entry output")
            semantic=_semantic_writer(package,plan,writer,supplier.output_codecs)
            raw=_output_payload(semantic,receipt,logicals[0],MAX_PARENT_BYTES)
            seal=decode_canonical_bytes(raw,r.SelectedE4ProtectedEntrySeal,maximum_bytes=MAX_PARENT_BYTES)
            if seal!=expected_entry_seal(entry) or seal.canonical_bytes()!=raw:
                raise PermissionError("selected E4 leaf changes exact successful entry source/census/models")
        writer.require_verification_snapshot()
    if custody.current_task(context,runner)!=current:
        raise PermissionError("selected E4 issue/grants/source changed during parent preparation")
    return package,plan,task,receipts,controls,entry


def prepare_selected_e4_protected(supplier,context,runner):
    if type(runner) is not SelectedE4ProtectedWorker or runner.prepared_scope is not None:
        raise PermissionError("selected E4 requires installed unprepared protected worker")
    package,plan,task,_,controls,entry=authenticate_selected_e4_parent(supplier,context,runner)
    kinds={v.config_record_type.SCHEMA:v.config_record_type for v in owner.operation_declarations()}
    selected=controls.get(context.config.artifact_id);kind=None if selected is None else kinds.get(selected.logical.payload_schema)
    if kind is None:raise PermissionError("selected E4 changes installed exact native configuration owner")
    config=_selected_control(supplier.custody,task,selected,kind)
    _current_source_qualifications(package,task)
    if entry.wave_id is None:
        entry_tasks=tuple(v for v in plan.tasks if v.task_id==owner.global_node(entry.programme,"phase-entry"))
        if len(entry_tasks)!=1:raise PermissionError("selected E4 full phase changes actual entry task")
        specs=tuple(v for v in entry_tasks[0].external_inputs if v.expected_payload_schema==r.SelectedE4PhaseCollectionEvidence.SCHEMA)
        if len(specs)!=1:raise PermissionError("selected E4 full phase omits its original wave evidence metadata")
        collection=_published_input(supplier.writer,context.run_id,specs[0],r.SelectedE4PhaseCollectionEvidence,custody=supplier.custody)
        expected=dict(owner.phase_collect_contracts(entry.configuration,collection)[0])
    else:
        expected=dict(owner.contracts(entry.programme,entry.bank,entry.evidence,entry.evidence_size_bytes,
            entry.decision,entry.models,entry.calibration,entry.declaration,entry.declaration_publication,entry.wave_id,
            secondary_readout=entry.secondary_readout,referenced_models=any(value.capability.config.config_schema in (owner.SelectedE4ProtectedReferencedConfig.SCHEMA,
                owner.SelectedE4ProtectedReferencedPublicConfig.SCHEMA,owner.SelectedE4ProtectedProtocolConfig.SCHEMA,
                owner.SelectedE4ProtectedProtocolPublicConfig.SCHEMA) for value in plan.tasks),
            compact_protocol=any(value.capability.config.config_schema in (owner.SelectedE4ProtectedProtocolConfig.SCHEMA,
                owner.SelectedE4ProtectedProtocolPublicConfig.SCHEMA) for value in plan.tasks))[0])
    if config!=expected.get(context.task_id) or config.fingerprint()!=context.config.content_sha256:
        raise PermissionError("selected E4 changes complete parent-derived original wave source/config")
    if owner.referenced_config(config):
        rows=tuple(value for value in controls.values() if value.logical.payload_schema==p.SelectedE4PublicModels.SCHEMA)
        if len(rows)!=1:raise PermissionError("selected E4 leaf omits its exact shared frozen public models")
        models=_selected_control(supplier.custody,task,rows[0],p.SelectedE4PublicModels)
        if models!=entry.models:raise PermissionError("selected E4 leaf changes actual entry-authenticated public models")
        owner.bind_selected_e4_models(config,models)
    if owner.native_config(config):
        from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source
        rows=tuple(v for v in controls.values() if v.logical.payload_schema==NumericalProducingProvenance.SCHEMA)
        if len(rows)!=1:
            raise PermissionError("selected E4 protected leaf loses exact standalone original provenance input")
        provenance=_selected_control(supplier.custody,task,rows[0],NumericalProducingProvenance)
        original=next(v for v in entry.bank.provenances if v.identity==config.source.provenance)
        if provenance!=original:
            raise PermissionError("selected E4 protected leaf substitutes full original producing provenance")
        bind_selected_native_source(config.source,provenance)
    return runner.with_prepared_scope((context.run_id,context.task_id,context.input_materialization_ids,
        ObjectIdentity.from_record(plan.execution_plan_id,plan)))


class SelectedE4RuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self,supplier,*,writer,output_codecs,reveal_authority_id=None,custody=None):
        self.supplier,self.writer,self.output_codecs,self.reveal_authority_id=supplier,writer,dict(output_codecs),reveal_authority_id
        if custody is not None and (type(custody) is not CurrentIssuedTaskCustody
                or custody.writer is not writer or custody.reveal_authority_id!=reveal_authority_id):
            raise TypeError("selected E4 shared custody changes its exact writer or reveal selection")
        self.custody=CurrentIssuedTaskCustody(writer=writer,reveal_authority_id=reveal_authority_id) if custody is None else custody
    def resolve_input(self,spec):return self.supplier.resolve_input(spec)
    def prepare_selected_e4_protected(self,context,runner):
        with self.custody.preparation_scope():
            return prepare_selected_e4_protected(self,context,runner)
    def prepare_selected_e4_method(self,context,runner):
        from .selected_e4_method_runtime import prepare_selected_e4_method
        with self.custody.preparation_scope():
            return prepare_selected_e4_method(self,context,runner)


def bind_selected_e4_handoff(handoff,*,writer,reveal_authority_id=None):
    from dataclasses import replace
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    from empirical_lawhood.api.recursive_operations import operation_catalog
    codecs=operation_catalog()[2]
    ports=[]
    custody=CurrentIssuedTaskCustody(writer=writer,reveal_authority_id=reveal_authority_id)
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("selected E4 handoff changes exact installed scientific operand supplier")
        supplier=SelectedE4RuntimeInputSupplier(platform.port.supplier,writer=writer,output_codecs=codecs,
            reveal_authority_id=reveal_authority_id,custody=custody)
        ports.append(ExecutablePlatformPort(platform.port_key,RecursiveOperationInputPort(supplier)))
    return replace(handoff,platform_ports=tuple(ports))
