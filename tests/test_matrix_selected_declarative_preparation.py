# SPDX-License-Identifier: MPL-2.0
"""Declarative selected preparation controls; disclosed fixtures grant no science."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_prepared_choices as scientific_choices
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_operational_resources import MatrixSelectedOperationalResources
from empirical_lawhood.api.domain_composition.matrix_selected_declarative import derivation as api
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, load_experiment_specification, prepare_experiment
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentFileInputBinding, ExperimentFileInputSelection
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key
from tests.test_matrix_selected_opportunity import opportunity, transfer, campaign_fixture, evidence_for  # noqa: F401
from tests.test_matrix_selected_revision_native import revision_case, selected_calibrated, selected_revision, selected_e4_populations, selected_bridge, confirmation_products  # noqa: F401
from tests.test_matrix_selected_protected import confirmation as protected_confirmation  # noqa: F401
from tests.test_recursive_public_service import _plane

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def disclosed_commitments():
    """Existing unpublished locator fixture, never accepted as real custody."""
    from tests.test_matrix_preparation_initialization import initialization_request
    from tests.test_matrix_selected_protected import transfer_case
    return initialization_request(transfer_case()).original_commitments


def disclose_original_commitment_seam(monkeypatch, *, expected_source_scan_bytes):
    from empirical_lawhood.api import matrix_prepared_original_commitments as custody
    def disclosed(*, writer, programme, evidence, source_scan_bytes):
        assert type(source_scan_bytes) is int and source_scan_bytes == expected_source_scan_bytes > 0
        assert evidence.original_commitments == disclosed_commitments()
        evidence.original_commitments.__post_init__()
    monkeypatch.setattr(custody, "authenticate_prepared_original_commitments", disclosed)
    disclose_produced_parent_seam(monkeypatch)


def disclosed_produced_parents(originals, development=()):
    """Literal exposed fixture labels; never real original-custody evidence."""
    rows = [ArtifactLineageParent(pin, VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED)
        for value in originals for pin in (value.record, value.prior_execution.receipt)]
    rows.extend(ArtifactLineageParent(pin, value.publication.logical.visibility_ceiling,
        value.publication.logical.outcome_access) for value in development for pin in (value.record, value.receipt))
    return tuple(sorted(set(rows), key=lineage_parent_sort_key))


def disclose_produced_parent_seam(monkeypatch):
    """Close only the already exposed original-producer metadata test boundary."""
    monkeypatch.setattr(api, 'selected_produced_input_parents',
        lambda writer, *, originals, development=(): disclosed_produced_parents(originals, development))


def science(programme, account="ORIGINAL_E3"):
    return scientific_choices.SelectedPreparedDevelopmentSpecification("specification.declarative.exposed." + account.lower(), account,
        "E5_OPPORTUNITY", len({value.root.root.independent_group_id for value in programme.sources.sources}),
        programme.point_design.arms, programme.criterion, programme.minimum_recoverable_groups, programme.tie_policy, ())


def request(programme, *, revision=None):
    evidence = evidence_for(programme)
    sources = programme.sources
    first = sources.sources[0]
    phases = ("design", "history", "assess", "measure", "frames", "project", "point", "mechanical", "responses", "response-score", "nominate")
    resources = MatrixSelectedOperationalResources("resources.selected-declarative.exposed", "OPPORTUNITY",
        tuple((phase, ResourceBudget(1, 2 * 1024**3, 0, None, 2 * 1024**3, 2 * 1024**3)) for phase in sorted(phases)))
    return domain.SelectedPreparedDerivationRequestV2("request.selected-declarative.exposed",
        sources, None, programme.reservation, MatrixSelectedPublicPackage.from_package(programme.point_design.package) if revision is None else None,
        evidence.upstream_products if revision is None else (), tuple(scientific_choices.SelectedPreparedRecipeFamily(arm,
            next(value.family_id for value in programme.point_design.interpretations if value.recipe == recipe.identity),
            next(value.scientific_premise for value in programme.point_design.interpretations if value.recipe == recipe.identity))
            for arm, recipe in programme.point_design.arms) if revision is None else (),
        None, None, None if revision is None else revision.programme.selected_package,
        None if revision is None else revision.evidence, programme.assay, programme.panels,
        campaign_fixture()[0].campaign, None, InformationCutoff("cutoff.selected-declarative.exposed",
            first.coordinate.clock_id, CausalPhase.PREPARATION, Decimal(0)), "operator.disclosed-release-validation",
        None, None, (), (), (), resources, None, disclosed_commitments(),
        disclosed_produced_parents(evidence.upstream_products) if revision is None else
        disclosed_produced_parents((revision.evidence.downstream_nomination, revision.evidence.calibration),
            (revision.evidence.revision_fit, revision.evidence.revision_freeze,
                *((revision.evidence.preparation_nomination,) if revision.evidence.preparation_nomination is not None else ()))))


def selection(specification, selected_request, original):
    programme, evidence = domain.make_programme(specification, selected_request, e3_package=original.point_design.package)
    return domain.SelectedPreparedDerivedSelectionV4("selection.selected-declarative.exposed",
        specification.identity, selected_request, programme, evidence)


def handles(lowered):
    return {key: PreparedExperimentFile(artifact, "1.0.0",
        Path("/media/chevre/EL/empirical-lawhood/scratch/disclosed-unpublished") / str(index), artifact.size_bytes)
        for index, (key, artifact) in enumerate(lowered.input_artifacts)}


def test_current_selection_roundtrips_exact_science_and_direct_input_graph(opportunity):  # noqa: F811
    spec, current_request = science(opportunity), request(opportunity)
    current = selection(spec, current_request, opportunity)
    raw = current.canonical_bytes()
    reopened = decode_canonical_bytes(raw, type(current), maximum_bytes=None)
    assert reopened == current and reopened.canonical_bytes() == raw
    graph = domain.lower(spec, current).draft
    assert domain.lower(spec, reopened).draft.canonical_bytes() == graph.canonical_bytes()
    assert any(operation.selection.capability_key.endswith(".direct-inputs")
        for operation in graph.operations)
    assert current.request == current_request
    assert current.evidence.original_commitments == current_request.original_commitments
    assert domain.derived_selection_types() == (domain.SelectedPreparedDerivedSelectionV4, domain.SelectedPreparedDerivedSelectionV5)


@pytest.mark.parametrize("schema", (
    "empirical-lawhood/matrix-experimental-programme/selected-declarative-derived-selection",
    "empirical-lawhood/matrix-experimental-programme/selected-declarative-derived-selection-v2",
    "empirical-lawhood/matrix-experimental-programme/selected-declarative-derived-selection-v3",
))
def test_current_selection_codec_refuses_retired_graph_schemas(opportunity, schema):  # noqa: F811
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    spec, selected_request = science(opportunity), request(opportunity)
    current = selection(spec, selected_request, opportunity)
    document = current.to_document()
    document["schema"] = schema
    with pytest.raises(ValueError, match="schema"):
        decode_canonical_bytes(canonical_json_document_bytes(document), domain.SelectedPreparedDerivedSelectionV4, maximum_bytes=None)


def test_supported_threshold_edit_derives_programme_graph_allocation_and_real_capability_census(opportunity):  # noqa: F811
    spec, selected = science(opportunity), request(opportunity)
    original_bytes = opportunity.canonical_bytes()
    first = selection(spec, selected, opportunity)
    edited = replace(spec, criterion=replace(spec.criterion, normalized_error_maximum=spec.criterion.normalized_error_maximum / Decimal(2)))
    second = selection(edited, selected, opportunity)
    assert first.programme.sources is selected.development_sources
    assert second.programme.sources is selected.development_sources
    assert second.programme.criterion == edited.criterion != first.programme.criterion
    assert second.programme.identity != first.programme.identity
    assert second.programme.point_design.package == first.programme.point_design.package
    lowered = domain.lower(edited, second)
    bound = domain.bind_inputs(edited, {"selection": second}, files=handles(lowered))
    result = prepare_experiment(edited, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection(workers=4, environment_id="main.exposed",
            source_snapshot=edited.identity, output_root="/media/chevre/EL/empirical-lawhood/scratch/exposed"))
    assert result.executable and result.draft == lowered.draft
    assert len(result.allocation.units) == spec.expected_groups
    assert result.census.native_effect_count == 2 * spec.expected_sources
    declarations = {value.registration().selection: value for value in domain.owner_for(edited).operation_declarations()}
    expected_outputs = sum(len(declarations[operation.selection].outputs) for operation in lowered.draft.operations)
    assert sum(value for _, value in result.census.output_counts) == expected_outputs
    domain.validate_instance(specification=edited, allocation=result.allocation, draft=result.draft, source_records=result.design_records)
    with pytest.raises(ValueError, match="declaration|scientific"):
        domain.validate_selection(spec, second)
    assert b'"scores"' not in second.programme.canonical_bytes()
    assert opportunity.canonical_bytes() == original_bytes


def test_recipe_edit_is_explicit_preserves_original_starts_and_refuses_invalid_restored_context(opportunity):  # noqa: F811
    spec, selected = science(opportunity), request(opportunity)
    index = next(index for index, (_, value) in enumerate(spec.arms) if value.kind != "HOLD")
    arm, recipe = spec.arms[index]
    couplings = list(recipe.half_tick_couplings)
    row = couplings[1]
    couplings[1] = (row[0] + Decimal("0.001"), row[1])
    edited_recipe = replace(recipe, half_tick_couplings=tuple(couplings))
    arms = tuple((name, edited_recipe if name == arm else value) for name, value in spec.arms)
    # Recipe feature interpretations are explicit scientific operands, not an
    # inferred temperature-to-family rule.
    edited = replace(spec, arms=arms)
    bank = domain.derive_sources(edited, selected)
    assert bank != selected.development_sources
    assert {value.initial for value in bank.sources} == {value.initial for value in selected.development_sources.sources}
    bad = replace(edited_recipe, half_tick_couplings=(*edited_recipe.half_tick_couplings[:-1], (Decimal(999), Decimal(999))))
    with pytest.raises(ValueError, match="restored handoff"):
        domain.derive_sources(replace(spec, arms=tuple((name, bad if name == arm else value) for name, value in arms)), selected)


def test_unsigned_copied_request_refuses_loader_and_cold_binding_reports_derivation(opportunity, tmp_path):  # noqa: F811
    assert tmp_path.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    spec, selected = science(opportunity), request(opportunity)
    (tmp_path / "specification.json").write_bytes(spec.canonical_bytes())
    (tmp_path / "request.json").write_bytes(selected.canonical_bytes())
    source = ExperimentFileInputSelection("sources.selected-declarative.unbound", domain.DEVELOPMENT_PROTOCOL_ID,
        (ExperimentInputBinding("request", selected.identity, "request.json", len(selected.canonical_bytes())),), ())
    (tmp_path / "sources.json").write_bytes(source.canonical_bytes())
    declaration = load_experiment_specification(tmp_path / "specification.json")
    with pytest.raises(PermissionError, match="actual selected artifact writer"):
        load_experiment_inputs(declaration, tmp_path / "sources.json")
    # Cold typed construction checks graph dependencies; it supplies no custody.
    loaded = domain.bind_inputs(declaration, {"request": selected})
    result = prepare_experiment(declaration, scientific_inputs=loaded.scientific_inputs, method_inputs=loaded.method_inputs,
        execution=ExecutionSelection(workers=4))
    assert result.draft is None and not result.executable
    assert any(value.source_key == "request" for value in result.dependencies)
    assert loaded.method_inputs.request == selected
    assert decode_canonical_bytes(selected.canonical_bytes(), type(selected), maximum_bytes=None) == selected


def test_revision_route_reuses_actual_paired_point_owner_and_does_not_fallback_to_e3(revision_case):  # noqa: F811
    case = revision_case
    spec, selected = science(case.original, "REVISION"), request(case.original, revision=case)
    programme, evidence = domain.make_programme(spec, selected, excluded_groups=case.programme.excluded_group_ids)
    assert programme.selected_package is case.programme.selected_package
    assert programme.criterion == spec.criterion
    assert programme.excluded_group_ids == case.programme.excluded_group_ids
    bound = domain.SelectedPreparedDerivedSelectionV4("selection.declarative.revision", spec.identity, selected, programme, evidence)
    graph = domain.lower(spec, bound).draft
    assert all("revision" in value.selection.capability_key or "matrix-coupling-preparation" in value.selection.capability_key
        for value in graph.operations)
    with pytest.raises(ValueError, match="E4 producer"):
        domain.make_programme(spec, replace(selected, revision=None), excluded_groups=())


def test_actual_typed_e4_projection_fills_revision_request_and_preserves_unentered_gate(
        revision_case, selected_calibrated, monkeypatch):  # noqa: F811
    # Pure disclosed record projection only; no unpublished locator is accepted
    # as custody. The full public exporter still requires an actual E4 run.
    from empirical_lawhood.api import selected_e4_revision_export as export
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as e4
    case, fitted = revision_case, selected_calibrated
    spec, selected = science(case.original, "REVISION"), request(case.original, revision=case)
    empty = replace(selected, revision=None, revision_evidence=None)
    before = empty.canonical_bytes()
    confirmation = confirmation_products(fitted)
    nomination = e4.nominate_downstream(confirmation.specification, confirmation.result, fitted.export,
        confirmation.public_calibration, record_id=case.evidence.downstream_nomination.record.object_id)
    operands = dict(specification=spec, request=empty, revision=fitted.export, nomination=nomination,
        revision_fit=case.evidence.revision_fit, revision_freeze=case.evidence.revision_freeze,
        calibration_product=case.evidence.calibration, downstream_nomination=case.evidence.downstream_nomination)
    ready = export._project_revision_request(**operands)
    assert empty.canonical_bytes() == before and empty.revision is None and empty.revision_evidence is None
    assert ready.revision.models.original == fitted.export.models.identity
    assert ready.revision.models.revision_parameters == selected.revision.models.revision_parameters
    assert ready.revision.nomination == nomination.identity == case.evidence.downstream_nomination.record
    assert ready.revision.original_calibration == case.evidence.calibration.record
    temporary = domain.revision_programme(spec, ready)
    assert ready.revision_evidence.programme == temporary.identity
    programme, evidence = domain.make_programme(spec, ready, excluded_groups=case.programme.excluded_group_ids)
    assert programme.identity != temporary.identity
    assert evidence.programme == programme.identity and programme.selected_package == ready.revision
    assert (evidence.revision_fit, evidence.revision_freeze, evidence.downstream_nomination, evidence.calibration,
        evidence.public_calibration, evidence.revision_export, evidence.original_e3_package) == (
        case.evidence.revision_fit, case.evidence.revision_freeze, case.evidence.downstream_nomination,
        case.evidence.calibration, case.evidence.public_calibration, case.evidence.revision_export,
        case.evidence.original_e3_package)
    assert decode_canonical_bytes(ready.canonical_bytes(), type(ready), maximum_bytes=None) == ready
    with pytest.raises(ValueError, match="freeze"):
        export._project_revision_request(**{**operands, "revision_fit": case.evidence.revision_freeze})
    # These knowable input refusals occur before any service/retained-run read.
    with pytest.raises(TypeError, match="revision DEV"):
        export.derive_selected_e4_revision_request(service=object(), directory=None, programme_request_path=None,
            specification=replace(spec, account="ORIGINAL_E3"), request=empty)
    with pytest.raises(ValueError, match="empty revision"):
        export.derive_selected_e4_revision_request(service=object(), directory=None, programme_request_path=None,
            specification=spec, request=selected)
    rule = replace(confirmation.rule, required_rejected_comparisons=("e4.revision-baseline",))
    refused_spec = replace(confirmation.specification, nomination_rule=rule)
    refused_result = replace(confirmation.result, specification=refused_spec.identity, nomination_rule=rule)
    refused = e4.nominate_downstream(refused_spec, refused_result, fitted.export,
        confirmation.public_calibration, record_id="downstream.nomination.unentered-export-control")
    assert refused.selected is None
    def no_programme(*args, **kwargs):
        pytest.fail("unentered E4 decision attempted downstream source/programme derivation")
    monkeypatch.setattr(domain, "revision_programme", no_programme)
    with pytest.raises(PermissionError, match="remains unentered"):
        export._project_revision_request(**{**operands, "nomination": refused})


def test_foreign_current_source_or_original_custody_refuses_before_any_metadata_publication(opportunity, monkeypatch):  # noqa: F811
    spec, selected = science(opportunity), request(opportunity)
    disclose_produced_parent_seam(monkeypatch)
    head = selected.development_sources.sources[0].provenance.observed_git_head
    monkeypatch.setattr(api, "capture_admitted_target_source", lambda root: SimpleNamespace(
        implementation_commit="f" * 40 if head != "f" * 40 else "e" * 40, implementation_sha256="a" * 64))
    monkeypatch.setattr(api, "original_e3_package", lambda *args: pytest.fail("read original before current source admission"))
    with pytest.raises(ValueError, match="current producing provenance"):
        api.derive_authenticated_selection(spec, selected, writer=object(), project_root=ROOT)
    monkeypatch.setattr(api, "capture_admitted_target_source", lambda root: SimpleNamespace(
        implementation_commit=head, implementation_sha256="a" * 64))
    def refuse(*args, read_access):
        assert read_access is None
        raise PermissionError("original current grant refused")
    monkeypatch.setattr(api, "original_e3_package", refuse)
    with pytest.raises(PermissionError, match="original current grant"):
        api.derive_authenticated_selection(spec, selected, writer=object(), project_root=ROOT)


def literal_files(programme):
    initial, _ = encode_matrix_arrays({"positions": np.zeros((2, 3, 4, 4), dtype="<c16"),
        "momenta": np.zeros((2, 3, 4, 4), dtype="<c16")})
    templates, _ = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"),
        "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"), "trace_coefficients": np.zeros((2, 3), dtype="<f8"),
        "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    result = {value.initial.array_artifact: initial for value in programme.sources.sources}
    result[programme.assay.template_artifact] = templates
    assert all(sha256(raw).hexdigest() == artifact.sha256 and len(raw) == artifact.size_bytes for artifact, raw in result.items())
    return result


def test_public_cli_refuses_unsigned_sources_before_metadata_or_native_contact(opportunity, tmp_path, monkeypatch):  # noqa: F811
    from typer.testing import CliRunner
    from empirical_lawhood.cli.app import app
    from empirical_lawhood.cli import integrations
    from empirical_lawhood.infrastructure import bounded_io
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor

    writer = _plane(tmp_path / "plane")
    plane = Path(writer.root.contract.canonical_path)
    spec, selected = science(opportunity), request(opportunity)
    (plane / "specification.json").write_bytes(spec.canonical_bytes())
    request_path = plane / "request.json"
    request_path.write_bytes(selected.canonical_bytes())
    files = []
    protected_paths = {request_path}
    for index, (artifact, raw) in enumerate(literal_files(opportunity).items()):
        name = "original-file." + str(index) + ".npz"
        path = plane / name
        path.write_bytes(raw)
        protected_paths.add(path)
        files.append(ExperimentFileInputBinding("file." + str(index), artifact, "1.0.0", name, len(raw)))
    source = ExperimentFileInputSelection("sources.declarative.unsigned", domain.DEVELOPMENT_PROTOCOL_ID,
        (ExperimentInputBinding("request", selected.identity, "request.json", len(selected.canonical_bytes())),), tuple(files))
    source_path = plane / "sources.json"
    source_path.write_bytes(source.canonical_bytes())
    read = bounded_io.read_bounded_bytes
    def refuse_protected_body(path, **kwargs):
        assert Path(path) not in protected_paths, "unsigned request/FILE opened before original locator admission"
        return read(path, **kwargs)
    def forbidden(*args, **kwargs):
        pytest.fail("unsigned copied inputs reached derivation, publication or native dispatch")
    monkeypatch.setattr(bounded_io, "read_bounded_bytes", refuse_protected_body)
    monkeypatch.setattr(api, "derive_authenticated_selection", forbidden)
    monkeypatch.setattr(ExternalArtifactPlane, "write", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute_deadline_free", forbidden)
    monkeypatch.setattr(integrations, "_storage", lambda: (ROOT, SimpleNamespace(maximum_parallel_tasks=4), writer))
    args = ["--project-root", str(ROOT), "campaign", "experiment-derive-inputs", "--input", str(plane / "specification.json"),
        "--sources", str(source_path), "--metadata-directory", str(plane / "derived"),
        "--output-selection", str(plane / "current-sources.json"), "--environment-id", "main.exposed",
        "--attempt-dir", str(plane / "attempt"), "--progress-file", str(plane / "progress.json")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code != 0 and "complete canonical locator roster" in result.stdout + result.stderr
    assert source_path.read_bytes() == source.canonical_bytes()
    assert not (plane / "derived").exists() and not (plane / "current-sources.json").exists()
    assert (plane / "attempt" / "invocation.json").is_file()


def test_exact_phase_resources_derive_all_actual_task_cells_without_a_task_map(opportunity):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
    from tests.test_matrix_e3_protected_public_lowering import resource_selection
    spec, selected = science(opportunity), request(opportunity)
    bound = selection(spec, selected, opportunity)
    lowered = domain.lower(spec, bound)
    rules = resource_selection(maximum_parallel_tasks=4)
    owner = domain.owner_for(spec)
    operational = SelectedE4OperationalResources("resources.declarative.explicit",
        replace(rules.resources, aggregate_memory_ceiling_bytes=8 * 1024**3),
        tuple((phase, 100) for phase in sorted(owner.PHASES)), rules.native_progress, 1)
    # This pure projection checks existing cells only, without issuing a DEV
    # study or claiming that ordinary DEV has an issued aggregate envelope.
    projection = domain.resource_selection(spec, SimpleNamespace(request=SimpleNamespace(operational_resources=operational)), lowered.draft)
    assert projection.maximum_parallel_tasks == 4
    assert {value.task_id for value in projection.task_cells} == {value.node_id for value in lowered.draft.operations}
    assert sum(value.physical_execution_cost for value in projection.task_cells) == 2 * spec.expected_sources
    by_task = {value.node_id: value.resource_budget for value in lowered.draft.operations}
    for cell in projection.task_cells:
        budget = by_task[cell.task_id]
        assert (cell.resource_budget.cpu_cores, cell.resource_budget.memory_bytes, cell.resource_budget.output_bytes,
            cell.resource_budget.source_byte_limit) == (budget.cpu_cores, budget.memory_bytes, budget.output_bytes, budget.source_scan_bytes)
    tiny = replace(operational, controls=replace(operational.controls, aggregate_memory_ceiling_bytes=1))
    with pytest.raises(ValueError, match="aggregate"):
        domain.resource_selection(spec, SimpleNamespace(request=SimpleNamespace(operational_resources=tiny)), lowered.draft)


def test_public_workflow_inventory_declares_both_copied_examples_and_derivation_command():
    from empirical_lawhood.api.workflows import list_workflows
    workflow, = (value for value in list_workflows() if value.workflow_id == "matrix-selected-revision")
    expected = {
        "programmes/foundations/emergent-structure/workflows/matrix-selected-revision/declarative-opportunity.example.json": scientific_choices.SelectedPreparedDevelopmentSpecification.SCHEMA,
        "programmes/foundations/emergent-structure/workflows/matrix-selected-revision/declarative-transfer.example.json": scientific_choices.SelectedPreparedProtectedSpecification.SCHEMA,
        "programmes/foundations/emergent-structure/workflows/matrix-selected-revision/initialization.example.json": "empirical-lawhood/matrix-experimental-programme/initialization-specification",
        "programmes/foundations/emergent-structure/workflows/matrix-selected-revision/initialization.sources.example.json": "empirical-lawhood/experiment-inputs/file-selection",
    }
    assert {value.path: value.schema_id for value in workflow.inputs} == expected
    derive, = (value for value in workflow.operations if value.command == "campaign experiment-derive-inputs")
    specifications = {path: schema for path, schema in expected.items() if path.endswith((
        "declarative-opportunity.example.json", "declarative-transfer.example.json"))}
    assert set(derive.inputs) == set(specifications)
    for path, schema in specifications.items():
        record = load_experiment_specification(ROOT / path)
        assert record.SCHEMA == schema
        assert record.account == 'REVISION' and record.criterion.is_matched
        assert record.expected_groups == (16 if record.phase == 'E5_OPPORTUNITY' else 64)
        assert record.minimum_recoverable_groups == 2 and record.criterion.horizon_tick == 64
        assert all(recipe.effort == 8 and recipe.primary_steps == 256 for _, recipe in record.arms)


def test_current_prepared_menu_refuses_an_equal_effort_undeclared_ramp():
    from decimal import Decimal
    record = load_experiment_specification(ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-selected-revision/declarative-opportunity.example.json')
    recipes = dict(record.arms)
    early = recipes['early']
    values = list(early.half_tick_couplings)
    values[100] = (values[100][0] + Decimal('.0000000001'), values[100][1])
    changed = replace(early, half_tick_couplings=tuple(values))
    assert changed.effort == early.effort == 8
    with pytest.raises(ValueError, match='exact fixed early/delayed'):
        replace(record, arms=tuple((arm, changed if arm == 'early' else recipe) for arm, recipe in record.arms))


def test_changed_original_selector_refuses_before_first_publication(opportunity, tmp_path, monkeypatch):  # noqa: F811
    writer = _plane(tmp_path / "changed-selector-plane")
    plane = Path(writer.root.contract.canonical_path)
    spec, selected = science(opportunity), request(opportunity)
    (plane / "request.json").write_bytes(selected.canonical_bytes())
    files = []
    for index, (artifact, raw) in enumerate(literal_files(opportunity).items()):
        name = "original." + str(index) + ".npz"
        (plane / name).write_bytes(raw)
        files.append(ExperimentFileInputBinding("file." + str(index), artifact, "1.0.0", name, len(raw)))
    original = ExperimentFileInputSelection("sources.declarative.change-control", domain.DEVELOPMENT_PROTOCOL_ID,
        (ExperimentInputBinding("request", selected.identity, "request.json", len(selected.canonical_bytes())),), tuple(files))
    source = plane / "sources.json"
    source.write_bytes(original.canonical_bytes())
    head = selected.development_sources.sources[0].provenance.observed_git_head
    monkeypatch.setattr(api, "capture_admitted_target_source", lambda root: SimpleNamespace(
        implementation_commit=head, implementation_sha256="a" * 64))
    from empirical_lawhood.api import experiment_preparation as preparation_api
    # Disclosed post-authentication unit seam only. No copied-input bootstrap,
    # original authority or issued/public success is asserted by this control.
    bound = selection(spec, selected, opportunity)
    cold = domain.bind_inputs(spec, {"request": selected}, files={value.key: PreparedExperimentFile(
        value.identity, value.record_version, plane / value.relative_path, value.maximum_bytes) for value in original.files})
    def loaded(actual_specification, path, *, artifact_writer, read_access):
        assert actual_specification == spec and Path(path) == source and read_access is None
        assert artifact_writer.root.contract == writer.root.contract
        return cold
    def derived(actual_specification, actual_request, *, writer, project_root, read_access, _admitted_source):
        assert actual_specification == spec and actual_request == selected and project_root == ROOT and read_access is None
        return bound
    monkeypatch.setattr(preparation_api, "load_experiment_inputs", loaded)
    monkeypatch.setattr(api, "derive_authenticated_selection", derived)
    actual_plan = api.plan_current_metadata
    def changed_selector(*args, **kwargs):
        planned = actual_plan(*args, **kwargs)
        source.write_bytes(b"changed selected input")
        return planned
    monkeypatch.setattr(api, "plan_current_metadata", changed_selector)
    monkeypatch.setattr(writer, "write", lambda value: pytest.fail("changed selector reached publication"))
    destination, metadata = plane / "derived.json", plane / "metadata"
    with pytest.raises(ValueError, match="selector changed"):
        api.derive_inputs(specification=spec, source_selection_path=source, project_root=ROOT, artifact_writer=writer,
            metadata_directory=metadata, output_selection_path=destination,
            execution=ExecutionSelection(workers=4, environment_id="main.exposed", source_snapshot=spec.identity,
                output_root=str(plane / "outputs")))
    assert not destination.exists() and not metadata.exists()


def _protected_formal_graph(original, *, revision=None):
    """Real installed graph/compiler over unpublished TEST custody only.

    The source access descriptors and original entry pin are disclosed compiler
    fixtures. No source qualification, issue, grant, execution or native work is
    performed or claimed by this control.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as original_owner
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as revision_owner
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedEntryEvidenceV3, MatrixRevisionEntryEvidenceV2
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec, RecursiveStudyDraft
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from tests.test_matrix_selected_protected import root_inputs
    from tests.matrix_selected_e4_public_fixture import _source_admissions
    owner = original_owner if revision is None else revision_owner
    programme = original
    if revision is not None:
        programme = replace(revision.programme, record_id="programme.disclosed.protected-formal." + original.phase.lower().replace("_", "-"),
            phase=original.phase, sources=original.sources, reservation=original.sources.closure.reservation,
            arms=original.point_design.arms, expected_groups=original.point_design.expected_groups,
            assay=original.assay, panels=original.panels, criterion=original.criterion,
            transfer_domain_claims=original.transfer_domain_claims,
            preparation_nomination=ObjectIdentity("nomination.disclosed.unpublished-phase",
                "empirical-lawhood/matrix-experimental-programme/revision-programme-assessment", "1.0.0", "a" * 64)
                if original.phase == "E5_CONFIRMATION" else None)
    arguments = root_inputs(original)
    root = arguments["root"]
    if revision is None:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
    sources = tuple(value for _, value in programme.sources.source_arms())
    endpoints = tuple(sorted({(value.coordinate.clock_id, value.coordinate.physical_time(value.total_ticks)) for value in sources}))
    cutoffs = tuple(InformationCutoff("cutoff.disclosed.phase." + str(index), clock, CausalPhase.PRE_ACTION, endpoint)
        for index, (clock, endpoint) in enumerate(endpoints))
    clocks = {value.clock_id: value for value in root.system.clocks}
    for source in sources:
        clocks[source.coordinate.clock_id] = replace(root.system.clocks[0], clock_id=source.coordinate.clock_id,
            nominal_period=source.primary_view.timestep)
    experiment = replace(root.experiment, information_cutoffs=cutoffs,
        obligations=replace(root.experiment.obligations, support=replace(root.experiment.obligations.support,
            physical_unit_count=len(root.evaluation_unit_ids), information_cutoff_id=cutoffs[0].cutoff_id,
            denominator_cell_ids=tuple(sorted("case." + value.source_id for value in sources)))))
    old = domain.pin(root.experiment, "experiment_id")
    campaign = replace(root.campaign, budget=ResourceBudget(4, 8 * 1024**3, 0, None, 128 * 1024**3, 128 * 1024**3), nodes=tuple(replace(value, object_identity=domain.pin(experiment, "experiment_id"))
        if value.object_identity == old else value for value in root.campaign.nodes))
    designs = list(root.design_inputs)
    references = {value for source in sources for value in owner.preparation.operands(source)}
    if revision is None:
        references.update((programme.identity, programme.original_programme))
    for reference in sorted(references, key=lambda value: value.object_id):
        if reference not in {value.object_identity for value in designs}:
            designs.append(replace(root.design_inputs[0], input_id="design." + reference.object_id,
                object_identity=reference, materialization_sha256=reference.object_fingerprint))
    if revision is not None:
        for reference in (programme.identity, programme.selected_package.identity):
            designs.append(replace(root.design_inputs[0], input_id="design." + reference.object_id,
                object_identity=reference, materialization_sha256=reference.object_fingerprint))
    designs = tuple(sorted(designs, key=lambda value: value.input_id))
    root = replace(root, system=replace(root.system, clocks=tuple(clocks[key] for key in sorted(clocks))),
        experiment=experiment, campaign=campaign, resource_ceiling=campaign.budget, design_inputs=designs,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(value.input_id for value in designs)))
    kind = MatrixSelectedEntryEvidenceV3 if revision is None else MatrixRevisionEntryEvidenceV2
    evidence = ObjectIdentity("evidence.disclosed.unpublished-phase", kind.SCHEMA, kind.VERSION, "a" * 64)
    if revision is None:
        from tests.test_matrix_e6_transport_assessment import exposed_parent_census
        parents = exposed_parent_census(programme)
    else:
        parents = disclosed_produced_parents((revision.evidence.downstream_nomination, revision.evidence.calibration),
            (revision.evidence.revision_fit, revision.evidence.revision_freeze,
                *((revision.evidence.preparation_nomination,) if revision.evidence.preparation_nomination is not None else ())))
    configs, external, links, records, arrays = owner.contracts(programme, evidence, 1,
        produced_input_parents=parents)
    declarations = {value.registration().selection: value for value in owner.operation_declarations()}
    def declaration(config):
        version = (owner.config_capability_version(config) if revision is None else
            "2.0.0" if type(config) in (*owner.preparation.native_config_types(), owner.MatrixRevisionRootConfigV2) else "1.0.0")
        key = owner.capability_key(config.phase, version) if revision is None else owner.capability_key(config.phase, "PROTECTED", version)
        return next(value for value in declarations.values() if value.capability_key == key)
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node, selection=declaration(config).registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=ResourceBudget(1, 2 * 1024**3, 0, None, 2 * 1024**3, 2 * 1024**3))
        for node, config in configs)
    draft = RecursiveStudyDraft("draft.disclosed.protected-formal." + programme.phase.lower().replace("_", "-"), root.question, campaign, (), (), (),
        operations, external, links, tuple(node for node, _ in configs), prospective_draft=root)
    # The unpublished entry pin is an explicit compiler seam, never a source
    # body or successful receipt. The helper needs only its declared revision.
    entry_external, = (value for value in external if value.logical_artifact_id == evidence.object_id)
    records = (*records, (entry_external.input_id, SimpleNamespace(VERSION=kind.VERSION)))
    retained = tuple(value.input_id for value in external if value.scientific_role == "HISTORY")
    source_configs, qualifications = _source_admissions(draft, records, arrays, root=root,
        prefix="disclosed.protected-formal." + programme.phase.lower().replace("_", "-"),
        observation_operator=programme.assay.identity, retained_history_ids=retained)
    by_input = dict(records)
    versions = {value.logical_artifact_id: by_input[value.input_id].VERSION
        if value.input_id in by_input else "1.0.0" for value in external}
    draft = _source_projection(draft, SimpleNamespace(qualifications=qualifications, source_configs=source_configs), versions,
        retained_history_ids=retained)
    assert {value.source_id for value in qualifications} == {value.input_id for value in external} - set(retained)
    assert {value.source_id for value in draft.prospective_draft.source_materializations} == {value.source_id for value in qualifications}
    selected = {value.selection for value in operations}
    declarations = tuple(value for selection, value in declarations.items() if selection in selected)
    registry = CapabilityRegistry("registry.disclosed.protected-formal", tuple(sorted(
        (value.manifest() for value in declarations), key=lambda value: value.registry_id)))
    return SimpleNamespace(draft=draft, programme=programme, owner=owner, declarations=declarations,
        registry=registry, qualifications=qualifications)


