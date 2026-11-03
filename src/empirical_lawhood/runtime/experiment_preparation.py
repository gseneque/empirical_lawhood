# SPDX-License-Identifier: MPL-2.0
"""Typed preparation reports; compilation and execution retain existing owners."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, ClassVar
from types import MappingProxyType

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_schema, validate_semantic_version, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOriginKind, RecursiveInputOrigins
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec, validate_storage_codecs
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult

if TYPE_CHECKING:
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveCandidatePreview
    from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig


class DependencyKind(StrEnum):
    SOFTWARE = "SOFTWARE"
    SCIENTIFIC_EVIDENCE = "SCIENTIFIC_EVIDENCE"
    AUTHORITY = "AUTHORITY"
    EXTERNAL_INPUT = "EXTERNAL_INPUT"
    ENVIRONMENT = "ENVIRONMENT"
    STORAGE = "STORAGE"


@dataclass(frozen=True, slots=True)
class ExperimentDependency:
    code: str
    kind: DependencyKind
    detail: str
    source_key: str | None = None

    def __post_init__(self):
        validate_stable_id(self.code)
        if type(self.kind) is not DependencyKind or not self.detail:
            raise ValueError("entry dependency needs a specific category and explanation")
        if self.source_key is not None:
            validate_stable_id(self.source_key)


def _counts(rows):
    if (type(rows) is not tuple or tuple(name for name, _ in rows)
            != tuple(sorted({name for name, _ in rows}))
            or any(type(count) is not int or count < 0 for _, count in rows)):
        raise ValueError("experiment census needs sorted unique nonnegative counts")
    for name, _ in rows:
        validate_stable_id(name)


@dataclass(frozen=True, slots=True)
class ExperimentCensus:
    role_counts: tuple[tuple[str, int], ...]
    resolved_role_counts: tuple[tuple[str, int], ...]
    operation_counts: tuple[tuple[str, int], ...]
    output_counts: tuple[tuple[str, int], ...]
    native_effect_count: int

    def __post_init__(self):
        for rows in (self.role_counts, self.resolved_role_counts,
                     self.operation_counts, self.output_counts):
            _counts(rows)
        if type(self.native_effect_count) is not int or self.native_effect_count < 0:
            raise ValueError("native-effect census must be nonnegative")
        # An invalid selection still reports its complete actual census. Domain
        # preparation records mismatches as dependencies rather than dropping units.


@dataclass(frozen=True, slots=True)
class ExecutionSelection:
    workers: int | None = None
    environment_id: str | None = None
    source_snapshot: ObjectIdentity | None = None
    output_root: str | None = None

    def __post_init__(self):
        if self.workers is not None and (type(self.workers) is not int or self.workers < 1):
            raise ValueError("execution selection needs a positive worker count")
        if self.environment_id is not None:
            validate_stable_id(self.environment_id)
        if self.source_snapshot is not None and type(self.source_snapshot) is not ObjectIdentity:
            raise ValueError("execution selection needs an exact frozen source identity")
        if self.output_root is not None and not self.output_root:
            raise ValueError("execution output root must be explicitly selected")


def select_experiment_workers(workers, *, profile_maximum=None):
    """Resolve explicit operational choices; absence never selects a worker count."""
    for name, value in (("workers", workers), ("profile maximum", profile_maximum)):
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(name + " requires a positive integer")
    if workers is None:
        return profile_maximum
    if profile_maximum is not None and workers != profile_maximum:
        raise ValueError("experiment workers differ from the selected operator profile")
    return workers


@dataclass(frozen=True, slots=True)
class PreparedExperimentFile:
    """Operational source handle, reauthenticated by the authoring owner.

    Construction does not read bytes or establish scientific admissibility.
    The selected physical codec and domain consumer retain those duties.
    """

    identity: ArtifactIdentity
    record_version: str
    path: Path
    maximum_bytes: int

    def __post_init__(self):
        if type(self.identity) is not ArtifactIdentity:
            raise TypeError("prepared experiment file requires its exact artifact identity")
        self.identity.__post_init__()
        validate_semantic_version(self.record_version)
        if (not isinstance(self.path, Path) or not self.path.is_absolute()
                or type(self.maximum_bytes) is not int or self.maximum_bytes < 1
                or type(self.identity.size_bytes) is not int
                or not 0 <= self.identity.size_bytes <= self.maximum_bytes):
            raise ValueError("prepared experiment file needs an absolute path and sufficient byte bound")


@dataclass(frozen=True, slots=True)
class ExperimentPreparation:
    """Operational metadata; outcome limitations grant no entry prerequisites."""

    specification: ObjectIdentity
    census: ExperimentCensus
    dependencies: tuple[ExperimentDependency, ...]
    allocation: UnitAllocation | None = None
    draft: RecursiveStudyDraft | None = None
    input_records: tuple[tuple[str, CanonicalRecord], ...] = ()
    execution: ExecutionSelection | None = None
    specification_record: CanonicalRecord | None = None
    design_records: tuple[tuple[str, CanonicalRecord], ...] = ()
    input_files: tuple[tuple[str, PreparedExperimentFile], ...] = ()
    contribution_dirs: tuple[Path, ...] = ()
    origins: RecursiveInputOrigins | None = None
    prospective_spec: RecursiveProspectiveAuthoringSpec | None = None
    source_configs: tuple[SourceMaterializationConfig, ...] = ()
    assessment_limitations: tuple[ExperimentDependency, ...] = ()
    prospective_candidate_preview: RecursiveProspectiveCandidatePreview | None = None
    programme: CanonicalRecord | None = None
    # Exact selected canonical source metadata, including operational records.
    # This noncanonical carrier grants no access and is not scientific design.
    authoring_source_records: tuple[tuple[str, CanonicalRecord], ...] = ()

    def __post_init__(self):
        if type(self.specification) is not ObjectIdentity or type(self.census) is not ExperimentCensus:
            raise ValueError("preparation needs its exact specification and complete census")
        if (type(self.dependencies) is not tuple
                or any(type(row) is not ExperimentDependency for row in self.dependencies)
                or tuple(row.code for row in self.dependencies)
                != tuple(sorted({row.code for row in self.dependencies}))):
            raise ValueError("preparation dependencies must be sorted and uniquely identified")
        if (type(self.assessment_limitations) is not tuple
                or any(type(row) is not ExperimentDependency for row in self.assessment_limitations)
                or tuple(row.code for row in self.assessment_limitations)
                != tuple(sorted({row.code for row in self.assessment_limitations}))):
            raise ValueError("assessment limitations must be exact typed, sorted and uniquely identified")
        for row in self.assessment_limitations:
            row.__post_init__()
            if row.kind is not DependencyKind.SCIENTIFIC_EVIDENCE:
                raise ValueError("assessment limitations may describe only scientific-evidence outcome limits")
        if self.programme is not None:
            if (not isinstance(self.programme, CanonicalRecord)
                    or self.draft is not None or self.input_records or self.input_files or self.origins is not None
                    or self.contribution_dirs or self.prospective_spec is not None or self.source_configs
                    or self.prospective_candidate_preview is not None or self.authoring_source_records):
                raise ValueError("Composite preparation requires its typed full plan and separate component projections")
            self.programme.__post_init__()
        if self.allocation is not None:
            self.allocation.__post_init__()
        if self.draft is not None:
            if self.allocation is None:
                raise ValueError("a compiled preparation cannot omit its immutable allocation")
            self.draft.__post_init__()
        if (type(self.input_records) is not tuple
                or tuple(key for key, _ in self.input_records)
                != tuple(sorted({key for key, _ in self.input_records}))
                or any(not isinstance(record, CanonicalRecord) for _, record in self.input_records)):
            raise ValueError("prepared experiment inputs must be uniquely bound canonical records")
        if (type(self.input_files) is not tuple
                or tuple(key for key, _ in self.input_files) != tuple(sorted({key for key, _ in self.input_files}))
                or any(type(value) is not PreparedExperimentFile for _, value in self.input_files)
                or {key for key, _ in self.input_files} & {key for key, _ in self.input_records}):
            raise ValueError("prepared experiment files must have unique disjoint input bindings")
        if (type(self.contribution_dirs) is not tuple
                or any(not isinstance(path, Path) or not path.is_absolute() or ".." in path.parts
                       for path in self.contribution_dirs)
                or len(set(self.contribution_dirs)) != len(self.contribution_dirs)):
            raise ValueError("prepared experiment contribution directories need distinct absolute paths")
        parent_inputs = set()
        if self.origins is not None:
            if type(self.origins) is not RecursiveInputOrigins or self.draft is None:
                raise ValueError("prepared experiment origins require their exact compiled draft")
            self.origins.validate_draft(self.draft)
            parent_inputs = {row.input_id for row in self.origins.inputs
                             if row.kind is RecursiveInputOriginKind.CONTRIBUTION}
        if self.contribution_dirs or self.draft is not None and self.draft.contribution_parents:
            if (self.draft is None or self.origins is None
                    or len(self.contribution_dirs) != len(self.draft.contribution_parents)):
                raise ValueError("prepared experiment parents need complete directories and explicit input origins")
        if self.input_records or self.input_files or parent_inputs:
            if self.draft is None:
                raise ValueError("prepared input projections need their compiled draft")
            selected = {link.external_input_id for link in self.draft.links
                        if link.consumer_node_id in self.draft.selected_operation_ids and link.external_input_id is not None}
            expected = {row.input_id: row for row in self.draft.external_inputs if row.input_id in selected
                        and not (self.prospective_spec is not None and row.parent_substitution)}
            bound = {key for key, _ in self.input_records} | {key for key, _ in self.input_files}
            if parent_inputs & bound:
                raise ValueError("prepared experiment cannot bind a parent-owned input as a source")
            if set(expected) != bound | parent_inputs:
                raise ValueError("prepared input projections omit or add external operands")
            for key, record in self.input_records:
                if (record.SCHEMA != expected[key].payload_schema
                        or record.fingerprint() != expected[key].expected_content_sha256):
                    raise ValueError("prepared input projection changes its exact scientific operand")
            for key, value in self.input_files:
                validate_stable_id(key)
                value.__post_init__()
                external = expected[key]
                if ((value.identity.artifact_id, value.identity.payload_schema, value.identity.media_type,
                        value.identity.sha256) != (external.logical_artifact_id, external.payload_schema,
                        external.media_type, external.expected_content_sha256)
                        or external.maximum_size_bytes is None
                        or value.identity.size_bytes > external.maximum_size_bytes
                        or value.maximum_bytes > external.maximum_size_bytes):
                    raise ValueError("prepared file projection changes its exact external operand or byte bound")
        if self.execution is not None:
            if type(self.execution) is not ExecutionSelection:
                raise TypeError("prepared experiment needs its separate typed execution selection")
            self.execution.__post_init__()
        if self.specification_record is not None:
            if (not isinstance(self.specification_record, CanonicalRecord)
                    or self.specification_record.fingerprint() != self.specification.object_fingerprint
                    or self.specification_record.SCHEMA != self.specification.object_schema
                    or self.specification_record.VERSION != self.specification.object_version):
                raise ValueError("prepared experiment changes its selected specification bytes")
        if (type(self.design_records) is not tuple
                or tuple(key for key, _ in self.design_records) != tuple(sorted({key for key, _ in self.design_records}))
                or any(not isinstance(record, CanonicalRecord) for _, record in self.design_records)):
            raise ValueError("prepared original design records require unique canonical bindings")
        for key, _ in self.design_records:
            validate_stable_id(key)
        if (type(self.authoring_source_records) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in self.authoring_source_records)
                or tuple(key for key, _ in self.authoring_source_records)
                    != tuple(sorted({key for key, _ in self.authoring_source_records}))
                or any(not isinstance(record, CanonicalRecord) for _, record in self.authoring_source_records)):
            raise ValueError("authoring source custody needs uniquely keyed actual canonical records")
        for key, record in self.authoring_source_records:
            validate_stable_id(key)
            record.canonical_bytes()
        if self.prospective_spec is not None:
            from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
            from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

            if type(self.prospective_spec) is not RecursiveProspectiveAuthoringSpec:
                raise TypeError("prospective preparation requires its exact existing authoring specification")
            self.prospective_spec.__post_init__()
            if self.draft is None or self.prospective_spec.draft != self.draft:
                raise ValueError("prospective preparation changes its exact selected scientific draft")
            if self.contribution_dirs or self.origins is not None:
                raise ValueError("prospective preparation uses its existing qualified-parent bindings, not development parent origins")
            if (type(self.source_configs) is not tuple
                    or any(type(record) is not SourceMaterializationConfig for record in self.source_configs)):
                raise TypeError("prospective source configurations require their exact canonical record roster")
            for record in self.source_configs:
                record.__post_init__()
            hashes = tuple(record.fingerprint() for record in self.source_configs)
            required = {source.source_config_sha256
                        for source in self.draft.prospective_draft.source_materializations}
            if hashes != tuple(sorted(required)):
                raise ValueError("prospective source configurations change the exact selected digest roster")
        elif type(self.source_configs) is not tuple or self.source_configs:
            raise ValueError("source configurations require their prospective authoring specification")
        if self.prospective_candidate_preview is not None:
            from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveCandidatePreview, RecursiveProspectiveDesignInputs

            preview = self.prospective_candidate_preview
            if type(preview) is not RecursiveProspectiveCandidatePreview:
                raise TypeError("prepared prospective comparison requires its exact candidate preview")
            preview.__post_init__()
            if (self.prospective_spec is None or self.execution is None
                    or preview.design_inputs != RecursiveProspectiveDesignInputs.from_spec(self.prospective_spec)
                    or self.execution.source_snapshot != ObjectIdentity.from_record("recursive-member.implementation", preview.implementation)):
                raise ValueError("prepared prospective preview changes its exact design or selected source closure")

    @property
    def executable(self) -> bool:
        return ((self.draft is not None or self.programme is not None) and not self.dependencies
            and self.execution is not None and self.execution.workers is not None)


@dataclass(frozen=True, slots=True)
class PreparedExperimentInputs:
    """Domain-resolved byte bindings; admissibility remains in preparation."""

    scientific_inputs: Mapping[str, UnitAllocation]
    method_inputs: object | None = None

    def __post_init__(self):
        if (not isinstance(self.scientific_inputs, Mapping)
                or any(type(value) is not UnitAllocation for value in self.scientific_inputs.values())):
            raise TypeError("resolved scientific inputs require typed immutable allocations")
        for key in self.scientific_inputs:
            validate_stable_id(key)
        object.__setattr__(self, "scientific_inputs", MappingProxyType(dict(self.scientific_inputs)))


@dataclass(frozen=True, slots=True)
class ExperimentInstanceBinding(CanonicalRecord):
    """Exact selected design associated with existing scientific/executable plans."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/experiment-preparation/instance-binding"
    specification: ObjectIdentity
    allocation: ObjectIdentity
    draft: ObjectIdentity
    scientific_projection: ObjectIdentity
    campaign: ObjectIdentity
    sources: tuple[ObjectIdentity, ...] = ()

    def __post_init__(self):
        for value in (self.specification, self.allocation, self.draft,
                      self.scientific_projection, self.campaign):
            if type(value) is not ObjectIdentity:
                raise TypeError("experiment instance binding requires exact immutable record identities")
        if self.allocation.object_schema != UnitAllocation.SCHEMA or self.draft.object_schema != RecursiveStudyDraft.SCHEMA:
            raise ValueError("experiment instance binding substitutes its allocation/draft schema")
        if (type(self.sources) is not tuple or any(type(value) is not ObjectIdentity for value in self.sources)
                or tuple(value.object_id for value in self.sources) != tuple(sorted({value.object_id for value in self.sources}))):
            raise ValueError("experiment instance binding requires sorted unique original source identities")


