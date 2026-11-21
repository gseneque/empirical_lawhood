# SPDX-License-Identifier: MPL-2.0
"""Independent exact kinetic diagnostics on retained or analytical operands.

Rank is local differential information, never a unique fitted rate vector.
Concentration and lumping checks establish the supplied mathematical closure,
not the physical validity of its states, rates or independent biological units.
"""

from dataclasses import dataclass
from fractions import Fraction as F
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import ENDPOINT_ORDER, PARAMETER_ORDER, DissolvedGasQuery, FourStateRates, FourStateResult
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model_assessment import assess_four_state
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


def _ordered_selection(values, order, name):
    if type(values) is not tuple or not values or values != tuple(value for value in order if value in values):
        raise ValueError(name + " must retain its nonempty unique declared order")


def _rref(matrix):
    """Finite exact elimination; no floating rank threshold or singular inverse."""
    rows = [list(row) for row in matrix]
    pivots = []
    for column in range(len(rows[0])):
        found = next((i for i in range(len(pivots), len(rows)) if rows[i][column]), None)
        if found is None:
            continue
        rank = len(pivots)
        rows[rank], rows[found] = rows[found], rows[rank]
        divisor = rows[rank][column]
        rows[rank] = [value / divisor for value in rows[rank]]
        for i in range(len(rows)):
            if i != rank:
                factor = rows[i][column]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[rank], strict=True)]
        pivots.append(column)
        if len(pivots) == len(rows):
            break
    nullspace = []
    for column in range(len(rows[0])):
        if column not in pivots:
            vector = [F(0)] * len(rows[0])
            vector[column] = F(1)
            for row, pivot in zip(rows, pivots, strict=False):
                vector[pivot] = -row[column]
            nullspace.append(tuple(vector))
    return len(pivots), tuple(nullspace)


@dataclass(frozen=True, slots=True)
class EndpointIdentifiability(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/endpoint-identifiability"
    analysis_id: str
    retained_result: ObjectIdentity
    independent_numerical_assessment: ObjectIdentity
    observed_endpoints: tuple[str, ...]
    free_parameters: tuple[str, ...]
    jacobian: tuple[tuple[Exact, ...], ...]
    exact_rank: int
    nullspace: tuple[tuple[Exact, ...], ...]
    zero_parameter_ids: tuple[str, ...]
    interpretation: str = "LOCAL_UNCONSTRAINED_DIFFERENTIAL_RANK_NOT_GLOBAL_IDENTIFICATION"

    def __post_init__(self):
        validate_stable_id(self.analysis_id)
        for row in (self.retained_result, self.independent_numerical_assessment):
            exact(row, ObjectIdentity)
        _ordered_selection(self.observed_endpoints, ENDPOINT_ORDER, "observed endpoints")
        _ordered_selection(self.free_parameters, PARAMETER_ORDER, "free parameters")
        if (type(self.jacobian) is not tuple or len(self.jacobian) != len(self.observed_endpoints)
                or any(type(row) is not tuple or len(row) != len(self.free_parameters) for row in self.jacobian)):
            raise ValueError("identifiability loses the full selected derivative matrix")
        for row in self.jacobian:
            for value in row:
                exact(value, Exact)
        if type(self.nullspace) is not tuple or any(type(row) is not tuple for row in self.nullspace):
            raise ValueError("identifiability needs its complete immutable nullspace")
        for row in self.nullspace:
            for value in row:
                exact(value, Exact)
        rank, basis = _rref(tuple(tuple(value.fraction for value in row) for row in self.jacobian))
        expected_basis = tuple(tuple(Exact.of(value) for value in row) for row in basis)
        if type(self.exact_rank) is not int or self.exact_rank != rank or self.nullspace != expected_basis:
            raise ValueError("identifiability contradicts its exact rank or complete nullspace")
        if (type(self.zero_parameter_ids) is not tuple
                or self.zero_parameter_ids != tuple(p for p in self.free_parameters if p in self.zero_parameter_ids)):
            raise ValueError("zero-rate boundary census changes the selected free parameters")
        if self.interpretation != "LOCAL_UNCONSTRAINED_DIFFERENTIAL_RANK_NOT_GLOBAL_IDENTIFICATION":
            raise ValueError("local rank cannot establish global or finite-parameter identifiability")

    @property
    def local_unconstrained_nullity(self):
        return len(self.free_parameters) - self.exact_rank

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.analysis_id, self)


