# SPDX-License-Identifier: MPL-2.0
"""Restrained-center thermodynamic integration from original equilibrium traces.

For fixed k and Cartesian configurational measure, dA_k(s)/ds=k(s-<xi>).
The integral is a restrained free-energy difference. No barrier, transmission
coefficient, physical rate or unrestrained measure correction is inferred.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import math
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_records import EquilibriumReweightingSelection, _number
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_read import read_equilibrium_reweighting, recheck_reweighting_originals, validate_reweighting_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_science import statistical_inefficiency
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import AtomicTransformation, validate_atomic_transformation
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational


FORMATION_REQUIREMENTS = (
    'activation-dividing-surface-and-reactant-normalization',
    'complete-chemical-alternative-and-preparation-coverage',
    'finite-restraint-and-coordinate-measure-correction',
    'quadrature-discretization-error',
    'stationary-ensemble-and-sampling-uncertainty',
    'transmission-prefactor-and-effective-network-connection',
)


@dataclass(frozen=True, slots=True)
class RestrainedFormationNode(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/restrained-formation-node'
    node_id: str
    center_angstrom: Decimal
    wt_trace_ids: tuple[str, ...]
    mutant_trace_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.node_id)
        _number(self.center_angstrom,'restraint center')
        for rows in (self.wt_trace_ids,self.mutant_trace_ids):
            if type(rows) is not tuple or not rows or rows!=tuple(sorted(set(rows))):
                raise ValueError('formation node needs every selected independent or dependent trace')
            for row in rows:
                validate_stable_id(row)
        if set(self.wt_trace_ids)&set(self.mutant_trace_ids):
            raise ValueError('one original trace cannot supply both mutation arms')


@dataclass(frozen=True, slots=True)
class RestrainedFormationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/restrained-formation-selection'
    selection_id: str
    paired_case: RubiscoPairedCase
    equilibrium: EquilibriumReweightingSelection
    nodes: tuple[RestrainedFormationNode, ...]
    force_constant_kj_mol_angstrom2: Decimal
    estimator_protocol: ObjectIdentity
    coordinate_correspondence: AtomicTransformation
    maximum_split_integral_disagreement_j_mol: Decimal | None = None
    scope: str = 'FIXED_RESTRAINED_CENTER_INTEGRAL_NOT_ACTIVATION_FREE_ENERGY'
    quadrature_rule: str = 'ORDERED_COMPOSITE_TRAPEZOID'
    measure: str = 'UNCONSTRAINED_CARTESIAN_CONFIGURATIONS_FIXED_CELL_AND_TEMPERATURE'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.paired_case,RubiscoPairedCase)
        exact(self.equilibrium,EquilibriumReweightingSelection)
        exact(self.estimator_protocol,ObjectIdentity)
        exact(self.coordinate_correspondence,AtomicTransformation)
        if (self.coordinate_correspondence.case!=self.paired_case.identity
                or self.coordinate_correspondence.kind!='FINITE_SEQUENCE_SUBSTITUTION'):
            raise ValueError('formation requires the complete finite paired atomic transformation')
        _number(self.force_constant_kj_mol_angstrom2,'restraint stiffness',positive=True)
        if self.maximum_split_integral_disagreement_j_mol is not None:
            _number(self.maximum_split_integral_disagreement_j_mol,'split-integral tolerance',positive=True)
        if type(self.nodes) is not tuple or not 2<=len(self.nodes)<=1024:
            raise ValueError('formation estimator needs a complete finite multi-center interval')
        for node in self.nodes:
            exact(node,RestrainedFormationNode)
        centers=tuple(Fraction(n.center_angstrom) for n in self.nodes)
        if centers!=tuple(sorted(set(centers))) or len({n.node_id for n in self.nodes})!=len(self.nodes):
            raise ValueError('formation centers must be unique and strictly increasing in physical order')
        names=tuple(t for n in self.nodes for ids in (n.wt_trace_ids,n.mutant_trace_ids) for t in ids)
        if len(names)!=len(set(names)) or set(names)!={t.trace_id for t in self.equilibrium.traces}:
            raise ValueError('formation quadrature must use the complete selected trace denominator exactly once')
        if len({e.temperature_kelvin for e in self.equilibrium.ensembles})!=1:
            raise ValueError('paired formation cannot join different temperatures')
        if any(e.coordinate_window.cv_kinds!=('DISTANCE_DIFFERENCE',) for e in self.equilibrium.ensembles):
            raise ValueError('formation estimator requires one explicit ordered C-H-O distance difference')
        if (self.scope!='FIXED_RESTRAINED_CENTER_INTEGRAL_NOT_ACTIVATION_FREE_ENERGY'
                or self.quadrature_rule!='ORDERED_COMPOSITE_TRAPEZOID'
                or self.measure!='UNCONSTRAINED_CARTESIAN_CONFIGURATIONS_FIXED_CELL_AND_TEMPERATURE'):
            raise ValueError('formation estimator cannot change its measure, integral or barrier meaning')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id,self)

    @property
    def weights_angstrom(self):
        centers=tuple(Fraction(n.center_angstrom) for n in self.nodes)
        weights=[Fraction(0) for _ in centers]
        for i,(left,right) in enumerate(zip(centers[:-1],centers[1:],strict=True)):
            weights[i]+=(right-left)/2
            weights[i+1]+=(right-left)/2
        return tuple(weights)


def validate_restrained_formation_inputs(selection,sources):
    exact(selection,RestrainedFormationSelection)
    capacity=validate_reweighting_inputs(selection.equilibrium,sources)
    by_trace={s.trace_id:s for s in sources}
    by_ensemble={e.ensemble_id:e for e in selection.equilibrium.ensembles}
    traces={t.trace_id:t for t in selection.equilibrium.traces}
    arm_operators={}
    arm_sources={}
    for node in selection.nodes:
        for arm,names,material in (('WT',node.wt_trace_ids,selection.paired_case.parent),
                                  ('MUTANT',node.mutant_trace_ids,selection.paired_case.mutant)):
            for name in names:
                source=by_trace[name]
                selected=source.config.selection
                window=selected.window
                if (source.representation.material!=material or window is None
                        or window.cv_kinds!=('DISTANCE_DIFFERENCE',)
                        or window.centers!=(node.center_angstrom,)
                        or window.force_constants!=(selection.force_constant_kj_mol_angstrom2,)):
                    raise ValueError('formation trace changes material, coordinate, stiffness or selected center')
                ensemble=by_ensemble[traces[name].ensemble_id]
                key=(ensemble.prototype,ensemble.coordinate_window.cv_atom_ids,
                     source.config.original.selection.cell.lengths_angstrom)
                if arm_operators.setdefault(arm,key)!=key:
                    raise ValueError('a formation arm changes its reference potential, atom correspondence or cell')
                arm_sources.setdefault(arm,source)
    if arm_operators['WT'][2]!=arm_operators['MUTANT'][2]:
        raise ValueError('paired restrained formation requires a matched fixed cell')
    left,right=(arm_sources[arm].representation for arm in ('WT','MUTANT'))
    validate_atomic_transformation(selection.coordinate_correspondence,left,right,case=selection.paired_case)
    ordered=[]
    for arm,representation in (('WT',left),('MUTANT',right)):
        by_id={atom.atom_id:i for i,atom in enumerate(representation.atoms)}
        atoms=tuple(by_id[name] for name in arm_operators[arm][1][0])
        if tuple(representation.atoms[i].atomic_number for i in atoms)!=(6,1,8):
            raise ValueError('formation receiver requires the ordered physical carbon, hydrogen and oxygen')
        ordered.append(atoms)
    mapping=dict(selection.coordinate_correspondence.common_atoms)
    if tuple(mapping.get(i) for i in ordered[0])!=ordered[1]:
        raise ValueError('paired formation coordinates do not follow the authenticated physical atom correspondence')
    # The existing complete equilibrium operation and its independent reader
    # fix natural masses, constraints=NONE and mass_repartitioning=False.
    # No constrained-dynamics configuration is admitted by that owner.
    return capacity


def restrained_center_statistics(*,selection,coordinates,eligible):
    """Finite paired estimates and coupled block draws, never coverage by fiat.

    Coordinates come from the independent authenticated projection. Failed or
    incomplete traces keep their prefix but cannot contribute a node estimate.
    """
    import numpy as np
    exact(selection,RestrainedFormationSelection)
    trace_ids=tuple(t.trace_id for t in selection.equilibrium.traces)
    if set(coordinates)!=set(trace_ids) or set(eligible)!=set(trace_ids):
        raise ValueError('formation statistics changes the full trace census')
    values={}
    for name in trace_ids:
        q=np.asarray(coordinates[name])
        if (q.dtype.kind not in 'fiu' or q.ndim!=1 or not np.isfinite(q).all()
                or type(eligible[name]) is not bool):
            raise ValueError('formation statistics needs finite real coordinate series and explicit eligibility')
        values[name]=q.astype('<f8',copy=False)
    centers={t:float(n.center_angstrom) for n in selection.nodes for t in (*n.wt_trace_ids,*n.mutant_trace_ids)}
    stiffness=float(selection.force_constant_kj_mol_angstrom2)*1000
    with np.errstate(over='raise',invalid='raise'):
        observations={name:stiffness*(centers[name]-q) for name,q in values.items()}
    if any(not np.isfinite(v).all() for v in observations.values()):
        raise ValueError('formation receiver is not representable in J/mol/angstrom')
    weights=selection.weights_angstrom

    def integrate(indices=None):
        means=[]
        for node in selection.nodes:
            arms=[]
            for names in (node.wt_trace_ids,node.mutant_trace_ids):
                if any(not eligible[t] or len(observations[t])==0 for t in names):
                    arms.append(None)
                    continue
                samples=[observations[t] if indices is None else observations[t][indices[t]] for t in names]
                arms.append(math.fsum(float(v) for x in samples for v in x)/sum(map(len,samples)))
            means.append(tuple(arms))
        paired=tuple(None if any(x is None for x in arms) else arms[1]-arms[0] for arms in means)
        # Integrate from the retained binary64 sample values with exact
        # rational quadrature weights; no ambient Decimal rounding is used.
        total=None if any(x is None for x in paired) else sum((w*Fraction(x) for w,x in zip(weights,paired,strict=True)),Fraction(0))
        return tuple(means),paired,total

    means,paired,point=integrate()
    # Assess drift of the selected paired integral itself. The inherited
    # basin/MBAR contrasts are different observables and cannot supply this
    # receiver's stationarity diagnostic by substitution.
    split_integrals=[]
    if all(eligible[name] and len(x)>=2 for name,x in observations.items()):
        for half in (0,1):
            indices={name:np.arange(0,len(x)//2) if half==0 else np.arange(len(x)//2,len(x))
                for name,x in observations.items()}
            split_integrals.append(integrate(indices)[2])
    else:
        split_integrals=[None,None]
    split_disagreement=(None if any(x is None for x in split_integrals)
        else abs(split_integrals[1]-split_integrals[0]))
    criteria=selection.equilibrium.criteria
    groups={}
    for trace in selection.equilibrium.traces:
        groups.setdefault(trace.resampling_group_id,[]).append(trace)
    incomplete=tuple(name for name,traces in sorted(groups.items()) if
        len({len(observations[t.trace_id]) for t in traces})!=1
        or any(not eligible[t.trace_id] or len(observations[t.trace_id])==0 for t in traces))
    rng=np.random.Generator(np.random.PCG64DXSM(criteria.bootstrap_seed))
    draws=[]
    for _ in range(criteria.bootstrap_replicates):
        if incomplete:
            draws.append(None)
            continue
        indices={}
        for _,traces in sorted(groups.items()):
            n=len(observations[traces[0].trace_id])
            block=traces[0].block_samples
            starts=rng.integers(n,size=(n+block-1)//block,dtype=np.int64)
            selected=((starts[:,None]+np.arange(block))%n).ravel()[:n]
            indices.update((t.trace_id,selected) for t in traces)
        draws.append(integrate(indices)[2])
    correlations={name:statistical_inefficiency(x) for name,x in observations.items()}
    reasons=[]
    split_tolerance=selection.maximum_split_integral_disagreement_j_mol
    if split_disagreement is None:
        reasons.append(('paired-integral','RECEIVER_SPLIT_HALVES_UNAVAILABLE'))
    elif split_tolerance is None:
        reasons.append(('paired-integral','RECEIVER_SPLIT_TOLERANCE_UNSELECTED'))
    elif split_disagreement>Fraction(split_tolerance):
        reasons.append(('paired-integral','RECEIVER_SPLIT_INTEGRAL_DISAGREEMENT'))
    for trace in selection.equilibrium.traces:
        name=trace.trace_id
        g=correlations[name]
        if not eligible[name] or not len(observations[name]):
            reasons.append((name,'COMPLETE_ORIGINAL_TRACE_UNAVAILABLE'))
        if not g['resolved']:
            reasons.append((name,'RECEIVER_CORRELATION_UNRESOLVED'))
        if len(observations[name])//trace.block_samples<criteria.minimum_blocks:
            reasons.append((name,'TOO_FEW_RECEIVER_CORRELATION_BLOCKS'))
        if g['inefficiency'] is not None and trace.block_samples<Fraction(criteria.block_inefficiency_multiplier)*Fraction(g['inefficiency']):
            reasons.append((name,'RECEIVER_BLOCK_SHORTER_THAN_SELECTED_INEFFICIENCY_MULTIPLE'))
    rank=math.ceil(Fraction(criteria.simultaneous_coverage)*(criteria.bootstrap_replicates+1))
    half_width=None
    if point is not None and all(x is not None for x in draws) and rank<=len(draws):
        half_width=sorted(abs(x-point) for x in draws)[rank-1]
    else:
        reasons.append(('paired-integral','COMPLETE_BLOCK_UNCERTAINTY_UNAVAILABLE'))
    return dict(node_ids=tuple(n.node_id for n in selection.nodes),
        quadrature_weights_angstrom=tuple(rational(w) for w in weights),
        arm_mean_forces_j_mol_angstrom=means,paired_mean_forces_j_mol_angstrom=paired,
        paired_restrained_free_energy_j_mol=None if point is None else rational(point),
        quadrature_rule=selection.quadrature_rule,correlation=correlations,
        split_half_integrals_j_mol=tuple(None if x is None else rational(x) for x in split_integrals),
        split_half_disagreement_j_mol=None if split_disagreement is None else rational(split_disagreement),
        maximum_split_integral_disagreement_j_mol=None if split_tolerance is None else str(split_tolerance),
        stationarity_scope='FINITE_SPLIT_AND_CORRELATION_DIAGNOSTICS_NOT_PROOF_OF_EQUILIBRIUM',
        bootstrap=dict(method='COUPLED_CIRCULAR_BLOCKS_FIXED_LENGTH_COMPLETE_COUNTS',
            seed=criteria.bootstrap_seed,generator='NUMPY_PCG64DXSM',numpy_version=np.__version__,
            incomplete_groups=incomplete,requested_replicates=criteria.bootstrap_replicates,
            joint_paired_integrals_j_mol=tuple(None if x is None else rational(x) for x in draws),
            failed_replicates=sum(x is None for x in draws),simultaneous_coverage=str(criteria.simultaneous_coverage),
            maximum_deviation_j_mol=None if half_width is None else rational(half_width),
            interpretation='CONDITIONAL_BLOCK_BOOTSTRAP_ESTIMATE_NOT_GUARANTEED_COVERAGE'),
        selected_receiver_diagnostics='UNEVALUABLE' if reasons else 'SATISFIED',reasons=tuple(sorted(set(reasons))),
        formation_requirements=FORMATION_REQUIREMENTS,activation_free_energy_j_mol=None,
        formation_rate_ratio=None,physical_rate_admission='UNEVALUABLE',evidence_scope=selection.scope)


def read_restrained_formation(*,selection,sources,assessor_source):
    validate_restrained_formation_inputs(selection,sources)
    equilibrium,arrays=read_equilibrium_reweighting(selection=selection.equilibrium,sources=sources,assessor_source=assessor_source)
    coordinates={t.trace_id:arrays[t.trace_id+'.coordinates'][:,0] for t in selection.equilibrium.traces}
    eligible={name:row['eligible_for_complete_window_fit'] for name,row in equilibrium['trace_census'].items()}
    report=restrained_center_statistics(selection=selection,coordinates=coordinates,eligible=eligible)
    recheck_reweighting_originals(sources)
    return dict(selection=selection.identity.to_document(),assessor_source=assessor_source.to_document(),
        equilibrium=equilibrium,formation=report,new_native_calls=0,new_reference_evaluations=0,
        evidence_scope=selection.scope),arrays
