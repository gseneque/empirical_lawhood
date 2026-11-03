# SPDX-License-Identifier: MPL-2.0
"""Ordinary E4 structural completion over its actual retained original evidence.

The existing full-factor PURE producer and independent reader own mathematics,
arrays and receipts. This composition supplies the phase's predeclared choices;
it creates no native entry, issue, qualification or outcome-access authority.
"""
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as full
from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as workers
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as development
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as original_workers
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import SelectedE4DevelopmentAcquisition
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_structure import structural_measurement
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, ExperimentInstanceBinding
from empirical_lawhood.runtime.prospective_experiment import source_filename


def _pin(value, field):
    return ObjectIdentity.from_record(getattr(value, field), value)


def structure_projection(result):
    """Expose the complete structural result without copying its response again."""
    return {key: value for key, value in result.items()
        if key not in ("original_response", "original_wave_observations")}


def _development_inputs(specification, instance, payloads):
    if (type(specification) is not development.SelectedE3E4ExperimentSpecification
            or type(instance) is not ExperimentInstanceBinding or instance.specification != specification.identity):
        raise PermissionError("ordinary E4 structure changes its actual original DEV companion")
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection
    kinds = (*development._scientific_input_types(), MatrixE4SecondaryReadoutSelection)
    records = {}
    for reference in instance.sources:
        selected = tuple(kind for kind in kinds
            if (kind.SCHEMA, kind.VERSION) == (reference.object_schema, reference.object_version))
        if len(selected) != 1 or selected[0] in records:
            raise PermissionError("ordinary E4 structure changes its complete actual source roster")
        kind, = selected
        raw = payloads[source_filename(reference)]
        record = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        if record.canonical_bytes() != raw or ObjectIdentity.from_record(reference.object_id, record) != reference:
            raise PermissionError("ordinary E4 structure substitutes actual companion source bytes")
        records[kind] = record
    if set(records) != set(kinds):
        raise PermissionError("ordinary E4 structure omits an actual scientific source")
    inputs = development.SelectedE3E4Inputs(*(records[kind] for kind in development._scientific_input_types()),
        secondary_readout=records[MatrixE4SecondaryReadoutSelection])
    inputs.secondary_readout.validate_target(specification.structure.secondary_target)
    for role in ("programme", "bank", "evidence", "campaign"):
        record = getattr(inputs, role)
        field = {"programme": "programme_id", "bank": "bank_id", "evidence": "record_id", "campaign": "campaign_id"}[role]
        if _pin(record, field) != getattr(specification, role):
            raise PermissionError("ordinary E4 structure substitutes actual selected " + role)
    structural_measurement(programme=inputs.programme, bank=inputs.bank, choices=specification.structure)
    return inputs


def _directory(writer, directory):
    directory = Path(directory)
    if not directory.is_absolute() or any(path.is_symlink() for path in (directory, *directory.parents)):
        raise ValueError("ordinary E4 structure requires its exact unlinked authored directory")
    root = Path(writer.root.contract.canonical_path)
    relative = (directory / "structure").relative_to(root).as_posix()
    return writer.root.resolve(relative, for_write=False)


def _acquisition(*, directory, writer, programme, report, products, plan):
    receipt = products["receipts"].get(original_workers.global_node(programme, "entry"))
    if receipt is None:
        raise PermissionError("ordinary E4 structure lacks its actual successful source-entry receipt")
    relative = Path(directory).resolve(strict=True).relative_to(writer.root.contract.canonical_path).as_posix()
    return SelectedE4DevelopmentAcquisition("acquisition." + plan.fingerprint(), relative, report["run_id"],
        _pin(plan, "execution_plan_id"), _pin(receipt, "receipt_id"), False)


def _campaign(original, scope, resources):
    study = workers.development_root(scope, study_id="study.full-factor." + scope.programme.programme_id)
    budgets = dict(resources.phase_budgets)
    return replace(original, campaign_id="campaign.e4.structure." + scope.programme.fingerprint(),
        objective=study.question, system_ids=(study.system.object_id,), world_ids=(study.world_id,),
        target_claim_ids=tuple(sorted(claim.claim_id for claim in study.claims)),
        budget=ResourceBudget.aggregate((*((budgets["measure"], budgets["assess"]) * len(scope.sources)), budgets["reduce"])))