@dataclass(frozen=True, slots=True)
class ExperimentConfigurationCapability:
    """Immutable code-owned fixed facts and supported selections for one record.

    This is cold capability metadata, never scientific evidence or authority.
    Historical records keep their complete canonical field census.
    """

    contract_id: str
    record_type: type[CanonicalRecord]
    fixed_fields: tuple[tuple[str, object], ...]
    selectable_fields: tuple[str, ...]

    def __post_init__(self):
        from dataclasses import fields
        from decimal import Decimal

        validate_stable_id(self.contract_id)
        if not isinstance(self.record_type, type) or not issubclass(self.record_type, CanonicalRecord):
            raise TypeError("configuration capability requires its exact canonical record owner")
        def immutable(value):
            return type(value) in (str, int, bool, Decimal, type(None)) or (
                type(value) is tuple and all(immutable(item) for item in value))
        if (type(self.fixed_fields) is not tuple or any(type(row) is not tuple or len(row) != 2
                or type(row[0]) is not str or not immutable(row[1]) for row in self.fixed_fields)):
            raise TypeError("configuration capability facts require immutable canonical values")
        names = tuple(name for name, _ in self.fixed_fields)
        selected = self.selectable_fields
        if (names != tuple(sorted(set(names))) or type(selected) is not tuple
                or any(type(name) is not str for name in selected) or selected != tuple(sorted(set(selected)))
                or set(names) & set(selected)
                or set(names) | set(selected) != {field.name for field in fields(self.record_type)}):
            raise ValueError("configuration capability must partition every fixed and selectable field exactly")
        self.metadata()  # Validate canonical values; no provider or prerequisite contact.

    def validate(self, record):
        if type(record) is not self.record_type:
            raise TypeError("configuration capability received another record owner/revision")
        for name, expected in self.fixed_fields:
            actual = getattr(record, name)
            if type(actual) is not type(expected) or actual != expected:
                raise ValueError("unsupported acquisition geometry: capability " + self.contract_id
                                 + " fixes " + name + "=" + repr(expected))

    def metadata(self):
        from hashlib import sha256
        import json
        from empirical_lawhood.kernel.serialization import canonical_json_bytes

        value = dict(contract_id=self.contract_id, schema=self.record_type.SCHEMA,
            version=self.record_type.VERSION, fixed_fields=dict(self.fixed_fields),
            selectable_fields=self.selectable_fields)
        encoded = canonical_json_bytes(value)
        return {**json.loads(encoded), "sha256": sha256(encoded).hexdigest()}


