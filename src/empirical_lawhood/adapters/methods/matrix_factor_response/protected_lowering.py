# SPDX-License-Identifier: MPL-2.0
"""Specification-derived current E3 graph, with no acquisition or authority."""

from dataclasses import dataclass, replace

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection

from .protected_feature_bindings import FEATURE_ARRAY_INPUTS, FEATURE_RECORD_INPUTS, ProtectedE3FeatureConfig, feature_task_id
from .protected_adjudication import ProtectedE3AdjudicationConfig, adjudication_task_id
from .protected_prefix_workers import prefix_worker_phase
from .protected_response_bindings import _arrays, _records
from .protected_response_preparation import response_task_id
from .protected_response_records import ProtectedE3PhysicalForecastConfig, ProtectedE3ResponseConfig, _object
from .protected_source_records import ProtectedE3SourceConfig, ProtectedE3SourcePhase, identity, source_task_id
from .protected_statistical_bindings import ProtectedE3StatisticalConfig, statistical_task_id


@dataclass(frozen=True, slots=True)
class ProtectedE3LoweredExperiment:
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]
    file_identities: tuple
    resource_selection: ExecutionResourceSelection


def task_id(config):
    if type(config) is ProtectedE3AdjudicationConfig:
        return adjudication_task_id(config.specification, config.allocation)
    if type(config) is ProtectedE3SourceConfig:
        return source_task_id(config.source.root_id, config.phase)
    if type(config) is ProtectedE3FeatureConfig:
        return feature_task_id(config.root.root_id)
    if type(config) is ProtectedE3PhysicalForecastConfig:
        return response_task_id(config.root_id, "physical-forecast")
    if type(config) is ProtectedE3ResponseConfig:
        return response_task_id(config.source.root_id, config.operation)
    return statistical_task_id(config.specification, config.allocation, config.operation, mode=config.mode, root=config.root)


def operation_class(config):
    """Installed operation phase, independent of generated task identities."""
    return (config.phase.value if type(config) is ProtectedE3SourceConfig else "feature" if type(config) is ProtectedE3FeatureConfig
        else "physical-forecast" if type(config) is ProtectedE3PhysicalForecastConfig else
        config.mode + "-freeze" if config.operation == "freeze" else config.operation)


def selected_configs(specification, allocation, selection):
    """One projection of task identities from selected original whole units."""
    census = tuple((role, len(allocation.unit_ids(role))) for role in ("calibration", "evaluation"))
    fit = selection.fit_config
    if (fit.specification, fit.allocation, fit.query_census, fit.source_manifest, fit.training_allocation) != (
            specification.identity, allocation.identity, census, identity(selection.manifest), selection.training_allocation.identity):
        raise ValueError("protected E3 fit changes its selected original allocation, manifest or complete census")
    configs = [fit]
    configs.append(ProtectedE3AdjudicationConfig("config." + adjudication_task_id(specification.identity, allocation.identity),
        specification.identity, allocation.identity))
    for operation, mode in (("freeze", "model"), ("calibrate", ""), ("freeze", "calibration"), ("assess", "")):
        node = statistical_task_id(specification.identity, allocation.identity, operation, mode=mode)
        configs.append(ProtectedE3StatisticalConfig("config." + node, operation, specification.identity, allocation.identity, census, mode))
    protocols = {p.public_source.root.root_id: p for p in selection.protocols}
    profiles = {p.original_protocol: p for p in selection.numerical_profiles}
    for source in selection.sources:
        root = source.root.root
        if root.role.value == "WITHHELD_TRANSFER":
            continue
        protocol = protocols[root.root_id]
        profile = profiles[_object(protocol)]
        for phase in ProtectedE3SourcePhase:
            configs.append(ProtectedE3SourceConfig("config." + source_task_id(root.root_id, phase), phase,
                specification.identity, identity(selection.manifest), source))
        configs.append(ProtectedE3FeatureConfig("config." + feature_task_id(root.root_id), specification.identity,
            allocation.identity, ObjectIdentity.from_record("public.matrix-e3." + root.root_id, protocol.public_source), _object(selection.manifest.native_specification.selection.numerical_design), root))
        mode = "calibration" if root.role.value == "CALIBRATION" else "evaluation"
        node = statistical_task_id(specification.identity, allocation.identity, "forecast", mode=mode, root=root)
        configs.append(ProtectedE3StatisticalConfig("config." + node, "forecast", specification.identity, allocation.identity, census, mode, root))
        configs.append(ProtectedE3PhysicalForecastConfig("config." + response_task_id(root.root_id, "physical-forecast"),
            root.root_id, specification.identity, _object(protocol), identity(profile)))
        for operation in ("responses", "response-score"):
            configs.append(ProtectedE3ResponseConfig("config." + response_task_id(root.root_id, operation), operation,
                specification.identity, identity(selection.manifest), source, identity(selection.response_selection),
                _object(protocol), identity(profile)))
    return tuple(sorted(configs, key=task_id))


