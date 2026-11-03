# SPDX-License-Identifier: MPL-2.0
"""Independent precontact root checks; synthetic fixtures confer no authority."""

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.rc_prerequisite_chain.operation_bindings import (
    operation_manifests, operation_registrations, output_codecs,
)
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import default_chain_config
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import prospective_fixture
from tests.runtime_platform.test_recursive_prospective_workflow import _registrations


def _compile_prospective(compilation, registrations):
    return compile_recursive_wave(
        draft=compilation.draft, registrations=registrations, registry=compilation.registry,
        implementation_commit="a" * 40,
        qualifications=compilation.candidate_context.qualifications,
        known_design_inputs=compilation.candidate_context.known_design_inputs,
        output_codecs=compilation.output_codecs,
    )


@pytest.mark.parametrize("unit_scope", ["evaluation", "development", "unassigned"])
def test_prospective_unit_projection_cannot_infer_an_eligible_stage_from_roster_labels(unit_scope):
    compilation, _, _ = prospective_fixture(typed_outputs=True)
    root = compilation.candidate_draft
    if unit_scope == "evaluation":
        units = root.evaluation_unit_ids
    elif unit_scope == "development":
        units = ("exposed.development.unit",)
        compilation = replace(compilation, draft=replace(compilation.draft,
            prospective_draft=replace(root, development_unit_ids=units)))
    else:
        units = ("outside.actual.study",)
    assert units
    registrations = tuple(replace(registration, scientific_unit_ids=lambda record: units)
                          if registration.adjudication_output_id is not None else registration
                          for registration in _registrations(compilation))
    with pytest.raises(ValueError, match="prospective unit-bound operation requires.*stage/source unit validator"):
        _compile_prospective(compilation, registrations)


def test_prospective_native_registration_remains_unavailable_with_matching_root_unit_labels():
    compilation, _, _ = prospective_fixture(typed_outputs=True)
    units = compilation.candidate_draft.evaluation_unit_ids
    assert units
    registrations = tuple(replace(registration, native_effect=True,
                          scientific_unit_ids=lambda record: units,
                          native_effect_slot_ids=lambda record: ("native.synthetic.frozen-slot",))
                          if registration.adjudication_output_id is not None else registration
                          for registration in _registrations(compilation))
    selected = {registration.selection.selection_id for registration in registrations if registration.native_effect}
    compilation = replace(compilation, draft=replace(compilation.draft,
        operations=tuple(replace(operation, maximum_attempts=1)
                         if operation.selection.selection_id in selected else operation
                         for operation in compilation.draft.operations)))
    with pytest.raises(ValueError, match="prospective native operation requires.*stage/source unit validator"):
        _compile_prospective(compilation, registrations)


def test_explicit_unitless_context_registration_preserves_existing_candidate_authority_boundary():
    compilation, _, _ = prospective_fixture(typed_outputs=True)
    registrations = tuple(replace(registration, scientific_unit_ids=lambda record: ())
                          for registration in _registrations(compilation))
    result = _compile_prospective(compilation, registrations)
    assert result.candidate_report.candidate is not None
    assert result.run_plan is None and result.execution_plan is None
    assert result.candidate_draft.evaluation_unit_ids == compilation.candidate_draft.evaluation_unit_ids


def test_full_rc_summary_cannot_extend_an_early_slice_unit_census():
    config = default_chain_config()
    early = rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,), include_summary=False)
    complete = rc_recursive_draft(config)
    summary = next(operation for operation in complete.operations if operation.node_id == "rc.summary")
    summary_link = next(link for link in complete.links if link.consumer_node_id == "rc.summary")
    altered = replace(early,
        operations=tuple(sorted((*early.operations, summary), key=lambda value: value.node_id)),
        selected_operation_ids=tuple(sorted((*early.selected_operation_ids, summary.node_id))),
        links=tuple(sorted((*early.links, summary_link), key=lambda value: value.edge_id)))
    with pytest.raises(ValueError, match="operation scientific units differ from the selected study root"):
        compile_recursive_wave(draft=altered, registrations=operation_registrations(),
            registry=CapabilityRegistry("independent.rc.root-check",
                tuple(sorted(operation_manifests(), key=lambda value: value.registry_id))),
            implementation_commit="a" * 40, output_codecs=output_codecs())


def _native_prospective_fixture(validator, *, wrong_unit=False):
    """Register synthetic phase semantics without executing a native worker."""
    compilation, _, _ = prospective_fixture(typed_outputs=True)
    unit_ids = (("outside.actual.study",) if wrong_unit
                else compilation.candidate_draft.evaluation_unit_ids)
    registrations = tuple(replace(registration, native_effect=True,
                          scientific_unit_ids=lambda record: unit_ids,
                          native_effect_slot_ids=lambda record: ("native.synthetic.frozen-slot",),
                          complete_unit_census=True, scientific_root_validator=validator)
                          if registration.adjudication_output_id is not None else registration
                          for registration in _registrations(compilation))
    selected = {registration.selection.selection_id for registration in registrations if registration.native_effect}
    compilation = replace(compilation, draft=replace(compilation.draft,
        operations=tuple(replace(operation, maximum_attempts=1)
                         if operation.selection.selection_id in selected else operation
                         for operation in compilation.draft.operations)))
    return compilation, registrations


def test_installed_prospective_validator_receives_actual_frozen_root_source_and_unit_census():
    seen = []

    def validate(config, context):
        # This synthetic source/phase policy is code-owned. Its successful
        # validation permits candidate compilation; it grants no authority.
        assert config.scalar == 3
        assert context.unit_ids == context.root.evaluation_unit_ids
        assert context.selected_unit_ids == context.root.evaluation_unit_ids
        assert context.complete_unit_census is True
        assert context.qualifications
        assert context.known_design_inputs
        source = context.root.source_materializations[0]
        assert any(qualification.materialization == source.materialization
                   and qualification.content_sha256 == source.content_sha256
                   for qualification in context.qualifications)
        seen.append(context)

    compilation, registrations = _native_prospective_fixture(validate)
    result = _compile_prospective(compilation, registrations)
    assert len(seen) == 1
    assert seen[0].root == compilation.draft.prospective_draft
    assert seen[0].qualifications == compilation.candidate_context.qualifications
    assert seen[0].known_design_inputs == compilation.candidate_context.known_design_inputs
    assert result.candidate_report.candidate is not None
    assert result.run_plan is None and result.execution_plan is None


def test_installed_prospective_validator_can_refuse_units_without_worker_or_authority():
    def validate(config, context):
        if context.unit_ids != context.root.evaluation_unit_ids:
            raise ValueError("FROZEN_SYNTHETIC_SOURCE_UNIT_MISMATCH")

    compilation, registrations = _native_prospective_fixture(validate, wrong_unit=True)
    with pytest.raises(ValueError, match="FROZEN_SYNTHETIC_SOURCE_UNIT_MISMATCH"):
        _compile_prospective(compilation, registrations)


def test_negative_validator_return_cannot_be_ignored_as_success():
    compilation, registrations = _native_prospective_fixture(lambda config, context: False)
    with pytest.raises(ValueError, match="validator.*None|validator.*success|validator.*negative"):
        _compile_prospective(compilation, registrations)
