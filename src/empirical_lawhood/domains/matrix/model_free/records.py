# SPDX-License-Identifier: MPL-2.0
"""Strict authored contracts; each operation carries only its actual root census."""
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from hashlib import sha256
import random
from typing import ClassVar

from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id, validate_sha256
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.matrix.matrix_array_chunks import ChunkedMatrixArrays, FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, framed_size
from empirical_lawhood.domains.matrix.classical_series.records import json_object, json_text, unit_id

NAMESPACE = "matrix-model-free"
PREFIX = "empirical-lawhood/" + NAMESPACE
PROTOCOL_ID = NAMESPACE + ".development"
MODULES = tuple("M" + str(i) for i in range(8))
PREREQUISITES = {"M3": ("M1",), "M4": ("M3",), "M5": ("M1",), "M7": ("M1",)}
PAYLOAD_SCHEMAS = {"acquire": "matrix-model-free-acquisition.v1", "analyse": "matrix-model-free-analysis.v1", "synthesise": "matrix-model-free-synthesis.v1"}


@dataclass(frozen=True, slots=True)
class RootAssignment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/root-assignment"
    seed: int
    modules: tuple[str, ...]
    role: str = "development"
    audit_selected: bool | None = None
    inclusion_probability: str | None = None
    frame_id: str | None = None
    frame_size: int | None = None
    audit_size: int | None = None

    def __post_init__(self):
        unit_id(self.seed)
        if self.role not in ("development", "confirmation"):
            raise ValueError("declare development or fresh confirmation explicitly")
        if not self.modules or self.modules != tuple(sorted(set(self.modules))) or set(self.modules) - set(MODULES):
            raise ValueError("select a sorted unique implemented module census")
        if "M2" in self.modules and set(self.modules) - {"M0", "M2"}:
            raise ValueError("stationary-memory roots must be separate from formation/response cohorts")
        fields = (self.audit_selected, self.inclusion_probability, self.frame_id, self.frame_size, self.audit_size)
        if any(v is not None for v in fields):
            if "M5" not in self.modules or any(v is None for v in fields) or type(self.audit_selected) is not bool:
                raise ValueError("finite-frame audit needs one complete declared sampling assignment")
            if type(self.frame_size) is not int or type(self.audit_size) is not int or not 0 < self.audit_size <= self.frame_size:
                raise ValueError("invalid finite-frame sample size")
            if (type(self.inclusion_probability) is not str or not Decimal(self.inclusion_probability).is_finite()
                    or not Decimal(0) < Decimal(self.inclusion_probability) <= Decimal(1)):
                raise ValueError("every finite-frame unit requires positive inclusion probability")
            validate_stable_id(self.frame_id)

    @property
    def unit_id(self):
        return unit_id(self.seed)


@dataclass(frozen=True, slots=True)
class RetainedInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/retained-input"
    key: str
    identity: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.key)
        if type(self.identity) is not ObjectIdentity or self.identity.object_schema != PREFIX + "/product":
            raise ValueError("retained input requires an exact model-free product identity")


