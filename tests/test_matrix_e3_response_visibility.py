# SPDX-License-Identifier: MPL-2.0
"""Exposed TRAIN ancestry remains visible while fresh response bytes stay sealed.

The compiler fixture is synthetic software conformance, with no native work,
fresh scientific observations or qualification. Original response forms retain
their exact canonical bytes; newly inherited visibility is a distinct form.
"""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.compiler import compile_run_plan
from empirical_lawhood.runtime.plans import OutputTemplate
from tests.runtime_platform.conftest import build_protocol_fixture
from tests.test_matrix_e3_response_records import arguments, case as response_case, publication, qualification  # noqa: F401


def arrays(access=Access.EVALUATION_SEALED, visibility=Visibility.PROSPECTIVE, *, role="RESPONSES"):
    source = ObjectIdentity("literal.source", ScheduledSource.SCHEMA, ScheduledSource.VERSION, "a" * 64)
    return ScheduledResponseArrays("literal.arrays", role, source,
        ArtifactIdentity("literal.archive", "literal-response", MATRIX_ARRAY_SCHEMA, "b" * 64, "application/x-npz", 128),
        (MatrixArrayMember("literal", "<i8", (1,), sha256(b"\0" * 8).hexdigest()),), (source,), access, visibility)


def compiled_sealed_freeze():
    """Use the public compiler with the fixture's real development parents."""
    fixture = build_protocol_fixture()
    freeze = next(step for step in fixture.template.steps if step.step_id == "freeze")
    freeze = replace(freeze, requested_outcome_access=Access.EVALUATION_SEALED,
        visibility_ceiling=Visibility.PROSPECTIVE,
        outputs=(OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ,
            "application/x-npz", ".npz"),))
    template = replace(fixture.template, steps=tuple(freeze if step.step_id == "freeze" else step
        for step in fixture.template.steps))
    registry = replace(fixture.registry, capabilities=tuple(
        replace(capability, maximum_outcome_access=Access.EVALUATION_SEALED, output_schema_ids=(MATRIX_ARRAY_SCHEMA,))
            if capability.capability_key == "reference.freeze" else
        replace(capability, input_schema_ids=(MATRIX_ARRAY_SCHEMA,))
            if capability.capability_key == "reference.evaluate" else capability
        for capability in fixture.registry.capabilities))
    plan = compile_run_plan(run_plan_id="literal.inherited-response", campaign=fixture.campaign, system=fixture.system,
        experiment=fixture.experiment, frozen_proposal=fixture.frozen_proposal, authorization=fixture.authorization,
        template=template, registry=registry, implementation_commit=fixture.run_plan.implementation_commit,
        approval_service=fixture.approval_service)
    return next(step.outputs[0] for step in plan.steps if step.step_id == "freeze")


def test_compiled_sealed_response_retains_exposed_train_ancestry():
    output = compiled_sealed_freeze()
    assert output.outcome_access is Access.EVALUATION_SEALED
    assert output.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
    assert output.parent_visibility_ceilings == (Visibility.DEVELOPMENT_ONLY, Visibility.DEVELOPMENT_ONLY)
    record = arrays(output.outcome_access, output.visibility_ceiling)
    assert decode_canonical_bytes(record.canonical_bytes(), ScheduledResponseArrays, maximum_bytes=None) == record


def test_current_native_response_accepts_sealed_inherited_visibility(response_case):  # noqa: F811
    original = response_case.response
    changed = replace(original, arrays=replace(original.arrays, visibility_ceiling=Visibility.DEVELOPMENT_ONLY))
    assert changed.validate_source(response_case.native_config, **arguments(response_case)) is response_case.source
    assert changed.arrays.outcome_access is Access.EVALUATION_SEALED
    assert original.arrays.visibility_ceiling is Visibility.PROSPECTIVE
    assert changed.canonical_bytes() != original.canonical_bytes()
    assert decode_canonical_bytes(original.canonical_bytes(), type(original), maximum_bytes=None) == original


