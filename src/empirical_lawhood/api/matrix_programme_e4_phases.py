# SPDX-License-Identifier: MPL-2.0
"""C-backed E4 projections over actual ordinary source and phase readers.

All populations come from C, all mathematical choices from D. Later entry,
issue, reveal and produced-input qualifications remain genuine prerequisites.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_researcher_programme.e4_operations import MatrixProgrammeE4Access
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes

from .matrix_programme_projection import MatrixProgrammePrerequisite


def _namespace(context, phase):
    return context.namespace + '.' + phase.replace('-', '.')


def _operations(context):
    operations = context.plan.specification.operations.e4
    operations.__post_init__()
    if operations.protected_resources.controls.maximum_parallel_tasks != context.execution.workers:
        raise ValueError('programme E4 controls differ from its actual selected worker count')
    return operations


def _source_request(context, phase, original):
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import (
        MatrixFiniteDtSourceAssemblyRequest, MatrixFiniteDtRetainedE3AssemblyRequest)
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection
    source = context.plan.specification.operations.source_metadata
    if source.operational_resources.controls.maximum_parallel_tasks != context.execution.workers:
        raise ValueError('programme source controls differ from the actual worker selection')
    values = source.request_values()
    values['scratch_namespace'] = source.scratch_namespace + '.' + phase.replace('-', '.')
    kind = (MatrixFiniteDtRetainedE3AssemblyRequest if original.original_preparation.record.object_schema in (
        ConfiguredE3ContinuedPreparationSelection.SCHEMA, ConfiguredE3UnfinishedPreparationSelection.SCHEMA, ConfiguredE3ClosedPreparationSelection.SCHEMA)
        else MatrixFiniteDtSourceAssemblyRequest)
    return kind('request.' + _namespace(context, phase),
        _namespace(context, phase), context.plan.specification.input_commitments,
        original.original_e3, original.original_preparation, original.original_assay,
        original.products, 'CONFIRMATION' if phase in ('e4.source-conf', 'e4.confirmation') else 'CALIBRATION',
        context.native_training_locator(), **values)


def _banks(context, phase, original):
    from .matrix_programme_e4_inputs import published_programme_e4_inputs
    return published_programme_e4_inputs(request=_source_request(context, phase, original),
        project_root=context.service.project_root, artifact_writer=context.writer,
        metadata_directory=context.metadata_directory(phase) / 'original-banks', execution=context.execution)


def _template_files(context, phase, bank, original):
    """Copy only C's exact pre-outcome template bytes, never a future result."""
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
    artifacts = {protocol.templates.array_artifact.artifact_id: protocol.templates.array_artifact
        for protocol in bank.response_selection.protocols}
    publications = {value.logical.logical_artifact_id: value
        for value in bank.response_selection.template_publications}
    rows = []
    budget = context.plan.specification.operations.metadata_budget
    if sum(value.size_bytes for value in artifacts.values()) > min(budget.output_bytes, budget.memory_bytes):
        raise ValueError('programme E4 original templates exceed the selected metadata budget')
    for name in sorted(artifacts):
        artifact, publication = artifacts[name], publications[name]
        manifest = context.writer.read_manifest(publication.materialization.relative_path)
        context.writer.verify_manifest(manifest)
        if (manifest.logical, manifest.materialization) != (publication.logical, publication.materialization):
            raise PermissionError('programme E4 changes the original C template publication')
        raw = read_bounded_bytes(context.writer.root.resolve(publication.materialization.relative_path, for_write=False),
            maximum_bytes=artifact.size_bytes)
        if (len(raw), sha256(raw).hexdigest()) != (artifact.size_bytes, artifact.sha256):
            raise PermissionError('programme E4 changes the original C template bytes')
        filename = 'template.' + artifact.fingerprint() + '.npz'
        relative = (context.metadata_directory(phase) / 'original-inputs' / filename).relative_to(
            context.writer.root.contract.canonical_path).as_posix()
        logical = publication.logical
        original.require_current()
        context.writer.write(ArtifactWriteRequest(artifact.artifact_id, relative, artifact.payload_schema,
            logical.profile, artifact.media_type, _namespace(context, phase), str(Path(relative).parent),
            raw, logical.visibility_ceiling, logical.parent_visibility_ceilings, logical.outcome_access,
            lineage_parents=logical.lineage_parents))
        rows.append(ExperimentFileInputBinding('external.selected-e4-array.' + artifact.fingerprint(),
            artifact, '1.0.0', filename, artifact.size_bytes))
    original.require_current()
    return tuple(rows)


