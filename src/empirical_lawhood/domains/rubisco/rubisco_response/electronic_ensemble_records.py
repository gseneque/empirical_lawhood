# SPDX-License-Identifier: MPL-2.0
"""Complete original electronic-pair ensembles and prospective rate controls."""

from dataclasses import dataclass
from decimal import Decimal
import math
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import ElectronicStateCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_records import EquilibriumReweightingSelection
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence, roster
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class ElectronicPairObservable(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/electronic-pair-observable'
    pair_id: str
    ensemble_id: str
    donor_state_id: str
    acceptor_state_id: str
    coupling: str
    gap_half_widths_hartree: tuple[Decimal, ...]
    primary_gap_half_width_hartree: Decimal
    minimum_crossing_configurations: int
    minimum_crossing_weight_ess: Decimal
    maximum_bandwidth_log_rate_range: Decimal
    maximum_landau_zener_probability: Decimal
    maximum_rate_memory_product: Decimal
    spin_population_model: str = 'NOT_APPLICABLE'
    maximum_relative_spin_completion_error: Decimal = Decimal('0.01')

    def __post_init__(self):
        for name in (self.pair_id, self.ensemble_id, self.donor_state_id, self.acceptor_state_id):
            validate_stable_id(name)
        if (self.donor_state_id == self.acceptor_state_id
                or self.coupling not in ('SPIN_FREE', 'SPIN_ORBIT_COLLINEAR_COMPONENT',
                    'SPIN_ORBIT_SINGLET_TRIPLET_MULTIPLET')):
            raise ValueError('electronic pair requires two distinct states and an explicit coupling interpretation')
        required_population = ('ISOTROPIC_UNPOLARIZED_ZERO_FIELD'
            if self.coupling == 'SPIN_ORBIT_SINGLET_TRIPLET_MULTIPLET' else 'NOT_APPLICABLE')
        if self.spin_population_model != required_population:
            raise ValueError('electronic spin transfer requires its explicit complete population model')
        if (type(self.gap_half_widths_hartree) is not tuple or len(self.gap_half_widths_hartree) < 2
                or self.gap_half_widths_hartree != tuple(sorted(set(self.gap_half_widths_hartree)))
                or self.primary_gap_half_width_hartree not in self.gap_half_widths_hartree):
            raise ValueError('electronic crossing requires its ordered bandwidth controls and selected primary width')
        for value in self.gap_half_widths_hartree:
            validate_decimal(value, field_name='gap_half_width_hartree', minimum=Decimal(0))
            if not 0 < float(value) < math.inf:
                raise ValueError('electronic crossing width must be finite and positive')
        for name in ('minimum_crossing_weight_ess', 'maximum_bandwidth_log_rate_range',
                'maximum_landau_zener_probability', 'maximum_rate_memory_product',
                'maximum_relative_spin_completion_error'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if not math.isfinite(float(value)):
                raise ValueError('electronic rate criteria require finite exact numerical limits')
        if (type(self.minimum_crossing_configurations) is not int or self.minimum_crossing_configurations < 2
                or self.minimum_crossing_weight_ess < 1
                or not 0 < self.maximum_landau_zener_probability < 1
                or not 0 < self.maximum_rate_memory_product < 1):
            raise ValueError('electronic rate controls require actual support and weak-coupling/time-separation limits')
        if not 0 < self.maximum_relative_spin_completion_error < 1:
            raise ValueError('electronic spin completion requires an explicit relative arithmetic error limit')


@dataclass(frozen=True, slots=True)
class ElectronicEnsembleRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/electronic-ensemble-rule'
    selection_id: str
    equilibrium: EquilibriumReweightingSelection
    electronic_criteria: ElectronicStateCriteria
    pairs: tuple[ElectronicPairObservable, ...]
    maximum_workspace_bytes: int
    assumptions: tuple[str, ...]
    scope: str = 'CONDITIONAL_ORIGINAL_ELECTRONIC_ENSEMBLES_WITHOUT_PHYSICAL_SPIN_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.equilibrium, EquilibriumReweightingSelection)
        exact(self.electronic_criteria, ElectronicStateCriteria)
        roster(self.pairs, ElectronicPairObservable, 'pair_id')
        if {p.ensemble_id for p in self.pairs} != {e.ensemble_id for e in self.equilibrium.ensembles}:
            raise ValueError('electronic ensemble rule omits or adds a selected equilibrium population')
        if len({(p.ensemble_id,p.donor_state_id,p.acceptor_state_id,p.coupling) for p in self.pairs}) != len(self.pairs):
            raise ValueError('electronic ensemble rule repeats the same original pair observable')
        if (type(self.maximum_workspace_bytes) is not int or self.maximum_workspace_bytes <= 0
                or type(self.assumptions) is not tuple or not self.assumptions
                or any(type(s) is not str or not s.strip() for s in self.assumptions)
                or self.scope != 'CONDITIONAL_ORIGINAL_ELECTRONIC_ENSEMBLES_WITHOUT_PHYSICAL_SPIN_OR_RATE_ADMISSION'):
            raise ValueError('electronic ensembles require their full workspace, assumptions and evidence ceiling')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class ElectronicEnsembleEvidence(FirstPassageEvidence):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/electronic-ensemble-evidence'
    SELECTION_KIND: ClassVar[type] = ElectronicEnsembleRule
