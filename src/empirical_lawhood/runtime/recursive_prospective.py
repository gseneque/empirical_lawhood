# SPDX-License-Identifier: MPL-2.0
"""Prospective composition through existing authoring, source and issue contracts."""
from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
from typing import TYPE_CHECKING, ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (CanonicalRecord, require_sorted_unique_ids,
                                                     validate_stable_id, validate_sha256)
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage, ProposedStudyExtension
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection, RecursiveStudyDraft
from empirical_lawhood.planning.study_authoring import DesignInputRecord, MaterializationQualificationReceipt
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure
from .artifacts import ArtifactLineageParent
from .execution_envelope import ExecutionResourceEnvelopeSpec
from .candidate_compiler import CandidateCompilationContext, ExecutableStudyCandidate, StandardCandidateCompilationContext
from .candidate_composition import (
    CandidateCapabilityCatalog, CandidateCapabilityRegistration,
    CandidateContextResolution, StandardCandidateContextResolution,
)
from .recursive_compiler import RecursiveCompilation
from .recursive_qualified_parents import RecursiveQualifiedParentBinding
from .study_issue import IssuedExtensionSet, StudyExtensionDecoderRegistration

if TYPE_CHECKING:
    from .source_resolution import CandidateSourceResolutionService


RECURSIVE_SELECTION_DECODER_KEY = "recursive.scientific-selection"
RECURSIVE_SELECTION_MAXIMUM_BYTES = 16 * 1024**2
BOUNDED_RECURSIVE_SELECTION_DECODER_KEY = "recursive.scientific-selection-bounded32"
BOUNDED_RECURSIVE_SELECTION_MAXIMUM_BYTES = 32 * 1024**2
# Additive operational capacity profiles; historical decoder/carrier limits
# remain unchanged. These allocations confer no scientific authority.
LARGE_RECURSIVE_SELECTION_DECODER_KEY = "recursive.scientific-selection-bounded64"
LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES = 64 * 1024**2
DRAFT128_RECURSIVE_SELECTION_DECODER_KEY = "recursive.scientific-selection-draft128"
DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES = 128 * 1024**2
LARGE_RECURSIVE_OPERATIONAL_ENVELOPE_MAXIMUM_BYTES = 256 * 1024**2
LARGE_RECURSIVE_RETAINED_MEMBER_MAXIMUM_BYTES = 512 * 1024**2


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveOperand(CanonicalRecord):
    """An exact physical source, including its declared enclosing scope.

    The selected scientific input and storage codec own applicable byte bounds.
    Control-record decoding limits do not limit the size of its referenced data.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/recursive-prospective-operand'
    logical_artifact_id: str
    content_sha256: str
    size_bytes: int
    payload_schema: str
    media_type: str
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    lineage_parents: tuple[ArtifactLineageParent, ...] = ()

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_schema
        validate_stable_id(self.logical_artifact_id, field_name='logical_artifact_id')
        validate_sha256(self.content_sha256)
        validate_schema(self.payload_schema)
        if type(self.size_bytes) is not int or self.size_bytes <= 0 or not self.media_type:
            raise ValueError('prospective operand requires its positive exact physical byte size')
        identities = tuple(parent.identity for parent in self.lineage_parents)
        if identities != tuple(sorted(set(identities), key=lambda value: (value.object_id, value.object_schema,
                                                                       value.object_version, value.object_fingerprint))):
            raise ValueError('prospective operand lineage must be sorted and exact')


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveDesignInputs:
    """Exact candidate inputs before operational resources can be bound.

    This operational projection is not a canonical scientific record, a handoff
    or an authority. The existing candidate owner still authenticates its inputs.
    """
    spec_id: str
    draft: RecursiveStudyDraft
    entry_package: ExperimentEntryPackage
    formal_methods: FormalMethodCatalog
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    known_design_inputs: tuple[DesignInputRecord, ...]
    external_operands: tuple[RecursiveProspectiveOperand, ...] = ()
    qualified_parent_bindings: tuple[RecursiveQualifiedParentBinding, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.spec_id, field_name='spec_id')
        for record, kind in ((self.draft, RecursiveStudyDraft), (self.entry_package, ExperimentEntryPackage),
                (self.formal_methods, FormalMethodCatalog)):
            if type(record) is not kind:
                raise TypeError('prospective design needs its exact scientific record types')
            record.__post_init__()
        if self.draft.prospective_draft is None or self.draft.development_study is not None:
            raise ValueError('prospective authoring requires its genuine prospective scientific root')
        for values, kind, attribute, name in ((self.qualifications, MaterializationQualificationReceipt, 'receipt_id', 'qualifications'),
                (self.known_design_inputs, DesignInputRecord, 'input_id', 'known_design_inputs'),
                (self.formal_source_inventories, FormalGapSourceCapabilityInventory, 'denominator_id', 'formal_source_inventories'),
                (self.external_operands, RecursiveProspectiveOperand, 'logical_artifact_id', 'external_operands'),
                (self.qualified_parent_bindings, RecursiveQualifiedParentBinding, 'binding_id', 'qualified_parent_bindings')):
            if type(values) is not tuple or any(type(row) is not kind for row in values):
                raise TypeError('prospective design needs its exact typed ' + name)
            require_sorted_unique_ids(values, attribute=attribute, field_name=name)
            for row in values:
                row.__post_init__()
        if not self.formal_source_inventories:
            raise ValueError('prospective entry requires its actual formal source denominator')

    @classmethod
    def from_spec(cls, spec):
        if type(spec) is not RecursiveProspectiveAuthoringSpec:
            raise TypeError('prospective design projection requires its exact bound specification')
        return cls(**{field.name: getattr(spec, field.name) for field in fields(cls)})

    def bind_resources(self, resources):
        return RecursiveProspectiveAuthoringSpec(**{field.name: getattr(self, field.name) for field in fields(self)},
            resources=resources)


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveAuthoringSpec(CanonicalRecord):
    """A genuine standard entry package beside the shared authored scientific graph."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/recursive-prospective-authoring-spec'
    spec_id: str
    draft: RecursiveStudyDraft
    entry_package: ExperimentEntryPackage
    formal_methods: FormalMethodCatalog
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    known_design_inputs: tuple[DesignInputRecord, ...]
    resources: ExecutionResourceEnvelopeSpec
    external_operands: tuple[RecursiveProspectiveOperand, ...] = ()
    qualified_parent_bindings: tuple[RecursiveQualifiedParentBinding, ...] = ()

    def __post_init__(self):
        RecursiveProspectiveDesignInputs.from_spec(self)
        if type(self.resources) is not ExecutionResourceEnvelopeSpec:
            raise TypeError('prospective authoring requires its exact bound resource envelope')
        self.resources.__post_init__()


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveCandidatePreview:
    """Nonauthorizing comparison facts, freshly checked by the authoring owner.

    One API invocation may retain its prepared immutable compilation. A preview
    supplied to another invocation carries no compilation or access verdict.
    """

    design_inputs: RecursiveProspectiveDesignInputs
    implementation: ImplementationSourceClosure
    candidate: ExecutableStudyCandidate
    issued_extensions: IssuedExtensionSet

    def __post_init__(self):
        for value, kind in ((self.design_inputs, RecursiveProspectiveDesignInputs),
                (self.implementation, ImplementationSourceClosure), (self.candidate, ExecutableStudyCandidate),
                (self.issued_extensions, IssuedExtensionSet)):
            if type(value) is not kind:
                raise TypeError('prospective preview requires its exact actual candidate projection types')
            value.__post_init__()
        proposed = self.candidate.authoring_package.extension_set
        if (self.implementation.source_closure_id != self.design_inputs.spec_id + '.source-closure'
                or self.issued_extensions.proposed_extension_set != ObjectIdentity.from_record(proposed.extension_set_id, proposed)):
            raise ValueError('prospective preview changes its exact source or outer candidate extension association')


