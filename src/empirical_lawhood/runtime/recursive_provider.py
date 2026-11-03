# SPDX-License-Identifier: MPL-2.0
"""Existing executable factories for stateless registered scientific operations."""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
from hashlib import sha256
from types import MappingProxyType
from typing import Callable, Mapping, Protocol

from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.study_authoring import CapabilitySelection
from .capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission
from .artifacts import ArtifactProfile, is_canonical_json_media_type
from .recursive_storage_codecs import (RecursiveStorageCodec, resolve_storage_codec,
                                     validate_storage_codecs)
from .execution import ParentPreparedTaskRunner, TaskRunner
from .executable_bindings import (ExecutableBindingRole, ExecutableCapabilityBinding,
                                  ExecutableRecordTypeBinding, ExternalConfigExecutableCapabilityBinding)
from .plans import (BarrierKind, ExternalInputSpec, OutputTemplate, ScientificStage,
                    validate_scientific_stage_barrier)
from .providers import (CampaignRuntimeProvider, CapabilityOutputSemanticContract, CapabilityWorkerPreparation,
                        ExternalInputPayload, validate_worker_preparations)
from .recursive_compiler import (RecursiveOperationRegistration, RecursivePortContract,
                                 RegisteredPublicationRequirement, RegisteredProvenanceRequirement)


class RecursiveInputSupplier(Protocol):
    """Create a fresh bounded source for an exact frozen input; never run science."""
    def resolve_input(self, spec: ExternalInputSpec) -> ExternalInputPayload: ...


@dataclass(frozen=True, slots=True)
class RecursiveOperationInputPort:
    """Noncanonical code-injected source port, scoped to one registered operation."""
    supplier: RecursiveInputSupplier

    def __post_init__(self) -> None:
        if not callable(getattr(self.supplier, "resolve_input", None)):
            raise TypeError("recursive input supplier lacks its bounded exact-input method")


def recursive_input_port_key(selection) -> str:
    return f"recursive.inputs.{selection.capability_key}"


def recursive_operation_binding(*, registration: RecursiveOperationRegistration, manifest: CapabilityManifest,
                                components=()) -> ExecutableCapabilityBinding:
    """Static descriptor; all scientific input bytes remain in frozen input contracts."""
    if (manifest.capability_key != registration.selection.capability_key
        or manifest.capability_version != registration.selection.capability_version
        or manifest.implementation_sha256 != registration.selection.implementation_sha256):
        raise ValueError("recursive binding manifest differs from its registered operation")
    return ExternalConfigExecutableCapabilityBinding(
        binding_id=f"executable.{manifest.capability_key}", capability_key=manifest.capability_key,
        capability_version=manifest.capability_version,
        capability_implementation_sha256=manifest.implementation_sha256,
        role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
        provider_key=f"recursive.provider.{manifest.capability_key}", provider_version="1.0.0",
        provider_implementation_sha256=manifest.implementation_sha256, capability_backed=True,
        discovery_components=tuple(components), accepted_profile_types=(),
        accepted_config_types=(ExecutableRecordTypeBinding(registration.config_record_type.SCHEMA,
                                                          registration.config_record_type.VERSION),),
        required_issued_payload_schemas=(), codec_registration_identities=(), issued_decoder_registrations=(),
        input_schema_ids=manifest.input_schema_ids, output_schema_ids=manifest.output_schema_ids,
        artifact_validator_identities=(), required_platform_port_keys=(recursive_input_port_key(registration.selection),),
        may_require_active_mount=manifest.requires_active_mount, may_require_source_qualification=False,
        may_require_network=manifest.requires_network, may_require_authority=False,
    )


