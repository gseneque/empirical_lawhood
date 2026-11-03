# SPDX-License-Identifier: MPL-2.0
"""Explicit operational selections for the original whole Matrix programme."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3ResourceSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import NativeTrainingAssemblyRequest
from empirical_lawhood.kernel.authority import AuthorityPolicy, ResourceBudget
from empirical_lawhood.kernel.obligations import ComputabilityEvidence
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import ComputabilityEnvelope

from .e1_assembly import MatrixProgrammeE1AssemblySelection
from .e2_assembly import MatrixProgrammeE2AssemblyRequest
from .e4_operations import MatrixProgrammeE4Operations
from .prepared_operations import MatrixProgrammePreparedOperations
from .source_operations import MatrixProgrammeSourceOperations


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE3Operations(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e3-operations'
    record_id: str
    resources: ProtectedE3ResourceSelection
    authority_policy: AuthorityPolicy
    computability_envelope: ComputabilityEnvelope
    computability_evidence: ComputabilityEvidence
    operator_id: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.operator_id)
        for value, kind in ((self.resources, ProtectedE3ResourceSelection),
                (self.authority_policy, AuthorityPolicy), (self.computability_envelope, ComputabilityEnvelope),
                (self.computability_evidence, ComputabilityEvidence)):
            if type(value) is not kind:
                raise TypeError('programme E3 requires its exact current resource and authority selections')
            value.__post_init__()
        if self.computability_evidence.envelope_id != self.computability_envelope.envelope_id:
            raise ValueError('programme E3 changes its actual computability envelope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeOperations(CanonicalRecord):
    """Budgets and actual operator contracts, separate from D and later results."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/operations'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    metadata_budget: ResourceBudget
    source_metadata: MatrixProgrammeSourceOperations
    e1: MatrixProgrammeE1AssemblySelection
    e2: MatrixProgrammeE2AssemblyRequest
    training: NativeTrainingAssemblyRequest
    e3: MatrixProgrammeE3Operations
    e4: MatrixProgrammeE4Operations
    prepared: MatrixProgrammePreparedOperations

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.metadata_budget, ResourceBudget), (self.source_metadata, MatrixProgrammeSourceOperations),
                (self.e1, MatrixProgrammeE1AssemblySelection), (self.e2, MatrixProgrammeE2AssemblyRequest),
                (self.training, NativeTrainingAssemblyRequest), (self.e3, MatrixProgrammeE3Operations),
                (self.e4, MatrixProgrammeE4Operations), (self.prepared, MatrixProgrammePreparedOperations)):
            if type(value) is not kind:
                raise TypeError('whole programme operations require every exact current typed selection')
            value.__post_init__()
        for field in ('memory_bytes', 'source_scan_bytes', 'output_bytes'):
            if type(getattr(self.metadata_budget, field)) is not int or getattr(self.metadata_budget, field) < 1:
                raise ValueError('whole programme requires finite positive metadata ' + field)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