def recursive_selection_decoder_registration(*, implementation_sha256: str) -> StudyExtensionDecoderRegistration:
    return StudyExtensionDecoderRegistration(
        "decoder.recursive-scientific-selection", RECURSIVE_SELECTION_DECODER_KEY, "1.0.0",
        RecursiveScientificSelection.SCHEMA, RecursiveScientificSelection.VERSION,
        sha256(RecursiveScientificSelection.SCHEMA.encode()).hexdigest(), implementation_sha256,
        RECURSIVE_SELECTION_MAXIMUM_BYTES)


def bounded_recursive_selection_decoder_registration(*, implementation_sha256: str) -> StudyExtensionDecoderRegistration:
    """Add a separately installed capacity; retain the original decoder bytes."""
    return StudyExtensionDecoderRegistration(
        "decoder.recursive-scientific-selection-bounded32", BOUNDED_RECURSIVE_SELECTION_DECODER_KEY, "1.0.0",
        RecursiveScientificSelection.SCHEMA, RecursiveScientificSelection.VERSION,
        sha256(RecursiveScientificSelection.SCHEMA.encode()).hexdigest(), implementation_sha256,
        BOUNDED_RECURSIVE_SELECTION_MAXIMUM_BYTES)



def large_recursive_selection_decoder_registration(*, implementation_sha256: str) -> StudyExtensionDecoderRegistration:
    """An explicitly installed larger capacity beside both historical decoders."""
    return StudyExtensionDecoderRegistration(
        "decoder.recursive-scientific-selection-bounded64", LARGE_RECURSIVE_SELECTION_DECODER_KEY, "1.0.0",
        RecursiveScientificSelection.SCHEMA, RecursiveScientificSelection.VERSION,
        sha256(RecursiveScientificSelection.SCHEMA.encode()).hexdigest(), implementation_sha256,
        LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES)


