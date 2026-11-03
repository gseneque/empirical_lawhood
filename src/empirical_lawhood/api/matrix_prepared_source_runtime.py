# SPDX-License-Identifier: MPL-2.0
"""Receipt-backed prepared instrument controls; never a nomination or authority.

The complete original E5 development graph supplies its actual preparation,
frame and response controls, including nonuse. Nomination/headroom is not a
prerequisite for this instrument-only projection. Ordinary source/issue/reveal
owners retain their separate authority boundaries.
"""
from empirical_lawhood.adapters.methods.matrix_factor_response.exposure import MatrixScheduledPhysicalExclusion

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier

from contextlib import contextmanager
from dataclasses import dataclass, replace

from empirical_lawhood.adapters.methods import matrix_prepared_source_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import entry_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_request
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_bindings as preparation
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science, prepared_prefix
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as opportunity
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as revision
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_future, selected_revision_future
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationHistory, MatrixPreparationAssessment, preparation_identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import MatrixPreparedMechanicalForecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponseReadout
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_development_product import MatrixRevisionDevelopmentProduct
from empirical_lawhood.api.native_training_banks import _read_instance, _receipt_product
from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_roots
from empirical_lawhood.api.recursive_operations import development_output_contracts, operation_catalog
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input


def _allocations(programme):
    return programme.allocations if hasattr(programme, "allocations") else programme.sources.allocations


def _complete_development(writer, directory, *, validate_authored,read_access=None):
    """Read once after exact consumer preflight, retaining original DEV semantics."""
    def validate(**roots):
        preflight = validate_authored(**roots)
        _, _, codecs = operation_catalog()
        development_output_contracts(roots["plan"], codecs)
        return preflight
    result, roots, preflight = _read_recursive_wave_with_roots(directory=directory,
        artifact_writer=writer, include_products=True, terminal_product_format="compact",
        allow_partial=False, validate_authored=validate,
        **({} if read_access is None else {"read_access":read_access}))
    report, products, actual_draft, actual_plan = result
    packet, draft, _, run, plan, _ = roots
    if (actual_draft != draft or actual_plan != plan or report["run_id"] != run.run_plan_id
            or report["packet_sha256"] != packet.fingerprint() or report["status"] != "SUCCEEDED"
            or set(products["receipts"]) != {task.task_id for task in plan.tasks}):
        raise PermissionError("prepared source requires the unchanged complete successful development graph")
    return products, roots, preflight


def _native_training_prerequisite(writer, locator):
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
    if type(locator) is not MatrixFiniteDtTrainingLocator:
        raise TypeError("prepared source requires the exact original native TRAIN locator")
    locator.__post_init__()
    directory = writer.root.resolve(locator.authored_directory, for_write=False)
    def validate(*, packet, draft, source, payloads, run, plan, index):
        specification, request, _ = _read_instance(payloads)
        if (type(plan) is not DevelopmentExecutionPlan or r.pin(packet, "packet_id") != locator.packet
                or r.pin(plan, "execution_plan_id") != locator.execution_plan or run.run_plan_id != locator.run_id
                or draft.development_study is None or draft.prospective_draft is not None):
            raise PermissionError("prepared source substitutes original native TRAIN custody or development lane")
        phases = authenticate_request(writer, request)
        if len(phases) != 4:
            raise PermissionError("prepared source requires actual complete pre-TRAIN future commitments")
        return specification, request, phases
    products, roots, (specification, request, phases) = _complete_development(writer, directory,
        validate_authored=validate)
    _, _, _, _, plan, _ = roots
    acquisition, _ = _receipt_product(writer, products, plan, entry_task_id(specification), train.NativeTrainingAcquisitionSeal)
    if acquisition != train.acquisition_seal(specification, request):
        raise PermissionError("prepared source substitutes its actual pre-TRAIN acquisition seal")
    return specification, request, acquisition, phases


