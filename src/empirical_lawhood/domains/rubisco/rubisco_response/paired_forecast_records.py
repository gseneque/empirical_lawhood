# SPDX-License-Identifier: MPL-2.0
"""Prospective joins from original supplier analyses to conditional pairs.

The source indices address one complete, deduplicated native carrier census.
They do not select successful outcomes. Correspondence sources identify the
selected chemical interpretation and never grant physical rate admission.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext, validate_paired_chemical_selection
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_records import ElectronicEnsembleRule
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence, roster
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_network_records import PhysicalSupplierSelection
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_records import ReactiveFluxRule


@dataclass(frozen=True, slots=True)
class ForecastSupplier(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/forecast-supplier'
    supplier_id: str
    selection: ReactiveFluxRule | ElectronicEnsembleRule | PhysicalSupplierSelection
    source_indices: tuple[int, ...]
    dependence_set_id: str

    def __post_init__(self):
        validate_stable_id(self.supplier_id)
        validate_stable_id(self.dependence_set_id)
        if type(self.selection) not in (ReactiveFluxRule, ElectronicEnsembleRule, PhysicalSupplierSelection):
            raise TypeError('forecast requires an exact supported original supplier selection')
        self.selection.__post_init__()
        if (type(self.source_indices) is not tuple or not self.source_indices
                or any(type(i) is not int or i < 0 for i in self.source_indices)
                or len(set(self.source_indices)) != len(self.source_indices)):
            raise ValueError('forecast supplier needs its complete ordered original carrier indices')


@dataclass(frozen=True, slots=True)
class ForecastOperand(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/forecast-operand'
    supplier_id: str
    kind: str
    observable_id: str
    member_id: str | None
    chemical_correspondence: ObjectIdentity

    def __post_init__(self):
        for value in (self.supplier_id, self.observable_id):
            validate_stable_id(value)
        exact(self.chemical_correspondence, ObjectIdentity)
        if self.kind not in {'FLUX_RATE', 'ELECTRONIC_RATE', 'PASSAGE_RATE', 'PROCESSING_RATE', 'BULK_CAPTURE'}:
            raise ValueError('forecast operand has no supported original rate meaning')
        if self.kind == 'PASSAGE_RATE':
            validate_stable_id(self.member_id)
        elif self.kind != 'PROCESSING_RATE' and self.member_id is not None:
            raise ValueError('forecast operand adds an unselected member')
        if self.kind == 'PROCESSING_RATE' and self.member_id not in {'PRODUCTIVE_RETURN', 'REVERSE_RETURN'}:
            raise ValueError('processing operand must retain complete productive or reverse return')


@dataclass(frozen=True, slots=True)
class ForecastRatePair(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/forecast-rate-pair'
    parameter: str
    wild_type: ForecastOperand | None
    mutant: ForecastOperand | None

    def __post_init__(self):
        if self.parameter not in PARAMETER_ORDER:
            raise ValueError('forecast changes the complete reversible kinetic parameter census')
        for operand in (self.wild_type, self.mutant):
            if operand is not None:
                exact(operand, ForecastOperand)


@dataclass(frozen=True, slots=True)
class ForecastCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/forecast-case'
    case_id: str
    case: RubiscoPairedCase
    context: RubiscoAssayContext
    rates: tuple[ForecastRatePair, ...]
    closure_model: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.case_id)
        exact(self.case, RubiscoPairedCase)
        exact(self.context, RubiscoAssayContext)
        validate_paired_chemical_selection(self.case, self.context.chemistry)
        exact(self.closure_model, ObjectIdentity)
        roster(self.rates, ForecastRatePair, 'parameter')
        if tuple(r.parameter for r in self.rates) != PARAMETER_ORDER:
            raise ValueError('forecast must retain all eight rate roles, including missing reversals')


@dataclass(frozen=True, slots=True)
class PairedForecastSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/paired-forecast-selection'
    selection_id: str
    suppliers: tuple[ForecastSupplier, ...]
    cases: tuple[ForecastCase, ...]
    dependence_source: ObjectIdentity
    maximum_analysis_bytes: int
    assumptions: tuple[str, ...]
    interpretation: str = 'CONDITIONAL_JOINT_SUPPLIER_DRAWS_WITHOUT_PHYSICAL_OR_BIOLOGICAL_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        roster(self.suppliers, ForecastSupplier, 'supplier_id', allow_empty=True)
        roster(self.cases, ForecastCase, 'case_id')
        exact(self.dependence_source, ObjectIdentity)
        suppliers = {s.supplier_id for s in self.suppliers}
        used = {o.supplier_id for c in self.cases for r in c.rates for o in (r.wild_type, r.mutant) if o is not None}
        if used != suppliers:
            raise ValueError('forecast omits or adds a selected supplier in its complete operand census')
        if len({c.case.identity for c in self.cases}) != len(self.cases):
            raise ValueError('forecast duplicates a paired case as another independent view')
        if (type(self.maximum_analysis_bytes) is not int or self.maximum_analysis_bytes <= 0
                or type(self.assumptions) is not tuple or not self.assumptions
                or any(type(a) is not str or not a.strip() for a in self.assumptions)
                or self.interpretation != 'CONDITIONAL_JOINT_SUPPLIER_DRAWS_WITHOUT_PHYSICAL_OR_BIOLOGICAL_ADMISSION'):
            raise ValueError('forecast requires bounded analysis, explicit dependence assumptions and evidence limits')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class PairedForecastEvidence(FirstPassageEvidence):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/paired-forecast-evidence'
    SELECTION_KIND: ClassVar[type] = PairedForecastSelection