@dataclass(frozen=True, slots=True)
class RecursiveOperationProviderFactory:
    binding: ExecutableCapabilityBinding
    registration: RecursiveOperationRegistration
    manifest: CapabilityManifest
    runner_factory: Callable[[], TaskRunner]
    output_codecs: Mapping[str, type[CanonicalRecord]]
    contribution_describer: Callable | None = None
    next_wave_builder: Callable | None = None
    inquiry_outcome_projector: Callable | None = None
    inquiry_evidence_projector: Callable | None = None
    inquiry_endpoint_validator: Callable | None = None
    inquiry_record_identity: Callable | None = None
    inquiry_work_projector: Callable | None = None
    runner_preparation_factory: Callable[[RecursiveInputSupplier, TaskRunner], ParentPreparedTaskRunner] | None = None

    def __post_init__(self) -> None:
        from .stage_contracts import validate_operation_stage_kind

        validate_operation_stage_kind(self.registration.stage, self.manifest.kind,
            outcome_access=self.registration.outcome_access,
            visibility_ceiling=self.registration.visibility_ceiling)
        expected = recursive_operation_binding(registration=self.registration, manifest=self.manifest,
                                               components=self.binding.discovery_components)
        if self.binding != expected:
            raise ValueError("recursive factory changes its static executable descriptor")
        for callback in (self.contribution_describer, self.next_wave_builder, self.inquiry_outcome_projector, self.inquiry_evidence_projector, self.inquiry_endpoint_validator, self.inquiry_record_identity, self.inquiry_work_projector, self.runner_preparation_factory):
            if callback is not None and not callable(callback):
                raise TypeError("recursive contribution callbacks must be code-owned callables")
        if not callable(self.runner_factory):
            raise TypeError("recursive runner factory must be code-owned")
        if self.runner_preparation_factory is not None and (
                not self.registration.native_effect and self.registration.native_effect_slot_ids is not None):
            raise ValueError('pure parent preparation cannot introduce native effect slots')
        for port in self.registration.input_ports:
            if not is_canonical_json_media_type(port.media_type) and resolve_storage_codec(self.registration.storage_codecs,
                    payload_schema=port.payload_schema, media_type=port.media_type) is None:
                raise ValueError("recursive factory input lacks its exact registered storage codec")
        for output in self.registration.outputs:
            if output.profile is not ArtifactProfile.CANONICAL_JSON:
                if resolve_storage_codec(self.registration.storage_codecs, payload_schema=output.payload_schema,
                        profile=output.profile, media_type=output.media_type) is not None:
                    continue
                raise ValueError("recursive factory output lacks an exact typed codec or registered storage codec")
            codec = self.output_codecs.get(output.payload_schema)
            if codec is None or codec.SCHEMA != output.payload_schema:
                raise ValueError("recursive factory output lacks an exact typed codec")

    def build_provider(self, *, registry, records, platform_ports) -> CampaignRuntimeProvider:
        if records or tuple(port.port_key for port in platform_ports) != self.binding.required_platform_port_keys:
            raise ValueError("recursive factory needs only its exact bounded input platform port")
        port = platform_ports[0].port
        if not isinstance(port, RecursiveOperationInputPort):
            raise TypeError("recursive factory received another platform product")
        registered = registry.resolve(self.manifest.capability_key, self.manifest.capability_version)
        if registered != self.manifest:
            raise ValueError("recursive factory manifest differs from its frozen registry")
        return RecursiveOperationProvider(registry, self.registration, self.manifest, self.runner_factory,
                                          self.output_codecs, port.supplier, self.runner_preparation_factory)


