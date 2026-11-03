# SPDX-License-Identifier: MPL-2.0
"""Independent public E3 projections over disclosed software-only originals.

Every source group, qualification and availability in these fixtures is
synthetic conformance metadata. They provide no genuine protected source,
scientific qualification, authority or fresh result.
"""

from dataclasses import replace
from decimal import Decimal
from functools import partial
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import project_protected_e3_allocation
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_feature_bindings import feature_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_original_publications import ProtectedE3OriginalPublications
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import project_protected_e3_response_numerics
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_preparation import response_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import ProtectedE3FitConfig, statistical_task_id
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole, SourceMaterializationRole
from empirical_lawhood.planning.formal_analysis import derive_formal_gap_applicability
from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
from empirical_lawhood.runtime.execution_envelope import ChildResourceTokenLimit, NonTimeResourceBudget, ProgressHeartbeat, ProgressLivenessContract
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from tests.experiment_entry_support import entry_package_for_draft
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture
from tests.test_matrix_e3_protected_source_records import fixture as source_fixture, response_fixture
from tests.test_matrix_e3_response_records import qualification
from tests.test_matrix_experiment_methods import fixture as mathematical_fixture, selected_input_records
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance_fixture, publish, stock as stock_fixture
from tests.test_matrix_scheduled_history import scheduled as scheduled_fixture


def original_case(directory: Path, *, selected64=False, cal_count=None, eval_count=None):
    """One literal original population with authentic guarded byte transport."""
    directory.mkdir(parents=True, exist_ok=True)
    provenance = provenance_fixture.__wrapped__()
    # These unacquired software inputs select actual current producing source;
    # the scheduled fixture's default synthetic provenance remains unchanged.
    scheduled = scheduled_fixture.__wrapped__(stock_fixture.__wrapped__(directory, provenance),
        producing_provenance=provenance)
    counts = {key: value for key, value in (("cal_count", cal_count), ("eval_count", eval_count)) if value is not None}
    if selected64 and counts:
        raise ValueError("selected64 fixture retains its original complete population")
    if counts:
        # Only the disclosed fixture constructor is parameterized here. The
        # patch ends before preparation, authoring or a worker can be invoked.
        from tests import test_matrix_e3_protected_inputs as source_literals
        counts["minimum_usable"] = counts.get("eval_count", 8)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(source_literals, "fixture", partial(mathematical_fixture, **counts))
            selected = source_fixture(scheduled, selected64=False)
    else:
        selected = source_fixture(scheduled, selected64=selected64)
    plane, manifest = selected.plane, selected.manifest
    inputs = replace(selected.inputs, reservation=manifest.reservation,
        native_specification=manifest.native_specification)
    allocation = project_protected_e3_allocation(inputs)
    response_selection, protocols, panels = response_fixture(selected)
    publication_clock = "clock.literal.public-e3.publications"
    availability = AvailabilitySpec(publication_clock, CausalPhase.PREPARATION,
        OutcomeAccess.OUTCOME_BLIND, Decimal(0))
    fit_cutoff = InformationCutoff("cutoff.literal.public-e3.before-train", publication_clock,
        CausalPhase.PREPARATION, Decimal(1))
    publications = tuple((key, publication, availability) for key, publication in (
        ("allocation", manifest.reservation.publication),
        ("native-selection", manifest.native_specification.publication),
        ("reservation", manifest.reservation_publication),
        ("roles", publish(plane, allocation, "literal.public-e3.roles"))))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_census_publication
    originals = ProtectedE3OriginalPublications("originals.literal.public-e3", inputs.specification.identity,
        identity(manifest), inputs.training_allocation.identity,
        publish(plane, manifest, "literal.public-e3.source-manifest"),
        publish(plane, inputs.training_allocation, "literal.public-e3.training-allocation"),
        exposure_census_publication(manifest.audit))
    fit_config = ProtectedE3FitConfig("config." + statistical_task_id(inputs.specification.identity,
        allocation.identity, "fit"), inputs.specification.identity, allocation.identity,
        tuple((role, len(allocation.unit_ids(role))) for role in ("calibration", "evaluation")),
        identity(manifest), inputs.training_allocation.identity, fit_cutoff, publications, originals)
    arguments = dict(selected64=True, train_count=64, cal_count=64, eval_count=64,
        minimum_usable=58) if selected64 else counts
    _, training_sources, _, methods = mathematical_fixture(**arguments)
    banks = selected_input_records(training_sources, methods)
    root, context = _fixture()
    response_publication = publish(plane, response_selection, "literal.public-e3.responses")
    response_qualification = qualification(response_selection, response_publication, "public-e3.responses")
    numerical_profiles = tuple(project_protected_e3_response_numerics(protocol,
        provenance=response_selection, publication=response_publication, qualification=response_qualification)
        for protocol in protocols)
    pins = (inputs.specification.identity, allocation.identity, identity(manifest),
        identity(selected.projection), identity(response_selection))
    design_inputs = tuple(DesignInputRecord("design.literal.public-e3." + str(index), pin,
        pin.object_fingerprint, fit_cutoff, DesignInputRole.READINESS_METADATA,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, "human.synthetic-software")
        for index, pin in enumerate(sorted(pins, key=lambda value: value.object_id)))
    clocks = {clock.clock_id: clock for clock in root.system.clocks}
    for clock_id in {publication_clock, *(row.clock_id for row in manifest.reservation.allocation.coordinates)}:
        clocks[clock_id] = replace(root.system.clocks[0], clock_id=clock_id)
    system = replace(root.system, world=replace(root.system.world, kind=WorldKind.NUMERICAL_SIMULATOR,
        unrepresented_physics=("physical-transfer",)), clocks=tuple(clocks[key] for key in sorted(clocks)))
    root = replace(root, question=inputs.specification.question, system=system,
        design_inputs=design_inputs, design_origin=replace(root.design_origin,
            declared_input_ids=tuple(row.input_id for row in design_inputs)),
        development_unit_ids=allocation.unit_ids("train"),
        evaluation_unit_ids=tuple(sorted((*allocation.unit_ids("calibration"), *allocation.unit_ids("evaluation")))),
        development_seed_ids=(), evaluation_seed_ids=(), source_materializations=())
    entry = entry_package_for_draft(root)
    return SimpleNamespace(plane=plane, inputs=inputs, specification=inputs.specification,
        allocation=allocation, manifest=manifest, sources=selected.descriptors,
        projections=(selected.projection,), mathematical_protocol=selected.mathematical,
        response_selection=response_selection, protocols=protocols, panels=panels,
        numerical_profiles=numerical_profiles, response_qualification=response_qualification,
        originals=originals, fit_config=fit_config, train_features=banks["train-features"],
        train_outcomes=banks["train-outcomes"], campaign=methods.campaign, root=root,
        entry_package=entry, template_qualification=context.qualifications[0], provenance=provenance,
        candidate_bytes=selected.args["candidate_bytes"])


