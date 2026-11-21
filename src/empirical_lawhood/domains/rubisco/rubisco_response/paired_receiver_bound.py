# SPDX-License-Identifier: MPL-2.0
"""One scalar bound for a fixed paired formation quadrature.

For a *supplied enclosing joint error hull*, linear support gives an exact
bound. Molecular coverage and the cost of obtaining it are separate premises.
No scalar receiver, small indicator or diagnostic reference result supplies
those premises. The six-output kinetic indicator keeps its original contract.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import isqrt
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_nonempty, validate_stable_id
from empirical_lawhood.science.models.time import InformationCutoff
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import roster
from empirical_lawhood.domains.rubisco.rubisco_response.policy_indicator import JointErrorVertex, cutoff_precedes, exact_vector, pre_action_cutoff


CORRECTIONS = ('coordinate-and-restraint','hidden-state-feedback','nonlinear-and-direct-mutation',
    'preparation','quadrature','sampling')
PREMISES = ('before-omitted-work','complete-error-decomposition','joint-molecular-coverage','selected-estimator-and-ensemble')
ADDED_COSTS = ('development','failed-and-uncertain-work','fallback','molecular-transfer','observation',
    'operator-construction-and-updates','preparation','qualification','verification')


def periodic_receiver_omission_coefficient(cell_lengths_angstrom):
    """Bound the bare paired center integral using its actual periodic domain.

    Each minimum-image distance lies in [0, D/2], where D is the box
    diagonal. Thus xi lies in [-D/2, D/2] under every probability measure.
    At a shared center, |g_M-g_W| <= 1000*k*D. Positive trapezoid weights
    sum to the center span L, so omission about zero has |Q_k| <= 1000*k*D*L.
    This does not bound the corrections from that integral to an activation
    barrier. It needs neither a trajectory nor assumptions of cancellation.
    """
    if (type(cell_lengths_angstrom) is not tuple or len(cell_lengths_angstrom)!=3
            or any(type(x) is not Decimal or not x.is_finite() or x<=0 for x in cell_lengths_angstrom)):
        raise ValueError('periodic receiver bound requires three positive exact orthorhombic cell lengths')
    square=sum((Fraction(x)**2 for x in cell_lengths_angstrom),Fraction(0))
    scale=10**12
    lower=isqrt(square.numerator*scale**2//square.denominator)
    upper=Fraction(lower,scale)
    if upper**2<square:
        upper+=Fraction(1,scale)
    from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational
    return dict(cell_lengths_angstrom=tuple(str(x) for x in cell_lengths_angstrom),
        cell_diagonal_squared_angstrom2=rational(square),
        paired_coordinate_span_upper_angstrom=rational(upper),
        coefficient_j_mol_per_kj_mol_angstrom2_per_angstrom=rational(1000*upper),
        formula='abs(Q_k) <= coefficient * k * (s_max-s_min)',
        approximation_error_formula='abs(Q_hat-Q_k) <= abs(Q_hat) + coefficient * k * (s_max-s_min)',
        integration_rule='POSITIVE_COMPOSITE_TRAPEZOID_WEIGHTS_SUM_TO_CENTER_SPAN',
        geometry='ORTHORHOMBIC_MINIMUM_IMAGE_DISTANCE_12_MINUS_DISTANCE_23',
        measure_scope='ANY_NORMALIZED_WT_AND_MUTANT_CONFIGURATIONAL_MEASURES_IN_THE_SAME_CELL',
        scope='BARE_DISCRETE_RESTRAINED_CENTER_INTEGRAL_NOT_ACTIVATION_BARRIER',
        activation_correction_bound_j_mol=None,new_native_calls=0)


def assess_periodic_receiver_omission_coefficient(cell_lengths_angstrom, retained):
    """Verify the outward norm enclosure by exact squared inequalities."""
    if (type(cell_lengths_angstrom) is not tuple or len(cell_lengths_angstrom)!=3
            or any(type(x) is not Decimal or not x.is_finite() or x<=0 for x in cell_lengths_angstrom)):
        raise ValueError('periodic receiver assessor requires its exact positive cell lengths')
    def fraction(key):
        value=retained[key]
        return Fraction(value['numerator'],value['denominator'])
    # This reader uses neither the producer nor its integer-square-root step.
    squared=sum((Fraction(x)*Fraction(x) for x in cell_lengths_angstrom),Fraction(0))
    diagonal=fraction('paired_coordinate_span_upper_angstrom')
    correct=(tuple(retained['cell_lengths_angstrom'])==tuple(str(x) for x in cell_lengths_angstrom)
        and fraction('cell_diagonal_squared_angstrom2')==squared and diagonal>0
        and diagonal**2>=squared and (diagonal-Fraction(1,10**12))**2<squared
        and fraction('coefficient_j_mol_per_kj_mol_angstrom2_per_angstrom')==1000*diagonal
        and retained['geometry']=='ORTHORHOMBIC_MINIMUM_IMAGE_DISTANCE_12_MINUS_DISTANCE_23'
        and retained['integration_rule']=='POSITIVE_COMPOSITE_TRAPEZOID_WEIGHTS_SUM_TO_CENTER_SPAN'
        and retained['formula']=='abs(Q_k) <= coefficient * k * (s_max-s_min)'
        and retained['approximation_error_formula']=='abs(Q_hat-Q_k) <= abs(Q_hat) + coefficient * k * (s_max-s_min)'
        and retained['measure_scope']=='ANY_NORMALIZED_WT_AND_MUTANT_CONFIGURATIONAL_MEASURES_IN_THE_SAME_CELL'
        and retained['scope']=='BARE_DISCRETE_RESTRAINED_CENTER_INTEGRAL_NOT_ACTIVATION_BARRIER'
        and retained['activation_correction_bound_j_mol'] is None and retained['new_native_calls']==0)
    return dict(numerical_disposition='SATISFIED' if correct else 'FALSIFIED',
        molecular_domain_coverage='CONDITIONAL_ON_THE_AUTHENTICATED_SHARED_CELL_AND_COORDINATE_CONVENTION',
        activation_barrier_bound='UNEVALUABLE',physical_rate_admission='UNEVALUABLE',new_native_calls=0)


@dataclass(frozen=True, slots=True)
class ReceiverBoundPremise(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/receiver-bound-premise'
    premise_id: str
    disposition: A
    evidence: ObjectIdentity | None
    available_at: InformationCutoff | None
    argument: str

    def __post_init__(self):
        if self.premise_id not in PREMISES or type(self.disposition) is not A:
            raise ValueError('receiver bound changes a required scientific premise')
        validate_nonempty(self.argument,field_name='argument')
        if (self.evidence is None)!=(self.available_at is None):
            raise ValueError('receiver premise must retain its evidence availability')
        if self.evidence is not None:
            exact(self.evidence,ObjectIdentity)
            exact(self.available_at,InformationCutoff)
        if self.disposition is A.SATISFIED and self.evidence is None:
            raise ValueError('receiver premise cannot be satisfied without original evidence')


@dataclass(frozen=True, slots=True)
class ReceiverShortcutCost(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/receiver-shortcut-cost'
    cost_id: str
    avoided_reference_cost: tuple[Exact, Exact] | None
    added_costs: tuple[tuple[str, tuple[Exact, Exact] | None], ...]
    measurement_and_conversion_sources: tuple[ObjectIdentity, ...]
    cost_unit: str

    def __post_init__(self):
        validate_stable_id(self.cost_id)
        if (type(self.added_costs) is not tuple or tuple(name for name,_ in self.added_costs)!=ADDED_COSTS
                or self.cost_unit not in {'USD_TOTAL_COST','SECONDS_SELECTED_SERIAL_RESOURCE'}):
            raise ValueError('receiver shortcut must retain every added cost in one selected unit')
        from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import interval
        for bounds in (self.avoided_reference_cost,*(bounds for _,bounds in self.added_costs)):
            if bounds is not None:
                interval(bounds,positive=False)
                if bounds[0].fraction<0:
                    raise ValueError('receiver shortcut cannot subtract an uncharged negative expense')
        identities(self.measurement_and_conversion_sources,allow_empty=True)
        if (self.avoided_reference_cost is not None or any(b is not None for _,b in self.added_costs)) and not self.measurement_and_conversion_sources:
            raise ValueError('receiver shortcut needs the actual cost and conversion evidence')


@dataclass(frozen=True, slots=True)
class PairedReceiverBoundInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/paired-receiver-bound-input'
    input_id: str
    paired_case: ObjectIdentity
    estimator: ObjectIdentity
    quadrature: ObjectIdentity
    node_ids: tuple[str, ...]
    weights_angstrom: tuple[Exact, ...]
    vertices: tuple[JointErrorVertex, ...]
    paired_error_tolerance_j_mol: Exact
    interpretation: str
    information_cutoff: InformationCutoff
    premises: tuple[ReceiverBoundPremise, ...]
    omitted_work: tuple[ObjectIdentity, ...]
    requires_omitted_work_outputs: bool
    costs: ReceiverShortcutCost
    sources: tuple[ObjectIdentity, ...]
    correction_ids: tuple[str, ...] = CORRECTIONS
    error_meaning: str = 'SIGNED_PAIRED_QUADRATURE_ERROR_WITH_EXPLICIT_REMAINDER_COORDINATES'

    def __post_init__(self):
        validate_stable_id(self.input_id)
        for pin in (self.paired_case,self.estimator,self.quadrature):
            exact(pin,ObjectIdentity)
        if (type(self.node_ids) is not tuple or not self.node_ids or len(set(self.node_ids))!=len(self.node_ids)
                or len(self.node_ids)>1024):
            raise ValueError('receiver bound needs its complete finite ordered quadrature')
        for name in self.node_ids:
            validate_stable_id(name)
        exact_vector(self.weights_angstrom,len(self.node_ids))
        if not any(v.fraction for v in self.weights_angstrom):
            raise ValueError('zero quadrature weights cannot evade the selected molecular contribution')
        roster(self.vertices,JointErrorVertex,'vertex_id',allow_empty=True)
        for vertex in self.vertices:
            exact_vector(vertex.parameter_errors,2*len(self.node_ids)+len(CORRECTIONS))
        exact(self.paired_error_tolerance_j_mol,Exact)
        if self.paired_error_tolerance_j_mol.fraction<=0:
            raise ValueError('receiver bound requires a selected positive physical error tolerance')
        if self.interpretation not in {'RIGOROUS_BOUND','CALIBRATED_BOUND','DEVELOPMENT_HEURISTIC'}:
            raise ValueError('receiver bound loses its scientific interpretation')
        pre_action_cutoff(self.information_cutoff)
        roster(self.premises,ReceiverBoundPremise,'premise_id')
        if tuple(p.premise_id for p in self.premises)!=PREMISES:
            raise ValueError('receiver bound omits a scientific coverage or causal premise')
        identities(self.omitted_work,allow_empty=True)
        if type(self.requires_omitted_work_outputs) is not bool:
            raise TypeError('receiver bound must disclose whether it needs the work being omitted')
        exact(self.costs,ReceiverShortcutCost)
        identities(self.sources)
        required={self.paired_case,self.estimator,self.quadrature,*self.omitted_work,*self.costs.measurement_and_conversion_sources}
        required.update(p.evidence for p in self.premises if p.evidence is not None)
        if not required.issubset(self.sources):
            raise ValueError('receiver bound drops an original source, work contract or cost evidence')
        if (self.correction_ids!=CORRECTIONS
                or self.error_meaning!='SIGNED_PAIRED_QUADRATURE_ERROR_WITH_EXPLICIT_REMAINDER_COORDINATES'):
            raise ValueError('receiver bound changes its correction census or error meaning')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.input_id,self)


@dataclass(frozen=True, slots=True)
class PairedReceiverBound(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/paired-receiver-bound'
    result_id: str
    selected_input: ObjectIdentity
    signed_vertex_errors_j_mol: tuple[Exact, ...]
    paired_error_interval_j_mol: tuple[Exact, Exact] | None
    absolute_error_bound_j_mol: Exact | None
    scope: str = 'EXACT_DECLARED_CONVEX_HULL_SUPPORT_NOT_MOLECULAR_COVERAGE'
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.result_id)
        exact(self.selected_input,ObjectIdentity)
        if (self.selected_input.object_schema,self.selected_input.object_version)!=(PairedReceiverBoundInput.SCHEMA,PairedReceiverBoundInput.VERSION):
            raise ValueError('receiver bound substitutes its selected input revision')
        exact_vector(self.signed_vertex_errors_j_mol,len(self.signed_vertex_errors_j_mol))
        from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import interval
        if self.paired_error_interval_j_mol is not None:
            interval(self.paired_error_interval_j_mol,positive=False)
            exact(self.absolute_error_bound_j_mol,Exact)
            if not self.signed_vertex_errors_j_mol or self.absolute_error_bound_j_mol.fraction<0:
                raise ValueError('empty support cannot acquire an error bound')
        elif self.signed_vertex_errors_j_mol or self.absolute_error_bound_j_mol is not None:
            raise ValueError('missing joint support must retain an unknown bound')
        if (self.scope!='EXACT_DECLARED_CONVEX_HULL_SUPPORT_NOT_MOLECULAR_COVERAGE'
                or type(self.new_native_calls) is not int or self.new_native_calls!=0):
            raise ValueError('receiver support arithmetic cannot grant molecular coverage or native work')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id,self)


def bound_paired_receiver(selection, *, result_id):
    exact(selection,PairedReceiverBoundInput)
    n=len(selection.node_ids)
    errors=[]
    for vertex in selection.vertices:
        values=tuple(v.fraction for v in vertex.parameter_errors)
        errors.append(sum((w.fraction*(values[n+i]-values[i]) for i,w in enumerate(selection.weights_angstrom)),Fraction(0))
            +sum(values[2*n:],Fraction(0)))
    bounds=(Exact.of(min(errors)),Exact.of(max(errors))) if errors else None
    return PairedReceiverBound(result_id,selection.identity,tuple(Exact.of(v) for v in errors),bounds,
        Exact.of(max(map(abs,errors))) if errors else None)


def assess_paired_receiver_bound(selection, retained):
    """Check the dual linear functional independently of the bound producer."""
    exact(selection,PairedReceiverBoundInput)
    exact(retained,PairedReceiverBound)
    if retained.selected_input!=selection.identity:
        raise ValueError('receiver assessor changes the exact selected error problem')
    coefficients=tuple(-v.fraction for v in selection.weights_angstrom)+tuple(v.fraction for v in selection.weights_angstrom)+(Fraction(1),)*len(CORRECTIONS)
    projections=tuple(sum((a*b.fraction for a,b in zip(coefficients,v.parameter_errors,strict=True)),Fraction(0)) for v in selection.vertices)
    current=tuple(v.fraction for v in retained.signed_vertex_errors_j_mol)
    expected_bounds=None if not projections else (min(projections),max(projections))
    actual_bounds=None if retained.paired_error_interval_j_mol is None else tuple(v.fraction for v in retained.paired_error_interval_j_mol)
    actual_absolute=None if retained.absolute_error_bound_j_mol is None else retained.absolute_error_bound_j_mol.fraction
    correct=(current==projections and actual_bounds==expected_bounds
        and actual_absolute==(max(map(abs,projections)) if projections else None))
    reasons=set()
    if not correct:
        reasons.add('INDEPENDENT_SUPPORT_EQUATIONS_FALSIFIED')
    if not projections:
        reasons.add('JOINT_ERROR_SET_UNAVAILABLE')
    if selection.interpretation=='DEVELOPMENT_HEURISTIC':
        reasons.add('HEURISTIC_CANNOT_ADMIT_OMITTED_WORK')
    elif selection.interpretation=='CALIBRATED_BOUND':
        # A finite calibration set does not supply simultaneous molecular
        # coverage or a valid rule under repeated stopping opportunities.
        # This narrow receiver contract has no risk-spending procedure.
        reasons.add('CALIBRATION_HAS_NO_ADMITTED_SIMULTANEOUS_STOPPING_COVERAGE')
    for premise in selection.premises:
        if premise.disposition is not A.SATISFIED:
            reasons.add('UNSUPPORTED_PREMISE.'+premise.premise_id)
        if premise.available_at is not None and not cutoff_precedes(premise.available_at,selection.information_cutoff):
            reasons.add('UNAVAILABLE_BEFORE_DECISION.'+premise.premise_id)
    if selection.requires_omitted_work_outputs:
        reasons.add('BOUND_REQUIRES_THE_WORK_IT_CLAIMS_TO_AVOID')
    if not selection.omitted_work:
        reasons.add('NO_CONCRETE_OMITTED_WORK_CONTRACT')
    if projections and max(map(abs,projections))>selection.paired_error_tolerance_j_mol.fraction:
        reasons.add('PAIRED_ERROR_EXCEEDS_SELECTED_TOLERANCE')
    cost=selection.costs
    added=None if any(bounds is None for _,bounds in cost.added_costs) else sum((bounds[1].fraction for _,bounds in cost.added_costs),Fraction(0))
    avoided=None if cost.avoided_reference_cost is None else cost.avoided_reference_cost[0].fraction
    if added is None or avoided is None:
        reasons.add('COMPLETE_NET_WORK_SAVING_UNEVALUABLE')
    elif avoided<=added:
        reasons.add('COMPLETE_ADDED_COST_NOT_STRICTLY_LESS_THAN_AVOIDED_COST')
    from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational
    return dict(selection=selection.identity.to_document(),retained_result=retained.identity.to_document(),
        numerical_disposition='SATISFIED' if correct else 'FALSIFIED',
        mathematical_scope=retained.scope,
        shortcut_disposition='CONDITIONAL_CANDIDATE_WITHIN_REVIEWED_PREMISES' if not reasons else 'RETAIN_NATIVE_REFERENCE',
        reason_codes=tuple(sorted(reasons)),
        conservative_avoided_cost=None if avoided is None else rational(avoided),
        conservative_added_cost=None if added is None else rational(added),cost_unit=cost.cost_unit,
        new_native_calls=0,physical_rate_admission='UNEVALUABLE',biological_predictive_validity='UNEVALUABLE')
