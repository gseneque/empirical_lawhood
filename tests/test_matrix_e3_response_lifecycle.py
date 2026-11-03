# SPDX-License-Identifier: MPL-2.0
"""Literal response lifecycle controls; no native acquisition or qualification."""

from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import ProtectedE3ResponseNumericalProfile
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.compiler import compile_run_plan
from empirical_lawhood.runtime.plans import OutputTemplate
from tests.runtime_platform.conftest import build_protocol_fixture


def compiled_response_output(declared_access):
    """Compile a profile-schema parent and an array prediction using real lanes.

    The synthetic fixture's original profile-schema parent is explicitly
    development visible. This tests shared compiler propagation, without
    asserting that synthetic metadata is a qualified numerical profile.
    """
    fixture = build_protocol_fixture()
    steps = []
    for step in fixture.template.steps:
        if step.step_id == "develop-a":
            step = replace(step, outputs=(OutputTemplate("numerical-profile", ProtectedE3ResponseNumericalProfile.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),))
        elif step.step_id == "freeze":
            step = replace(step, dependency_step_ids=("develop-a",), requested_outcome_access=declared_access,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outputs=(OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ,
                    "application/x-npz", ".npz"),))
        steps.append(step)
    capabilities = []
    for capability in fixture.registry.capabilities:
        if capability.capability_key == "reference.develop-a":
            capability = replace(capability, output_schema_ids=(ProtectedE3ResponseNumericalProfile.SCHEMA,))
        elif capability.capability_key == "reference.freeze":
            capability = replace(capability, maximum_outcome_access=declared_access,
                input_schema_ids=(ProtectedE3ResponseNumericalProfile.SCHEMA,), output_schema_ids=(MATRIX_ARRAY_SCHEMA,))
        elif capability.capability_key == "reference.evaluate":
            capability = replace(capability, input_schema_ids=(MATRIX_ARRAY_SCHEMA,))
        capabilities.append(capability)
    plan = compile_run_plan(run_plan_id="literal.profile-response-lane", campaign=fixture.campaign, system=fixture.system,
        experiment=fixture.experiment, frozen_proposal=fixture.frozen_proposal, authorization=fixture.authorization,
        template=replace(fixture.template, steps=tuple(steps)), registry=replace(fixture.registry, capabilities=tuple(capabilities)),
        implementation_commit=fixture.run_plan.implementation_commit, approval_service=fixture.approval_service)
    parent = next(step.outputs[0] for step in plan.steps if step.step_id == "develop-a")
    assert parent.payload_schema == ProtectedE3ResponseNumericalProfile.SCHEMA
    assert parent.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert parent.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    return next(step.outputs[0] for step in plan.steps if step.step_id == "freeze")


def test_actual_profile_parent_makes_physical_prediction_development_visible():
    output = compiled_response_output(OutcomeAccess.OUTCOME_BLIND)
    assert output.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert output.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert output.parent_visibility_ceilings == (VisibilityCeiling.DEVELOPMENT_ONLY,)


def test_actual_profile_parent_keeps_new_response_bytes_sealed_with_development_visibility():
    output = compiled_response_output(OutcomeAccess.EVALUATION_SEALED)
    assert output.outcome_access is OutcomeAccess.EVALUATION_SEALED
    assert output.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert output.parent_visibility_ceilings == (VisibilityCeiling.DEVELOPMENT_ONLY,)
