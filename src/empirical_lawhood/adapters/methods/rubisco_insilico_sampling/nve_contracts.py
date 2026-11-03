# SPDX-License-Identifier: MPL-2.0
"""Selected 100 ps numerical controls, retaining the whole 96 denominator."""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from . import contracts as sampling, control_contracts as force


def unit_id(key):
    return 'control.nve.'+'.'.join(key)


def unit_ids():
    return tuple(sorted(unit_id(key) for key in sampling.trajectory_roster()))


@dataclass(frozen=True, slots=True)
class RelaxedModelSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/relaxed-model-supply'
    product_id: str
    model_assets: p.ModelAssets
    chemical_return: ObjectIdentity
    chemical_assessment: ObjectIdentity
    system: p.NativeTextFile
    relaxed_state: p.NativeTextFile

    def __post_init__(self):
        validate_stable_id(self.product_id)
        self.model_assets.__post_init__()
        for row,kind in ((self.chemical_return,force.ChemicalForceReturn),(self.chemical_assessment,force.ChemicalForceAssessment)):
            row.__post_init__()
            if row.object_schema != kind.SCHEMA:
                raise ValueError('relaxed supply substitutes actual chemical control/assessment')
        for row in (self.system,self.relaxed_state):
            row.__post_init__()
            if row.evidence.byte_count <= 0:
                raise ValueError('relaxed supply omits genuine original full native bytes')
        if PurePosixPath(self.relaxed_state.evidence.relative_path).name != 'minimized.xml':
            raise ValueError('relaxed supply replaces the actual returned relaxed State')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.product_id,self)

    @property
    def model_id(self):
        return force.model_id((self.model_assets.construct_id,self.model_assets.joint_view_id,self.model_assets.parameter_view))


@dataclass(frozen=True, slots=True)
class NVEControlPlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/nve-control-plan'
    plan_id: str
    chemical_controls: force.ChemicalForcePlan
    # Model ID, genuine relaxed supply, original definition/completion/return and
    # independent assessment. These remain explicit scientific input sources.
    admitted_parents: tuple[tuple[str,ObjectIdentity,ObjectIdentity,ObjectIdentity,ObjectIdentity,ObjectIdentity], ...]
    selected_cases: tuple[tuple[str,str,str,str,str], ...]
    workdir: str
    code_sources: tuple[tuple[str,str], ...]
    dependency_lock_sha256: str
    full_census: tuple[tuple[str,str,str,str,str], ...] = sampling.trajectory_roster()
    ensembles: tuple[tuple[str,int,int], ...] = sampling.ENSEMBLES
    integration: tuple[tuple[str,Decimal,Decimal], ...] = sampling.INTEGRATION
    numerical_window_picosecond: Decimal = Decimal('100')
    receiver_cadence_picosecond: Decimal = Decimal('10')
    receiver_contract: str = 'ALL_ELEVEN_FULL_STATES_AND_OPAQUE_CHECKPOINTS'
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.plan_id)
        self.chemical_controls.__post_init__()
        from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkCompletion
        names=tuple(row[0] for row in self.admitted_parents)
        available={row[0] for row in self.chemical_controls.selected_assets}
        if not names or names != tuple(sorted(set(names))) or set(names)-available:
            raise ValueError('NVE control omits actual independently admitted model subset')
        for _,supply,definition,completion,returned,assessment in self.admitted_parents:
            for row,kind in ((supply,RelaxedModelSupply),(definition,NativeSubworkDefinition),(completion,NativeSubworkCompletion),
                    (returned,force.ChemicalForceReturn),(assessment,force.ChemicalForceAssessment)):
                row.__post_init__()
                if row.object_schema != kind.SCHEMA:
                    raise ValueError('NVE control substitutes genuine original chemical parent custody')
        if (not self.selected_cases or self.selected_cases != tuple(sorted(set(self.selected_cases)))
                or set(self.selected_cases)-set(sampling.trajectory_roster())
                or {force.model_id(row[:3]) for row in self.selected_cases}-set(names)):
            raise ValueError('NVE control changes its explicit admitted trajectory subset')
        path=PurePosixPath(self.workdir)
        if (not path.is_absolute() or '..' in path.parts or not path.is_relative_to(p.NATIVE_WORK_ROOT)
                or str(path)==p.NATIVE_WORK_ROOT or self.workdir==self.chemical_controls.workdir):
            raise ValueError('NVE control needs a distinct fresh selected workdir')
        if not self.code_sources or tuple(row[0] for row in self.code_sources) != tuple(sorted(set(row[0] for row in self.code_sources))):
            raise ValueError('NVE control omits exact selected producing source')
        for path,digest in self.code_sources:
            if PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
                raise ValueError('NVE producing source escapes selected root')
            validate_sha256(digest)
        validate_sha256(self.dependency_lock_sha256)
        if (self.full_census!=sampling.trajectory_roster() or self.ensembles!=sampling.ENSEMBLES
                or self.integration!=sampling.INTEGRATION or self.numerical_window_picosecond!=100
                or self.receiver_cadence_picosecond!=10 or self.receiver_contract!='ALL_ELEVEN_FULL_STATES_AND_OPAQUE_CHECKPOINTS'
                or self.physical_independent_units!=0):
            raise ValueError('NVE control changes fixed 100 ps/2 fs/1 fs/seeds/full96 scientific contracts')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.plan_id,self)

    @property
    def cutoff_nanometer(self):return self.chemical_controls.cutoff_nanometer
    @property
    def temperature_kelvin(self):return self.chemical_controls.temperature_kelvin
    @property
    def platform_precision(self):return self.chemical_controls.platform_precision
    @property
    def device_index(self):return self.chemical_controls.device_index
    @property
    def deterministic_forces(self):return self.chemical_controls.deterministic_forces
    @property
    def use_cpu_pme(self):return self.chemical_controls.use_cpu_pme
    @property
    def hardware(self):return self.chemical_controls.hardware
    @property
    def interpreter_path(self):return self.chemical_controls.interpreter_path
    @property
    def interpreter_sha256(self):return self.chemical_controls.interpreter_sha256