def _development(context, phase, original):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4ExperimentSpecification
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence
    from .matrix_programme_e4_inputs import original_e3_lineage
    from .domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    operations = _operations(context)
    with _banks(context, phase, original) as current:
        bank, programme = dict(current.banks)['DEVELOPMENT'], dict(current.programmes)['DEVELOPMENT']
        parents = selected_produced_input_parents(context.writer, originals=original.products)
        evidence = SelectedE3E4Evidence('evidence.' + _namespace(context, phase), programme.identity,
            original.products, parents)
        specification = SelectedE3E4ExperimentSpecification('experiment.' + _namespace(context, phase),
            programme.identity, bank.identity, evidence.identity,
            ObjectIdentity.from_record(operations.campaign.campaign_id, operations.campaign),
            context.design.e4_structure, operations.structural_resources)
        files = _template_files(context, phase, bank, original)
        return context.derive(phase, specification,
            {'programme': programme, 'bank': bank, 'evidence': evidence,
                'campaign': operations.campaign, 'resources': operations.development_resources}, files=files, sibling_selector=True,
            lineage_parents=original_e3_lineage(original_e3=original.original_e3), require_current=original.require_current)


def _revision(context, phase, original):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import allocation
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4RevisionExperimentSpecification
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_revision_transition import (
        SelectedE4RevisionAcquisitionSource, SelectedE4RevisionAcquisitionSpecification)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import bind_group_fold_slots
    from .matrix_programme_e4_inputs import original_e3_lineage
    operations = _operations(context)
    actual = context.method_inputs('e4.development')
    programme, bank = actual.programme, actual.bank
    if programme.bank != bank.identity or bank.forecast_design.package != original.public:
        raise PermissionError('programme revision changes its actual completed original E4 DEV population or E3 account')
    choices = context.design.e4_revision
    folds = bind_group_fold_slots(programme, choices.fold_slots, choices.fold_count)
    revision = SelectedE4RevisionExperimentSpecification('revision.' + _namespace(context, phase),
        programme.identity, choices.target, choices.trigger, folds, choices.fold_count,
        choices.maximum_fit_calls, choices.revision_candidates, choices.baseline_candidates,
        choices.revision_tie_order, choices.baseline_tie_order, choices.matched_selection)
    specification = SelectedE4RevisionAcquisitionSpecification('experiment.' + _namespace(context, phase), revision)
    source = SelectedE4RevisionAcquisitionSource('source.' + _namespace(context, phase),
        context.child_directory('e4.development').relative_to(context.writer.root.contract.canonical_path).as_posix(), False)
    resources = replace(operations.method_resources,
        record_id='resources.' + _namespace(context, phase) + '.methods',
        phase_budgets=tuple(row for row in operations.method_resources.phase_budgets if row[0] in ('revision-fit', 'revision-freeze')))
    return context.derive(phase, specification, {'allocation': allocation(programme),
        'campaign': operations.campaign, 'source': source, 'resources': resources},
        lineage_parents=original_e3_lineage(original_e3=original.original_e3), require_current=original.require_current)


def _source_qualification(context, phase):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4SourceQualification
    from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
    from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationSpec, ScientificSourceQualificationResult
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    source_phase = 'e4.source-cal' if phase == 'e4.calibration' else 'e4.source-conf'
    from .matrix_programme_decisions import source_assessment
    report = source_assessment(context, source_phase)
    def decode(value, kind):
        return decode_canonical_bytes(canonical_json_document_bytes(value), kind,
            maximum_bytes=context.plan.specification.operations.metadata_budget.source_scan_bytes)
    if report.get('scientific_completion') != 'COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT':
        raise MatrixProgrammePrerequisite(phase, 'ACTUAL_SOURCE_ASSESSMENT_REQUIRED',
            'Complete and authenticate the original finite-dt source closeout before protected E4 entry.')
    return SelectedE4SourceQualification('qualification.' + _namespace(context, phase),
        decode(report['qualification_specification'], ScientificSourceQualificationSpec),
        decode(report['qualification_result'], ScientificSourceQualificationResult),
        decode(report['pipeline_evidence'], MatrixSourcePipelineEvidence),
        tuple(decode(value, RecursivePriorExecutionBinding) for value in report['prior_executions']),
        tuple((decode(pin, ObjectIdentity), decode(publication, ArtifactWriteResult))
            for pin, publication in report['publications']))