def draft128_recursive_selection_decoder_registration(*, implementation_sha256: str) -> StudyExtensionDecoderRegistration:
    """Admit a 128 MiB draft while preserving the 64 MiB scientific payload."""
    return StudyExtensionDecoderRegistration(
        "decoder.recursive-scientific-selection-draft128", DRAFT128_RECURSIVE_SELECTION_DECODER_KEY, "1.0.0",
        RecursiveScientificSelection.SCHEMA, RecursiveScientificSelection.VERSION,
        sha256(RecursiveScientificSelection.SCHEMA.encode()).hexdigest(), implementation_sha256,
        LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES)


def recursive_selection_proposal(*, selection: RecursiveScientificSelection,
                                 registration: StudyExtensionDecoderRegistration) -> ProposedStudyExtension:
    bounds = {RECURSIVE_SELECTION_DECODER_KEY: RECURSIVE_SELECTION_MAXIMUM_BYTES,
        BOUNDED_RECURSIVE_SELECTION_DECODER_KEY: BOUNDED_RECURSIVE_SELECTION_MAXIMUM_BYTES,
        LARGE_RECURSIVE_SELECTION_DECODER_KEY: LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES,
        DRAFT128_RECURSIVE_SELECTION_DECODER_KEY: LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES}
    if (registration.payload_schema != selection.SCHEMA or registration.payload_version != selection.VERSION
        or bounds.get(registration.decoder_key) != registration.maximum_payload_bytes
        or len(selection.canonical_bytes()) > registration.maximum_payload_bytes):
        raise ValueError("recursive scientific proposal differs from its allowlisted decoder")
    return ProposedStudyExtension("extension.recursive-scientific-selection", "recursive.science",
           ObjectIdentity.from_record(selection.selection_id, selection), len(selection.canonical_bytes()),
           registration.decoder_key, registration.decoder_version, registration.config_sha256, True,
           OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)