def _development_selection(writer, locator,*,current_access=None):
    """Select an entire real E5 graph, independently of its nomination outcome."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
        MatrixSelectedOpportunityRootConfigV2, MatrixRevisionRootConfigV2)
    if type(locator) not in (MatrixSelectedDevelopmentProduct, MatrixRevisionDevelopmentProduct):
        raise TypeError("prepared source needs an exact original E5 development product locator")
    locator.__post_init__()
    directory = writer.root.resolve(locator.authoring_relative_path, for_write=False)
    def validate(*, packet, draft, source, payloads, run, plan, index):
        if (type(plan) is not DevelopmentExecutionPlan or r.pin(packet, "packet_id") != locator.authored_wave
                or r.pin(run, "run_plan_id") != locator.run_plan or r.pin(plan, "execution_plan_id") != locator.execution_plan
                or run.run_plan_id != locator.run_id or draft.development_study is None or draft.prospective_draft is not None):
            raise PermissionError("prepared source substitutes the original complete E5 development custody")
        is_revision = type(locator) is MatrixRevisionDevelopmentProduct
        owner = revision if is_revision else opportunity
        final_phase = "assess-programme" if is_revision else "nominate"
        declarations = {(value.capability_key, value.capability_version): value for value in owner.operation_declarations()}
        final_key = owner.capability_key(final_phase, "DEVELOPMENT") if is_revision else owner.NAMESPACE + "." + final_phase
        final_ops = tuple(value for value in draft.operations if value.node_id == locator.task_id
            and value.selection.capability_key == final_key)
        if len(final_ops) != 1:
            raise PermissionError("prepared source omits its actual complete installed E5 terminal producer")
        final = final_ops[0]
        config = decode_recursive_config_input(final, declarations[(final_key, final.selection.capability_version)].registration()).record
        programme = config.programme
        programme.__post_init__()
        if (programme.phase != "E5_OPPORTUNITY" or config.phase != final_phase
                or draft.development_study != owner.development_root(programme, draft.development_study.study_id)):
            raise PermissionError("prepared source changes its actual complete exposed opportunity science")
        entry_phase = "entry" if is_revision else "design"
        entry_key = owner.capability_key(entry_phase, "DEVELOPMENT", "2.0.0") if is_revision else owner.COMMITTED_DESIGN_KEY
        entry_ops = tuple(value for value in draft.operations if value.selection.capability_key == entry_key)
        if len(entry_ops) != 1:
            raise PermissionError("prepared source omits its genuine original development entry")
        entry = decode_recursive_config_input(entry_ops[0], declarations[(entry_ops[0].selection.capability_key, entry_ops[0].selection.capability_version)].registration()).record
        if (type(entry) is not (MatrixRevisionRootConfigV2 if is_revision else MatrixSelectedOpportunityRootConfigV2)
                or entry.programme != programme):
            raise PermissionError("prepared source terminal differs from its original committed entry programme")
        produced_parents = entry.produced_input_parents
        expected, external, links, _, _ = owner.contracts(programme,
            entry.entry_evidence if is_revision else entry.evidence,
            entry.entry_evidence_size_bytes if is_revision else entry.evidence_size_bytes,
            produced_input_parents=produced_parents)
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
        output_access, output_visibility = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
            parents=produced_parents)
        if (set(dict(expected)) != {value.node_id for value in draft.operations}
                or draft.external_inputs != external or draft.links != links
                or {task.task_id for task in plan.tasks} != set(dict(expected))):
            raise PermissionError("prepared source thins the actual complete development task/source/edge census")
        expected = dict(expected)
        tasks = {task.task_id: task for task in plan.tasks}
        for operation in draft.operations:
            declaration = declarations.get((operation.selection.capability_key, operation.selection.capability_version))
            if declaration is None or operation.selection != declaration.registration().selection:
                raise PermissionError("prepared source changes an installed original E5 producer")
            observed = decode_recursive_config_input(operation, declaration.registration()).record
            task = tasks[operation.node_id]
            manifest = declaration.manifest()
            if (observed != expected[operation.node_id]
                    or (task.capability.capability_key, task.capability.capability_version, task.capability_implementation_sha256,
                        task.capability.kind, task.capability.config.config_id, task.capability.config.config_schema,
                        task.capability.config.content_sha256, task.capability.config.config_schema_sha256,
                        task.capability.requested_resources, task.capability.requested_outcome_access, task.capability.required_permissions, task.stage) !=
                       (manifest.capability_key, manifest.capability_version, manifest.implementation_sha256,
                        manifest.kind, observed.config_id, manifest.config_schema, observed.fingerprint(), manifest.config_schema_sha256,
                        operation.resource_budget, OutcomeAccess.DEVELOPMENT_VISIBLE, manifest.permissions, declaration.stage)
                    or tuple((output.output_id, output.payload_schema, output.profile, output.media_type) for output in task.outputs) !=
                       tuple(sorted((task.task_id + "." + output.output_id, output.payload_schema, output.profile, output.media_type)
                           for output in declaration.outputs))
                    or any(output.outcome_access is not output_access
                        or output.visibility_ceiling is not output_visibility for output in task.outputs)):
                raise PermissionError("prepared source changes actual E5 config, method, stage or DEV scope")
        return programme, is_revision, entry, entry_ops[0].node_id
    products, roots, (programme, is_revision, entry, entry_task) = _complete_development(writer, directory,
        validate_authored=validate,read_access=current_access)
    _, _, _, run, plan, _ = roots
    owner = revision if is_revision else opportunity
    tasks = {task.task_id: task for task in plan.tasks}
    terminal_kind = revision.MatrixRevisionProgrammeAssessment if is_revision else opportunity.MatrixPreparationNomination
    terminal, receipt = _receipt_product(writer, products, plan, locator.task_id, terminal_kind)
    publication = products["outputs"].get(locator.logical_artifact_id)
    if (r.pin(terminal) != locator.record or r.pin(receipt, "receipt_id") != locator.receipt
            or publication is None or (publication.logical, publication.materialization) !=
                (locator.publication.logical, locator.publication.materialization)):
        raise PermissionError("prepared source changes its actual complete development terminal publication")
    authenticate_publication(writer, locator.publication, terminal)
    # The successful actual entry owns these original producer locators. Reading
    # its exact published input does not replay or grant their old authority.
    from empirical_lawhood.api.matrix_selected_runtime import _published_input
    evidence_pin = entry.entry_evidence if is_revision else entry.evidence
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
        MatrixRevisionEntryEvidenceV2, MatrixSelectedOpportunityEvidenceV2,
    )
    evidence_type = MatrixRevisionEntryEvidenceV2 if is_revision else MatrixSelectedOpportunityEvidenceV2
    evidence_specs = tuple(value for value in tasks[entry_task].external_inputs
        if (value.expected_payload_schema, value.expected_content_sha256) ==
            (evidence_pin.object_schema, evidence_pin.object_fingerprint))
    if len(evidence_specs) != 1:
        raise PermissionError("prepared source omits its actual receipted entry evidence input")
    evidence = _published_input(writer, run.run_plan_id, evidence_specs[0], evidence_type)
    if evidence.identity != evidence_pin:
        raise PermissionError("prepared source changes its actual original entry evidence")
    from .domain_composition.matrix_selected_declarative.derivation import require_evidence_produced_input_parents
    require_evidence_produced_input_parents(writer, entry.produced_input_parents, evidence)
    # No selected-arm, headroom or NOMINATED predicate belongs to instrument custody.
    return programme, owner, is_revision, products, plan, entry_task, evidence


def _prepared_control(writer, programme, owner, is_revision, products, plan, entry_task, source):
    selected = {}
    phases = (("history", MatrixPreparationHistory), ("assess", MatrixPreparationAssessment),
        ("measure", prepared_prefix.MatrixPreparedFactorWitness), ("frames", prepared_prefix.MatrixPreparedFrameAssessment),
        ("project", prepared_prefix.MatrixPreparedCausalPrefix), ("point", owner.OUTPUTS["point"]),
        ("mechanical", MatrixPreparedMechanicalForecast), ("responses", owner.OUTPUTS["responses"]),
        ("response-score", MatrixPreparedResponseReadout))
    receipts = [products["receipts"][entry_task]]
    for phase, kind in phases:
        node = preparation.node_id(source, phase) if phase in ("history", "assess") else owner.NAMESPACE + "." + source.source_id + "." + phase
        selected[phase], receipt = _receipt_product(writer, products, plan, node, kind)
        receipts.append(receipt)
    history, assessment, witness, frames, causal, point, mechanical, responses, score = (selected[phase] for phase, _ in phases)
    allocation, = (value for value in _allocations(programme) if scheduled.identity(value) == source.original.allocation)
    history.validate_source(source, allocation)
    preparation_science.validate_preparation_assessment(source, history.arrays, assessment)
    protocol = programme.protocol(source)
    panels = dict(programme.panels)[source.root.root.independent_group_id]
    phase = "response-score"
    if is_revision:
        config = selected_revision_future.MatrixRevisionFutureConfig("config." + owner.NAMESPACE + "." + source.source_id + "." + phase,
            programme.identity, source, protocol, panels, programme.selected_package, phase)
        future_owner = selected_revision_future
    else:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import package_identity
        config = selected_opportunity_future.MatrixSelectedOpportunityFutureConfig("config." + owner.NAMESPACE + "." + source.source_id + "." + phase,
            programme.identity, source, protocol, panels, programme.point_design.identity, package_identity(programme.point_design.package), phase)
        future_owner = selected_opportunity_future
    future_owner.validate_future_history(config, history, causal, point, mechanical, responses)
    if (witness.source != source.identity or witness.preparation != preparation_identity(history.arrays)
            or witness.numerical != preparation_identity(assessment) or witness.policy != scheduled.identity(source.original.policy)
            or frames.source != source.identity or frames.witness != prepared_prefix.identity(witness)
            or frames.numerical_design != scheduled.identity(source.original.policy.factor_numerical_design)
            or causal.source != source.identity or causal.preparation != preparation_identity(history.arrays)
            or causal.numerical != preparation_identity(assessment) or causal.witness != prepared_prefix.identity(witness)
            or causal.frame_assessment != prepared_prefix.identity(frames) or causal.policy != scheduled.identity(source.original.policy)
            or causal.cutoff_tick != source.total_ticks or score.source != source.identity
            or score.preparation != preparation_identity(history.arrays) or score.original_protocol != scheduled.identity(protocol)
            or score.panels != tuple(panel.identity for panel in panels)
            or score.forecast != (mechanical.arrays.identity if responses.disposition == "COMPLETED" else None)):
        raise PermissionError("prepared source changes actual recipe, causal/frame/assay/control ancestry")
    expected = {"control.prepared." + source.source_id + "." + branch: (1 if view == "PRIMARY" else 2) * protocol.horizon_steps[-1]
        for branch, view, *_ in branch_census(protocol, panels)}
    if responses.disposition == "COMPLETED":
        if ({row.control_id for row in score.controls} != set(expected) or len(score.controls) != len(expected)
                or any(row.denominator_steps != expected[row.control_id] or row.tolerance != protocol.native_reference_tolerance
                    for row in score.controls) or score.disposition not in ("FINITE", "PARTIAL", "NATIVE_CROSSCHECK_FAILED")):
            raise PermissionError("prepared source thins actually exercised independent response controls")
    elif score.controls or score.numerical_pass or score.disposition != responses.disposition:
        raise PermissionError("prepared source nonuse invents exercised native response controls")
    return r.MatrixPreparedSourceControl(source=source.identity, root_id=source.root.root.root_id,
        group_id=source.root.root.independent_group_id, recipe=source.recipe.identity, initial=source.initial, provenance=source.provenance.identity,
        numerical=scheduled.identity(source.numerical_design), factor_numerical=scheduled.identity(source.original.policy.factor_numerical_design),
        instrument_sha256=r.instrument_signature(protocol), history=preparation_identity(history), assessment=preparation_identity(assessment),
        witness=prepared_prefix.identity(witness), frames=prepared_prefix.identity(frames), causal=prepared_prefix.identity(causal),
        mechanical=prepared_prefix.identity(mechanical), responses=prepared_prefix.identity(responses), score=prepared_prefix.identity(score),
        receipts=tuple(sorted({r.pin(value, "receipt_id") for value in receipts}, key=lambda value: value.object_id)),
        numerical_pass=assessment.numerical_pass, frame_controls_pass=frames.numerical_pass,
        frame_controls_violated=any(row.disposition == "VIOLATED" for row in frames.controls),
        response_controls_pass=score.numerical_pass, response_control_count=len(score.controls),
        causal_disposition=causal.disposition, response_disposition=responses.disposition)


def _read_development_controls(*, writer, locator):
    """Return the complete actual DEV control witness, including every nonuse."""
    programme, owner, is_revision, products, plan, entry_task, _ = _development_selection(writer, locator)
    sources = (programme.source_arms() if is_revision else tuple((None, source) for source in programme.sources.sources))
    controls = tuple(sorted((_prepared_control(writer, programme, owner, is_revision, products, plan, entry_task, source)
        for _, source in sources), key=lambda row: row.source.object_id))
    return programme, controls


@contextmanager
def _committed_e4_selections(writer, commitment, request, *, maximum_source_bytes, native_training_locator=None):
    """Keep actual whole C custody alive while using all original E4 phases."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import validate_request_programme_inputs
    from empirical_lawhood.infrastructure.matrix_completed_source import original_e3_commitment, original_e3_programme_inputs
    from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
    with authenticated_programme_inputs(writer=writer, commitment=commitment,
            maximum_source_bytes=maximum_source_bytes) as inputs, original_e3_programme_inputs(
                writer=writer, inputs=inputs, maximum_source_bytes=maximum_source_bytes) as e3_inputs:
        if request.input_commitments == original_e3_commitment(writer, inputs, commitment):
            validate_request_programme_inputs(request, e3_inputs)
            yield inputs
        else:
            from empirical_lawhood.infrastructure.matrix_retained_training import authenticated_retained_training_source
            with authenticated_retained_training_source(writer=writer, inputs=e3_inputs,
                    maximum_source_bytes=maximum_source_bytes) as (retained, original):
                if (retained.input_commitments != request.input_commitments
                        or retained.export_adoption.request != request.identity
                        or native_training_locator != retained.training_locator):
                    raise PermissionError('prepared source substitutes its exact retained TRAIN source lineage')
                validate_request_programme_inputs(request, original)
                yield inputs


