# SPDX-License-Identifier: MPL-2.0
"""Complete prepared-prefix witnesses and independent received-byte controls."""

from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_prefix as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from tests import test_matrix_coupling_preparation as fixture


@pytest.fixture
def case(tmp_path):
    metadata = fixture.metadata.__wrapped__(tmp_path)
    source, initial, coarse, bridge, _ = fixture.selected.__wrapped__(metadata)
    arrays = preparation_science.propagate_preparation(source, initial, coarse_innovations=coarse, bridge_innovations=bridge)
    raw, operand = preparation_science.preparation_array_product(source, initial, arrays, artifact_id="array.literal-prefix-preparation")
    numerical = preparation_science.assess_preparation_arrays(source, initial, operand, arrays,
        assessment_id="assessment.literal-prefix-preparation")
    diagnostics, witness = method.measure_prepared_prefix(source, initial, operand, numerical, raw,
        artifact_id="array.literal-prepared-factor-witness")
    return source, initial, operand, numerical, witness, raw, diagnostics


def test_prepared_prefix_cold_full_denominators_and_seedless_causal_nonuse(case, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("prepared prefix cold reader entered measurement, producer, RNG or eigensolve")

    monkeypatch.setattr(method, "measure_prepared_prefix", forbidden)
    monkeypatch.setattr(preparation_science, "acquire_preparation", forbidden)
    monkeypatch.setattr(preparation_science, "baoab_step_with_hermitian_noise", forbidden)
    monkeypatch.setattr(np.linalg, "eigh", forbidden)
    monkeypatch.setattr(np.random, "Generator", forbidden)
    frames = method.check_prepared_frames(*case)
    source, _, operand, _, witness, *_ = case
    count = 2 * len(source.original.policy.factor_rule.sectors) * len(source.original.policy.factor_rule.lattice)
    assert tuple(len(row.measured_errors) for row in frames.controls) == (count, 15 * count, count, count, count, count)
    assert len(witness.traces) == 4 and sum(len(row.observations) for row in witness.traces) == count
    raw, causal = method.project_prepared_prefix(*case[:5], frames, *case[5:], artifact_id="array.literal-prepared-causal")
    values = decode_matrix_arrays(raw, causal.arrays)
    assert causal.source == source.identity and causal.preparation == method.preparation_identity(operand)
    assert causal.cutoff_tick == source.total_ticks
    assert not any(name.endswith("innovations") for name in values)
    assert values["primary_ticks"].shape == (source.total_ticks + 1,)
    assert values["fine_ticks"].shape == (2 * source.total_ticks + 1,)
    if causal.disposition != "AVAILABLE":
        assert causal.frame_sha256 is None and np.isnan(values["frame"]).all()


def test_prepared_prefix_refuses_thinned_view_sector_or_forged_frame_assessment(case):
    source, initial, operand, numerical, witness, raw, diagnostics = case
    with pytest.raises(ValueError, match="complete lattice"):
        method.check_prepared_frames(source, initial, operand, numerical, replace(witness, traces=witness.traces[:-1]), raw, diagnostics)
    frames = method.check_prepared_frames(*case)
    altered = replace(frames, record_id="frames.unselected-original")
    with pytest.raises(ValueError, match="assessment"):
        method.project_prepared_prefix(source, initial, operand, numerical, witness, altered, raw, diagnostics,
            artifact_id="array.forbidden-prepared-causal")


def test_independent_prepared_frame_operator_check_retains_changed_measurement_negative(case):
    source, initial, operand, numerical, witness, raw, diagnostics = case
    arrays = {name: value.copy() for name, value in decode_matrix_arrays(diagnostics, witness.arrays).items()}
    key = next(name for name in arrays if name.endswith("_operator"))
    arrays[key][0, 0, 0] += .01
    changed_raw, members = encode_matrix_arrays(arrays, nonfinite_members=tuple(row.name for row in witness.arrays.members if not row.finite_required))
    changed_artifact = replace(witness.arrays.array_artifact, artifact_id="array.changed-prepared-operator",
        sha256=sha256(changed_raw).hexdigest(), size_bytes=len(changed_raw))
    changed_witness = replace(witness, arrays=replace(witness.arrays, array_artifact=changed_artifact, members=members))
    measured = method.check_prepared_frames(source, initial, operand, numerical, changed_witness, raw, changed_raw)
    assert not measured.numerical_pass
    operator = next(row for row in measured.controls if row.method == "raw-operator")
    assert operator.disposition == "VIOLATED" and len(operator.measured_errors) == 28
