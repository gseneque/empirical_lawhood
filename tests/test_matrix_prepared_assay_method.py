# SPDX-License-Identifier: MPL-2.0
"""Small original-protocol metadata projections; no trajectory, issue or fit."""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod, TOLERANCES
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_functional import _validate_matched_future_panels, validate_prepared_functional_selection
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponsePanel
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1FactorRule
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import ScalarClosureSpec
from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorNumericalDesign, MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol, physical_forecast_implementation
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_parameter_history import source as parameter_template


def reference(name, schema, *, version="1.0.0"):
    return ObjectIdentity(name, schema, version, sha256(name.encode()).hexdigest())


def literal_protocol():
    coordinate = parameter_template().coordinate
    coordinate = replace(coordinate, autonomous_ticks=coordinate.autonomous_ticks + 128, observation_ticks=(0, coordinate.total_ticks + 128))
    definition = MatrixParameterScalarDefinition("scalar.literal-assay-method")
    normalization = ArtifactIdentity(definition.definition_id, "literal-method-only", definition.SCHEMA, definition.fingerprint(),
        "application/json", len(definition.canonical_bytes()))
    rule = E1FactorRule("rule.literal-assay-method", ("X", "Y"), tuple(range(7)), D(".001"), 4, 0,
        D(".05"), D(".05"), D(15), D(15), D(30), D("1e-10"), D("1e-20"), D(".5"),
        ScalarClosureSpec("closure.literal-assay-method", normalization, D(".30")))
    policy = original.ScheduledPrefixPolicy("policy.literal-assay-method", 6, rule,
        MatrixParameterFactorNumericalDesign("numerical.literal-assay-method", *(D("1e-9") for _ in range(6))),
        "Y", "FIXED_DECLARED_CUTOFF_CAUSALLY_ADMITTED_PRIMARY_FRAME")
    root = MatrixProgrammeRoot("root.literal-assay-method", "group.literal-assay-method", "regime.literal-assay-method",
        coordinate.coordinate_id, MatrixProgrammeRole.DEVELOPMENT, coordinate.clock_id)
    public = ScheduledPublicSource(reference("source.literal-assay-method", original.ScheduledSource.SCHEMA,
        version=original.ScheduledSource.VERSION), root, coordinate, policy,
        reference("allocation.literal-assay-method", original.ScheduledAllocation.SCHEMA),
        reference("reservation.literal-assay-method", original.ScheduledReservation.SCHEMA))
    arrays = {"generic_basis": np.zeros((3, 4, 4), dtype="<c16"), "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"),
        "trace_coefficients": np.zeros((2, 3), dtype="<f8"), "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")}
    raw, members = encode_matrix_arrays(arrays)
    templates = ScheduledResponseArrays("templates.literal-assay-method", "TEMPLATES", public.source,
        ArtifactIdentity("array.literal-assay-method", "literal-metadata-only", MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), "application/x-npz", len(raw)),
        members, (public.source,), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    protocol = ScheduledResponseProtocol("protocol.literal-assay-method", public, reference("criterion.literal-assay-method", "empirical-lawhood/testing/method-criterion"),
        MatrixFactorResponseModel("model.literal-assay-method", physical_forecast_implementation()),
        tuple(MatrixFactorAction("action.literal-assay-method." + role.lower(), role, D(".01"), 1, D(1)) for role in ACTION_ROLES),
        (16, 64, 128), 48, templates, D("1e-5"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-8"), D("1e-8"),
        D("1e-5"), D("1e-12"), D("1e-10"), "PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME")
    return protocol, len(raw)


def test_shared_assay_projects_all_original_physical_fields_and_separate_source_identity():
    protocol, size = literal_protocol()
    assert size < 2048
    method = MatrixPreparedAssayMethod.from_protocol("method.literal-fixed-assay", protocol)
    method.validate_protocol(protocol)
    assert decode_canonical_bytes(method.canonical_bytes(), MatrixPreparedAssayMethod, maximum_bytes=None) == method
    # Explicit census: adding a physical field to the original protocol must
    # update this projection instead of silently becoming a matching exception.
    assert {row.name for row in fields(protocol)} == {"protocol_id", "public_source", "criterion", "mechanical_model", "actions", "horizon_steps",
        "receiver_count", "templates", "origin_rule", *TOLERANCES}
    for name in ("criterion", "mechanical_model", "actions", "horizon_steps", "receiver_count", "origin_rule", *TOLERANCES):
        assert getattr(method, name) == getattr(protocol, name)
    assert (method.template_artifact, method.template_members) == (protocol.templates.array_artifact, protocol.templates.members)
    public = replace(protocol.public_source, source=replace(protocol.public_source.source, object_id="source.literal-assay-method.other"),
        root=replace(protocol.public_source.root, root_id="root.literal-assay-method.other"))
    other = replace(protocol, protocol_id="protocol.literal-assay-method.other", public_source=public,
        templates=replace(protocol.templates, operand_id="templates.literal-assay-method.other", source=public.source, producers=(public.source,)))
    assert ObjectIdentity.from_record(other.protocol_id, other) != ObjectIdentity.from_record(protocol.protocol_id, protocol)
    assert MatrixPreparedAssayMethod.from_protocol(method.record_id, other) == method


@pytest.mark.parametrize("damage", ("tolerance", "template-sha", "force", "criterion"))
def test_shared_assay_refuses_changed_physical_contract(damage):
    protocol, _ = literal_protocol()
    method = MatrixPreparedAssayMethod.from_protocol("method.literal-fixed-assay", protocol)
    if damage == "tolerance":
        changed = replace(protocol, weak_response_minimum=protocol.weak_response_minimum * 2)
    elif damage == "template-sha":
        changed = replace(protocol, templates=replace(protocol.templates,
            array_artifact=replace(protocol.templates.array_artifact, sha256="f" * 64)))
    elif damage == "force":
        changed = replace(protocol, actions=tuple(replace(row, force_norm=row.force_norm * 2) for row in protocol.actions))
    else:
        changed = replace(protocol, criterion=replace(protocol.criterion, object_fingerprint="f" * 64))
    with pytest.raises(ValueError, match="frozen complete"):
        method.validate_protocol(changed)


def panel_pair(group, label="literal"):
    return tuple(MatrixPreparedResponsePanel("panel." + group + "." + str(at), group, role,
        tuple(MatrixHistorySeed(purpose, sha256((label + group + role + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
        for at, role in enumerate(("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")))


def test_functional_matched_consumer_preserves_both_future_panels_and_actual_group_purposes():
    panels = panel_pair("group.literal-matched-future")
    _validate_matched_future_panels(((panels[0].independent_group_id, panels),) * 3)
    for at in (0, 1):
        changed = list(panels)
        changed[at] = panel_pair("group.literal-matched-future", "changed")[at]
        with pytest.raises(ValueError, match="across arms"):
            _validate_matched_future_panels(((panels[0].independent_group_id, panels), (panels[0].independent_group_id, tuple(changed))))
    with pytest.raises(ValueError, match="whole-group"):
        _validate_matched_future_panels((("group.wrong-original-future", panels),))


def test_new_method_and_functional_owner_refuse_wrong_record_types():
    with pytest.raises(TypeError, match="exact original"):
        MatrixPreparedAssayMethod.from_protocol("method.wrong-owner", object())
    with pytest.raises(TypeError, match="own exact"):
        validate_prepared_functional_selection(object(), object(), object(), object(), assay_method=object())