def _future_source_selections(inputs):
    """Current source bindings over authenticated unchanged pre-TRAIN panels."""
    roles = (('CALIBRATION', 'e3.calibration'), ('EVALUATION', 'e3.confirmation'),
        ('TRANSFER_NEARBY', 'e6.nearby'), ('TRANSFER_SHIFTED', 'e6.shifted'))
    return tuple((role, inputs.phase(phase).responses) for role, phase in roles)


def _prepared_phases(inputs):
    return tuple((role, inputs.phase(role)) for role in (
        "e5.development", "e5.confirmation", "e6.nearby", "e6.shifted"))


def _e4_phases(inputs):
    return tuple((phase, inputs.phase("e4." + phase.lower()))
        for phase in ("CALIBRATION", "CONFIRMATION", "DEVELOPMENT"))


def _require_original_e4_scope(writer, inputs, programme, evidence, *, training_specification, training_request,current_access=None):
    """Original producer joins stay distinct from pre-acquisition mathematics."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedEntryEvidence
    if isinstance(evidence, (opportunity.MatrixSelectedOpportunityEvidence, MatrixSelectedEntryEvidence)):
        if programme.point_design.package.specification != inputs.scientific_design.e3:
            raise PermissionError("prepared source C changes the actual original E3 scientific specification")
        from .matrix_selected_e3_e4_runtime import authenticate_selected_e3_training_banks
        from .selected_prepared_access import _selected
        authenticate_selected_e3_training_banks(public=programme.point_design.package,
            upstream_products=_selected(evidence.upstream_products,current_access), training_specification=training_specification,
            training_request=training_request, writer=writer)
    else:
        from empirical_lawhood.api.selected_e4_native_runtime import development_product
        _, _, codecs = operation_catalog()
        original, _, bank = development_product(writer, evidence.revision_fit,
            "revision-fit", codecs, include_bank=True,read_access=None if current_access is None else current_access.development_access())
        selected = inputs.phase("e4.development")
        if (bank.reservation != selected.reservation or bank.specification != selected.native_specification
                or bank.response_selection != selected.responses
                or bank.provenances != (inputs.producing_provenance,)
                or bank.forecast_design.package.specification != inputs.scientific_design.e3
                or bank.forecast_design.criterion_record != inputs.scientific_design.training_protocol.mathematical_protocol
                or original.bank != bank.identity
                or evidence.original_e3_package != bank.forecast_design.package.original_package):
            raise PermissionError("prepared source C changes actual selected revision E3/E4 producers")


@dataclass(frozen=True, slots=True)
class PreparedSourceExposureFacts:
    """Authenticated runtime values for current CONF preparation, not authority."""
    request: train.NativeTrainingAcquisitionRequest
    acquisition: train.NativeTrainingAcquisitionSeal
    future_selections: tuple
    programme: object
    controls: tuple[r.MatrixPreparedSourceControl, ...]
    input_commitments: ObjectIdentity
    e4_phases: tuple
    prepared_phases: tuple
    producing_provenance: object
    effective_seeds: tuple[int, ...]
    group_ids: tuple[str, ...]
    coordinates: tuple
    future_source_selections: tuple = ()


@contextmanager
def prepared_source_exposure_facts(*, writer, locator, native_training_locator, input_commitments,
        maximum_source_bytes,current_access=None):
    """Authenticate complete C/TRAIN/DEV facts within one dependent lifetime."""
    specification, request, acquisition, future = _native_training_prerequisite(writer, native_training_locator)
    with _committed_e4_selections(writer, input_commitments, request,
            maximum_source_bytes=maximum_source_bytes, native_training_locator=native_training_locator) as inputs:
        yield _prepared_source_exposure_facts(writer=writer, locator=locator, request=request,
            acquisition=acquisition, future=future, inputs=inputs, training_specification=specification,current_access=current_access)


def _prepared_source_exposure_facts(*, writer, locator, request, acquisition, future, inputs, training_specification,current_access=None):
    """Use an already scoped C; never carry its resolved view out of the owner."""
    programme, owner, is_revision, products, plan, entry_task, evidence = _development_selection(writer, locator,current_access=current_access)
    source_rows = (programme.source_arms() if is_revision else tuple((None, source) for source in programme.sources.sources))
    controls = tuple(sorted((_prepared_control(writer, programme, owner, is_revision, products, plan, entry_task, source)
        for _, source in source_rows), key=lambda row: row.source.object_id))
    _require_original_e4_scope(writer, inputs, programme, evidence,
        training_specification=training_specification, training_request=request,current_access=current_access)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
        validate_committed_prepared_sources, validate_committed_prepared_panels,
    )
    prepared = _prepared_phases(inputs)
    validate_committed_prepared_sources(phase=programme.phase, sources=programme.sources,
        phases=prepared, producing_provenance=inputs.producing_provenance)
    validate_committed_prepared_panels(phase=programme.phase, assay=programme.assay,
        panels=programme.panels, selections=tuple((role, selected.responses) for role, selected in prepared))
    selections = _e4_phases(inputs)
    excluded = set(request.train_manifest.audit.census.effective_seed_exclusions) | set(request.future_manifest.audit.census.effective_seed_exclusions)
    excluded.update(seed for allocation in _allocations(programme) for seed in allocation.exposure.census.effective_seed_exclusions)
    groups, coordinates = set(), {}

    def include_source(root, coordinate):
        excluded.update(stream.effective_seed for stream in root.streams)
        groups.add(root.root.independent_group_id)
        if coordinates.setdefault(coordinate.coordinate_id, coordinate) != coordinate:
            raise PermissionError("prepared exposure supplement substitutes an original physical coordinate")

    for manifest in (request.train_manifest, request.future_manifest):
        declared = {scheduled.coordinate_identity(value): value for value in manifest.reservation.allocation.coordinates}
        for root in manifest.reservation.allocation.roots:
            if manifest is request.train_manifest or root.root.role.value in ("CALIBRATION", "CONFIRMATION"):
                include_source(root, declared[root.coordinate])
    excluded.update(stream.effective_seed for panel in request.panels for stream in panel.streams)
    excluded.update(stream.effective_seed for role, selection in future if role in ("CALIBRATION", "EVALUATION")
        for _, panels in selection.panels for panel in panels for stream in panel.streams)
    for _, phase in selections:
        selection, allocation = phase.responses, phase.reservation.allocation
        selection.validate_allocation(allocation)
        declared = {scheduled.coordinate_identity(value): value for value in allocation.coordinates}
        for root in allocation.roots:
            include_source(root, declared[root.coordinate])
        excluded.update(stream.effective_seed for _, panels in selection.panels
            for panel in panels for stream in panel.streams)
    for _, source in source_rows:
        include_source(source.root, source.coordinate)
    excluded.update(stream.effective_seed for _, panels in programme.panels for panel in panels for stream in panel.streams)
    return PreparedSourceExposureFacts(request, acquisition, future, programme, controls, inputs.commitments.identity, selections, prepared, inputs.producing_provenance,
        tuple(sorted(excluded)), tuple(sorted(groups)), tuple(coordinates[key] for key in sorted(coordinates)),
        _future_source_selections(inputs))


def _require_current_exposure_subset(original, current, *, effective_seeds, group_ids, coordinates):
    """Require conservative exclusions without asserting actual RNG use.

    The explicit current rejection set retains unused reservations separately
    classified in content-pinned external factual provenance.
    """
    before, after = original.census, current.census
    if before.mandatory_floor != after.mandatory_floor:
        raise PermissionError("prepared CONF changes its immutable mandatory exclusion floor")
    for name in ("effective_seed_exclusions", "exposed_independent_groups", "exposed_regimes", "exposed_artifact_sha256s",
            "constant_physical_exclusions", "scheduled_physical_exclusions"):
        if not set(getattr(before,name)) <= set(getattr(after,name)):
            raise PermissionError("prepared CONF removes or alters an immutable original exposure fact")
    selected_provenance={value.artifact_id:value for value in after.factual_provenance}
    if any(selected_provenance.get(value.artifact_id)!=value for value in before.factual_provenance):
        raise PermissionError("prepared CONF removes or alters original external factual provenance")
    selected = {value.coordinate_id: value for value in current.prior_scheduled_coordinates}
    if any(selected.get(value.coordinate_id) != value for value in (*original.prior_scheduled_coordinates, *coordinates)):
        raise PermissionError("prepared CONF omits or alters an actual selected-sequence physical coordinate")
    if (not set(effective_seeds).issubset(after.effective_seed_exclusions)
            or not set(group_ids).issubset(after.exposed_independent_groups)
            or not {MatrixScheduledPhysicalExclusion.from_coordinate(value) for value in coordinates}.issubset(
                after.scheduled_physical_exclusions)):
        raise PermissionError("prepared CONF omits required TRAIN/E3/E4/E5 reservation and exposure exclusions")


def certify_prepared_source_instrument(*, writer, locator, native_training_locator, bank, cutoff, record_id, maximum_source_bytes,current_access=None):
    _validate_prepared_source_certificate_bank(writer, bank)
    with prepared_source_exposure_facts(writer=writer, locator=locator, native_training_locator=native_training_locator,
            input_commitments=bank.input_commitments, maximum_source_bytes=maximum_source_bytes,current_access=current_access) as facts:
        return _prepared_source_certificate_from_facts(locator=locator, native_training_locator=native_training_locator,
            bank=bank, cutoff=cutoff, record_id=record_id, writer=writer, facts=facts)


def _validate_prepared_source_certificate_bank(writer, bank):
    """Keep the public bank and exact support checks before source reconstruction."""
    if type(bank) is not r.MatrixPreparedSourceBank:
        raise TypeError("prepared source requires its exact complete protected future bank")
    bank.__post_init__()
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import _authenticate_artifact
    for artifact, custody in bank.exposure_support:
        _authenticate_artifact(writer, artifact, custody)


def _prepared_source_certificate_from_facts(*, writer, locator, native_training_locator, bank, cutoff, record_id, facts):
    """Finish this invocation's authenticated facts; no cache or source authority."""
    request, acquisition, future = facts.request, facts.acquisition, facts.future_selections
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
        validate_committed_prepared_sources, validate_committed_prepared_panels,
    )
    if bank.input_commitments.record != facts.input_commitments:
        raise PermissionError("prepared source changes its actual original whole C publication identity")
    validate_committed_prepared_sources(phase=bank.phase, sources=bank.sources,
        phases=facts.prepared_phases, producing_provenance=facts.producing_provenance)
    validate_committed_prepared_panels(phase=bank.phase, assay=bank.assay,
        panels=bank.panels, selections=tuple((role, selected.responses) for role, selected in facts.prepared_phases))
    # The certificate below retains the original pre-TRAIN selector identities.
    # Only source matching uses the explicitly authenticated continued bindings.
    r.require_original_future_commitments(bank, request,
        getattr(facts, 'future_source_selections', ()) or future)
    if bank.phase == "E5_CONFIRMATION":
        _require_current_exposure_subset(request.future_manifest.audit, bank.audit,
            effective_seeds=facts.effective_seeds, group_ids=facts.group_ids, coordinates=facts.coordinates)
    elif bank.audit != request.future_manifest.audit:
        raise PermissionError("prepared transfer changes its exact original exposure audit")
    for publication, value in ((bank.reservation.publication, bank.reservation.allocation),
            (bank.specification.publication, bank.specification.selection), (bank.audit_publication, bank.audit)):
        authenticate_publication(writer, publication, value)
    originals = (bank.audit.census, *bank.audit.prior_scheduled_coordinates)
    for publication in bank.audit.prior_corpus:
        candidates = tuple(value for value in originals if (value.SCHEMA, value.fingerprint()) ==
            (publication.logical.payload_schema, publication.logical.content_sha256))
        if len(candidates) != 1:
            raise PermissionError("prepared source changes an actual original prior-corpus publication")
        authenticate_publication(writer, publication, candidates[0])
    reserved = {stream.effective_seed for root in request.future_manifest.reservation.allocation.roots for stream in root.streams}
    reserved.update(stream.effective_seed for _, selection in future for _, panels in selection.panels
        for panel in panels for stream in panel.streams)
    groups = tuple(sorted({row.group_id for row in facts.controls}))
    return r.MatrixPreparedInstrumentCertificate(record_id=record_id, locator=locator,
        native_training_locator=native_training_locator, native_training_request=request.identity,
        native_training_acquisition=acquisition.identity, original_future_reservation=scheduled.identity(request.future_manifest.reservation),
        development_programme=facts.programme.identity, input_commitments=facts.input_commitments,
        development_group_ids=groups, controls=facts.controls, excluded_effective_seeds=facts.effective_seeds,
        reserved_future_effective_seeds=tuple(sorted(reserved)), original_future_panels=tuple((role, selection.identity) for role, selection in future),
        future_bank=bank.identity, future_group_ids=bank.group_ids, cutoff=cutoff)


