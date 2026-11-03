# SPDX-License-Identifier: MPL-2.0
"""Exposed current E3 workers, live original access and ordinary E4 DEV.

TRAIN rows, qualification selections and issue grants are disclosed software
inputs. They are not native TRAIN acquisition or scientific qualification.
The four downstream E3 products must, however, be produced by their real
configured workers and successful original receipts. No arithmetic E3 export
from the metadata fixture is used as downstream evidence or authority.
"""

from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.api.results import RunCampaignRequest
from empirical_lawhood.api.selected_e3_access import original_input_access, select_current_e3_access
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection, PreparedExperimentFile
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile


ROOT = Path(__file__).resolve().parents[1]
EL = Path('/media/chevre/EL')
WORKERS = 4


def _exposed_inputs(directory, *, root_contract_factory=None):
    """Keep the complete existing fixture with an actually guarded EL plane."""
    import numpy as np

    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from tests import test_matrix_e3_protected_source_records as templates
    from tests import test_matrix_factor_confirmation_eligibility as stock
    from tests import test_matrix_scheduled_history as scheduled
    from tests.test_matrix_finite_dt_source_assembly import source_metadata_case
    from tests.test_matrix_scheduled_response_forecast import pauli

    def actual_plane(path, *, storage_codecs):
        path.mkdir()
        contract = (ExternalRootContract('recursive-software-fixture', 'Exposed C25 software custody',
            str(path), str(EL), OperatorStorageProfile.SCHEMA, 1)
            if root_contract_factory is None else root_contract_factory(path))
        plane = ExternalArtifactPlane(GuardedExternalRoot(contract),
            validators=ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs()))
        diagnostic = plane.root.diagnostic()
        assert diagnostic.read_ready and diagnostic.write_ready, diagnostic
        return plane

    provenance = capture_matrix_provenance(project_root=ROOT)
    parameter_template, encode = scheduled.parameter_template, templates.encode_matrix_arrays
    instrument = {
        'generic_basis': np.asarray([np.kron(np.eye(2), value) / 2 for value in pauli()], dtype='<c16'),
        'force_coefficients': np.stack((np.eye(3), np.eye(3))).astype('<f8') / np.sqrt(6),
        'trace_coefficients': np.ones((2, 3), dtype='<f8') / np.sqrt(6),
        'receiver_coefficients': np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4),
    }

    def publish_instrument(values, **kwargs):
        assert {key: (value.dtype.str, value.shape) for key, value in values.items()} == {
            key: (value.dtype.str, value.shape) for key, value in instrument.items()}
        return encode(instrument, **kwargs)

    # These patches construct explicit software input bytes only. Every patch
    # ends before preparation, authoring, current grants or a worker is used.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(stock, '_matrix_plane', actual_plane)
        patch.setattr(scheduled, 'parameter_template',
            lambda: replace(parameter_template(), provenance=provenance))
        patch.setattr(templates, 'encode_matrix_arrays', publish_instrument)
        return source_metadata_case(directory)


def _profile(plane):
    return _profile_for_path(Path(plane.root.contract.canonical_path))


def _profile_for_path(path):
    return OperatorStorageProfile('software.c25.storage', 'external-filesystem', '1.0.0',
        str(path.parent), str(EL), path.name, 'c25-scratch', OperatorStorageAccessMode.READ_WRITE,
        None, None, (), 'strict-mount-contained-no-symlink', 1, (), WORKERS, False)