def _protected_formal_request(case, draft):
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess
    from empirical_lawhood.kernel.worlds import EvidenceUnitScope
    from empirical_lawhood.planning.formal_analysis import (
        FormalGapSourceCapabilityInventory, FormalMethodBinding, FormalMethodCatalog, FormalMethodRole,
        derive_formal_gap_applicability,
    )
    from empirical_lawhood.planning.formal_gaps import FormalGapCoverageAssignment, FormalGapCoverageDisposition
    from tests.experiment_entry_support import entry_package_for_draft
    root = draft.prospective_draft
    entry = entry_package_for_draft(root)
    operation, declaration = domain._protected_assessor(draft, case.owner)
    manifest = declaration.manifest()
    control = root.experiment.controls[0].control_id
    gaps = tuple(replace(value, minimum_independent_units=len(root.evaluation_unit_ids),
        maximum_claim_ceiling=EvidenceCeiling.RESPONSE, control_ids=(control,)) for value in entry.register.gaps)
    register = replace(entry.register, gaps=gaps)
    # Deliberately stale address: derivation must use the actual newly admitted
    # locks, not this old copied source pin, while retaining all formal facts.
    inventory = FormalGapSourceCapabilityInventory("inventory.disclosed.phase", "denominator.before-derived-phase",
        entry.checklist.portfolio_world, (ObjectIdentity("source.before-derived-phase", "empirical-lawhood/testing/old-source", "1.0.0", "b" * 64),),
        ("operand.fixture",), ("support.fixture",), root.evaluation_unit_ids, EvidenceUnitScope.PHYSICAL_INDEPENDENT_UNIT,
        (), ("estimator.fixture",), (control,), ("multiplicity.fixture",), (), (),
        EvidenceCeiling.RESPONSE, OutcomeAccess.OUTCOME_BLIND)
    assignments = tuple(FormalGapCoverageAssignment(value.gap_id, FormalGapCoverageDisposition.TEST_IN_THIS_ACT, None, (),
        "estimator.fixture", (control,), "multiplicity.fixture", (root.experiment.obligations.uncertainty.uncertainty_id,),
        ("old-output",), ("old-node",)) for value in register.gaps)
    coverage = replace(entry.coverage, register=domain.pin(register, "register_id"), candidate_act_id="draft.before-derived-phase",
        denominator_id=inventory.denominator_id, applicability=derive_formal_gap_applicability(register, inventory), assignments=assignments)
    entry = replace(entry, register=register, coverage=coverage, checklist=replace(entry.checklist,
        formal_gap_register=domain.pin(register, "register_id"), formal_gap_coverage=domain.pin(coverage, "coverage_id")))
    product = next(value for value in declaration.outputs if value.output_id == "product")
    catalog = FormalMethodCatalog("catalog.disclosed.phase", tuple(sorted((FormalMethodBinding(family, role,
        manifest.capability_key, manifest.capability_version, manifest.implementation_sha256, tuple(value.gap_id for value in register.gaps),
        declaration.config_record_type.SCHEMA, product.payload_schema, EvidenceCeiling.RESPONSE, OutcomeAccess.EVALUATOR_REVEAL)
        for family, role in (("estimator.fixture", FormalMethodRole.ESTIMATOR), ("multiplicity.fixture", FormalMethodRole.MULTIPLICITY))),
        key=lambda value: value.binding_id)))
    return SimpleNamespace(entry=entry, formal_methods=catalog, formal_source_inventories=(inventory,))