def recursive_capability_catalog(compilation: RecursiveCompilation, registrations=()) -> CandidateCapabilityCatalog:
    """Static catalog exposes the same actual materialized topology and manifests."""
    manifests = tuple(compilation.registry.resolve(selection.capability_key, selection.capability_version)
                      for selection in sorted({operation.selection for operation in compilation.operations},
                                              key=lambda value: value.selection_id))
    actual = {registration.registration_id: registration for registration in registrations}
    rows = tuple(actual.get(manifest.registry_id, CandidateCapabilityRegistration(manifest,
                 f"recursive.provider.{manifest.capability_key}", "1.0.0", "application/json",
                 RECURSIVE_SELECTION_MAXIMUM_BYTES)) for manifest in manifests)
    if any(row.manifest != manifest for row, manifest in zip(rows, manifests, strict=True)):
        raise ValueError('recursive static discovery changes its exact installed manifest')
    return CandidateCapabilityCatalog(f"catalog.{compilation.draft.draft_id}", rows,
        (compilation.template,))


def validate_recursive_issued_selection(*, selection, candidate, registry):
    """Authenticate shared science against actual issued graph and config ports."""
    from .recursive_compiler import configuration_edge_id, configuration_input_id
    from .scientific_graph_preservation import _validate_configuration_graph_bindings

    draft = candidate.authoring_package.base.draft
    base = candidate.base_candidate.base_candidate
    if selection.scientific_root != ObjectIdentity.from_record(draft.draft_id, draft):
        raise ValueError('issued recursive scientific selection changes its genuine candidate root')
    operations = {operation.node_id: operation for operation in selection.operations}
    steps = {step.step_id: step for step in base.protocol.steps}
    nodes = {node.node_id: node for node in base.scientific_graph.nodes}
    if set(operations) != set(steps) or set(nodes) != set(operations):
        raise ValueError('issued recursive selection changes its actual operation census')
    for node, operation in operations.items():
        step = steps[node]
        manifest = registry.resolve(operation.selection.capability_key, operation.selection.capability_version)
        if (step.capability_key != operation.selection.capability_key or step.capability_version != operation.selection.capability_version
            or manifest.implementation_sha256 != operation.selection.implementation_sha256
            or nodes[node].implementation_sha256 != operation.selection.implementation_sha256
            or step.config.config_id != operation.config_id or step.config.artifact_id != operation.config_id
            or step.config.config_schema != operation.config_identity.object_schema
            or step.config.content_sha256 != operation.config_identity.object_fingerprint
            or step.resource_budget != operation.resource_budget or step.maximum_attempts != operation.maximum_attempts
            or step.resource_lock_ids != operation.resource_lock_ids or step.obligation_ids != operation.obligation_ids):
            raise ValueError('issued recursive selection changes a frozen operation or exact config operand')
    _validate_configuration_graph_bindings(base.scientific_graph, selection.operations, steps)
    configuration_edges = {configuration_edge_id(node) for node in operations}
    links = {link.edge_id: link for link in selection.links}
    edges = {edge.edge_id: edge for edge in base.scientific_graph.edges}
    if set(links) & configuration_edges or set(links) | configuration_edges != set(edges):
        raise ValueError('issued recursive selection changes its exact scientific edge census')
    for edge_id, link in links.items():
        edge = edges[edge_id]
        if ((link.producer_node_id, link.producer_output_id, link.external_input_id, link.consumer_node_id, link.consumer_input_id,
             link.scientific_role) != (edge.producer_node_id, edge.producer_output_id, edge.external_input_id,
             edge.consumer_node_id, edge.consumer_input_id, edge.scientific_role.value)):
            raise ValueError('issued recursive selection changes a scientific input role or port')
    configuration_inputs = {configuration_input_id(operation.config_id) for operation in operations.values()}
    externals = {value.input_id: value for value in selection.external_inputs}
    actual = {value.input_id: value for value in base.scientific_graph.external_inputs}
    if set(externals) & configuration_inputs or set(externals) | configuration_inputs != set(actual):
        raise ValueError('issued recursive selection changes its external scientific denominator')
    for input_id, operand in externals.items():
        actual_operand = actual[input_id]
        if ((operand.logical_artifact_id, operand.expected_content_sha256, operand.payload_schema, operand.media_type,
             operand.maximum_size_bytes, operand.outcome_access, operand.visibility_ceiling, operand.scientific_role)
            != (actual_operand.logical_artifact_id, actual_operand.expected_content_sha256, actual_operand.payload_schema,
                actual_operand.media_type, actual_operand.maximum_size_bytes, actual_operand.outcome_access,
                actual_operand.visibility_ceiling, actual_operand.scientific_role.value)):
            raise ValueError('issued recursive selection changes exact source bytes, scope or access')
    requirements = {requirement.requirement_id: requirement for requirement in selection.requirements}
    for connection in selection.connections:
        requirement = requirements.get(connection.requirement_id)
        if requirement is None or requirement.assessment_operation_id != connection.assessment_operation_id:
            raise ValueError('issued recursive connection changes its declared assessor')
        matches = tuple(link for link in selection.links if link.requirement_id == requirement.requirement_id
                        and link.connection_id == connection.connection_id and link.consumer_node_id == requirement.consumer_operation_id
                        and link.consumer_input_id == connection.consumer_input_id
                        and link.producer_node_id == connection.supplier_operation_id
                        and link.producer_output_id == connection.supplier_output_id
                        and link.external_input_id == connection.external_input_id)
        if len(matches) != 1 or connection.assessment_operation_id not in operations or connection.evidence_role not in requirement.permitted_roles:
            raise ValueError('issued recursive requirement lacks its exact supplier and permitted evidence role')


