# SPDX-License-Identifier: MPL-2.0
"""Actual issued wave reads and full-phase state; no native/provider contact."""

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.api.current_result_custody import authenticate_current_execution_plan,retained_output_artifact_plane
from empirical_lawhood.api.matrix_selected_runtime import _published_input
from empirical_lawhood.api.matrix_training_provenance import original_comparator_training
from empirical_lawhood.api.recursive_qualified_parents import _actual_package,_replay_parent_authority,_require_parent_authorities_current,MAX_PARENT_BYTES
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.recursive_custody import read_execution_products
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.recovery import build_run_recovery_index


def _inputs(writer,plan,run_id,*,require_current,external_contracts=()):
    exact={row.logical_artifact_id:row for row in external_contracts}
    selected={}
    for task in plan.tasks:
        for spec in task.external_inputs:
            old=selected.setdefault(spec.logical_artifact_id,spec)
            from dataclasses import replace
            if replace(old,input_id=spec.input_id)!=spec:
                raise PermissionError("selected E4 original plan aliases external scientific inputs")
    values=[]
    for key,spec in sorted(selected.items()):
        relative,_,_=provider_input_location(writer,run_id,key)
        manifest=writer.read_manifest(relative)
        if (manifest.materialization.relative_path!=relative
                or manifest.materialization.storage_root_id!=writer.root.contract.storage_root_id
                or manifest.logical.logical_artifact_id!=key
                or any(expected is not None and actual!=expected for actual,expected in (
                    (manifest.logical.payload_schema,spec.expected_payload_schema),(manifest.logical.content_sha256,spec.expected_content_sha256),
                    (manifest.materialization.size_bytes,spec.expected_size_bytes),(manifest.logical.media_type,spec.expected_media_type),
                    (manifest.logical.outcome_access,spec.expected_outcome_access),(manifest.logical.visibility_ceiling,spec.expected_visibility_ceiling)))):
            raise PermissionError("selected E4 original wave substitutes exact persisted input custody")
        declared=exact.get(key)
        if declared is not None and (manifest.logical.payload_schema,manifest.logical.media_type,
                manifest.logical.content_sha256,manifest.materialization.size_bytes,
                manifest.logical.outcome_access,manifest.logical.visibility_ceiling)!=(
                declared.payload_schema,declared.media_type,declared.expected_content_sha256,
                declared.maximum_size_bytes,declared.outcome_access,declared.visibility_ceiling):
            raise PermissionError("selected E4 original publication changes its exact declared scientific bytes")
        require_current(writer)
        writer.verify_manifest(manifest)
        values.append(VerifiedArtifactInput(manifest.logical,manifest.materialization))
    return tuple(values)


def _record(writer,products,task_id,output,kind,*,require_current):
    receipt=products["receipts"].get(task_id)
    if receipt is None:return None
    indexed=products.get("product_index_by_key")
    if indexed is None:
        rows=tuple(v for v in products["product_index"] if (v["task_id"],v["output_id"])==(task_id,task_id+"."+output))
    else:
        row=indexed.get((task_id,task_id+"."+output))
        rows=() if row is None else (row,)
    if len(rows)!=1:raise PermissionError("selected E4 completed task lacks exact required typed output")
    row=rows[0]
    if row["schema"]!=kind.SCHEMA:raise PermissionError("selected E4 retained product changes actual scientific schema")
    require_current(writer)
    raw=read_bounded_bytes(writer.root.resolve(row["relative_path"],for_write=False),maximum_bytes=MAX_PARENT_BYTES)
    record=decode_canonical_bytes(raw,kind,maximum_bytes=MAX_PARENT_BYTES)
    if record.canonical_bytes()!=raw or record.fingerprint()!=row["sha256"]:
        raise PermissionError("selected E4 original typed product changes canonical bytes")
    return record