def assess_endpoint_identifiability(result, *, analysis_id,
                                    observed_endpoints=("kcat_c", "specificity"), free_parameters=PARAMETER_ORDER):
    """Use independently checked retained derivatives, without producer entry."""
    exact(result, FourStateResult)
    _ordered_selection(observed_endpoints, ENDPOINT_ORDER, "observed endpoints")
    _ordered_selection(free_parameters, PARAMETER_ORDER, "free parameters")
    assessed = assess_four_state(result, assessment_id=analysis_id + ".numerical")
    if assessed.disposition is not A.SATISFIED:
        raise ValueError("identifiability cannot consume failed independent kinetic arithmetic")
    entries = {(row.endpoint, row.parameter): row.derivative for row in result.sensitivities}
    matrix = tuple(tuple(entries[endpoint, parameter] for parameter in free_parameters) for endpoint in observed_endpoints)
    rank, nullspace = _rref(tuple(tuple(value.fraction for value in row) for row in matrix))
    return EndpointIdentifiability(analysis_id, assessed.result,
        ObjectIdentity.from_record(assessed.assessment_id, assessed), observed_endpoints, free_parameters, matrix, rank,
        tuple(tuple(Exact.of(value) for value in row) for row in nullspace),
        tuple(p for p in free_parameters if getattr(result.rates, p) == 0))


def _concentration_fluxes(rates, query):
    q = rates.fractions
    carbon = q["c"] * F(query.co2_um) / (q["d_c"] + q["r_c"])
    oxygen = q["o"] * F(query.o2_um) / (q["d_o"] + q["r_o"])
    normalization = 1 + q["b"] / q["a"] + carbon * (1 + q["r_c"] / q["a"]) + oxygen * (1 + q["r_o"] / q["a"])
    return q["r_c"] * carbon / normalization, q["r_o"] * oxygen / normalization


@dataclass(frozen=True, slots=True)
class ConcentrationPointFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/concentration-point-finding"
    retained_result: ObjectIdentity
    query: DissolvedGasQuery
    numerical_assessment: ObjectIdentity
    scope_matches: bool
    numerical_gate: A
    response_gate: A
    specificity_from_flux: Exact | None
    specificity_gate: A

    def __post_init__(self):
        for row in (self.retained_result, self.numerical_assessment):
            exact(row, ObjectIdentity)
        exact(self.query, DissolvedGasQuery)
        if type(self.scope_matches) is not bool:
            raise ValueError("concentration finding needs its actual rate-scope match")
        for disposition in (self.numerical_gate, self.response_gate, self.specificity_gate):
            if type(disposition) is not A:
                raise ValueError("concentration finding needs its actual assessment disposition")
        if self.specificity_from_flux is not None:
            exact(self.specificity_from_flux, Exact)
            if self.query.co2_um == 0 or self.query.o2_um == 0:
                raise ValueError("specificity from flux is undefined on a zero-gas boundary")
        elif self.specificity_gate is not A.UNEVALUABLE:
            raise ValueError("missing specificity cannot pass or fail a division that is undefined")


@dataclass(frozen=True, slots=True)
class ConcentrationResponseAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/concentration-response-assessment"
    assessment_id: str
    rates: FourStateRates
    expected_queries: tuple[DissolvedGasQuery, ...]
    findings: tuple[ConcentrationPointFinding, ...]
    complete_census: bool
    disposition: A
    interpretation: str = "RETAINED_CONDITIONAL_CONCENTRATION_RESPONSE_NOT_PHYSICAL_VALIDATION"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.rates, FourStateRates)
        _queries(self.expected_queries)
        if type(self.findings) is not tuple:
            raise ValueError("concentration assessment needs its full retained result census")
        for row in self.findings:
            exact(row, ConcentrationPointFinding)
        complete = tuple(row.query for row in self.findings) == self.expected_queries
        if type(self.complete_census) is not bool or self.complete_census != complete:
            raise ValueError("concentration assessment changes its full selected query denominator")
        if self.disposition is not _concentration_disposition(complete, self.findings):
            raise ValueError("concentration assessment changes its independent findings")
        if self.interpretation != "RETAINED_CONDITIONAL_CONCENTRATION_RESPONSE_NOT_PHYSICAL_VALIDATION":
            raise ValueError("mathematical concentration response cannot establish physical rate independence")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def _queries(queries):
    if type(queries) is not tuple or not 1 <= len(queries) <= 128:
        raise ValueError("concentration design needs its nonempty bounded explicit query census")
    for query in queries:
        exact(query, DissolvedGasQuery)
    if len({(q.co2_um, q.o2_um) for q in queries}) != len(queries):
        raise ValueError("concentration design repeats a query as another test")


def _concentration_disposition(complete, findings):
    if any(not row.scope_matches or A.FALSIFIED in (row.numerical_gate, row.response_gate, row.specificity_gate)
           for row in findings):
        return A.FALSIFIED
    if (not complete or sum(row.specificity_gate is A.SATISFIED for row in findings) < 2
            or any(row.numerical_gate is not A.SATISFIED or row.response_gate is not A.SATISFIED for row in findings)):
        return A.UNEVALUABLE
    return A.SATISFIED