def _run_original(case, directory, monkeypatch):
    """Author/issue/run the installed configured producers and native futures."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import (
        RESOURCE_BINDING_DEPENDENCY, bind_protected_e3_experiment_inputs,
    )
    from empirical_lawhood.infrastructure.source_closure import capture_target_closure
    from empirical_lawhood.planning.formal_analysis import derive_formal_gap_applicability
    from tests.experiment_entry_support import entry_package_for_draft
    from tests.runtime_platform.test_recursive_prospective_workflow import _issue_public_handoff
    from tests.runtime_platform.test_study_issue import _issue_api_fixture
    from tests.test_matrix_e3_public_programme import _execution, _native_receipt_census, _primary_census
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest, _read_exact_record
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt

    plane, profile = case.plane, _profile(case.plane)
    selection = case.preparation
    # Reuse the original role publication already named by this fixture's
    # exact qualification/source-config census. The metadata wrapper's second
    # equal-byte alias is not the selected transport of that existing proof.
    allocation_pin = selection.fit_config.allocation
    roles_qualification, = (row for row in selection.qualifications
        if (row.materialization.object_schema, row.materialization.object_version,
            row.materialization.object_fingerprint) == (allocation_pin.object_schema,
                allocation_pin.object_version, allocation_pin.object_fingerprint))
    assert roles_qualification.source_id == 'external.' + roles_qualification.materialization.object_id
    roles_config, = (row for row in selection.source_configs
        if row.source_id == roles_qualification.source_id)
    manifest = plane.read_manifest('inputs/' + roles_qualification.materialization.object_id + '.json')
    roles_publication = _publication_from_manifest(plane, manifest)
    roles = _read_exact_record(plane, roles_publication, UnitAllocation,
        maximum_bytes=roles_config.maximum_bytes)
    assert roles.identity == allocation_pin
    assert ObjectIdentity.from_record(roles_publication.logical.logical_artifact_id, roles) == roles_qualification.materialization
    assert roles_publication.logical.content_sha256 == roles_qualification.content_sha256 == roles.fingerprint()
    selection = replace(selection, fit_config=replace(selection.fit_config,
        publications=tuple((key, roles_publication if key == 'roles' else publication, availability)
            for key, publication, availability in selection.fit_config.publications)))
    # The metadata wrapper's disclosed world label is retained. Its prospective
    # software entry/inventory must name that actual world before real issue.
    entry = entry_package_for_draft(selection.root)
    inventory, = selection.formal_source_inventories
    inventory = replace(inventory, evidence_world=entry.checklist.portfolio_world,
        denominator_id=selection.root.system.system_id,
        denominator_inapplicable_gap_ids=tuple(row.gap_id for row in entry.register.gaps))
    coverage = replace(entry.coverage, denominator_id=selection.root.system.system_id,
        applicability=derive_formal_gap_applicability(entry.register, inventory))
    entry = replace(entry, coverage=coverage, checklist=replace(entry.checklist,
        formal_gap_coverage=ObjectIdentity.from_record(coverage.coverage_id, coverage)))
    selection = replace(selection, entry_package=entry, formal_source_inventories=(inventory,))
    files = dict(case.training.template_files)
    for name in ('features', 'outcomes'):
        artifact = getattr(selection, 'training_' + name)
        path = plane.root.resolve('literal-training/' + name + '.json', for_write=False)
        raw = path.read_bytes()
        assert (len(raw), sha256(raw).hexdigest()) == (artifact.size_bytes, artifact.sha256)
        files[artifact.artifact_id] = PreparedExperimentFile(artifact, json.loads(raw)['version'], path, len(raw))
    bound = bind_protected_e3_experiment_inputs(case.public.specification,
        {'protected-selection': selection}, files=files)
    closure = capture_target_closure(ROOT, selection.selection_id + '.prospective.source-closure').closure
    execution = ExecutionSelection(WORKERS, 'main-locked',
        ObjectIdentity.from_record('recursive-member.implementation', closure), plane.root.contract.canonical_path)
    service = ExperimentProgrammeService(ROOT, plane, profile)
    preparation = service.prepare(case.public.specification, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=execution)
    # Candidate/resource preview belongs to the ordinary prepare_authoring
    # hook. No other missing source, authority or scientific premise is allowed.
    assert preparation.draft is not None
    assert tuple((row.code, row.kind) for row in preparation.dependencies) == (
        (RESOURCE_BINDING_DEPENDENCY, DependencyKind.SOFTWARE),)
    authored = service.author(preparation=preparation, output_dir=directory)
    assert authored['scientific_authority'] == 'NONE' and authored['native_contact'] == 'none'
    selected = load_prepared_prospective_experiment(directory=directory, project_root=ROOT,
        storage_profile=profile, artifact_writer=plane)
    handoff = selected.handoff
    scaffold = directory.parent / 'software-issue'
    scaffold.mkdir()
    api, paths, _, custody = _issue_api_fixture(scaffold, standard_fixture=lambda: (
        handoff.authoring.base, handoff.context.resolve_standard(handoff.authoring.base).context))
    parts = (handoff, EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY,
        GENERATED_EXTENSION_BUNDLE_AGGREGATE, plane, b'', api, paths, custody)
    issued = _issue_public_handoff(scaffold, monkeypatch, handoff_parts=parts,
        namespace='software-c25-configured-e3', compiled_candidate=selected.candidate)
    output = directory.parent / 'actual-e3-execution'
    output.mkdir()
    control = _execution(case, handoff, issued, output, maximum_parallel_tasks=WORKERS)
    service = ExperimentProgrammeService(ROOT, plane, profile,
        prospective_api_factory=lambda **_: control.api)
    report = service.run(directory=directory, maximum_parallel_tasks=WORKERS,
        request=RunCampaignRequest(control.package_path, confirmed=True,
            reveal_authority_id=control.reveal.authority_id))
    (output / 'report.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    assert report['status'] == 'SUCCEEDED', report
    assert control.executor.completed and control.executor.ready
    assert all(row.ready for row in control.executor.ready.values())
    assert all(pid != os.getpid() for _, _, pid in control.executor.completed)
    plan = control.service._load_status_execution_plan(control.package.run_plan_id)
    tasks = {task.task_id for task in plan.tasks}
    assert tasks == set(control.executor.contracts) == set(control.executor.ready)
    assert tasks == {task for task, _, _ in control.executor.completed}
    # Retain actual worker/source/Ready evidence before any downstream reader,
    # export, bootstrap or DEV failure can obscure successful original work.
    proof = {'parent_pid': os.getpid(), 'run_id': control.package.run_plan_id,
        'execution_plan': ObjectIdentity.from_record(plan.execution_plan_id, plan).to_document(),
        'scientific_specification': case.public.specification.identity.to_document(),
        'source_entries': tuple(control.executor.source_entries.values()),
        'workers': control.executor.completed, 'task_count': len(tasks),
        'prepared': {key: value.identity.to_document() for key, value in control.executor.contracts.items()},
        'ready': {key: value.proof() for key, value in control.executor.ready.items()}}
    (output / 'actual-worker-execution-proof.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    primary = _primary_census(plane, control.package.run_plan_id)
    receipt_paths = (Path(plane.root.contract.canonical_path) / 'runs' / control.package.run_plan_id / 'receipts').glob('*/*.json')
    receipts = tuple(decode_canonical_bytes(path.read_bytes(), CanonicalTaskReceipt, maximum_bytes=1024**2)
        for path in receipt_paths if not path.name.endswith('.manifest.json'))
    ordinary = tuple(row for row in receipts if row.task_id in tasks)
    assert len(ordinary) == len(tasks) and {row.task_id for row in ordinary} == tasks
    assert all(row.operational_status.value == 'SUCCEEDED' for row in ordinary)
    native = _native_receipt_census(plane, control.package.run_plan_id, plan,
        {key for key, value in control.executor.contracts.items() if value.native_effect},
        tuple(row for row in receipts if row.task_id not in tasks))
    (output / 'primary-before-downstream.json').write_text(json.dumps({
        'primary': primary, 'native_subwork_receipts': native,
        'ordinary_receipts': tuple(ObjectIdentity.from_record(row.receipt_id, row).to_document() for row in ordinary)},
        sort_keys=True, indent=2) + '\n')
    return service, selected, control, execution


def _publish_development(case, public, products, parents, execution, current):
    """Publish exact C-derived DEV sources, preserving real original custody."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.e4_inputs import compose_programme_e4_banks
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as workers
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorResources
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import (
        PROTOCOL_ID, SelectedE3E4ExperimentSpecification, SelectedE3E4OperationalSelection,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.planning.experiment_inputs import (
        ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding,
    )

    composed = compose_programme_e4_banks(case.committed, original_e3=public,
        criterion_publication=case.criterion_publication)
    bank, programme = dict(composed.banks)['DEVELOPMENT'], dict(composed.programmes)['DEVELOPMENT']
    assert len(programme.group_ids) == 4 and len(programme.cases) == 36
    evidence = SelectedE3E4Evidence('evidence.software-c25.actual-originals', programme.identity, products, parents)
    access = original_input_access(artifact_writer=case.plane, evidence=evidence, read_access=current)
    # Explicit software reservations, not a measured memory/capacity claim.
    budget = ResourceBudget(1, 2 * 1024**3, 0, None, 512 * 1024**2, 256 * 1024**2)
    resources = SelectedE3E4OperationalSelection('resources.software-c25.development',
        tuple((phase, budget) for phase in sorted(workers.PHASES)))
    structural = ScheduledFullFactorResources('resources.software-c25.structure',
        tuple((phase, budget) for phase in ('assess', 'measure', 'reduce')))
    tasks = workers.operational_tasks(programme, bank, evidence=evidence)
    campaign = replace(case.preparation.root.campaign, campaign_id='campaign.software-c25.development',
        budget=ResourceBudget.aggregate((budget,) * len(tasks)))
    specification = SelectedE3E4ExperimentSpecification('experiment.software-c25.development', programme.identity,
        bank.identity, evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign),
        case.committed.scientific_design.e4_structure, structural)
    prefix = 'current-development-inputs'
    root = Path(case.plane.root.contract.canonical_path)
    from empirical_lawhood.api.matrix_full_factor_secondary import publish_e4_secondary_target
    secondary = publish_e4_secondary_target(writer=case.plane,directory=root/prefix/'early-secondary',
        target=specification.structure.secondary_target,bank=bank)
    records = (('bank', bank, bank.bank_id), ('campaign', campaign, campaign.campaign_id),
        ('evidence', evidence, evidence.record_id), ('programme', programme, programme.programme_id),
        ('resources', resources, resources.record_id),('secondary_readout', secondary, secondary.record_id))
    bindings, writes = [], []
    for key, record, identifier in records:
        selected_parents = access.record_parents(record)
        if selected_parents:
            pair = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=selected_parents)
        else:
            pair = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE
        path = prefix + '/' + key + '.json'
        bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record(identifier, record),
            key + '.json', len(record.canonical_bytes())))
        writes.append(ArtifactWriteRequest(identifier, path, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            'application/json', 'software.c25.development-inputs', prefix, record.canonical_bytes(),
            pair[1], tuple(row.visibility_ceiling for row in selected_parents), pair[0],
            lineage_parents=selected_parents))
    arrays = workers.contracts(programme, bank, evidence.identity, len(evidence.canonical_bytes()),
        produced_input_parents=parents, secondary_readout=secondary)[4]
    assert arrays
    original_files = tuple(case.training.template_files.values())
    file_bindings = []
    for key, artifact in arrays:
        original, = (value for value in original_files if value.identity == artifact)
        file_bindings.append(ExperimentFileInputBinding(key, artifact, original.record_version,
            original.path.relative_to(root / prefix).as_posix() if original.path.is_relative_to(root / prefix)
                else 'template.npz', artifact.size_bytes))
    # All cases select the exact same declared immutable instrument. Copy its
    # original bytes once; no resampling, new templates or model publication.
    template, = original_files
    template_raw = template.path.read_bytes()
    assert (len(template_raw), sha256(template_raw).hexdigest()) == (
        template.identity.size_bytes, template.identity.sha256)
    writes.append(ArtifactWriteRequest(template.identity.artifact_id, prefix + '/template.npz',
        template.identity.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, template.identity.media_type,
        'software.c25.development-inputs', prefix, template_raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    selector = ExperimentFileInputSelection('selection.software-c25.development', PROTOCOL_ID,
        tuple(bindings), tuple(file_bindings))
    metadata_access, metadata_visibility = produced_access(declared_access=OutcomeAccess.OUTCOME_BLIND,
        declared_visibility=VisibilityCeiling.PROSPECTIVE, parents=parents)
    for name, record, identifier in (('experiment.json', specification, specification.specification_id),
            ('sources.json', selector, selector.selection_id)):
        writes.append(ArtifactWriteRequest(identifier, prefix + '/' + name, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'software.c25.development-inputs', prefix,
            record.canonical_bytes(), metadata_visibility,
            tuple(row.visibility_ceiling for row in parents), metadata_access, lineage_parents=parents))
    access.require_current()
    # One atomic publication has exactly one evidence class. Group only the
    # actual selected input members; preserve every payload, parent and label.
    by_evidence_class = {}
    for request in writes:
        pair = request.visibility_ceiling, request.outcome_access
        by_evidence_class.setdefault(pair, []).append(request)
    publications = []
    for pair, members in sorted(by_evidence_class.items(), key=lambda item: tuple(value.value for value in item[0])):
        scope_id = 'software.c25.development-inputs.' + '.'.join(
            value.value.lower().replace('_', '-') for value in pair)
        batch = tuple(replace(request, publication_scope_id=scope_id) for request in members)
        access.require_current()
        publications.extend(case.plane.write_batch(batch))
        access.require_current()
    access.require_current()
    by_logical = {value.logical.logical_artifact_id: value.logical for value in publications}
    assert by_logical[bank.bank_id].lineage_parents == parents
    assert by_logical[bank.bank_id].outcome_access is OutcomeAccess.EVALUATION_SEALED
    assert by_logical[programme.programme_id].lineage_parents == access.record_parents(programme)
    selector_path = root / prefix / 'sources.json'
    bound = load_experiment_inputs(specification, selector_path, artifact_writer=case.plane, read_access=current)
    execution = replace(execution, source_snapshot=ObjectIdentity.from_record(
        'recursive-member.implementation', implementation_binding(ROOT)))
    service = ExperimentProgrammeService(ROOT, case.plane, _profile(case.plane))
    preparation = service.prepare(specification, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=execution)
    assert preparation.executable, preparation.dependencies
    return service, preparation, specification, selector_path


def _assert_authored_custody(*, directory, plane, parents, current, output):
    """Inspect actual final task/config publications, not preliminary rows."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans
    from empirical_lawhood.api.recursive_operations import operation_catalog

    _, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=plane,
        lazy_payloads=True, read_access=current)
    _, plan, _ = _retained_plans(payloads, draft)
    access = payloads.original_input_access
    assert access.parents == parents
    registrations, _, _ = operation_catalog()
    kinds = {value.selection.capability_key: value.config_record_type for value in registrations}
    relative = directory.relative_to(plane.root.contract.canonical_path)
    configs = []
    for task in plan.tasks:
        kind = kinds[task.capability.capability_key]
        name = 'config-' + sha256(task.task_id.encode()).hexdigest()[:24] + '.json'
        access.require_current()
        raw = payloads[name]
        record = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        expected_parents = access.record_parents(record)
        manifest = plane.read_manifest((relative / name).as_posix())
        frozen, = (value for value in task.external_inputs
            if value.logical_artifact_id == task.capability.config.artifact_id)
        assert manifest.logical.content_sha256 == frozen.expected_content_sha256 == record.fingerprint()
        assert manifest.logical.lineage_parents == expected_parents
        assert (manifest.logical.outcome_access, manifest.logical.visibility_ceiling) == (
            frozen.expected_outcome_access, frozen.expected_visibility_ceiling)
        if expected_parents:
            assert expected_parents == parents
            assert (manifest.logical.outcome_access, manifest.logical.visibility_ceiling) == produced_access(
                declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=parents)
            configs.append({'task_id': task.task_id, 'config': task.capability.config.to_document(),
                'logical': manifest.logical.to_document()})
    assert configs, 'the actual model-bearing entry configuration must retain original custody'
    graph_members = ('draft.json', 'template.json', 'scientific-projection.json', 'run-plan.json',
        'execution-plan.json', 'graph-preservation.json')
    for name in graph_members:
        access.require_current()
        logical = plane.read_manifest((relative / name).as_posix()).logical
        assert logical.lineage_parents == parents
        assert (logical.outcome_access, logical.visibility_ceiling) == produced_access(
            declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=parents)
    access.require_current()
    output.write_text(json.dumps({'model_bearing_configurations': configs,
        'graph_members': graph_members, 'original_parents': tuple(row.to_document() for row in parents)},
        sort_keys=True, indent=2) + '\n')


@pytest.mark.native
def test_actual_configured_e3_protected_parents_bootstrap_native_dev_and_ordinary_structure(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_exports import ConfiguredProtectedE3ProductExportSelection
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.product_export import _PRODUCTS, _original_product
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.scientific_read import read_protected_e3_original_products
    from empirical_lawhood.api.prospective_experiment import load_retained_prospective_experiment
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.runtime.artifacts import lineage_parent_sort_key
    from tests.test_matrix_e3_public_programme import _primary_census

    assert tmp_path.is_relative_to(EL), 'select an explicit EL pytest basetemp for this actual worker control'
    case = _exposed_inputs(tmp_path / 'original-inputs')
    original_c = case.committed.commitments.canonical_bytes()
    root = Path(case.plane.root.contract.canonical_path)
    original_directory = root / 'actual-configured-e3'
    service, selected, control, execution = _run_original(case, original_directory, monkeypatch)
    export = ConfiguredProtectedE3ProductExportSelection('export.software-c25.actual-originals',
        control.package.run_plan_id, ObjectIdentity.from_record(control.package.package_id, control.package),
        control.reveal.authority_id, 'package.software-c25.actual-originals', 'actual-original-export')
    export_path = root / 'export-selection.json'
    export_path.write_bytes(export.canonical_bytes())
    exported = service.export_products(directory=original_directory, selection_path=export_path)
    products = tuple(sorted((decode_canonical_bytes(Path(exported['paths'][name]).read_bytes(),
        MatrixSelectedOriginalProduct, maximum_bytes=1024**2) for name, _, _ in _PRODUCTS),
        key=lambda value: value.record.object_id))
    current = select_current_e3_access(products)
    retained = load_retained_prospective_experiment(directory=original_directory, project_root=ROOT,
        storage_profile=service.storage_profile, artifact_writer=case.plane)
    from empirical_lawhood.api.matrix_programme_projection import _original_e3_selection_binding
    # The real typed companion must take the compact content-binding path.
    # Literal lifetime probes alone do not establish this production shape.
    assert _original_e3_selection_binding(retained) is not retained
    with read_protected_e3_original_products(selected=retained, artifact_writer=case.plane,
            run_id=control.package.run_plan_id, expected_package=control.package,
            reveal_authority_id=control.reveal.authority_id) as read:
        full = ConfiguredMatrixSelectedFrozenPackage(export.frozen_package_record_id,
            read.specification, read.allocation, read.prefit, read.models, read.model_freeze,
            read.calibration, read.calibrated_freeze,
            tuple(sorted((*read.allocation.unit_ids('calibration'), *read.allocation.unit_ids('evaluation')))))
        public = ConfiguredMatrixSelectedPublicPackage.from_package(full)
        actual = tuple(_original_product(read, export, *row) for row in _PRODUCTS)
        assert products == tuple(sorted((value for value, _ in actual), key=lambda value: value.record.object_id))
        parents = tuple(sorted({parent for _, rows in actual for parent in rows}, key=lineage_parent_sort_key))
        assert len(parents) == 8
        assert any(row.outcome_access is OutcomeAccess.EVALUATION_SEALED for row in parents)
        assert all(value.prior_execution.run_id == control.package.run_plan_id for value in products)
        read.require_current()
        development, preparation, specification, selector = _publish_development(
            case, public, products, parents, execution, current)
        read.require_current()
    directory = root / 'actual-current-development'
    development.author(preparation=preparation, output_dir=directory, read_access=current)
    _assert_authored_custody(directory=directory, plane=case.plane, parents=parents, current=current,
        output=tmp_path / 'actual-authored-custody-proof.json')
    report = development.run(directory=directory, maximum_parallel_tasks=WORKERS, read_access=current)
    (tmp_path / 'development-report.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    assert report['status'] == 'SUCCEEDED', report
    science = report['scientific_result']['structure']
    assert science['scientific_completion'] == 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'
    assert (science['assigned_cases'], science['assigned_groups'], science['actual_pure_task_count']) == (36, 4, 73)
    assert science['new_native_contact_count'] == 0
    assert (directory / 'structure' / 'analysis').is_dir()

    def primary():
        return {path.name: _primary_census(case.plane, path.name)
            for path in (root / 'runs').iterdir() if path.is_dir() and (path / 'receipts').is_dir()}

    before = primary()
    assert len(before) >= 3

    def no_effect(*args, **kwargs):
        raise AssertionError('completed read/recovery must not start another worker')

    with monkeypatch.context() as patch:
        patch.setattr(LocalProcessExecutor, 'execute', no_effect)
        patch.setattr(LocalProcessExecutor, 'execute_deadline_free', no_effect)
        retained = development.read(directory=directory, read_access=current)
        recovered = development.recover(directory=directory, maximum_parallel_tasks=WORKERS, read_access=current)
    assert retained['scientific_result']['structure'] == science
    assert recovered['status'] == 'SUCCEEDED'
    assert primary() == before
    assert case.committed.commitments.canonical_bytes() == original_c

    # Expire the actual stored grants at their ordinary current-access clock.
    # Immutable authoring/products/receipts remain untouched; no stale bootstrap
    # result or completed receipt may authorize a new protected input read.
    class ExpiredClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2030, 1, 1, tzinfo=UTC)

    from empirical_lawhood.api import recursive_qualified_parents
    assert control.reveal.expires_at_utc < '2030-01-01T00:00:00Z'
    with monkeypatch.context() as patch:
        patch.setattr(recursive_qualified_parents, 'datetime', ExpiredClock)
        patch.setattr(LocalProcessExecutor, 'execute', no_effect)
        patch.setattr(LocalProcessExecutor, 'execute_deadline_free', no_effect)
        with pytest.raises(PermissionError):
            load_experiment_inputs(specification, selector, artifact_writer=case.plane, read_access=current)
        with pytest.raises(PermissionError):
            development.read(directory=directory, read_access=current)
    assert primary() == before
