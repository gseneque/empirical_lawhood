# SPDX-License-Identifier: MPL-2.0
"""Protected response-consumer encoding controls over exposed authored arrays.

The available causal state is the existing disclosed software operand. Complete
future arrays below are literal constant paths, deliberately not simulator
output. Their independent native-transition failure must survive both encodings.
Nothing here acquires a trajectory, issues a study or qualifies scientific data.
"""

from contextlib import ExitStack
from dataclasses import replace
from hashlib import sha256
import json
from types import SimpleNamespace
import tracemalloc

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_science as science
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast, response_records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_science as original_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledNativeEvidence
from empirical_lawhood.infrastructure import dataset_readers
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion
from tests.test_matrix_e3_response_lifecycle_available import available as available
from tests.test_matrix_e3_response_preparation import case as case, original_case as original_case
from tests.test_matrix_e3_response_science import LIMITS, blocked, byte_fetch, context, no_native as no_native, score_config, store
from tests.test_matrix_e3_scheduled_datasets import BLOCK, physical_dataset


@pytest.fixture(autouse=True)
def no_response_production(monkeypatch, no_native):  # noqa: F811
    """Cold consumers may not acquire, fit, draw or perform native contact."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods
    from empirical_lawhood.runtime import experimental_statistics

    for owner, names in ((original_science, ("native_responses", "panel_innovations", "native_scheduled_branch", "hermitian_noise")),
            (protected_experiment_methods, ("fit_protected_e3_models",)),
            (experimental_statistics, ("fit_standardized_ridge",)),
            (np.linalg, ("eigvalsh",)), (ExternalNativeEffectContactStore, ("begin",)),
            (ExternalNativeSubworkStore, ("begin", "contact"))):
        for name in names:
            monkeypatch.setattr(owner, name, blocked)


def operands(case):
    return (case.history.arrays, case.causal.arrays, case.protocol.templates,
        case.physical.arrays, case.response.arrays)


def received_negative(case):
    """Complete literal future plus disclosed receipt metadata, no native run.

    The real protected boundary still validates every direct operand, stream,
    completion and exact publication size/hash. Literal held paths intentionally
    violate the original forced/noisy dynamics; no metadata makes them valid.
    """
    result = SimpleNamespace(**vars(case))
    prefix = decode_matrix_arrays(case.native_raw, case.history.arrays)
    horizon = case.protocol.horizon_steps[-1]
    arrays = {}
    for panel in case.panels:
        for name, count in (("primary", horizon), ("fine", 2 * horizon), ("bridge", horizon)):
            arrays["noise." + panel.panel_id + "." + name] = np.zeros((count, 2, 3, 4, 4), dtype="<c16")
    for branch, view, panel, _, _ in response_records.branch_census(case.protocol, case.panels):
        label, multiplier = view.lower(), 1 if view == "PRIMARY" else 2
        count, start = multiplier * horizon, multiplier * case.source.policy.cutoff_tick
        values = {phase: np.repeat(prefix[label + "_" + phase][-1:], count + 1, axis=0)
            for phase in ("positions", "momenta")}
        values.update(innovations=arrays["noise." + panel.panel_id + "." + label],
            ticks=np.arange(start, start + count + 1, dtype="<i8"),
            alpha_tilde=np.asarray([case.source.coordinate.couplings(tick, refinement=multiplier)
                for tick in range(start, start + count + 1)], dtype="<f8"))
        arrays.update(("branch." + branch + "." + name, value) for name, value in values.items())
    raw, operand = response_forecast.array_product(case.protocol, arrays, role="RESPONSES",
        artifact_id="literal.encoding.received-arrays", producers=(case.native_config.source.identity,
            identity(case.selection), records._object(case.physical), identity(case.error), identity(case.profile)),
        access=OutcomeAccess.EVALUATION_SEALED, visibility=VisibilityCeiling.PROSPECTIVE)
    _, configuration, task, operation, direct, streams, outputs = records.protected_e3_response_native_contract(
        case.native_config, **{key: value for key, value in context(case).items() if key in (
            "source", "manifest", "specification", "selection", "protocol", "numerical_profile", "panels",
            "history", "causal", "physical", "error")})
    original = case.history.native
    parent = replace(original.definition.parent_contact, task_id=task,
        execution_task=replace(original.definition.parent_contact.execution_task, object_id=task))
    definition = replace(original.definition, subwork_id="responses." + case.source.root_id,
        operation_id=operation, parent_contact=parent, configuration=configuration,
        sources=direct, streams=streams, outputs=outputs)
    native_task = "native-subwork." + sha256((task + ":" + definition.subwork_id).encode()).hexdigest()
    consumed = tuple(row for row in streams if row.object_id.endswith(("autonomous-coarse-driver", "autonomous-fine-bridge")))
    completion = NativeSubworkCompletion(definition.identity, original.completion.contact,
        OperationalStatus.SUCCEEDED, ("arrays",), (), consumed,
        tuple(row for row in streams if row not in consumed), (), InquiryCost(None, None, None),
        "EXPOSED AUTHORED CONSTANT ARRAYS AND METADATA ONLY; NO NATIVE CONTACT OR SCIENTIFIC QUALIFICATION", None, ())
    publications = []
    for suffix, payload, schema, profile, media in (("output.arrays", raw, operand.array_artifact.payload_schema,
            ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
            ("completion", completion.canonical_bytes(), completion.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")):
        from tests.native_completion_fixtures import completion_parents
        parents = completion_parents(completion, VisibilityCeiling.PROSPECTIVE, OutcomeAccess.EVALUATION_SEALED) if suffix == 'completion' else ()
        publications.append(case.plane.write(ArtifactWriteRequest(native_task + "." + suffix,
            "literal/encoding-metadata/" + suffix, schema, profile, media, "literal-encoding", "literal",
            payload, VisibilityCeiling.PROSPECTIVE, tuple(parent.visibility_ceiling for parent in parents),
            OutcomeAccess.EVALUATION_SEALED, lineage_parents=parents)))
    attempt = parent.run_id + "." + native_task + ".attempt-001"
    receipt = CanonicalTaskReceipt("receipt." + attempt, parent.run_id, native_task, attempt,
        parent.implementation_commit, definition.input_materialization_ids,
        tuple(sorted((row.materialization for row in publications), key=lambda row: row.materialization_id)),
        tuple(sorted((row.logical for row in publications), key=lambda row: row.logical_artifact_id)), (),
        OperationalStatus.SUCCEEDED, ())
    result.response_raw = raw
    result.response = replace(case.response, configuration=records._object(case.native_config),
        protocol=records._object(case.protocol), numerical_profile=identity(case.profile), response_selection=identity(case.selection),
        history=identity(case.history), causal_prefix=identity(case.causal),
        physical_forecast=records._object(case.physical), error_forecast=identity(case.error), arrays=operand,
        native=(ScheduledNativeEvidence(definition, completion, receipt),), disposition="COMPLETED", reason_codes=())
    return result


def assess(case, fetch):
    score = science.assess_responses(score_config(case), case.native_config, case.response, **context(case),
        fetch=fetch, **LIMITS, score_id="score.literal.encoding")
    outcome = science.project_outcome(score_config(case), case.native_config, case.response, score,
        **context(case), record_id="outcome.literal.encoding")
    return score, outcome


@pytest.mark.parametrize("variant", ("nonuse", "received-negative"))
def test_same_protected_assessor_keeps_complete_results_over_npz_and_physical_members(case, available, tmp_path, monkeypatch, variant):  # noqa: F811
    selected = case if variant == "nonuse" else received_negative(available)
    payloads = store(selected)
    expected = assess(selected, byte_fetch(payloads))
    original_bytes = tuple(value.canonical_bytes() for value in operands(selected))
    slices = []
    read = dataset_readers._VerifiedDatasetSession.read_member_bytes

    def bounded_read(session, name, start, stop):
        slices.append(stop - start)
        assert 0 <= stop - start <= LIMITS["maximum_slice_bytes"]
        return read(session, name, start, stop)

    with ExitStack() as stack:
        readers = {value.array_artifact.artifact_id: stack.enter_context(physical_dataset(value,
            payloads[value.array_artifact.artifact_id], tmp_path / str(index)))
            for index, value in enumerate(operands(selected))}
        manifests = tuple(readers[value.array_artifact.artifact_id].manifest for value in operands(selected))
        # The actual transform writer admitted every byte of every original
        # member against its original hash, dtype, shape and scientific refs.
        assert tuple(tuple((member.name, member.dtype, member.shape, member.sha256) for member in row.members)
            for row in manifests) == tuple(tuple((member.name, member.dtype, member.shape, member.sha256)
                for member in value.members) for value in operands(selected))
        monkeypatch.setattr(dataset_readers._VerifiedDatasetSession, "read_member_bytes", bounded_read)
        tracemalloc.start()
        try:
            actual = assess(selected, lambda artifact: readers[artifact.artifact_id])
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
    assert tuple(value.canonical_bytes() for value in actual) == tuple(value.canonical_bytes() for value in expected)
    assert tuple(value.canonical_bytes() for value in operands(selected)) == original_bytes
    score, outcome = actual
    assert len(score.cells) == 240 and len(score.cumulative_log_errors) == 15
    assert tuple(view.view_id for view in outcome.views) == ("fine", "primary")
    assert all(view.errors == (None,) * 15 and view.dispositions == ("NUMERICAL_FAILURE",) * 15 for view in outcome.views)
    assert not score.numerical_pass and all(value is None for value in score.cumulative_log_errors)
    assert slices and max(slices) <= LIMITS["maximum_slice_bytes"]
    if variant == "received-negative":
        assert len(selected.response.arrays.members) == 246 and len(selected.response.branch_ids) == 48
        assert score.disposition == "NATIVE_CROSSCHECK_FAILED" and len(score.controls) == 48
        assert sum(value.denominator_steps for value in score.controls) == 24 * (128 + 256)
        assert all(value.denominator_real_coordinates == 192 for value in score.controls)
        assert any(value.failed_steps for value in score.controls)
        assert peak < sum(value.size_bytes for value in selected.response.arrays.members)
    else:
        assert score.disposition == "UNEVALUABLE" and not score.controls
        assert all(value.actual_odd_responses is None for value in score.cells)
    (tmp_path / "protected-response-encoding-evidence.json").write_text(json.dumps({
        "scope": "Exposed consumer conformance only; authored arrays/metadata; no native acquisition, scientific qualification or complete public encoding route.",
        "variant": variant, "logical_dataset_sha256": [row.fingerprint() for row in manifests],
        "logical_bytes": [row.size_bytes for row in manifests], "member_counts": [len(row.members) for row in manifests],
        "score_sha256": score.fingerprint(), "outcome_sha256": outcome.fingerprint(),
        "score_disposition": score.disposition, "score_cells": len(score.cells), "controls": len(score.controls),
        "transition_steps": sum(value.denominator_steps for value in score.controls),
        "control_real_coordinates": sorted({value.denominator_real_coordinates for value in score.controls}),
        "exact_canonical_result_parity": True, "original_array_owners_unchanged": True,
        "chunk_bytes": BLOCK, "physical_cache_bytes_per_source": 2 * BLOCK,
        "maximum_assessment_slice_bytes": max(slices), "assessment_slice_count": len(slices),
        "traced_peak_bytes_through_assessment_and_final_seals": peak,
        "memory_scope": "Includes protected source/record validation, cold prediction reproof, independent transition checks, output projection and final seals. Excludes fixture/transform construction, RSS and kernel caches; no population-scaling claim.",
    }, indent=2) + "\n")


@pytest.mark.parametrize("damage", ("omitted-member", "dtype", "shape"))
def test_changed_complete_physical_manifest_refuses_before_response_arithmetic(case, tmp_path, monkeypatch, damage):  # noqa: F811
    payloads = store(case)
    with physical_dataset(case.causal.arrays, case.causal_raw, tmp_path / "causal") as reader:
        members = reader.manifest.members
        if damage == "omitted-member":
            members = members[1:]
        else:
            index = next(index for index, member in enumerate(members)
                if member.name == ("fine_ticks" if damage == "dtype" else "fine_positions"))
            member = members[index]
            changed = replace(member, **({"dtype": "<f8"} if damage == "dtype" else {"shape": (member.shape[0], 3, 2, 4, 4)}))
            members = (*members[:index], changed, *members[index + 1:])
        other = dataset_readers.ArrayDatasetReader(replace(reader.manifest, members=members), reader._source, **LIMITS)
        monkeypatch.setattr(science, "assess_paired_response_arrays", blocked)
        with pytest.raises(ValueError, match="scientific values or source associations"):
            assess(case, lambda artifact: other if artifact == case.causal.arrays.array_artifact else payloads[artifact.artifact_id])


@pytest.mark.parametrize("damage", ("mutation", "truncation"))
def test_changed_admitted_physical_value_refuses_in_same_protected_assessor(case, tmp_path, damage):  # noqa: F811
    payloads = store(case)
    directory = tmp_path / "responses"
    with physical_dataset(case.response.arrays, case.response_raw, directory) as reader:
        path = directory / "unentered_branches.values"
        with path.open("r+b", buffering=0) as handle:
            if damage == "truncation":
                handle.truncate(path.stat().st_size - 8)
            else:
                handle.seek(-1, 2)
                value = handle.read(1)
                handle.seek(-1, 2)
                assert handle.write(bytes((value[0] ^ 1,))) == 1
        with pytest.raises(ValueError, match="physical (array|dataset)"):
            assess(case, lambda artifact: reader if artifact == case.response.arrays.array_artifact else payloads[artifact.artifact_id])