class RecursiveOperationProvider(CampaignRuntimeProvider):
    """One registered operation; the existing composite owns scheduler composition."""
    def __init__(self, registry, registration, manifest, runner_factory, output_codecs, supplier,
                 runner_preparation_factory=None):
        self.registry = registry
        self.registry_sha256 = registry.fingerprint()
        self.capability_count = 1
        self.registration = registration
        self.manifest = manifest
        self.runner_factory = runner_factory
        self.output_codecs = dict(output_codecs)
        self.supplier = supplier
        self.runner_preparation_factory = runner_preparation_factory
        self.issued_source_schema_ids = ()

    def worker_preparations(self, registry, execution_plan=None):
        if registry != self.registry:
            raise ValueError("recursive worker preparation registry differs")
        registration = self.registration
        if registration.selection != CapabilitySelection(self.manifest.capability_key,
                self.manifest.capability_version, self.manifest.implementation_sha256):
            raise ValueError("recursive worker preparation changes its installed operation")
        return validate_worker_preparations((CapabilityWorkerPreparation(
            registration.selection, registration.provenance_requirements, registration.native_effect,
            registration.native_work_preparer, registration.worker_environment_selector),), registry, execution_plan)

    def runners(self, registry, source_records=()):
        if registry != self.registry or source_records:
            raise ValueError("recursive provider refuses changed registry or undeclared issued sources")
        runner = self.runner_factory()
        if runner.manifest != self.manifest:
            raise ValueError("recursive stateless runner differs from the registered manifest")
        if self.runner_preparation_factory is not None:
            runner = self.runner_preparation_factory(self.supplier, runner)
            if (not isinstance(runner, ParentPreparedTaskRunner) or runner.manifest != self.manifest
                    or runner.native_effect != self.registration.native_effect):
                raise ValueError('recursive preparation factory changes its explicit wrapper or installed manifest')
        return (runner,)

    def external_inputs(self, plan, source_records=()):
        if plan.registry_sha256 != self.registry_sha256 or source_records:
            raise ValueError("recursive provider input scope differs from the frozen plan")
        owners = {}
        exact = {}
        for task in plan.tasks:
            for spec in task.external_inputs:
                current = exact.setdefault(spec.logical_artifact_id, spec)
                if replace(current, input_id=spec.input_id) != spec:
                    raise ValueError("recursive tasks disagree about a shared external input")
                owners[spec.logical_artifact_id] = min(owners.get(spec.logical_artifact_id, f"{task.capability.capability_key}@{task.capability.capability_version}"),
                                                     f"{task.capability.capability_key}@{task.capability.capability_version}")
        values = []
        for artifact_id in sorted(exact):
            if owners[artifact_id] != self.manifest.registry_id:
                continue
            spec = exact[artifact_id]
            payload = self.supplier.resolve_input(spec)
            if (payload.logical_artifact_id != spec.logical_artifact_id
                or (spec.expected_content_sha256 is not None and
                    (payload.logical_content_sha256 not in {None, spec.expected_content_sha256}
                     or payload.source_sha256 != spec.expected_content_sha256))
                or (spec.identity_scope_sha256 is not None and not any(
                    parent.identity.object_fingerprint == spec.identity_scope_sha256 for parent in payload.lineage_parents))
                or payload.payload_schema != spec.expected_payload_schema
                or (spec.expected_media_type is not None and payload.media_type != spec.expected_media_type)
                or (spec.expected_size_bytes is not None and payload.size_bytes != spec.expected_size_bytes)
                or (spec.expected_outcome_access is not None and payload.outcome_access is not spec.expected_outcome_access)
                or (spec.expected_visibility_ceiling is not None and payload.visibility_ceiling is not spec.expected_visibility_ceiling)):
                payload.close()
                raise ValueError("recursive supplied bytes or scientific access differ from the frozen input")
            values.append(payload)
        return tuple(values)

    def output_semantic_contracts(self, registry, execution_plan=None):
        if registry != self.registry:
            raise ValueError("recursive semantic registry differs")
        contracts = {}
        for output in self.registration.outputs:
            if output.profile is not ArtifactProfile.CANONICAL_JSON:
                contract = CapabilityOutputSemanticContract.from_manifest(
                    self.manifest, payload_schema=output.payload_schema, profile=output.profile)
            else:
                contract = CapabilityOutputSemanticContract.from_manifest(
                    self.manifest, payload_schema=output.payload_schema, profile=output.profile,
                    top_level_keys=("schema", "value", "version"),
                    value_keys=tuple(sorted(field.name for field in fields(self.output_codecs[output.payload_schema]))),
                    record_version=self.output_codecs[output.payload_schema].VERSION)
            if contracts.setdefault(contract.key, contract) != contract:
                raise ValueError("recursive outputs give one semantic key conflicting typed contracts")
        return tuple(contracts.values())

    def scientific_adjudication_contract(self, registry, execution_plan=None):
        if registry != self.registry:
            raise ValueError("recursive adjudication registry differs")
        from .adjudication import MAX_ADJUDICATION_BYTES, ScientificAdjudicationOutputContract, ScientificAdjudicationRecord
        declared = tuple(output for output in self.registration.outputs
                         if output.output_id == self.registration.adjudication_output_id
                         and output.payload_schema == ScientificAdjudicationRecord.SCHEMA)
        if not declared:
            return None
        if len(declared) != 1 or execution_plan is None:
            raise ValueError('recursive adjudicator needs its exact single planned output')
        matches = tuple((task, output) for task in execution_plan.tasks
                        if task.capability.capability_key == self.manifest.capability_key
                        and task.capability.capability_version == self.manifest.capability_version
                        for output in task.outputs if output.payload_schema == ScientificAdjudicationRecord.SCHEMA)
        if len(matches) != 1:
            raise ValueError('recursive adjudication locator is ambiguous in this selected wave')
        return ScientificAdjudicationOutputContract(self.manifest.capability_key, self.manifest.capability_version,
                    matches[0][1].output_id, ScientificAdjudicationRecord.SCHEMA,
                    maximum_bytes=min(MAX_ADJUDICATION_BYTES, matches[0][0].capability.requested_resources.output_bytes)
                    if matches[0][0].capability.requested_resources.output_bytes is not None else MAX_ADJUDICATION_BYTES)


