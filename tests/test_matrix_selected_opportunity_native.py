# SPDX-License-Identifier: MPL-2.0
"""Original native projections and truthful nonentry; no RNG or native work."""

from dataclasses import fields, replace
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity as programme_owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_future as future
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import preparation_identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import forecast_public
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_native_body import _execute_future_native
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import forecast_selected_point
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import package_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays, decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_selected_native_work import literal_history
from tests.test_matrix_selected_point import feature, literal_unavailable_measurement
from tests.test_matrix_selected_opportunity import opportunity, transfer  # noqa: F401 - shared in-memory fixtures


def test_actual_selected_opportunity_native_future_keeps_original_streams_and_all_nonentry_branches(opportunity, monkeypatch):  # noqa: F811
    programme = programme_owner.public_programme(opportunity)
    # Only an existing test constructor's field interface is adapted. Its output
    # is the actual typed history/native definition; this is no scientific root.
    fixture_fields = SimpleNamespace(sources=SimpleNamespace(source_arms=lambda: tuple((None, source) for source in programme.sources.sources),
        closure=SimpleNamespace(reservation=programme.reservation)))
    source, history, original_work, _, _ = literal_history(fixture_fields, native_version="2.0.0")
    public = next(row for _, row in programme.point_design.sources if row.source == source.identity)
    _, _, prefix, _, _, prefix_raw, _ = literal_unavailable_measurement("E5_OPPORTUNITY")
    prefix = replace(prefix, source=source.identity, preparation=preparation_identity(history.arrays),
        arrays=replace(prefix.arrays, source=source.identity, producers=tuple(sorted((source.identity, preparation_identity(history.arrays),
            prefix.witness, prefix.frame_assessment), key=lambda row: row.object_id))))
    point = forecast_selected_point(programme.point_design, replace(feature(programme.point_design, public), prefix=identity(prefix),
        frame_sha256=None, disposition="UNAVAILABLE", values=()), record_id="point.opportunity.native-control")
    protocol = programme.protocol(source)
    templates, _ = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"), "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"),
        "trace_coefficients": np.zeros((2, 3), dtype="<f8"), "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    _, mechanical = forecast_public(public, protocol, prefix, prefix_raw, templates, artifact_id="mechanical.opportunity.native-control")
    config = future.MatrixSelectedOpportunityFutureConfigV2("config." + future.node_id(source, "responses"), programme.identity, source, protocol,
        dict(programme.panels)[source.root.root.independent_group_id], programme.point_design.identity, package_identity(programme.point_design.package), "responses")
    task = future.node_id(source, "responses")
    parent = replace(history.native.definition.parent_contact, task_id=task,
        execution_task=ObjectIdentity(task, "empirical-lawhood/runtime/execution-task", "1.0.0", "d" * 64))
    context = SimpleNamespace(run_id=parent.run_id, task_id=task, attempt_id=parent.attempt_id, input_materialization_ids=parent.input_materialization_ids)
    obsolete = future.MatrixSelectedOpportunityFutureConfig(**{field.name: getattr(config, field.name) for field in fields(config)})
    with pytest.raises(TypeError, match="current direct-input"):
        future.initial_native_work(context, obsolete, history, prefix, point, mechanical, parent)
    work = future.initial_native_work(context, config, history, prefix, point, mechanical, parent)
    assert original_work.scientific_unit_ids == work.scientific_unit_ids == (source.root.root.independent_group_id,)
    assert len(original_work.definitions[0].streams) == 2
    assert len(work.definitions[0].streams) == 4
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_bindings import native_input_records, validate_native_input_records
    selected = native_input_records(source, panels=config.panels)
    assert set(work.definitions[0].streams) == {pin for name, pin, _ in selected if name.startswith("native-stream.")}
    assert all(value.purpose.startswith("autonomous") for name, _, value in selected if name.startswith("native-stream."))
    received = {name: value for name, _, value in selected}
    validate_native_input_records(config, received)
    missing = dict(received)
    del missing[next(name for name in missing if name.startswith("native-stream."))]
    with pytest.raises(ValueError, match="used RNG"):
        validate_native_input_records(config, missing)
    first = next(name for name in received if name.startswith("native-stream."))
    wrong = {**received, first: replace(received[first], digest_sha256="f" * 64)}
    with pytest.raises(ValueError, match="used RNG"):
        validate_native_input_records(config, wrong)
    assert identity(point) in work.definitions[0].sources and identity(mechanical) in work.definitions[0].sources
    assert work.definitions[0].operation_id == future.NAMESPACE + ".paired-pulse.direct-inputs.v2"
    def forbidden(*args, **kwargs):
        raise AssertionError("truthful opportunity nonentry entered native/RNG work")
    monkeypatch.setattr(np.random, "Generator", forbidden)
    values, _, native, disposition = _execute_future_native(config, history, prefix, mechanical, b"", b"", b"", SimpleNamespace(), work)
    assert native == () and disposition == "UNEVALUABLE"
    assert np.array_equal(values["unentered_branches"], np.arange(48, dtype="<i8"))
    raw, arrays = future.array_product(source, values, artifact_id="future.opportunity.native-control")
    product = future.MatrixSelectedOpportunityFutureHistory("responses.opportunity.native-control", source.identity, preparation_identity(history),
        identity(prefix), identity(point), identity(mechanical), ObjectIdentity.from_record(protocol.protocol_id, protocol), tuple(row.identity for row in config.panels),
        tuple(row[0] for row in branch_census(protocol, config.panels)), arrays, (), disposition)
    future.validate_future_history(config, history, prefix, point, mechanical, product)
    assert decode_canonical_bytes(product.canonical_bytes(), type(product), maximum_bytes=None) == product
    assert len(decode_matrix_arrays(raw, arrays)["unentered_branches"]) == 48
    readout = future.assess_future(config, history, prefix, point, mechanical, product, b"", b"", b"", raw, record_id="readout.opportunity.native-control")
    assert readout.disposition == "UNEVALUABLE" and len(readout.cells) == 240
    assert all(row.normalized_error is None for row in readout.cells)
    with pytest.raises(ValueError, match="selected point"):
        future.validate_future_history(config, history, prefix, replace(point, record_id="point.foreign-opportunity"), mechanical, product)
