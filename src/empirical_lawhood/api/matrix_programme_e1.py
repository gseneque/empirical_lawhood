# SPDX-License-Identifier: MPL-2.0
"""Assemble ordinary compact E1 inputs from the authentic whole-programme C.

Only canonical metadata is produced. This is neither native acquisition nor
source/sampling qualification, execution permission, or outcome authorization.
No historical root, issued package, input receipt or file is loaded here.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_preparation as compact
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_records as records
from empirical_lawhood.adapters.methods.matrix_researcher_programme import e1_assembly as domain
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experiments import ExperimentSpec, RevealBarrierSpec
from empirical_lawhood.kernel.obligations import ObligationStatus
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import LifecycleStatus, ReadinessStatus
from empirical_lawhood.kernel.worlds import NumericalCoordinateKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.planning.study_authoring import (
    DesignInputRecord, DesignInputRole, DesignOrigin, DesignOriginKind, SourceAccessDisposition,
    SourceMaterializationRef, StudyDraft, StudyDraftLifecycle,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def _require_science(selection, resolved):
    """Join declarations to actual C/D before creating any new publication."""
    context, design = selection.scientific_context, resolved.scientific_design
    system, criterion = context.system, design.e1_criterion
    reservation = resolved.phase('e1').reservation
    allocation = reservation.allocation
    criterion.validate_allocation(allocation, design.e1_factor_rule)
    if (system.system_id != criterion.system_id or system.world.world_id != criterion.world_id
            or ObjectIdentity.from_record(system.relation.relation_id, system.relation) != criterion.relation
            or system.independent_unit.unit_id != criterion.independent_unit_id
            or context.assignment.independent_unit_id != criterion.independent_unit_id
            or allocation.coordinates != design.e1_coordinates):
        raise ValueError('programme E1 context changes the actual D/C system, relation, unit or complete coordinates')
    clocks = {clock.clock_id: clock for clock in system.clocks}
    if (set(clocks) != {coordinate.clock_id for coordinate in allocation.coordinates}
            or any((clocks[coordinate.clock_id].time_unit, clocks[coordinate.clock_id].nominal_period)
                != (coordinate.primary_view.time_unit, coordinate.primary_view.timestep)
                for coordinate in allocation.coordinates)):
        raise ValueError('programme E1 context changes its actual four physical clocks')
    views = {view.view_id: view for view in system.numerical_views}
    expected_views = {view.view_id: view for coordinate in allocation.coordinates
        for view in (coordinate.primary_view, coordinate.fine_view)}
    if (set(views) != set(expected_views)
            or any(view.precision != expected_views[name].precision.value or not any(
                value.kind is NumericalCoordinateKind.TIMESTEP and value.value == expected_views[name].timestep
                and value.unit == expected_views[name].time_unit for value in view.coordinates)
                for name, view in views.items())):
        raise ValueError('programme E1 context changes its exact paired numerical views')
    if (system.relation.horizon.duration != design.e1_factor_rule.primary_dt * criterion.survival_duration_ticks
            or any(claim.world_id != system.world.world_id or claim.relation_id != system.relation.relation_id
                or claim.physical_independent_unit_id != system.independent_unit.unit_id
                or claim.numerical_view_ids != tuple(views) for claim in context.claims)
            or not any(value.capability_key == bindings.NAMESPACE + '.check' for value in context.controls)
            or not any(value.capability_key == bindings.KEY for value in context.obligations.falsifiers)):
        raise ValueError('programme E1 context changes its whole-root claim, survival horizon or independent falsifier')
    policy = system.authority_policy
    if resolved.commitments.namespace not in policy.scope_ids:
        raise PermissionError('programme E1 requires an explicit current policy scope for this programme namespace')
    if not resolved.exposure_census.exposed_independent_groups:
        raise ValueError('programme E1 reveal barrier requires the actual prior exposure group census')
    capacity, = selection.resources.child_token_limits
    if len(allocation.roots) > capacity.physical_execution_token_limit:
        raise ValueError('programme E1 explicit native capacity omits C-assigned roots')


def _required_obligations(context, cutoff, count):
    """Preserve requirements while discarding inherited completion/capacity acts."""
    original = context.obligations
    def required(value):
        return replace(value, status=ObligationStatus.REQUIRED, evidence_link_ids=())
    return replace(original,
        support=replace(required(original.support), information_cutoff_id=cutoff.cutoff_id,
            physical_unit_count=count, nested_numerical_view_count=len(context.system.numerical_views)),
        validity=required(original.validity), uncertainty=required(original.uncertainty),
        falsifiers=tuple(required(value) for value in original.falsifiers),
        closure=required(original.closure), structural_convergence=required(original.structural_convergence),
        computability=replace(original.computability, readiness=ReadinessStatus.PREREQUISITE_NOT_MET,
            unresolved_reason_codes=('CURRENT_EXECUTION_CAPACITY_NOT_ADMITTED',), evidence_link_ids=()),
        discrepancy=None if original.discrepancy is None else required(original.discrepancy))


def scientific_root(*, selection, resolved, manifest):
    """Pure current projection; no source or authority receipt can enter it."""
    _require_science(selection, resolved)
    context = selection.scientific_context
    namespace = resolved.commitments.namespace + '.e1'
    sources = records.sources_for_manifest(manifest)
    terminal = bindings.E1CompactAdjudicationConfig('config.' + bindings.KEY, manifest.identity,
        resolved.scientific_design.e1_criterion, sources)
    cutoffs = bindings.cutoffs(terminal)
    groups = tuple(sorted(source.root.root.independent_group_id for source in sources))
    obligations = _required_obligations(context, cutoffs[0], len(groups))
    experiment = ExperimentSpec('experiment.' + namespace, context.system.system_id, context.system.world.world_id,
        context.system.relation, context.system.independent_unit.unit_id, context.claims, context.assignment,
        context.measurement_quantity_ids, context.controls, context.precision_goals, cutoffs,
        RevealBarrierSpec('reveal.' + namespace, resolved.exposure_census.exposed_independent_groups,
            'cohort.' + namespace, sha256(canonical_json_bytes(groups)).hexdigest(),
            (namespace + '.sealed-complete-full-history',), OutcomeAccess.EVALUATION_SEALED, True),
        obligations, VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.PROSPECTIVE,
        context.system.authority_policy.policy_id, ReadinessStatus.AUTHORITY_REQUIRED)
    node = CampaignNode('node.' + namespace, CampaignNodeKind.EXPERIMENT_SPEC, CampaignLane.PROSPECTIVE,
        ObjectIdentity.from_record(experiment.experiment_id, experiment), (), LifecycleStatus.ACTIVE)
    campaign = replace(selection.campaign, objective=context.question, system_ids=(context.system.system_id,),
        world_ids=(context.system.world.world_id,), target_claim_ids=tuple(value.claim_id for value in context.claims),
        nodes=(node,), root_node_ids=(node.node_id,), active_node_ids=(node.node_id,), evidence_state=(),
        lifecycle_status=LifecycleStatus.ACTIVE)
    pins = tuple(sorted({resolved.commitments.identity, resolved.scientific_design.identity, context.identity,
        *(operand for source in sources for operand in bindings.source_operands(source))},
        key=lambda value: value.object_id))
    design_inputs = tuple(DesignInputRecord('input.' + namespace + '.' + str(index).zfill(5), pin,
        pin.object_fingerprint, cutoffs[0], DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, context.observation_operator.object_id) for index, pin in enumerate(pins))
    ceiling = ResourceBudget(selection.resources.maximum_parallel_tasks,
        selection.resources.aggregate_memory_ceiling_bytes, 0, None, None, None)
    if not context.system.authority_policy.budget_ceiling.contains(ceiling):
        raise ValueError('programme E1 current policy does not contain its explicit current resource ceiling')
    return StudyDraft('draft.' + namespace, StudyDraftLifecycle.DRAFT, context.question, context.alternative_ids,
        DesignOrigin('origin.' + namespace, DesignOriginKind.ORDINARY_THEORY_PREDECLARED,
            tuple(value.input_id for value in design_inputs), VisibilityCeiling.PROSPECTIVE), design_inputs,
        resolved.exposure_census.exposed_independent_groups, groups, (), (), (), context.system, experiment,
        campaign, 'recursive.' + namespace, (), (), ceiling)


def _partial_selection(selection, resolved, manifest):
    root = scientific_root(selection=selection, resolved=resolved, manifest=manifest)
    selected = compact.E1CompactExperimentSelectionV2('selection.' + resolved.commitments.namespace + '.e1',
        root, manifest, selection.phase_budgets, selection.resources, selection.native_progress, (),
        root.design_inputs, (), selection.entry_package, selection.formal_methods, selection.formal_source_inventories)
    specification = compact.E1CompactExperimentSpecification('experiment.' + resolved.commitments.namespace + '.e1',
        root.question, tuple(value.root_id for value in records.sources_for_manifest(manifest)), selected.identity)
    draft, _, operands = compact._derive(specification, selected)
    budget = ResourceBudget.aggregate(value.resource_budget for value in draft.operations)
    if not selection.campaign.budget.contains(budget):
        raise ValueError('programme E1 current campaign does not contain every actual selected task budget')
    return specification, selected, draft, operands


def assemble_programme_e1(*, specification, selection, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, maximum_source_bytes):
    """Authenticate C and publish the existing compact experiment's actual inputs."""
    from empirical_lawhood.api.derived_array_access import (
        DerivedInputAccess, derive_matrix_input_access_batch, supports_derived_input_access_batch,
    )
    from empirical_lawhood.api.derived_metadata_access import derive_canonical_metadata_access
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.infrastructure.source_origin import require_selected_implementation
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

    domain.bind_inputs(specification, {'selection': selection})
    execution.__post_init__()
    project = Path(project_root).resolve(strict=True)
    require_selected_implementation(project)
    implementation = implementation_binding(project)
    if (execution.source_snapshot != ObjectIdentity.from_record('recursive-member.implementation', implementation)
            or execution.workers != selection.resources.maximum_parallel_tasks
            or execution.environment_id is None or execution.output_root is None):
        raise ValueError('programme E1 requires its actual source and explicit matching worker/environment/output selections')
    root_path = Path(artifact_writer.root.contract.canonical_path).resolve(strict=True)
    directory, output = Path(metadata_directory), Path(output_selection_path)
    if (not directory.is_absolute() or directory != directory.resolve(strict=False)
            or not directory.is_relative_to(root_path) or directory.is_relative_to(project)
            or not output.is_absolute() or output != output.resolve(strict=False)
            or not output.parent.is_relative_to(directory) or output.name != 'sources.json'
            or Path(execution.output_root).resolve(strict=True) != root_path):
        raise ValueError('programme E1 metadata must use sources.json under its explicit canonical guarded external directory')
    relative = directory.relative_to(root_path).as_posix()
    selected_relative = output.parent.relative_to(root_path).as_posix()
    artifact_writer.root.resolve(output.relative_to(root_path).as_posix(), for_write=True)
    publications = []

    def request(name, logical, record, *, selection_output=False):
        destination = selected_relative if selection_output else relative
        return ArtifactWriteRequest(logical, destination + '/' + name + '.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', selection.record_id, relative,
            record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)

    def publish(name, logical, record, *, selection_output=False):
        # A new read observation is stable on replay. Original embedded flags
        # in C/reservations remain untouched; only this write's transient flag
        # is excluded from newly constructed metadata.
        actual = artifact_writer.write(request(name, logical, record, selection_output=selection_output))
        publications.append(actual)
        return replace(actual, created=False)

    with authenticated_programme_inputs(writer=artifact_writer, commitment=specification.input_commitments,
            maximum_source_bytes=maximum_source_bytes) as resolved:
        _require_science(selection, resolved)
        provenance = resolved.producing_provenance
        if (provenance.observed_git_head, provenance.code_sources_sha256, provenance.dependency_lock_sha256) != (
                implementation.observed_git_head, implementation.code_sources_sha256, implementation.dependency_lock_sha256):
            raise PermissionError('programme E1 producing provenance differs from the actual selected implementation')
        design = resolved.scientific_design
        namespace = resolved.commitments.namespace + '.e1'
        reservation = resolved.phase('e1').reservation
        science = records.E1CompactScientificSelection('science.' + namespace, records.identity(reservation),
            design.e1_factor_rule, design.e1_criterion, design.e1_numerical_design, design.e1_factor_numerical_design)
        scalar = design.e1_scalar_definition
        scalar_pin = ObjectIdentity.from_record(scalar.definition_id, scalar)
        scalar_publication, = (value.publication for value in resolved.commitments.scalar_definitions
            if value.record == scalar_pin)
        frozen = records.E1CompactFrozenSpecification('frozen.' + namespace, science,
            publish('scientific-selection', science.identity.object_id, science))
        manifest = records.E1CompactManifest('manifest.' + namespace, reservation, frozen, provenance, scalar, scalar_publication)
        target, selected, draft, operands = _partial_selection(selection, resolved, manifest)
        operand_index = dict(operands)
        requests = tuple(request('operands/' + sha256(external.input_id.encode()).hexdigest(),
            external.logical_artifact_id, operand_index[external.input_id]) for external in draft.external_inputs)
        actual_publications = artifact_writer.write_compact_batch(requests)
        publications.extend(actual_publications)
        inputs = tuple(DerivedInputAccess(replace(publication, created=False), operand_index[external.input_id], external)
            for publication, external in zip(actual_publications, draft.external_inputs, strict=True))
        access = dict(root=selected.root, observation_operator=selection.scientific_context.observation_operator)
        if supports_derived_input_access_batch(artifact_writer, len(inputs)):
            admissions = derive_matrix_input_access_batch(writer=artifact_writer, inputs=inputs, **access)
        else:
            admissions = tuple(derive_canonical_metadata_access(writer=artifact_writer, publication=value.publication,
                record=value.operand, external=value.external, **access) for value in inputs)
        materials = tuple(sorted((SourceMaterializationRef(config.source_id, config.role,
            selected.root.system.world.world_id, qualification.materialization, qualification.content_sha256,
            config.fingerprint(), qualification.observation_operator, qualification.numerical_view_ids,
            ObjectIdentity.from_record(qualification.receipt_id, qualification), SourceAccessDisposition.VERIFIED_ACCESS)
            for config, qualification in admissions), key=lambda value: value.source_id))
        selected = replace(selected, root=replace(selected.root, source_materializations=materials),
            qualifications=tuple(sorted((value for _, value in admissions), key=lambda value: value.receipt_id)),
            source_configs=tuple(sorted((value for value, _ in admissions), key=lambda value: value.fingerprint())))
        target = replace(target, selection=selected.identity)
        draft, _, _ = compact._derive(target, selected)
        registrations, registry, codecs = operation_catalog()
        compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
            implementation_commit=implementation.observed_git_head, implementation_sha256=implementation.code_sources_sha256,
            qualifications=selected.qualifications, known_design_inputs=selected.known_design_inputs, output_codecs=codecs)
        if compiled.candidate_draft is None or compiled.candidate_report is None:
            raise ValueError('programme E1 requires the ordinary prospective compiler scientific-root projection')
        selected = replace(selected, root=compiled.candidate_draft)
        target = replace(target, selection=selected.identity)
        preparation = compact.prepare(target, execution=execution, method_inputs=selected)
        # Keep the shared scientific operands at their original locations while
        # allowing a separately retained entry-review selection. Adding reviewed
        # entry/formal acts must not change the draft they identify or overwrite
        # the earlier incomplete selection.
        selected_pub = publish('selection', selected.identity.object_id, selected, selection_output=True)
        target_path = output.parent / 'specification.json'
        publish('specification', target.identity.object_id, target, selection_output=True)
        selector = ExperimentFileInputSelection('inputs.' + namespace, compact.PROTOCOL_ID,
            (ExperimentInputBinding('selection', selected.identity, 'selection.json', selected_pub.materialization.size_bytes),), ())
        publish('sources', selector.selection_id, selector, selection_output=True)
        payload = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
            'version': '1.0.0', 'value': {'specification': specification.identity, 'target_specification': target.identity,
                'input_commitments': specification.input_commitments.record, 'scientific_context': selection.scientific_context.identity,
                'root_count': len(target.root_ids), 'external_input_count': len(inputs),
                'metadata_access_receipt_count': len(admissions), 'native_contact': 'NONE',
                'scientific_authority': 'NONE', 'qualification': 'NOT_ESTABLISHED',
                'computability': 'CURRENT_EXECUTION_CAPACITY_NOT_ADMITTED',
                'candidate_diagnostics': tuple((value.code.value, value.field_path, value.message)
                    for value in compiled.candidate_report.diagnostics),
                'dependencies': tuple((value.code, value.kind.value, value.detail) for value in preparation.dependencies)}})
        requirements = artifact_writer.write(ArtifactWriteRequest('requirements.' + namespace,
            selected_relative + '/requirements.json', 'empirical-lawhood/operational/experiment-input-requirements',
            ArtifactProfile.CANONICAL_JSON, 'application/json', selection.record_id, relative, payload,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        publications.append(requirements)
        if implementation_binding(project) != implementation:
            raise PermissionError('programme E1 implementation changed during current input assembly')
        return ExperimentInputDerivationResult(specification.identity, selector, output, preparation,
            tuple(publications), requirements, target, target_path)


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Ordinary public derive hook; it never invokes a native runner."""
    from .experiment_preparation import load_experiment_inputs
    selected = load_experiment_inputs(specification, source_selection_path, artifact_writer=artifact_writer, read_access=read_access).method_inputs
    if selected is None:
        raise ValueError('programme E1 derivation requires its exact current input selection')
    maximum_source_bytes = max(budget.source_byte_limit for _, budget in selected.phase_budgets)
    return assemble_programme_e1(specification=specification, selection=selected, project_root=project_root,
        artifact_writer=artifact_writer, metadata_directory=metadata_directory,
        output_selection_path=output_selection_path, execution=execution, maximum_source_bytes=maximum_source_bytes)
