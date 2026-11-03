# SPDX-License-Identifier: MPL-2.0
"""Pure materialization of selected scientific waves from code-owned operations."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import ClaimSpec, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_schema, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft, validate_selected_requirement_graph
from empirical_lawhood.planning.study_authoring import CapabilitySelection, DesignInputRecord, MaterializationQualificationReceipt, StudyDraft
from .candidate_compiler import CandidateCompilationContext, CandidateCompilationReport, StudyTemplate
from .capabilities import CapabilityPermission, CapabilityRegistry
from .artifacts import ArtifactLineageParent, ArtifactProfile, is_canonical_json_media_type, lineage_parent_sort_key
from .recursive_storage_codecs import (RecursiveStorageCodec, resolve_storage_codec,
                                     validate_storage_codecs)
from .plans import BarrierKind, ExternalInputSpec, OutputTemplate, ProtocolExecutionPlan, ScientificStage


@dataclass(frozen=True, slots=True)
class RecursivePortContract:
    port_id: str
    payload_schema: str
    media_type: str
    maximum_size_bytes: int | None
    minimum_count: int = 1
    maximum_count: int | None = 1

    def __post_init__(self) -> None:
        validate_stable_id(self.port_id, field_name="port_id")
        validate_schema(self.payload_schema)
        if not self.media_type or (self.maximum_size_bytes is not None and self.maximum_size_bytes <= 0):
            raise ValueError("scientific port needs a media type and positive optional byte bound")
        if (type(self.minimum_count) is not int or self.minimum_count < 0
                or (self.maximum_count is not None
                    and (type(self.maximum_count) is not int or self.maximum_count < 1
                         or self.minimum_count > self.maximum_count))):
            raise ValueError("scientific port multiplicity is invalid")
        if self.port_id == "config":
            raise ValueError("config is the compiler-owned implicit input")

    def matches(self, name: str) -> bool:
        return name == self.port_id if self.maximum_count == 1 else name.startswith(self.port_id + ".")


@dataclass(frozen=True, slots=True)
class RecursiveScientificRootPreparationContext:
    """One invocation's complete immutable scientific inputs, never authority."""

    root: CanonicalRecord
    config_inputs: tuple[RecursiveConfigInput, ...]
    requirements: tuple[ScientificRequirementSpec, ...]
    connections: tuple[ScientificConnectionSpec, ...]
    links: tuple[RecursiveInputLink, ...]
    external_inputs: tuple[RecursiveExternalInput, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    known_design_inputs: tuple[DesignInputRecord, ...]
    selected_unit_ids_by_selection: Mapping[str, tuple[str, ...]]

    def __post_init__(self):
        if (not isinstance(self.selected_unit_ids_by_selection, Mapping)
                or any(type(selection) is not str or type(units) is not tuple
                    or any(type(unit) is not str for unit in units)
                    or units != tuple(sorted(set(units)))
                    for selection, units in self.selected_unit_ids_by_selection.items())):
            raise TypeError("scientific preparation requires exact sorted selected-unit tuples")
        object.__setattr__(self, "selected_unit_ids_by_selection",
            MappingProxyType(dict(self.selected_unit_ids_by_selection)))


@dataclass(frozen=True, slots=True)
class RecursiveScientificRootContext:
    """Frozen compiler inputs for code-owned validation; this grants no authority."""

    root: CanonicalRecord
    node_id: str
    stage: ScientificStage
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    unit_ids: tuple[str, ...]
    selected_unit_ids: tuple[str, ...]
    complete_unit_census: bool
    requirements: tuple[ScientificRequirementSpec, ...]
    connections: tuple[ScientificConnectionSpec, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    known_design_inputs: tuple[DesignInputRecord, ...]
    config_inputs: tuple[RecursiveConfigInput, ...]
    links: tuple[RecursiveInputLink, ...]
    external_inputs: tuple[RecursiveExternalInput, ...] = ()
    scientific_preparation: object | None = None
    # Authored but unselected operations remain design metadata. They never
    # create steps, resource cells, native slots or execution authority.
    declared_config_inputs: tuple[RecursiveConfigInput, ...] = ()


@dataclass(frozen=True, slots=True)
class RegisteredPublicationRequirement:
    """Code-owned custody predicate, evaluated over its complete selected configs."""

    requirement_id: str
    validate: Callable

    def __post_init__(self):
        validate_stable_id(self.requirement_id)
        if not callable(self.validate):
            raise TypeError("publication requirement needs a code-owned validator")


@dataclass(frozen=True, slots=True)
class RegisteredProvenanceRequirement:
    """Domain numerical admissibility; observing source/runtime is shared I/O."""

    requirement_id: str
    validate_observation: Callable

    def __post_init__(self):
        validate_stable_id(self.requirement_id)
        if not callable(self.validate_observation):
            raise TypeError("provenance requirement needs a code-owned validator")


@dataclass(frozen=True, slots=True)
class RecursiveOperationRegistration:
    selection: CapabilitySelection
    stage: ScientificStage
    config_record_type: type[CanonicalRecord]
    input_ports: tuple[RecursivePortContract, ...]
    outputs: tuple[OutputTemplate, ...]
    required_permissions: tuple[CapabilityPermission, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    resource_ceiling: ResourceBudget
    barrier: BarrierKind = BarrierKind.NONE
    native_effect: bool = False
    assessment_projector: Callable | None = None
    scientific_operand_sha256s: Callable[[CanonicalRecord], tuple[str, ...]] | None = None
    adjudication_output_id: str | None = None
    qualified_parent_assessor: Callable | None = None
    scientific_unit_ids: Callable[[CanonicalRecord], tuple[str, ...]] | None = None
    native_effect_slot_ids: Callable[[CanonicalRecord], tuple[str, ...]] | None = None
    complete_unit_census: bool = False
    scientific_root_validator: Callable[[CanonicalRecord, RecursiveScientificRootContext], None] | None = None
    scientific_claim_resolver: Callable[[CanonicalRecord, RecursiveScientificRootContext,
                                        ScientificRequirementSpec, ScientificConnectionSpec], ClaimSpec] | None = None
    qualified_parent_evidence_schema_ids: tuple[str, ...] = ()
    qualified_parent_prior_execution_bindings: Callable | None = None
    qualified_parent_prior_execution_scope_validator: Callable | None = None
    publication_requirements: tuple[RegisteredPublicationRequirement, ...] = ()
    provenance_requirements: tuple[RegisteredProvenanceRequirement, ...] = ()
    storage_codecs: tuple[RecursiveStorageCodec, ...] = ()
    native_work_preparer: Callable | None = None
    input_record_types: tuple[type[CanonicalRecord], ...] = ()
    worker_environment_selector: Callable | None = None
    config_input_parents: Callable | None = None
    scientific_root_preparer: Callable | None = None

    @property
    def supported_lifecycles(self):
        from .stage_contracts import operation_lifecycle

        return (operation_lifecycle(outcome_access=self.outcome_access,
                                    visibility_ceiling=self.visibility_ceiling),)

    def __post_init__(self) -> None:
        validate_storage_codecs(self.storage_codecs)
        from .recursive_record_codecs import validate_input_record_types
        validate_input_record_types(self.input_record_types)
        if not {kind.SCHEMA for kind in self.input_record_types} <= {port.payload_schema for port in self.input_ports}:
            raise ValueError('operation input codecs include an undeclared input schema')
        if self.native_work_preparer is not None and (not self.native_effect or not callable(self.native_work_preparer)):
            raise ValueError("native work preparation requires an installed native effect and code-owned callback")
        if self.worker_environment_selector is not None and not callable(self.worker_environment_selector):
            raise TypeError("worker environment selection requires a code-owned callback")
        if self.config_input_parents is not None and not callable(self.config_input_parents):
            raise TypeError("configuration custody requires a code-owned parent projection")
        if self.scientific_root_preparer is not None and (
                not callable(self.scientific_root_preparer) or not callable(self.scientific_root_validator)):
            raise TypeError("scientific root preparation requires a code-owned preparer and validator")
        if not isinstance(self.config_record_type, type) or not issubclass(self.config_record_type, CanonicalRecord):
            raise TypeError("operation configuration requires a code-owned canonical record type")
        if not self.outputs:
            raise ValueError("registered operation needs a complete output census")
        if tuple(sorted(set(port.port_id for port in self.input_ports))) != tuple(port.port_id for port in self.input_ports):
            raise ValueError("registered input ports must be sorted and unique")
        if tuple(sorted(set(output.output_id for output in self.outputs))) != tuple(output.output_id for output in self.outputs):
            raise ValueError("registered output ports must be sorted and unique")
        for callback in (self.scientific_unit_ids, self.native_effect_slot_ids, self.scientific_root_validator,
                         self.scientific_claim_resolver):
            if callback is not None and not callable(callback):
                raise TypeError("scientific unit and native slot projections must be code-owned callables")
        if type(self.complete_unit_census) is not bool or (self.complete_unit_census and not self.native_effect):
            raise ValueError("a complete acquisition census requires a native operation registration")
        if self.adjudication_output_id is not None:
            from .adjudication import ScientificAdjudicationRecord
            if not any(output.output_id == self.adjudication_output_id and output.payload_schema == ScientificAdjudicationRecord.SCHEMA
                       for output in self.outputs):
                raise ValueError('registered adjudication locator lacks its exact typed output')
        schemas = self.qualified_parent_evidence_schema_ids
        if (type(schemas) is not tuple or len(schemas) > 4 or schemas != tuple(sorted(set(schemas)))
                or any(type(schema) is not str or not schema for schema in schemas)
                or (schemas and not callable(self.qualified_parent_assessor))):
            raise ValueError('qualified-parent companion schemas require a bounded exact installed assessor declaration')
        for schema in schemas:
            validate_schema(schema)
        if (self.qualified_parent_prior_execution_bindings is not None
                and (not callable(self.qualified_parent_prior_execution_bindings)
                     or not callable(self.qualified_parent_prior_execution_scope_validator)
                     or not schemas or not callable(self.qualified_parent_assessor))):
            raise ValueError('prior execution projection requires an installed assessor and exact companion schema declaration')
        if (self.qualified_parent_prior_execution_scope_validator is not None
                and (not callable(self.qualified_parent_prior_execution_scope_validator)
                     or self.qualified_parent_prior_execution_bindings is None)):
            raise ValueError('prior execution scope validator requires its exact installed locator projection')
        for requirements, record_type in (
                (self.publication_requirements, RegisteredPublicationRequirement),
                (self.provenance_requirements, RegisteredProvenanceRequirement)):
            if (type(requirements) is not tuple
                    or any(type(value) is not record_type for value in requirements)
                    or tuple(value.requirement_id for value in requirements)
                    != tuple(sorted({value.requirement_id for value in requirements}))):
                raise ValueError("registered requirements need sorted unique code-owned declarations")


@dataclass(frozen=True, slots=True)
class DecodedRecursiveConfigInput:
    """Strict selected configuration bytes, before whole-census custody projection."""

    node_id: str
    config_id: str
    payload: bytes
    record: CanonicalRecord
    record_type: type[CanonicalRecord]

    @property
    def payload_schema(self) -> str:
        return self.record.SCHEMA


@dataclass(frozen=True, slots=True)
class RecursiveConfigInput:
    node_id: str
    config_id: str
    input_spec: ExternalInputSpec
    payload: bytes
    record: CanonicalRecord
    record_type: type[CanonicalRecord]
    input_parents: tuple[ArtifactLineageParent, ...] = ()

    @property
    def payload_schema(self) -> str:
        return self.record.SCHEMA


def decode_recursive_config_input(operation, registration):
    """Decode the actual record; this does not project an input custody contract."""
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.planning.recursive_authoring import MAX_RECURSIVE_CONFIG_BYTES

    raw = operation.config_payload.encode("utf-8")
    config = decode_canonical_bytes(raw, registration.config_record_type,
                                    maximum_bytes=MAX_RECURSIVE_CONFIG_BYTES)
    if getattr(config, "config_id", operation.config_id) != operation.config_id:
        raise ValueError("operation config ID differs from its exact payload")
    return DecodedRecursiveConfigInput(operation.node_id, operation.config_id, raw,
                                      config, registration.config_record_type)


def _project_config_input(decoded, registration, all_config_records):
    from .plans import derived_development_custody

    if (type(decoded) is not DecodedRecursiveConfigInput
            or type(decoded.record) is not registration.config_record_type
            or decoded.record_type is not registration.config_record_type
            or getattr(decoded.record, "config_id", decoded.config_id) != decoded.config_id
            or not decoded.record.canonical_equals(decoded.payload)):
        raise ValueError("configuration custody substitutes its exact decoded owning record")
    parents = (() if registration.config_input_parents is None else
        registration.config_input_parents(decoded.record, all_config_records))
    if (type(parents) is not tuple or any(type(value) is not ArtifactLineageParent for value in parents)
            or tuple(lineage_parent_sort_key(value) for value in parents) !=
                tuple(sorted({lineage_parent_sort_key(value) for value in parents}))):
        raise ValueError("configuration custody requires sorted exact distinct lineage parents")
    for parent in parents:
        if (type(parent.identity) is not ObjectIdentity
                or type(parent.outcome_access) is not OutcomeAccess
                or type(parent.visibility_ceiling) is not VisibilityCeiling):
            raise TypeError("configuration custody substitutes a parent identity or access contract")
        parent.identity.__post_init__()
    access, visibility = derived_development_custody(registration.outcome_access,
        registration.visibility_ceiling, tuple(value.outcome_access for value in parents),
        tuple(value.visibility_ceiling for value in parents))
    spec = ExternalInputSpec("config", decoded.config_id, decoded.record.fingerprint(), decoded.record.SCHEMA,
        "application/json", len(decoded.payload), visibility, access, None)
    return RecursiveConfigInput(decoded.node_id, decoded.config_id, spec, decoded.payload,
        decoded.record, decoded.record_type, parents)


def project_recursive_config_inputs(config_inputs, registrations_for_node):
    """Project one complete decoded census, sharing its immutable records tuple."""
    if (type(config_inputs) is not tuple or any(type(row) is not DecodedRecursiveConfigInput for row in config_inputs)
            or len({row.node_id for row in config_inputs}) != len(config_inputs)
            or {row.node_id for row in config_inputs} != set(registrations_for_node)):
        raise ValueError("configuration custody requires its exact complete decoded node census")
    records = tuple(sorted(((row.node_id, row.record) for row in config_inputs), key=lambda value: value[0]))
    return tuple(_project_config_input(row, registrations_for_node[row.node_id], records) for row in config_inputs)


def configuration_input_id(config_id):
    from hashlib import sha256
    return "compiler.configuration." + sha256(config_id.encode()).hexdigest()


def configuration_edge_id(node_id):
    return "compiler.configuration." + node_id


def configuration_graph_bindings(config_inputs):
    """Freeze the compiler-owned config operands using ordinary graph records."""
    from .candidate_compiler import CandidateGraphEdge, CandidateGraphExternalInput, ContentIdentityPolicy
    from .plans import ScientificInputRole

    if type(config_inputs) is not tuple or any(type(row) is not RecursiveConfigInput for row in config_inputs):
        raise TypeError("configuration graph requires finalized exact input custody")
    externals, seen, edges = {}, {}, []
    for row in config_inputs:
        spec = row.input_spec
        previous = seen.setdefault(row.config_id, row)
        if (previous.input_spec, previous.payload, previous.input_parents) != (spec, row.payload, row.input_parents):
            raise ValueError("shared configuration changes its exact bytes or parent custody")
        input_id = configuration_input_id(row.config_id)
        external = CandidateGraphExternalInput(input_id, ScientificInputRole.CONFIGURATION, row.config_id,
            ContentIdentityPolicy.EXACT_SHA256, spec.expected_content_sha256, spec.expected_payload_schema,
            spec.expected_media_type, spec.expected_size_bytes, spec.expected_outcome_access,
            spec.expected_visibility_ceiling)
        if externals.setdefault(input_id, external) != external:
            raise ValueError("configuration graph aliases distinct actual input contracts")
        edges.append(CandidateGraphEdge(configuration_edge_id(row.node_id), None, None, input_id,
            row.node_id, "config", ScientificInputRole.CONFIGURATION, row.config_id,
            external.payload_schema, external.media_type, external.maximum_size_bytes,
            external.outcome_access, external.visibility_ceiling, BarrierKind.NONE))
    return tuple(sorted(externals.values(), key=lambda value: value.input_id)), tuple(sorted(edges, key=lambda value: value.edge_id))


def validate_recursive_config_input(*, operation, registration, config_input, all_config_records=None):
    """Authenticate a decoded row against the operation's immutable binding.

    This pure check reuses already decoded records and performs no custody reads.
    Publication/scientific validators cannot accept a caller-substituted row.
    """
    row = config_input
    raw = operation.config_payload.encode("utf-8")
    if (type(row) is not RecursiveConfigInput
            or row.node_id != operation.node_id or row.config_id != operation.config_id
            or row.record_type is not registration.config_record_type
            or type(row.record) is not registration.config_record_type
            or getattr(row.record, "config_id", operation.config_id) != operation.config_id
            or row.payload != raw or not row.record.canonical_equals(raw)):
        raise ValueError("selected operation changes its frozen configuration record or bytes")
    if all_config_records is None:
        if registration.config_input_parents is not None:
            raise ValueError("configuration custody needs its complete original record census")
        all_config_records = ((row.node_id, row.record),)
    from bisect import bisect_left
    if type(all_config_records) is not tuple:
        raise ValueError("configuration custody needs its immutable complete record census")
    position = bisect_left(all_config_records, row.node_id, key=lambda value: value[0])
    if (position == len(all_config_records) or all_config_records[position] != (row.node_id, row.record)
            or position + 1 < len(all_config_records) and all_config_records[position + 1][0] == row.node_id):
        raise ValueError("configuration custody omits or substitutes its actual selected record")
    expected = _project_config_input(DecodedRecursiveConfigInput(row.node_id, row.config_id, raw,
        row.record, row.record_type), registration, all_config_records)
    if row != expected:
        raise ValueError("selected operation changes its frozen configuration input binding")


def validate_recursive_scientific_roots(*, root, config_inputs, registrations_for_node,
                               requirements, connections, links, qualifications,
                               known_design_inputs, external_inputs=(), declared_config_inputs=()):
    """Join all strictly decoded design metadata before scientific projection."""
    config_inputs, requirements, connections = tuple(config_inputs), tuple(requirements), tuple(connections)
    links, external_inputs = tuple(links), tuple(external_inputs)
    qualifications, known_design_inputs = tuple(qualifications), tuple(known_design_inputs)
    units_by_node, unit_censuses = {}, {}
    for row in config_inputs:
        registration = registrations_for_node[row.node_id]
        units = (() if registration.scientific_unit_ids is None else
                 _registered_identity_projection(registration.scientific_unit_ids, row.record,
                                                 field_name="scientific_unit_ids"))
        units_by_node[row.node_id] = units
        unit_censuses.setdefault(registration.selection.selection_id, set()).update(units)
    selected_units = {selection: tuple(sorted(units)) for selection, units in unit_censuses.items()}
    batch = RecursiveScientificRootPreparationContext(root, config_inputs, requirements, connections,
        links, external_inputs, qualifications, known_design_inputs, selected_units)
    preparations = {}
    for row in config_inputs:
        preparer = registrations_for_node[row.node_id].scientific_root_preparer
        if preparer is not None and id(preparer) not in preparations:
            prepared = preparer(batch)
            if prepared is None:
                raise ValueError("registered scientific root preparer must return its invocation-local preparation")
            preparations[id(preparer)] = (preparer, prepared)
    contexts = {}
    for row in config_inputs:
        registration = registrations_for_node[row.node_id]
        context = RecursiveScientificRootContext(root, row.node_id, registration.stage,
            registration.outcome_access, registration.visibility_ceiling, units_by_node[row.node_id],
            batch.selected_unit_ids_by_selection[registration.selection.selection_id],
            registration.complete_unit_census, requirements, connections,
            batch.qualifications, batch.known_design_inputs, config_inputs, links, external_inputs,
            None if registration.scientific_root_preparer is None else preparations[id(registration.scientific_root_preparer)][1],
            tuple(declared_config_inputs))
        contexts[row.node_id] = context
        if (registration.scientific_root_validator is not None
            and registration.scientific_root_validator(row.record, context) is not None):
            raise ValueError("registered scientific root validator must raise on refusal and return None on success")
    claims = (getattr(root, "claims", ()) if not hasattr(root, "experiment")
              else (() if root.experiment is None else root.experiment.claims))
    config_by_node = {row.node_id: row.record for row in config_inputs}
    for connection in connections:
        requirement = next(value for value in requirements if value.requirement_id == connection.requirement_id)
        node = requirement.assessment_operation_id
        registration = registrations_for_node[node]
        if registration.scientific_claim_resolver is None:
            matches = tuple(claim for claim in claims if claim.claim_id == connection.claim_id)
            if len(matches) != 1:
                raise ValueError("selected scientific connection does not resolve to one declared root claim")
            resolved = matches[0]
        else:
            resolved = registration.scientific_claim_resolver(config_by_node[node], contexts[node], requirement, connection)
        if (type(resolved) is not ClaimSpec
            or sum(claim.canonical_bytes() == resolved.canonical_bytes() for claim in claims) != 1):
            raise ValueError("registered scientific claim resolver must return one exact typed declared root claim")
        scope = requirement.scope
        system = root.system
        system_id = system.object_id if isinstance(system, ObjectIdentity) else system.system_id
        if scope is None or scope.world_id != resolved.world_id or scope.system_id != system_id:
            raise ValueError("selected scientific claim differs from its requirement world or system scope")


@dataclass(frozen=True, slots=True)
class RecursiveCompilation:
    draft: RecursiveStudyDraft
    template: StudyTemplate
    run_plan: CanonicalRecord | None
    execution_plan: ProtocolExecutionPlan | None
    registry: CapabilityRegistry
    operations: tuple[RecursiveOperationSpec, ...]
    config_inputs: tuple[RecursiveConfigInput, ...]
    output_codecs: Mapping[str, type[CanonicalRecord]]
    requirement_bindings: tuple[tuple[str, str, str], ...]
    selected_scientific_projection: CanonicalRecord
    proof: CanonicalRecord | None
    candidate_context: CandidateCompilationContext | None = None
    candidate_draft: StudyDraft | None = None
    candidate_report: CandidateCompilationReport | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_codecs", MappingProxyType(dict(self.output_codecs)))


def project_recursive_assessments(*, draft, registrations, outputs, qualifications=(), known_design_inputs=()):
    """Project authenticated typed outputs without recomputing scientific results.

    The custody caller authenticates every supplied output receipt first. This
    owner checks scientific requirement identities and actual evidence bytes.
    """
    from empirical_lawhood.kernel.recursive_requirements import RequirementSupplyAssessment

    selected = set(draft.selected_operation_ids)
    links = tuple(link for link in draft.links if link.consumer_node_id in selected)
    requirements, connections, _ = _close_requirements(draft, selected, links)
    by_selection = {registration.selection.selection_id: registration for registration in registrations}
    operations = {operation.node_id: operation for operation in draft.operations if operation.node_id in selected}
    root = draft.development_study if draft.development_study is not None else draft.prospective_draft
    registrations_for_node = {node: by_selection[operation.selection.selection_id]
                              for node, operation in operations.items()}
    config_inputs = project_recursive_config_inputs(tuple(
        decode_recursive_config_input(operation, registrations_for_node[node])
        for node, operation in operations.items()), registrations_for_node)
    external_ids = {link.external_input_id for link in links if link.external_input_id is not None}
    validate_recursive_scientific_roots(root=root, config_inputs=config_inputs,
        registrations_for_node=registrations_for_node, requirements=requirements,
        connections=connections, links=links, qualifications=qualifications,
        known_design_inputs=known_design_inputs,
        external_inputs=tuple(value for value in draft.external_inputs if value.input_id in external_ids),
        declared_config_inputs=(() if len(operations) == len(draft.operations) else project_recursive_config_inputs(tuple(
            decode_recursive_config_input(operation, by_selection[operation.selection.selection_id])
            for operation in draft.operations if operation.selection.selection_id in by_selection),
            {operation.node_id: by_selection[operation.selection.selection_id]
                for operation in draft.operations if operation.selection.selection_id in by_selection})))
    source_fingerprints = {(value.SCHEMA, value.VERSION, value.fingerprint()) for value in outputs.values()}
    source_fingerprints.update((parent.record.object_schema, parent.record.object_version,
                               parent.record.object_fingerprint)
                              for manifest in draft.contribution_parents for parent in manifest.products)
    values = []
    for requirement in requirements:
        chosen = tuple(connection for connection in connections if connection.requirement_id == requirement.requirement_id)
        for connection in chosen:
            node = requirement.assessment_operation_id
            operation = operations[node]
            registration = by_selection[operation.selection.selection_id]
            assessed = tuple((port, record) for (owner, port), record in outputs.items() if owner == node)
            if not assessed:
                continue  # Operationally missing assessment remains in the recovery census.
            projected = []
            for _, record in assessed:
                if registration.assessment_projector is not None:
                    projected.extend(registration.assessment_projector(record, requirement, connection))
                elif isinstance(record, RequirementSupplyAssessment):
                    projected.append(record)
            if not projected:
                raise ValueError('declared assessor output lacks its registered scientific assessment projection')
            for assessment in projected:
                if (type(assessment) is not RequirementSupplyAssessment
                    or assessment.requirement != ObjectIdentity.from_record(requirement.requirement_id, requirement)
                    or assessment.connection != ObjectIdentity.from_record(connection.connection_id, connection)):
                    raise ValueError('retained scientific assessment changes its declared requirement or connection')
                if any((identity.object_schema, identity.object_version, identity.object_fingerprint)
                       not in source_fingerprints for identity in assessment.evidence):
                    raise ValueError('retained scientific assessment cites unavailable producing evidence')
                values.append(assessment)
    values.sort(key=lambda value: value.assessment_id)
    if len({value.assessment_id for value in values}) != len(values):
        raise ValueError('scientific assessment projection repeats an assessment identity')
    return tuple(values)


def _require_receipt_output_order(outputs: tuple[OutputTemplate, ...]) -> None:
    """Keep the existing logical and materialization receipt orders compatible.

    The artifact owner appends a period and 24 hexadecimal digest characters to
    each logical ID. Every task uses one common logical prefix. Refuse output
    names whose order can change when those unknown digest suffixes are added.
    The historical receipt schema and all accepted output identifiers remain
    unchanged.
    """
    for left, right in zip(outputs, outputs[1:]):
        if left.output_id + '.' + 'f' * 24 >= right.output_id + '.' + '0' * 24:
            raise ValueError('selected output identifiers cannot guarantee the existing receipt materialization order')


def _registered_identity_projection(projector, config, *, field_name):
    """Read an exact code-owned projection without interpreting JSON predicates."""
    identities = projector(config)
    if (not isinstance(identities, tuple)
            or any(not isinstance(identity, str) for identity in identities)
            or tuple(sorted(set(identities))) != identities):
        raise ValueError(f"registered {field_name} projection must be sorted and unique")
    for identity in identities:
        validate_stable_id(identity, field_name=field_name)
    return identities


def _derive_recursive_selection_and_bindings(draft: RecursiveStudyDraft):
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
    selected = set(draft.selected_operation_ids)
    operations = tuple(operation for operation in draft.operations if operation.node_id in selected)
    links = tuple(link for link in draft.links if link.consumer_node_id in selected)
    if any(link.consumer_input_id == "config" or link.scientific_role == "CONFIGURATION"
            or link.edge_id.startswith("compiler.configuration.") for link in links):
        raise ValueError("configuration graph links belong to the compiler's exact implicit inputs")
    external_ids = {link.external_input_id for link in links if link.external_input_id is not None}
    external_inputs = tuple(value for value in draft.external_inputs if value.input_id in external_ids)
    requirements, connections, bindings = _close_requirements(draft, selected, links)
    root = draft.development_study if draft.development_study is not None else draft.prospective_draft
    if root is None:
        raise ValueError("selected scientific projection lacks its immutable root")
    root_id = root.study_id if draft.development_study is not None else root.draft_id
    projection = RecursiveScientificSelection(
        selection_id=f"selection.{draft.draft_id}", requirements=requirements, connections=connections,
        operations=operations, external_inputs=external_inputs, links=links,
        contribution_parents=tuple(ObjectIdentity.from_record(parent.contribution_id, parent) for parent in draft.contribution_parents),
        scientific_root=ObjectIdentity.from_record(root_id, root))
    return projection, bindings


def derive_recursive_scientific_selection(draft: RecursiveStudyDraft):
    """Derive the immutable selected scientific graph without execution settings."""
    return _derive_recursive_selection_and_bindings(draft)[0]


def compile_recursive_wave(*, draft: RecursiveStudyDraft,
                           registrations: tuple[RecursiveOperationRegistration, ...],
                           registry: CapabilityRegistry, implementation_commit: str,
                           run_plan_id: str | None = None, qualifications=(),
                           known_design_inputs=(), output_codecs: Mapping[str, type[CanonicalRecord]] | None = None,
                           authoring_materialization=None,
                           implementation_sha256: str | None = None) -> RecursiveCompilation:
    """Close only explicitly selected operations, using registered typed contracts."""
    from dataclasses import replace
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from .candidate_compiler import (
        AuthoringMaterializationIdentity, CandidateGraphEdge, CandidateGraphExternalInput,
        CandidateGraphNode, CandidateScientificGraph, ContentIdentityPolicy,
        ObligationCoverage, ObligationCoverageBinding, compile_draft_candidate,
    )
    from .capabilities import CapabilityConfigRef, CapabilityRequirement
    from .compiler import _project_output_custody, _scientific_external_inputs_for_step, _scientific_inputs_for_step, lower_run_plan
    if implementation_sha256 is not None and (
        len(implementation_sha256) != 64
        or any(character not in '0123456789abcdef' for character in implementation_sha256)
    ):
        raise ValueError('recursive compilation requires an exact implementation SHA-256')
    from .plans import ArtifactOutputSpec, DevelopmentRunPlan, ProtocolStepTemplate, ProtocolTemplate, RunPlanStep, ScientificInputRole
    from .scientific_graph_preservation import prove_development_graph_parity

    if not isinstance(draft, RecursiveStudyDraft):
        raise TypeError("recursive compiler requires its typed authored draft")
    selected = set(draft.selected_operation_ids)
    if not selected:
        raise ValueError("selected wave is empty; the partial programme remains authorable")
    if draft.unresolved_decisions:
        raise ValueError("selected wave retains unresolved scientific decisions")
    if draft.development_study is None and draft.prospective_draft is None:
        raise ValueError("selected wave lacks a development or prospective scientific root")
    operations = tuple(operation for operation in draft.operations if operation.node_id in selected)
    registrations_by_id = {registration.selection.selection_id: registration for registration in registrations}
    if len(registrations_by_id) != len(registrations):
        raise ValueError("operation registration selections must be unique")
    links = tuple(link for link in draft.links if link.consumer_node_id in selected)
    external_ids = {link.external_input_id for link in links if link.external_input_id is not None}
    external_inputs = tuple(value for value in draft.external_inputs if value.input_id in external_ids)
    external_by_id = {value.input_id: value for value in external_inputs}
    if set(external_by_id) != external_ids:
        raise ValueError("selected wave names an unavailable external input")
    dependencies = {operation.node_id: set() for operation in operations}
    links_by_consumer = {operation.node_id: [] for operation in operations}
    for link in links:
        links_by_consumer[link.consumer_node_id].append(link)
        if link.producer_node_id is not None:
            if link.producer_node_id not in selected:
                raise ValueError("selected wave requires an unselected supplier operation")
            dependencies[link.consumer_node_id].add(link.producer_node_id)
    links_by_consumer = {node: tuple(incoming) for node, incoming in links_by_consumer.items()}
    levels: dict[str, int] = {}
    while len(levels) < len(operations):
        ready = sorted(node for node, parents in dependencies.items() if node not in levels and parents.issubset(levels))
        if not ready:
            raise ValueError("selected scientific wave contains a dependency cycle")
        for node in ready:
            levels[node] = 1 + max((levels[parent] for parent in dependencies[node]), default=0)
            if draft.maximum_depth is not None and levels[node] > draft.maximum_depth:
                raise ValueError("selected scientific wave exceeds its depth bound")
    projection, requirement_bindings = _derive_recursive_selection_and_bindings(draft)
    requirements, connections = projection.requirements, projection.connections
    root = draft.development_study if draft.development_study is not None else draft.prospective_draft
    development = draft.development_study is not None
    development_pair = draft.development_study.access_pair if development else None
    run_id = run_plan_id or f"recursive.{draft.draft_id}"
    validate_stable_id(run_id, field_name="run_plan_id")
    template_id = f"recursive.{draft.draft_id}"
    steps = []
    configs = []
    registrations_for_node = {}
    native_slots = set()
    acquisition_censuses = {}
    for operation in operations:
        registration = registrations_by_id.get(operation.selection.selection_id)
        if registration is None or registration.selection != operation.selection:
            raise ValueError("selected operation lacks its exact code-owned registration")
        _require_receipt_output_order(registration.outputs)
        registrations_for_node[operation.node_id] = registration
        manifest = registry.resolve(operation.selection.capability_key, operation.selection.capability_version)
        if manifest.implementation_sha256 != operation.selection.implementation_sha256:
            raise ValueError("selected operation implementation differs from the locked registry")
        if manifest.config_schema != registration.config_record_type.SCHEMA:
            raise ValueError("registered configuration schema differs from its manifest")
        from .stage_contracts import validate_operation_stage_kind
        validate_operation_stage_kind(registration.stage, manifest.kind,
            outcome_access=registration.outcome_access, visibility_ceiling=registration.visibility_ceiling)
        if not registration.resource_ceiling.contains(operation.resource_budget):
            raise ValueError("selected operation exceeds its registered resource ceiling")
        if registration.native_effect and operation.maximum_attempts != 1:
            raise ValueError("native operations require one attempt and explicit receipt recovery")
        if development:
            if (registration.outcome_access, registration.visibility_ceiling) != development_pair:
                raise ValueError("development registration changes its exact exposed scientific access")
            if development_pair[0] is OutcomeAccess.EVALUATION_REVEALED and (
                    registration.native_effect or registration.barrier is not BarrierKind.NONE):
                raise ValueError("revealed follow-up permits only pure operations without authority barriers")
        config_input = decode_recursive_config_input(operation, registration)
        config = config_input.record
        if registration.native_effect:
            if registration.scientific_unit_ids is None or registration.native_effect_slot_ids is None:
                raise ValueError("native operation lacks code-owned scientific unit and effect slot projections")
            if not development and registration.scientific_root_validator is None:
                raise ValueError("prospective native operation requires a registered frozen stage/source unit validator")
        unit_ids = ()
        if registration.scientific_unit_ids is not None:
            unit_ids = _registered_identity_projection(registration.scientific_unit_ids, config,
                                                       field_name="scientific_unit_ids")
            if not development and unit_ids and registration.scientific_root_validator is None:
                raise ValueError("prospective unit-bound operation requires a registered frozen stage/source unit validator")
            if development and not set(unit_ids).issubset(draft.development_study.assigned_unit_ids):
                raise ValueError("operation scientific units differ from the selected study root")
            if registration.complete_unit_census:
                acquisition_censuses.setdefault(registration.selection.selection_id, set()).update(unit_ids)
        if registration.native_effect:
            slots = _registered_identity_projection(registration.native_effect_slot_ids, config,
                                                    field_name="native_effect_slot_ids")
            if not slots or native_slots.intersection(slots):
                raise ValueError("selected native acquisition repeats or omits its declared effect slot")
            native_slots.update(slots)
        if registration.scientific_operand_sha256s is not None:
            hashes = registration.scientific_operand_sha256s(config)
            if not isinstance(hashes, tuple) or tuple(sorted(set(hashes))) != hashes:
                raise ValueError("registered scientific operand projection must be sorted and unique")
            allowed_hashes = ({operand.object_fingerprint for operand in draft.development_study.scientific_operands}
                             if development else
                             {item.object_identity.object_fingerprint for item in draft.prospective_draft.design_inputs})
            if not set(hashes).issubset(allowed_hashes):
                raise ValueError("operation scientific operands differ from the selected study root")
        config_ref = CapabilityConfigRef(operation.config_id, config.SCHEMA, manifest.config_schema_sha256,
                                         config.fingerprint(), operation.config_id)
        configs.append(config_input)
        node_links = links_by_consumer[operation.node_id]
        seen = set()
        for port in registration.input_ports:
            port_links = tuple(link for link in node_links if port.matches(link.consumer_input_id))
            if (len(port_links) < port.minimum_count
                    or (port.maximum_count is not None and len(port_links) > port.maximum_count)):
                raise ValueError(f"selected operation {operation.node_id} has an incomplete port census: {port.port_id}")
            seen.update(link.edge_id for link in port_links)
        if seen != {link.edge_id for link in node_links}:
            raise ValueError("selected operation contains an undeclared scientific input port")
        steps.append(ProtocolStepTemplate(operation.node_id, registration.stage,
                     operation.selection.capability_key, operation.selection.capability_version, config_ref,
                     tuple(sorted(dependencies[operation.node_id])), registration.outputs,
                     registration.required_permissions, registration.outcome_access, registration.visibility_ceiling,
                     operation.resource_budget, operation.resource_lock_ids, registration.barrier,
                     operation.maximum_attempts, operation.obligation_ids))
    if development:
        for census in acquisition_censuses.values():
            if census != set(draft.development_study.assigned_unit_ids):
                raise ValueError("selected native acquisition has an incomplete assigned unit census")
    configs = list(project_recursive_config_inputs(tuple(configs), registrations_for_node))
    validate_recursive_scientific_roots(root=root, config_inputs=tuple(configs),
        registrations_for_node=registrations_for_node, requirements=requirements,
        connections=connections, links=links, qualifications=qualifications,
        known_design_inputs=known_design_inputs, external_inputs=external_inputs,
        declared_config_inputs=(() if len(operations) == len(draft.operations) else project_recursive_config_inputs(tuple(
            decode_recursive_config_input(operation, registrations_by_id[operation.selection.selection_id])
            for operation in draft.operations if operation.selection.selection_id in registrations_by_id),
            {operation.node_id: registrations_by_id[operation.selection.selection_id]
                for operation in draft.operations if operation.selection.selection_id in registrations_by_id})))
    # One exact external configuration artifact may be reused, but never under changed bytes.
    config_by_id = {}
    for row in configs:
        previous = config_by_id.setdefault(row.config_id, row)
        if (previous.payload, previous.payload_schema, previous.input_spec, previous.input_parents) != (
                row.payload, row.payload_schema, row.input_spec, row.input_parents):
            raise ValueError("configuration identity is reused with different bytes, schema or custody")
    configuration_externals, configuration_edges = configuration_graph_bindings(tuple(configs))
    graph_externals = tuple(sorted((*configuration_externals, *(CandidateGraphExternalInput(
        value.input_id, ScientificInputRole(value.scientific_role), value.logical_artifact_id,
        ContentIdentityPolicy.PARENT_RECEIPT_SUBSTITUTION if value.parent_substitution else ContentIdentityPolicy.EXACT_SHA256,
        value.expected_content_sha256, value.payload_schema, value.media_type, value.maximum_size_bytes,
        value.outcome_access, value.visibility_ceiling) for value in external_inputs)), key=lambda value: value.input_id))
    steps_by_id = {step.step_id: step for step in steps}
    edges = list(configuration_edges)
    for link in links:
        registration = registrations_for_node[link.consumer_node_id]
        port_matches = tuple(port for port in registration.input_ports if port.matches(link.consumer_input_id))
        if len(port_matches) != 1:
            raise ValueError("scientific input port matches ambiguous registered contracts")
        port = port_matches[0]
        if not is_canonical_json_media_type(port.media_type) and resolve_storage_codec(registration.storage_codecs,
                payload_schema=port.payload_schema, media_type=port.media_type) is None:
            raise ValueError("registered input port lacks its exact registered storage codec")
        if link.producer_node_id is not None:
            supplier = registrations_for_node[link.producer_node_id]
            output = next((output for output in supplier.outputs if output.output_id == link.producer_output_id), None)
            if output is None:
                raise ValueError("selected edge names an unavailable supplier output")
            schema, media = output.payload_schema, output.media_type
            declared_inputs = tuple(kind for kind in registration.input_record_types if kind.SCHEMA == schema)
            if declared_inputs:
                codec = (output_codecs or {}).get(schema)
                if (output.profile is not ArtifactProfile.CANONICAL_JSON or codec is None
                        or codec not in declared_inputs):
                    raise ValueError('supplier record revision is outside its selected declared consumer contract')
            logical_id = f"scientific.{link.producer_node_id}.{link.producer_output_id}"
            access, visibility = supplier.outcome_access, supplier.visibility_ceiling
            bound = steps_by_id[link.producer_node_id].resource_budget.output_bytes
            storage = resolve_storage_codec(supplier.storage_codecs,
                payload_schema=schema, profile=output.profile, media_type=media)
            if storage is not None and storage.maximum_bytes is not None:
                bound = storage.maximum_bytes if bound is None else min(bound, storage.maximum_bytes)
        else:
            external = external_by_id[link.external_input_id]
            schema, media, logical_id = external.payload_schema, external.media_type, external.logical_artifact_id
            access, visibility, bound = external.outcome_access, external.visibility_ceiling, external.maximum_size_bytes
        if (schema != port.payload_schema or media != port.media_type
                or (port.maximum_size_bytes is not None and
                    (bound is None or bound > port.maximum_size_bytes))):
            raise ValueError(f"supplier product is incompatible with registered port {link.consumer_node_id}.{link.consumer_input_id}: "
                             f"schema={schema}, media={media}, bound={bound}; contract={port}")
        edges.append(CandidateGraphEdge(link.edge_id, link.producer_node_id, link.producer_output_id,
                     link.external_input_id, link.consumer_node_id, link.consumer_input_id,
                     ScientificInputRole(link.scientific_role), logical_id, schema, media, bound,
                     access, visibility, registration.barrier))
    # A declaration supplies the minimum custody of its own operation. Internal
    # edges must also retain the actual transitive custody of its inputs; using
    # only the supplier declaration would drop exposed TRAIN ancestry after a
    # sealed forecast. Derive this before freezing the scientific graph so its
    # exact edges and the executable projection use the same custody owner.
    edges_by_consumer = {node: [] for node in levels}
    for edge in edges:
        edges_by_consumer[edge.consumer_node_id].append(edge)
    inherited_edges = {}
    output_custody = {}
    for node in sorted(levels, key=lambda key: (levels[key], key)):
        incoming = []
        for edge in edges_by_consumer[node]:
            if edge.producer_node_id is not None:
                access, visibility = output_custody[(edge.producer_node_id, edge.producer_output_id)]
                edge = replace(edge, outcome_access=access, visibility_ceiling=visibility)
            incoming.append(edge)
            inherited_edges[edge.edge_id] = edge
        step = steps_by_id[node]
        custody = _project_output_custody(step,
            parent_visibility_ceilings=tuple(edge.visibility_ceiling for edge in incoming),
            parent_outcome_accesses=tuple(edge.outcome_access for edge in incoming),
            scientific_graph=True)
        for output, selected_custody in zip(step.outputs, custody, strict=True):
            output_custody[(node, output.output_id)] = selected_custody
    edges = sorted((inherited_edges[edge.edge_id] for edge in edges), key=lambda value: value.edge_id)
    graph = CandidateScientificGraph(f"graph.{draft.draft_id}", graph_externals,
        tuple(CandidateGraphNode(step.step_id, step.stage, step.capability_key, step.capability_version,
              registrations_for_node[step.step_id].selection.implementation_sha256, step.fingerprint(),
              step.obligation_ids, step.requested_outcome_access, step.visibility_ceiling, step.resource_budget) for step in steps),
        tuple(edges))
    # Index the final inherited edges, not the declaration-labelled objects
    # used while propagating custody above. Preserve the frozen graph order.
    incoming_edges_by_consumer = {node: [] for node in levels}
    for edge in graph.edges:
        incoming_edges_by_consumer[edge.consumer_node_id].append(edge)
    incoming_edges_by_consumer = {node: tuple(incoming)
        for node, incoming in incoming_edges_by_consumer.items()}
    bindings = []
    owned = set()
    for step in steps:
        for obligation in step.obligation_ids:
            if obligation in owned:
                raise ValueError("selected obligation requires one explicit proof owner")
            owned.add(obligation)
            bindings.append(ObligationCoverageBinding(obligation, step.step_id, step.outputs[0].output_id,
                            tuple(edge.edge_id for edge in incoming_edges_by_consumer[step.step_id])))
    coverage = ObligationCoverage(f"coverage.{draft.draft_id}", tuple(sorted(bindings, key=lambda value: value.obligation_id)))
    protocol = ProtocolTemplate(template_id, "1.0.0", tuple(steps), False, False, True)
    template = StudyTemplate(template_id, "1.0.0", protocol, graph, coverage)
    codecs = dict(output_codecs or {})
    for step in steps:
        for output in step.outputs:
            if output.profile is not ArtifactProfile.CANONICAL_JSON:
                owner = registrations_for_node[step.step_id]
                if resolve_storage_codec(owner.storage_codecs, payload_schema=output.payload_schema,
                        profile=output.profile, media_type=output.media_type) is not None:
                    continue
                raise ValueError("registered output lacks its exact canonical record codec or registered storage codec")
            elif output_codecs is not None:
                codec = codecs.get(output.payload_schema)
                if codec is None or codec.SCHEMA != output.payload_schema:
                    raise ValueError("registered output lacks its exact canonical record codec")
    context = candidate_draft = report = run_plan = execution_plan = proof = None
    if development:
        study = draft.development_study
        if study.world_id not in draft.campaign.world_ids or study.system.object_id not in draft.campaign.system_ids:
            raise ValueError("development scientific root differs from its campaign scope")
        if not {claim.claim_id for claim in study.claims}.issubset(draft.campaign.target_claim_ids):
            raise ValueError("development campaign omits selected scientific claims")
        compiled = {}
        graph_external_by_id = {value.input_id: value for value in graph.external_inputs}
        config_by_node = {row.node_id: row for row in configs}
        for node in sorted(levels, key=lambda key: (levels[key], key)):
            step = steps_by_id[node]
            manifest = registry.resolve(step.capability_key, step.capability_version)
            incoming = incoming_edges_by_consumer[node]
            requirement = CapabilityRequirement(step.capability_key, step.capability_version, manifest.kind, step.config,
                          tuple(sorted({step.config.config_schema, *(edge.payload_schema for edge in incoming)})),
                          tuple(sorted({output.payload_schema for output in step.outputs})), step.required_permissions,
                          EvidenceCeiling.NON_PROMOTABLE, step.requested_outcome_access, step.resource_budget)
            registry.require(requirement)
            parents = tuple(sorted((edge.visibility_ceiling for edge in incoming), key=lambda value: value.value))
            outputs = tuple(ArtifactOutputSpec(f"{node}.{output.output_id}", f"artifact.{run_id}.{node}.{output.output_id}",
                        f"runs/{run_id}/outputs/{node}/{output.output_id}{output.filename_suffix}",
                        output.payload_schema, output.profile, output.media_type, output_custody[(node, output.output_id)][1],
                        parents, output_custody[(node, output.output_id)][0]) for output in step.outputs)
            external_specs = tuple(sorted((config_by_node[node].input_spec,
                *_scientific_external_inputs_for_step(graph, incoming_edges=incoming, external_by_id=graph_external_by_id)), key=lambda value: value.input_id))
            compiled[node] = RunPlanStep(node, step.stage, requirement, step.dependency_step_ids, external_specs, outputs,
                step.resource_lock_ids, step.barrier, step.maximum_attempts, step.obligation_ids,
                scientific_inputs=_scientific_inputs_for_step(incoming_edges=incoming, external_by_id=graph_external_by_id, compiled_steps=compiled))
        run_plan = DevelopmentRunPlan(run_id, ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign),
                   ObjectIdentity.from_record(study.study_id, study), ObjectIdentity.from_record(draft.draft_id, draft),
                   ObjectIdentity.from_record(projection.selection_id, projection), ObjectIdentity.from_record(template_id, template),
                   registry.fingerprint(), implementation_commit, tuple(compiled[node] for node in sorted(compiled)))
        execution_plan = lower_run_plan(run_plan, registry)
        from .input_access import derive_original_parent_input_contracts, validate_planned_input_access
        original_contracts = derive_original_parent_input_contracts(execution_plan,
            config_inputs=tuple(configs), registrations_for_node=registrations_for_node)
        validate_planned_input_access(execution_plan, original_parent_input_contracts=original_contracts)
        proof = prove_development_graph_parity(draft=draft, selection=projection, template=template,
                 run_plan=run_plan, execution_plan=execution_plan, registry=registry)
    else:
        candidate_draft = replace(draft.prospective_draft, dag_template_key=template_id,
             capability_selections=tuple(sorted({operation.selection for operation in operations}, key=lambda value: value.selection_id)))
        projection = replace(projection, scientific_root=ObjectIdentity.from_record(candidate_draft.draft_id, candidate_draft))
        context = CandidateCompilationContext(f"context.{draft.draft_id}", registry, (template,), tuple(qualifications),
                  tuple(known_design_inputs), implementation_sha256 or registry.fingerprint())
        materialization = authoring_materialization or AuthoringMaterializationIdentity("application/json",
                          candidate_draft.canonical_size_bytes(), candidate_draft.fingerprint())
        report = compile_draft_candidate(draft=candidate_draft, authoring_materialization=materialization, context=context)
        if report.candidate is not None and report.candidate.scientific_graph != template.graph:
            raise ValueError('prospective source normalization changes the authored scientific graph; bind its exact qualified logical source before freeze')
    return RecursiveCompilation(draft, template, run_plan, execution_plan, registry, operations, tuple(configs), codecs,
                                requirement_bindings, projection, proof, context, candidate_draft, report)


def _close_requirements(draft, selected, links):
    requirements = tuple(value for value in draft.requirements if value.consumer_operation_id in selected)
    validate_selected_requirement_graph(requirements=requirements, suppliers=draft.suppliers,
                                        maximum_depth=draft.maximum_depth)
    by_requirement = {value.requirement_id: value for value in requirements}
    all_requirements = {value.requirement_id: value for value in draft.requirements}
    all_connections = {value.connection_id: value for value in draft.connections}
    connections = []
    bindings = []
    for requirement in requirements:
        if requirement.scope is None or requirement.assessment_operation_id is None:
            raise ValueError("selected requirement lacks its scientific scope or assessment")
        if requirement.assessment_operation_id not in selected:
            raise ValueError("selected requirement assessment is not selected")
        if not set(requirement.further_requirement_ids).issubset(by_requirement):
            raise ValueError("selected requirement has unresolved further prerequisites")
        matches = tuple(connection for connection in draft.connections if connection.requirement_id == requirement.requirement_id)
        if not matches:
            if not requirement.background_assumption_ids:
                raise ValueError("selected requirement has neither a supplier nor declared fixed background")
            bindings.append((requirement.requirement_id, requirement.consumer_operation_id, requirement.assessment_operation_id))
            continue
        chosen = tuple(connection for connection in matches if connection.supplier_operation_id in selected
                       or (connection.external_input_id is not None and any(link.external_input_id == connection.external_input_id for link in links)))
        if len(chosen) != 1:
            raise ValueError("selected requirement needs exactly one chosen supplier connection")
        connection = chosen[0]
        if connection.evidence_role not in requirement.permitted_roles or connection.assessment_operation_id != requirement.assessment_operation_id:
            raise ValueError("selected connection exceeds the declared scientific role or assessment")
        matching_links = tuple(link for link in links if link.connection_id == connection.connection_id)
        if len(matching_links) != 1:
            raise ValueError("selected connection needs its exact scientific input edge")
        link = matching_links[0]
        if (link.requirement_id != requirement.requirement_id or link.consumer_node_id != requirement.consumer_operation_id
            or link.producer_node_id != connection.supplier_operation_id or link.producer_output_id != connection.supplier_output_id
            or link.consumer_input_id != connection.consumer_input_id):
            raise ValueError("selected connection differs from its actual supplier-consumer edge")
        if connection.external_input_id is not None:
            if link.external_input_id != connection.external_input_id:
                raise ValueError("external assessed connection changes its scientific input")
            parent = next((parent for parent in draft.contribution_parents
                           if ObjectIdentity.from_record(parent.contribution_id, parent) == connection.supplier_contribution), None)
            if parent is None:
                raise ValueError("external assessed connection omits its exact contribution manifest")
            product = next((product for product in parent.products if product.product_id == connection.supplier_product_id), None)
            external = next((external for external in draft.external_inputs if external.input_id == connection.external_input_id), None)
            if (product is None or external is None or product.role is not connection.evidence_role
                or external.payload_schema != product.artifact.payload_schema
                or external.expected_content_sha256 != product.artifact.sha256
                or external.outcome_access is not product.outcome_access
                or external.visibility_ceiling is not product.visibility_ceiling):
                raise ValueError("external contribution product changes its exact role, bytes or access")
        connections.append(connection)
        bindings.append((requirement.requirement_id, requirement.consumer_operation_id, requirement.assessment_operation_id))
    for link in links:
        if link.requirement_id is not None and link.requirement_id not in by_requirement:
            raise ValueError("scientific edge names an unselected requirement")
        if link.connection_id is not None and link.connection_id not in all_connections:
            raise ValueError("scientific edge names an absent connection")
    for proposal in draft.suppliers:
        if proposal.selected and proposal.requirement_id in by_requirement:
            if proposal.unavailable_reason_codes or not set(proposal.operation_ids).issubset(selected):
                raise ValueError("selected supplier proposal is unavailable or unselected")
            if not set(proposal.prerequisite_requirement_ids).issubset(all_requirements):
                raise ValueError("selected supplier proposal names an absent prerequisite")
    return requirements, tuple(sorted(connections, key=lambda value: value.connection_id)), tuple(bindings)