def _structural_companion(*,payloads,programme,bank,choices,secondary_readout,resources,campaign,original,declaration,current_access,measurement):
    from empirical_lawhood.api.matrix_full_factor_read import _inputs
    protected=declaration is not None
    kind=full.ScheduledFullFactorProtectedSpecification if protected else full.ScheduledFullFactorDevelopmentSpecification
    raw=payloads['experiment-specification.json']
    specification=decode_canonical_bytes(raw,kind,maximum_bytes=len(raw))
    raw=payloads['experiment-instance.json']
    instance=decode_canonical_bytes(raw,ExperimentInstanceBinding,maximum_bytes=len(raw))
    inputs=_inputs(specification,instance,payloads)
    _require_structural_inputs(specification=specification,inputs=inputs,programme=programme,bank=bank,
        choices=choices,secondary_readout=secondary_readout,resources=resources,campaign=campaign,original=original,declaration=declaration,
        current_access=current_access,measurement=measurement)
    return specification,instance,inputs


def _require_structural_inputs(*,specification,inputs,programme,bank,choices,secondary_readout,resources,campaign,
        original,declaration,current_access,measurement):
    protected=declaration is not None
    request=inputs.request
    request_kind=full.ScheduledFullFactorProtectedRequestV4 if protected else full.ScheduledFullFactorDevelopmentRequestV3
    if (type(request) is not request_kind or inputs.programme!=programme or inputs.bank!=bank
            or inputs.resources!=resources or specification.measurement!=measurement
            or inputs.campaign!=_campaign(campaign,inputs.reference,resources)
            or specification.specification_id!='experiment.e4.structure.'+programme.fingerprint()
            or request.secondary_readout!=secondary_readout
            or request.secondary_readout.target!=choices.secondary_target.identity
            or (protected and request.declaration!=declaration.identity)
            or (not protected and request.original!=original)):
        raise PermissionError('ordinary E4 structure changes its exact phase, original custody, choices or reservations')
    if protected:
        current_access.require_originals(request.waves)


def _retained_structure_preparation(*,directory,writer,programme,bank,choices,secondary_readout,resources,campaign,
        original,declaration,current_access,measurement,execution):
    """Reuse exact derived inputs under fresh original access before body hashing."""
    from empirical_lawhood.api.experiment_preparation import _input_member,load_experiment_inputs,prepare_experiment
    from empirical_lawhood.api.matrix_full_factor_access import development_original_access,protected_original_access
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    protected=declaration is not None
    kind=full.ScheduledFullFactorProtectedSpecification if protected else full.ScheduledFullFactorDevelopmentSpecification
    request_kind=full.ScheduledFullFactorProtectedRequestV4 if protected else full.ScheduledFullFactorDevelopmentRequestV3
    metadata=[]
    def locator(path,record_kind):
        manifest=writer.read_manifest(path.relative_to(writer.root.contract.canonical_path).as_posix())
        if (manifest.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE or manifest.logical.lineage_parents):
            raise PermissionError('retained E4 bootstrap changes its exact outcome-blind locator contract')
        raw=read_bounded_bytes(path,maximum_bytes=manifest.materialization.size_bytes)
        record=decode_canonical_bytes(raw,record_kind,maximum_bytes=len(raw))
        if record.canonical_bytes()!=raw or manifest.logical.content_sha256!=record.fingerprint():
            raise PermissionError('retained E4 bootstrap substitutes exact canonical locator bytes')
        metadata.append(manifest)
        return record
    target=locator(directory/'specification.json',kind)
    selector_path=directory/'sources.json'
    selector=locator(selector_path,ExperimentFileInputSelection)
    requests=tuple(row for row in selector.bindings if row.key=='request')
    if len(requests)!=1:raise PermissionError('retained E4 inputs omit their one exact original request')
    request=locator(_input_member(directory,requests[0].relative_path),request_kind)
    if request.identity!=target.request or request.identity!=requests[0].identity:
        raise PermissionError('retained E4 inputs substitute their original request')
    access=(protected_original_access(artifact_writer=writer,request=request,read_access=current_access) if protected else
        development_original_access(artifact_writer=writer,request=request,read_access=current_access)[0])
    facts={(row.logical,row.materialization) for row in metadata}
    def guard(member):
        if (member.logical,member.materialization) not in facts:access.require_member(member)
        access.require_current()
    for manifest in metadata:writer.verify_manifest(manifest,before_member=guard)
    reopened=load_experiment_inputs(target,selector_path,artifact_writer=writer,read_access=current_access)
    _require_structural_inputs(specification=target,inputs=reopened.method_inputs,programme=programme,bank=bank,
        choices=choices,secondary_readout=secondary_readout,resources=resources,campaign=campaign,original=original,declaration=declaration,
        current_access=current_access,measurement=measurement)
    prepared=prepare_experiment(target,scientific_inputs=reopened.scientific_inputs,
        method_inputs=reopened.method_inputs,execution=execution)
    path=directory/'requirements.json'
    manifest=writer.read_manifest(path.relative_to(writer.root.contract.canonical_path).as_posix())
    # The ordinary loader has already authenticated these exact selected
    # records/files. Freeze their member facts before a publication closure can
    # visit a sibling; a current grant alone does not admit a foreign member.
    for binding in (*selector.bindings,*selector.files):
        member_path=_input_member(directory,binding.relative_path)
        member=writer.read_manifest(member_path.relative_to(writer.root.contract.canonical_path).as_posix())
        facts.add((member.logical,member.materialization))
    if (manifest.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or manifest.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or manifest.logical.lineage_parents):
        raise PermissionError('retained E4 requirements change their exact outcome-blind metadata contract')
    facts.add((manifest.logical,manifest.materialization))
    access.require_current()
    writer.verify_manifest(manifest,before_member=guard)
    initial=type(target)(target.specification_id,request.identity,None,None,None)
    expected=canonical_json_bytes({'schema':'empirical-lawhood/operational/experiment-input-requirements',
        'version':'1.0.0','value':{'specification':initial.identity,'target_specification':target.identity,
            'source_selection':selector,'native_contact':'NONE','scientific_authority':'NONE',
            'qualification':'NOT_ESTABLISHED','dependencies':tuple({'code':row.code,'kind':row.kind.value,
                'detail':row.detail,'source_key':row.source_key} for row in prepared.dependencies)}})
    access.require_current()
    if (manifest.logical.payload_schema!='empirical-lawhood/operational/experiment-input-requirements'
            or read_bounded_bytes(path,maximum_bytes=len(expected))!=expected):
        raise PermissionError('retained E4 requirements substitute the exact original derivation target or selector')
    access.require_current()
    return prepared


