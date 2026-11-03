# SPDX-License-Identifier: MPL-2.0
"""Bounded canonical dependency bytes carried by ordinary authenticated ports.

This transport establishes canonical object identity. The execution service owns
artifact authentication, receipts and outcome access. Entries admit a fixed set
of domain records, never a caller supplied class or import path.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord

MAXIMUM_CUSTODY_BYTES_V2 = 16 * 1024**2


@dataclass(frozen=True, slots=True)
class CanonicalEvidenceEntryV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/physical/virtual-cell/canonical-evidence-entry"
    VERSION: ClassVar[str] = "2.0.0"
    identity: ObjectIdentity
    canonical_utf8: str

    def __post_init__(self):
        if type(self.identity) is not ObjectIdentity or type(self.canonical_utf8) is not str:
            raise TypeError("custody entry requires its exact identity and canonical bytes")
        self.identity.__post_init__()
        payload = self.canonical_utf8.encode("utf-8")
        from hashlib import sha256

        if len(payload) > MAXIMUM_CUSTODY_BYTES_V2 or sha256(payload).hexdigest() != self.identity.object_fingerprint:
            raise ValueError("custody entry changes its actual canonical bytes")


@dataclass(frozen=True, slots=True)
class CanonicalEvidenceV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/physical/virtual-cell/canonical-evidence"
    VERSION: ClassVar[str] = "2.0.0"
    entries: tuple[CanonicalEvidenceEntryV2, ...]

    def __post_init__(self):
        if type(self.entries) is not tuple or len(self.entries) > 128:
            raise ValueError("custody transport exceeds its fixed record count")
        identities = []
        for value in self.entries:
            if type(value) is not CanonicalEvidenceEntryV2:
                raise TypeError("custody transport requires typed entries")
            value.__post_init__()
            identities.append((value.identity.object_schema, value.identity.object_id))
        if identities != sorted(set(identities)):
            raise ValueError("custody transport aliases or repeats record roles")
        if sum(len(value.canonical_utf8.encode("utf-8")) for value in self.entries) > MAXIMUM_CUSTODY_BYTES_V2:
            raise ValueError("custody transport exceeds its canonical byte bound")
        if len(self.canonical_bytes()) > MAXIMUM_CUSTODY_BYTES_V2:
            raise ValueError("custody transport exceeds its serialized byte bound")

    @classmethod
    def from_records(cls, records):
        return cls(tuple(CanonicalEvidenceEntryV2(identity, value.canonical_bytes().decode("utf-8"))
            for identity, value in sorted(records, key=lambda row: (row[0].object_schema, row[0].object_id))))

    def actual_records(self):
        from .analysis import ModelFitRecord, OfficialAggregateScore, TournamentRecord
        from .contracts import MetricContract, ProvenanceBoundVirtualCellPipelineConfig, VirtualCellSourceManifest, VirtualCellSourceObject
        from .config_v2 import VirtualCellPipelineSelectionV2
        from .correction_records_v2 import OfficialMetricSetV2, SharedTemplateShiftV2BuildReceipt
        from .prediction import PredictionRoster
        from .records import FalsifierPanel, ModelArtifactBinding, PreparedSourceRecord, ResponseSummaryRecord
        from .records_v2 import ModelDevelopmentRecordV2, ModelSelectionRecordV2, PredictionFreezeRecordV2, OfficialEvaluationRecordV2

        kinds = { (kind.SCHEMA, kind.VERSION): kind for kind in (
            ModelFitRecord, OfficialAggregateScore, TournamentRecord, MetricContract,
            ProvenanceBoundVirtualCellPipelineConfig, VirtualCellSourceManifest,
            VirtualCellSourceObject, VirtualCellPipelineSelectionV2,
            OfficialMetricSetV2, SharedTemplateShiftV2BuildReceipt, PredictionRoster,
            FalsifierPanel, ModelArtifactBinding, PreparedSourceRecord, ResponseSummaryRecord,
            ModelDevelopmentRecordV2, ModelSelectionRecordV2, PredictionFreezeRecordV2,
            OfficialEvaluationRecordV2,
        ) }
        self.__post_init__()
        values = []
        for entry in self.entries:
            identity = entry.identity
            kind = kinds.get((identity.object_schema, identity.object_version))
            if kind is None:
                raise ValueError("custody transport contains an unregistered domain record")
            value = decode_canonical_bytes(entry.canonical_utf8.encode("utf-8"), kind,
                maximum_bytes=MAXIMUM_CUSTODY_BYTES_V2)
            if ObjectIdentity.from_record(identity.object_id, value) != identity:
                raise ValueError("custody transport changes schema, revision or canonical identity")
            values.append((identity, value))
        return tuple(values)