def _require_wave_graph(plan, external, links):
    """Authenticate the chosen historical/current direct-input graph exactly."""
    external_by_id={row.input_id:row for row in external}
    tasks={row.task_id:row for row in plan.tasks}
    by_task={task_id:[] for task_id in tasks}
    for link in links:
        by_task[link.consumer_node_id].append(link)
    for task_id,task in tasks.items():
        expected=by_task[task_id]
        actual={row.consumer_input_id:row for row in task.scientific_inputs}
        if len(actual)!=len(task.scientific_inputs) or set(actual)!={row.consumer_input_id for row in expected}:
            raise PermissionError("selected E4 retained wave changes its exact scientific port roster")
        for link in expected:
            edge=actual[link.consumer_input_id]
            if link.producer_node_id is None:
                selected=external_by_id[link.external_input_id]
                specs=tuple(row for row in task.external_inputs if row.logical_artifact_id==selected.logical_artifact_id)
                if len(specs)!=1:
                    raise PermissionError("selected E4 retained wave loses an exact direct original input")
                spec,=specs
                # The generic compiler can leave the optional operational
                # size unset. The scientific edge and actual publication below
                # must both retain the exact domain-selected byte count.
                if ((spec.expected_payload_schema,spec.expected_media_type,spec.expected_content_sha256,
                        spec.expected_outcome_access,spec.expected_visibility_ceiling)!=(
                        selected.payload_schema,selected.media_type,selected.expected_content_sha256,
                        selected.outcome_access,selected.visibility_ceiling)
                        or spec.expected_size_bytes not in (None,selected.maximum_size_bytes)
                        or (edge.payload_schema,edge.media_type,edge.maximum_size_bytes,
                            edge.outcome_access,edge.visibility_ceiling)!=(selected.payload_schema,selected.media_type,
                            selected.maximum_size_bytes,selected.outcome_access,selected.visibility_ceiling)
                        or (edge.producer_task_id,edge.producer_output_id,edge.external_input_id,
                            edge.logical_artifact_id,edge.operational_logical_artifact_id)!=(None,None,
                            selected.input_id,selected.logical_artifact_id,selected.logical_artifact_id)):
                    raise PermissionError("selected E4 retained wave substitutes its exact direct original carrier")
            else:
                producer=tasks[link.producer_node_id]
                outputs=tuple(row for row in producer.outputs if row.output_id==link.producer_node_id+"."+link.producer_output_id)
                if len(outputs)!=1:
                    raise PermissionError("selected E4 retained wave loses its exact original producer output")
                output,=outputs
                if ((edge.producer_task_id,edge.producer_output_id,edge.external_input_id,
                        edge.operational_logical_artifact_id)!=(producer.task_id,output.output_id,None,output.logical_artifact_id)):
                    raise PermissionError("selected E4 retained wave substitutes its exact consumed producer")
        if task.dependency_task_ids!=tuple(sorted({row.producer_node_id for row in expected if row.producer_node_id is not None})):
            raise PermissionError("selected E4 retained wave changes its complete dependency census")



