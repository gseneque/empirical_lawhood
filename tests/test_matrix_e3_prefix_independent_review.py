# SPDX-License-Identifier: MPL-2.0
"""Independent literal prefix consistency controls; no scientific authority.

Native stepping and random generation are blocked. Source, contact and receipt
metadata are exposed fixtures, and do not establish actual custody or entry.
"""

from dataclasses import replace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_records as owner
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_source
from tests import test_matrix_e3_prefix_records as producer
from tests.test_matrix_e3_prefix_science_extraction import blocked
from tests.test_matrix_factor_confirmation_eligibility import stock
from tests.test_matrix_parameter_history import source as parameter_template
from tests.test_matrix_scheduled_history import scheduled


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    root = tmp_path_factory.mktemp("independent-prefix-records")
    base = scheduled.__wrapped__(stock.__wrapped__(root, parameter_template().provenance))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(parameter_source, "acquire_parameter_history", blocked)
        patch.setattr(parameter_history, "advance_parameter_pair", blocked)
        patch.setattr(np.random, "Generator", blocked)
        patch.setattr(np.random, "PCG64DXSM", blocked)
        yield producer.current_case(base, patch)


def _causal_members(case, members):
    return replace(case.causal, arrays=replace(case.causal.arrays, members=members))


def test_selected_full_controls_preserve_original_measured_negative(case):
    assert case.source.policy.cutoff_tick == case.specification.measurement.origin_tick == 256
    assert case.numerical.controls == case.old_numerical.controls
    assert case.frames.controls == case.old_frames.controls
    assert tuple(len(control.measured_errors) for control in case.numerical.controls) == (256, 512, 256, 256)
    assert tuple(len(control.measured_errors) for control in case.frames.controls) == (68, 1020, 68, 68, 68, 68)
    assert not case.numerical.numerical_pass
    assert case.causal.disposition == case.old_causal.disposition == "UNEVALUABLE"
    assert case.causal.reason == case.old_causal.reason == "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED"
    case.causal.validate_source(case.source, case.history, case.numerical, case.witness, case.frames)


@pytest.mark.parametrize("change", ("fine-extent", "complex-to-real"))
def test_causal_array_schema_cannot_hide_missing_physical_coordinates(case, change):
    members = []
    for member in case.causal.arrays.members:
        if change == "fine-extent" and member.name == "fine_positions":
            member = replace(member, shape=(*member.shape[:-1], 3))
        elif change == "complex-to-real" and member.name == "primary_positions":
            member = replace(member, dtype="<f8")
        members.append(member)
    with pytest.raises(ValueError, match="complete array members"):
        _causal_members(case, tuple(members))


def test_nonframe_phase_cannot_opt_out_of_finite_values(case):
    members = tuple(replace(member, finite_required=False) if member.name == "fine_momenta" else member
        for member in case.causal.arrays.members)
    with pytest.raises(ValueError, match="finite frame or phase"):
        _causal_members(case, members)


def test_witness_array_producer_cannot_rebind_the_numerical_assessment(case):
    numerical = owner.identity(case.numerical)
    producers = tuple(sorted((replace(row, object_fingerprint="e" * 64) if row == numerical else row
        for row in case.witness.arrays.producers), key=lambda row: row.object_id))
    witness = replace(case.witness, arrays=replace(case.witness.arrays, producers=producers))
    with pytest.raises(ValueError, match="exact producers"):
        witness.validate_source(case.source, case.history, case.numerical)


@pytest.mark.parametrize("reason", ("CAUSAL_CUTOFF_OBSERVATION_UNAVAILABLE",
    "DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED", "UNRECORDED_SOURCE_FAILURE"))
def test_negative_equation_failure_cannot_be_relabelled_as_other_nonuse(case, reason):
    disposition = "NO_ORIGIN" if reason == "DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED" else "UNEVALUABLE"
    changed = replace(case.causal, reason=reason, disposition=disposition)
    with pytest.raises(ValueError, match="cutoff admission or nonuse"):
        changed.validate_source(case.source, case.history, case.numerical, case.witness, case.frames)


def _ordinary_alias(case):
    artifact = replace(case.history.arrays.array_artifact,
        artifact_id="ordinary." + case.history.native.definition.parent_contact.task_id + ".arrays")
    return replace(case.history, arrays=replace(case.history.arrays, array_artifact=artifact))


def test_ordinary_array_alias_preserves_original_nested_checkpoint_and_receipt(case):
    changed = _ordinary_alias(case)
    assert changed.arrays.array_artifact.artifact_id != case.history.arrays.array_artifact.artifact_id
    assert changed.arrays.array_artifact.sha256 == case.history.arrays.array_artifact.sha256
    assert changed.native.receipt.canonical_bytes() == case.history.native.receipt.canonical_bytes()
    assert changed.checkpoint.canonical_bytes() == case.history.checkpoint.canonical_bytes()
    assert changed.validate_source(case.config, case.manifest, specification=case.specification) == case.source


def test_ordinary_array_alias_cannot_change_original_native_bytes(case):
    alias = _ordinary_alias(case)
    artifact = replace(alias.arrays.array_artifact, sha256="e" * 64)
    changed = replace(alias, arrays=replace(alias.arrays, array_artifact=artifact))
    with pytest.raises(ValueError):
        changed.validate_source(case.config, case.manifest, specification=case.specification)


def test_ordinary_array_alias_cannot_replace_checkpoint_native_array_identity(case):
    alias = _ordinary_alias(case)
    checkpoint = replace(alias.checkpoint, prefix_arrays=alias.arrays.array_artifact)
    receipt = alias.native.receipt
    checkpoint_id = receipt.task_id + ".output.checkpoint"
    receipt = replace(receipt,
        output_logical_artifacts=tuple(replace(row, content_sha256=checkpoint.fingerprint())
            if row.logical_artifact_id == checkpoint_id else row for row in receipt.output_logical_artifacts),
        output_materializations=tuple(replace(row, physical_sha256=checkpoint.fingerprint(),
            size_bytes=len(checkpoint.canonical_bytes())) if row.logical_artifact_id == checkpoint_id else row
            for row in receipt.output_materializations))
    changed = replace(producer.native_change(alias, receipt=receipt), checkpoint=checkpoint)
    assert changed.checkpoint.prefix_arrays.artifact_id == alias.arrays.array_artifact.artifact_id
    assert changed.checkpoint.prefix_arrays.sha256 == case.history.checkpoint.prefix_arrays.sha256
    with pytest.raises(ValueError, match="physical native arrays/checkpoint custody"):
        changed.validate_source(case.config, case.manifest, specification=case.specification)
