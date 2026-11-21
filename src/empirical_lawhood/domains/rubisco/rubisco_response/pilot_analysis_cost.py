# SPDX-License-Identifier: MPL-2.0
"""Original non-force analysis/export invocation costs and exact scope."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import roster
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation import _integer
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_programme import ANALYSES


@dataclass(frozen=True, slots=True)
class PilotAnalysisCostScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-analysis-cost-scope'
    analysis_kind: str
    scientific_selection: ObjectIdentity
    producing_provenance: ObjectIdentity

    def __post_init__(self):
        if self.analysis_kind not in ANALYSES:
            raise ValueError('non-force calibration needs a supported complete analysis/export operation')
        exact(self.scientific_selection, ObjectIdentity)
        exact(self.producing_provenance, ObjectIdentity)
        if self.producing_provenance.object_schema != NumericalProducingProvenance.SCHEMA:
            raise ValueError('non-force cost scope loses its actual producing implementation and environment')

    @property
    def identity(self):
        return ObjectIdentity.from_record('scope.pilot-analysis.'+self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class PilotAnalysisCostObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-analysis-cost-observation'
    observation_id: str
    scope: PilotAnalysisCostScope
    producing_provenance: NumericalProducingProvenance
    analysis_relative_path: str
    analysis_evidence: ObjectIdentity | None
    members: tuple[FileEvidence, ...]
    disposition: str
    cost: InquiryCost
    process_peak_rss_bytes: int
    failure: str | None
    memory_scope: str = 'PROCESS_LIFETIME_HIGH_WATER_CONSERVATIVE_FOR_SELECTED_INVOCATION'

    def __post_init__(self):
        validate_stable_id(self.observation_id)
        exact(self.scope, PilotAnalysisCostScope)
        exact(self.producing_provenance, NumericalProducingProvenance)
        if self.producing_provenance.identity != self.scope.producing_provenance:
            raise ValueError('non-force observation must retain its complete original producing provenance')
        validate_relative_locator(self.analysis_relative_path)
        if self.analysis_evidence is not None:
            exact(self.analysis_evidence, ObjectIdentity)
        roster(self.members, FileEvidence, 'relative_path', allow_empty=True)
        exact(self.cost, InquiryCost)
        _integer(self.process_peak_rss_bytes, 'observed process high-water RSS', positive=True)
        if self.disposition not in {'COMPLETE', 'FAILED'}:
            raise ValueError('analysis calibration must preserve its original complete or failed invocation')
        if (self.disposition == 'COMPLETE' and (self.analysis_evidence is None or self.failure is not None)
                or self.disposition == 'FAILED' and (self.analysis_evidence is not None or not self.failure)):
            raise ValueError('analysis calibration changes its original invocation outcome')
        if any(getattr(self.cost, k) is None for k in ('cpu_seconds', 'wall_seconds', 'retained_bytes')):
            raise ValueError('measured non-force invocation requires its complete observed cost')
        if self.memory_scope != 'PROCESS_LIFETIME_HIGH_WATER_CONSERVATIVE_FOR_SELECTED_INVOCATION':
            raise ValueError('process high-water memory cannot become an incremental per-task memory measurement')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.observation_id, self)