@dataclass(frozen=True, slots=True)
class RecursiveScientificHooks:
    assessment_projector: Callable | None = None
    scientific_operand_sha256s: Callable | None = None
    adjudication_output_id: str | None = None
    qualified_parent_assessor: Callable | None = None
    scientific_unit_ids: Callable | None = None
    native_effect_slot_ids: Callable | None = None
    scientific_root_validator: Callable | None = None
    scientific_claim_resolver: Callable | None = None
    qualified_parent_evidence_schema_ids: tuple[str, ...] = ()
    qualified_parent_prior_execution_bindings: Callable | None = None
    qualified_parent_prior_execution_scope_validator: Callable | None = None
    scientific_root_preparer: Callable | None = None

    def __post_init__(self):
        if self.scientific_root_preparer is not None and (
                not callable(self.scientific_root_preparer) or not callable(self.scientific_root_validator)):
            raise TypeError("scientific root preparation requires a code-owned preparer and validator")


@dataclass(frozen=True, slots=True)
class RecursiveInquiryHooks:
    contribution_describer: Callable | None = None
    next_wave_builder: Callable | None = None
    inquiry_outcome_projector: Callable | None = None
    inquiry_evidence_projector: Callable | None = None
    inquiry_endpoint_validator: Callable | None = None
    inquiry_record_identity: Callable | None = None
    inquiry_work_projector: Callable | None = None


@dataclass(frozen=True, slots=True)
class RecursiveExecutionProperties:
    barrier: BarrierKind = BarrierKind.NONE
    native_effect: bool = False
    native_work_preparer: Callable | None = None
    complete_unit_census: bool = False
    deterministic: bool = True
    seed_required: bool = False
    requires_clean_commit: bool = True
    requires_active_mount: bool = True
    requires_network: bool = False
    runner_preparation_factory: Callable | None = None
    worker_environment_selector: Callable | None = None