@dataclass(frozen=True, slots=True)
class RecursiveCandidateContextProvider:
    """Resolve the exact compiled draft using the existing bounded source owner."""
    compilation: RecursiveCompilation
    source_resolution_service: CandidateSourceResolutionService
    formal_methods: FormalMethodCatalog | None = None
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...] = ()
    capability_registrations: tuple[CandidateCapabilityRegistration, ...] = ()

    @property
    def catalog(self) -> CandidateCapabilityCatalog:
        return recursive_capability_catalog(self.compilation, self.capability_registrations)

    def resolve(self, draft) -> CandidateContextResolution:
        if self.compilation.candidate_draft is None or draft != self.compilation.candidate_draft:
            raise ValueError("recursive prospective context refuses a different authored scientific wave")
        template = self.compilation.template
        catalog = self.catalog
        source = self.source_resolution_service.resolve(draft=draft, templates=(template,), catalog=catalog)
        previous = self.compilation.candidate_context
        if previous is None:
            raise ValueError('recursive prospective context lacks its producing source identity')
        known = {} if previous is None else {item.input_id: item for item in previous.known_design_inputs}
        for item in draft.design_inputs:
            known.setdefault(item.input_id, item)
        context = CandidateCompilationContext(f"context.{draft.draft_id}", self.compilation.registry,
                  (template,), source.qualifications, tuple(known[key] for key in sorted(known)),
                  previous.implementation_sha256)
        return CandidateContextResolution(context, source.diagnostics, source)

    def resolve_standard(self, package) -> StandardCandidateContextResolution:
        if self.formal_methods is None or not self.formal_source_inventories:
            raise ValueError("recursive prospective readiness requires the real standard formal context")
        resolution = self.resolve(package.draft)
        system_id = package.draft.system.system_id
        inventories = tuple(value for value in self.formal_source_inventories if value.denominator_id == system_id)
        if not inventories:
            raise ValueError("recursive prospective formal context lacks the selected system denominator")
        context = StandardCandidateCompilationContext(f"standard-context.{package.package_id}", resolution.context,
                                                      self.formal_methods, inventories)
        return StandardCandidateContextResolution(context, resolution.diagnostics, resolution.source_resolution)