def authenticate_prepared_source_certificate(*, writer, certificate, bank, maximum_source_bytes,
        control_reader=None, original_input_access=None,current_access=None):
    """Reconstruct immutable scientific facts within the existing bounded lifetime."""
    if original_input_access is not None:
        from .prepared_source_access import authenticated_prepared_source_access
        from .selected_prepared_access import _ordinary
        with authenticated_prepared_source_access(scope=original_input_access,
                locator=certificate.native_training_locator) as access:
            with _ordinary(writer).read_context(before_member=access.require_original_member) as originals:
                authenticate_prepared_source_certificate(writer=originals, certificate=certificate, bank=bank,
                    maximum_source_bytes=maximum_source_bytes,current_access=access.current_access)
                originals.require_verification_snapshot()
            access.require_current()
        return
    from .current_result_custody import CurrentResultPlanReader
    from empirical_lawhood.kernel.decoding import decimal_context_key
    if type(certificate) is not r.MatrixPreparedInstrumentCertificate:
        raise TypeError("prepared source requires its actual complete DEV control certificate")
    certificate.__post_init__()
    if type(maximum_source_bytes) is not int or maximum_source_bytes < 1:
        raise ValueError("prepared source read requires an explicit current positive source byte ceiling")
    reader = control_reader
    if reader is not None:
        if type(reader) is not CurrentResultPlanReader or reader.writer.root is not writer.root:
            raise PermissionError("prepared source changes its original immutable verification lifetime")
        reader.writer.require_verification_snapshot()
        writer = reader.writer
    key = (certificate.locator.fingerprint(), certificate.native_training_locator.fingerprint(), certificate.record_id,
        certificate.cutoff.fingerprint(), bank.fingerprint(), maximum_source_bytes, decimal_context_key())
    cache = None if reader is None else getattr(reader, "_matrix_prepared_source_certificates", None)
    cached = None if cache is None else cache.get(key)
    from empirical_lawhood.api.matrix_finite_dt_source_runtime import _native_training_file_supports, _verify_file_supports
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    file_supports = ()
    expected = None if cached is None else cached[0]
    if cached is not None:
        file_supports = cached[1]
        _verify_file_supports(writer, file_supports)
    if expected is None:
        native_files = _native_training_file_supports(writer, certificate.native_training_locator,
            certificate.native_training_request)
        current_files = tuple((artifact, custody) for artifact, custody in bank.exposure_support
            if type(custody) is ExperimentFileInputBinding)
        file_supports = tuple(dict.fromkeys((*native_files, *current_files)))
        _verify_file_supports(writer, file_supports)
        expected = certify_prepared_source_instrument(writer=writer, locator=certificate.locator,
            native_training_locator=certificate.native_training_locator, bank=bank, cutoff=certificate.cutoff, record_id=certificate.record_id, maximum_source_bytes=maximum_source_bytes,
            **({} if current_access is None else {"current_access":current_access}))
        if reader is not None:
            if cache is None:
                cache = reader._matrix_prepared_source_certificates = {}
            if len(cache) >= 2:
                cache.pop(next(iter(cache)))
            cache[key] = (expected, file_supports)
    if expected != certificate:
        raise PermissionError("prepared source refuses a caller-asserted, altered or incomplete DEV certificate")
    _verify_file_supports(writer, file_supports)
    if reader is not None:
        reader.writer.require_verification_snapshot()


class MatrixPreparedSourceRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self, supplier, *, custody):
        from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
        if type(custody) is not CurrentIssuedTaskCustody:
            raise TypeError("prepared source requires exact shared current issued task custody")
        self.supplier, self.custody = supplier, custody

    def resolve_input(self, spec):
        return self.supplier.resolve_input(spec)

    def prepare_matrix_prepared_source_gate(self, context, runner):
        with self.custody.preparation_scope():
            return self._prepare_matrix_prepared_source_gate(context, runner)

    def _prepare_matrix_prepared_source_gate(self, context, runner):
        from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as bindings
        if type(runner) is not bindings.MatrixPreparedSourceGateWorker:
            raise PermissionError("prepared source refuses a foreign prepared worker")
        _, _, task = self.custody.current_task(context, runner)
        from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
        science_edges = validated_task_scientific_input_edges(task)
        _, manifests = self.custody.task_inputs(context, task)
        specifications = {value.logical_artifact_id: value for value in task.external_inputs}
        if len(specifications) != len(task.external_inputs):
            raise PermissionError("prepared source aliases its actual frozen input census")
        manifest = manifests[context.config.artifact_id]
        expected = specifications[context.config.artifact_id]
        config = self.custody.control_record(manifest, r.MatrixPreparedSourceGateConfig, manifest.materialization.size_bytes,
            expected_outcome_access=expected.expected_outcome_access,
            expected_visibility_ceiling=expected.expected_visibility_ceiling)
        if config.gate_kind is not runner.kind or config.phase != runner.phase or config.resource_budget != context.resource_budget:
            raise PermissionError("prepared source changes its actual selected phase, gate or resources")
        records = {}
        for name, kind in bindings.input_kinds(runner.phase).items():
            edges = tuple(edge for edge in science_edges if edge.consumer_input_id == name)
            if len(edges) != 1 or edges[0].producer_task_id is not None:
                raise PermissionError("prepared source changes actual external operand ownership")
            manifest = manifests.get(edges[0].operational_logical_artifact_id)
            if manifest is None or manifest.logical.payload_schema != kind.SCHEMA:
                raise PermissionError("prepared source substitutes an original actual scientific operand")
            read = self.custody.control_record if name in ("numerical", "cutoff") else self.custody.immutable_control_record
            expected = specifications[edges[0].operational_logical_artifact_id]
            records[name] = read(manifest, kind, manifest.materialization.size_bytes,
                expected_outcome_access=expected.expected_outcome_access,
                expected_visibility_ceiling=expected.expected_visibility_ceiling)
        if len(science_edges) != len(records):
            raise PermissionError("prepared source changes its complete original gate input census")
        r.validate_gate_operands(config, records["scope"], records)
        authenticate_prepared_source_certificate(writer=self.custody.writer, certificate=records["certificate"],
            bank=records["bank"], maximum_source_bytes=context.resource_budget.source_scan_bytes,
            control_reader=self.custody._control_reader, original_input_access=self.custody.original_input_access)
        return runner.with_prepared_scope(bindings.PreparedMatrixSourceGateScope(context.run_id, context.task_id,
            config.identity, records["scope"].identity, records["certificate"].identity))


