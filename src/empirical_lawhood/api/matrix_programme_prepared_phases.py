# SPDX-License-Identifier: MPL-2.0
"""Project ordinary prepared phases from C and genuine completed predecessors.

This module authors input metadata. Existing initialization, DEV, source,
prospective-entry and scientific readers retain their own custody and effects.
No result or scientific permission is inferred from a declared reservation.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_initialization as initialization
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as declarative
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_experiment import MatrixPreparationSourceBank
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import is_baseline_recipe
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_preparation_records import MatrixConfirmationSources, MatrixReservedTransferSources
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
    MatrixPreparedOriginalCommitments, MatrixSelectedEntryEvidenceV3, prepared_original_panel,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import MatrixSelectedPointDesign
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import SelectedPreparedProtectedSpecification
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedNominationSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.exposure import MatrixScheduledPhysicalExclusion
from empirical_lawhood.adapters.methods.matrix_researcher_programme.prepared_operations import MatrixProgrammePreparedAccess
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit, corpus_artifact, exposure_support
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, lineage_parent_sort_key


PHASES = ('e5.initialize-development', 'e5.development', 'e5.initialize-confirmation',
    'e5.source', 'e5.confirmation', 'e6.initialize', 'e6.source', 'e6')
_PRIOR_ROLES = ('train', 'e3.calibration', 'e3.confirmation',
    'e4.development', 'e4.calibration', 'e4.confirmation')


@dataclass(slots=True)
class _PreparedRead:
    """Immutable predecessor reuse for one live original-reader lifetime."""
    public: object
    original_e3: object
    original_preparation: object
    original_assay: object
    products: tuple
    require_current: object
    development: object = None
    revision: object = None


def _development_locator(context, original):
    if original.development is None:
        original.development = context.development_product('e5.development')
    return original.development


def _operations(context):
    operations = context.plan.specification.operations.prepared
    operations.__post_init__()
    if context.execution.workers != context.plan.specification.operations.source_metadata.operational_resources.controls.maximum_parallel_tasks:
        raise ValueError('prepared source controls must match the actual programme worker selection')
    return operations


def _namespace(context, phase):
    return context.namespace + '.' + phase.replace('-', '.')


def _parents(context, phase, original):
    publication = original.original_e3.publication
    rows = [ArtifactLineageParent(original.original_e3.record,
        publication.logical.visibility_ceiling, publication.logical.outcome_access)]
    rows.extend(publication.logical.lineage_parents)
    if context.design.downstream_account == 'REVISION':
        rows.extend(_request_parents(context, phase, original))
    if phase in ('e5.initialize-confirmation', 'e5.source', 'e5.confirmation'):
        nomination = _development_locator(context, original)
        rows.append(ArtifactLineageParent(nomination.record, nomination.publication.logical.visibility_ceiling,
            nomination.publication.logical.outcome_access))
        rows.append(ArtifactLineageParent(nomination.receipt, nomination.publication.logical.visibility_ceiling,
            nomination.publication.logical.outcome_access))
    return tuple(sorted(set(rows), key=lineage_parent_sort_key))


def _request_parents(context, phase, original):
    """Only actual product/receipt parents, without the derivative export pin."""
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    development = ((_development_locator(context, original),)
        if phase in ('e5.initialize-confirmation', 'e5.source', 'e5.confirmation') else ())
    if context.design.downstream_account == 'REVISION':
        revision = _revision_originals(context, original)
        return selected_produced_input_parents(context.writer, originals=(revision.calibration, revision.downstream),
            development=(revision.fit, revision.freeze, *development))
    return selected_produced_input_parents(context.writer, originals=original.products, development=development)


def _record(context, phase, name, record, original, *, inherited=False, identity=None, lineage_parents=None):
    original.require_current()
    if not inherited:
        publication=context.publish_record(phase,name,record,identity=identity,require_current=original.require_current)
    else:
        from .matrix_programme_projection import record_identity
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
        pin=record_identity(record) if identity is None else identity
        raw=record.canonical_bytes();budget=context.plan.specification.operations.metadata_budget
        if (len(raw)>min(budget.output_bytes,budget.memory_bytes) or type(pin) is not ObjectIdentity
                or (pin.object_schema,pin.object_version,pin.object_fingerprint)!=(record.SCHEMA,record.VERSION,record.fingerprint())):
            raise ValueError('prepared produced input changes its exact identity or metadata budget')
        parents=_parents(context,phase,original) if lineage_parents is None else lineage_parents
        pair=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=parents)
        relative=(context.metadata_directory(phase)/name).relative_to(context.writer.root.contract.canonical_path).as_posix()
        request=ArtifactWriteRequest(pin.object_id,relative,record.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json',
            _namespace(context,phase),str(Path(relative).parent),raw,pair[1],tuple(row.visibility_ceiling for row in parents),
            pair[0],lineage_parents=parents)
        context.writer.preflight_write(request)
        original.require_current()
        publication=context.writer.write(request)
    original.require_current()
    return publication


def _raw(context, phase, name, raw, *, schema, logical, profile, media_type, original):
    budget = context.plan.specification.operations.metadata_budget
    if len(raw) > min(budget.memory_bytes, budget.output_bytes):
        raise ValueError('prepared copied input exceeds the explicit programme metadata budget')
    path = context.metadata_directory(phase) / name
    relative = path.relative_to(context.writer.root.contract.canonical_path).as_posix()
    original.require_current()
    publication = context.writer.write(ArtifactWriteRequest(logical, relative, schema, profile, media_type,
        _namespace(context, phase), str(Path(relative).parent), raw, VisibilityCeiling.PROSPECTIVE,
        (), OutcomeAccess.OUTCOME_BLIND))
    original.require_current()
    return publication


def _role_sources(context, phase, role, *, original):
    """Derive an exact role view; the full original C remains its custody parent.

    C's E5 allocation contains DEV and CONF. A current CONF allocation cannot
    contain the excluded DEV members. All members of the selected role remain,
    with their exact original physical roots, groups, streams and policies.
    """
    selected = context.inputs.phase(role)
    responses = selected.responses
    parent = selected.reservation.allocation
    root_ids = tuple(sorted(protocol.public_source.root.root_id for protocol in responses.protocols))
    if len(root_ids) != len(set(root_ids)):
        raise PermissionError('prepared C repeats a selected phase root')
    selected_root_ids = set(root_ids)
    roots = tuple(row for row in parent.roots if row.root.root_id in selected_root_ids)
    if tuple(row.root.root_id for row in roots) != root_ids:
        raise PermissionError('prepared projection omits an original C phase root')
    groups = {row.root.independent_group_id for row in roots}
    if len(groups) != len(roots):
        raise ValueError('prepared phase requires one original root per independent group')
    namespace = _namespace(context, phase)
    baseline = context.inputs.exposure_audit
    prior_roles = (*_PRIOR_ROLES, *(() if role == 'e5.development' else ('e5.development',)))
    seeds, excluded_groups, coordinates, parent_pins = set(), set(), {}, []
    for prior_role in prior_roles:
        prior = context.inputs.phase(prior_role)
        parent_pins.append(context.commitments.phase(prior_role))
        by_id = {row.root.root_id: row for row in prior.reservation.allocation.roots}
        by_coordinate = {scheduled.coordinate_identity(value): value for value in prior.reservation.allocation.coordinates}
        for protocol in prior.responses.protocols:
            row = by_id[protocol.public_source.root.root_id]
            excluded_groups.add(row.root.independent_group_id)
            seeds.update(stream.effective_seed for stream in row.streams)
            coordinate = by_coordinate[row.coordinate]
            if coordinates.setdefault(coordinate.coordinate_id, coordinate) != coordinate:
                raise PermissionError('prepared exclusions alias different original physical coordinates')
        seeds.update(stream.effective_seed for _, panels in prior.responses.panels for panel in panels for stream in panel.streams)
    if groups & excluded_groups or any(stream.effective_seed in seeds for row in roots for stream in row.streams):
        raise PermissionError('prepared phase collides with a preceding original reservation')
    facts = canonical_json_bytes({'schema': 'empirical-lawhood/operational/programme-prepared-exclusion-facts',
        'version': '1.0.0', 'value': {'input_commitments': context.plan.specification.input_commitments.record,
            'selected_role': role, 'original_phase': context.commitments.phase(role), 'prior_roles': tuple(parent_pins),
            'classification': 'CONSERVATIVE_DECLARED_RESERVATION_EXCLUSIONS_NOT_A_CONTACT_OR_MEASURED_EXPOSURE_CENSUS',
            'effective_seeds': tuple(sorted(seeds)), 'independent_groups': tuple(sorted(excluded_groups)),
            'physical_policy': 'RETAIN_ORIGINAL_COORDINATES_AS_ELIGIBILITY_EXCLUSIONS_NOT_MEASURED_PHYSICAL_EVIDENCE',
            'coordinates': tuple(scheduled.coordinate_identity(coordinates[key]) for key in sorted(coordinates)),
            'selected_root_ids': root_ids, 'native_contact': 'NONE'}})
    facts_pub = _raw(context, phase, 'current-exclusions/facts.json', facts,
        schema='empirical-lawhood/operational/programme-prepared-exclusion-facts',
        logical='facts.' + namespace, profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json', original=original)
    provenance = {value.artifact_id: value for value in baseline.census.factual_provenance}
    for publication in (context.plan.specification.input_commitments.publication, facts_pub):
        artifact = corpus_artifact(publication)
        if provenance.setdefault(artifact.artifact_id, artifact) != artifact:
            raise PermissionError('prepared exclusion provenance aliases an original publication')
    prior_coordinates = {value.coordinate_id: value for value in baseline.prior_scheduled_coordinates}
    for name, value in coordinates.items():
        if prior_coordinates.setdefault(name, value) != value:
            raise PermissionError('prepared exclusions change an original coordinate')
    census = replace(baseline.census, census_id='census.' + namespace,
        effective_seed_exclusions=tuple(sorted(set(baseline.census.effective_seed_exclusions) | seeds)),
        exposed_independent_groups=tuple(sorted(set(baseline.census.exposed_independent_groups) | excluded_groups)),
        scheduled_physical_exclusions=tuple(sorted({*baseline.census.scheduled_physical_exclusions,
            *(MatrixScheduledPhysicalExclusion.from_coordinate(value) for value in coordinates.values())},
            key=lambda value: value.fingerprint())),
        exposed_artifact_sha256s=tuple(sorted({*baseline.census.exposed_artifact_sha256s,
            facts_pub.logical.content_sha256, context.plan.specification.input_commitments.record.object_fingerprint})),
        factual_provenance=tuple(provenance[key] for key in sorted(provenance)))
    census_pub = _record(context, phase, 'current-exclusions/census.json', census, original)
    old_publications = {(value.logical.payload_schema, value.logical.content_sha256): value for value in baseline.prior_corpus}
    corpus = [census_pub]
    for key in sorted(prior_coordinates):
        value = prior_coordinates[key]
        publication = old_publications.get((value.SCHEMA, value.fingerprint()))
        if publication is None:
            publication = _record(context, phase, 'current-exclusions/coordinate.' + value.fingerprint() + '.json',
                value, original, identity=scheduled.coordinate_identity(value))
        corpus.append(publication)
    audit = ScheduledExposureAudit('audit.' + namespace, census, tuple(prior_coordinates[key] for key in sorted(prior_coordinates)),
        tuple(sorted(corpus, key=lambda value: value.logical.logical_artifact_id)))
    audit_pub = _record(context, phase, 'current-exclusions/audit.json', audit, original, identity=scheduled.identity(audit))
    coordinate_pins = {row.coordinate for row in roots}
    scopes = tuple(replace(scope, independent_group_ids=tuple(group for group in scope.independent_group_ids if group in groups))
        for scope in parent.matched_scopes if set(scope.independent_group_ids) & groups)
    allocation = replace(parent, allocation_id='allocation.' + namespace,
        coordinates=tuple(value for value in parent.coordinates if scheduled.coordinate_identity(value) in coordinate_pins),
        roots=roots, matched_scopes=scopes, exposure=replace(parent.exposure, scope_id='exposure.' + namespace,
            census=census, prior_scheduled_coordinates=audit.prior_scheduled_coordinates, scheduled_audit=corpus_artifact(audit_pub)))
    allocation_pub = _record(context, phase, 'current-exclusions/allocation.json', allocation, original,
        identity=scheduled.identity(allocation))
    reservation = scheduled.ScheduledReservation('reservation.' + namespace, allocation, allocation_pub)
    old_selection = selected.native_specification.selection
    policy_pins = {pin for coordinate, pin in old_selection.coordinate_policies if coordinate in coordinate_pins}
    selection = replace(old_selection, selection_id='selection.' + namespace, reservation=scheduled.identity(reservation),
        prefix_policies=tuple(value for value in old_selection.prefix_policies if scheduled.identity(value) in policy_pins),
        coordinate_policies=tuple(row for row in old_selection.coordinate_policies if row[0] in coordinate_pins))
    selection_pub = _record(context, phase, 'current-exclusions/native-selection.json', selection, original,
        identity=scheduled.identity(selection))
    specification = scheduled.ScheduledSpecification('specification.' + namespace, selection, selection_pub)
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=(context.inputs.producing_provenance,))
    public_by_root = {protocol.public_source.root.root_id: protocol.public_source for protocol in responses.protocols}
    references = tuple(index.reference(source_id=public_by_root[root_id].source.object_id, root_id=root_id,
        provenance=context.inputs.producing_provenance.identity) for root_id in root_ids)
    index.require_roster(references, expected_root_ids=root_ids)
    return initialization.MatrixPreparationInitializationSources('sources.' + namespace, reservation, specification,
        (context.inputs.producing_provenance,), references, audit, audit_pub)


def _transfer_sources(context):
    roles = (context.inputs.phase('e6.nearby'), context.inputs.phase('e6.shifted'))
    first, second = roles
    if (first.reservation, first.native_specification) != (second.reservation, second.native_specification):
        raise PermissionError('E6 changes the single original pre-TRAIN future reservation')
    index = ScheduledSourceIndex.from_shared(reservation=first.reservation, specification=first.native_specification,
        provenances=(context.inputs.producing_provenance,))
    protocols = sorted((protocol for role in roles for protocol in role.responses.protocols),
        key=lambda value: value.public_source.root.root_id)
    references = tuple(index.reference(source_id=protocol.public_source.source.object_id,
        root_id=protocol.public_source.root.root_id, provenance=context.inputs.producing_provenance.identity) for protocol in protocols)
    return initialization.MatrixPreparationInitializationSources('sources.' + context.namespace + '.e6.original',
        first.reservation, first.native_specification, (context.inputs.producing_provenance,), references,
        context.inputs.exposure_audit, context.commitments.exposure_audit.publication)


def _original_commitments(context):
    operations = _operations(context)
    return MatrixPreparedOriginalCommitments('commitments.' + context.namespace + '.prepared',
        context.native_training_locator(), context.plan.specification.input_commitments, operations.maximum_source_bytes)


def _initialize(context, phase, original):
    scientific_phase = {'e5.initialize-development': 'E5_OPPORTUNITY',
        'e5.initialize-confirmation': 'E5_CONFIRMATION', 'e6.initialize': 'E6_TRANSFER'}[phase]
    if scientific_phase == 'E6_TRANSFER':
        sources, development = _transfer_sources(context), None
    else:
        role = 'e5.development' if scientific_phase == 'E5_OPPORTUNITY' else 'e5.confirmation'
        if scientific_phase == 'E5_CONFIRMATION':
            _nomination(context, None if context.design.downstream_account == 'REVISION' else _package(context, original), original)
        sources = _role_sources(context, phase, role, original=original)
        development = None if scientific_phase == 'E5_OPPORTUNITY' else _development_locator(context, original)
    request = initialization.MatrixPreparationInitializationRequest('request.' + _namespace(context, phase),
        _namespace(context, phase), scientific_phase, sources, _original_commitments(context),
        exposure_support(sources.audit), development)
    specification = initialization.MatrixPreparationInitializationSpecification('experiment.' + _namespace(context, phase), request.identity)
    from empirical_lawhood.api.matrix_preparation_initialization import publish_initialization
    directory = context.metadata_directory(phase)
    publication = _record(context, phase, 'specification.json', specification, original)
    result = publish_initialization(specification=specification, request=request,
        project_root=context.service.project_root, writer=context.writer, metadata_directory=directory,
        output_selection_path=directory / 'sources.json', execution=context.execution)
    return replace(result, publications=(publication, *result.publications), target_specification=specification,
        target_specification_path=directory / 'specification.json')


def _initial_bank(context, phase):
    inputs = context.method_inputs(phase)
    request, bank = inputs
    if type(bank) is not initialization.MatrixPreparationInitializationBank or bank.request != request:
        raise PermissionError('prepared phase requires its exact completed deterministic initialization bank')
    bank.__post_init__()
    return bank


def _panels(context, phase):
    roles = {'E5_OPPORTUNITY': ('e5.development',), 'E5_CONFIRMATION': ('e5.confirmation',),
        'E6_TRANSFER': ('e6.nearby', 'e6.shifted')}[phase]
    groups = {}
    for role in roles:
        for group, values in context.inputs.phase(role).responses.panels:
            if group in groups:
                raise PermissionError('prepared phase repeats a C-assigned independent panel group')
            groups[group] = tuple(sorted((prepared_original_panel(value) for value in values), key=lambda value: value.panel_id))
    return tuple((group, groups[group]) for group in sorted(groups))


def _package(context, original):
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import original_e3_package
    from empirical_lawhood.api.recursive_operations import operation_catalog
    return original_e3_package(context.writer, SimpleNamespace(original_e3=original.public,
        original_e3_products=original.products, assay=context.design.prepared_assay), operation_catalog()[2])


def _revision_originals(context, original):
    """Actual selected DEV/CAL/CONF products, without an E3 model fallback."""
    if original.revision is not None:
        return original.revision
    from empirical_lawhood.api.matrix_researcher_programme_e4_lineage import programme_revision_read
    from empirical_lawhood.api.matrix_sampling_runtime import _original_product
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import (
        SelectedE4RevisionExport, SelectedE4PublicCalibration)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionSelectedPackage
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite
    revision = programme_revision_read(context)
    fit, freeze, decision = revision.nomination_locator, revision.frozen_locator, revision.decision
    if not decision.fit_available:
        raise MatrixProgrammePrerequisite('e5.development', 'ACTUAL_REVISION_NOT_FROZEN',
            'The declared REVISION account requires its actual constructible frozen E4 models.')
    codecs = operation_catalog()[2]
    development, selected, frozen = revision.development, revision.nomination, revision.frozen
    actual_plan = context.method_inputs('e4.confirmation').plan
    export = actual_plan.tail.revision
    if type(export) is not SelectedE4RevisionExport or export != SelectedE4RevisionExport.from_products(
            development, selected, frozen, record_id=export.record_id):
        raise PermissionError('prepared revision changes the actual original E4 CONF frozen export')
    calibration = context.original_product('e4.calibration', methods.SelectedE4Calibration.SCHEMA)
    downstream = context.original_product('e4.confirmation', methods.SelectedE4DownstreamNomination.SCHEMA)
    def read(locator, kind):
        raw = _original_product(context.writer, locator, locator.record, codecs)
        value = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        if value.identity != locator.record or value.canonical_bytes() != raw:
            raise PermissionError('prepared revision changes its actual original CAL/CONF canonical product')
        return value
    actual_calibration = read(calibration, methods.SelectedE4Calibration)
    actual_nomination = read(downstream, methods.SelectedE4DownstreamNomination)
    public_calibration = actual_nomination.calibration_product
    if type(public_calibration) is not SelectedE4PublicCalibration or public_calibration != SelectedE4PublicCalibration.from_calibration(
            actual_calibration, record_id=public_calibration.record_id):
        raise PermissionError('prepared revision changes its actual original CAL public projection')
    if (actual_nomination.selected != 'REVISION' or actual_nomination.frozen_revision != export.models.frozen
            or actual_nomination.calibration != actual_calibration.identity
            or actual_nomination.calibration_product != public_calibration
            or actual_nomination.frozen_product != export.decision):
        raise PermissionError('prepared REVISION changes the actual E4 CONF nomination, frozen model or original CAL')
    models = SelectedE4PointModels.from_models(export.models, record_id='point-models.' + context.namespace + '.prepared')
    package = MatrixRevisionSelectedPackage('package.' + context.namespace + '.revision-prepared', models,
        downstream.record, calibration.record, public_calibration if models.relation_fit is not None else None,
        original.public if models.relation_fit is not None else None)
    groups = {*original.public.training_unit_ids, *original.public.selection_unit_ids, *development.group_ids,
        *public_calibration.group_ids, *(row.independent_group_id for row in actual_nomination.confirmation_product.groups)}
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    parents = selected_produced_input_parents(context.writer, originals=(calibration, downstream), development=(fit, freeze))
    original.revision = SimpleNamespace(fit=fit, freeze=freeze, calibration=calibration, downstream=downstream,
        export=export, public_calibration=public_calibration, package=package, excluded_groups=tuple(sorted(groups)))
    original.revision.parents = parents
    return original.revision


def _nomination(context, package, original):
    from empirical_lawhood.api.matrix_selected_opportunity_runtime import authenticate_selected_development_nomination
    locator = _development_locator(context, original)
    if context.design.downstream_account == 'REVISION':
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import MatrixRevisionProgrammeAssessment
        from .matrix_programme_decisions import development_assessment
        report = development_assessment(context)
        result = _decode(report['assessment'], MatrixRevisionProgrammeAssessment)
        if result.identity != locator.record or result.functional.disposition != 'NOMINATED':
            raise PermissionError('prepared revision CONF has no actual authenticated DEV nominee')
        return result.functional, None, locator.publication
    return authenticate_selected_development_nomination(context.writer, locator, package=package,
        criterion=context.design.e5_development.criterion, nomination_pin=locator.record,
        expected_groups=context.design.e5_development.expected_groups)


def _protected_science(context, phase, original, *, sources=None):
    """Construct science from originals; source qualification is a later owner."""
    transfer = phase.startswith('e6')
    revision = context.design.downstream_account == 'REVISION'
    package = _revision_originals(context, original).package if revision else _package(context, original)
    nomination = None if transfer else _nomination(context, package, original)
    if transfer:
        specification = context.design.e6
        bank = _initial_bank(context, 'e6.initialize')
    else:
        choices = context.design.e5_confirmation
        selected = nomination[0]
        menu = dict(context.design.e5_development.arms)
        recipe = menu.get(selected.selected_arm_id)
        if (selected.selected_arm_id not in choices.eligible_nominee_arm_ids or recipe is None
                or recipe.identity != selected.selected_recipe):
            raise PermissionError('E5 confirmation nominee is outside the frozen current DEV menu')
        arms = tuple(sorted((arm, menu[arm]) for arm in (choices.baseline_arm_id, selected.selected_arm_id)))
        specification = SelectedPreparedProtectedSpecification('experiment.' + context.namespace + '.e5.confirmation',
            context.design.downstream_account, 'E5_CONFIRMATION', choices.expected_groups, arms, choices.criterion,
            context.design.e5_development.minimum_recoverable_groups if revision else None,
            context.design.e5_development.tie_policy if revision else None, ())
        bank = _initial_bank(context, 'e5.initialize-confirmation')
    if sources is None:
        closure = bank.prepared_closure(record_id='closure.' + context.namespace + '.' + specification.phase.lower(),
            numerical_scope=scheduled.identity(bank.request.sources.specification.selection.numerical_design))
        baseline, = (arm for arm, recipe in specification.arms if is_baseline_recipe(recipe))
        if transfer:
            recipe, = (recipe for _, recipe in specification.arms)
            coordinates = tuple(sorted({row.coordinate for row in closure.descriptors}, key=lambda value: value.object_id))
            sources = MatrixReservedTransferSources('sources.' + context.namespace + '.e6', closure,
                tuple((coordinate, recipe) for coordinate in coordinates), baseline)
        else:
            sources = MatrixConfirmationSources('sources.' + context.namespace + '.e5.confirmation',
                closure, specification.arms, baseline)
    if revision:
        programme = _revision_programme(context, specification, sources, original, nomination=nomination)
        if nomination is not None:
            from empirical_lawhood.api.matrix_selected_revision_runtime import _development_nomination
            from empirical_lawhood.api.recursive_operations import operation_catalog
            if _development_nomination(context.writer, _development_locator(context, original), programme,
                    operation_catalog()[2]) != nomination[0]:
                raise PermissionError('prepared revision changes its actual authenticated DEV nomination')
        return specification, programme, nomination
    interpretations = tuple(value for value in context.design.recipe_interpretations if value.arm_id in dict(specification.arms))
    rows = tuple(sorted(((arm, MatrixPreparedPublicSource.from_source(source)) for arm, source in sources.source_arms()),
        key=lambda row: row[1].source.object_id))
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedRecipeInterpretation
    recipe_interpretations = tuple(sorted((MatrixPreparedRecipeInterpretation(dict(specification.arms)[value.arm_id].identity,
        value.family_id, value.scientific_premise) for value in interpretations), key=lambda value: value.recipe.object_id))
    design = MatrixSelectedPointDesign('design.' + specification.fingerprint(), package, specification.phase,
        specification.expected_groups, specification.arms, rows, recipe_interpretations)
    full = MatrixSelectedProtectedProgramme('programme.' + specification.fingerprint() + '.' + sources.fingerprint(),
        sources, design, context.design.prepared_assay, _panels(context, specification.phase), specification.criterion,
        specification.transfer_domain_claims, None if nomination is None else nomination[0],
        None if nomination is None else nomination[2], None if nomination is None else nomination[1])
    return specification, MatrixSelectedPublicProgramme.from_programme(full), nomination


def _revision_programme(context, specification, sources, original, *, nomination=None):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionPreparedProgramme
    revision = _revision_originals(context, original)
    groups = set(revision.excluded_groups)
    if nomination is not None:
        groups.update(nomination[0].development_unit_ids)
    if type(sources) is MatrixPreparationSourceBank:
        # The original reservation itself is retained by the initializer.
        reservation = _initial_bank(context, 'e5.initialize-development').request.sources.reservation
    else:
        reservation = sources.closure.reservation
    return MatrixRevisionPreparedProgramme('programme.' + specification.fingerprint() + '.' + sources.fingerprint(),
        specification.phase, revision.package, sources, reservation, specification.arms, specification.expected_groups,
        context.design.prepared_assay, _panels(context, specification.phase), specification.criterion,
        tuple(sorted(groups)), specification.minimum_recoverable_groups, specification.tie_policy,
        specification.transfer_domain_claims, None if nomination is None else _development_locator(context, original).record)


def _revision_evidence(context, programme, original, *, report=None, nomination=None):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixRevisionEntryEvidenceV2
    from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
    from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationResult, ScientificSourceQualificationSpec
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    revision = _revision_originals(context, original)
    return MatrixRevisionEntryEvidenceV2('evidence.' + programme.fingerprint(), programme.identity,
        revision.fit, revision.freeze, revision.downstream, revision.calibration, revision.export.identity,
        revision.public_calibration, original.public.original_package,
        None if report is None else _decode(report['qualification_specification'], ScientificSourceQualificationSpec),
        None if report is None else _decode(report['pipeline_evidence'], MatrixSourcePipelineEvidence),
        None if report is None else _decode(report['qualification_result'], ScientificSourceQualificationResult),
        () if report is None else tuple(_decode(value, RecursivePriorExecutionBinding) for value in report['prior_executions']),
        () if report is None else tuple((_decode(pin, ObjectIdentity), _decode(value, ArtifactWriteResult))
            for pin, value in report['publications']),
        None if nomination is None else _development_locator(context, original), _original_commitments(context))


def _copy_files(context, phase, artifacts, original):
    """Copy exactly the required original blind NPZ publications, never a path guess."""
    publications = [publication for selected in context.bindings.values() for publication in selected.publications]
    publications.extend(publication for value in context.inputs.phases if value.responses is not None
        for publication in value.responses.template_publications)
    by_artifact = {}
    for publication in publications:
        key = (publication.logical.logical_artifact_id, publication.logical.payload_schema,
            publication.logical.content_sha256, publication.materialization.size_bytes)
        by_artifact.setdefault(key, publication)
    files = []
    for index, artifact in enumerate(sorted(set(artifacts), key=lambda value: value.artifact_id)):
        publication = by_artifact.get((artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.size_bytes))
        if publication is None or (publication.logical.profile, publication.logical.outcome_access,
                publication.logical.visibility_ceiling) != (ArtifactProfile.MATRIX_ARRAY_NPZ,
                    OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE):
            raise PermissionError('prepared inputs lack the exact original blind initialization/template publication')
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
        authenticate_publication(context.writer, publication)
        raw = read_bounded_bytes(context.writer.root.resolve(publication.materialization.relative_path, for_write=False),
            maximum_bytes=artifact.size_bytes)
        if len(raw) != artifact.size_bytes or sha256(raw).hexdigest() != artifact.sha256:
            raise PermissionError('prepared copied FILE differs from its exact original bytes')
        filename = 'files/' + str(index).zfill(5) + '.' + artifact.sha256 + '.npz'
        _raw(context, phase, filename, raw, schema=artifact.payload_schema, logical=artifact.artifact_id,
            profile=ArtifactProfile.MATRIX_ARRAY_NPZ, media_type=artifact.media_type, original=original)
        files.append(ExperimentFileInputBinding('file.' + str(index).zfill(5), artifact, '1.0.0', filename, artifact.size_bytes))
    return tuple(files)


def _derive(context, phase, specification, records, original, *, files=(), selected=False):
    """Use the ordinary public deriver with its genuine per-protocol layout."""
    from empirical_lawhood.api.experiment_preparation import _protocol
    directory = context.metadata_directory(phase)
    publications, bindings = [], []
    from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import (
        MatrixPreparedSourceAssemblySpecification, MatrixPreparedRetainedE3AssemblySpecification)
    source_assembly = type(specification) in (MatrixPreparedSourceAssemblySpecification, MatrixPreparedRetainedE3AssemblySpecification)
    if source_assembly and phase not in ('e5.source', 'e6.source'):
        raise PermissionError('prepared source assembly changes its exact programme phase')
    if selected:
        request=records['request']
        records={**records,**dict(declarative.original_locator_records(request))}
    for key, record in sorted(records.items()):
        name = 'input.' + key + '.json'
        identity=ObjectIdentity.from_record(key,record) if key.startswith(('original.','development.')) else record.identity
        if source_assembly and key == 'prepared-programme':
            from .matrix_programme_e4_inputs import prepared_source_lineage
            model_parents = prepared_source_lineage(original_e3=original.original_e3,
                development_product=records['development-product'])
        else:
            model_parents = None
        publications.append(_record(context, phase, name, record, original, lineage_parents=model_parents,
            inherited=((key == 'prepared-programme') if source_assembly else
                (selected or key in ('request','prepared-programme','development-product'))
                    and not key.startswith(('original.','development.'))),identity=identity))
        bindings.append(ExperimentInputBinding(key, identity, name, len(record.canonical_bytes())))
    selector = ExperimentFileInputSelection('sources.' + specification.fingerprint(), _protocol(specification).protocol_id,
        tuple(bindings), files)
    publications.append(_record(context, phase, 'input-specification.json', specification, original,
        inherited=not source_assembly and not selected and phase in ('e5.source', 'e5.confirmation', 'e6.source', 'e6')))
    publications.append(_record(context, phase, 'input-sources.json', selector, original,
        inherited=not source_assembly and not selected and phase in ('e5.source', 'e6.source')))
    result = context.service.derive_inputs(specification_path=directory / 'input-specification.json',
        source_selection_path=directory / 'input-sources.json', metadata_directory=directory / 'derived' if selected else directory,
        output_selection_path=directory / 'sources.json', execution=context.execution)
    original.require_current()
    return replace(result, publications=(*publications, *result.publications),
        target_specification=specification if result.target_specification is None else result.target_specification,
        target_specification_path=directory / 'input-specification.json' if result.target_specification is None else result.target_specification_path)


def _development(context, phase, original):
    operations = _operations(context)
    specification = context.design.e5_development
    bank = _initial_bank(context, 'e5.initialize-development')
    closure = bank.prepared_closure(record_id='closure.' + context.namespace + '.e5.development',
        numerical_scope=scheduled.identity(bank.request.sources.specification.selection.numerical_design))
    index = closure.source_index()
    sources = tuple(sorted((closure.prepare_source(reference, recipe, index=index)
        for reference in closure.descriptors for _, recipe in specification.arms), key=lambda value: value.source_id))
    selected = MatrixPreparationSourceBank('bank.' + context.namespace + '.e5.development', (closure.reservation.allocation,), sources)
    revision = context.design.downstream_account == 'REVISION'
    revision_originals = _revision_originals(context, original) if revision else None
    revision_evidence = (_revision_evidence(context, _revision_programme(context, specification, selected, original), original)
        if revision else None)
    request = declarative.SelectedPreparedDerivationRequestV2('request.' + _namespace(context, phase), selected, None,
        closure.reservation, None if revision else original.public, () if revision else original.products,
        () if revision else context.design.recipe_interpretations,
        None, None, revision_originals.package if revision else None, revision_evidence,
        context.design.prepared_assay, _panels(context, 'E5_OPPORTUNITY'),
        operations.campaign, None, operations.cutoff, operations.operator_id, None, None, (), (), (),
        operations.opportunity_resources, None, _original_commitments(context), _request_parents(context, phase, original))
    artifacts = {source.initial.array_artifact for source in selected.sources} | {request.assay.template_artifact}
    files = _copy_files(context, phase, artifacts, original)
    return _derive(context, phase, specification, {'request': request}, original, files=files, selected=True)


def _source(context, phase, original):
    from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import (
        MatrixPreparedSourceAssemblyRequest, MatrixPreparedSourceAssemblySpecification,
        MatrixPreparedRetainedE3AssemblyRequest, MatrixPreparedRetainedE3AssemblySpecification,
    )
    _, programme, _ = _protected_science(context, phase, original)
    settings = context.plan.specification.operations.source_metadata
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection
    continued = original.original_preparation.record.object_schema in (ConfiguredE3ContinuedPreparationSelection.SCHEMA,
        ConfiguredE3UnfinishedPreparationSelection.SCHEMA, ConfiguredE3ClosedPreparationSelection.SCHEMA)
    kind = MatrixPreparedRetainedE3AssemblyRequest if continued else MatrixPreparedSourceAssemblyRequest
    request = kind('request.' + _namespace(context, phase), _namespace(context, phase),
        context.plan.specification.input_commitments, original.original_e3, original.original_preparation,
        original.original_assay, original.products, programme.identity, _development_locator(context, original).identity,
        context.native_training_locator(), exposure_support(programme.sources.closure.audit), settings.physical_cutoff,
        settings.source_computability_evidence, settings.source_budget, settings.dataset_work_envelope,
        settings.operational_resources, settings.metadata_issuer_id, settings.metadata_approver_id,
        settings.metadata_requester_id, settings.metadata_private_key_relative_path, settings.metadata_validity_seconds,
        settings.metadata_reason_codes, settings.licence_id, settings.scratch_namespace + '.' + phase.replace('-', '.'),
        settings.allow_metadata_key_creation, settings.metadata_valid_from_utc)
    kind = MatrixPreparedRetainedE3AssemblySpecification if continued else MatrixPreparedSourceAssemblySpecification
    specification = kind('experiment.' + _namespace(context, phase), request.identity)
    return _derive(context, phase, specification, {'request': request, 'prepared-programme': programme,
        'development-product': _development_locator(context, original)}, original)


def _decode(document, kind):
    raw = canonical_json_document_bytes(document)
    return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))


def _protected(context, phase, original):
    from empirical_lawhood.adapters.methods.matrix_prepared_source_experiment import MatrixPreparedSourceInputs, validate_input_companions
    from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
    from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationResult, ScientificSourceQualificationSpec
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    operations = _operations(context)
    access = None if context.operation is None else context.operation.access_for(phase)
    if type(access) is not MatrixProgrammePreparedAccess:
        from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite
        raise MatrixProgrammePrerequisite(phase, 'PREPARED_CURRENT_ENTRY_REQUIRED',
            'Select MatrixProgrammePreparedAccess with the actual current root, entry and formal denominator.')
    access.__post_init__()
    source_phase = 'e6.source' if phase == 'e6' else 'e5.source'
    inputs = context.method_inputs(source_phase)
    if type(inputs) is not MatrixPreparedSourceInputs:
        raise TypeError('prepared protected phase needs its exact actual source selection and companions')
    validate_input_companions(inputs)
    selected = inputs.selection
    from .matrix_programme_decisions import source_assessment
    report = source_assessment(context, source_phase)
    specification, programme, nomination = _protected_science(context, phase, original, sources=selected.bank.sources)
    closure = programme.sources.closure
    revision = context.design.downstream_account == 'REVISION'
    if revision:
        evidence = _revision_evidence(context, programme, original, report=report, nomination=nomination)
    else:
        publication, = (value for value in context.binding(source_phase).publications
            if (value.logical.payload_schema, value.logical.content_sha256) == (closure.reservation.SCHEMA, closure.reservation.fingerprint()))
        evidence = MatrixSelectedEntryEvidenceV3('evidence.' + _namespace(context, phase), programme.original_programme,
            publication, _decode(report['qualification_specification'], ScientificSourceQualificationSpec),
            _decode(report['pipeline_evidence'], MatrixSourcePipelineEvidence),
            _decode(report['qualification_result'], ScientificSourceQualificationResult), original.products,
            tuple(_decode(value, RecursivePriorExecutionBinding) for value in report['prior_executions']),
            tuple((_decode(pin, ObjectIdentity), _decode(value, ArtifactWriteResult)) for pin, value in report['publications']),
            _original_commitments(context), None if nomination is None else _development_locator(context, original))
    declarative.validate_evidence(programme, evidence)
    policy = access.root.system.authority_policy
    if operations.campaign.authority_policy != ObjectIdentity.from_record(policy.policy_id, policy):
        raise PermissionError('prepared protected campaign changes its actual selected root authority policy')
    original_transport = phase == 'e6' and not revision
    kwargs = {'transport_policy': context.inputs.e6_policy} if original_transport else {}
    kind = declarative.SelectedPreparedDerivationRequestV3 if original_transport else declarative.SelectedPreparedDerivationRequestV2
    request = kind('request.' + _namespace(context, phase), None, programme.sources, closure.reservation,
        None if revision else original.public, () if revision else original.products,
        () if revision else tuple(value for value in context.design.recipe_interpretations if value.arm_id in dict(specification.arms)),
        None if revision else evidence, None if nomination is None or revision else MatrixSelectedNominationSelection.from_nomination(nomination[0]),
        _revision_originals(context, original).package if revision else None, evidence if revision else None,
        context.design.prepared_assay, programme.panels, operations.campaign, access.root,
        operations.cutoff, operations.operator_id, access.entry, access.formal_methods,
        access.formal_source_inventories, (), (), operations.protected_resources, context.plan.specification.operations.source_metadata.operational_resources,
        _original_commitments(context), _request_parents(context, phase, original), **kwargs)
    artifacts = {value.initial.array_artifact for _, value in programme.sources.source_arms()} | {request.assay.template_artifact}
    files = _copy_files(context, phase, artifacts, original)
    return _derive(context, phase, specification, {'request': request}, original, files=files, selected=True)


def project_prepared_phase(context, phase):
    """One eligible ordinary input projection; never a parallel runner."""
    if phase not in PHASES:
        raise ValueError('unsupported current prepared programme phase: ' + str(phase))
    _operations(context)
    with context.e3_originals(publish=True) as read:
        original = _PreparedRead(read.public, read.original_e3, read.original_preparation,
            read.original_assay, read.products, read.require_current)
        def require_current():
            read.require_current()
            if original.revision is not None:
                from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
                revision = original.revision
                if selected_produced_input_parents(context.writer, originals=(revision.calibration, revision.downstream),
                        development=(revision.fit, revision.freeze)) != revision.parents:
                    raise PermissionError('prepared revision original parent access or publication changed during projection')
        original.require_current = require_current
        original.require_current()
        if phase in ('e5.initialize-development', 'e5.initialize-confirmation', 'e6.initialize'):
            result = _initialize(context, phase, original)
        elif phase == 'e5.development':
            result = _development(context, phase, original)
        elif phase in ('e5.source', 'e6.source'):
            result = _source(context, phase, original)
        else:
            result = _protected(context, phase, original)
        original.require_current()
        return result
