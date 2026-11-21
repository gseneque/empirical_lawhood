# SPDX-License-Identifier: MPL-2.0
"""Prepare descendants from complete original histories and exact endpoint phase.

This owner derives selections only. The existing trajectory/equilibrium API
authors and executes them through ordinary source, resource and native custody.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageSelection, PassageRegion, decimal_number, roster
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_read import RetainedFirstPassagePath
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import contains
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_protocol import physical_settings, stochastic_path
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_history import read_physical_history
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import ReferenceTrajectorySelection, prepare_reference_trajectory
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import ReferenceEquilibriumSelection, prepare_reference_equilibrium
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs
from empirical_lawhood.domains.rubisco.rubisco_response.weighted_path_resampling import WeightedResamplingEvidence, assess_weighted_resampling


@dataclass(frozen=True,slots=True)
class WeightedBinMap(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/rubisco-response/weighted-bin-map'
    VERSION: ClassVar[str]='1.0.0'
    ensemble_id: str
    regions: tuple[PassageRegion,...]
    outside_bin_id: str

    def __post_init__(self):
        validate_stable_id(self.ensemble_id)
        validate_stable_id(self.outside_bin_id)
        roster(self.regions,PassageRegion,'region_id')
        if self.outside_bin_id in {r.region_id for r in self.regions}:
            raise ValueError('weighted bins must retain a distinct unassigned-coordinate bin')
        for index,first in enumerate(self.regions):
            for second in self.regions[index+1:]:
                if len(first.lower)!=len(second.lower) or all(a<d and c<b for a,b,c,d in zip(first.lower,first.upper,second.lower,second.upper,strict=True)):
                    raise ValueError('weighted bins overlap or change their coordinate denominator')

    def bin_for(self,coordinates):
        matches=tuple(r.region_id for r in self.regions if contains(r,coordinates))
        if len(matches)>1:
            raise ValueError('weighted coordinate enters overlapping bins')
        return matches[0] if matches else self.outside_bin_id


@dataclass(frozen=True,slots=True)
class WeightedContinuationRule(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/rubisco-response/weighted-continuation-rule'
    VERSION: ClassVar[str]='1.0.0'
    rule_id: str
    initial_passages: FirstPassageSelection
    resampling_selection: ObjectIdentity
    bins: tuple[WeightedBinMap,...]
    next_dynamics: ReferenceDynamicsSettings
    stochastic_seed: int
    target_physical_steps: int
    maximum_boundary_energy_error_kj_mol: Decimal
    maximum_boundary_gradient_error_kj_mol_per_angstrom: Decimal

    def __post_init__(self):
        validate_stable_id(self.rule_id)
        exact(self.initial_passages,FirstPassageSelection)
        exact(self.resampling_selection,ObjectIdentity)
        exact(self.next_dynamics,ReferenceDynamicsSettings)
        roster(self.bins,WeightedBinMap,'ensemble_id')
        if tuple(b.ensemble_id for b in self.bins)!=tuple(e.ensemble_id for e in self.initial_passages.ensembles):
            raise ValueError('continuation must retain a bin map for every original ensemble')
        for bins,ensemble in zip(self.bins,self.initial_passages.ensembles,strict=True):
            if any(len(region.lower)!=len(ensemble.coordinate_window.cv_kinds) for region in bins.regions):
                raise ValueError('continuation changes the selected coordinate denominator')
        if type(self.stochastic_seed) is not int or not 0<=self.stochastic_seed<2**128:
            raise ValueError('continuation requires its prospective PCG64DXSM stream-derivation seed')
        if type(self.target_physical_steps) is not int or self.target_physical_steps<=self.next_dynamics.steps:
            raise ValueError('continuation needs an explicit total physical horizon beyond one segment')
        for name in ('maximum_boundary_energy_error_kj_mol', 'maximum_boundary_gradient_error_kj_mol_per_angstrom'):
            decimal_number(getattr(self, name), name)
            if getattr(self, name)<0:
                raise ValueError('continuation boundary limits must be nonnegative')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.rule_id,self)


@dataclass(frozen=True,slots=True)
class PreparedWeightedChild(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/rubisco-response/prepared-weighted-child'
    VERSION: ClassVar[str]='1.0.0'
    path_id: str
    parent_path_id: str
    root_path_id: str
    ensemble_id: str
    run_id: str
    original_history: tuple[ObjectIdentity,...]
    start_physical_step: int
    selection: ReferenceTrajectorySelection | ReferenceEquilibriumSelection

    def __post_init__(self):
        for value in (self.path_id,self.parent_path_id,self.root_path_id,self.ensemble_id,self.run_id):
            validate_stable_id(value)
        if (type(self.original_history) is not tuple or not self.original_history
                or any(type(p) is not ObjectIdentity for p in self.original_history)
                or type(self.start_physical_step) is not int or self.start_physical_step<=0
                or type(self.selection) not in (ReferenceTrajectorySelection,ReferenceEquilibriumSelection)
                or self.selection.phase_source!=self.original_history[-1]):
            raise ValueError('weighted child loses its exact original history, endpoint phase source or clock')


@dataclass(frozen=True,slots=True)
class PreparedWeightedContinuation(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/rubisco-response/prepared-weighted-continuation'
    VERSION: ClassVar[str]='1.0.0'
    preparation_id: str
    rule: WeightedContinuationRule
    resampling: WeightedResamplingEvidence
    assessor_source: ObjectIdentity
    children: tuple[PreparedWeightedChild,...]
    scope: str='EXACT_ORIGINAL_PHASE_CONTINUATION_WITHOUT_RATE_OR_ENSEMBLE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.preparation_id)
        exact(self.rule,WeightedContinuationRule)
        exact(self.resampling,WeightedResamplingEvidence)
        exact(self.assessor_source,ObjectIdentity)
        roster(self.children,PreparedWeightedChild,'path_id',allow_empty=True)
        if (self.rule.resampling_selection!=self.resampling.selection.identity
                or {c.path_id for c in self.children}!={r.path.path_id for r in self.resampling.offspring}
                or self.scope!='EXACT_ORIGINAL_PHASE_CONTINUATION_WITHOUT_RATE_OR_ENSEMBLE_ADMISSION'):
            raise ValueError('weighted continuation drops an offspring or changes its prospective rule')
        rows={r.path.path_id:r for r in self.resampling.offspring}
        for child in self.children:
            row=rows[child.path_id]
            if (child.parent_path_id!=row.parent_path_id or child.original_history!=row.path.history
                    or child.start_physical_step!=row.path.physical_step
                    or child.ensemble_id!=row.path.ensemble_id or child.run_id!=row.path.run_id):
                raise ValueError('weighted child substitutes its selected ancestor or original clock')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.preparation_id,self)


@dataclass(frozen=True,slots=True)
class RetainedWeightedHistory:
    path_id: str
    segments: tuple[RetainedFirstPassagePath,...]

    def __post_init__(self):
        validate_stable_id(self.path_id)
        if type(self.segments) is not tuple or not self.segments or any(type(s) is not RetainedFirstPassagePath for s in self.segments):
            raise ValueError('weighted history needs every selected original segment')


def _read_history(*,state,history,rule,ensemble,bins,assessor_source):
    roots=tuple(p for p in rule.initial_passages.paths if p.configuration==history.segments[0].config.identity)
    if len(roots)!=1 or (roots[0].ensemble_id,roots[0].run_id)!=(state.ensemble_id,state.run_id):
        raise ValueError('weighted history changes its original selected root or run')
    report=read_physical_history(segments=history.segments,ensemble=ensemble,assessor_source=assessor_source,
        maximum_boundary_energy_error_kj_mol=rule.maximum_boundary_energy_error_kj_mol,
        maximum_boundary_gradient_error_kj_mol_per_angstrom=rule.maximum_boundary_gradient_error_kj_mol_per_angstrom)
    if (report['history']!=state.history or report['phase']!=state.phase or report['physical_step']!=state.physical_step
            or report['path_disposition']!='HORIZON_CENSORED' or report['physical_step']!=report['selected_steps']
            or any(r is None or r['native_error'] is not None for r in report['original_reports'])
            or report['physical_step']+rule.next_dynamics.steps>rule.target_physical_steps
            or physical_settings(history.segments[0].config).step_seconds!=rule.next_dynamics.step_seconds):
        raise ValueError('active weighted parent changes its original history, endpoint, clock or continuation horizon')
    if bins.bin_for(report['arrays']['coordinates'][-1])!=state.bin_id:
        raise ValueError('weighted resampling changes the independently read endpoint bin')
    return dict(report,root=roots[0],source=history.segments[-1])


def prepare_weighted_continuation(*,rule,resampling,histories,assessor_source):
    """Derive all children before authoring; perform no force or native entry."""
    exact(rule,WeightedContinuationRule)
    exact(resampling,WeightedResamplingEvidence)
    exact(assessor_source,ObjectIdentity)
    if rule.resampling_selection!=resampling.selection.identity:
        raise ValueError('weighted continuation substitutes the prospective resampling rule')
    assess_weighted_resampling(resampling)
    active=tuple(p for p in resampling.original_paths if p.disposition=='ACTIVE')
    if (type(histories) is not tuple or any(type(h) is not RetainedWeightedHistory for h in histories)
            or tuple(h.path_id for h in histories)!=tuple(p.path_id for p in active)):
        raise ValueError('weighted continuation omits or reorders an active original history')
    ensembles={e.ensemble_id:e for e in rule.initial_passages.ensembles}
    maps={b.ensemble_id:b for b in rule.bins}
    for bins in rule.bins:
        if not {bins.outside_bin_id,*(r.region_id for r in bins.regions)}.issubset(resampling.selection.bin_ids):
            raise ValueError('resampling selection omits a prospective coordinate bin')
    workspace=sum(sum(physical_settings(s.config).steps+1 for s in h.segments)*4096
        +max((s.config.selection.physical_atom_count for s in h.segments),default=0)*3*8*64 for h in histories)
    parents={h.path_id:h for h in histories}
    workspace+=sum(parents[row.parent_path_id].segments[-1].config.selection.physical_atom_count*3*8*4
        for row in resampling.offspring)
    if workspace>rule.initial_passages.maximum_projection_bytes:
        raise ValueError('complete weighted histories exceed the selected continuation workspace allocation')
    readouts={}
    for state,history in zip(active,histories,strict=True):
        if state.ensemble_id not in ensembles:
            raise ValueError('weighted parent changes its selected original ensemble')
        readouts[state.path_id]=_read_history(state=state,history=history,rule=rule,ensemble=ensembles[state.ensemble_id],
            bins=maps[state.ensemble_id],assessor_source=assessor_source)
    children,phases=[],{}
    used_seeds={s.config.selection.settings.random_seed for h in histories for s in h.segments if stochastic_path(s.config)}
    for row in resampling.offspring:
        parent=readouts[row.parent_path_id]
        source=parent['source']
        config=source.config
        kwargs=dict(prototype=config.original.selection,representation=source.representation,phase_source=row.path.history[-1],
            initial_angstrom=parent['coordinates'],initial_velocity_nm_per_ps=parent['velocities'],
            criteria=config.selection.criteria,density_guess_policy=config.selection.density_guess_policy)
        if stochastic_path(config):
            token=sha256(rule.canonical_bytes()+row.path.path_id.encode('ascii')).hexdigest()
            seed=int(token[:32],16)
            if seed in used_seeds:
                raise ValueError('prospective stochastic continuation stream collides with another original or child stream')
            used_seeds.add(seed)
            settings=replace(config.selection.settings,settings_id='settings.weighted-bath.'+token,
                dynamics=rule.next_dynamics,random_seed=seed)
            selection,raw=prepare_reference_equilibrium(**kwargs,settings=settings,window=None,convention=None)
        else:
            selection,raw=prepare_reference_trajectory(**kwargs,settings=rule.next_dynamics)
        if selection.phase_bytes.object_fingerprint!=row.path.phase.object_fingerprint:
            raise AssertionError('prepared weighted child changes exact original endpoint bytes')
        child=PreparedWeightedChild(row.path.path_id,row.parent_path_id,parent['root'].path_id,row.path.ensemble_id,
            row.path.run_id,row.path.history,row.path.physical_step,selection)
        children.append(child)
        phases[child.path_id]=raw
    children=tuple(sorted(children,key=lambda c:c.path_id))
    digest=sha256(rule.canonical_bytes()+resampling.canonical_bytes()+assessor_source.canonical_bytes()
        +b''.join(c.canonical_bytes() for c in children)).hexdigest()
    prepared=PreparedWeightedContinuation('preparation.weighted-continuation.'+digest,rule,resampling,assessor_source,children)
    recheck_original_native_outputs(tuple(s for h in histories for s in h.segments),description='weighted continuation')
    return dict(prepared=prepared,phase_bytes=phases,parent_readouts=readouts,new_native_calls=0)
