# SPDX-License-Identifier: MPL-2.0
"""One explicit source-metadata resource and machine-control selection."""
from dataclasses import dataclass, fields
from datetime import datetime
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.obligations import ComputabilityEvidence
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.dataset_authority import DatasetWorkEnvelope, _validate_reason_codes
from empirical_lawhood.planning.source_pipelines import _validate_static_locator


@dataclass(frozen=True, slots=True)
class MatrixProgrammeSourceOperations(CanonicalRecord):
    """Metadata controls confer no source qualification or scientific authority."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/source-operations"
    record_id: str
    physical_cutoff: InformationCutoff
    source_computability_evidence: ComputabilityEvidence
    source_budget: ResourceBudget
    dataset_work_envelope: DatasetWorkEnvelope
    operational_resources: SelectedE4OperationalResources
    metadata_issuer_id: str
    metadata_approver_id: str
    metadata_requester_id: str
    metadata_private_key_relative_path: str
    metadata_validity_seconds: int
    metadata_reason_codes: tuple[str, ...]
    licence_id: str
    scratch_namespace: str
    allow_metadata_key_creation: bool
    metadata_valid_from_utc: str | None

    def __post_init__(self):
        for value in (self.record_id, self.metadata_issuer_id, self.metadata_approver_id, self.metadata_requester_id):
            validate_stable_id(value)
        for value, kind in ((self.physical_cutoff, InformationCutoff),
                (self.source_computability_evidence, ComputabilityEvidence), (self.source_budget, ResourceBudget),
                (self.dataset_work_envelope, DatasetWorkEnvelope), (self.operational_resources, SelectedE4OperationalResources)):
            if type(value) is not kind:
                raise TypeError("source operations require their exact current operational owners")
            value.__post_init__()
        for name in ("memory_bytes", "source_scan_bytes", "output_bytes"):
            if type(getattr(self.source_budget, name)) is not int or getattr(self.source_budget, name) < 1:
                raise ValueError("source operations require explicit positive " + name)
        if self.metadata_requester_id == self.metadata_approver_id:
            raise PermissionError("source metadata request cannot self-approve")
        validate_relative_locator(self.metadata_private_key_relative_path)
        if (type(self.metadata_validity_seconds) is not int or self.metadata_validity_seconds < 1
                or type(self.allow_metadata_key_creation) is not bool
                or type(self.metadata_reason_codes) is not tuple or not self.metadata_reason_codes
                or self.metadata_reason_codes != tuple(sorted(set(self.metadata_reason_codes)))):
            raise ValueError("source operations require explicit validity, key policy and sorted metadata reasons")
        _validate_reason_codes(self.metadata_reason_codes, field_name="metadata_reason_codes",
            envelope_limit=self.dataset_work_envelope.control.max_reason_codes)
        if type(self.licence_id) is not str or not self.licence_id.strip():
            raise ValueError("source operations require the actual source licence")
        _validate_static_locator(self.scratch_namespace, field_name="scratch_namespace")
        if self.metadata_valid_from_utc is not None:
            if type(self.metadata_valid_from_utc) is not str or not self.metadata_valid_from_utc.endswith("Z"):
                raise ValueError("source metadata start must be an explicit UTC timestamp")
            datetime.fromisoformat(self.metadata_valid_from_utc.replace("Z", "+00:00"))

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def request_values(self):
        """Project the existing finite/prepared request fields without a new policy."""
        self.__post_init__()
        return {field.name: getattr(self, field.name) for field in fields(self) if field.name != "record_id"}