@dataclass(frozen=True, slots=True)
class RecursiveOperationDeclaration:
    """One code-owned operation, deriving existing cold and executable projections.

    Construction checks contracts without invoking runners, scientific validators,
    input readers or environment probes. Domain hooks retain their scientific scope.
    """

    capability_key: str
    capability_version: str
    implementation_id: str
    kind: CapabilityKind
    config_record_type: type[CanonicalRecord]
    stage: ScientificStage
    input_ports: tuple[RecursivePortContract, ...]
    outputs: tuple[OutputTemplate, ...]
    permissions: tuple[CapabilityPermission, ...]
    evidence_ceiling: EvidenceCeiling
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    resources: ResourceBudget
    conformance_check_ids: tuple[str, ...]
    runner_factory: Callable[[], TaskRunner]
    record_codecs: Mapping[str, type[CanonicalRecord]]
    scientific_hooks: RecursiveScientificHooks = RecursiveScientificHooks()
    inquiry_hooks: RecursiveInquiryHooks = RecursiveInquiryHooks()
    execution_properties: RecursiveExecutionProperties = RecursiveExecutionProperties()
    publication_requirements: tuple[RegisteredPublicationRequirement, ...] = ()
    provenance_requirements: tuple[RegisteredProvenanceRequirement, ...] = ()
    storage_codecs: tuple[RecursiveStorageCodec, ...] = ()
    input_record_types: tuple[type[CanonicalRecord], ...] = ()
    config_input_parents: Callable | None = None
    runtime_id: str | None = None
    implementation_sha256: str | None = None
    additional_input_schema_ids: tuple[str, ...] = ()

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_stable_id

        validate_stable_id(self.implementation_id)
        validate_storage_codecs(self.storage_codecs)
        if (type(self.scientific_hooks) is not RecursiveScientificHooks
                or type(self.inquiry_hooks) is not RecursiveInquiryHooks
                or type(self.execution_properties) is not RecursiveExecutionProperties):
            raise TypeError("operation declaration needs its typed scientific/inquiry/execution contracts")
        validate_scientific_stage_barrier(self.stage, self.execution_properties.barrier)
        if (not isinstance(self.config_record_type, type)
                or not issubclass(self.config_record_type, CanonicalRecord)):
            raise TypeError("operation declaration needs a strict canonical configuration type")
        codecs = dict(self.record_codecs)
        for schema, codec in codecs.items():
            if (not isinstance(codec, type) or not issubclass(codec, CanonicalRecord)
                    or codec.SCHEMA != schema):
                raise ValueError("operation declaration substitutes a strict record codec")
        object.__setattr__(self, "record_codecs", MappingProxyType(codecs))
        registration = self.registration()
        for hook in fields(self.scientific_hooks):
            value = getattr(self.scientific_hooks, hook.name)
            if hook.name not in ("adjudication_output_id", "qualified_parent_evidence_schema_ids"):
                if value is not None and not callable(value):
                    raise TypeError("scientific operation hooks must be code-owned callables")
        for value in fields(self.execution_properties):
            if value.name not in ("barrier", "runner_preparation_factory", "native_work_preparer", "worker_environment_selector"):
                if type(getattr(self.execution_properties, value.name)) is not bool:
                    raise TypeError("operation execution properties require exact booleans")
        storage = {}
        for codec in self.storage_codecs:
            key = (codec.payload_schema, codec.profile, codec.media_type)
            if key in storage:
                raise ValueError("operation declaration repeats an exact storage codec")
            storage[key] = codec
        for port in registration.input_ports:
            if is_canonical_json_media_type(port.media_type):
                canonical = port.payload_schema in codecs or any(
                    kind.SCHEMA == port.payload_schema for kind in self.input_record_types)
                raw = resolve_storage_codec(self.storage_codecs,
                    payload_schema=port.payload_schema, media_type=port.media_type)
                if canonical and raw is not None:
                    raise ValueError("operation JSON input ambiguously declares canonical records and raw storage")
                if not canonical and (raw is None or raw.profile is not ArtifactProfile.RAW_SOURCE_BYTES):
                    raise ValueError("operation input lacks its declared strict record codec")
            elif not any(schema == port.payload_schema and media == port.media_type
                         for schema, _, media in storage):
                raise ValueError("operation binary input lacks an exact registered storage codec")
        for output in registration.outputs:
            if output.profile is ArtifactProfile.CANONICAL_JSON:
                if not is_canonical_json_media_type(output.media_type) or output.payload_schema not in codecs:
                    raise ValueError("operation output lacks its exact JSON contract and strict codec")
            elif (output.payload_schema, output.profile, output.media_type) not in storage:
                raise ValueError("operation binary output lacks an exact registered storage codec")
        self.provider_factory()  # Contract validation only; never construct a runner.

    def manifest(self) -> CapabilityManifest:
        props = self.execution_properties
        return CapabilityManifest(
            capability_key=self.capability_key, capability_version=self.capability_version,
            kind=self.kind, config_schema=self.config_record_type.SCHEMA,
            config_schema_sha256=sha256(self.config_record_type.SCHEMA.encode()).hexdigest(),
            input_schema_ids=tuple(sorted({self.config_record_type.SCHEMA,
                *(port.payload_schema for port in self.input_ports), *self.additional_input_schema_ids})),
            output_schema_ids=tuple(sorted({output.payload_schema for output in self.outputs})),
            permissions=self.permissions, maximum_evidence_ceiling=self.evidence_ceiling,
            maximum_outcome_access=self.outcome_access, resource_ceiling=self.resources,
            deterministic=props.deterministic, seed_required=props.seed_required,
            language_id="python", runtime_id=self.capability_key if self.runtime_id is None else self.runtime_id,
            requires_clean_commit=props.requires_clean_commit,
            requires_active_mount=props.requires_active_mount, requires_network=props.requires_network,
            conformance_check_ids=self.conformance_check_ids,
            implementation_sha256=(sha256((self.capability_key + "." + self.implementation_id).encode()).hexdigest()
                if self.implementation_sha256 is None else self.implementation_sha256))

    def registration(self) -> RecursiveOperationRegistration:
        manifest = self.manifest()
        props = self.execution_properties
        return RecursiveOperationRegistration(
            selection=CapabilitySelection(manifest.capability_key, manifest.capability_version,
                                          manifest.implementation_sha256),
            stage=self.stage, config_record_type=self.config_record_type,
            input_ports=self.input_ports, outputs=self.outputs,
            required_permissions=self.permissions, outcome_access=self.outcome_access,
            visibility_ceiling=self.visibility_ceiling, resource_ceiling=self.resources,
            barrier=props.barrier, native_effect=props.native_effect,
            complete_unit_census=props.complete_unit_census,
            publication_requirements=self.publication_requirements,
            provenance_requirements=self.provenance_requirements,
            storage_codecs=self.storage_codecs,
            input_record_types=self.input_record_types,
            native_work_preparer=props.native_work_preparer,
            worker_environment_selector=props.worker_environment_selector,
            config_input_parents=self.config_input_parents,
            **{field.name: getattr(self.scientific_hooks, field.name)
               for field in fields(self.scientific_hooks)})

    def provider_factory(self, *, components=()) -> RecursiveOperationProviderFactory:
        manifest = self.manifest()
        registration = self.registration()
        return RecursiveOperationProviderFactory(
            binding=recursive_operation_binding(registration=registration, manifest=manifest,
                                                components=components),
            registration=registration, manifest=manifest,
            runner_factory=self.runner_factory, output_codecs=self.record_codecs,
            runner_preparation_factory=self.execution_properties.runner_preparation_factory,
            **{field.name: getattr(self.inquiry_hooks, field.name)
               for field in fields(self.inquiry_hooks)})