@dataclass(frozen=True, slots=True)
class NVEControlReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/nve-control-return'
    unit_id: str
    plan: ObjectIdentity
    relaxed_supply: ObjectIdentity
    operators_completed: bool
    atom_count: int
    files: tuple[p.FileEvidence, ...]
    native_calls: tuple[ObjectIdentity, ...]
    error_text: str | None = None
    physical_independent_units: int = 0

    def __post_init__(self):
        if self.unit_id not in unit_ids() or self.plan.object_schema!=NVEControlPlan.SCHEMA or self.relaxed_supply.object_schema!=RelaxedModelSupply.SCHEMA:
            raise ValueError('NVE return substitutes actual selected control/supply')
        for row in (self.plan,self.relaxed_supply):row.__post_init__()
        if type(self.operators_completed) is not bool or type(self.atom_count) is not int or self.atom_count<0 or self.physical_independent_units!=0:
            raise ValueError('NVE return manufactures physical qualification')
        paths=tuple(row.relative_path for row in self.files)
        if paths!=tuple(sorted(set(paths))):raise ValueError('NVE return omits whole actual raw file census')
        for row in self.files:row.__post_init__()
        from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
        if tuple(row.object_id for row in self.native_calls)!=tuple(sorted(set(row.object_id for row in self.native_calls))):
            raise ValueError('NVE return changes complete actual call denominator')
        for row in self.native_calls:
            row.__post_init__()
            if row.object_schema!=NativeSubworkDefinition.SCHEMA:raise ValueError('NVE return relabels native calls')
        names={PurePosixPath(row).name for row in paths}
        required={'numerical-control.json','nve-progress.jsonl','apparatus-cuda.json','initial-full-state.xml',
            *('nve-state-'+str(i).zfill(2)+'.xml' for i in range(1,11)),
            *('nve-checkpoint-'+str(i).zfill(2)+'.bin' for i in range(11))}
        if self.operators_completed and (not self.native_calls or self.atom_count<=0 or self.error_text is not None or not required.issubset(names)):
            raise ValueError('NVE operators completed without every actual receiver/checkpoint')
        if not self.operators_completed and not self.error_text:raise ValueError('NVE adverse return omits known error')

    @property
    def identity(self):return ObjectIdentity.from_record(self.unit_id,self)


@dataclass(frozen=True, slots=True)
class NVEControlCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/nve-control-census'
    plan: ObjectIdentity
    states: tuple[tuple[str,NativeSubworkState], ...]
    physical_independent_units: int = 0

    def __post_init__(self):
        self.plan.__post_init__()
        if (self.plan.object_schema!=NVEControlPlan.SCHEMA or tuple(row[0] for row in self.states)!=unit_ids()
                or any(type(row[1]) is not NativeSubworkState for row in self.states) or self.physical_independent_units!=0):
            raise ValueError('NVE census drops unentered/adverse controls or manufactures physical qualification')


