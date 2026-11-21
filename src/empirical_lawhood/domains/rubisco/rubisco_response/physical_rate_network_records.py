# SPDX-License-Identifier: MPL-2.0
"""Complete chemical, release and encounter networks over retained rate cases."""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence, PathWeight, decimal_number, roster
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_records import PhysicalRateSelection


@dataclass(frozen=True, slots=True)
class PhysicalRateOperand(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-operand'
    VERSION: ClassVar[str] = '1.0.0'
    ensemble_id: str
    event_id: str

    def __post_init__(self):
        validate_stable_id(self.ensemble_id)
        validate_stable_id(self.event_id)


@dataclass(frozen=True, slots=True)
class PhysicalNetworkState(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-network-state'
    VERSION: ClassVar[str] = '1.0.0'
    state_id: str
    definition: ObjectIdentity
    outgoing_ensemble_id: str | None
    entry_distribution_source: ObjectIdentity | None
    terminal_outcome: str | None
    released_3pga: int
    released_2phosphoglycolate: int
    substrate_ready: bool

    def __post_init__(self):
        validate_stable_id(self.state_id)
        exact(self.definition, ObjectIdentity)
        if any(type(v) is not int or v < 0 for v in (self.released_3pga,self.released_2phosphoglycolate)) or type(self.substrate_ready) is not bool:
            raise ValueError('physical network requires explicit product counts and substrate readiness')
        if self.terminal_outcome is None:
            validate_stable_id(self.outgoing_ensemble_id)
            exact(self.entry_distribution_source,ObjectIdentity)
        elif (self.terminal_outcome not in {'PRODUCTIVE_RETURN','REVERSE_RETURN','COMMITTED','ESCAPED','OTHER'}
                or self.outgoing_ensemble_id is not None or self.entry_distribution_source is not None):
            raise ValueError('physical network terminal states cannot supply hidden outgoing transitions')


@dataclass(frozen=True, slots=True)
class PhysicalNetworkEntry(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-network-entry'
    VERSION: ClassVar[str] = '1.0.0'
    state_id: str
    weight: PathWeight

    def __post_init__(self):
        validate_stable_id(self.state_id)
        exact(self.weight,PathWeight)


@dataclass(frozen=True, slots=True)
class PhysicalNetworkEdge(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-network-edge'
    VERSION: ClassVar[str] = '1.0.0'
    edge_id: str
    source_state_id: str
    target_state_id: str
    rate: PhysicalRateOperand

    def __post_init__(self):
        for value in (self.edge_id,self.source_state_id,self.target_state_id):
            validate_stable_id(value)
        exact(self.rate,PhysicalRateOperand)
        if self.source_state_id == self.target_state_id:
            raise ValueError('a selected first exit cannot silently reset into the same state')


@dataclass(frozen=True, slots=True)
class PhysicalRateNetwork(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-network'
    VERSION: ClassVar[str] = '1.0.0'
    network_id: str
    role: str
    states: tuple[PhysicalNetworkState, ...]
    edges: tuple[PhysicalNetworkEdge, ...]
    initial: tuple[PhysicalNetworkEntry, ...]
    observation_times_seconds: tuple[Decimal, ...]
    maximum_probability_error: Decimal
    maximum_squared_cv_error: Decimal
    maximum_entry_log_moment_change: Decimal
    maximum_arithmetic_error: Decimal
    verification_precision_bits: int
    chemical_correspondence: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.network_id)
        if self.role not in {'CARBON_PROCESSING','OXYGEN_PROCESSING','CARBON_ENCOUNTER','OXYGEN_ENCOUNTER'}:
            raise ValueError('physical network changes its selected branch and chemical role')
        roster(self.states,PhysicalNetworkState,'state_id')
        roster(self.edges,PhysicalNetworkEdge,'edge_id')
        roster(self.initial,PhysicalNetworkEntry,'state_id')
        exact(self.chemical_correspondence,ObjectIdentity)
        states = {s.state_id:s for s in self.states}
        transient = {s.state_id for s in self.states if s.terminal_outcome is None}
        if (not transient or len(transient)==len(states) or len({states[s].outgoing_ensemble_id for s in transient}) != len(transient)
                or not {r.state_id for r in self.initial}.issubset(transient)
                or sum((r.weight.fraction for r in self.initial),Fraction()) != 1):
            raise ValueError('physical network needs its complete transient, absorbing and exact entry census')
        if len({edge.rate for edge in self.edges}) != len(self.edges):
            raise ValueError('physical network duplicates one observed transition as two rates')
        for edge in self.edges:
            if (edge.source_state_id not in transient or edge.target_state_id not in states
                    or edge.rate.ensemble_id != states[edge.source_state_id].outgoing_ensemble_id):
                raise ValueError('physical network changes the original transition source or target')
            before,after = states[edge.source_state_id],states[edge.target_state_id]
            if before.released_3pga > after.released_3pga or before.released_2phosphoglycolate > after.released_2phosphoglycolate:
                raise ValueError('initial-rate product sinks cannot silently recapture released products')
        reached = {row.state_id for row in self.initial}
        while True:
            expanded = reached | {e.target_state_id for e in self.edges if e.source_state_id in reached}
            if expanded == reached:
                break
            reached = expanded
        if reached != set(states):
            raise ValueError('physical network contains states outside the declared entry denominator')
        escapes = set(states)-transient
        while True:
            expanded = escapes | {e.source_state_id for e in self.edges if e.target_state_id in escapes}
            if expanded == escapes:
                break
            escapes = expanded
        if escapes != set(states):
            raise ValueError('physical network has a nonabsorbing closed class; its finite exit moment is unidentified')
        outcomes = {s.terminal_outcome for s in self.states if s.terminal_outcome is not None}
        processing = self.role.endswith('PROCESSING')
        required = {'PRODUCTIVE_RETURN','REVERSE_RETURN'} if processing else {'COMMITTED','ESCAPED'}
        if not required.issubset(outcomes) or not outcomes.issubset(required|{'OTHER'}):
            raise ValueError('physical network must retain both productive and reverse/escape outcomes')
        products = (2,0) if self.role.startswith('CARBON') else (1,1)
        for state in self.states:
            if state.terminal_outcome == 'PRODUCTIVE_RETURN' and (
                    (state.released_3pga,state.released_2phosphoglycolate)!=products or not state.substrate_ready):
                raise ValueError('productive processing requires complete product release and substrate-ready return')
            if (state.terminal_outcome == 'REVERSE_RETURN' and (state.released_3pga or state.released_2phosphoglycolate)
                    or not processing and (state.released_3pga or state.released_2phosphoglycolate)):
                raise ValueError('reverse/encounter outcomes cannot silently include product processing')
        times = self.observation_times_seconds
        if type(times) is not tuple or len(times)<2 or times != tuple(sorted(set(times))):
            raise ValueError('physical network requires prospective positive time queries for its complete exit law')
        for value in times:
            decimal_number(value,'network observation time',positive=True)
        for name in ('maximum_probability_error','maximum_squared_cv_error','maximum_entry_log_moment_change','maximum_arithmetic_error'):
            decimal_number(getattr(self,name),name,positive=True)
        if self.maximum_probability_error>=1 or self.maximum_arithmetic_error>=1:
            raise ValueError('network probability/arithmetic tolerance must be less than one')
        if type(self.verification_precision_bits) is not int or self.verification_precision_bits<64:
            raise ValueError('physical network requires an explicit Arb verification precision of at least 64 bits')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.network_id,self)


@dataclass(frozen=True, slots=True)
class PhysicalEncounterReduction(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-encounter-reduction'
    VERSION: ClassVar[str] = '1.0.0'
    reduction_id: str
    network_id: str
    association: PhysicalRateOperand
    dissolved_concentration_queries_uM: tuple[Decimal, ...]
    mean_time_multipliers: tuple[Decimal, ...]
    maximum_elimination_relative_error: Decimal
    bulk_to_encounter_correspondence: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.reduction_id)
        validate_stable_id(self.network_id)
        exact(self.association,PhysicalRateOperand)
        exact(self.bulk_to_encounter_correspondence,ObjectIdentity)
        values = self.dissolved_concentration_queries_uM
        if type(values) is not tuple or not values or values != tuple(sorted(set(values))):
            raise ValueError('encounter elimination requires its complete ordered dissolved concentration query set')
        for value in values:
            decimal_number(value,'dissolved concentration query',positive=True)
        if (type(self.mean_time_multipliers) is not tuple or len(self.mean_time_multipliers)<2
                or self.mean_time_multipliers != tuple(sorted(set(self.mean_time_multipliers)))):
            raise ValueError('encounter elimination requires a prospective time grid scaled by its proposed capture mean')
        for value in self.mean_time_multipliers:
            decimal_number(value,'capture mean multiplier',positive=True)
        decimal_number(self.maximum_elimination_relative_error,'encounter elimination error',positive=True)
        if self.maximum_elimination_relative_error>=1:
            raise ValueError('encounter elimination requires a relative error smaller than one')


@dataclass(frozen=True, slots=True)
class PhysicalSupplierSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-supplier-selection'
    VERSION: ClassVar[str] = '1.0.0'
    selection_id: str
    rates: PhysicalRateSelection
    networks: tuple[PhysicalRateNetwork, ...]
    encounter_reductions: tuple[PhysicalEncounterReduction, ...]
    maximum_network_analysis_bytes: int
    scope: str = 'CONDITIONAL_RETAINED_RATE_NETWORKS_WITHOUT_PHYSICAL_OR_BIOLOGICAL_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.rates,PhysicalRateSelection)
        roster(self.networks,PhysicalRateNetwork,'network_id')
        roster(self.encounter_reductions,PhysicalEncounterReduction,'reduction_id',allow_empty=True)
        indexed = {n.network_id:n for n in self.networks}
        for item in self.encounter_reductions:
            if item.network_id not in indexed or not indexed[item.network_id].role.endswith('ENCOUNTER'):
                raise ValueError('bulk association must refer to its complete selected encounter network')
            if item.association in {e.rate for e in indexed[item.network_id].edges}:
                raise ValueError('encounter elimination would count the same bulk access twice')
        if (type(self.maximum_network_analysis_bytes) is not int or self.maximum_network_analysis_bytes<=0
                or self.scope != 'CONDITIONAL_RETAINED_RATE_NETWORKS_WITHOUT_PHYSICAL_OR_BIOLOGICAL_ADMISSION'):
            raise ValueError('physical supplier needs an explicit finite analysis allocation and evidence limit')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id,self)


@dataclass(frozen=True, slots=True)
class PhysicalSupplierEvidence(FirstPassageEvidence):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-supplier-evidence'
    SELECTION_KIND: ClassVar[type] = PhysicalSupplierSelection