@dataclass(frozen=True, slots=True)
class ExperimentInputConfigurationDeclaration:
    """Explicit editable input role; other source records remain unregistered."""

    consumer_id: str
    record_type: type[CanonicalRecord]
    maximum_config_bytes: int
    example_paths: tuple[str, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.consumer_id)
        if not isinstance(self.record_type, type) or not issubclass(self.record_type, CanonicalRecord):
            raise TypeError("input configuration needs its exact code-owned record type")
        if type(self.maximum_config_bytes) is not int or self.maximum_config_bytes < 1:
            raise ValueError("input configuration needs a positive parser byte bound")
        if (type(self.example_paths) is not tuple or self.example_paths != tuple(sorted(set(self.example_paths)))
                or any(not path or path.startswith("/") or ".." in path.split("/") for path in self.example_paths)):
            raise ValueError("input configuration examples need safe selected-source paths")


@dataclass(frozen=True, slots=True)
class ExperimentProtocolDeclaration:
    """Static domain authoring contract, projected by the extension generator."""

    protocol_id: str
    specification_type: type[CanonicalRecord]
    prepare: Callable
    consumer_id: str
    example_paths: tuple[str, ...] = ()
    maximum_config_bytes: int | None = None
    input_record_types: tuple[type[CanonicalRecord], ...] = ()
    bind_inputs: Callable | None = None
    validate_instance: Callable | None = None
    input_storage_codecs: tuple[RecursiveStorageCodec, ...] = ()
    bind_input_locations: bool = False
    requires_prospective_runtime_binding: bool = False
    input_file_record_types: tuple[type[CanonicalRecord], ...] = ()
    requires_development_runtime_binding: bool = False
    configuration_inputs: tuple[ExperimentInputConfigurationDeclaration, ...] = ()
    programme_record_type: type[CanonicalRecord] | None = None
    configuration_capabilities: tuple[ExperimentConfigurationCapability, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        validate_stable_id(self.consumer_id)
        if (type(self.configuration_capabilities) is not tuple
                or any(type(value) is not ExperimentConfigurationCapability for value in self.configuration_capabilities)
                or tuple(value.contract_id for value in self.configuration_capabilities)
                != tuple(sorted({value.contract_id for value in self.configuration_capabilities}))
                or len({(value.record_type.SCHEMA, value.record_type.VERSION)
                        for value in self.configuration_capabilities}) != len(self.configuration_capabilities)):
            raise TypeError("experiment configuration capabilities require unique immutable code-owned contracts")
        for value in self.configuration_capabilities:
            value.__post_init__()
        if self.programme_record_type is not None and (
                not isinstance(self.programme_record_type, type)
                or not issubclass(self.programme_record_type, CanonicalRecord)
                or self.requires_prospective_runtime_binding or self.requires_development_runtime_binding):
            raise TypeError("Composite protocol requires its exact typed plan and separate component lifecycles")
        if (not isinstance(self.specification_type, type)
                or not issubclass(self.specification_type, CanonicalRecord)
                or not callable(self.prepare)):
            raise TypeError("experiment protocol needs a strict specification and code-owned preparation")
        if (self.maximum_config_bytes is not None
                and (type(self.maximum_config_bytes) is not int or self.maximum_config_bytes < 1)):
            raise ValueError("experiment protocol has an invalid selected configuration byte limit")
        if (type(self.example_paths) is not tuple
                or self.example_paths != tuple(sorted(set(self.example_paths)))
                or any(not path or path.startswith("/") or ".." in path.split("/")
                       for path in self.example_paths)):
            raise ValueError("experiment examples need safe selected-source paths")
        if (type(self.input_record_types) is not tuple
                or any(not isinstance(record, type) or not issubclass(record, CanonicalRecord)
                       for record in self.input_record_types)
                or len({(record.SCHEMA, record.VERSION) for record in self.input_record_types}) != len(self.input_record_types)
                or bool(self.input_record_types or self.input_storage_codecs or self.input_file_record_types) != (self.bind_inputs is not None)
                or self.bind_inputs is not None and not callable(self.bind_inputs)):
            raise TypeError("experiment input decoding needs one closed code-owned domain binding")
        if (type(self.configuration_inputs) is not tuple
                or any(type(value) is not ExperimentInputConfigurationDeclaration for value in self.configuration_inputs)):
            raise TypeError("experiment configuration inputs need explicit typed declarations")
        consumers = [self.consumer_id]
        for value in self.configuration_inputs:
            value.__post_init__()
            if value.record_type not in self.input_record_types:
                raise ValueError("editable input configuration lacks its exact owning protocol input codec")
            consumers.append(value.consumer_id)
        if len(set(consumers)) != len(consumers):
            raise ValueError("experiment configuration consumers must be unique")
        validate_storage_codecs(self.input_storage_codecs)
        from empirical_lawhood.runtime.recursive_record_codecs import validate_input_record_types

        validate_input_record_types(self.input_file_record_types)
        if (type(self.bind_input_locations) is not bool
                or self.bind_input_locations and self.bind_inputs is None):
            raise TypeError("experiment input locations require an explicit registered input binder")
        if self.validate_instance is not None and not callable(self.validate_instance):
            raise TypeError("experiment instance validation must be a code-owned scientific callback")
        if type(self.requires_prospective_runtime_binding) is not bool:
            raise TypeError("prospective runtime binding requirement must be explicit")
        if (type(self.requires_development_runtime_binding) is not bool
                or self.requires_development_runtime_binding and self.requires_prospective_runtime_binding):
            raise TypeError("development runtime binding must select one explicit lifecycle")


@dataclass(frozen=True, slots=True)
class ExperimentRuntimeBinding:
    """Code-owned API composition, kept outside inward domain descriptors."""

    protocol_id: str
    bind_handoff: Callable | None
    prepare_authoring: Callable | None = None
    read_result: Callable | None = None
    specification_schema: str | None = None
    bind_development_runtime: Callable | None = None
    programme_service_factory: Callable | None = None
    derive_inputs: Callable | None = None
    export_products: Callable | None = None
    derivation_target_protocol_ids: tuple[str, ...] = ()
    read_development_result: Callable | None = None
    supports_incomplete_assessment: bool = False
    authenticate_instance: Callable | None = None
    complete_development_result: Callable | None = None
    validate_development_read_access: Callable | None = None
    validate_authoring_read_access: Callable | None = None
    development_bootstrap_record_types: tuple[type[CanonicalRecord], ...] = ()
    bootstrap_development_input_access: Callable | None = None
    bootstrap_authoring_input_access: Callable | None = None
    bootstrap_selected_input_access: Callable | None = None
    read_access_record_types: tuple[type[CanonicalRecord], ...] = ()
    select_read_access: Callable | None = None
    prospective_bootstrap_record_types: tuple[type[CanonicalRecord], ...] = ()
    bootstrap_prospective_input_access: Callable | None = None
    derive_prospective_design_inputs: Callable | None = None
    derive_inputs_with_service: Callable | None = None

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        if type(self.supports_incomplete_assessment) is not bool:
            raise TypeError('incomplete scientific assessment support requires an explicit boolean')
        if self.supports_incomplete_assessment and not callable(self.read_result):
            raise ValueError('incomplete scientific assessment requires its code-owned scientific reader')
        if (self.bind_handoff is None and not callable(self.bind_development_runtime)
                and not callable(self.programme_service_factory)
                and not callable(self.derive_inputs) and not callable(self.export_products)
                and not callable(self.read_development_result)
                or self.bind_handoff is not None and not callable(self.bind_handoff)):
            raise TypeError("experiment runtime binding requires its code-owned API callback")
        if self.programme_service_factory is not None and (
                not callable(self.programme_service_factory)
                or any(value is not None for value in (self.bind_handoff, self.bind_development_runtime,
                    self.prepare_authoring, self.read_result, self.specification_schema,
                    self.read_development_result))):
            raise TypeError("Composite runtime composition requires its separate code-owned component service")
        if self.bind_development_runtime is not None and not callable(self.bind_development_runtime):
            raise TypeError("development runtime binding requires its code-owned API callback")
        if self.prepare_authoring is not None and not callable(self.prepare_authoring):
            raise TypeError("experiment authoring preparation requires its code-owned API callback")
        if self.derive_prospective_design_inputs is not None and (
                not callable(self.derive_prospective_design_inputs)
                or not callable(self.prepare_authoring) or not callable(self.bind_handoff)):
            raise TypeError("prospective design derivation requires its ordinary authoring and handoff owners")
        if self.authenticate_instance is not None and not callable(self.authenticate_instance):
            raise TypeError("experiment instance custody requires its code-owned API callback")
        if self.authenticate_instance is not None and self.programme_service_factory is not None:
            raise ValueError("Composite programmes authenticate their separate component instances")
        if self.derive_inputs_with_service is not None and (
                not callable(self.derive_inputs_with_service) or not callable(self.derive_inputs)):
            raise TypeError("operator-aware derivation requires its ordinary code-owned input deriver")
        if self.derive_inputs is not None and not callable(self.derive_inputs):
            raise TypeError("experiment input derivation requires its code-owned API callback")
        if self.export_products is not None and not callable(self.export_products):
            raise TypeError("experiment product export requires its code-owned API callback")
        if (type(self.derivation_target_protocol_ids) is not tuple
                or self.derivation_target_protocol_ids != tuple(sorted(set(self.derivation_target_protocol_ids)))
                or self.derivation_target_protocol_ids and not callable(self.derive_inputs)):
            raise ValueError('preprocessing targets require one installed input deriver and sorted exact protocol IDs')
        for target in self.derivation_target_protocol_ids:
            validate_stable_id(target)
        readers = (self.read_result, self.read_development_result)
        if any(value is not None for value in readers) != (self.specification_schema is not None):
            raise ValueError("experiment scientific read requires one explicit specification schema")
        for reader in readers:
            if reader is not None and not callable(reader):
                raise TypeError("experiment scientific read requires its code-owned API callback")
        if self.read_development_result is not None and any(value is not None for value in
                (self.bind_handoff, self.read_result, self.programme_service_factory)):
            raise TypeError("development scientific read cannot select a prospective or composite lifecycle")
        if self.complete_development_result is not None and (
                not callable(self.complete_development_result) or not callable(self.read_development_result)):
            raise TypeError("development result production requires its ordinary scientific read owner")
        if self.validate_development_read_access is not None and (
                not callable(self.validate_development_read_access)
                or not callable(self.read_development_result) or not callable(self.bind_development_runtime)):
            raise TypeError("development access selection requires its ordinary runtime and scientific read owners")
        if self.validate_authoring_read_access is not None and (
                not callable(self.validate_authoring_read_access)
                or not callable(self.prepare_authoring)
                or not callable(self.bind_development_runtime)
                or not callable(self.read_development_result)):
            raise TypeError("authoring access requires its ordinary development preparation and read owners")
        if (type(self.development_bootstrap_record_types) is not tuple
                or any(not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
                    for kind in self.development_bootstrap_record_types)
                or len(set(self.development_bootstrap_record_types)) != len(self.development_bootstrap_record_types)
                or bool(self.development_bootstrap_record_types) != any(value is not None for value in
                    (self.bootstrap_development_input_access,
                        self.bootstrap_selected_input_access if self.bootstrap_prospective_input_access is None else None))
                or self.bootstrap_development_input_access is not None
                    and not callable(self.bootstrap_development_input_access)):
            raise TypeError('development bootstrap requires its exact closed locator codecs and callback')
        if self.bootstrap_selected_input_access is not None and not callable(self.bootstrap_selected_input_access):
            raise TypeError('selected input bootstrap requires its code-owned current-access callback')
        if self.bootstrap_development_input_access is not None and (
                not callable(self.bind_development_runtime) or not callable(self.read_development_result)):
            raise TypeError('development bootstrap requires its ordinary runtime and scientific reader')
        if self.bootstrap_authoring_input_access is not None and (
                not callable(self.bootstrap_authoring_input_access)
                or not callable(self.bootstrap_development_input_access)
                    and not callable(self.bootstrap_prospective_input_access)):
            raise TypeError('authoring bootstrap requires its exact original access owner')
        if (type(self.prospective_bootstrap_record_types) is not tuple
                or any(not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
                    for kind in self.prospective_bootstrap_record_types)
                or len(set(self.prospective_bootstrap_record_types)) != len(self.prospective_bootstrap_record_types)
                or bool(self.prospective_bootstrap_record_types) != (self.bootstrap_prospective_input_access is not None)
                or self.bootstrap_prospective_input_access is not None
                    and (not callable(self.bootstrap_prospective_input_access)
                        or not callable(self.bind_handoff) or not callable(self.read_result))):
            raise TypeError('prospective bootstrap requires its exact closed locator codecs and issued owners')
        if len({(kind.SCHEMA, kind.VERSION) for kind in self.prospective_bootstrap_record_types}) != len(self.prospective_bootstrap_record_types):
            raise ValueError('prospective bootstrap repeats a canonical locator revision')
        if (type(self.read_access_record_types) is not tuple
                or any(not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
                    for kind in self.read_access_record_types)
                or len(set(self.read_access_record_types)) != len(self.read_access_record_types)
                or bool(self.read_access_record_types) != (self.select_read_access is not None)
                or self.select_read_access is not None and not callable(self.select_read_access)):
            raise TypeError('read access selection requires exact locator codecs and its code-owned projection')
        if len({(kind.SCHEMA, kind.VERSION) for kind in self.read_access_record_types}) != len(self.read_access_record_types):
            raise ValueError('read access selection repeats a canonical locator revision')
        if self.specification_schema is not None:
            validate_schema(self.specification_schema)


@dataclass(frozen=True, slots=True)
class ExperimentInputDerivationResult:
    """Operational current metadata output, not a scientific authority grant."""
    specification: ObjectIdentity
    source_selection: CanonicalRecord
    source_selection_path: Path
    preparation: ExperimentPreparation
    publications: tuple[ArtifactWriteResult, ...]
    requirements_publication: ArtifactWriteResult
    target_specification: CanonicalRecord | None = None
    target_specification_path: Path | None = None

    def __post_init__(self):
        from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
        from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
        if (self.target_specification is None) != (self.target_specification_path is None):
            raise ValueError('preprocessing transition requires both exact target specification and path')
        if self.target_specification is not None:
            if (not isinstance(self.target_specification, CanonicalRecord)
                    or not isinstance(self.target_specification_path, Path) or not self.target_specification_path.is_absolute()
                    or getattr(self.target_specification, 'identity', None) != self.preparation.specification
                    or self.preparation.specification_record != self.target_specification):
                raise TypeError('preprocessing transition substitutes its actual target specification or preparation')
            self.target_specification.__post_init__()
        if (type(self.specification) is not ObjectIdentity
                or type(self.source_selection) is not ExperimentFileInputSelection
                or type(self.preparation) is not ExperimentPreparation
                or not isinstance(self.source_selection_path, Path)
                or not self.source_selection_path.is_absolute()
                or self.target_specification is None and self.preparation.specification != self.specification):
            raise TypeError("derived experiment inputs require exact selected specification, selector, path and preparation")
        self.source_selection.__post_init__()
        self.preparation.__post_init__()
        if type(self.publications) is not tuple or any(type(row) is not ArtifactWriteResult for row in self.publications):
            raise TypeError("derived current metadata must retain actual publication records")
        for row in self.publications:
            row.__post_init__()
        if (type(self.requirements_publication) is not ArtifactWriteResult
                or self.requirements_publication not in self.publications
                or self.requirements_publication.logical.payload_schema != "empirical-lawhood/operational/experiment-input-requirements"):
            raise TypeError("derived inputs must retain their exact complete operational requirements publication")