def resource_selection(_case=None, *, maximum_parallel_tasks=1):
    """Reusable explicit operational defaults; no generated task ID roster."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3ResourceSelection

    controls = ExecutionResourceSelection("resources.literal.public-e3", (),
        (ChildResourceTokenLimit("child.literal.public-e3", 256, 0),), (), (), (), None, None,
        maximum_parallel_tasks, maximum_parallel_tasks * 2 * 1024**3, (), (), "b" * 64, True, True, True, True)
    return ProtectedE3ResourceSelection(controls,
        NonTimeResourceBudget("budget.literal.public-e3.default", 1, 2 * 1024**3, 64 * 1024**2, 100, 128 * 1024**2),
        ProgressLivenessContract("liveness.literal.public-e3.default", ProgressHeartbeat.SCHEMA,
            "software-only-native-work", Decimal(30), True, True))


def prepared_case(directory: Path, *, selected64=False, cal_count=None, eval_count=None, maximum_parallel_tasks=1):
    """Build closed preparation inputs through the real lowerer's projections."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection

    case = original_case(directory, selected64=selected64, cal_count=cal_count, eval_count=eval_count)
    resources = resource_selection(case, maximum_parallel_tasks=maximum_parallel_tasks)
    formal = _standard_fixture()[1]
    training = []
    files = {}
    for name, record in (("features", case.train_features), ("outcomes", case.train_outcomes)):
        artifact = ArtifactIdentity(record.record_id, "original-exposed-training-" + name,
            record.SCHEMA, record.fingerprint(), "application/json", len(record.canonical_bytes()))
        training.append(artifact)
        path = case.plane.root.resolve("literal-training/" + name + ".json", for_write=True)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(record.canonical_bytes())
        files[artifact.artifact_id] = PreparedExperimentFile(artifact, record.VERSION, path, artifact.size_bytes)
    for publication in case.response_selection.template_publications:
        artifact = next(protocol.templates.array_artifact for protocol in case.protocols
            if protocol.templates.array_artifact.artifact_id == publication.logical.logical_artifact_id)
        files[artifact.artifact_id] = PreparedExperimentFile(artifact, "1.0.0",
            case.plane.root.resolve(publication.materialization.relative_path, for_write=False), artifact.size_bytes)
    selection = ProtectedE3PreparationSelection(selection_id="selection.literal.public-e3", root=case.root,
        entry_package=case.entry_package, fit_config=case.fit_config, manifest=case.manifest,
        training_allocation=case.inputs.training_allocation, sources=case.sources, projections=case.projections,
        mathematical_protocol=case.mathematical_protocol, response_selection=case.response_selection,
        protocols=case.protocols, panels=case.panels, numerical_profiles=case.numerical_profiles,
        training_features=training[0], training_outcomes=training[1], formal_methods=formal.formal_methods,
        formal_source_inventories=formal.source_inventories, resource_selection=resources,
        numerical_qualifications=(case.response_qualification,))
    lowered = lower_protected_matrix_response_error(case.specification, case.allocation, selection)
    # Explicitly declare this synthetic world's policy from the actual derived
    # aggregate. Production preparation never enlarges a supplied policy.
    aggregate = lowered.draft.campaign.budget
    declared_ceiling = lowered.draft.prospective_draft.resource_ceiling
    policy = replace(case.root.system.authority_policy, budget_ceiling=declared_ceiling)
    system = replace(case.root.system, authority_policy=policy)
    campaign = replace(case.root.campaign, budget=aggregate,
        authority_policy=ObjectIdentity.from_record(policy.policy_id, policy))
    case.root = replace(case.root, system=system, campaign=campaign, resource_ceiling=declared_ceiling)
    case.entry_package = entry_package_for_draft(case.root)
    selection = replace(selection, root=case.root, entry_package=case.entry_package)
    lowered = lower_protected_matrix_response_error(case.specification, case.allocation, selection)
    input_records = dict(lowered.input_records)
    records = {external.logical_artifact_id: input_records[external.input_id]
        for external in lowered.draft.external_inputs if external.input_id in input_records}
    configs, qualifications = [], []
    for index, external in enumerate(lowered.draft.external_inputs):
        version = records[external.logical_artifact_id].VERSION if external.logical_artifact_id in records else files[external.logical_artifact_id].record_version
        pin = ObjectIdentity(external.logical_artifact_id, external.payload_schema, version, external.expected_content_sha256)
        config = SourceMaterializationConfig("source-config.literal.public-e3." + str(index), external.input_id,
            # This test uses the same exact role as the existing protected
            # factorial source projection; domain meaning stays in records.
            SourceMaterializationRole.OBSERVATION_STREAM,
            external.expected_content_sha256, external.maximum_size_bytes, external.maximum_size_bytes,
            external.payload_schema, external.media_type, SourceReadMode.ORDINARY_BOUNDED,
            external.outcome_access, external.visibility_ceiling)
        configs.append(config)
        qualifications.append(replace(case.template_qualification,
            receipt_id="qualification.literal.public-e3." + str(index), source_id=external.input_id,
            materialization=pin, content_sha256=pin.object_fingerprint,
            evidence_world_id=case.root.system.world.world_id,
            clock_ids=tuple(clock.clock_id for clock in case.root.system.clocks),
            outcome_access=external.outcome_access, visibility_ceiling=external.visibility_ceiling))
    inventory = replace(formal.source_inventories[0], denominator_id=case.root.system.system_id,
        evidence_world=case.entry_package.checklist.portfolio_world,
        source_materializations=tuple(sorted((row.materialization for row in qualifications), key=lambda row: row.object_id)),
        independent_unit_ids=case.allocation.unit_ids("evaluation"),
        denominator_inapplicable_gap_ids=tuple(row.gap_id for row in case.entry_package.register.gaps))
    coverage = replace(case.entry_package.coverage, denominator_id=case.root.system.system_id,
        applicability=derive_formal_gap_applicability(case.entry_package.register, inventory))
    entry = replace(case.entry_package, coverage=coverage, checklist=replace(case.entry_package.checklist,
        formal_gap_coverage=ObjectIdentity.from_record(coverage.coverage_id, coverage)))
    selection = replace(selection, entry_package=entry, formal_source_inventories=(inventory,),
        qualifications=tuple(sorted(qualifications, key=lambda row: row.receipt_id)),
        source_configs=tuple(sorted(configs, key=lambda row: row.fingerprint())))
    case.selection, case.files, case.lowered = selection, files, lowered
    return case


