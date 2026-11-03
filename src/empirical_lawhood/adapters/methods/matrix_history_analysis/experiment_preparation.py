# SPDX-License-Identifier: MPL-2.0
"""Descriptive E2 selection over original dedicated services, independent of E1."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.experimental_design import IndependentUnit,UnitAllocation,UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_relative_locator,validate_stable_id
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind,ExperimentCensus,ExperimentDependency,
    ExperimentPreparation,PreparedExperimentInputs)
from .records import MatrixHistoryAllocation,MatrixHistoryAnalysisConfig

PROTOCOL_ID='matrix.history.descriptive-programme'


def _pin(value,kind):
    if type(value) is not ObjectIdentity or (value.object_schema,value.object_version)!=(kind.SCHEMA,kind.VERSION):
        raise ValueError('E2 selector substitutes an original allocation/analysis edition')
    value.__post_init__()


@dataclass(frozen=True,slots=True)
class MatrixHistoryProgrammeSpecification(CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-history-analysis/programme-specification'
    specification_id:str
    allocation:ObjectIdentity
    analysis:ObjectIdentity
    source_receipt_paths:tuple[str,...]
    result_relative_root:str
    mode:str='ANALYZE_RETAINED'

    def __post_init__(self):
        validate_stable_id(self.specification_id);validate_relative_locator(self.result_relative_root)
        _pin(self.allocation,MatrixHistoryAllocation);_pin(self.analysis,MatrixHistoryAnalysisConfig)
        if (type(self.source_receipt_paths) is not tuple or self.source_receipt_paths!=tuple(sorted(set(self.source_receipt_paths)))
                or len(self.source_receipt_paths)>256):
            raise ValueError('E2 source receipts must be explicit unique ordered retained locators')
        for path in self.source_receipt_paths:validate_relative_locator(path)
        if self.mode not in ('ANALYZE_RETAINED','READ_RETAINED','ACQUIRE_AND_ANALYZE'):
            raise ValueError('E2 programme mode is outside the declared dedicated workflow')

    @property
    def identity(self):return ObjectIdentity.from_record(self.specification_id,self)


@dataclass(frozen=True,slots=True)
class MatrixHistoryProgrammeInputs:
    allocation:MatrixHistoryAllocation|None=None
    analysis:MatrixHistoryAnalysisConfig|None=None

    def __post_init__(self):
        for value,kind in ((self.allocation,MatrixHistoryAllocation),(self.analysis,MatrixHistoryAnalysisConfig)):
            if value is not None:
                if type(value) is not kind:raise TypeError('E2 copied inputs require their exact original owners')
                value.__post_init__()


@dataclass(frozen=True,slots=True)
class MatrixHistoryProgrammePlan(CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-history-analysis/programme-plan'
    record_id:str
    specification:MatrixHistoryProgrammeSpecification
    allocation:MatrixHistoryAllocation
    analysis:MatrixHistoryAnalysisConfig
    source_snapshot:ObjectIdentity
    environment_id:str
    output_root:str
    workers:int

    def __post_init__(self):
        validate_stable_id(self.record_id);validate_stable_id(self.environment_id)
        if (type(self.specification) is not MatrixHistoryProgrammeSpecification or type(self.source_snapshot) is not ObjectIdentity
                or type(self.allocation) is not MatrixHistoryAllocation or type(self.analysis) is not MatrixHistoryAnalysisConfig):
            raise TypeError('E2 programme retains exact science and original source selections')
        self.specification.__post_init__();self.source_snapshot.__post_init__()
        self.allocation.__post_init__();self.analysis.__post_init__()
        if (self.allocation.identity!=self.specification.allocation or self.analysis.identity!=self.specification.analysis
                or self.analysis.source.allocation!=self.allocation.identity):
            raise ValueError('E2 programme substitutes its original exact allocation/analysis/source')
        if not self.output_root or type(self.workers) is not int or self.workers<1:
            raise ValueError('E2 programme requires explicit storage and worker selection')

    @property
    def identity(self):return ObjectIdentity.from_record(self.record_id,self)


def bind_inputs(specification,records,*,files=None):
    if set(records)-{'allocation','analysis'} or files:raise ValueError('E2 accepts only its exact original allocation and analysis')
    inputs=MatrixHistoryProgrammeInputs(**records)
    for value,pin in ((inputs.allocation,specification.allocation),(inputs.analysis,specification.analysis)):
        if value is not None and value.identity!=pin:raise ValueError('E2 copied input substitutes its selected exact identity')
    if inputs.allocation is not None and inputs.analysis is not None and inputs.analysis.source.allocation!=inputs.allocation.identity:
        raise ValueError('E2 copied analysis and source allocation differ')
    return PreparedExperimentInputs({},inputs)


def prepare(specification,*,execution,method_inputs=None,**_kwargs):
    specification.__post_init__()
    inputs=MatrixHistoryProgrammeInputs() if method_inputs is None else method_inputs
    if type(inputs) is not MatrixHistoryProgrammeInputs:raise TypeError('E2 requires its registered exact original input selection')
    inputs.__post_init__()
    dependencies=[]
    for name,value,pin in (('allocation',inputs.allocation,specification.allocation),('analysis',inputs.analysis,specification.analysis)):
        if value is None:dependencies.append(ExperimentDependency('e2.'+name,DependencyKind.EXTERNAL_INPUT,'Supply original E2 '+name+' bytes.',name))
        elif value.identity!=pin:raise ValueError('E2 preparation substitutes its exact selected '+name)
    if specification.mode=='ACQUIRE_AND_ANALYZE':
        dependencies.append(ExperimentDependency('e2.parallel-native-entry',DependencyKind.SOFTWARE,
            'The dedicated produce_matrix_histories owner is serial. Use existing source export/import commands or select retained source receipts; this facade does not claim a four-worker native lowering.'))
    for name,kind in (('workers',DependencyKind.ENVIRONMENT),('environment_id',DependencyKind.ENVIRONMENT),
            ('source_snapshot',DependencyKind.ENVIRONMENT),('output_root',DependencyKind.STORAGE)):
        if getattr(execution,name) is None:dependencies.append(ExperimentDependency('e2.execution.'+name.replace('_','-'),kind,'Select explicit '+name+'.'))
    allocation=programme=None
    if inputs.allocation is not None:
        original=inputs.allocation
        units=tuple(sorted((IndependentUnit(value.history_id,original.allocation_id,value.family_id,('fine','primary'),original.exposure!='PROPOSED_UNRUN')
            for value in original.roots),key=lambda value:value.unit_id))
        allocation=UnitAllocation('projection.'+specification.specification_id,(original.identity,),units,
            tuple(UnitRoleAssignment(value.unit_id,'descriptive') for value in units))
    if inputs.allocation is not None and inputs.analysis is not None and all(getattr(execution,name) is not None
            for name in ('workers','environment_id','source_snapshot','output_root')):
        programme=MatrixHistoryProgrammePlan('plan.'+specification.specification_id,specification,inputs.allocation,inputs.analysis,
            execution.source_snapshot,execution.environment_id,execution.output_root,execution.workers)
    # The original closed E2 allocation fixes 256 assigned independent histories.
    counts=(('descriptive',256),)
    census=ExperimentCensus(counts,counts if programme is not None else (('descriptive',0),),
        (('descriptive-analysis',256),),(('result',1),),0)
    return ExperimentPreparation(specification.identity,census,tuple(sorted(dependencies,key=lambda value:value.code)),
        allocation=allocation,execution=execution,specification_record=specification,programme=programme)
