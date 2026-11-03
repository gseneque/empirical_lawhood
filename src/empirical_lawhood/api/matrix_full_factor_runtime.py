# SPDX-License-Identifier: MPL-2.0
"""Ordinary authored/issued task custody for the PURE original-history follow-up."""

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as owner
from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody,CurrentIssuedTaskCustody,CurrentIssuedTaskCustodySupplier
from empirical_lawhood.api.matrix_full_factor_custody import authenticate_original_full_factor_reference
from empirical_lawhood.api.recursive_qualified_parents import _actual_package,_replay_parent_authority
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input


def _pin(value,field):return ObjectIdentity.from_record(getattr(value,field),value)


def _graph(draft):
    if draft.development_study is None or draft.prospective_draft is not None:
        raise PermissionError('full factor runtime requires its ordinary PURE analysis lifecycle')
    declarations={row.capability_key:row for row in owner.operation_declarations()}
    if any(row.selection.capability_key not in declarations for row in draft.operations):
        raise PermissionError('full factor runtime changes its exact finite PURE operation roster')
    configs={row.node_id:decode_recursive_config_input(row,declarations[row.selection.capability_key].registration()).record for row in draft.operations}
    reductions=tuple(value for value in configs.values() if type(value) is owner.ScheduledFullFactorReduceConfig)
    if len(reductions)!=1:raise PermissionError('full factor runtime lacks one complete original-roster reducer')
    reduction,=reductions
    expected=owner.lower(reduction.scope,reduction.resources,draft_id=draft.draft_id,
        campaign=draft.campaign,protected_root=None)
    if draft!=expected:raise PermissionError('full factor runtime changes the exact full roster, links, roots or immutable configs')
    return reduction.scope,configs


def _original_grants(writer,scope,source=None,*,control_reader=None,current_access=None):
    if not scope.protected:return
    waves=scope.waves if source is None else tuple(row for row in scope.waves if source.root_id in next(wave.root_ids for wave in scope.programme.waves if wave.wave_id==row.wave_id))
    if not waves:raise PermissionError('full factor case omits its actual original protected wave')
    from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess,selected_e4_authority_binding
    if current_access is not None:
        if type(current_access) is not SelectedE4CurrentAccess:
            raise TypeError('current E4 access requires its exact operation-local selection')
        current_access.require_originals(scope.waves)
    entries=[]
    for locator in waves:
        package=_actual_package(writer,locator.run_id,control_reader=control_reader)
        if _pin(package,'package_id')!=locator.package:raise PermissionError('full factor original protected package changed')
        binding=selected_e4_authority_binding(locator,current_access)
        _replay_parent_authority(binding,package,writer)
        entries.append((binding,package))
    # A prior wave's grant may expire during a later publication replay.
    # This owner samples all selected grants after its final physical guard.
    from empirical_lawhood.api.recursive_qualified_parents import _require_parent_authorities_current
    _require_parent_authorities_current(tuple(entries),writer)


class ScheduledFullFactorRuntimeSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self,supplier,*,writer,draft,codecs,directory=None,plan=None,read_access=None,payloads=None):
        self.supplier,self.writer,self.output_codecs=supplier,writer,dict(codecs)
        reference,self.configs=_graph(draft)
        self.current_access=read_access
        self.original_input_access=getattr(payloads,'original_input_access',None)
        if self.original_input_access is None or self.original_input_access.parents!=reference.produced_input_parents:
            raise PermissionError('full factor runtime lacks its actual complete original-parent bootstrap')
        self.original_input_access.require_current()
        if read_access is not None and reference.protected:
            from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess
            if type(read_access) is not SelectedE4CurrentAccess:
                raise TypeError('full factor current access requires its exact protected original wave selection')
            read_access.require_originals(reference.waves)
        self.scope,_=authenticate_original_full_factor_reference(writer=writer,reference=reference,codecs=self.output_codecs,
            current_access=read_access)
        self.custody=CurrentDevelopmentTaskCustody(writer=writer,directory=directory,plan=plan,
            payloads=payloads,original_input_access=self.original_input_access,read_access=read_access)
        self.original_custody=CurrentIssuedTaskCustody(writer=writer) if self.scope.protected else None
        # One complete original reader replay per binding. Each worker still
        # reauthenticates current grants and actual current input/dependency custody.

    def current_issued_task_custody(self):return self.original_custody

    def resolve(self,logical_artifact_ids):return self.supplier.resolve(logical_artifact_ids)
    def resolve_input(self,spec):return self.supplier.resolve_input(spec)

    def require_original_input_access(self,task,value):return self.custody.require_original_input_access(task,value)

    def prepare_full_factor_followup(self,context,runner):
        if type(runner) is not owner.ScheduledFullFactorWorker or runner.prepared_scope is not None:
            raise PermissionError('full factor requires its exact installed unprepared PURE worker')
        if self.original_custody is not None:
            with self.original_custody.preparation_scope():return self._prepare(context,runner)
        return self._prepare(context,runner)

    def _prepare(self,context,runner):
        self.original_input_access.require_current()
        if self.scope.protected:
            selected=self.configs.get(context.task_id)
            if selected is None:
                raise PermissionError('full factor task changes the actual original PURE graph')
            source=None if runner.phase=='reduce' else next(row for row in self.scope.sources
                if row.root_id==selected.source.root_id)
            # Recheck before task input/dependency custody can open protected
            # bytes, and again below after their complete exact joins.
            with self.original_custody.original_read_scope() as (writer,parent):
                _original_grants(writer,self.scope,source,control_reader=parent.plan_reader,current_access=self.current_access)
        current=self.custody.current_task(context,runner)
        _,plan,task=current
        receipts,controls=self.custody.task_inputs(context,task)
        manifest=controls.get(context.config.artifact_id)
        kind=owner.ScheduledFullFactorReduceConfig if runner.phase=='reduce' else owner.ScheduledFullFactorCaseConfig
        specs=tuple(row for row in task.external_inputs if row.logical_artifact_id==context.config.artifact_id)
        if manifest is None or len(specs)!=1:raise PermissionError('full factor task lacks exact automatic configuration custody')
        config=self.custody.control_record(manifest,kind,manifest.materialization.size_bytes)
        if (config!=self.configs.get(task.task_id) or config.fingerprint()!=context.config.content_sha256
                or config.protected!=self.scope.protected or context.outcome_access is not
                    (OutcomeAccess.EVALUATION_REVEALED if self.scope.protected else OutcomeAccess.DEVELOPMENT_VISIBLE)):
            raise PermissionError('full factor task substitutes original scope, selected PURE phase or current configuration')
        if self.scope.protected:
            source=None if runner.phase=='reduce' else next(row for row in self.scope.sources if row.root_id==config.source.root_id)
            # The existing synchronous run scope reuses immutable original
            # controls; original issue/execution/reveal grants are fresh here.
            with self.original_custody.original_read_scope() as (writer,parent):
                _original_grants(writer,self.scope,source,control_reader=parent.plan_reader,current_access=self.current_access)
        if self.custody.current_task(context,runner)!=current:
            raise PermissionError('full factor current custody changed during preparation')
        self.original_input_access.require_current()
        return runner.with_prepared_scope((context.run_id,context.task_id,context.input_materialization_ids,_pin(plan,'execution_plan_id')))


def bind_development_runtime(*,supplier,writer,directory,plan,output_codecs,read_access=None,payloads=None):
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    if payloads is None:
        _,draft,_,payloads=load_authored_wave(directory=directory,artifact_writer=writer,lazy_payloads=True,read_access=read_access)
    else:
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
        raw=payloads['draft.json'];draft=decode_canonical_bytes(raw,RecursiveStudyDraft,maximum_bytes=len(raw))
    from empirical_lawhood.api.recursive_authoring import _authenticate_experiment_instance
    from empirical_lawhood.api.matrix_full_factor_read import _inputs,_decode
    from empirical_lawhood.api.matrix_full_factor_secondary import authenticate_full_factor_target
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_preparation import ScheduledFullFactorDevelopmentSpecification,ScheduledFullFactorProtectedSpecification
    instance=_authenticate_experiment_instance(payloads=payloads,draft=draft,artifact_writer=writer)
    kind=ScheduledFullFactorProtectedSpecification if instance.specification.object_schema==ScheduledFullFactorProtectedSpecification.SCHEMA else ScheduledFullFactorDevelopmentSpecification
    specification=_decode(payloads['experiment-specification.json'],kind)
    inputs=_inputs(specification,instance,payloads)
    authenticate_full_factor_target(writer=writer,request=inputs.request,bank=inputs.bank)
    return ScheduledFullFactorRuntimeSupplier(supplier,writer=writer,draft=draft,codecs=output_codecs,directory=directory,plan=plan,
        read_access=read_access,payloads=payloads)


def validate_development_read_access(*,directory,artifact_writer,specification,instance,payloads,draft,plan,read_access):
    """Authorize exact original outcomes before generic input/product reads."""
    from empirical_lawhood.api.matrix_full_factor_read import _inputs
    from empirical_lawhood.api.selected_e4_access import SelectedE4CurrentAccess,require_current_e4_access
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_preparation import (
        ScheduledFullFactorProtectedSpecification,
    )
    if (read_access is not None and type(read_access) is not SelectedE4CurrentAccess
            or type(specification) is not ScheduledFullFactorProtectedSpecification):
        raise TypeError('full factor read access requires its exact protected original selection')
    inputs=_inputs(specification,instance,payloads)
    if not inputs.reference.protected:
        raise PermissionError('replacement original access requires the ordinary protected PURE analysis')
    if read_access is not None:read_access.require_originals(inputs.reference.waves)
    require_current_e4_access(writer=artifact_writer,originals=inputs.reference.waves,current_access=read_access)
    access=getattr(payloads,'original_input_access',None)
    if access is None or access.parents!=inputs.reference.produced_input_parents:
        raise PermissionError('full factor protected read changes its actual original-parent scope')
    access.require_current()
