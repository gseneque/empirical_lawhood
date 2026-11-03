# SPDX-License-Identifier: MPL-2.0
"""Explicit operational controls; derive exact task cells from frozen phase owners."""
from dataclasses import dataclass,replace
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_stable_id
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit,ExecutionResourceTaskCellSpec,NonTimeResourceBudget,ProgressLivenessContract)
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection


@dataclass(frozen=True,slots=True)
class SelectedE4OperationalResources(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/operational-resources"
    record_id:str
    controls:ExecutionResourceSelection
    source_request_limits:tuple[tuple[str,int],...]
    native_progress:ProgressLivenessContract
    maximum_attempts:int

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.controls) is not ExecutionResourceSelection:raise TypeError("selected E4 needs exact explicit resource controls")
        self.controls.__post_init__()
        if self.controls.task_cells or len(self.controls.child_token_limits)!=1:
            raise ValueError("selected E4 resource controls derive all task cells and select one explicit child capacity")
        if (type(self.source_request_limits) is not tuple or any(type(v) is not tuple or len(v)!=2 for v in self.source_request_limits)
                or tuple(k for k,_ in self.source_request_limits)!=tuple(sorted({k for k,_ in self.source_request_limits}))
                or any(type(v) is not int or v<0 for _,v in self.source_request_limits)
                or type(self.maximum_attempts) is not int or self.maximum_attempts not in (1,2)
                or type(self.native_progress) is not ProgressLivenessContract):
            raise ValueError("selected E4 requires explicit phase source limits, native progress and attempts")
        self.native_progress.__post_init__()

    def for_component(self,*,component_id,budgets,phases,native_groups):
        """Only code-owned generated census enters this pure resource projection."""
        self.__post_init__()
        if set(budgets)!=set(phases) or set(native_groups)-set(budgets):
            raise ValueError("selected E4 resource projection changes actual complete operation census")
        limits=dict(self.source_request_limits)
        if set(phases.values())-set(limits):raise ValueError("selected E4 omits an explicit phase source-request budget")
        capacity,=self.controls.child_token_limits
        native_count=len(native_groups)
        if (native_count>capacity.physical_execution_token_limit
                or native_count*(self.maximum_attempts-1)>capacity.retry_token_limit):
            raise ValueError("selected E4 complete component exceeds explicit native/retry capacity")
        cells=[]
        for node,budget in sorted(budgets.items()):
            budget.__post_init__()
            if (budget.wall_time_seconds is not None or budget.gpu_devices!=0 or
                    any(type(v) is not int or v<0 for v in (budget.memory_bytes,budget.output_bytes,budget.source_scan_bytes))
                    or budget.memory_bytes==0 or budget.memory_bytes>self.controls.aggregate_memory_ceiling_bytes):
                raise ValueError("selected E4 budget exceeds selected finite aggregate or changes non-time policy")
            native=node in native_groups
            cells.append(ExecutionResourceTaskCellSpec("cell."+node,node,capacity.child_id,
                native_groups.get(node),"preparation."+node if native else None,self.maximum_attempts,int(native),int(native),native,
                NonTimeResourceBudget("budget."+node,budget.cpu_cores,budget.memory_bytes,budget.output_bytes,limits[phases[node]],budget.source_scan_bytes),
                replace(self.native_progress,contract_id="liveness."+node) if native else None,None,None))
        return replace(self.controls,envelope_spec_id=self.controls.envelope_spec_id+"."+component_id,task_cells=tuple(cells),
            child_token_limits=(ChildResourceTokenLimit(capacity.child_id,native_count,native_count*(self.maximum_attempts-1)),))


def derive_selected_e4_resources(declaration,tail,selection):
    from .selected_e4_native_bindings import PHASES,NATIVE,global_node,local_node
    from .selected_e4_method_bindings import operations_for_programme,method_node,adjudication_operation
    if type(selection) is not SelectedE4OperationalResources:raise TypeError("selected E4 needs its explicit operational resource profile")
    selection.__post_init__()
    required={*PHASES,"phase-collect",*operations_for_programme(declaration.programme)}
    if set(dict(selection.source_request_limits))!=required:
        raise ValueError("selected E4 request limits must cover exactly native and selected scientific phases")
    result=[];all_native=0
    for wave in declaration.programme.waves:
        budgets={};phases={};native_groups={}
        for phase in ("entry","reduce"):
            node=global_node(declaration.programme,phase,wave.wave_id);budgets[node]=dict(declaration.budgets.phase_budgets)[phase];phases[node]=phase
        node=global_node(declaration.programme,"adjudicate",wave.wave_id)
        budgets[node]=declaration.budgets.collector_budget;phases[node]="phase-collect"
        for case in declaration.programme.cases:
            if case.root_id not in wave.root_ids:continue
            for phase in PHASES:
                if phase in ("entry","reduce"):continue
                node=local_node(case.root_id,phase);budgets[node]=dict(declaration.budgets.phase_budgets)[phase];phases[node]=phase
                if phase in NATIVE:native_groups[node]=case.independent_group_id
        all_native+=len(native_groups)
        result.append((wave.wave_id,selection.for_component(component_id=wave.wave_id,budgets=budgets,phases=phases,native_groups=native_groups)))
    capacity,=selection.controls.child_token_limits
    if all_native>capacity.physical_execution_token_limit or all_native*(selection.maximum_attempts-1)>capacity.retry_token_limit:
        raise ValueError("selected E4 complete frozen phase exceeds explicitly selected total physical capacity")
    programme=declaration.programme
    budgets={global_node(programme,"phase-entry"):dict(declaration.budgets.phase_budgets)["entry"],
        global_node(programme,"phase-collect"):declaration.budgets.collector_budget}
    phases={global_node(programme,"phase-entry"):"entry",global_node(programme,"phase-collect"):"phase-collect"}
    for operation,budget in tail.resources.phase_budgets:
        node=method_node(programme.identity,operation);budgets[node]=budget;phases[node]=operation
    terminal=adjudication_operation(programme);producer=operations_for_programme(programme)[-1]
    node=method_node(programme.identity,terminal)
    budgets[node]=dict(tail.resources.phase_budgets)[producer];phases[node]=producer
    result.append(("assessment",selection.for_component(component_id="assessment",budgets=budgets,phases=phases,native_groups={})))
    return tuple(sorted(result))