def lower_protected_matrix_response_error(specification, allocation, selection):
    """Derive all current native, predictor and statistical connections once.

    Original byte locators stay distinct from eligibility and current authority.
    TRAIN and template bodies are files; this function never opens either.
    """
    from .protected_composition import operation_declarations
    from .protected_preparation import _resolve_protected_e3_resources, validate_selection_science

    validate_selection_science(specification, allocation, selection)
    declarations = {row.capability_key: row for row in operation_declarations()}
    configs = selected_configs(specification, allocation, selection)
    configs_by_task = {task_id(config): config for config in configs}
    resources = _resolve_protected_e3_resources(selection, configs)
    cells = {cell.task_id: cell for cell in resources.task_cells}
    records, externals, links, files, operations = {}, {}, [], {}, []
    required = {key: pub for key, pub, _ in selection.fit_config.publications}
    public = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE
    development = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY

    def external(node, name, record, *, logical=None, lane=public, role="SOURCE"):
        logical = logical or "input.matrix-e3." + record.fingerprint()
        key = "external." + logical
        raw = record.canonical_bytes()
        item = RecursiveExternalInput(key, logical, record.SCHEMA, "application/json", len(raw), *lane, record.fingerprint(), role)
        if externals.setdefault(key, item) != item or records.setdefault(key, record) != record:
            raise ValueError("protected E3 aliases exact original external input roles or bytes")
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=key, scientific_role=role))

    def file_input(node, name, artifact, *, lane=public, role="SOURCE"):
        key = "external." + artifact.artifact_id
        item = RecursiveExternalInput(key, artifact.artifact_id, artifact.payload_schema, artifact.media_type,
            artifact.size_bytes, *lane, artifact.sha256, role)
        if externals.setdefault(key, item) != item or files.setdefault(key, artifact) != artifact:
            raise ValueError("protected E3 aliases original file operands")
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=key, scientific_role=role))

    def dependency(node, name, producer, output="product", role="HISTORY"):
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name,
            producer_node_id=producer, producer_output_id=output, scientific_role=role))

    def statistic(operation, mode="", root=None):
        return statistical_task_id(specification.identity, allocation.identity, operation, mode=mode, root=root)

    manifest = selection.manifest
    protocols = {p.public_source.root.root_id: p for p in selection.protocols}
    profiles = {p.original_protocol: p for p in selection.numerical_profiles}
    projections = {p.prefix_policy: p for p in selection.projections}
    descriptors = {s.root_id: s for s in selection.sources}
    query_roots = {role: tuple(p.public_source.root for p in selection.protocols if
        p.public_source.root.role.value == ("CALIBRATION" if role == "calibration" else "CONFIRMATION"))
        for role in ("calibration", "evaluation")}
    for config in configs:
        node = task_id(config)
        phase = operation_class(config)
        declaration = declarations["matrix-e3-protected." + phase]
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
            config_id=getattr(config, "record_id", getattr(config, "config_id", None)), config=config,
            obligation_ids=("obligation." + node + ".complete-selected-scope",), resource_budget=ResourceBudget(
                cells[node].resource_budget.cpu_cores, cells[node].resource_budget.memory_bytes, 0, None,
                cells[node].resource_budget.source_byte_limit, cells[node].resource_budget.output_bytes)))
        if type(config) is ProtectedE3AdjudicationConfig:
            pub = required["roles"]
            external(node, "allocation", allocation, logical=pub.logical.logical_artifact_id,
                lane=(pub.logical.outcome_access, pub.logical.visibility_ceiling))
            external(node, "specification", specification)
            dependency(node, "assessment", statistic("assess"), role="OUTCOME")
        elif type(config) is ProtectedE3SourceConfig:
            source = descriptors[config.source.root_id]
            prefix_node = source_task_id(source.root_id, ProtectedE3SourcePhase.PREFIX)
            prefix_config = configs_by_task[prefix_node]
            coordinate = next(c for c in manifest.reservation.allocation.coordinates if c.coordinate_id == source.root.root.coordinate_id)
            provenance = next(p for p in manifest.provenances if p.identity == source.provenance)
            if config.phase is ProtectedE3SourcePhase.PREFIX:
                for name, record in (("specification", specification), ("manifest", manifest), ("source", source),
                        ("coordinate", coordinate), ("provenance", provenance)):
                    external(node, name, record)
                for stream in source.root.streams:
                    external(node, "streams." + stream.purpose, stream, logical=source.root.stream_identity(stream).object_id)
            else:
                selected = prefix_worker_phase(config.phase)
                for name, _, producer in selected.records:
                    if producer is not None:
                        dependency(node, name, source_task_id(source.root_id, producer))
                    else:
                        external(node, name, {"specification": specification, "manifest": manifest, "prefix-config": prefix_config}[name])
                for name, producer in selected.arrays:
                    dependency(node, name, source_task_id(source.root_id, producer), "arrays")
        elif type(config) is ProtectedE3FeatureConfig:
            protocol = protocols[config.root.root_id]
            for name, _, producer in FEATURE_RECORD_INPUTS:
                if producer is None:
                    external(node, name, {"specification": specification, "public-source": protocol.public_source,
                        "numerical-design": manifest.native_specification.selection.numerical_design}[name])
                else:
                    dependency(node, name, source_task_id(config.root.root_id, producer))
            for name, producer in FEATURE_ARRAY_INPUTS:
                dependency(node, name, source_task_id(config.root.root_id, producer), "arrays")
        elif type(config) in (ProtectedE3PhysicalForecastConfig, ProtectedE3ResponseConfig):
            root_id = config.root_id if phase == "physical-forecast" else config.source.root_id
            descriptor, protocol = descriptors[root_id], protocols[root_id]
            root = protocol.public_source.root
            confirmation = root.role.value == "CONFIRMATION"
            profile = profiles[_object(protocol)]
            prefix = source_task_id(root_id, ProtectedE3SourcePhase.PREFIX)
            project = source_task_id(root_id, ProtectedE3SourcePhase.PROJECT)
            projection = projections[_object(protocol.public_source.policy)]
            selected_panels = tuple(p for p in selection.panels if p.independent_group_id == root.independent_group_id)
            external_records = {"specification": specification, "protocol": protocol, "numerical-profile": profile,
                "mathematical-protocol": selection.mathematical_protocol, "projection": projection, "manifest": manifest,
                "source": descriptor, "coordinate": protocol.public_source.coordinate,
                "provenance": next(p for p in manifest.provenances if p.identity == descriptor.provenance),
                "selection": selection.response_selection, "prefix-config": configs_by_task[prefix],
                "physical-config": configs_by_task[response_task_id(root_id, "physical-forecast")],
                "native-config": configs_by_task[response_task_id(root_id, "responses")], "allocation": allocation}
            dependencies = {"causal": (project, "product"), "history": (prefix, "product"), "checkpoint": (prefix, "checkpoint"),
                "physical": (response_task_id(root_id, "physical-forecast"), "product"), "models": (statistic("fit"), "product"),
                "frozen": (statistic("freeze", "calibration" if confirmation else "model"), "product"),
                "error": (statistic("forecast", "evaluation" if confirmation else "calibration", root), "product"),
                "calibration": (statistic("calibrate"), "product"), "model-freeze": (statistic("freeze", "model"), "product"),
                "responses": (response_task_id(root_id, "responses"), "product")}
            for name, _ in _records(phase):
                if name in ("calibration", "model-freeze") and not confirmation:
                    continue
                if name == "panels":
                    for panel in selected_panels:
                        external(node, name + "." + panel.panel_id, panel)
                elif name == "streams":
                    for owner in (descriptor.root, *(p for p in selected_panels if p.role == "INDEPENDENT_FUTURE")):
                        for stream in owner.streams:
                            external(node, name + "." + owner.stream_identity(stream).object_id, stream,
                                logical=owner.stream_identity(stream).object_id)
                elif name in dependencies:
                    dependency(node, name, *dependencies[name], role="MODEL" if name in ("models", "frozen", "error", "calibration", "model-freeze") else "HISTORY")
                elif name == "allocation":
                    # Share the exact original roles publication with fit and
                    # statistics instead of publishing the same census again.
                    pub = required["roles"]
                    external(node, name, allocation, logical=pub.logical.logical_artifact_id,
                        lane=(pub.logical.outcome_access, pub.logical.visibility_ceiling))
                else:
                    external(node, name, external_records[name], lane=(profile.provenance_publication.logical.outcome_access, profile.provenance_publication.logical.visibility_ceiling) if name == "numerical-profile" else public)
            array_sources = {"prefix-arrays": (prefix, "arrays"), "causal-arrays": (project, "arrays"),
                "physical-arrays": (response_task_id(root_id, "physical-forecast"), "arrays"),
                "response-arrays": (response_task_id(root_id, "responses"), "arrays")}
            for name in _arrays(phase):
                if name == "templates-arrays":
                    file_input(node, name, protocol.templates.array_artifact)
                else:
                    dependency(node, name, *array_sources[name])
        else:
            if phase == "fit":
                originals = {"allocation": (allocation, "roles"), "original-allocation": (manifest.reservation.allocation, "allocation"),
                    "native-selection": (manifest.native_specification.selection, "native-selection"), "reservation": (manifest.reservation, "reservation")}
                for name, record in (("specification", specification), ("manifest", manifest), ("training-allocation", selection.training_allocation)):
                    external(node, name, record)
                for name, (record, key) in originals.items():
                    pub = required[key]
                    external(node, name, record, logical=pub.logical.logical_artifact_id,
                        lane=(pub.logical.outcome_access, pub.logical.visibility_ceiling))
                file_input(node, "features", selection.training_features, lane=development)
                file_input(node, "outcomes", selection.training_outcomes, lane=development)
            else:
                # The roles publication is reused under its original logical ID.
                pub = required["roles"]
                external(node, "allocation", allocation, logical=pub.logical.logical_artifact_id,
                    lane=(pub.logical.outcome_access, pub.logical.visibility_ceiling))
                external(node, "specification", specification)
                if phase in ("model-freeze", "calibration-freeze", "forecast", "calibrate"):
                    dependency(node, "models", statistic("fit"), role="MODEL")
                if phase == "model-freeze":
                    dependency(node, "prefit-join", statistic("fit"), "prefit-join", role="MODEL")
                elif phase == "calibration-freeze":
                    dependency(node, "model-freeze", statistic("freeze", "model"), role="MODEL")
                    dependency(node, "calibration", statistic("calibrate"), role="MODEL")
                else:
                    mode = config.mode if phase == "forecast" else "calibration" if phase == "calibrate" else "evaluation"
                    dependency(node, "frozen", statistic("freeze", "model" if mode == "calibration" else "calibration"), role="MODEL")
                    if phase == "forecast":
                        dependency(node, "feature", feature_task_id(config.root.root_id))
                        if mode == "evaluation":
                            dependency(node, "model-freeze", statistic("freeze", "model"), role="MODEL")
                            dependency(node, "calibration", statistic("calibrate"), role="MODEL")
                    else:
                        for root in query_roots[mode]:
                            dependency(node, "forecasts." + root.root_id, statistic("forecast", mode, root), role="MODEL")
                            dependency(node, "outcomes." + root.root_id, response_task_id(root.root_id, "response-score"), "outcome", role="OUTCOME")
    root = selection.root
    if root.campaign is None:
        raise ValueError("protected E3 needs its actual selected prospective campaign")
    # Freeze the code-derived original operands as design metadata. These pins
    # are declared references, never new publications or source qualifications.
    references = {ref.object_id: ref for ref in (specification.identity, allocation.identity, identity(manifest), selection.training_allocation.identity)}
    for descriptor in selection.sources:
        for ref in (_object(descriptor), descriptor.identity, descriptor.allocation, descriptor.reservation,
                descriptor.selection, descriptor.specification, descriptor.provenance, descriptor.coordinate):
            if references.setdefault(ref.object_id, ref) != ref:
                raise ValueError("protected E3 scientific operands alias original identities")
    for config in configs:
        for name in ("specification", "allocation", "public_source", "numerical_design", "protocol", "numerical_profile",
                "source_manifest", "response_selection"):
            ref = getattr(config, name, None)
            if isinstance(ref, type(specification.identity)):
                if references.setdefault(ref.object_id, ref) != ref:
                    raise ValueError("protected E3 configuration aliases scientific identities")
    pins = tuple(DesignInputRecord("design.matrix-e3." + ref.object_fingerprint, ref, ref.object_fingerprint,
        selection.fit_config.fit_cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, root.design_inputs[0].operator_id)
        for ref in sorted(references.values(), key=lambda ref: ref.object_fingerprint))
    by_id = {pin.input_id: pin for pin in (*root.design_inputs, *pins)}
    design_inputs = tuple(by_id[key] for key in sorted(by_id))
    query_groups = tuple(sorted(p.public_source.root.independent_group_id for p in selection.protocols))
    cutoffs = tuple(sorted((InformationCutoff("cutoff." + p.public_source.root.root_id, p.public_source.coordinate.clock_id,
        CausalPhase.PRE_ACTION, p.public_source.coordinate.physical_time(p.public_source.policy.cutoff_tick))
        for p in selection.protocols), key=lambda row: row.cutoff_id))
    experiment = replace(root.experiment, information_cutoffs=cutoffs)
    aggregate_budget = ResourceBudget.aggregate(op.resource_budget for op in operations)
    original_experiment = ObjectIdentity.from_record(root.experiment.experiment_id, root.experiment)
    selected_experiment = ObjectIdentity.from_record(experiment.experiment_id, experiment)
    campaign = replace(root.campaign, objective=specification.question, budget=aggregate_budget,
        nodes=tuple(replace(node, object_identity=selected_experiment)
        if node.object_identity == original_experiment else node for node in root.campaign.nodes))
    root = replace(root, design_inputs=design_inputs,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(pin.input_id for pin in design_inputs)),
        development_unit_ids=allocation.unit_ids("train"), evaluation_unit_ids=query_groups,
        experiment=experiment, campaign=campaign,
        resource_ceiling=replace(aggregate_budget, memory_bytes=resources.aggregate_memory_ceiling_bytes),
        dag_template_key="recursive.draft.matrix-e3.protected." + specification.fingerprint(),
        capability_selections=tuple(sorted({row.selection for row in operations}, key=lambda row: row.selection_id)))
    from empirical_lawhood.runtime.candidate_compiler import required_candidate_obligation_ids
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.runtime.plans import ProtocolStepTemplate, ProtocolTemplate
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, project_recursive_config_inputs
    from .protected_composition import validate_generated_links

    registrations = {row.registration().selection.selection_id: row.registration() for row in declarations.values()}
    decoded = tuple(decode_recursive_config_input(op, registrations[op.selection.selection_id]) for op in operations)
    projected = project_recursive_config_inputs(decoded, {op.node_id: registrations[op.selection.selection_id] for op in operations})
    validate_generated_links(projected, tuple(links))
    assessment = next(op for op in operations if op.node_id == statistic("assess"))
    config = configs_by_task[assessment.node_id]
    declaration = declarations["matrix-e3-protected.assess"]
    manifest = declaration.manifest()
    config_ref = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config.record_id)
    step = ProtocolStepTemplate(assessment.node_id, declaration.stage, manifest.capability_key, manifest.capability_version,
        config_ref, (), declaration.outputs, declaration.permissions, declaration.outcome_access,
        declaration.visibility_ceiling, assessment.resource_budget, (), declaration.execution_properties.barrier, 1,
        assessment.obligation_ids)
    obligations = required_candidate_obligation_ids(root.experiment,
        ProtocolTemplate("template." + assessment.node_id, "1.0.0", (step,), False, False, True))
    # Each actual cutoff is owned by its frozen forecast. Remaining canonical
    # obligations receive one complete final assessment owner, including all
    # adverse and unevaluable outcomes rather than an inferred success.
    cutoff_owners = {"cutoff." + p.public_source.root.root_id:
        statistic("forecast", "calibration" if p.public_source.root.role.value == "CALIBRATION" else "evaluation", p.public_source.root)
        for p in selection.protocols}
    additions = {op.node_id: [] for op in operations}
    reveal_obligations = {root.experiment.reveal_barrier.barrier_id,
        *(root.experiment.experiment_id + "." + suffix for suffix in ("authority", "required-outputs", "seal-reveal-separation"))}
    for obligation in obligations:
        if obligation not in assessment.obligation_ids:
            owner = (adjudication_task_id(specification.identity, allocation.identity) if obligation in reveal_obligations
                else cutoff_owners.get(obligation, assessment.node_id))
            additions[owner].append(obligation)
    operations = [replace(op, obligation_ids=tuple(sorted((*op.obligation_ids, *additions[op.node_id])))) for op in operations]
    draft = RecursiveStudyDraft("draft.matrix-e3.protected." + specification.fingerprint(), root.question, root.campaign,
        (), (), (), tuple(sorted(operations, key=lambda row: row.node_id)), tuple(sorted(externals.values(), key=lambda row: row.input_id)),
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(configs_by_task)), prospective_draft=root)
    return ProtectedE3LoweredExperiment(draft, tuple(sorted(records.items())), tuple(sorted(files.items())), resources)