@dataclass(frozen=True, slots=True)
class RetainedArray(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/retained-array"
    key: str
    identity: ArtifactIdentity

    def __post_init__(self):
        validate_stable_id(self.key)
        if type(self.identity) is not ArtifactIdentity or self.identity.payload_schema != FRAMED_ARRAY_SCHEMA or self.identity.media_type != FRAMED_ARRAY_MEDIA:
            raise ValueError("retained arrays require the existing exact framed codec")


@dataclass(frozen=True, slots=True)
class ParentLineage(CanonicalRecord):
    """Immutable pins populated by the authenticated public parent-read route.

The record binds provenance and the information cutoff into scientific identity.
It is not an authority token or a claim of globally unexposed random seeds.
"""
    SCHEMA: ClassVar[str] = PREFIX + "/parent-lineage"
    purpose: str
    parent_specification: ObjectIdentity
    parent_summaries: tuple[ObjectIdentity, ...]
    parent_assignments: tuple[RootAssignment, ...]
    parent_packet_sha256: str
    parent_execution_plan_sha256: str
    parent_producing_code_sha256: str
    parent_readout_sha256: str
    exposed_seeds: tuple[int, ...]
    exposed_seeds_sha256: str
    frozen_settings_sha256: str

    def __post_init__(self):
        if self.purpose not in ("development-freeze", "retained-reanalysis", "population-deployment"):
            raise ValueError("unknown parent information-cutoff purpose")
        if type(self.parent_specification) is not ObjectIdentity or self.parent_specification.object_schema != PREFIX + "/specification":
            raise ValueError("lineage requires the exact original specification identity")
        if (type(self.parent_summaries) is not tuple or not self.parent_summaries
                or any(type(p) is not ObjectIdentity or p.object_schema != PREFIX + "/product" for p in self.parent_summaries)
                or tuple(p.object_id for p in self.parent_summaries) != tuple(sorted({p.object_id for p in self.parent_summaries}))):
            raise ValueError("lineage requires a complete sorted parent-summary identity census")
        if (type(self.parent_assignments) is not tuple or not self.parent_assignments
                or any(type(r) is not RootAssignment for r in self.parent_assignments)
                or tuple(r.seed for r in self.parent_assignments) != tuple(sorted({r.seed for r in self.parent_assignments}))):
            raise ValueError("lineage requires the original complete assigned-root census")
        if self.purpose in ("development-freeze", "population-deployment") and any(r.role != "development" for r in self.parent_assignments):
            raise ValueError("confirmation freezes choices from an exposed development parent")
        if type(self.exposed_seeds) is not tuple or self.exposed_seeds != tuple(sorted(set(self.exposed_seeds))):
            raise ValueError("exposed seed census must be uniquely sorted")
        for seed in self.exposed_seeds:
            unit_id(seed)
        if not {r.seed for r in self.parent_assignments} <= set(self.exposed_seeds):
            raise ValueError("lineage loses an already exposed parent root")
        for value in (self.parent_packet_sha256, self.parent_execution_plan_sha256,
                      self.parent_producing_code_sha256, self.parent_readout_sha256,
                      self.exposed_seeds_sha256, self.frozen_settings_sha256):
            validate_sha256(value)
        if self.exposed_seeds_sha256 != sha256(json_text({"seeds": list(self.exposed_seeds)}).encode()).hexdigest():
            raise ValueError("exposed-root digest differs from its complete census")


def selection_key(module, assignment):
    return module.lower() + "." + assignment.unit_id


def restrict_assignment(assignment, modules):
    """Project an original root to selected modules without changing its role.

The complete parent assignment stays in ParentLineage. Sampling fields belong
to M5 and are preserved exactly whenever that module is selected.
"""
    options = {} if "M5" in modules else {name: None for name in
        ("audit_selected", "inclusion_probability", "frame_id", "frame_size", "audit_size")}
    return replace(assignment, modules=modules, **options)


def audit_assignments(assignments, settings):
    """Freeze simple random sampling before any target native outcomes exist."""
    frame = tuple(r for r in assignments if "M5" in r.modules)
    if not frame:
        return assignments
    p = settings["population"]
    if len(frame) != p["frame_size"]:
        raise ValueError("the finite-frame size must equal the declared independent-root roster")
    size = p["audit_size"]
    seed = p.get("sampling_seed", 20261117)
    selected = set(random.Random(seed).sample([r.seed for r in frame], size))
    identity = "frame." + sha256(json_text({"roots": [r.seed for r in frame], "sampling_seed": seed,
        "audit_size": size, "role": frame[0].role}).encode()).hexdigest()
    with localcontext() as context:
        context.prec = 50
        probability = str(Decimal(size) / Decimal(len(frame)))
    return tuple(replace(r, audit_selected=r.seed in selected, inclusion_probability=probability,
        frame_id=identity, frame_size=len(frame), audit_size=size) if "M5" in r.modules else r for r in assignments)


@dataclass(frozen=True, slots=True)
class Specification(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/specification"
    specification_id: str
    settings_json: str
    assignments: tuple[RootAssignment, ...]
    study_label: str
    mode: str = "new-development"
    evidence_scope: str = "PREDECLARED_DEVELOPMENT"
    retained_inputs: tuple[RetainedInput, ...] = ()
    retained_arrays: tuple[RetainedArray, ...] = ()
    parent_lineage: ParentLineage | None = None

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if not isinstance(self.study_label, str) or not self.study_label.strip():
            raise ValueError("a scientific study label is required")
        json_object(self.settings_json)
        if type(self.assignments) is not tuple or not self.assignments:
            raise ValueError("declare the complete independent-root census")
        for row in self.assignments:
            if type(row) is not RootAssignment:
                raise TypeError("root assignments require exact records")
            row.__post_init__()
            if self.mode == "new-development" and any(set(PREREQUISITES.get(m, ())) - set(row.modules) for m in row.modules):
                raise ValueError("native modules require their declared upstream checkpoint suppliers")
        if tuple(r.seed for r in self.assignments) != tuple(sorted({r.seed for r in self.assignments})):
            raise ValueError("root seeds must be sorted, unique and disjoint across cohorts")
        if len({r.role for r in self.assignments}) != 1:
            raise ValueError("development and confirmation require separately frozen inquiries")
        role = self.assignments[0].role
        if role == "confirmation" and self.mode == "new-development":
            from .confirmation import validate_confirmation
            validate_confirmation(self.settings, self.assignments)
        expected_scope = "FRESH_CONFIRMATION" if role == "confirmation" else "EXPOSED_DEVELOPMENT"
        if self.settings.get("evidence_scope") != expected_scope:
            raise ValueError("scientific settings cannot relabel the assigned root role")
        if self.assignments != audit_assignments(self.assignments, self.settings):
            raise ValueError("finite-frame audit differs from its frozen probability sample")
        expected = {"new-development": "PREDECLARED_DEVELOPMENT", "reanalysis": "EXPOSED_REANALYSIS"}
        if self.mode not in expected or self.evidence_scope != expected[self.mode]:
            raise ValueError("execution mode and exposure scope disagree")
        for rows, kind in ((self.retained_inputs, RetainedInput), (self.retained_arrays, RetainedArray)):
            if type(rows) is not tuple or any(type(r) is not kind for r in rows):
                raise TypeError("retained selections require exact immutable records")
            if tuple(r.key for r in rows) != tuple(sorted({r.key for r in rows})):
                raise ValueError("retained selections must be uniquely sorted")
        expected_keys = {selection_key(m, r) for r in self.assignments for m in r.modules}
        if self.mode == "new-development" and (self.retained_inputs or self.retained_arrays):
            raise ValueError("new acquisition cannot substitute previously exposed products")
        if self.mode == "reanalysis" and ({r.key for r in self.retained_inputs} != expected_keys or {r.key for r in self.retained_arrays} != {"arrays." + k for k in expected_keys}):
            raise ValueError("reanalysis needs each selected original acquisition and array companion")
        lineage = self.parent_lineage
        deployment = (self.mode == "new-development" and role == "development"
            and any('M5' in row.modules for row in self.assignments)
            and self.settings['population']['mode'] == 'sparse')
        if self.mode == "new-development" and role == "development" and not deployment:
            if lineage is not None:
                raise ValueError("a new development inquiry cannot impersonate an authenticated successor")
        else:
            if type(lineage) is not ParentLineage:
                raise ValueError("confirmation/reanalysis requires authenticated parent lineage")
            lineage.__post_init__()
            purpose = "retained-reanalysis" if self.mode == "reanalysis" else "population-deployment" if deployment else "development-freeze"
            if lineage.purpose != purpose or lineage.frozen_settings_sha256 != sha256(self.settings_json.encode()).hexdigest():
                raise ValueError("parent cutoff does not bind these frozen scientific settings")
            if self.mode == "new-development" and set(lineage.exposed_seeds) & {r.seed for r in self.assignments}:
                raise ValueError("exposed parent roots cannot become fresh confirmation")
            if self.mode == "reanalysis":
                original = {r.seed: r for r in lineage.parent_assignments}
                for current in self.assignments:
                    previous = original.get(current.seed)
                    if previous is None or restrict_assignment(previous, current.modules) != current or not set(current.modules) <= set(previous.modules):
                        raise ValueError("reanalysis changes original root role or sampling metadata")
                for module in {m for r in self.assignments for m in r.modules}:
                    if {r.seed for r in self.assignments if module in r.modules} != {r.seed for r in lineage.parent_assignments if module in r.modules}:
                        raise ValueError("module reanalysis cannot discard originally assigned roots")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)

    @property
    def settings(self):
        return json_object(self.settings_json)

    @property
    def independent_unit_ids(self):
        return tuple(r.unit_id for r in self.assignments)


@dataclass(frozen=True, slots=True)
class OperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/operation-config"
    config_id: str
    phase: str
    module: str
    specification: ObjectIdentity
    settings_json: str
    assignments: tuple[RootAssignment, ...]
    evidence_scope: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.phase not in ("acquire", "analyse", "synthesise") or not self.config_id.endswith("." + self.phase):
            raise ValueError("operation identity and scientific phase disagree")
        if self.module not in MODULES:
            raise ValueError("unknown scientific module")
        if type(self.specification) is not ObjectIdentity or self.specification.object_schema != Specification.SCHEMA:
            raise ValueError("operation needs its exact authored specification")
        json_object(self.settings_json)
        if type(self.assignments) is not tuple or not self.assignments or tuple(r.seed for r in self.assignments) != tuple(sorted({r.seed for r in self.assignments})):
            raise ValueError("operation requires its complete sorted assigned roots")
        if any(type(r) is not RootAssignment or self.module not in r.modules for r in self.assignments):
            raise ValueError("module changes its assigned root population")
        for assignment in self.assignments:
            assignment.__post_init__()
        if self.phase != "synthesise" and len(self.assignments) != 1:
            raise ValueError("native work and assessment are independently recoverable per root")
        if self.evidence_scope not in ("PREDECLARED_DEVELOPMENT", "EXPOSED_REANALYSIS"):
            raise ValueError("unsupported evidence scope")

    @property
    def node_id(self):
        return self.config_id.removeprefix("config.")

    @property
    def settings(self):
        return json_object(self.settings_json)


@dataclass(frozen=True, slots=True)
class Product(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/product"
    record_id: str
    config: OperationConfig
    payload_json: str
    dependencies: tuple[ObjectIdentity, ...] = ()
    array_manifest: ChunkedMatrixArrays | None = None
    array_artifact: ArtifactIdentity | None = None

    def __post_init__(self):
        if type(self.config) is not OperationConfig or self.record_id != self.config.node_id + ".product":
            raise ValueError("product changes its producing operation")
        body = json_object(self.payload_json)
        if body.get("schema") != PAYLOAD_SCHEMAS[self.config.phase] or body.get("module") != self.config.module:
            raise ValueError("product scientific schema/module differs from its operation")
        if self.config.phase != "synthesise" and body.get("seed") != self.config.assignments[0].seed:
            raise ValueError("product changes its independent root")
        if tuple(p.object_id for p in self.dependencies) != tuple(sorted({p.object_id for p in self.dependencies})):
            raise ValueError("product must retain uniquely sorted original dependencies")
        if any(type(p) is not ObjectIdentity or p.object_schema != self.SCHEMA for p in self.dependencies):
            raise ValueError("product dependency has the wrong original type")
        if (self.array_manifest is None) != (self.array_artifact is None):
            raise ValueError("binary operands need both manifest and exact artifact")
        if self.array_manifest is not None:
            if self.config.phase != "acquire" or type(self.array_manifest) is not ChunkedMatrixArrays or type(self.array_artifact) is not ArtifactIdentity:
                raise ValueError("only native acquisitions carry physical binary operands")
            if (self.array_artifact.payload_schema, self.array_artifact.media_type, self.array_artifact.size_bytes) != (FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, framed_size(self.array_manifest)):
                raise ValueError("binary acquisition differs from its complete framed transport")
            assignment = self.config.assignments[0]
            expected_allocation = ObjectIdentity.from_record("assignment." + assignment.unit_id, assignment)
            if (self.array_manifest.source != self.config.specification
                    or self.array_manifest.allocation != expected_allocation
                    or self.array_manifest.producers != (self.config.specification,)
                    or self.array_manifest.operand_id != "arrays." + sha256(self.array_artifact.artifact_id.encode()).hexdigest()):
                raise ValueError("native arrays change the original source, allocation or producing identity")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def payload(self):
        if self.array_manifest is not None:
            raise ValueError("native arrays require their authenticated companion")
        return json_object(self.payload_json)

    @property
    def metadata(self):
        return json_object(self.payload_json)
