# SPDX-License-Identifier: MPL-2.0
"""Exact complete prepared-prediction graph; no native entry or source claim."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_prediction_bindings as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_experiment import MatrixPreparationSourceBank
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol, physical_forecast_implementation
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests import test_matrix_prepared_point as point_fixture
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture


@pytest.fixture
def selected(tmp_path):
    source, initial, _, _, allocation, point, _ = point_fixture.selected_scope(tmp_path)
    coordinates = tuple(replace(row, autonomous_ticks=row.autonomous_ticks + 128,
        observation_ticks=tuple(range(row.total_ticks + 129))) for row in allocation.coordinates)
    by_id = {row.coordinate_id: row for row in coordinates}
    allocation = replace(allocation, coordinates=coordinates,
        roots=tuple(replace(row, coordinate=coordinate_identity(by_id[row.root.coordinate_id])) for row in allocation.roots),
        matched_scopes=tuple(replace(row, coordinates=tuple(coordinate_identity(by_id[value.object_id]) for value in row.coordinates))
            for row in allocation.matched_scopes))
    root = next(row for row in allocation.roots if row.root.root_id == source.root.root.root_id)
    public = replace(source.original, coordinate=by_id[source.coordinate.coordinate_id], allocation=original.identity(allocation))
    source = replace(source, original=public, root=root)
    point = replace(point, sources=(MatrixPreparedPublicSource.from_source(source),))
    bank = MatrixPreparationSourceBank("bank.literal-prepared-prediction", (allocation,), (source,))
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype="<c16")
    templates = {"generic_basis": np.asarray([np.kron(np.eye(2), row) / 2 for row in pauli], dtype="<c16"),
        "force_coefficients": np.stack((np.eye(3), np.eye(3))).astype("<f8") / np.sqrt(6),
        "trace_coefficients": np.ones((2, 3), dtype="<f8") / np.sqrt(6),
        "receiver_coefficients": np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4)}
    raw, members = encode_matrix_arrays(templates)
    operand = ScheduledResponseArrays("templates.literal-prediction", "TEMPLATES", source.original.source,
        ArtifactIdentity("array.literal-prediction-templates", "literal-selected-templates", MATRIX_ARRAY_SCHEMA,
            sha256(raw).hexdigest(), "application/x-npz", len(raw)), members, (source.original.source,),
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    criterion = point.original_forecast.criterion_record
    protocol = ScheduledResponseProtocol("protocol.literal-prepared-prediction", source.original, point.original_forecast.criterion,
        MatrixFactorResponseModel("model.literal-prepared-prediction", physical_forecast_implementation()),
        tuple(sorted((MatrixFactorAction("action.literal-prediction." + row.role.lower(), row.role, row.amplitude,
            row.pulse_steps, row.force_norm) for row in criterion.action_scales), key=lambda row: row.action_id)),
        (16, 64, 128), 48, operand, D("1e-5"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-8"), D("1e-8"),
        D("1e-5"), D("1e-12"), criterion.receiver_gram_tolerance, "PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME")
    programme = method.MatrixPreparedPredictionProgramme("programme.literal-prepared-prediction", bank, point, ((source.source_id, protocol),))
    lowered = method.lower_prepared_prediction(programme, campaign=campaign_fixture()[0].campaign, draft_id="draft.literal-prepared-prediction")
    return programme, lowered, initial, raw


def compile_selected(lowered):
    declarations = method.operation_declarations()
    registry = CapabilityRegistry("registry.literal-prepared-prediction", tuple(row.manifest() for row in declarations))
    return compile_recursive_wave(draft=lowered.draft, registry=registry,
        registrations=tuple(row.registration() for row in declarations), implementation_commit="a" * 40,
        output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})


def test_complete_prepared_prediction_compiles_real_source_lifecycle_and_seedless_predictors(selected):
    programme, lowered, *_ = selected
    compiled = compile_selected(lowered)
    assert len(compiled.execution_plan.tasks) == 8
    assert programme.scope == method.SCOPE and "NOT_COMPLETE_E5_OR_E6" in programme.scope
    assert decode_canonical_bytes(programme.canonical_bytes(), type(programme), maximum_bytes=None) == programme
    declarations = method.operation_declarations()
    history = next(row for row in declarations if row.capability_key.endswith(".history"))
    history_runner = history.provider_factory().runner_factory()
    assert type(history_runner) is method.source_owner.MatrixPreparationNativeRunner
    assert history_runner.manifest == history.manifest()
    assert history_runner.manifest.capability_key == method.NAMESPACE + ".history"
    assert callable(history_runner.execute_with_native_subwork)
    assert history.registration().native_work_preparer is method.source_owner.prepare_native_work
    for task in compiled.execution_plan.tasks:
        if task.task_id.endswith((".point", ".mechanical")):
            assert all(row.expected_payload_schema not in (MatrixPreparationSourceBank.SCHEMA, method.MatrixPreparationSource.SCHEMA,
                original.ScheduledAllocation.SCHEMA) for row in task.external_inputs)
    assert sum(row.SCHEMA == programme.point_design.SCHEMA for _, row in lowered.input_records) == 1
    assert len(lowered.input_artifacts) == 2


@pytest.mark.parametrize("damage", ("digest", "size", "logical-id", "source-phase", "causal-link", "missing-phase", "foreign-phase"))
def test_complete_prepared_prediction_refuses_external_or_census_edits(selected, damage):
    _, lowered, *_ = selected
    draft = lowered.draft
    if damage in ("digest", "size", "logical-id"):
        external = draft.external_inputs[0]
        changed = replace(external, **{"expected_content_sha256": "f" * 64} if damage == "digest" else
            {"maximum_size_bytes": external.maximum_size_bytes + 1} if damage == "size" else {"logical_artifact_id": "artifact.unselected-prediction"})
        draft = replace(draft, external_inputs=(changed, *draft.external_inputs[1:]))
    elif damage == "source-phase":
        operation = next(row for row in draft.operations if row.node_id.endswith(".history"))
        config = decode_canonical_bytes(operation.config_payload.encode(), method.source_owner.MatrixPreparationOperationConfig, maximum_bytes=None)
        config = replace(config, allocation_size_bytes=config.allocation_size_bytes + 1)
        draft = replace(draft, operations=tuple(replace(row, config_payload=config.canonical_bytes().decode()) if row == operation else row for row in draft.operations))
    elif damage == "causal-link":
        link = next(row for row in draft.links if row.consumer_node_id.endswith(".point") and row.consumer_input_id == "causal-arrays")
        draft = replace(draft, links=tuple(replace(row, producer_node_id=row.producer_node_id.replace(".project", ".measure")) if row == link else row for row in draft.links))
    elif damage == "missing-phase":
        operation = next(row for row in draft.operations if row.node_id.endswith(".mechanical"))
        draft = replace(draft, operations=tuple(row for row in draft.operations if row != operation),
            selected_operation_ids=tuple(row for row in draft.selected_operation_ids if row != operation.node_id),
            links=tuple(row for row in draft.links if row.consumer_node_id != operation.node_id))
    else:
        operation = next(row for row in draft.operations if row.node_id.endswith(".mechanical"))
        draft = replace(draft, selected_operation_ids=tuple(row for row in draft.selected_operation_ids if row != operation.node_id))
    with pytest.raises(ValueError):
        compile_selected(replace(lowered, draft=draft))


def test_same_researcher_preparation_seam_rebuilds_full_graph_without_running_any_method(selected, tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_prediction_experiment as public
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
    from tests.test_matrix_later_programme import ref

    programme, lowered, initial, templates = selected
    campaign = campaign_fixture()[0].campaign
    specification = public.MatrixPreparedPredictionSpecification("experiment.literal-prepared-prediction", programme.identity,
        ObjectIdentity.from_record(campaign.campaign_id, campaign), 1, 1)
    files = {}
    for key, artifact in lowered.input_artifacts:
        raw = initial if key.startswith("external.initial-state.") else templates
        path = tmp_path / (artifact.artifact_id + ".npz")
        path.write_bytes(raw)
        files[key] = PreparedExperimentFile(artifact, "1.0.0", path.resolve(), len(raw))
    execution = ExecutionSelection(workers=1, environment_id="matrix-main", source_snapshot=ref("snapshot.literal-current"), output_root=str(tmp_path / "output"))

    def forbidden(*args, **kwargs):
        raise AssertionError("preparation/instance authentication ran a source, measurement, outcome reduction or forecast")

    for owner, names in ((method.source_owner.science, ("propagate_preparation", "acquire_preparation", "assess_preparation_arrays")),
            (method.prepared_prefix, ("measure_prepared_prefix", "check_prepared_frames", "project_prepared_prefix")),
            (method.prepared_point, ("causal_feature", "forecast")), (method.prepared_forecast, ("forecast_public",))):
        for name in names:
            monkeypatch.setattr(owner, name, forbidden)
    bound = public.bind_prediction_inputs(specification, {"programme": programme, "campaign": campaign}, files=files)
    prepared = public.prepare_prediction_experiment(specification, scientific_inputs=bound.scientific_inputs,
        execution=execution, method_inputs=bound.method_inputs)
    assert prepared.executable and prepared.census.native_effect_count == 1
    assert dict(prepared.census.operation_counts) == {"design": 1, **{phase: 1 for phase in method.ALL_PHASES}}
    assert len(prepared.input_files) == 2 and len(prepared.draft.operations) == 8
    for _ in range(2):
        public.validate_prediction_instance(specification=specification, allocation=prepared.allocation, draft=prepared.draft,
            source_records=prepared.design_records)
    with pytest.raises(ValueError, match="graph"):
        public.validate_prediction_instance(specification=specification, allocation=prepared.allocation,
            draft=replace(prepared.draft, links=prepared.draft.links[:-1]), source_records=prepared.design_records)
    absent = public.bind_prediction_inputs(specification, {"programme": programme, "campaign": campaign}, files={})
    missing = public.prepare_prediction_experiment(specification, scientific_inputs=absent.scientific_inputs,
        execution=execution, method_inputs=absent.method_inputs)
    assert not missing.executable
    assert {row.source_key for row in missing.dependencies if row.code.endswith(".missing")} == set(files)