def _complete_structure(report):
    result=report.get('scientific_result')
    if (report.get('status')!='SUCCEEDED' or type(result) is not dict
            or not _complete_structural_result(result)):
        raise PermissionError('ordinary E4 structure lacks its actual complete PURE production and retained census')
    return result


def _complete_structural_result(result):
    return (result.get('scientific_completion') == 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'
        or result.get('decision_consumption') == 'COMPLETE_RETAINED_FACTOR_CENSUS'
        and result.get('scientific_completion') == 'DEFERRED_TO_FULL_READ'
        and result.get('scientific_reconstruction') == 'OFF')


def read_development_structure_execution(*, directory, artifact_writer, acquisition_report, observe_controls=None):
    """Keep the required PURE child in operational completion without replay."""
    from .experiment_scientific_read import _development_runtime_context
    from .recursive_authoring import load_authored_wave
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    child = _directory(artifact_writer, directory) / 'analysis'
    if not child.exists() and not child.is_symlink():
        return {'state':'NOT_ENTERED','execution_complete':False}
    with artifact_writer.read_context() as writer:
        _, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=writer, lazy_payloads=True)
        selected = _development_runtime_context(payloads=payloads, draft=draft, callback_name='complete_development_result')
        if selected is None:
            raise PermissionError('ordinary E4 operational completion lost its original companion')
        _, specification, instance = selected
        inputs = _development_inputs(specification, instance, payloads)
        task_id = original_workers.global_node(inputs.programme, 'entry')
        row, = (row for row in acquisition_report['operational_census']
            if row['task_id'] == task_id and row['operational_status'] == 'SUCCEEDED')
        receipt = ExternalTaskReceiptStore(writer).read_by_receipt_id(acquisition_report['run_id'], task_id, row['receipt_id'])
        if receipt is None or receipt.fingerprint() != row['receipt_sha256']:
            raise PermissionError('ordinary E4 operational completion changes its original entry receipt')
        from empirical_lawhood.kernel.decoding import decode_canonical_record
        plan_pin = decode_canonical_record(acquisition_report['execution_plan'], ObjectIdentity)
        original = SelectedE4DevelopmentAcquisition('acquisition.' + plan_pin.object_fingerprint,
            Path(directory).relative_to(writer.root.contract.canonical_path).as_posix(), acquisition_report['run_id'],
            plan_pin, _pin(receipt, 'receipt_id'), False)
        return read_structural_execution(directory=directory, artifact_writer=writer, programme=inputs.programme,
            bank=inputs.bank, choices=specification.structure, secondary_readout=inputs.secondary_readout,
            resources=specification.structural_resources, campaign=inputs.campaign, original=original,
            declaration=None, current_access=None, observe_controls=observe_controls)