def _calibration_product(context):
    """Construct a locator only inside the actual CAL assessment reader."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_preparation import ASSESSMENT_COMPONENT_ID
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    from .selected_e4_native_read import _read_selected_e4_component
    selected, _, authority, _, run, _ = context.authority('e4.calibration', ASSESSMENT_COMPONENT_ID)
    def consume(*, writer, package, plan, entry, receipts, products, reveal):
        rows = tuple((value, receipt, logical) for value, receipt, logical in products
            if type(value) is science.SelectedE4Calibration)
        if len(rows) != 1:
            raise PermissionError('programme CONF requires the unique actual original E4 CAL product')
        value, receipt, logical = rows[0]
        prior = RecursivePriorExecutionBinding('binding.' + value.fingerprint(),
            ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
            ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority),
            ObjectIdentity.from_record(package.package_id, package),
            ObjectIdentity.from_record(plan.execution_plan_id, plan), run.run_plan_id, receipt.task_id,
            ObjectIdentity.from_record(receipt.receipt_id, receipt), logical.logical_artifact_id, value.identity,
            record_id_field='record_id')
        return MatrixSelectedOriginalProduct(prior, ObjectIdentity.from_record(reveal.authority_id, reveal))
    return _read_selected_e4_component(selected=selected, artifact_writer=context.writer,
        run_id=run.run_plan_id, reveal_authority_id=authority.reveal_authority_id, consume_tail=consume)


def _protected(context, phase, original):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_declarative as domain
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import operations_for_programme
    from .matrix_programme_e4_inputs import original_e3_lineage
    from .matrix_researcher_programme_e4_lineage import programme_revision_products
    from .domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    access = None if context.operation is None else context.operation.access_for(phase)
    if type(access) is not MatrixProgrammeE4Access:
        raise MatrixProgrammePrerequisite(phase, 'ACTUAL_E4_ENTRY_SELECTION_REQUIRED',
            'Select the actual prospective root, entry and formal source inventory for ' + phase + '.')
    access.__post_init__()
    operations = _operations(context)
    nomination, frozen, decision = programme_revision_products(context)
    population = 'CALIBRATION' if phase == 'e4.calibration' else 'CONFIRMATION'
    with _banks(context, phase, original) as current:
        banks, programmes = dict(current.banks), dict(current.programmes)
        bank, programme = banks[population], programmes[population]
        publication, = (value for value in current.publications
            if (value.logical.payload_schema, value.logical.content_sha256) == (bank.SCHEMA, bank.fingerprint()))
        source = _source_qualification(context, phase)
        resources = replace(operations.method_resources,
            record_id='resources.' + _namespace(context, phase) + '.methods',
            phase_budgets=tuple(row for row in operations.method_resources.phase_budgets
                if row[0] in operations_for_programme(programme)))
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_bindings import PHASES
        required = {*PHASES, 'phase-collect', *operations_for_programme(programme)}
        protected_resources = replace(operations.protected_resources,
            record_id='resources.' + _namespace(context, phase) + '.protected',
            source_request_limits=tuple(row for row in operations.protected_resources.source_request_limits if row[0] in required))
        if set(dict(protected_resources.source_request_limits)) != required:
            raise ValueError('programme E4 omits an actual selected phase source-request budget')
        calibration = _calibration_product(context) if population == 'CONFIRMATION' and decision.fit_available else None
        parents = selected_produced_input_parents(context.writer,
            originals=(*original.products, *((calibration,) if calibration is not None else ())),
            development=(nomination, frozen))
        request = domain.SelectedE4DeclarativeRequest('request.' + _namespace(context, phase),
            programme.programme_id, context.child_directory(phase).relative_to(context.writer.root.contract.canonical_path).as_posix(),
            publication, source, original.products, nomination, frozen, calibration,
            programmes['CALIBRATION'].programme_id if population == 'CONFIRMATION' else None,
            access.root, access.entry, access.formal_methods, access.formal_source_inventory,
            operations.native_budgets, resources, protected_resources,
            context.design.e4_calibration_alpha if population == 'CALIBRATION' else None,
            context.design.e4_nomination if population == 'CONFIRMATION' else None,
            context.design.e4_factorial if population == 'CONFIRMATION' else None,
            context.design.e4_structure, operations.structural_resources, parents)
        specification = domain.SelectedE4DeclarativeSpecification('experiment.' + _namespace(context, phase),
            bank.identity, None, population, bank.design.group_count, bank.design.cases_per_group,
            'Assess every originally assigned ' + population + ' group under the frozen D scientific design.')
        actual_development = context.method_inputs('e4.development')
        secondary = actual_development.secondary_readout
        if secondary is None:
            raise MatrixProgrammePrerequisite(phase, 'ORIGINAL_E4_SECONDARY_TARGET_REQUIRED',
                'Select the actual early target publication from the original DEV inputs.')
        secondary.validate_target(context.design.e4_structure.secondary_target)
        records = {'request': request, 'bank': bank, 'secondary_readout': secondary}
        if population == 'CONFIRMATION':
            records['calibration_bank'] = banks['CALIBRATION']
        return context.derive(phase, specification, records, sibling_selector=True,
            lineage_parents=original_e3_lineage(original_e3=original.original_e3), require_current=original.require_current)


def project_e4_phase(context, phase):
    with context.e3_originals(publish=True) as original:
        if phase == 'e4.development':
            return _development(context, phase, original)
        if phase == 'e4.revision':
            return _revision(context, phase, original)
        if phase in ('e4.source-cal', 'e4.source-conf'):
            from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import (
                MatrixFiniteDtSourceAssemblySpecification, MatrixFiniteDtRetainedE3AssemblySpecification,
                MatrixFiniteDtRetainedE3AssemblyRequest)
            from .matrix_programme_e4_inputs import original_e3_lineage
            request = _source_request(context, phase, original)
            kind = (MatrixFiniteDtRetainedE3AssemblySpecification if type(request) is MatrixFiniteDtRetainedE3AssemblyRequest
                else MatrixFiniteDtSourceAssemblySpecification)
            specification = kind('experiment.' + _namespace(context, phase), request.identity)
            return context.derive(phase, specification, {'request': request}, output_name='sources.json',
                lineage_parents=original_e3_lineage(original_e3=original.original_e3), require_current=original.require_current)
        if phase in ('e4.calibration', 'e4.confirmation'):
            return _protected(context, phase, original)
    raise ValueError('unsupported actual E4 programme phase')


def programme_e4_request(context, phase, *, include_collection=True):
    """Select real issued components; derive collection from actual wave reads."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as domain
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as records
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from .selected_e4_programme_service import (
        SelectedE4ComponentRequest, SelectedE4ProgrammeRequest, SelectedE4ProgrammeService, _locator)
    plan = context.method_inputs(phase).plan
    if type(plan) is not domain.SelectedE4ProtectedProgrammePlan:
        raise MatrixProgrammePrerequisite(phase, 'ACTUAL_E4_PLAN_REQUIRED', 'Derive the actual ordinary E4 plan before selecting its issued components.')
    components = []
    for component in plan.component_ids:
        path = context.child_directory(phase) / 'components' / component
        if not path.exists():
            continue
        try:
            _, _, authority, _, run, _ = context.authority(phase, component)
        except MatrixProgrammePrerequisite:
            continue
        components.append(SelectedE4ComponentRequest(component, run.run_plan_id, authority.package_path,
            authority.reveal_authority_id, authority.parent_record_path, authority.parent_input_binding_paths))
    components = tuple(sorted(components, key=lambda row: row.component_id))
    access = None if context.operation is None else context.operation.access_for(phase)
    collection = None
    waves = tuple(value for value in components if value.component_id != domain.ASSESSMENT_COMPONENT_ID)
    if (include_collection and type(access) is MatrixProgrammeE4Access and access.produced_qualifications
            and tuple(row.component_id for row in waves) == tuple(row.wave_id for row in plan.declaration.programme.waves)
            and (context.child_directory(phase) / 'structure' / 'analysis').exists()):
        # Read-only structure replays every current wave reveal and actual
        # complete terminal; absent results remain a prerequisite, never guessed.
        from empirical_lawhood.runtime.experiment_programme import ExperimentProgrammeDescriptor
        descriptor = ExperimentProgrammeDescriptor('programme.' + plan.fingerprint(),
            domain.PROGRAMME_PROTOCOL_ID, plan.specification.identity, plan.identity)
        service = SelectedE4ProgrammeService(service=context.service, descriptor=descriptor)
        request = SelectedE4ProgrammeRequest('request.' + _namespace(context, phase), plan.identity, components, None)
        _, state = service._state(context.child_directory(phase))
        observations, _ = service._structure(directory=context.child_directory(phase), plan=plan, state=state,
            request=request, produce=False)
        locators = tuple(_locator(context.writer, row, plan.declaration) for row in waves)
        evidence = records.SelectedE4PhaseCollectionEvidence('evidence.' + _namespace(context, phase) + '.collection',
            plan.declaration.identity, tuple(records.SelectedE4WaveInput(locator, observation.identity,
                len(observation.canonical_bytes())) for locator, observation in zip(locators, observations, strict=True)))
        artifacts = tuple(ArtifactIdentity(value.record_id, 'SOURCE', value.SCHEMA,
            value.fingerprint(), 'application/json', len(value.canonical_bytes())) for value in observations)
        collection = domain.SelectedE4PhaseCollectionSelection('collection.' + _namespace(context, phase),
            evidence, artifacts, access.produced_qualifications, access.produced_source_configs)
    return SelectedE4ProgrammeRequest('request.' + _namespace(context, phase), plan.identity, components, collection)
