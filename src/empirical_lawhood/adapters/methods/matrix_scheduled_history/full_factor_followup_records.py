# SPDX-License-Identifier: MPL-2.0
"""Explicit complete original source selection for PURE E4 structural follow-up."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .full_factor_records import ScheduledFullFactorSource, _exact, _pin, identity
from .selected_e3_e4_records import SelectedE3E4DevelopmentProgramme, SelectedE3E4CaseResult, pin
from .selected_e4_programme import SelectedE4PhaseProgramme
from .selected_e4_native_records import SelectedE4NativeCaseResult, SelectedE4NativeProgrammeDeclaration, SelectedE4WaveLocator
from .selected_e4_method_bindings import SelectedE4DevelopmentAcquisition
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorScope(CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-scope'
    record_id:str
    programme:SelectedE3E4DevelopmentProgramme|SelectedE4PhaseProgramme
    original_cases:tuple[SelectedE3E4CaseResult|SelectedE4NativeCaseResult,...]
    sources:tuple[ScheduledFullFactorSource,...]
    development:SelectedE4DevelopmentAcquisition|None
    declaration:SelectedE4NativeProgrammeDeclaration|None
    waves:tuple[SelectedE4WaveLocator,...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.programme) not in (SelectedE3E4DevelopmentProgramme,SelectedE4PhaseProgramme):
            raise TypeError('full factor scope requires its exact original selected programme')
        self.programme.__post_init__()
        protected=type(self.programme) is SelectedE4PhaseProgramme
        case_kind=SelectedE4NativeCaseResult if protected else SelectedE3E4CaseResult
        if (type(self.original_cases) is not tuple or any(type(row) is not case_kind for row in self.original_cases)
                or type(self.sources) is not tuple or any(type(row) is not ScheduledFullFactorSource for row in self.sources)
                or tuple(row.root_id for row in self.original_cases)!=tuple(row.root_id for row in self.programme.cases)
                or tuple(row.root_id for row in self.sources)!=tuple(row.root_id for row in self.programme.cases)):
            raise ValueError('full factor scope omits original observed cases or assigned coordinates')
        if protected:
            _exact(self.declaration,SelectedE4NativeProgrammeDeclaration)
            if self.development is not None or self.declaration.programme!=self.programme:
                raise ValueError('full factor protected scope changes original full declaration')
        else:
            _exact(self.development,SelectedE4DevelopmentAcquisition)
            if self.declaration is not None or self.waves or self.development.allow_partial:
                raise ValueError('full factor DEV scope invents original issued authority')
        if (type(self.waves) is not tuple or any(type(row) is not SelectedE4WaveLocator for row in self.waves)
                or tuple(row.wave_id for row in self.waves)!=tuple(sorted({row.wave_id for row in self.waves}))):
            raise ValueError('full factor scope duplicates or reorders original wave locators')
        waves={row.wave_id:row for row in self.waves}
        if protected and set(waves)!={row.wave_id for row in self.programme.waves}:
            raise ValueError('full factor scope adds an original wave outside assigned membership')
        for declared,case,source in zip(self.programme.cases,self.original_cases,self.sources,strict=True):
            case.__post_init__();source.__post_init__()
            if source.produced_input_parents!=self.sources[0].produced_input_parents or (protected
                    and source.produced_input_parents!=self.declaration.produced_input_parents):
                raise ValueError('full factor scope substitutes its complete original produced-parent census')
            state={'COMPLETED':'COMPLETED','FAILED':'FAILED','UNKNOWN':'UNKNOWN_COMPLETION','UNENTERED':'NOT_ENTERED'}[
                next(row for row in case.native if row.phase=='continue').disposition]
            if (source.programme!=self.programme.identity or source.original_case!=pin(case,'root_id')
                    or (source.root_id,source.group_id,source.source)!=(declared.root_id,declared.independent_group_id,declared.source)
                    or (case.root_id,case.group_id,case.source)!=(declared.root_id,declared.independent_group_id,declared.source)
                    or ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate)!=declared.coordinate
                    or source.source_state!=state or source.full_numerical!=case.full_assessment):
                raise ValueError('full factor scope substitutes original observed source/group/physical/continuation membership')
            for output in source.original_products:
                if protected:
                    wave=next(row for row in self.programme.waves if source.root_id in row.root_ids)
                    if waves.get(wave.wave_id)!=output.wave:
                        raise ValueError('full factor scope substitutes original producing wave/issue/reveal locator')
                elif (output.authored_directory,output.run_id,output.execution_plan)!=(
                        self.development.authored_directory,self.development.run_id,self.development.execution_plan):
                    raise ValueError('full factor scope substitutes original DEV producing run/plan')

    @property
    def identity(self):return identity(self)

    @property
    def protected(self):return type(self.programme) is SelectedE4PhaseProgramme

    @property
    def produced_input_parents(self):return self.sources[0].produced_input_parents


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorResources(CanonicalRecord):
    """Explicit operator reservations; no new scientific thresholds or defaults."""
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-resources'
    record_id:str
    phase_budgets:tuple[tuple[str,ResourceBudget],...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.phase_budgets) is not tuple or tuple(name for name,_ in self.phase_budgets)!=('assess','measure','reduce')
                or any(type(row) is not ResourceBudget for _,row in self.phase_budgets)):
            raise ValueError('full factor resources require exact measure/assess/global-reduce reservations')
        for _,row in self.phase_budgets:
            row.__post_init__()
            if row.gpu_devices!=0:raise ValueError('full factor PURE operation has no GPU implementation')

    @property
    def identity(self):return identity(self)

@dataclass(frozen=True,slots=True)
class ScheduledFullFactorSourceReference(CanonicalRecord):
    """Blind byte references; original dispositions remain in the revealed FILE."""
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-source-reference'
    root_id:str
    group_id:str
    source:ObjectIdentity
    source_artifact:ArtifactIdentity
    arrays:ArtifactIdentity|None

    def __post_init__(self):
        from empirical_lawhood.kernel.references import ArtifactIdentity
        validate_stable_id(self.root_id);validate_stable_id(self.group_id)
        if type(self.source) is not ObjectIdentity or (self.source.object_schema,self.source.object_version)!=(ScheduledFullFactorSource.SCHEMA,ScheduledFullFactorSource.VERSION):
            raise ValueError('full factor reference changes exact original source pin')
        self.source.__post_init__();_exact(self.source_artifact,ArtifactIdentity)
        if (self.source_artifact.artifact_id,self.source_artifact.payload_schema,self.source_artifact.sha256,self.source_artifact.media_type)!=(self.source.object_id,self.source.object_schema,self.source.object_fingerprint,'application/json'):raise ValueError('full factor reference changes exact case FILE bytes')
        if self.arrays is not None:_exact(self.arrays,ArtifactIdentity)

    @property
    def identity(self):return self.source


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorScopeReference(CanonicalRecord):
    """Outcome-free fixed roster and immutable external byte identities."""
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-scope-reference'
    VERSION:ClassVar[str]='2.0.0'
    record_id:str
    scope:ObjectIdentity
    scope_artifact:ArtifactIdentity
    programme:SelectedE3E4DevelopmentProgramme|SelectedE4PhaseProgramme
    sources:tuple[ScheduledFullFactorSourceReference,...]
    numerical_view_ids:tuple[str,...]
    development:SelectedE4DevelopmentAcquisition|None
    declaration:ObjectIdentity|None
    waves:tuple[SelectedE4WaveLocator,...]
    produced_input_parents:tuple[ArtifactLineageParent,...]

    def __post_init__(self):
        validate_produced_input_parents(self.produced_input_parents)
        from empirical_lawhood.kernel.references import ArtifactIdentity
        validate_stable_id(self.record_id);_exact(self.scope,ObjectIdentity);_exact(self.scope_artifact,ArtifactIdentity)
        if type(self.programme) not in (SelectedE3E4DevelopmentProgramme,SelectedE4PhaseProgramme):raise TypeError('full factor reference changes original programme')
        self.programme.__post_init__()
        if (self.scope.object_schema!=ScheduledFullFactorScope.SCHEMA or
                (self.scope_artifact.artifact_id,self.scope_artifact.payload_schema,self.scope_artifact.sha256,self.scope_artifact.media_type)!=
                (self.scope.object_id,self.scope.object_schema,self.scope.object_fingerprint,'application/json') or
                type(self.sources) is not tuple or any(type(row) is not ScheduledFullFactorSourceReference for row in self.sources) or
                tuple((row.root_id,row.group_id) for row in self.sources)!=tuple((row.root_id,row.independent_group_id) for row in self.programme.cases)):
            raise ValueError('full factor reference changes exact original scope, fixed roster or byte contract')
        for row in self.sources:row.__post_init__()
        if self.protected:
            _pin(self.declaration,(SelectedE4NativeProgrammeDeclaration,))
            if (self.development is not None or type(self.waves) is not tuple
                    or any(type(row) is not SelectedE4WaveLocator for row in self.waves)
                    or tuple(row.wave_id for row in self.waves)!=tuple(row.wave_id for row in self.programme.waves)):
                raise ValueError('full factor reference changes original protected selectors')
            for row in self.waves:row.__post_init__()
        else:
            _exact(self.development,SelectedE4DevelopmentAcquisition)
            if self.development.allow_partial or self.declaration is not None or self.waves:raise ValueError('full factor reference changes original DEV selector')
        if type(self.numerical_view_ids) is not tuple or self.numerical_view_ids!=tuple(sorted(set(self.numerical_view_ids))) or not self.numerical_view_ids:raise ValueError('full factor reference changes fixed numerical views')

    @property
    def identity(self):return identity(self)
    @property
    def protected(self):return type(self.programme) is SelectedE4PhaseProgramme


def scope_reference(scope):
    from empirical_lawhood.kernel.references import ArtifactIdentity
    artifact=ArtifactIdentity(scope.record_id,'original-full-factor-scope',scope.SCHEMA,scope.fingerprint(),'application/json',len(scope.canonical_bytes()))
    return ScheduledFullFactorScopeReference('reference.'+scope.record_id,scope.identity,artifact,scope.programme,
        tuple(ScheduledFullFactorSourceReference(row.root_id,row.group_id,row.identity,
            ArtifactIdentity(row.record_id,'original-full-factor-source',row.SCHEMA,row.fingerprint(),'application/json',len(row.canonical_bytes())),
            None if row.full_arrays is None else row.full_arrays.array_artifact) for row in scope.sources),
        tuple(sorted({view.view_id for source in scope.sources for view in (source.coordinate.primary_view,source.coordinate.fine_view)})),
        scope.development,None if scope.declaration is None else scope.declaration.identity,scope.waves,scope.produced_input_parents)
