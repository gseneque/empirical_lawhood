# SPDX-License-Identifier: MPL-2.0
"""Closed restrained-formation evidence; no implicit activation-rate claim."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_records import _number
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.restrained_formation import RestrainedFormationSelection


@dataclass(frozen=True, slots=True)
class RestrainedFormationEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/restrained-formation-evidence'
    evidence_id: str
    selection: ObjectIdentity
    provenance: NumericalProducingProvenance
    arrays: ArrayDatasetManifest
    array_artifact: ArtifactIdentity
    readout: FileEvidence
    original_results: tuple[ObjectIdentity, ...]
    analysis_cpu_seconds: Decimal
    analysis_wall_seconds: Decimal
    cost_scope: str = 'ORIGINAL_READ_AND_ANALYSIS_EXCLUDING_ENVIRONMENT_CAPTURE_AND_PUBLICATION'

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        for value,kind in ((self.selection,ObjectIdentity),(self.provenance,NumericalProducingProvenance),
                (self.arrays,ArrayDatasetManifest),(self.array_artifact,ArtifactIdentity),(self.readout,FileEvidence)):
            exact(value,kind)
        if (self.selection.object_schema!=RestrainedFormationSelection.SCHEMA
                or self.selection.object_version!=RestrainedFormationSelection.VERSION
                or self.array_artifact.payload_schema!='empirical-lawhood/source/checksummed-uninterpreted-public-bytes'
                or self.array_artifact.media_type!='application/zip' or self.readout.relative_path!='readout.json'
                or self.cost_scope!='ORIGINAL_READ_AND_ANALYSIS_EXCLUDING_ENVIRONMENT_CAPTURE_AND_PUBLICATION'):
            raise ValueError('formation evidence changes its selected estimator, carriers or cost scope')
        identities(self.original_results,allow_empty=True)
        references=tuple(sorted((self.selection,self.provenance.identity,*self.original_results),key=lambda p:p.object_id))
        if self.arrays.scientific_references!=references:
            raise ValueError('formation arrays lose original results, source or estimator selection')
        for value in (self.analysis_cpu_seconds,self.analysis_wall_seconds):
            _number(value,'original analysis cost')
            if value<0:
                raise ValueError('formation analysis cost cannot be negative')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id,self)