def write_public_file_selection(case):
    """Select existing original files through the installed public FILE schema."""
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    root = Path(case.plane.root.contract.canonical_path)
    record_path = root / "selected-protected-e3.canonical.json"
    raw = case.selection.canonical_bytes()
    record_path.write_bytes(raw)
    bindings = (ExperimentInputBinding("protected-selection",
        ObjectIdentity.from_record(case.selection.selection_id, case.selection), record_path.name, len(raw)),)
    files = tuple(ExperimentFileInputBinding(key, value.identity, value.record_version,
        value.path.relative_to(root).as_posix(), value.maximum_bytes) for key, value in sorted(case.files.items()))
    selection = ExperimentFileInputSelection("selection.literal.public-e3.files", "matrix.response-error.origin-only", bindings, files)
    path = root / "selected-protected-e3-file-inputs.json"
    path.write_bytes(selection.canonical_bytes())
    return path


@pytest.fixture(scope="module")
def selected(tmp_path_factory):
    return prepared_case(tmp_path_factory.mktemp("literal-public-e3-lowering"))


def _assert_one_selected_allocation_custody(case, draft, records, allocation):
    """All selected consumers share the actual roles publication, not a copy ID."""
    from collections import Counter
    from empirical_lawhood.kernel.experimental_design import UnitAllocation

    publications = {key: publication for key, publication, _ in case.selection.fit_config.publications}
    original = publications["roles"]
    selected, = ((key, record) for key, record in records
        if type(record) is UnitAllocation and record.identity == allocation.identity)
    selected_key, selected_record = selected
    assert selected_record is allocation
    assert selected_record.canonical_bytes() == case.allocation.canonical_bytes()
    assert selected_key == "external." + original.logical.logical_artifact_id
    external, = (row for row in draft.external_inputs if row.input_id == selected_key)
    assert (external.logical_artifact_id, external.expected_content_sha256, external.maximum_size_bytes,
        external.outcome_access, external.visibility_ceiling) == (
        original.logical.logical_artifact_id, original.logical.content_sha256, original.materialization.size_bytes,
        original.logical.outcome_access, original.logical.visibility_ceiling)
    consumers = tuple(edge for edge in draft.links if edge.consumer_input_id == "allocation")
    assert consumers and all(edge.external_input_id == selected_key for edge in consumers)
    operations = {row.node_id: row for row in draft.operations}
    counts = Counter(operations[edge.consumer_node_id].selection.capability_key for edge in consumers)
    queries = sum(len(allocation.unit_ids(role)) for role in ("calibration", "evaluation"))
    expected = {"matrix-e3-protected." + phase: queries for phase in ("forecast", "responses", "response-score")}
    expected.update({"matrix-e3-protected." + phase: 1 for phase in (
        "fit", "model-freeze", "calibrate", "calibration-freeze", "assess", "adjudicate")})
    assert dict(counts) == expected
    assert len({edge.consumer_node_id for edge in consumers}) == len(consumers)
    train = case.selection.training_allocation
    training, = ((key, record) for key, record in records
        if type(record) is UnitAllocation and record.identity == train.identity)
    training_key, training_record = training
    assert training_record is train and training_record is not selected_record
    assert training_record.canonical_bytes() == case.inputs.training_allocation.canonical_bytes()
    assert training_key == "external.input.matrix-e3." + train.fingerprint()
    assert len(tuple(record for _, record in records if type(record) is UnitAllocation)) == 2
    training_external, = (row for row in draft.external_inputs if row.input_id == training_key)
    assert (training_external.logical_artifact_id, training_external.expected_content_sha256,
        training_external.maximum_size_bytes) == (
        "input.matrix-e3." + train.fingerprint(), train.fingerprint(), len(train.canonical_bytes()))
    training_edge, = (edge for edge in draft.links if edge.consumer_input_id == "training-allocation")
    assert training_edge.external_input_id == training_key
    assert operations[training_edge.consumer_node_id].selection.capability_key == "matrix-e3-protected.fit"
    assert case.selection.fit_config.original_publications.training_allocation_publication.logical.content_sha256 == train.fingerprint()
    return {"selected_allocation_external_input": selected_key, "selected_allocation_bytes": len(allocation.canonical_bytes()),
        "selected_allocation_sha256": allocation.fingerprint(), "selected_allocation_materializations": 1,
        "shared_selected_allocation_object": True, "selected_allocation_consumer_count": len(consumers),
        "original_roles_logical_id": original.logical.logical_artifact_id,
        "original_training_external_input": training_key, "original_training_sha256": train.fingerprint(),
        "original_training_bytes": len(train.canonical_bytes()), "original_training_materializations": 1}