def _native_case_products(writer,products,plan,entry,bank,case,configs,tasks,materializations,*,direct_operands,require_current):
    """Replay native scope against the actual retained task and carrier inputs."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source
    kinds={"prefix":r.SelectedE4ProtectedPrefixHistory,"project":r.SelectedE4ProtectedCausalPrefix,
        "account":r.SelectedE4ProtectedAccountSeal,"mechanical":r.SelectedE4ProtectedMechanicalForecast,
        "continue":r.SelectedE4ProtectedFullHistory,"responses":r.SelectedE4ProtectedResponses}
    values={phase:_record(writer,products,owner.local_node(case.root_id,phase),"product",kind,
        require_current=require_current) for phase,kind in kinds.items()}
    if all(values[phase] is None for phase in owner.NATIVE):
        return values
    config=configs[owner.local_node(case.root_id,"prefix")]
    provenance,=(row for row in bank.provenances if row.identity==config.source.provenance)
    source=bind_selected_native_source(config.source,provenance)
    def bound(phase):
        value=configs[owner.local_node(case.root_id,phase)]
        return owner.bind_selected_e4_models(value,entry.models) if owner.referenced_config(value) else value
    prefix,causal,account,mechanical=(values[name] for name in ("prefix","project","account","mechanical"))
    if prefix is not None:
        prefix.validate_source(source,config=bound("prefix"))
    for phase in ("continue","responses"):
        product=values[phase]
        if product is None:continue
        if any(value is None for value in (prefix,causal,account,mechanical)):
            raise PermissionError("selected E4 retained future omits its actual prefix and pre-future lineage")
        if phase=="continue":
            product.validate_source(source,prefix,causal,account,mechanical,config=bound(phase),prefix_config=bound("prefix"))
        else:
            product.validate_source(source,prefix,causal,mechanical,account,config=bound(phase),prefix_config=bound("prefix"))
    plan_pin=r.pin(plan,"execution_plan_id")
    for phase in owner.NATIVE:
        product=values[phase]
        if product is None:continue
        events=product.native if phase=="responses" else (product.native,)
        node=owner.local_node(case.root_id,phase);task=tasks[node];receipt=products["receipts"][node]
        dependencies=tuple(sorted(products["receipts"][parent].receipt_id for parent in task.dependency_task_ids))
        for event in events:
            definition=event.definition;parent=definition.parent_contact
            if (definition.operation_id.endswith(".direct-operands.v2")!=direct_operands
                    or (parent.run_id,parent.task_id,parent.attempt_id,parent.execution_plan,parent.execution_task,
                        parent.implementation_commit,parent.input_materialization_ids,parent.dependency_receipt_ids)!=(
                        receipt.run_id,node,receipt.attempt_id,plan_pin,r.pin(task,"task_id"),receipt.implementation_commit,
                        definition.input_materialization_ids,dependencies)
                    or parent.input_materialization_ids!=receipt.input_materialization_ids):
                raise PermissionError("selected E4 native evidence changes its actual recorded graph/parent/input custody")
            if direct_operands:
                inputs=tuple(materializations[key] for key in parent.input_materialization_ids)
                for pin in (definition.configuration,*definition.sources,*definition.streams):
                    if sum((row.payload_schema,row.content_sha256)==(pin.object_schema,pin.object_fingerprint) for row in inputs)!=1:
                        raise PermissionError("selected E4 native evidence loses its unique actual direct scientific operand")
    return values


def read_selected_e4_wave(*,writer,declaration,locator,codecs,_consume_original=None,current_access=None):
    if _consume_original is not None and not callable(_consume_original):
        raise TypeError("original protected scientific consumer must be callable")
    from empirical_lawhood.api.selected_e4_access import require_current_e4_access
    with writer.read_context() as reading:
        result=_read_selected_e4_wave(writer=reading,declaration=declaration,locator=locator,codecs=codecs,
            _consume_original=_consume_original,current_access=current_access)
        reading.require_verification_snapshot()
    # A single-wave read can belong to a complete multiwave access selection.
    # Roster closure belongs to the programme/reference boundary below.
    from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess
    selected=None if current_access is None else SelectedE4CurrentAccess(tuple(
        value for value in current_access.waves if value.wave_id==locator.wave_id))
    require_current_e4_access(writer=writer,originals=(locator,),current_access=selected)
    return result


def _read_selected_e4_wave(*,writer,declaration,locator,codecs,_consume_original=None,current_access=None):
    if _consume_original is not None and not callable(_consume_original):
        raise TypeError("original protected scientific consumer must be callable")
    """Fresh original issue/execution/reveal before any protected product read."""
    locator.__post_init__();declaration.__post_init__()
    wave=declaration.wave(locator.wave_id)
    package=_actual_package(writer,locator.run_id)
    if r.pin(package,"package_id")!=locator.package:
        raise PermissionError("selected E4 wave substitutes actual original issued package")
    from empirical_lawhood.api.selected_e4_access import selected_e4_authority_binding
    binding=selected_e4_authority_binding(locator,current_access)
    issued,reveal=_replay_parent_authority(binding,package,writer)
    def require_current(reading):
        _,current=_require_parent_authorities_current(((binding,package),),reading)[0]
        if current!=reveal:
            raise PermissionError("selected E4 wave current reveal changed during its original read")
    plan=authenticate_current_execution_plan(package=package,issued=issued,run_id=locator.run_id,writer=writer)
    if r.pin(plan,"execution_plan_id")!=locator.execution_plan:
        raise PermissionError("selected E4 wave substitutes original execution plan")
    entry_tasks=tuple(v for v in plan.tasks if v.capability.capability_key==owner.NAMESPACE+".entry")
    if len(entry_tasks)!=1:raise PermissionError("selected E4 wave omits exact source-entry task")
    task=entry_tasks[0]
    entry_task_id=task.task_id
    specs=tuple(v for v in task.external_inputs if v.logical_artifact_id==task.capability.config.artifact_id)
    if len(specs)!=1:raise PermissionError("selected E4 wave source entry omits actual configuration")
    require_current(writer)
    entry=_published_input(writer,locator.run_id,specs[0],owner.SelectedE4ProtectedEntryConfig)
    banks=tuple(v for v in task.external_inputs if v.expected_payload_schema==p.SelectedE4PhaseBank.SCHEMA)
    if len(banks)!=1:raise PermissionError("selected E4 original wave omits complete source bank")
    require_current(writer)
    bank=_published_input(writer,locator.run_id,banks[0],p.SelectedE4PhaseBank)
    source_index=bank.source_index()
    from .matrix_full_factor_secondary import authenticate_e4_secondary_target
    require_current(writer)
    authenticate_e4_secondary_target(writer=writer, selection=entry.secondary_readout, bank=bank)
    require_current(writer)
    if bank.identity!=declaration.bank:raise PermissionError("selected E4 original wave changes exact source bank")
    if entry.declaration!=declaration or entry.wave_id!=locator.wave_id:
        raise PermissionError("selected E4 wave changes original full pre-entry source/membership/model/budget declaration")
    from empirical_lawhood.api.selected_e4_native_runtime import require_selected_e4_native_plan_budget
    require_selected_e4_native_plan_budget(package=package,plan=plan,entry=entry)
    native_tasks=tuple(task for task in plan.tasks if task.capability.capability_key.rsplit(".",1)[-1] in owner.NATIVE)
    if not native_tasks:
        raise PermissionError("selected E4 native wave omits its recorded native graph revision")
    direct_operands=all(task.capability.capability_version=="3.0.0" for task in native_tasks)
    if any(task.capability.capability_version=="3.0.0" for task in native_tasks) and not direct_operands:
        raise PermissionError("selected E4 native wave mixes historical and current operand graphs")
    configs,external,links,_,_=owner.contracts(entry.programme,bank,entry.evidence,entry.evidence_size_bytes,
        entry.decision,entry.models,entry.calibration,entry.declaration,entry.declaration_publication,entry.wave_id,
        secondary_readout=entry.secondary_readout,referenced_models=any(value.capability.config.config_schema in (owner.SelectedE4ProtectedReferencedConfig.SCHEMA,
            owner.SelectedE4ProtectedReferencedPublicConfig.SCHEMA,owner.SelectedE4ProtectedProtocolConfig.SCHEMA,
            owner.SelectedE4ProtectedProtocolPublicConfig.SCHEMA) for value in plan.tasks),
        compact_protocol=any(value.capability.config.config_schema in (owner.SelectedE4ProtectedProtocolConfig.SCHEMA,
            owner.SelectedE4ProtectedProtocolPublicConfig.SCHEMA) for value in plan.tasks),direct_operands=direct_operands)
    expected={n:c for n,c in configs}
    if {v.task_id for v in plan.tasks}!=set(expected):
        raise PermissionError("selected E4 wave original plan changes complete declared native task census")
    for task in plan.tasks:
        config=expected[task.task_id]
        manifest=package.registry.resolve(task.capability.capability_key,task.capability.capability_version)
        current=owner.declaration_for_config(config)
        expected_key=current.capability_key
        expected_version=("3.0.0" if direct_operands else "1.0.0" if owner.referenced_config(config) else "2.0.0") if config.phase in owner.NATIVE else current.capability_version
        if (manifest.capability_key!=expected_key or manifest.capability_version!=expected_version or manifest.config_schema!=config.SCHEMA
                or manifest.config_schema_sha256!=task.capability.config.config_schema_sha256):
            raise PermissionError("selected E4 retained wave changes its original supported config owner")
        if (task.capability.capability_key,task.capability.capability_version,task.capability_implementation_sha256,
                task.capability.config.content_sha256,task.capability.requested_resources,task.capability.requested_outcome_access)!=(
                manifest.capability_key,manifest.capability_version,manifest.implementation_sha256,config.fingerprint(),
                dict(declaration.planned_task_budgets)[task.task_id],owner.access(config.phase)):
            raise PermissionError("selected E4 wave substitutes actual installed native method/config/resource/access")
    _require_wave_graph(plan,external,links)
    semantic=retained_output_artifact_plane(package,plan,writer,codecs)
    recovery_index=build_run_recovery_index(plan,run_id=locator.run_id,wave_id="wave."+package.package_id,authority_identities=(
        r.pin(package.scientific_approval,"authorization_id"),r.pin(package.execution_authority,"authority_id")))
    store=ExternalRunRecoveryStore(semantic)
    retained=store.read_index(recovery_index.index_relative_path,expected_schema=recovery_index.SCHEMA)
    if retained!=recovery_index:raise PermissionError("selected E4 wave changes original complete recovery census")
    require_current(semantic)
    original_inputs=_inputs(semantic,plan,locator.run_id,require_current=require_current,external_contracts=external)
    require_current(semantic)
    from .recursive_execution import _read_only_custody_policy
    products=read_execution_products(plane=semantic,plan=plan,index=recovery_index,external_inputs=original_inputs,
        output_codecs=codecs,decode_products=False,_read_policy=_read_only_custody_policy(semantic))
    require_current(semantic)
    terminal=products["terminal"]
    status={v["task_id"]:v["operational_status"] for v in products["dispositions"]}
    actual_forecasts=_record(semantic,products,entry_task_id,"forecasts",p.SelectedE4ForecastBank,
        require_current=require_current)
    if actual_forecasts is None:
        revision_forecasts={}
    else:
        from empirical_lawhood.api.selected_e4_native_runtime import SelectedE4ParentEntry
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_science import entry_forecasts
        if actual_forecasts!=entry_forecasts(SelectedE4ParentEntry(entry,bank)):
            raise PermissionError("selected E4 wave substitutes actual before-native entry forecasts")
        revision_forecasts={v.case_id:v for v in actual_forecasts.forecasts}
    # These finite indices live only in this authenticated read; no authority
    # or mutable payload value is reused across independent calls.
    products["product_index_by_key"]={(row["task_id"],row["output_id"]):row for row in products["product_index"]}
    if len(products["product_index_by_key"])!=len(products["product_index"]):
        raise PermissionError("selected E4 original product index duplicates an exact producer output")
    task_index={task.task_id:task for task in plan.tasks}
    materializations={value.materialization.materialization_id:value.logical for value in original_inputs}
    materializations.update((value.materialization.materialization_id,value.logical) for value in products["outputs"].values())
    cases=[]
    for case in declaration.programme.cases:
        if case.root_id not in wave.root_ids:continue
        node=lambda phase:owner.local_node(case.root_id,phase)
        require_current(semantic)
        native_products=_native_case_products(semantic,products,plan,entry,bank,case,expected,task_index,materializations,
            direct_operands=direct_operands,require_current=require_current)
        completed=_record(semantic,products,node("collect"),"product",r.SelectedE4NativeCaseResult,
            require_current=require_current)
        if completed is not None:
            cases.append(completed);continue
        account=native_products["account"]
        score=_record(semantic,products,node("response-score"),"projection",p.SelectedE4ScoreProjection,
            require_current=require_current)
        causal=native_products["project"]
        numerical=_record(semantic,products,node("full-numerical"),"product",r.SelectedE4ProtectedNumericalAssessment,
            require_current=require_current)
        native=[]
        for phase in ("continue","prefix","responses"):
            product=native_products[phase]
            events=() if product is None else (product.native if phase=="responses" else (product.native,))
            event=None if not events else events[0]
            state="COMPLETED" if event is not None else "NOT_USED" if product is not None and phase=="responses" else "UNKNOWN"
            native.append(r.ScheduledProgrammeNativeDisposition(phase,state,None if event is None else event.definition.identity,
                None if event is None else ObjectIdentity.from_record(event.receipt.task_id + ".completion", event.completion),
                None if event is None else r.pin(event.receipt,"receipt_id"),
                ("actual-no-success-native-product-contact-not-inferred",) if event is None else ()))
        refs=tuple(sorted((r.ScheduledProgrammeReceiptReference(v.receipt_id,v.task_id,tuple(sorted(q.materialization_id for q in v.output_materializations))) for k,v in products["receipts"].items()
            if k in {node(phase) for phase in owner.PHASES if phase not in ("entry","reduce")}),key=lambda v:v.receipt_id))
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import selected_target_shape
        contract = getattr(bank.forecast_design.package.specification.measurement, "target_contract", "PAIRED15")
        methods, point_count, target_count = selected_target_shape(contract)
        cases.append(r.SelectedE4NativeCaseResult(case.root_id,case.source,case.independent_group_id,
            "FAILED" if any(status.get(node(phase))=="FAILED" for phase in owner.PHASES if phase not in ("entry","reduce")) else "UNKNOWN",
            "UNKNOWN" if numerical is None else "SATISFIED" if numerical.numerical_pass else "VIOLATED",
            "UNKNOWN" if score is None else score.disposition,(None,)*target_count if score is None else score.paired_log_targets,
            tuple((method,(None,)*point_count) for method in methods) if account is None else account.log_points,
            None if account is None else account.identity,None if score is None else score.original,
            None if numerical is None else r.identity(numerical),refs,tuple(native),("actual-case-collector-not-completed",),
            None if causal is None else p.SelectedE4PrefixProjection.from_record(causal,record_id="projection."+case.root_id),
            score,(None if account is None else account.revision) if contract == 'MATCHED_FACTOR58' else revision_forecasts.get(case.root_id),
            bank.source(case.root_id,index=source_index).coordinate,contract,
            p.SelectedE4CausalFeatureProjection.from_account(account) if account is not None and contract == 'MATCHED_FACTOR58' else None))
    events=tuple(sorted((r.pin(v,"event_id") for v in products["recovery_events"].values()),key=lambda v:v.object_id))
    result=r.SelectedE4WaveObservation("wave-observation."+locator.wave_id,declaration.identity,locator.wave_id,locator.execution_plan,
        r.pin(terminal,"terminal_event_id"),tuple(cases),events)
    if _consume_original is not None:
        if terminal is None or tuple(row.root_id for row in cases)!=wave.root_ids:
            raise PermissionError("original protected scientific consumer lacks its complete authenticated terminal wave census")
        with semantic.read_context() as observed_writer:
            observed_writer.require_verification_snapshot()
            require_current(observed_writer)
            _consume_original(writer=observed_writer,products=products,plan=plan,entry=entry,bank=bank,
                cases=tuple(cases),locator=locator,run_id=locator.run_id)
            observed_writer.require_verification_snapshot()
    state={"wave_id":locator.wave_id,"run_id":locator.run_id,"terminal":terminal.operational_status,
        "assigned_groups":wave.group_ids,"assigned_cases":wave.root_ids,"task_count":len(plan.tasks),
        "task_census":tuple(products["dispositions"]),
        "original_comparator_training":original_comparator_training(bank.forecast_design.package),
        "new_native_contact_count":0}
    require_current(semantic)
    return result,state


def read_selected_e4_programme(*,writer,declaration,locators,codecs,_consume_original=None,current_access=None):
    """One full assigned state; absent waves remain unentered, never completed."""
    if type(locators) is not tuple or any(type(v) is not r.SelectedE4WaveLocator for v in locators):
        raise TypeError("selected E4 programme needs exact immutable original wave locators")
    if _consume_original is not None and not callable(_consume_original):
        raise TypeError("selected E4 original scientific consumer must be callable")
    if current_access is not None:
        from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess
        if type(current_access) is not SelectedE4CurrentAccess:
            raise TypeError('current E4 access requires its exact operation-local selection')
        current_access.require_originals(locators)
    by_wave={v.wave_id:v for v in locators}
    if len(by_wave)!=len(locators) or set(by_wave)-{v.wave_id for v in declaration.programme.waves}:
        raise ValueError("selected E4 programme duplicates or adds a wave outside frozen membership")
    results=[];states=[]
    for wave in declaration.programme.waves:
        if wave.wave_id not in by_wave:
            states.append({"wave_id":wave.wave_id,"state":"UNENTERED_OR_NOT_SELECTED","assigned_groups":wave.group_ids,
                "assigned_cases":wave.root_ids});continue
        result,state=read_selected_e4_wave(writer=writer,declaration=declaration,locator=by_wave[wave.wave_id],
            codecs=codecs,_consume_original=_consume_original,current_access=current_access)
        results.append(result);states.append(state)
    training=tuple(state["original_comparator_training"] for state in states if "original_comparator_training" in state)
    if training and any(value!=training[0] for value in training[1:]):
        raise PermissionError("selected E4 waves change their exact original comparator TRAIN provenance")
    from empirical_lawhood.api.selected_e4_access import require_current_e4_access
    require_current_e4_access(writer=writer,originals=locators,current_access=current_access)
    return tuple(results),{"programme":declaration.programme.identity.to_document(),"declaration":declaration.identity.to_document(),
        "original_comparator_training":None if not training else training[0],
        "assigned_group_count":len(declaration.programme.group_ids),"assigned_case_count":len(declaration.programme.cases),
        "planned_task_count":len(declaration.planned_task_budgets),"waves":tuple(states),
        "all_wave_terminals_present":len(results)==len(declaration.programme.waves),
        "observation_status":"COMPLETE_CASE_CENSUS" if len(results)==len(declaration.programme.waves) and all(
            c.disposition=="COMPLETED" for v in results for c in v.cases) else "INCOMPLETE_OR_ADVERSE_RETAINED",
        "scientific_qualification":"NOT_ESTABLISHED","new_native_contact_count":0}




def read_selected_e4_component(*,selected,artifact_writer,run_id,reveal_authority_id=None,allow_partial=False):
    return _read_selected_e4_component(selected=selected,artifact_writer=artifact_writer,run_id=run_id,
        reveal_authority_id=reveal_authority_id,allow_partial=allow_partial)


def _read_selected_e4_component(*,selected,artifact_writer,run_id,reveal_authority_id=None,allow_partial=False,consume_tail=None):
    """Cold actual issued component science, with fresh reveal before payload."""
    from types import SimpleNamespace
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as preparation
    from empirical_lawhood.runtime.prospective_experiment import SPECIFICATION_FILENAME
    if type(allow_partial) is not bool:raise TypeError("selected E4 read needs explicit partial selection")
    specification=decode_canonical_bytes(selected.payloads[SPECIFICATION_FILENAME],preparation.SelectedE4NativeComponentSpecification,
        maximum_bytes=MAX_PARENT_BYTES)
    package=_actual_package(artifact_writer,run_id)
    if (r.pin(package.issued_study.candidate,"candidate_id")!=selected.association.candidate
            or package.issued_study.source_closure!=selected.implementation or package.run_plan_id!=run_id):
        raise PermissionError("selected E4 component read changes actual original candidate/source/run")
    if allow_partial:
        return {"scientific_completion":"NOT_ESTABLISHED","scientific_qualification":"NOT_ESTABLISHED",
            "assessment":"DEFERRED","assigned_tasks":len(selected.projection.tasks),"new_native_contact_count":0}
    if reveal_authority_id is None:raise PermissionError("selected E4 protected read requires actual current reveal")
    reveal=ExternalStudyOperationAuthorityStore(artifact_writer).load(reveal_authority_id)
    binding=SimpleNamespace(issued_study=r.pin(package.issued_study,"issue_id"),
        execution_authority=r.pin(package.execution_authority,"authority_id"),reveal_authority=r.pin(reveal,"authority_id"))
    def require_current(writer):
        _,current=_require_parent_authorities_current(((binding,package),),writer)[0]
        if current!=reveal:
            raise PermissionError("selected E4 component current reveal changed during its original read")
    issued,_=_replay_parent_authority(binding,package,artifact_writer)
    plan=authenticate_current_execution_plan(package=package,issued=issued,run_id=run_id,writer=artifact_writer)
    if {v.task_id for v in plan.tasks}!={v.task_id for v in selected.projection.tasks}:
        raise PermissionError("selected E4 retained component changes exact full task census")
    entries=tuple(v for v in plan.tasks if v.capability.capability_key in (owner.NAMESPACE+".entry",owner.NAMESPACE+".phase-entry"))
    if len(entries)!=1:raise PermissionError("selected E4 retained component lacks its actual unique source entry")
    entry_task,=entries
    config_spec=tuple(v for v in entry_task.external_inputs if v.logical_artifact_id==entry_task.capability.config.artifact_id)
    if len(config_spec)!=1:raise PermissionError("selected E4 source entry lacks actual config")
    require_current(artifact_writer)
    entry=_published_input(artifact_writer,run_id,config_spec[0],owner.SelectedE4ProtectedEntryConfig)
    if specification.declaration!=entry.declaration.identity or specification.wave_id!=entry.wave_id:
        raise PermissionError("selected E4 retained component changes full programme or selected wave")
    codecs=operation_catalog()[2]
    if entry.wave_id is not None:
        locator=r.SelectedE4WaveLocator(entry.wave_id,run_id,r.pin(package,"package_id"),binding.issued_study,
            binding.execution_authority,binding.reveal_authority,r.pin(plan,"execution_plan_id"))
        observation,state=read_selected_e4_wave(writer=artifact_writer,declaration=entry.declaration,locator=locator,codecs=codecs)
        require_current(artifact_writer)
        return {**state,"observation":observation.to_document(),"scientific_qualification":"NOT_ESTABLISHED"}
    # Current issue/reveal already authenticated. Reuse exact original generic
    # receipt/dependency/publication owner, without providers or native entry.
    from empirical_lawhood.api.recursive_qualified_parents import _collect_receipt_closure,_verify_receipt_closure
    semantic=retained_output_artifact_plane(package,plan,artifact_writer,codecs)
    prefixes=tuple(sorted(v.capability_key for v in package.registry.capabilities))
    with semantic.read_context() as writer:
        closure=_collect_receipt_closure(package,plan,writer,reveal,prefixes)
        require_current(writer)
        receipts=_verify_receipt_closure(writer,closure)
        products=[];retained=[]
        for task in plan.tasks:
            receipt=receipts[task.task_id]
            if task.capability.capability_key.startswith("matrix-selected-e4."):
                from empirical_lawhood.api.recursive_qualified_parents import _output_payload
                for logical in receipt.output_logical_artifacts:
                    kind=codecs[logical.payload_schema]
                    require_current(writer)
                    raw=_output_payload(writer,receipt,logical,MAX_PARENT_BYTES)
                    value=decode_canonical_bytes(raw,kind,maximum_bytes=MAX_PARENT_BYTES)
                    if value.canonical_bytes()!=raw:raise PermissionError("selected E4 tail substitutes canonical scientific output")
                    products.append((logical.logical_artifact_id,value.to_document()))
                    retained.append((value,receipt,logical))
        if consume_tail is not None:
            writer.require_verification_snapshot()
            require_current(writer)
            result=consume_tail(writer=writer,package=package,plan=plan,entry=entry,
                receipts=receipts,products=tuple(retained),reveal=reveal)
        writer.require_verification_snapshot()
    if consume_tail is not None:
        require_current(artifact_writer)
        return result
    banks=tuple(value for value in entry_task.external_inputs if value.expected_payload_schema==p.SelectedE4PhaseBank.SCHEMA)
    if len(banks)!=1:raise PermissionError("selected E4 assessment omits its exact original comparator source bank")
    require_current(artifact_writer)
    bank=_published_input(artifact_writer,run_id,banks[0],p.SelectedE4PhaseBank)
    if bank.identity!=entry.bank:raise PermissionError("selected E4 assessment substitutes its original comparator source bank")
    result={"programme":entry.programme.identity.to_document(),"groups":entry.scope_group_ids,
        "original_comparator_training":original_comparator_training(bank.forecast_design.package),
        "assigned_cases":len(entry.scope_cases),"scientific_completion":"COMPLETE_ASSIGNED_ASSESSMENT",
        "scientific_qualification":"NOT_ESTABLISHED","products":tuple(products),"new_native_contact_count":0}
    require_current(artifact_writer)
    return result