def assess_concentration_response(rates, expected_queries, retained_results, *, assessment_id):
    """Assess all queries independently, keeping absent work and zero-gas limits."""
    exact(rates, FourStateRates)
    _queries(expected_queries)
    if type(retained_results) is not tuple or len(retained_results) > 128:
        raise ValueError("concentration assessment requires a bounded immutable retained census")
    q = rates.fractions
    specificity = (q["c"] * q["r_c"] / (q["d_c"] + q["r_c"])) / (q["o"] * q["r_o"] / (q["d_o"] + q["r_o"]))
    findings = []
    for i, result in enumerate(retained_results):
        exact(result, FourStateResult)
        checked = assess_four_state(result, assessment_id=assessment_id + ".numerical." + str(i))
        carbon, oxygen = _concentration_fluxes(rates, result.query)
        actual_c, actual_o = result.carboxylation_events_per_site_s.fraction, result.oxygenation_events_per_site_s.fraction
        response = A.SATISFIED if (actual_c, actual_o) == (carbon, oxygen) else A.FALSIFIED
        observed, gate = None, A.UNEVALUABLE
        if result.query.co2_um > 0 and result.query.o2_um > 0 and actual_o > 0:
            # A nonpositive oxygen flux at a positive selected gas is a failed
            # numerical result, not a replacement zero-specificity observation.
            observed = Exact.of(actual_c * F(result.query.o2_um) / (actual_o * F(result.query.co2_um)))
            gate = A.SATISFIED if observed.fraction == specificity else A.FALSIFIED
        findings.append(ConcentrationPointFinding(checked.result, result.query,
            ObjectIdentity.from_record(checked.assessment_id, checked), result.rates == rates,
            checked.disposition, response, observed, gate))
    findings = tuple(findings)
    complete = tuple(row.query for row in findings) == expected_queries
    return ConcentrationResponseAssessment(assessment_id, rates, expected_queries, findings,
        complete, _concentration_disposition(complete, findings))


@dataclass(frozen=True, slots=True)
class MarkovLumpingSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/markov-lumping-selection"
    selection_id: str
    source: ObjectIdentity
    state_ids: tuple[str, ...]
    generator: tuple[tuple[Exact, ...], ...]
    blocks: tuple[tuple[int, ...], ...]
    state_meanings: ObjectIdentity
    physical_clock: ObjectIdentity
    generator_unit: str = "s^-1"

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        for source in (self.source, self.state_meanings, self.physical_clock):
            exact(source, ObjectIdentity)
        if type(self.state_ids) is not tuple or not 2 <= len(self.state_ids) <= 64 or len(set(self.state_ids)) != len(self.state_ids):
            raise ValueError("lumping needs a complete bounded state census")
        for key in self.state_ids:
            validate_stable_id(key)
        count = len(self.state_ids)
        if (type(self.generator) is not tuple or len(self.generator) != count
                or any(type(row) is not tuple or len(row) != count for row in self.generator)):
            raise ValueError("lumping generator changes its full state denominator")
        for i, row in enumerate(self.generator):
            for value in row:
                exact(value, Exact)
            if sum(value.fraction for value in row) != 0 or any(value.fraction < 0 for j, value in enumerate(row) if i != j):
                raise ValueError("lumping generator violates continuous-time conservation or positivity")
        if (type(self.blocks) is not tuple or not self.blocks
                or any(type(block) is not tuple or not block or block != tuple(sorted(set(block)))
                    or any(type(i) is not int for i in block) for block in self.blocks)
                or tuple(sorted(self.blocks, key=lambda row: row[0])) != self.blocks
                or sorted(i for block in self.blocks for i in block) != list(range(count))):
            raise ValueError("lumping partition omits, duplicates or relabels a selected state")
        if self.generator_unit != "s^-1":
            raise ValueError("lumping cannot substitute a step index for physical time")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def _lumping_violations(selection):
    # Strong continuous-time lumpability: every state in a source block has
    # the same total outgoing rate into each target block, including itself.
    return tuple((first, other, target, Exact.of(difference))
        for block in selection.blocks for first in (block[0],) for other in block[1:]
        for target, members in enumerate(selection.blocks)
        if (difference := sum(selection.generator[other][j].fraction - selection.generator[first][j].fraction for j in members)))


@dataclass(frozen=True, slots=True)
class StrongLumpingAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/strong-lumping-assessment"
    assessment_id: str
    selection: MarkovLumpingSelection
    violations: tuple[tuple[int, int, int, Exact], ...]
    disposition: A
    interpretation: str = "EXACT_MARKOV_AGGREGATION_ONLY_NOT_STATE_OR_CLOCK_ADMISSION"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.selection, MarkovLumpingSelection)
        expected = _lumping_violations(self.selection)
        if self.violations != expected or self.disposition is not (A.FALSIFIED if expected else A.SATISFIED):
            raise ValueError("lumping assessment drops an exact outgoing-rate counterexample")
        if self.interpretation != "EXACT_MARKOV_AGGREGATION_ONLY_NOT_STATE_OR_CLOCK_ADMISSION":
            raise ValueError("lumping cannot grant physical state or clock admission")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_strong_lumping(selection, *, assessment_id):
    exact(selection, MarkovLumpingSelection)
    violations = _lumping_violations(selection)
    return StrongLumpingAssessment(assessment_id, selection, violations, A.FALSIFIED if violations else A.SATISFIED)