def bind_prepared_source_handoff(handoff, *, writer, reveal_authority_id=None, original_input_access=None):
    from dataclasses import replace
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id,
        original_input_access=original_input_access)
    ports = []
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("prepared source changes the exact installed public input port")
        supplier = MatrixPreparedSourceRuntimeInputSupplier(platform.port.supplier, custody=custody)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))


def _validate_consumer_programme(bank, consumer_programme):
    """Bind source certification to the exact downstream acquisition contract."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import (
        MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme,
    )
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionPreparedProgramme
    if type(bank) is not r.MatrixPreparedSourceBank or type(consumer_programme) not in (
            MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme, MatrixRevisionPreparedProgramme):
        raise TypeError("prepared source requires its actual selected protected consumer programme")
    bank.__post_init__(); consumer_programme.__post_init__()
    if (consumer_programme.phase != bank.phase or consumer_programme.sources != bank.sources
            or consumer_programme.assay != bank.assay or consumer_programme.panels != bank.panels):
        raise PermissionError("prepared source consumer substitutes its actual sources, assay or future panels")


def authenticate_installed_prepared_source_prerequisite(*, writer, result, pipeline, publications, read_scope, consumer_programme=None):
    """Actual protected consumers replay the original prepared-control owner."""
    from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as bindings
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    supplied = dict(publications)
    scope_pins = {value for gate in result.gate_evidence for value in gate.input_operands
        if value.object_schema == r.MatrixPreparedSourceScope.SCHEMA}
    if len(scope_pins) != 1:
        raise PermissionError("prepared source omits its one exact original scope")
    reader = None if read_scope is None else read_scope.plan_reader

    def original(reference, kind):
        publication = supplied.get(reference)
        if publication is None or (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION):
            raise PermissionError("prepared source omits an exact published original operand")
        authenticate_publication(writer, publication)
        manifest = writer.read_manifest(publication.materialization.relative_path)
        if (manifest.logical, manifest.materialization) != (publication.logical, publication.materialization):
            raise PermissionError("prepared source changes actual original publication custody")
        if reader is None or kind in (MatrixParameterNumericalDesign, InformationCutoff):
            value = CurrentIssuedTaskCustody(writer=writer).control_record(manifest, kind, manifest.materialization.size_bytes)
        else:
            value = reader.read_control(manifest, kind, manifest.materialization.size_bytes)
        actual = r.pin(value, "cutoff_id") if hasattr(value, "cutoff_id") else scheduled.identity(value) if not hasattr(value, "identity") else value.identity
        if actual != reference:
            raise PermissionError("prepared source changes original operand identifier or bytes")
        return value

    scope = original(next(iter(scope_pins)), r.MatrixPreparedSourceScope)
    bank = original(scope.bank, r.MatrixPreparedSourceBank)
    if consumer_programme is not None:
        _validate_consumer_programme(bank, consumer_programme)
    declared = {bindings.gate_declaration(kind, bank.phase).capability_key: kind for kind in r.GATES}
    if len(result.gate_evidence) != len(declared) or {gate.method.capability_key for gate in result.gate_evidence} != set(declared):
        raise PermissionError("prepared source mixes or omits installed independent predicates")
    pins = {"scope": scope.identity, "bank": scope.bank, "source": scope.source_identity, "preparation": scope.preparation,
        "assay": scope.assay, "numerical": scope.numerical, "original-reservation": scope.original_future_reservation,
        "cutoff": r.pin(scope.cutoff, "cutoff_id"), "certificate": scope.certificate}
    records = {name: scope if name == "scope" else bank if name == "bank" else original(pins[name], kind)
        for name, kind in bindings.input_kinds(bank.phase).items()}
    for gate in result.gate_evidence:
        kind = declared[gate.method.capability_key]
        config, = (value for value in r.gate_configs(scope) if value.gate_kind is kind)
        declaration = bindings.gate_declaration(kind, bank.phase)
        if ((gate.method.capability_version, gate.method.implementation_sha256) !=
                (declaration.capability_version, declaration.manifest().implementation_sha256)
                or r.validate_gate_operands(config, scope, records) != gate):
            raise PermissionError("prepared source substitutes an actual independently installed gate")
    if (scope.profile != pipeline.pipeline_config.profile or scope.pipeline_receipt != pipeline.receipt
            or scope.publication != scope.recovery or scope.recovery != pipeline.pipeline_config.execution_evidence.recovery):
        raise PermissionError("prepared source substitutes its original pipeline or semantic verification")
    verification = supplied.get(scope.recovery)
    if verification is None:
        raise PermissionError("prepared source omits its exact semantic verification publication")
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import authenticate_installed_finite_dt_source_materialization
    authenticate_installed_finite_dt_source_materialization(writer=writer, programme=bank, bank=bank,
        pipeline=pipeline, verification_publication=verification)
    authenticate_prepared_source_certificate(writer=writer, certificate=records["certificate"], bank=bank, maximum_source_bytes=scope.resource_budget.source_scan_bytes, control_reader=reader)


def _prepared_gate_product_context(*, selection, product_custody, read_scope, package, execution_plan):
    """Join an independently read source selection to its actual owning packet."""
    from .current_task_custody import CurrentIssuedTaskCustody
    from .prepared_source_access import PreparedSourceOriginalInputAccess
    from .recursive_qualified_parents import _require_owned_product_binding
    from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
    if (type(selection) is not domain.MatrixPreparedSourceQualificationSelection
            or type(product_custody) is not CurrentIssuedTaskCustody
            or type(product_custody.original_input_access) is not PreparedSourceOriginalInputAccess):
        raise PermissionError("prepared gate replay requires its exact authenticated source selection and custody")
    _require_owned_product_binding(product_custody, read_scope, package, execution_plan)
    access = product_custody.original_input_access
    selection.__post_init__()
    if (type(access.issued_specification) is not domain.MatrixPreparedSourceQualificationSpecification
            or access.issued_specification.selection != selection.identity or not access.parents
            or not any((logical.payload_schema, logical.content_sha256, physical.size_bytes) ==
                (selection.SCHEMA, selection.fingerprint(), len(selection.canonical_bytes()))
                and tuple(parent for parent in logical.lineage_parents
                    if parent.identity in {value.identity for value in access.parents}) == access.parents
                for logical, physical in access.issued_members)):
        raise PermissionError("prepared gate replay substitutes its actual selected packet or complete original parents")
    if access.source_scope is not None and access.source_scope != selection.scope:
        raise PermissionError("prepared gate replay changes its actual selected scientific scope")
    access.require_current()
    # Cold bootstrap is locator-only. Only this independently authenticated
    # selected body supplies the immutable gate-config projection context.
    return replace(access, source_scope=selection.scope)


def validate_prepared_gate_product(*, selection, binding, package, execution_plan, receipt, logical,
        read_scope, product_custody):
    """Derive one output pair from exact frozen config/operands and declaration.

    The caller has already replayed source/DEV/TRAIN scientific prerequisites.
    This metadata check never grants access from a claimed label or parent pin.
    """
    from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as bindings
    from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
    from empirical_lawhood.kernel.evidence import inherited_visibility
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, derived_outcome_access, lineage_parent_sort_key
    from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from .current_task_custody import _require_provider_input_manifest

    access = _prepared_gate_product_context(selection=selection, product_custody=product_custody,
        read_scope=read_scope, package=package, execution_plan=execution_plan)
    task = read_scope.plan_reader.execution_task(execution_plan=execution_plan, task_id=binding.task_id)
    if task is None or receipt.task_id != task.task_id or receipt.run_id != package.run_plan_id:
        raise PermissionError("prepared gate replay changes its exact winning producer")
    science = validated_task_scientific_input_edges(task)
    configs = tuple(value for value in r.gate_configs(selection.scope)
        if (value.config_id, value.SCHEMA, value.fingerprint()) == (task.capability.config.config_id,
            task.capability.config.config_schema, task.capability.config.content_sha256))
    if len(configs) != 1:
        raise PermissionError("prepared gate replay changes its actual frozen configuration")
    config, = configs
    declaration = bindings.gate_declaration(config.gate_kind, selection.bank.phase)
    manifest = declaration.manifest()
    if (task.stage is not declaration.stage or task.capability.capability_key != manifest.capability_key
            or task.capability.capability_version != manifest.capability_version
            or task.capability_implementation_sha256 != manifest.implementation_sha256
            or task.capability.requested_outcome_access is not declaration.outcome_access
            or task.capability.required_permissions != manifest.permissions or task.dependency_task_ids
            or binding.scope_output_schema_ids or binding.additional_output_schema_ids):
        raise PermissionError("prepared gate replay substitutes its installed declaration or actual input ownership")
    records = domain.operands(selection)
    expected_product = r.validate_gate_operands(config, selection.scope, records)
    if (binding.record != r.pin(expected_product, "evidence_id") or binding.record_id_field != "evidence_id"
            or logical.content_sha256 != expected_product.fingerprint()):
        raise PermissionError("prepared gate replay changes its actual scientific product")
    if (len(science) != len(records) or {edge.consumer_input_id for edge in science} != set(records)
            or any(edge.producer_task_id is not None for edge in science)):
        raise PermissionError("prepared gate replay changes its complete scientific input census")
    specs = {value.logical_artifact_id: value for value in task.external_inputs}
    if len(specs) != len(task.external_inputs) or len(specs) != len(records) + 1:
        raise PermissionError("prepared gate replay aliases its complete config and operand census")
    selected = [(task.capability.config.artifact_id, config, True)]
    selected.extend((edge.operational_logical_artifact_id, records[edge.consumer_input_id], False) for edge in science)
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_experiment import operand_access_from_authoring
    operand_pairs = operand_access_from_authoring(operands=records, authoring=selection.authoring)
    inputs = []
    writer = read_scope.plan_reader.writer
    for logical_id, record, is_config in selected:
        expected = specs.get(logical_id)
        if (expected is None or (expected.expected_payload_schema, expected.expected_content_sha256,
                expected.expected_media_type) != (record.SCHEMA, record.fingerprint(), "application/json")
                or expected.expected_size_bytes not in (None, len(record.canonical_bytes()))):
            raise PermissionError("prepared gate replay substitutes its exact canonical config or scientific operand")
        relative, _, _ = provider_input_location(writer, binding.run_id, logical_id)
        actual = writer.read_manifest(relative)
        _require_provider_input_manifest(writer, binding.run_id, expected, actual,
            authenticated_size_bytes=len(record.canonical_bytes()))
        # The retained reader independently admitted these exact facts from
        # successful receipts/full input lineage before any body verification.
        product_custody.require_input_member(actual)
        parents = access.record_parents(record)
        selected_parents = tuple(parent for parent in actual.logical.lineage_parents
            if parent.identity in {value.identity for value in access.parents})
        if selected_parents != parents or parents and parents != access.parents:
            raise PermissionError("prepared gate replay changes its complete actual original parent census")
        if is_config:
            from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
            declared_pair = produced_access(declared_access=declaration.outcome_access,
                declared_visibility=declaration.visibility_ceiling, parents=parents)
        else:
            declared_pair = operand_pairs[next(name for name, value in records.items() if value is record)]
        if (actual.logical.outcome_access, actual.logical.visibility_ceiling) != declared_pair:
            raise PermissionError("prepared gate replay changes an exact frozen input custody pair")
        inputs.append(actual.logical)
    expected_access = derived_outcome_access(declaration.outcome_access, *(value.outcome_access for value in inputs))
    expected_visibility = inherited_visibility(tuple(value.visibility_ceiling for value in inputs), expected_access)
    parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(value.logical_artifact_id, value),
        value.visibility_ceiling, value.outcome_access) for value in inputs), key=lineage_parent_sort_key))
    if (logical.outcome_access is not expected_access or logical.visibility_ceiling is not expected_visibility
            or logical.lineage_parents != parents or len(task.outputs) != 1
            or (task.outputs[0].logical_artifact_id, task.outputs[0].outcome_access, task.outputs[0].visibility_ceiling) !=
                (logical.logical_artifact_id, expected_access, expected_visibility)):
        raise PermissionError("prepared gate replay drops exact inherited output custody or full input ancestry")
    access.require_current()


def authenticate_owning_prepared_source_prerequisite(*, writer, selection, result, pipeline, read_scope, product_custody):
    """Current owning read only; downstream consumers need their own live context."""
    from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
    package, plan = product_custody._current_package_plan
    access = _prepared_gate_product_context(selection=selection, product_custody=product_custody,
        read_scope=read_scope, package=package, execution_plan=plan)
    from .matrix_prepared_source_experiment import pipeline_evidence
    expected_pipeline, expected_result = pipeline_evidence(selection)
    if pipeline != expected_pipeline or result != expected_result:
        raise PermissionError("prepared source replay changes its exact independently authenticated selection")
    records = domain.operands(selection)
    expected = tuple(sorted((r.validate_gate_operands(config, selection.scope, records)
        for config in r.gate_configs(selection.scope)), key=lambda value: value.evidence_id))
    if result.gate_evidence != expected:
        raise PermissionError("prepared source replay changes its complete installed gate census")
    authenticate_prepared_source_certificate(writer=writer, certificate=selection.certificate,
        bank=selection.bank, maximum_source_bytes=selection.scope.resource_budget.source_scan_bytes,
        control_reader=read_scope.plan_reader, original_input_access=access)
    access.require_current()


def validate_prepared_terminal_product(*, selection, config, product, declaration, binding, package,
        execution_plan, receipt, logical, read_scope, product_custody):
    """Preserve the two pure terminal products while guarding their full closure."""
    from .current_task_custody import _require_provider_input_manifest
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
    access = _prepared_gate_product_context(selection=selection, product_custody=product_custody,
        read_scope=read_scope, package=package, execution_plan=execution_plan)
    task = read_scope.plan_reader.execution_task(execution_plan=execution_plan, task_id=binding.task_id)
    if (task is None or validated_task_scientific_input_edges(task) or len(task.external_inputs) != 1
            or task.stage is not declaration.stage
            or task.capability.requested_outcome_access is not declaration.outcome_access
            or task.capability.required_permissions != declaration.manifest().permissions
            or receipt.task_id != task.task_id or receipt.run_id != package.run_plan_id
            or logical.content_sha256 != product.fingerprint()):
        raise PermissionError("prepared terminal replay changes its exact pure configuration or declaration")
    spec, = task.external_inputs
    if (spec.logical_artifact_id != task.capability.config.artifact_id
            or (spec.expected_payload_schema, spec.expected_content_sha256, spec.expected_media_type,
                spec.expected_outcome_access, spec.expected_visibility_ceiling) != (config.SCHEMA,
                config.fingerprint(), "application/json", declaration.outcome_access, declaration.visibility_ceiling)
            or access.record_parents(config)):
        raise PermissionError("prepared terminal replay substitutes its intrinsic original config")
    writer = read_scope.plan_reader.writer
    relative, _, _ = provider_input_location(writer, binding.run_id, spec.logical_artifact_id)
    actual = writer.read_manifest(relative)
    _require_provider_input_manifest(writer, binding.run_id, spec, actual,
        authenticated_size_bytes=len(config.canonical_bytes()))
    product_custody.require_input_member(actual)
    expected_parent = ArtifactLineageParent(ObjectIdentity.from_record(actual.logical.logical_artifact_id, actual.logical),
        actual.logical.visibility_ceiling, actual.logical.outcome_access)
    if (actual.logical.lineage_parents or logical.lineage_parents != (expected_parent,)
            or logical.outcome_access is not declaration.outcome_access
            or logical.visibility_ceiling is not declaration.visibility_ceiling):
        raise PermissionError("prepared terminal replay changes its exact blind product custody")
    access.require_current()
