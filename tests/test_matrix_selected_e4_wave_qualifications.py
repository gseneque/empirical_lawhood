# SPDX-License-Identifier: MPL-2.0
"""Actual two-wave root semantics, exact source access and complete refusals."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition import _local_root
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401


@pytest.fixture(scope="module")
def two_wave_access(selected_e4_populations):  # noqa: F811
    programme, bank = selected_e4_populations.calibration, selected_e4_populations.calibration_bank
    index=bank.source_index()
    original, context = _fixture()
    views = {value.view_id: value for value in original.system.numerical_views}
    clocks = {value.clock_id: value for value in original.system.clocks}
    for descriptor in bank.sources:
        coordinate = bank.source(descriptor.root_id,index=index).coordinate
        clocks.setdefault(coordinate.clock_id, replace(original.system.clocks[0], clock_id=coordinate.clock_id))
        for view in (coordinate.primary_view, coordinate.fine_view):
            views[view.view_id] = replace(original.system.numerical_views[0], view_id=view.view_id)
    root = replace(original, system=replace(original.system,
        clocks=tuple(clocks[key] for key in sorted(clocks)), numerical_views=tuple(views[key] for key in sorted(views))))
    pin = ObjectIdentity("declaration.disclosed-two-wave", native.SelectedE4NativeProgrammeDeclaration.SCHEMA,
        native.SelectedE4NativeProgrammeDeclaration.VERSION, "a" * 64)
    roots = []
    for wave in programme.waves[:2]:
        selected_views = tuple(sorted({view.view_id for root_id in wave.root_ids
            for view in (bank.source(root_id,index=index).coordinate.primary_view,bank.source(root_id,index=index).coordinate.fine_view)}))
        roots.append(_local_root(native.SelectedE4WaveScope(pin, programme, wave, root), selected_views))
    external = RecursiveExternalInput("source.shared-canonical-metadata", "shared-canonical-metadata",
        ObjectIdentity.SCHEMA, "application/json", 256, context.qualifications[0].outcome_access,
        original.design_inputs[0].visibility_ceiling, "b" * 64)
    materialization = ObjectIdentity(external.logical_artifact_id, external.payload_schema, "1.0.0", external.expected_content_sha256)
    operator = context.qualifications[0].observation_operator
    receipts = tuple(replace(context.qualifications[0], receipt_id="qualification.actual-wave." + str(index),
        source_id=external.input_id, materialization=materialization, content_sha256=external.expected_content_sha256,
        evidence_world_id=local.system.world.world_id, observation_operator=operator,
        numerical_view_ids=tuple(value.view_id for value in local.system.numerical_views),
        native_unit_ids=tuple(sorted({value.native_unit for value in local.system.quantities})),
        frame_ids=tuple(sorted({value.coordinate_frame for value in local.system.quantities})),
        clock_ids=tuple(value.clock_id for value in local.system.clocks), receiver_semantics_id=local.system.relation.relation_id,
        validity_contract_id=local.experiment.obligations.validity.validity_id,
        uncertainty_contract_id=local.experiment.obligations.uncertainty.uncertainty_id,
        outcome_access=external.outcome_access, visibility_ceiling=external.visibility_ceiling)
        for index, local in enumerate(roots))
    return tuple(roots), external, receipts, operator


def choose(root, external, available, operator):
    return owner.select_component_qualifications(SimpleNamespace(prospective_draft=root, external_inputs=(external,)),
        available, {external.logical_artifact_id: "1.0.0"}, operator)


def test_two_actual_wave_roots_select_distinct_ordinary_access_without_relabeling(two_wave_access):
    roots, external, receipts, operator = two_wave_access
    assert roots[0].experiment.obligations.validity.validity_id != roots[1].experiment.obligations.validity.validity_id
    assert roots[0].experiment.obligations.uncertainty.uncertainty_id != roots[1].experiment.obligations.uncertainty.uncertainty_id
    assert choose(roots[0], external, receipts, operator) == (receipts[0],)
    assert choose(roots[1], external, receipts, operator) == (receipts[1],)
    assert receipts[0].materialization == receipts[1].materialization
    assert receipts[0].validity_contract_id != receipts[1].validity_contract_id


@pytest.mark.parametrize("change", ("dropped", "swapped", "ambiguous", "source", "payload", "clock", "view", "operator", "uncertainty", "outcome"))
def test_local_wave_refuses_missing_ambiguous_or_wrong_semantic_source_variant(two_wave_access, change):
    roots, external, receipts, operator = two_wave_access
    available = receipts
    if change in ("dropped", "swapped"):
        available = (receipts[1],)
    elif change == "ambiguous":
        available = (*receipts, replace(receipts[0], receipt_id="qualification.duplicate-scope"))
    else:
        fields = {"source": {"source_id": "another-source"},
            "payload": {"materialization": replace(receipts[0].materialization, object_fingerprint="f" * 64)},
            "clock": {"clock_ids": ("another-clock",)}, "view": {"numerical_view_ids": ("another-view",)},
            "operator": {"observation_operator": replace(operator, object_fingerprint="f" * 64)},
            "uncertainty": {"uncertainty_contract_id": receipts[1].uncertainty_contract_id},
            "outcome": {"outcome_access": receipts[0].outcome_access.DEVELOPMENT_VISIBLE}}
        available = (replace(receipts[0], **fields[change]), receipts[1])
    with pytest.raises(ValueError, match="exactly one current local-scope"):
        choose(roots[0], external, available, operator)
