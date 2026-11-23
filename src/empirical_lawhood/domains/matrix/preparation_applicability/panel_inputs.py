"""Exact ordinary panel publications for complete saved screen operands."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.matrix.preparation_applicability.phase_records import PreparationApplicabilityPrefix, PreparationApplicabilityPanel
from empirical_lawhood.domains.matrix.preparation_applicability.seals import PreparationApplicabilityLowerSeal
from empirical_lawhood.domains.matrix.preparation_applicability.records import PreparationApplicabilityMeasuredRoot
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest, CanonicalTaskReceipt
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.domains.matrix.preparation_applicability.result_access import PreparationApplicabilityResultAccess, PREPARATION_PROTECTED_OUTCOMES


@dataclass(frozen=True, slots=True)
class PreparationApplicabilityPanelPublication(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/preparation-applicability/panel-publication"
    prefix: PreparationApplicabilityPrefix
    panel: PreparationApplicabilityPanel
    seal: PreparationApplicabilityLowerSeal
    measurement: PreparationApplicabilityMeasuredRoot
    manifests: tuple[ArtifactManifest, ...]
    receipts: tuple[CanonicalTaskReceipt, ...]
    result_access: PreparationApplicabilityResultAccess

    def __post_init__(self):
        records = (self.prefix,self.panel,self.seal,self.measurement)
        if len(self.manifests)!=4 or len(self.receipts)!=4:
            raise ValueError("ordinary panel publication requires all four causal/readout receipts")
        root=self.prefix.root_id
        if (any(record.root_id!=root for record in records)
            or self.panel.prefix_sha256!=self.prefix.fingerprint()
            or self.panel.lower_seal_sha256!=self.seal.fingerprint()
            or self.measurement.prefix_sha256!=self.prefix.fingerprint()
            or self.measurement.panel_sha256!=self.panel.fingerprint()
            or self.measurement.lower_sha256!=self.seal.lower_sha256):
            raise ValueError("ordinary panel publication changes its causal native/seal join")
        for record,manifest,receipt,task in zip(records,self.manifests,self.receipts,("prefix","assay","lower","measure"),strict=True):
            if (manifest.publication is None or manifest.logical.payload_schema!=record.SCHEMA
                or manifest.logical.outcome_access not in PREPARATION_PROTECTED_OUTCOMES
                or manifest.materialization.physical_sha256!=record.fingerprint()
                or manifest.materialization.size_bytes!=len(record.canonical_bytes())
                or manifest.logical not in receipt.output_logical_artifacts
                or manifest.materialization not in receipt.output_materializations
                or receipt.task_id!=f"ap.{task}.{root}"
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or not receipt.checks):
                raise ValueError("ordinary panel is absent from its exact successful task publication")
        if len({receipt.run_id for receipt in self.receipts})!=1 or self.result_access.run_id != self.receipts[0].run_id:
            raise ValueError("ordinary panel mixes run custody")

    def authenticate(self,writer,receipt_store,*,result_access_authenticator,result_writer=None):
        output_writer = writer
        for receipt,manifest in zip(self.receipts,self.manifests,strict=True):
            plan = result_access_authenticator(context=self.result_access,receipt=receipt,logical=manifest.logical,writer=writer)
            if result_writer is not None and output_writer is writer:
                output_writer = result_writer(writer, plan, manifest.logical)
            if receipt_store.read_by_receipt_id(receipt.run_id,receipt.task_id,receipt.receipt_id)!=receipt:
                raise ValueError("ordinary panel task receipt differs from committed custody")
        output_writer.verify_manifests(self.manifests)