def read_structural_execution(*, directory, artifact_writer, programme, bank, choices, secondary_readout,
        resources, campaign, original=None, declaration=None, current_access=None, observe_controls=None):
    """Bind operational completion to the exact original structural companion."""
    from .experiment_execution_read import read_development_execution
    from .recursive_authoring import load_authored_wave
    from .development_structure_repair import selected_structure_directory
    with artifact_writer.read_context() as writer:
        child, repair, require_original = selected_structure_directory(writer=writer, directory=directory)
        if not child.exists() and not child.is_symlink():
            require_original()
            return {'state':'NOT_ENTERED','execution_complete':False,
                **({} if repair is None else {'structural_repair':repair.to_document()})}
        _, _, _, structural = load_authored_wave(directory=child, artifact_writer=writer,
            lazy_payloads=True, read_access=current_access)
        child_specification, _, _ = _structural_companion(payloads=structural, programme=programme,
            bank=bank, choices=choices, secondary_readout=secondary_readout,
            resources=resources, campaign=campaign, original=original,
            declaration=declaration, current_access=current_access, measurement=structural_measurement(
                programme=programme, bank=bank, choices=choices))
        result = read_development_execution(directory=child, artifact_writer=writer,
            expected_specification_bytes=child_specification.canonical_bytes(), read_access=current_access,
            observe_controls=observe_controls)
        require_original()
        return {**result, **({} if repair is None else {'structural_repair':repair.to_document(),
            'original_failed_structure_retained':True,'additional_independent_observations':0})}