@dataclass(frozen=True, slots=True)
class NVEControlAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/nve-control-assessment'
    VERSION: ClassVar[str] = '1.1.0'
    product_id: str
    plan: ObjectIdentity
    returned: tuple[ObjectIdentity, ...]
    cases: tuple[tuple[str,A,Decimal | None,tuple[str, ...]], ...]
    refinements: tuple[tuple[str,A,Decimal | None,Decimal | None], ...]
    disposition: A
    # Exact reduced rational kJ/mol per atom from reported binary64 P and K,
    # before their rounded native total. None/None retains missing evidence.
    reported_component_excursions: tuple[tuple[str,int | None,int | None], ...]
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        self.plan.__post_init__()
        if (self.plan.object_schema!=NVEControlPlan.SCHEMA or tuple(row[0] for row in self.cases)!=unit_ids()
                or self.physical_independent_units!=0 or type(self.disposition) is not A):
            raise ValueError('NVE assessment changes complete96 or scientific scope')
        for row in self.returned:
            row.__post_init__()
            if row.object_schema!=NVEControlReturn.SCHEMA:raise ValueError('NVE assessment substitutes original returns')
        if tuple(row.object_id for row in self.returned)!=tuple(sorted(set(row.object_id for row in self.returned))):
            raise ValueError('NVE assessment repeats/reorders original actual returns')
        expected_pairs=tuple(unit_id(key).rsplit('.',1)[0] for key in sampling.trajectory_roster() if key[-1]=='primary')
        if tuple(row[0] for row in self.refinements)!=expected_pairs:
            raise ValueError('NVE assessment drops/reorders complete48 refinement pairs')
        for _,verdict,excursion,reasons in self.cases:
            if type(verdict) is not A or (excursion is not None and (type(excursion) is not Decimal or not excursion.is_finite() or excursion<0)):
                raise ValueError('NVE assessment substitutes actual numerical receiver')
            if verdict is A.SATISFIED and (excursion is None or excursion>Decimal('0.001')):
                raise ValueError('NVE positive misses fixed complete energy precision')
            if reasons!=tuple(sorted(set(reasons))):raise ValueError('NVE assessment duplicates reasons')
        if tuple(row[0] for row in self.reported_component_excursions)!=unit_ids():
            raise ValueError('NVE component diagnostic drops full96 outcomes')
        for (_,verdict,_,_),(_,numerator,denominator) in zip(self.cases,self.reported_component_excursions,strict=True):
            if numerator is None and denominator is None:
                if verdict is A.SATISFIED:raise ValueError('positive NVE omits exact reported-component diagnostic')
                continue
            if (type(numerator) is not int or type(denominator) is not int or numerator<0 or denominator<=0
                    or Fraction(numerator,denominator).as_integer_ratio()!=(numerator,denominator)):
                raise ValueError('NVE component diagnostic substitutes exact reduced rational')
            if verdict is A.SATISFIED and Fraction(numerator,denominator)>Fraction(Decimal('0.001')):
                raise ValueError('positive NVE hides reported-component precision miss')
        for _,verdict,left,right in self.refinements:
            if type(verdict) is not A or any(value is not None and (type(value) is not Decimal or not value.is_finite() or value<0) for value in (left,right)):
                raise ValueError('NVE refinement omits actual finite independent pair operands')
            if verdict is A.SATISFIED and (left is None or right is None or right>left+Decimal('0.00001')):
                raise ValueError('NVE positive refinement omits/misses fixed paired precision')
        by_case={row[0]:row for row in self.cases}
        by_component={name:None if numerator is None else Fraction(numerator,denominator)
            for name,numerator,denominator in self.reported_component_excursions}
        for name,verdict,left,right in self.refinements:
            primary,refined=by_case[name+'.primary'],by_case[name+'.refined']
            if (left,right)!=(primary[2],refined[2]):
                raise ValueError('NVE refinement substitutes its corresponding actual case operands')
            expected=A.UNEVALUABLE
            if primary[1] is A.SATISFIED and refined[1] is A.SATISFIED:
                expected=A.SATISFIED if (right<=left+Decimal('0.00001')
                    and by_component[refined[0]]<=by_component[primary[0]]+Fraction(Decimal('0.00001'))) else A.REFUSED
            elif primary[1] is A.REFUSED or refined[1] is A.REFUSED:expected=A.REFUSED
            if verdict is not expected:raise ValueError('NVE refinement hides missing/negative exact reported-component precision')
        outcomes=tuple(row[1] for row in (*self.cases,*self.refinements))
        expected=A.UNEVALUABLE if A.UNEVALUABLE in outcomes else A.REFUSED if A.REFUSED in outcomes else A.SATISFIED
        if self.disposition is not expected:raise ValueError('NVE aggregate hides missing/negative numerical outcomes')
        if any(row[1] is A.SATISFIED and row[0] not in {value.object_id for value in self.returned} for row in self.cases):
            raise ValueError('NVE assessment fabricates a positive unreturned trajectory')
