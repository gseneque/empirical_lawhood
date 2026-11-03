# SPDX-License-Identifier: MPL-2.0
"""Literal supplied-innovation maths and refusals, never a scientific run."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import (
    APPLICABILITY, MatrixCouplingRecipe, MatrixPreparationInitialState, MatrixPreparationSource,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_experiment import (
    MatrixPreparationExperimentSpecification, MatrixPreparationSourceBank, bind_preparation_inputs,
    prepare_preparation_experiment, validate_preparation_instance,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history import independent
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.infrastructure.execution import _prepare_native_work
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests import test_matrix_later_programme as later
from tests.test_matrix_later_programme import ref
from tests.test_matrix_parameter_history import publish


@pytest.fixture
def metadata(tmp_path):
    return later.metadata.__wrapped__(tmp_path)


@pytest.fixture
def selected(metadata):
    _, original = metadata
    # Literal noncommuting Hermitian toy matrices and innovations; no RNG,
    # native contact, exposed source acquisition or provenance capture occurs.
    real = np.arange(96, dtype="<f8").reshape(2, 3, 4, 4) / 10000
    position = np.asarray((real + real.swapaxes(-1, -2)) / 2, dtype="<c16")
    momentum = np.asarray(np.flip(position, axis=1) / 10, dtype="<c16")
    raw, members = encode_matrix_arrays({"positions": position, "momenta": momentum})
    target = tuple(D(str(value)) for value in original.coordinate.couplings(original.policy.cutoff_tick))
    artifact = ArtifactIdentity("array.literal-shared-initial", "prepared-matched-initial", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    initial = MatrixPreparationInitialState("state.literal-shared-initial", ref("history.exposed-literal"),
        ref("assessment.exposed-literal"), artifact, members, target)
    n = original.policy.cutoff_tick
    schedule = tuple(target if tick in (0, 2 * n) else (target[0] + D("0.01") * (tick % 3), target[1])
        for tick in range(2 * n + 1))
    recipe = MatrixCouplingRecipe("recipe.literal.fixed", "FIXED_COUPLING", n, schedule,
        "HALF_TICK_COUPLING_TOTAL_VARIATION_L1", "effort.coupling-total-variation")
    source = MatrixPreparationSource("source.literal.prepared", ScheduledPublicSource.from_source(original), original.root,
        initial, recipe, original.provenance, original.numerical_design)
    coarse = np.repeat(position[None], n, axis=0)
    bridge = np.repeat(momentum[None], n, axis=0)
    return source, raw, coarse, bridge, original.allocation


def test_complete_half_tick_recipe_original_independent_equations_and_denominators(selected):
    source, initial, coarse, bridge, allocation = selected
    source.validate_allocation(allocation)
    arrays = science.propagate_preparation(source, initial, coarse_innovations=coarse, bridge_innovations=bridge)
    raw, operand = science.preparation_array_product(source, initial, arrays, artifact_id="array.literal-preparation")
    result = science.assess_preparation_arrays(source, initial, operand, arrays, assessment_id="assessment.literal-preparation")
    n = source.total_ticks
    assert result.numerical_pass and tuple(row.denominator_steps for row in result.controls) == (n, 2 * n, n, n)
    assert tuple(row.denominator_real_coordinates for row in result.controls) == (192, 192, 192, 96)
    assert source.applicability == APPLICABILITY and source.recipe.effort > 0
    assert arrays["primary_positions"].shape[0] == n + 1 and arrays["fine_positions"].shape[0] == 2 * n + 1
    assert np.array_equal(arrays["primary_innovations"], coarse)
    assert np.array_equal(arrays["bridge_innovations"], bridge)
    assert len(science.consume_preparation_arrays(source, initial, operand, raw)) == 11
    assert decode_canonical_bytes(source.canonical_bytes(), type(source), maximum_bytes=None) == source
    assert "APPLICABILITY_BOUND" in result.standing


def test_original_literal_trace_derivative_at_prepared_state(selected):
    source, raw, _, _, _ = selected
    state = science.initial_state(source.initial, raw)
    alpha = np.asarray(source.recipe.half_tick_couplings[1], dtype=float)
    gradient = independent.potential_gradient(state.positions, source.member, alpha)
    # Every diagonal and real/imaginary off-diagonal direction in both sectors.
    for sector in range(2):
        for component in range(3):
            for row in range(4):
                for column in range(row, 4):
                    for imaginary in ((False,) if row == column else (False, True)):
                        direction = np.zeros_like(state.positions)
                        direction[sector, component, row, column] = 1j if imaginary else 1
                        direction[sector, component, column, row] = -1j if imaginary else 1
                        epsilon = 1e-6
                        measured = (independent.potential(state.positions + epsilon * direction, source.member, alpha)
                            - independent.potential(state.positions - epsilon * direction, source.member, alpha)) / (2 * epsilon)
                        assert measured == pytest.approx(np.vdot(direction, gradient).real, abs=1e-8, rel=1e-6)


@pytest.mark.parametrize("damage", ("member", "fine-state", "half-schedule", "clock", "bridge", "census", "initial"))
def test_preparation_refuses_complete_census_or_independent_native_mutations(selected, damage):
    source, initial, coarse, bridge, _ = selected
    arrays = science.propagate_preparation(source, initial, coarse_innovations=coarse, bridge_innovations=bridge)
    if damage == "member":
        arrays["primary_positions"] = arrays["primary_positions"][:-1]
    elif damage == "fine-state":
        arrays["fine_momenta"][3, 0, 0, 0, 0] += 0.01
    elif damage == "half-schedule":
        arrays["fine_alpha_tilde"][1, 0] += 0.01
    elif damage == "clock":
        arrays["fine_ticks"][1] = 2
    elif damage == "bridge":
        arrays["fine_innovations"][0, 0, 0, 0, 0] += 0.01
    elif damage == "census":
        del arrays["bridge_innovations"]
    else:
        arrays["primary_positions"][0, 0, 0, 0, 0] += 0.01
    if damage in ("fine-state", "bridge"):
        _, operand = science.preparation_array_product(source, initial, arrays, artifact_id="array.mutated-literal")
        result = science.assess_preparation_arrays(source, initial, operand, arrays, assessment_id="assessment.mutated-literal")
        assert not result.numerical_pass
        assert sum(row.denominator_steps for row in result.controls) == 5 * source.total_ticks
        assert any(row.failed_steps for row in result.controls)
    else:
        with pytest.raises(ValueError, match="geometry|initial|schedule|clock|members"):
            science.preparation_array_product(source, initial, arrays, artifact_id="array.forbidden-literal")


@pytest.mark.parametrize("damage", ("hold", "duration", "restored", "initial-coupling", "applicability"))
def test_recipe_and_native_source_refuse_undeclared_physics(selected, damage):
    source, _, _, _, _ = selected
    with pytest.raises(ValueError, match="HOLD|duration|restored|coupling|source"):
        if damage == "hold":
            replace(source.recipe, kind="HOLD")
        elif damage == "duration":
            replace(source, recipe=replace(source.recipe, primary_steps=source.total_ticks + 1))
        elif damage == "restored":
            replace(source, recipe=replace(source.recipe,
                half_tick_couplings=(*source.recipe.half_tick_couplings[:-1], (D(999), D(999)))))
        elif damage == "initial-coupling":
            replace(source, initial=replace(source.initial, alpha_tilde=(D(0), D(0))))
        else:
            replace(source, applicability="GENERAL_FORCE_RECIPE")


def test_hold_and_path_effort_are_exact_and_decimal_context_independent(selected):
    source, _, _, _, _ = selected
    constant = source.recipe.half_tick_couplings[0]
    hold = replace(source.recipe, recipe_id="recipe.literal.hold", kind="HOLD",
        half_tick_couplings=(constant,) * len(source.recipe.half_tick_couplings))
    assert hold.effort == 0
    expected = source.recipe.effort
    duration = source.duration
    with localcontext() as context:
        context.prec = 2
        assert source.recipe.effort == expected and source.duration == duration


def test_lowering_uses_real_native_declarations_shared_initial_and_allocation_once(selected):
    source, _, _, _, allocation = selected
    hold = replace(source.recipe, recipe_id="recipe.literal.hold", kind="HOLD",
        half_tick_couplings=(source.initial.alpha_tilde,) * len(source.recipe.half_tick_couplings))
    other = replace(source, source_id="source.literal.hold", recipe=hold)
    campaign = campaign_fixture()[0].campaign
    lowered = bindings.lower_preparation_sources((source, other), allocations=(allocation,), campaign=campaign,
        draft_id="draft.literal-preparation")
    declarations = bindings.operation_declarations()
    registry = CapabilityRegistry("registry.literal-preparation", tuple(row.manifest() for row in declarations))
    compiled = compile_recursive_wave(draft=lowered.draft, registry=registry,
        registrations=tuple(row.registration() for row in declarations), implementation_commit="a" * 40,
        output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    assert len(compiled.execution_plan.tasks) == 4
    assert sum(record.SCHEMA == allocation.SCHEMA for _, record in lowered.input_records) == 1
    assert len(lowered.initial_artifacts) == 1 and len(lowered.draft.development_study.assigned_unit_ids) == 1
    assert all(row.registration().native_work_preparer is bindings.prepare_native_work for row in declarations if row.registration().native_effect)


def test_actual_sealed_initial_native_work_preparation_is_read_only_and_deterministic(selected, metadata, tmp_path):
    source, initial, _, _, allocation = selected
    plane, _ = metadata
    config = bindings.MatrixPreparationOperationConfig("config." + bindings.node_id(source, "history"), "history", source,
        len(allocation.canonical_bytes()))
    records = ((config.config_id, config.SCHEMA, config.canonical_bytes()),
        (source.source_id, source.SCHEMA, source.canonical_bytes()),
        (allocation.allocation_id, allocation.SCHEMA, allocation.canonical_bytes()))
    manifests = tuple(publish(plane, *row) for row in records) + (
        publish(plane, source.initial.array_artifact.artifact_id, MATRIX_ARRAY_SCHEMA, initial),)
    ports = tuple(sorted((plane.open(manifest, binding=WorkerInputBinding(manifest.logical.logical_artifact_id,
        manifest.materialization.materialization_id, manifest.logical.payload_schema, manifest.logical.media_type,
        manifest.materialization.size_bytes, manifest.logical.visibility_ceiling, manifest.logical.outcome_access, WorkerInputKind.EXTERNAL),
        maximum_bytes=manifest.materialization.size_bytes) for manifest in manifests), key=lambda row: row.artifact_id))
    declaration = next(row for row in bindings.operation_declarations() if row.capability_key.endswith(".history"))
    parent = NativeEffectContact("test.preparation.no-entry", bindings.node_id(source, "history"), "test.preparation.no-entry.attempt-001",
        ref("test.literal-plan"), ObjectIdentity(bindings.node_id(source, "history"), "empirical-lawhood/runtime/execution-task", "1.0.0", "a" * 64),
        source.provenance.observed_git_head, tuple(sorted(row.materialization.materialization_id for row in manifests)), ())
    outputs = (WorkerOutputPort(parent.task_id + ".product", bindings.MatrixPreparationHistory.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json"), WorkerOutputPort(parent.task_id + ".arrays", MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "array.future-preparation"))
    context = TaskContext(parent.run_id, parent.task_id, parent.attempt_id,
        CapabilityConfigRef(config.config_id, config.SCHEMA, declaration.manifest().config_schema_sha256, config.fingerprint(), config.config_id),
        tuple(port.binding for port in ports), ports, tuple(sorted(outputs, key=lambda row: row.output_id)), declaration.permissions,
        declaration.outcome_access, declaration.resources, WorkerIsolationProfile.TRUSTED_LOCAL)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    try:
        runner = declaration.provider_factory().runner_factory()
        assert type(runner) is bindings.MatrixPreparationNativeRunner
        assert runner.manifest == declaration.manifest()
        first = _prepare_native_work(bindings.prepare_native_work, runner, context, parent)
        second = _prepare_native_work(bindings.prepare_native_work, runner, context, parent)
        assert first == second and first.scientific_unit_ids == (source.root.root.independent_group_id,)
        assert len(first.definitions) == len(first.rosters) == 1
        assert first.definitions[0].input_materialization_ids == parent.input_materialization_ids
        assert all(port.tell() == 0 for port in context.input_ports)
        assert {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
    finally:
        for port in ports:
            port.close()


def test_same_public_preparation_seam_retains_original_file_census_and_full_instance(selected, tmp_path):
    source, raw, _, _, original_allocation = selected
    campaign = campaign_fixture()[0].campaign
    bank = MatrixPreparationSourceBank("bank.literal-preparation", (original_allocation,), (source,))
    specification = MatrixPreparationExperimentSpecification("experiment.literal-preparation", bank.identity,
        ObjectIdentity.from_record(campaign.campaign_id, campaign), 1, 1)
    path = tmp_path / "literal-initial.npz"
    path.write_bytes(raw)
    key, artifact = bank.input_artifacts[0]
    handle = PreparedExperimentFile(artifact, "1.0.0", path.resolve(), len(raw))
    inputs = bind_preparation_inputs(specification, {"bank": bank, "campaign": campaign}, files={key: handle})
    execution = ExecutionSelection(workers=1, environment_id="matrix-main", source_snapshot=ref("snapshot.actual-selected"), output_root=str(tmp_path / "output"))
    result = prepare_preparation_experiment(specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=execution)
    assert result.executable and result.census.native_effect_count == 1 and result.input_files == ((key, handle),)
    validate_preparation_instance(specification=specification, allocation=result.allocation, draft=result.draft,
        source_records=result.design_records)
    with pytest.raises(ValueError, match="graph"):
        validate_preparation_instance(specification=specification, allocation=result.allocation,
            draft=replace(result.draft, links=result.draft.links[:-1]), source_records=result.design_records)
    with pytest.raises(ValueError, match="census"):
        validate_preparation_instance(specification=specification, allocation=result.allocation,
            draft=result.draft, source_records=(*result.design_records, ("unselected.record", bank)))
    absent = bind_preparation_inputs(specification, {"bank": bank, "campaign": campaign}, files={})
    missing = prepare_preparation_experiment(specification, scientific_inputs=absent.scientific_inputs,
        method_inputs=absent.method_inputs, execution=execution)
    assert not missing.executable and any(row.source_key == key and row.code.endswith(".missing") for row in missing.dependencies)
    changed = prepare_preparation_experiment(replace(specification, expected_sources=2), scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=execution)
    assert not changed.executable and any(row.code.endswith(".census") for row in changed.dependencies)


def test_exposed_source_checkpoint_refuses_protected_original_role(selected):
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole

    source, _, _, _, _ = selected
    root = replace(source.root.root, role=MatrixProgrammeRole.CONFIRMATION)
    protected = replace(source, root=replace(source.root, root=root), original=replace(source.original, root=root))
    with pytest.raises(ValueError, match="development"):
        bindings.development_root((protected,), "study.forbidden-protected-as-exposed")