def _resume_structure(*, service, child, directory, writer, maximum_parallel_tasks,
        programme, bank, choices, secondary_readout, resources, campaign, original, declaration, current_access, measurement):
    """Reuse the actual authored companion before creating any new input identity."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.selected_e4_access import require_current_e4_access

    with writer.read_context() as reading:
        _, _, _, payloads = load_authored_wave(directory=child, artifact_writer=reading, lazy_payloads=True,read_access=current_access)
        _, _, inputs = _structural_companion(payloads=payloads, programme=programme, bank=bank,
            choices=choices,secondary_readout=secondary_readout, resources=resources, campaign=campaign, original=original, declaration=declaration,
            current_access=current_access, measurement=measurement)
        if declaration is not None:
            require_current_e4_access(writer=reading, originals=inputs.request.waves, current_access=current_access)
    options = {} if current_access is None else {'read_access': current_access}
    status = service.read(directory=child, allow_partial=True, **options)
    if status.get('status') == 'SUCCEEDED':
        return read_selected_e4_structure(directory=directory, artifact_writer=writer,
            programme=programme, bank=bank, choices=choices,secondary_readout=secondary_readout, resources=resources, campaign=campaign,
            original=original, declaration=declaration,
            waves=() if declaration is None else current_access.waves,read_access=current_access)
    # The ordinary runtime retains all original attempts and publication facts.
    # A repeated observation of a target publication must not change the frozen
    # secondary selection or request merely because its `created` flag differs.
    return _complete_structure(service.run(directory=child, maximum_parallel_tasks=maximum_parallel_tasks, **options))


def produce_selected_e4_structure(*, directory, artifact_writer, project_root, maximum_parallel_tasks,
        programme, bank, choices, secondary_readout, resources, campaign, development_directory=None, declaration=None, waves=(),
        environment_id=None,read_access=None):
    """Run or resume the declared PURE stage inside an ordinary actual phase."""
    from empirical_lawhood.api.matrix_full_factor_custody import derive_original_full_factor_scope
    from empirical_lawhood.api.matrix_full_factor_derivation import _derive_observed_input_selection
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.selected_e3_access import original_e3_authority_read_context
    from empirical_lawhood.infrastructure.numerical_provenance import observe_worker_environment

    from .matrix_full_factor_secondary import authenticate_e4_secondary_target
    if authenticate_e4_secondary_target(writer=artifact_writer, selection=secondary_readout, bank=bank) != choices.secondary_target:
        raise PermissionError('ordinary E4 structure replaces the actual pre-future target')
    measurement = structural_measurement(programme=programme, bank=bank, choices=choices)
    resources.__post_init__()
    selected_directory = _directory(artifact_writer, directory)
    from .development_structure_repair import selected_structure_directory
    with artifact_writer.read_context() as reading:
        child, _, require_original = selected_structure_directory(writer=reading, directory=directory)
        require_original()
    service=ExperimentProgrammeService(project_root=project_root,artifact_writer=artifact_writer)
    current_access=read_access
    original_waves=waves
    execution=None
    def selected_execution():
        implementation = implementation_binding(project_root)
        return ExecutionSelection(workers=maximum_parallel_tasks,
            environment_id=environment_id or "environment." + observe_worker_environment().fingerprint(),
            source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", implementation),
            output_root=artifact_writer.root.contract.canonical_path)
    def author_retained(execution,original):
        with artifact_writer.read_context() as reading:
            prepared=_retained_structure_preparation(directory=selected_directory/'inputs',writer=reading,
                programme=programme,bank=bank,choices=choices,secondary_readout=secondary_readout,resources=resources,campaign=campaign,
                original=original,declaration=declaration,current_access=current_access,
                measurement=measurement,execution=execution)
        options={} if current_access is None else {'read_access':current_access}
        service.author(preparation=prepared,output_dir=child,**options)
        return _complete_structure(service.run(directory=child,maximum_parallel_tasks=maximum_parallel_tasks,**options))
    if declaration is not None:
        from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess
        current_access=SelectedE4CurrentAccess(waves) if read_access is None else read_access
        current_access.require_originals(waves)
        if child.exists():
            return _resume_structure(service=service, child=child, directory=directory, writer=artifact_writer,
                maximum_parallel_tasks=maximum_parallel_tasks, programme=programme, bank=bank, choices=choices,secondary_readout=secondary_readout,
                resources=resources, campaign=campaign, original=None, declaration=declaration,
                current_access=current_access, measurement=measurement)
        if (selected_directory/'inputs'/'sources.json').exists():
            # The retained blind request owns the original locators. A newer
            # reveal grant must not change scope/request identities on retry.
            return author_retained(selected_execution(),None)
    accesses=[]
    with original_e3_authority_read_context(artifact_writer):
        with artifact_writer.read_context() as writer:
            scope, files = derive_original_full_factor_scope(writer=writer, programme=programme, bank=bank,
                record_id="scope.e4.structure." + programme.fingerprint(), codecs=operation_catalog()[2],
                declaration=declaration, waves=original_waves, _development_directory=development_directory,
                current_access=current_access,_secondary_readout=secondary_readout,
                _consume_original_access=lambda access,evidence:accesses.append((access,evidence)))
    if len(accesses)!=1:raise PermissionError('ordinary E4 structure lacks its actual original access scope')
    original_access,evidence=accesses[0]
    original_access.require_current(artifact_writer=artifact_writer)
    if full.measurement(scope) != measurement:
        raise PermissionError("ordinary E4 structure changes its predeclared complete numerical measurement")
    if child.exists():
        return _resume_structure(service=service, child=child, directory=directory, writer=artifact_writer,
            maximum_parallel_tasks=maximum_parallel_tasks, programme=programme, bank=bank, choices=choices,secondary_readout=secondary_readout,
            resources=resources, campaign=campaign, original=scope.development, declaration=None,
            current_access=current_access, measurement=measurement)
    execution=selected_execution()
    if (selected_directory/'inputs'/'sources.json').exists():
        return author_retained(execution,scope.development)
    writer = artifact_writer
    selected_campaign = _campaign(campaign, scope, resources)
    secondary = secondary_readout
    values = ("request.e4.structure." + programme.fingerprint(), programme.identity, bank.identity, resources.identity)
    if scope.protected:
        request = full.ScheduledFullFactorProtectedRequestV4(*values, scope.declaration.identity, scope.waves,
            _pin(selected_campaign, "campaign_id"), secondary)
        kind = full.ScheduledFullFactorProtectedSpecification
    else:
        request = full.ScheduledFullFactorDevelopmentRequestV3(*values, _pin(selected_campaign, "campaign_id"),
            scope.development, secondary)
        kind = full.ScheduledFullFactorDevelopmentSpecification
    specification = kind("experiment.e4.structure." + programme.fingerprint(), request.identity, None, None, None)
    inputs = full.ScheduledFullFactorFollowupInputs(request=request, programme=programme, bank=bank,
        resources=resources, campaign=selected_campaign,original_evidence=evidence)
    derived = _derive_observed_input_selection(specification=specification, method_inputs=inputs,
        scope=scope, files=files, project_root=project_root, artifact_writer=writer,
        metadata_directory=selected_directory / "inputs", output_selection_path=selected_directory / "inputs" / "sources.json",
        execution=execution,original_input_access=original_access,read_access=current_access)
    if not child.exists():
        service.author(preparation=derived.preparation, output_dir=child,
            **({} if current_access is None else {'read_access':current_access}))
    else:
        # Reuse is exact scientific identity, not the presence of an output path.
        from empirical_lawhood.api.recursive_authoring import load_authored_wave
        _, _, _, payloads = load_authored_wave(directory=child, artifact_writer=artifact_writer, lazy_payloads=True,read_access=current_access)
        raw = payloads["experiment-specification.json"]
        retained = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        if retained.canonical_bytes() != raw or retained != derived.target_specification:
            raise PermissionError("ordinary E4 structure reuses a different retained numerical stage")
    report = service.run(directory=child, maximum_parallel_tasks=maximum_parallel_tasks,
        **({} if current_access is None else {'read_access':current_access}))
    return _complete_structure(report)


def read_selected_e4_structure(*, directory, artifact_writer, programme, bank, choices, secondary_readout, resources,
        campaign, original=None, declaration=None, waves=(),read_access=None):
    """Authenticate the actual structural child and all original evidence; no writes."""
    from empirical_lawhood.api.matrix_full_factor_read import read_development_result
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_roots
    from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess,require_current_e4_access
    protected = declaration is not None
    current_access=(SelectedE4CurrentAccess(waves) if read_access is None else read_access) if protected else read_access
    from .matrix_full_factor_secondary import authenticate_e4_secondary_target
    if authenticate_e4_secondary_target(writer=artifact_writer, selection=secondary_readout, bank=bank) != choices.secondary_target:
        raise PermissionError('ordinary E4 read replaces the actual pre-future target')
    expected = structural_measurement(programme=programme, bank=bank, choices=choices)
    authored=[]
    def validate_authored(**context):
        specification,instance,inputs=_structural_companion(payloads=context['payloads'],programme=programme,bank=bank,
            choices=choices,secondary_readout=secondary_readout,resources=resources,campaign=campaign,original=original,declaration=declaration,
            current_access=current_access,measurement=expected)
        request=inputs.request
        if protected:
            current_access.require_originals(request.waves)
            require_current_e4_access(writer=artifact_writer,originals=request.waves,current_access=current_access)
        authored.append((specification,instance,request.waves if protected else ()))
    def consume(**context):
        if len(authored)!=1:
            raise PermissionError('ordinary E4 structure lacks one authenticated original companion preflight')
        specification,instance,_=authored[0]
        return read_development_result(specification=specification, instance=instance,
            read_access=current_access,**context)
    from .development_structure_repair import selected_structure_directory
    accesses=[]
    with artifact_writer.read_context() as writer:
        child, repair, require_original = selected_structure_directory(writer=writer, directory=directory)
        selected, _, _ = _read_recursive_wave_with_roots(directory=child, artifact_writer=writer,
            include_products=True, scientific_consumer=consume,validate_authored=validate_authored,
            read_access=current_access,_retain_original_input_access=accesses.append)
        require_original()
    for access in accesses:access.require_current(artifact_writer=artifact_writer)
    if protected:
        require_current_e4_access(writer=artifact_writer,originals=authored[0][2],current_access=current_access)
    result = selected[0].get("scientific_result")
    if type(result) is not dict or not _complete_structural_result(result):
        raise PermissionError("ordinary E4 read lacks its complete structural census")
    return {**result, **({} if repair is None else {'structural_repair':repair.to_document(),
        'original_failed_structure_retained':True,'additional_independent_observations':0})}


def complete_development_result(*, directory, artifact_writer, project_root, maximum_parallel_tasks,
        specification, instance, payloads, draft, plan, scheduler_result, read_access=None):
    from empirical_lawhood.runtime.execution import SchedulerResult
    from empirical_lawhood.kernel.status import OperationalStatus
    inputs = _development_inputs(specification, instance, payloads)
    if type(scheduler_result) is not SchedulerResult or scheduler_result.run_id != plan.source_plan.object_id:
        raise PermissionError("ordinary E4 completion changes its actual scheduler run")
    scheduler_result.__post_init__()
    entry = original_workers.global_node(inputs.programme, "entry")
    receipts = tuple(row for row in scheduler_result.receipts if row.task_id == entry)
    if not receipts:
        if (scheduler_result.status not in (OperationalStatus.FAILED, OperationalStatus.BLOCKED)
                or entry in scheduler_result.completed_task_ids
                or entry not in (*scheduler_result.failed_task_ids, *scheduler_result.blocked_task_ids)):
            raise PermissionError("ordinary E4 completion lacks a known original source-entry disposition")
        return {"state": "NOT_ENTERED_SOURCE_ENTRY_REFUSED", "scientific_completion": "NOT_ESTABLISHED",
            "new_native_contact_count": 0}
    if (len(receipts) != 1 or entry not in scheduler_result.completed_task_ids
            or receipts[0].run_id != scheduler_result.run_id
            or receipts[0].operational_status is not OperationalStatus.SUCCEEDED):
        raise PermissionError("ordinary E4 completion changes its actual successful source-entry receipt")
    original_input_access = getattr(payloads, 'original_input_access', None)
    if original_input_access is not None:
        original_input_access.require_current()
    return produce_selected_e4_structure(directory=directory, artifact_writer=artifact_writer,
        project_root=project_root, maximum_parallel_tasks=maximum_parallel_tasks, programme=inputs.programme,
        bank=inputs.bank, choices=specification.structure,secondary_readout=inputs.secondary_readout, resources=specification.structural_resources,
        campaign=inputs.campaign, development_directory=directory,read_access=read_access)


def read_development_result(*, directory, artifact_writer, specification, instance, payloads, report,
        products, draft, plan, allow_partial=False, read_access=None):
    """Deliver response and structure through the ordinary DEV result owner."""
    inputs = _development_inputs(specification, instance, payloads)
    original_input_access = getattr(payloads, 'original_input_access', None)
    if original_input_access is not None:
        original_input_access.require_current()
    entry_task = original_workers.global_node(inputs.programme, "entry")
    entry_receipt = products["receipts"].get(entry_task)
    if allow_partial or products.get("terminal") is None or entry_receipt is None:
        from empirical_lawhood.api.matrix_selected_e3_e4_read import _development_result
        entries = tuple(row for row in draft.operations if row.selection.capability_key == original_workers.NAMESPACE + ".entry")
        from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
        declarations = {row.capability_key: row for row in original_workers.operation_declarations()}
        if len(entries) != 1:
            raise PermissionError("ordinary E4 incomplete read changes its original source entry")
        operation, = entries
        entry = decode_recursive_config_input(operation, declarations[operation.selection.capability_key].registration()).record
        base = _development_result(artifact_writer=artifact_writer, report=report, products=products, draft=draft,
            plan=plan, entry=entry, original_input_access=original_input_access)
        state = "NOT_ESTABLISHED"
        if not allow_partial and products.get("terminal") is not None and entry_receipt is None:
            dispositions = tuple(row["operational_status"] for row in report["task_census"] if row["task_id"] == entry_task)
            if len(dispositions) != 1 or dispositions[0] not in ("FAILED", "BLOCKED"):
                raise PermissionError("ordinary E4 read cannot infer source nonentry from a missing receipt")
            state = "NOT_ENTERED_SOURCE_ENTRY_REFUSED"
        return {**base, "structure": {"state": state, "scientific_completion": "NOT_ESTABLISHED", "new_native_contact_count": 0}}
    if original_input_access is not None:original_input_access.require_current()
    original = _acquisition(directory=directory, writer=artifact_writer, programme=inputs.programme,
        report=report, products=products, plan=plan)
    structure = read_selected_e4_structure(directory=directory, artifact_writer=artifact_writer,
        programme=inputs.programme, bank=inputs.bank, choices=specification.structure,secondary_readout=inputs.secondary_readout,
        resources=specification.structural_resources, campaign=inputs.campaign, original=original,read_access=read_access)
    return {**structure["original_response"], "structure": structure_projection(structure)}