def test_actual_originals_derive_the_complete_public_graph_without_train_or_template_reads(selected, monkeypatch, tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error

    case = selected
    original = tuple(record.canonical_bytes() for record in (case.manifest, case.specification,
        case.allocation, case.inputs.training_allocation))
    monkeypatch.setattr(Path, "read_bytes", lambda *_args, **_kwargs: pytest.fail("lowering read scientific bodies"))
    lowered = lower_protected_matrix_response_error(case.specification, case.allocation, case.selection)
    assert len(lowered.draft.operations) == 286
    assert len({row.node_id for row in lowered.draft.operations}) == 286
    assert lowered.draft.development_study is None and lowered.draft.prospective_draft is not None
    assert lowered.draft.campaign.objective == case.specification.question
    assert len(lowered.file_identities) == 3
    reserved = {source.root_id for source in case.sources if source.root.root.role.value == "WITHHELD_TRANSFER"}
    assert not any(root in operation.node_id for root in reserved for operation in lowered.draft.operations)
    allocation_custody = _assert_one_selected_allocation_custody(case, lowered.draft, lowered.input_records, case.allocation)
    assert original == tuple(record.canonical_bytes() for record in (case.manifest, case.specification,
        case.allocation, case.inputs.training_allocation))
    (tmp_path / "alternative-allocation-custody.json").write_text(json.dumps(allocation_custody, indent=2) + "\n")


def test_independent_graph_oracle_requires_both_freezes_complete_denominators_and_forecasts_first(selected):
    case, draft = selected, selected.lowered.draft
    incoming = {}
    for edge in draft.links:
        incoming.setdefault(edge.consumer_node_id, {})[edge.consumer_input_id] = edge
    task = lambda operation, mode="", root=None: statistical_task_id(case.specification.identity,
        case.allocation.identity, operation, mode=mode, root=root)
    for role, native_role in (("calibration", "CALIBRATION"), ("evaluation", "CONFIRMATION")):
        roots = tuple(source.root.root for source in case.sources if source.root.root.role.value == native_role)
        reduce = incoming[task("calibrate" if role == "calibration" else "assess")]
        assert {name.removeprefix("forecasts.") for name in reduce if name.startswith("forecasts.")} == {root.root_id for root in roots}
        assert {name.removeprefix("outcomes.") for name in reduce if name.startswith("outcomes.")} == {root.root_id for root in roots}
        for root in roots:
            error = incoming[task("forecast", role, root)]
            assert error["frozen"].producer_node_id == task("freeze", "model" if role == "calibration" else "calibration")
            response = incoming[response_task_id(root.root_id, "responses")]
            assert response["error"].producer_node_id == task("forecast", role, root)
            assert response["physical"].producer_node_id == response_task_id(root.root_id, "physical-forecast")
            assert error["feature"].producer_node_id == feature_task_id(root.root_id)
            assert reduce["outcomes." + root.root_id].producer_node_id == response_task_id(root.root_id, "response-score")
    freeze = incoming[task("freeze", "calibration")]
    assert freeze["calibration"].producer_node_id == task("calibrate")
    assert freeze["model-freeze"].producer_node_id == task("freeze", "model")


def test_resource_defaults_derive_every_worker_bound_and_keep_the_caller_capacity(selected):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import (
        bind_protected_e3_experiment_inputs, derive_protected_e3_resource_selection,
    )
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    chosen = selected.selection.resource_selection
    original = chosen.canonical_bytes()
    assert not chosen.resources.task_cells
    resolved = bind_protected_e3_experiment_inputs(selected.specification,
        {"protected-selection": selected.selection}, files=selected.files)
    preparation = prepare_experiment(selected.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=ExecutionSelection(), protocol_bytes=selected.candidate_bytes)
    resources = derive_protected_e3_resource_selection(preparation)
    assert resources == selected.lowered.resource_selection
    assert {row.task_id for row in resources.task_cells} == {row.node_id for row in preparation.draft.operations}
    native = tuple(row for row in resources.task_cells if row.native_simulator_launch)
    assert len(resources.task_cells) == 286 and len(native) == 56
    assert resources.child_token_limits[0].physical_execution_token_limit == 56
    assert chosen.resources.child_token_limits[0].physical_execution_token_limit == 256
    assert all(row.maximum_attempts == 1 for row in resources.task_cells)
    assert all(row.resource_budget.memory_bytes == 2 * 1024**3 for row in resources.task_cells)
    assert all(row.physical_independent_unit_id and row.progress_liveness for row in native)
    assert original == chosen.canonical_bytes()
    assert preparation.draft.prospective_draft.system.authority_policy == selected.selection.root.system.authority_policy


def test_same_operational_selection_derives_an_edited_population_without_task_roster(selected, tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes

    edited = prepared_case(tmp_path, cal_count=1, eval_count=8)
    selection = replace(edited.selection, resource_selection=selected.selection.resource_selection)
    decoded = decode_canonical_bytes(selection.canonical_bytes(), ProtectedE3PreparationSelection, maximum_bytes=None)
    assert decoded == selection
    lowered = lower_protected_matrix_response_error(edited.specification, edited.allocation, decoded)
    assert len(lowered.draft.operations) == len(lowered.resource_selection.task_cells) == 96
    assert lowered.resource_selection.child_token_limits[0].physical_execution_token_limit == 18
    assert decoded.resource_selection.canonical_bytes() == selected.selection.resource_selection.canonical_bytes()
    assert not decoded.resource_selection.resources.task_cells


def test_per_operation_resource_override_changes_only_that_phase_and_preserves_originals(selected):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3OperationResources

    selected_resources = selected.selection.resource_selection
    override = ProtectedE3OperationResources("forecast", replace(selected_resources.default_budget,
        budget_id="budget.literal.forecast", output_bytes=32 * 1024**2, memory_bytes=1024**3))
    selection = replace(selected.selection, resource_selection=replace(selected_resources, operation_overrides=(override,)))
    lowered = lower_protected_matrix_response_error(selected.specification, selected.allocation, selection)
    configs = {row.node_id: row.config_payload for row in selected.lowered.draft.operations}
    assert all(configs[row.node_id] == row.config_payload for row in lowered.draft.operations)
    for operation in lowered.draft.operations:
        expected = override.resource_budget if operation.selection.capability_key.endswith(".forecast") else selected_resources.default_budget
        assert (operation.resource_budget.memory_bytes, operation.resource_budget.output_bytes) == (expected.memory_bytes, expected.output_bytes)
    assert lowered.draft.prospective_draft.system.authority_policy == selected.selection.root.system.authority_policy


@pytest.mark.parametrize("coordinate", ("native-tokens", "memory"))
def test_resource_capacity_refuses_the_complete_graph_before_any_worker(selected, monkeypatch, coordinate):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import bind_protected_e3_experiment_inputs
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection

    resources = selected.selection.resource_selection
    controls = resources.resources
    controls = (replace(controls, child_token_limits=(replace(controls.child_token_limits[0], physical_execution_token_limit=55),))
        if coordinate == "native-tokens" else replace(controls, aggregate_memory_ceiling_bytes=1024**3))
    selection = replace(selected.selection, resource_selection=replace(resources, resources=controls))
    monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *_args, **_kwargs: pytest.fail("resource preflight launched a worker"))
    resolved = bind_protected_e3_experiment_inputs(selected.specification,
        {"protected-selection": selection}, files=selected.files)
    preparation = prepare_experiment(selected.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=ExecutionSelection(), protocol_bytes=selected.candidate_bytes)
    dependency, = (row for row in preparation.dependencies if row.code == "matrix.e3.resource-capacity")
    assert dependency.kind is DependencyKind.ENVIRONMENT
    assert preparation.draft is None and not preparation.executable
    assert dict(preparation.census.resolved_role_counts) == dict(preparation.census.role_counts)
    assert selection.root.system.authority_policy == selected.selection.root.system.authority_policy


def test_historical_exact_resource_roster_remains_byte_exact_and_mixed_rules_refuse(selected):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes

    resources = selected.lowered.resource_selection
    original = resources.canonical_bytes()
    selection = replace(selected.selection, resource_selection=resources)
    decoded = decode_canonical_bytes(selection.canonical_bytes(), ProtectedE3PreparationSelection, maximum_bytes=None)
    assert lower_protected_matrix_response_error(selected.specification, selected.allocation, decoded).resource_selection.canonical_bytes() == original
    with pytest.raises(ValueError, match="empty task cells"):
        replace(selected.selection.resource_selection, resources=resources)


def test_public_prepare_and_standard_candidate_share_the_derived_selected_instance(selected):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import (
        bind_protected_e3_experiment_inputs, derive_protected_e3_design_inputs,
    )
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.planning.experiment_entry import StudyDefinition
    from empirical_lawhood.runtime.candidate_compiler import StandardCandidateCompilationContext, compile_study_candidate
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from tests.runtime_platform.test_candidate_compiler import _materialization

    case = selected
    resolved = bind_protected_e3_experiment_inputs(case.specification,
        {"protected-selection": case.selection}, files=case.files)
    preparation = prepare_experiment(case.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=ExecutionSelection(), protocol_bytes=case.candidate_bytes)
    assert preparation.draft is not None
    assert "matrix.e3.prospective-operation-lowering" not in {row.code for row in preparation.dependencies}
    assert "matrix.e3.authority-resource-budget" not in {row.code for row in preparation.dependencies}
    design = derive_protected_e3_design_inputs(preparation)
    registrations, registry, codecs = operation_catalog()
    compilation = compile_recursive_wave(draft=preparation.draft, registrations=registrations, registry=registry,
        implementation_commit="d" * 40, qualifications=design.qualifications,
        known_design_inputs=design.known_design_inputs, output_codecs=codecs)
    assert compilation.candidate_report.candidate is not None, compilation.candidate_report.diagnostics
    context = StandardCandidateCompilationContext("context.literal.public-e3", compilation.candidate_context,
        design.formal_methods, design.formal_source_inventories)
    study = StudyDefinition("study.literal.public-e3", compilation.candidate_draft, design.entry_package)
    report = compile_study_candidate(authoring_package=study, authoring_materialization=_materialization(), context=context)
    assert report.candidate is not None, [(row.code, row.field_path, row.message) for row in report.diagnostics]


def assert_parallel_authority_preflight(*, specification, selection, files, execution, bind_inputs,
        protocol_bytes=None):
    """Exercise actual public preparation with a sequential-only and exact policy."""
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind

    original_policy = selection.root.system.authority_policy
    resources = selection.resource_selection
    controls = replace(resources.resources, maximum_parallel_tasks=4,
        aggregate_memory_ceiling_bytes=4 * resources.default_budget.memory_bytes)
    selection = replace(selection, resource_selection=replace(resources, resources=controls))
    execution = replace(execution, workers=4)

    def prepare(chosen):
        bound = bind_inputs(specification, {"protected-selection": chosen}, files=files)
        return prepare_experiment(specification, scientific_inputs=bound.scientific_inputs,
            method_inputs=bound.method_inputs, execution=execution, protocol_bytes=protocol_bytes)

    def with_policy(chosen, budget):
        policy = replace(chosen.root.system.authority_policy, budget_ceiling=budget)
        root = replace(chosen.root, system=replace(chosen.root.system, authority_policy=policy),
            campaign=replace(chosen.root.campaign,
                authority_policy=ObjectIdentity.from_record(policy.policy_id, policy)))
        entry = replace(chosen.entry_package, checklist=replace(chosen.entry_package.checklist,
            draft=ObjectIdentity.from_record(root.draft_id, root)))
        return replace(chosen, root=root, entry_package=entry)

    initial = prepare(selection)
    assert initial.draft is not None
    sequential = initial.draft.campaign.budget
    declared = initial.draft.prospective_draft.resource_ceiling
    assert sequential.memory_bytes < declared.memory_bytes == controls.aggregate_memory_ceiling_bytes
    assert sequential.contains(sequential) and not sequential.contains(declared)
    held = prepare(with_policy(selection, sequential))
    dependency, = (row for row in held.dependencies if row.code == "matrix.e3.authority-resource-budget")
    assert dependency.kind is DependencyKind.AUTHORITY and not held.executable
    accepted = prepare(with_policy(selection, declared))
    assert "matrix.e3.authority-resource-budget" not in {row.code for row in accepted.dependencies}
    assert accepted.draft.operations == held.draft.operations and accepted.census == held.census
    assert accepted.draft.prospective_draft.system.authority_policy.budget_ceiling == declared
    assert selection.root.system.authority_policy == original_policy


def test_parallel_candidate_ceiling_requires_explicit_authority_before_authoring(selected):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import bind_protected_e3_experiment_inputs
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    assert_parallel_authority_preflight(specification=selected.specification, selection=selected.selection,
        files=selected.files, execution=ExecutionSelection(workers=4),
        bind_inputs=bind_protected_e3_experiment_inputs, protocol_bytes=selected.candidate_bytes)


def test_insufficient_declared_authority_budget_remains_a_dependency_before_native_entry(selected, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import bind_protected_e3_experiment_inputs
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection

    policy = replace(selected.selection.root.system.authority_policy,
        budget_ceiling=ResourceBudget(1, 1, 0, 1, 0, 0))
    root = replace(selected.selection.root,
        system=replace(selected.selection.root.system, authority_policy=policy),
        campaign=replace(selected.selection.root.campaign,
            authority_policy=ObjectIdentity.from_record(policy.policy_id, policy)))
    entry = replace(selected.selection.entry_package, checklist=replace(selected.selection.entry_package.checklist,
        draft=ObjectIdentity.from_record(root.draft_id, root)))
    selection = replace(selected.selection, root=root, entry_package=entry)
    def forbidden(*_args, **_kwargs):
        pytest.fail("an insufficient authority budget reached a worker")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    resolved = bind_protected_e3_experiment_inputs(selected.specification,
        {"protected-selection": selection}, files=selected.files)
    preparation = prepare_experiment(selected.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=ExecutionSelection(), protocol_bytes=selected.candidate_bytes)
    findings = {row.code: row for row in preparation.dependencies}
    assert findings["matrix.e3.authority-resource-budget"].kind is DependencyKind.AUTHORITY
    assert not preparation.executable
    assert preparation.draft.prospective_draft.system.authority_policy == policy
    assert preparation.draft.campaign.authority_policy == ObjectIdentity.from_record(policy.policy_id, policy)


def test_public_file_selection_decodes_the_protected_carrier_and_prepares_without_science(selected, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import e3_numerical_methods
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    path = write_public_file_selection(selected)
    original = selected.selection.canonical_bytes()
    def forbidden(*_args, **_kwargs):
        pytest.fail("public scientific input loading entered fitting or a worker")
    monkeypatch.setattr(e3_numerical_methods, "fit_standardized_ridge", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    resolved = load_experiment_inputs(selected.specification, path)
    assert resolved.method_inputs.selection == selected.selection
    assert dict(resolved.method_inputs.files) == selected.files
    assert selected.selection.canonical_bytes() == original
    prepared = prepare_experiment(selected.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=ExecutionSelection(), protocol_bytes=selected.candidate_bytes)
    assert len(prepared.allocation.units) == 44 and len(prepared.draft.operations) == 286
    assert "matrix.e3.prospective-operation-lowering" not in {row.code for row in prepared.dependencies}


@pytest.mark.parametrize("damage", ("missing", "changed"))
def test_public_file_selection_refuses_original_training_file_damage_before_domain_binding(selected, monkeypatch, damage):
    from empirical_lawhood.api import experiment_preparation as public

    path = write_public_file_selection(selected)
    declaration = public._protocol(selected.specification)
    def forbidden(*_args, **_kwargs):
        pytest.fail("unavailable or altered TRAIN file reached the scientific input binder")
    monkeypatch.setattr(public, "_protocol", lambda *_args: replace(declaration, bind_inputs=forbidden))
    original_path = selected.files[selected.train_features.record_id].path
    raw = original_path.read_bytes()
    parked = original_path.with_name(original_path.name + ".literal-unavailable")
    if damage == "missing":
        original_path.rename(parked)
    else:
        original_path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    try:
        with pytest.raises((ValueError, RuntimeError, FileNotFoundError)):
            public.load_experiment_inputs(selected.specification, path)
    finally:
        if damage == "missing":
            parked.rename(original_path)
        else:
            original_path.write_bytes(raw)
    assert original_path.read_bytes() == raw


def test_one_actual_qualified_original_container_authenticates_all_protocols_once(selected, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment
    from empirical_lawhood.api.domain_composition.matrix_protected_response.runtime import authenticate_protected_e3_numerical_originals

    actual, calls = commitment.authenticate_publication, []
    def authenticate(*args):
        calls.append(args[1])
        return actual(*args)
    monkeypatch.setattr(commitment, "authenticate_publication", authenticate)
    authenticate_protected_e3_numerical_originals(selected.plane, selected.selection)
    assert len(calls) == 1
    assert len(selected.selection.numerical_profiles) == len(selected.selection.protocols) == 28
    assert all(profile.provenance_publication == calls[0] for profile in selected.selection.numerical_profiles)


def test_existing_qualified_cal_and_conf_containers_preserve_all_original_protocol_members(selected, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion, ScheduledResponseSelection
    from empirical_lawhood.api.domain_composition.matrix_protected_response.runtime import authenticate_protected_e3_numerical_originals

    containers, qualifications, profiles = [], [], []
    for role in ("CALIBRATION", "CONFIRMATION"):
        protocols = tuple(protocol for protocol in selected.protocols if protocol.public_source.root.role.value == role)
        groups = tuple(sorted({protocol.public_source.root.independent_group_id for protocol in protocols}))
        panels = tuple((group, tuple(panel for panel in selected.panels if panel.independent_group_id == group)) for group in groups)
        criterion = ScheduledCalibrationCriterion("criterion.literal.legacy-numerics", "unit.whole-root", len(groups),
            Decimal(1), ("matrix-history.joint-decreasing-coupling",),
            "COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY") if role == "CALIBRATION" else None
        container = ScheduledResponseSelection("container.literal.legacy-numerics." + role.lower(),
            ObjectIdentity.from_record(selected.manifest.reservation.allocation.allocation_id, selected.manifest.reservation.allocation), protocols, panels, selected.response_selection.template_publications, criterion)
        container.validate_allocation(selected.manifest.reservation.allocation)
        publication = publish(selected.plane, container, "literal.public-e3.legacy-numerics." + role.lower())
        q = qualification(container, publication, "legacy-numerics." + role.lower())
        containers.append(container)
        qualifications.append(q)
        profiles.extend(project_protected_e3_response_numerics(protocol, provenance=container,
            publication=publication, qualification=q) for protocol in protocols)
    selection = replace(selected.selection, numerical_containers=tuple(containers),
        numerical_profiles=tuple(profiles), numerical_qualifications=tuple(qualifications))
    original_members = tuple(protocol.canonical_bytes() for protocol in selected.protocols)
    lowered = lower_protected_matrix_response_error(selected.specification, selected.allocation, selection)
    assert len(lowered.draft.operations) == 286
    assert original_members == tuple(protocol.canonical_bytes() for protocol in selection.protocols)
    actual, calls = commitment.authenticate_publication, []
    def authenticate(*args):
        calls.append(args[1])
        return actual(*args)
    monkeypatch.setattr(commitment, "authenticate_publication", authenticate)
    authenticate_protected_e3_numerical_originals(selected.plane, selection)
    assert len(calls) == 2
    assert len(selection.numerical_profiles) == 28


def test_changed_root_question_refuses_before_lowering_reads(selected, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error

    selection = replace(selected.selection, root=replace(selected.selection.root,
        question="Unrelated retained question"))
    monkeypatch.setattr(Path, "read_bytes", lambda *_args, **_kwargs: pytest.fail("refused lowering read scientific bodies"))
    with pytest.raises(ValueError, match="selected scientific question"):
        lower_protected_matrix_response_error(selected.specification, selected.allocation, selection)


def test_later_profile_changed_sidecar_descriptor_requires_its_own_original_authentication(selected):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import validate_selection_science
    from empirical_lawhood.api.domain_composition.matrix_protected_response.runtime import authenticate_protected_e3_numerical_originals

    profiles = selected.selection.numerical_profiles
    publication = profiles[1].provenance_publication
    changed = replace(publication, manifest_materialization=replace(publication.manifest_materialization,
        size_bytes=publication.manifest_materialization.size_bytes + 1))
    assert changed.materialization.materialization_id == profiles[0].provenance_publication.materialization.materialization_id
    assert changed.fingerprint() != profiles[0].provenance_publication.fingerprint()
    selection = replace(selected.selection, numerical_profiles=(profiles[0],
        replace(profiles[1], provenance_publication=changed), *profiles[2:]))
    # A well-typed descriptor is intentionally not an authentication result.
    # Authenticating the first unchanged publication must not stand in for
    # this later profile's different complete sidecar descriptor.
    validate_selection_science(selected.specification, selected.allocation, selection)
    with pytest.raises((ValueError, RuntimeError), match="sidecar"):
        authenticate_protected_e3_numerical_originals(selected.plane, selection)


@pytest.mark.parametrize("sidecar", (False, True))
def test_original_numerical_container_mutation_refuses_actual_public_authentication(selected, sidecar):
    from empirical_lawhood.api.domain_composition.matrix_protected_response.runtime import authenticate_protected_e3_numerical_originals

    publication = selected.selection.numerical_profiles[0].provenance_publication
    relative = publication.materialization.relative_path + (".manifest.json" if sidecar else "")
    path = selected.plane.root.resolve(relative, for_write=False)
    original = path.read_bytes()
    path.write_bytes(bytes((original[0] ^ 1,)) + original[1:])
    try:
        with pytest.raises((ValueError, RuntimeError)):
            authenticate_protected_e3_numerical_originals(selected.plane, selected.selection)
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("damage", ("roles", "cutoff", "source", "protocol", "training", "missing-numerical-qualification", "foreign-numerical-qualification"))
def test_original_source_or_causal_substitution_refuses_before_public_lowering_io(selected, monkeypatch, damage):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_lowering import lower_protected_matrix_response_error

    case, selection = selected, selected.selection
    monkeypatch.setattr(Path, "read_bytes", lambda *_args, **_kwargs: pytest.fail("refused lowering read scientific bodies"))
    with pytest.raises((ValueError, TypeError, PermissionError)):
        if damage == "roles":
            selection = replace(selection, fit_config=replace(selection.fit_config,
                query_census=(("calibration", 19), ("evaluation", 8))))
        elif damage == "cutoff":
            selection = replace(selection, fit_config=replace(selection.fit_config,
                fit_cutoff=replace(selection.fit_config.fit_cutoff, coordinate=Decimal(-1))))
        elif damage == "source":
            selection = replace(selection, sources=selection.sources[:-1])
        elif damage == "protocol":
            selection = replace(selection, protocols=selection.protocols[:-1])
        elif damage == "training":
            selection = replace(selection, training_allocation=replace(selection.training_allocation,
                allocation_id="allocation.literal.foreign-training"))
        elif damage == "missing-numerical-qualification":
            selection = replace(selection, numerical_qualifications=())
        else:
            qualification, = selection.numerical_qualifications
            qualification = replace(qualification, materialization=replace(qualification.materialization,
                object_fingerprint="f" * 64), content_sha256="f" * 64)
            selection = replace(selection, numerical_qualifications=(qualification,))
        lower_protected_matrix_response_error(case.specification, case.allocation, selection)


def test_selected64_uses_the_same_public_preparation_and_whole_unit_lowering(tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import bind_protected_e3_experiment_inputs
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    case = prepared_case(tmp_path, selected64=True)
    resolved = bind_protected_e3_experiment_inputs(case.specification,
        {"protected-selection": case.selection}, files=case.files)
    prepared = prepare_experiment(case.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=ExecutionSelection(), protocol_bytes=case.candidate_bytes)
    assert prepared.draft is not None
    assert len(prepared.allocation.units) == 320
    assert dict(prepared.allocation.role_counts) == {role: 64 for role in
        ("train", "calibration", "evaluation", "transfer_nearby", "transfer_shifted")}
    assert len(prepared.draft.operations) == 1286
    assert "matrix.e3.prospective-operation-lowering" not in {row.code for row in prepared.dependencies}
    allocation_custody = _assert_one_selected_allocation_custody(case, prepared.draft, prepared.input_records, prepared.allocation)
    (tmp_path / "selected-public-route-evidence.json").write_text(json.dumps({
        "claim": "SOFTWARE_CONFORMANCE_ONLY_NO_GENUINE_QUALIFICATION_OR_AUTHORITY",
        "specification": case.specification.fingerprint(), "allocation": prepared.allocation.fingerprint(),
        "draft": prepared.draft.fingerprint(), "independent_units": len(prepared.allocation.units),
        "role_counts": dict(prepared.allocation.role_counts), "tasks": len(prepared.draft.operations),
        "dependency_codes": [row.code for row in prepared.dependencies],
        "original_source_manifest": case.manifest.fingerprint(),
        "original_training_allocation": case.inputs.training_allocation.fingerprint(),
        "original_numerical_containers": len(case.selection.numerical_qualifications),
        "allocation_custody": allocation_custody,
    }, indent=2) + "\n")
