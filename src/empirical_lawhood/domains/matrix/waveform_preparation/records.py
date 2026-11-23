# SPDX-License-Identifier: MPL-2.0
"""Scientific definition and exact operands of the waveform preparation inquiry."""

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import ClassVar

from empirical_lawhood.domains.matrix.classical_series.records import json_text
from empirical_lawhood.domains.matrix.finite_response_law.original_f import (
    OriginalFiniteResponseLaw,
)
from empirical_lawhood.domains.matrix.finite_response_law.authoring.rerun_input import (
    FiniteResponseLawCurrentExposure,
)
from empirical_lawhood.domains.matrix.matrix_array_chunks import (
    ChunkedMatrixArrays,
    FRAMED_ARRAY_SCHEMA,
    FRAMED_ARRAY_MEDIA,
    framed_size,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_population import (
    allocate_waveform,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import (
    CanonicalRecord,
    validate_sha256,
    validate_stable_id,
)

NAMESPACE = "matrix-waveform-preparation"
PROTOCOL_ID = NAMESPACE + ".population"
PHASES = ("prefix", "forecast", "parents", "lower", "assay", "measure", "cohort")
NATIVE = ("prefix", "parents", "assay")
PREDECESSORS = {
    "prefix": (),
    "forecast": ("prefix",),
    "parents": ("prefix", "forecast"),
    "lower": ("prefix", "forecast", "parents"),
    "assay": ("prefix", "parents", "lower"),
    "measure": ("prefix", "forecast", "lower", "assay"),
    "cohort": ("measure",),
}
LOWER_USERS = ("forecast", "lower", "measure")


@dataclass(frozen=True, slots=True)
class WaveformSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/specification"
    specification_id: str
    role: str
    master_seed: int
    bootstrap_seed: int
    lower: ObjectIdentity
    producing_code_sha256: str
    dependency_lock_sha256: str
    source_snapshot_sha256: str
    exposure: ObjectIdentity
    development: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (
            self.role not in ("development", "evaluation")
            or self.lower.object_schema != OriginalFiniteResponseLaw.SCHEMA
            or any(
                type(v) is not int or not 0 <= v < 2**128
                for v in (self.master_seed, self.bootstrap_seed)
            )
        ):
            raise ValueError(
                "Waveform population requires its original law, split and numerical streams"
            )
        if self.exposure.object_schema != FiniteResponseLawCurrentExposure.SCHEMA:
            raise ValueError(
                "Waveform source requires an explicit prior-exposure inventory"
            )
        for digest in (
            self.producing_code_sha256,
            self.dependency_lock_sha256,
            self.source_snapshot_sha256,
        ):
            validate_sha256(digest)
        if (self.development is not None) != (self.role == "evaluation"):
            raise ValueError(
                "Confirmation requires an authenticated development screen"
            )

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)

    @property
    def count(self):
        return 32 if self.role == "development" else 128

    def draw(self, index):
        return allocate_waveform(
            master_seed=self.master_seed, role=self.role, index=index
        )

    @property
    def unit_ids(self):
        return tuple(self.draw(i).unit_id for i in range(self.count))


@dataclass(frozen=True, slots=True)
class WaveformOperation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/operation"
    design: WaveformSpecification
    phase: str
    index: int | None

    def __post_init__(self):
        if self.phase not in PHASES or (self.phase == "cohort") != (self.index is None):
            raise ValueError("Waveform operation changes its independent-unit scope")
        if self.index is not None and (
            type(self.index) is not int or not 0 <= self.index < self.design.count
        ):
            raise ValueError("Operation names an unassigned waveform")

    @property
    def node_id(self):
        suffix = "all" if self.index is None else str(self.index).zfill(3)
        return (
            "waveform."
            + self.design.fingerprint()[:32]
            + "."
            + self.phase
            + "."
            + suffix
        )

    @property
    def config_id(self):
        return "config." + self.node_id

    @property
    def specification(self):
        return self.design.identity

    @property
    def assignments(self):
        indexes = range(self.design.count) if self.index is None else (self.index,)
        return tuple(self.design.draw(i) for i in indexes)

    @property
    def unit_ids(self):
        return (
            self.design.unit_ids
            if self.index is None
            else (self.design.draw(self.index).unit_id,)
        )

    def suppliers(self):
        indexes = range(self.design.count) if self.index is None else (self.index,)
        return tuple(
            WaveformOperation(self.design, phase, i)
            for phase in PREDECESSORS[self.phase]
            for i in indexes
        )


@dataclass(frozen=True, slots=True)
class WaveformProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/waveform-preparation/product"
    config: WaveformOperation
    dependencies: tuple[ObjectIdentity, ...]
    operand_sha256: str
    payload_json: str
    array_manifest: ChunkedMatrixArrays | None = None
    array_artifact: ArtifactIdentity | None = None

    def __post_init__(self):
        validate_sha256(self.operand_sha256)
        if tuple(p.object_id for p in self.dependencies) != tuple(
            sorted(x.node_id + ".product" for x in self.config.suppliers())
        ):
            raise ValueError(
                "Waveform product omits or substitutes a causal predecessor"
            )
        if any(p.object_schema != self.SCHEMA for p in self.dependencies):
            raise ValueError("Waveform predecessor has a different record type")
        if (self.array_manifest is None) != (self.array_artifact is None):
            raise ValueError("Native data require the complete binary custody pair")
        if self.array_manifest is not None:
            draft, artifact = self.array_manifest, self.array_artifact
            (draw,) = self.config.assignments
            output_id = self.config.node_id + ".arrays"
            # The unqualified ID identifies standalone preflight and the first
            # producer's retained containers. Issued outputs bind their run.
            qualified = re.fullmatch(
                r"artifact\.recursive\.[0-9a-f]{24}\." + re.escape(output_id),
                artifact.artifact_id,
            )
            if (
                self.config.phase not in NATIVE
                or (artifact.artifact_id != output_id and qualified is None)
                or (artifact.payload_schema, artifact.media_type, artifact.size_bytes)
                != (FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, framed_size(draft))
                or draft.operand_id
                != "arrays." + sha256(artifact.artifact_id.encode()).hexdigest()
                or draft.source != self.config.specification
                or draft.producers != (self.config.specification,)
                or draft.allocation
                != ObjectIdentity.from_record("assignment." + draw.unit_id, draw)
            ):
                raise ValueError(
                    "Native arrays changed their original allocation, source or container"
                )
        if not isinstance(self.metadata, dict):
            raise ValueError("A waveform product needs a canonical record document")

    @property
    def record_id(self):
        return self.config.node_id + ".product"

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def metadata(self):
        return json.loads(self.payload_json)

    @property
    def payload(self):
        if self.array_manifest is not None:
            raise ValueError(
                "Read native waveform data through their authenticated framed companion"
            )
        return self.metadata

    @classmethod
    def from_operand(cls, config, dependencies, operand):
        return cls(
            config,
            tuple(
                sorted((p.identity for p in dependencies), key=lambda x: x.object_id)
            ),
            operand.fingerprint(),
            json_text(operand.to_document()),
        )