@pytest.mark.parametrize("phase", ("E5_CONFIRMATION", "E6_TRANSFER"))
@pytest.mark.parametrize("account", ("ORIGINAL_E3", "REVISION"))
def test_current_protected_phase_actual_candidate_compile_and_formal_refusals(transfer, request, phase, account):  # noqa: F811
    from empirical_lawhood.planning.experiment_entry import StudyDefinition
    from empirical_lawhood.runtime.candidate_compiler import (
        CandidateCompilationDisposition, CandidateDiagnosticCode, StandardCandidateCompilationContext,
        compile_study_candidate, _required_obligation_ids,
    )
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    original = transfer if phase == "E6_TRANSFER" else request.getfixturevalue("protected_confirmation")
    revision = request.getfixturevalue("revision_case") if account == "REVISION" else None
    case = _protected_formal_graph(original, revision=revision)
    assert sum(value.selection.capability_key.endswith(".direct-inputs") for value in case.draft.operations) == 2 * len(
        case.programme.source_arms() if revision is not None else case.programme.sources.source_arms())
    historical = case.draft.canonical_bytes()
    draft = domain._bind_protected_obligations(case.draft, case.programme, case.owner)
    canonical = set(_required_obligation_ids(draft.prospective_draft.experiment))
    assessor, _ = domain._protected_assessor(draft, case.owner)
    assert canonical <= set(assessor.obligation_ids)
    assert all(sum(key in value.obligation_ids for value in draft.operations) == 1 for key in canonical)
    assert case.draft.canonical_bytes() == historical
    selected = _protected_formal_request(case, draft)
    saved = tuple(value.canonical_bytes() for value in (selected.entry, *selected.formal_source_inventories))
    entry, inventories = domain._protected_formal_entry(draft, selected, case.owner)
    assert entry.coverage.candidate_act_id == draft.prospective_draft.draft_id
    assert entry.coverage.denominator_id == draft.prospective_draft.system.system_id
    assert inventories[0].source_materializations == tuple(sorted((value.materialization
        for value in draft.prospective_draft.source_materializations), key=lambda value: value.object_id))
    assert inventories[0].independent_unit_ids == selected.formal_source_inventories[0].independent_unit_ids
    assert entry.register == selected.entry.register
    assert tuple((value.obligation_ids, value.selected_estimator_family_id, value.selected_multiplicity_family_id)
        for value in entry.coverage.assignments) == tuple((value.obligation_ids, value.selected_estimator_family_id,
            value.selected_multiplicity_family_id) for value in selected.entry.coverage.assignments)
    assert tuple(value.canonical_bytes() for value in (selected.entry, *selected.formal_source_inventories)) == saved
    compilation = compile_recursive_wave(draft=draft, registrations=tuple(value.registration() for value in case.declarations),
        registry=case.registry, implementation_commit="a" * 40, qualifications=case.qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,
        output_codecs={key: kind for value in case.declarations for key, kind in value.record_codecs.items()})
    assert compilation.candidate_report.disposition is CandidateCompilationDisposition.COMPILED_AUTHORITY_PENDING, compilation.candidate_report.diagnostics
    assert all(value.required_output_id == "adjudication" and value.proof_owner_node_id == assessor.node_id
        for value in compilation.template.coverage.bindings if value.obligation_id in canonical)
    authoring = StudyDefinition("authoring.disclosed.protected-formal", compilation.candidate_draft, entry)
    context = StandardCandidateCompilationContext("context.disclosed.protected-formal", compilation.candidate_context,
        selected.formal_methods, inventories)
    materialization = compilation.candidate_report.authoring_materialization
    report = compile_study_candidate(authoring_package=authoring, authoring_materialization=materialization, context=context)
    assert report.disposition is CandidateCompilationDisposition.COMPILED_AUTHORITY_PENDING, report.diagnostics
    # Hostile graph addresses and source locks must still fail the standard
    # owner, independently of our projection's own validation.
    for change in ("owner", "output", "source-lock"):
        hostile, bad_context = authoring, context
        if change == "source-lock":
            first = inventories[0].source_materializations[0]
            wrong = replace(inventories[0], source_materializations=tuple(sorted((replace(first, object_fingerprint="f" * 64),
                *inventories[0].source_materializations[1:]), key=lambda value: value.object_id)))
            bad_context = replace(context, source_inventories=(wrong,))
        else:
            first = entry.coverage.assignments[0]
            first = replace(first, **({"adjudication_owner_ids": ("foreign-node",)} if change == "owner" else {"output_ids": ("foreign-output",)}))
            coverage = replace(entry.coverage, assignments=(first, *entry.coverage.assignments[1:]))
            bad_entry = replace(entry, coverage=coverage, checklist=replace(entry.checklist, formal_gap_coverage=domain.pin(coverage, "coverage_id")))
            hostile = replace(authoring, entry_package=bad_entry)
        refused = compile_study_candidate(authoring_package=hostile, authoring_materialization=materialization, context=bad_context)
        assert refused.disposition is CandidateCompilationDisposition.INVALID_DRAFT
        code = CandidateDiagnosticCode.FORMAL_GAP_BINDING_MISMATCH if change == "source-lock" else CandidateDiagnosticCode.FORMAL_GAP_GRAPH_BINDING_INVALID
        assert code in {value.code for value in refused.diagnostics}
    first = selected.entry.coverage.assignments[0]
    wrong = replace(first, obligation_ids=("e3.foreign-single-terminal",))
    coverage = replace(selected.entry.coverage, assignments=(wrong, *selected.entry.coverage.assignments[1:]))
    foreign = replace(selected.entry, coverage=coverage, checklist=replace(selected.entry.checklist,
        formal_gap_coverage=domain.pin(coverage, "coverage_id")))
    with pytest.raises(ValueError, match="foreign scientific obligations"):
        domain._protected_formal_entry(draft, SimpleNamespace(**{**vars(selected), "entry": foreign}), case.owner)
    for change in ("digest", "capability", "input-schema", "output-schema"):
        first = selected.formal_methods.bindings[0]
        field, value = {"digest": ("implementation_sha256", "0" * 64), "capability": ("capability_key", "matrix-e3-configured-protected.assess"),
            "input-schema": ("input_schema_id", "empirical-lawhood/wrong-input"), "output-schema": ("output_schema_id", "empirical-lawhood/wrong-output")}[change]
        first = replace(first, **{field: value})
        bad = replace(selected.formal_methods, bindings=(first, *selected.formal_methods.bindings[1:]))
        with pytest.raises(ValueError, match="exact actual phase assessor"):
            domain._protected_formal_entry(draft, SimpleNamespace(**{**vars(selected), "formal_methods": bad}), case.owner)
    cutoff = draft.prospective_draft.experiment.information_cutoffs[0]
    for changed in (replace(cutoff, coordinate=cutoff.coordinate + Decimal(1)),
            replace(cutoff, phase=CausalPhase.PREPARATION), replace(cutoff, includes_coordinate=False)):
        wrong = replace(draft, prospective_draft=replace(draft.prospective_draft,
            experiment=replace(draft.prospective_draft.experiment, information_cutoffs=(changed,
                *draft.prospective_draft.experiment.information_cutoffs[1:]))))
        with pytest.raises(ValueError, match="complete inclusive pre-action"):
            domain._bind_protected_obligations(wrong, case.programme, case.owner)
    project = case.owner.node_id(case.programme.sources.source_arms()[0][1], "project")
    thin = replace(draft, links=tuple(value for value in draft.links if value.producer_node_id != project))
    with pytest.raises(ValueError, match="complete causal-prefix ancestry"):
        domain._bind_protected_obligations(thin, case.programme, case.owner)