@pytest.mark.parametrize("access,visibility", (
    (Access.EVALUATION_SEALED, Visibility.PROSPECTIVE),
    (Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY),
))
def test_original_response_forms_keep_exact_canonical_bytes(access, visibility):
    record = arrays(access, visibility)
    assert decode_canonical_bytes(record.canonical_bytes(), ScheduledResponseArrays, maximum_bytes=None).canonical_bytes() == record.canonical_bytes()


@pytest.mark.parametrize("access,visibility", tuple((access, visibility)
    for access in Access for visibility in Visibility if (access, visibility) not in (
        (Access.EVALUATION_SEALED, Visibility.PROSPECTIVE),
        (Access.EVALUATION_SEALED, Visibility.DEVELOPMENT_ONLY),
        (Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY))))
def test_response_information_lanes_cannot_reseal_exposed_or_privileged_bytes(access, visibility):
    with pytest.raises(ValueError, match="information scope"):
        arrays(access, visibility)


def test_original_template_contract_stays_blind():
    original = arrays(Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, role="TEMPLATES")
    assert decode_canonical_bytes(original.canonical_bytes(), ScheduledResponseArrays, maximum_bytes=None) == original
    with pytest.raises(ValueError, match="information scope"):
        replace(original, visibility_ceiling=Visibility.DEVELOPMENT_ONLY)


def test_compiled_physical_forecast_retains_original_exposed_numerical_parameters(response_case):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_records as records
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_science as science
    from tests.test_matrix_e3_response_lifecycle import compiled_response_output
    from tests.test_matrix_e3_response_science import LIMITS, byte_fetch, public_context, store

    output = compiled_response_output(Access.OUTCOME_BLIND)
    assert (output.outcome_access, output.visibility_ceiling) == (Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY)
    case = response_case
    pub = publication(case, case.selection, "visible-original-numerical-container", access=Access.DEVELOPMENT_VISIBLE,
        visibility=Visibility.DEVELOPMENT_ONLY)
    q = qualification(case.selection, pub, "visible-original-numerical-container")
    profile = records.project_protected_e3_response_numerics(case.protocol, provenance=case.selection, publication=pub, qualification=q)
    config = replace(case.physical_config, numerical_profile=records.identity(profile))
    operands = dict(public_context(case), numerical_profile=profile)
    raw, result = science.forecast_physical(config, case.causal, **operands, fetch=byte_fetch(store(case)), **LIMITS,
        artifact_id=case.physical.arrays.array_artifact.artifact_id, forecast_id=case.physical.forecast_id,
        outcome_access=output.outcome_access, visibility_ceiling=output.visibility_ceiling)
    assert raw == case.physical_raw
    assert result.arrays.outcome_access is Access.DEVELOPMENT_VISIBLE
    assert result.arrays.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
    result.validate_public_inputs(config, causal=case.causal, **operands)

    def forbidden(*args, **kwargs):
        raise AssertionError("lowered source classification reached array payloads")

    with pytest.raises(ValueError, match="lowers original numerical provenance"):
        science.forecast_physical(config, case.causal, **operands, fetch=forbidden, **LIMITS,
            artifact_id=case.physical.arrays.array_artifact.artifact_id, forecast_id=case.physical.forecast_id,
            outcome_access=Access.OUTCOME_BLIND, visibility_ceiling=Visibility.PROSPECTIVE)
    lowered = replace(result, arrays=replace(result.arrays, outcome_access=Access.OUTCOME_BLIND, visibility_ceiling=Visibility.PROSPECTIVE))
    with pytest.raises(ValueError, match="lowers original numerical provenance"):
        lowered.validate_public_inputs(config, causal=case.causal, **operands)


def test_current_native_record_still_refuses_visible_development_response(response_case):  # noqa: F811
    visible = replace(response_case.response.arrays, outcome_access=Access.DEVELOPMENT_VISIBLE,
        visibility_ceiling=Visibility.DEVELOPMENT_ONLY)
    with pytest.raises(ValueError, match="complete protected native"):
        replace(response_case.response, arrays=visible)
