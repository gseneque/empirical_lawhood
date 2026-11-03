# SPDX-License-Identifier: MPL-2.0
"""Prepared future transport, cold-assessment and refusal controls; no native entry."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace
import pickle

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_future_custody as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationHistory, MatrixPreparationSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import MatrixPreparedMechanicalForecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPointSeal
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponsePanel
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_prepared_response_method import case  # noqa: F401 - supplied-innovation fixture


def reference(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


def marker():
    raw, members = encode_matrix_arrays({"unentered_branches": np.arange(48, dtype="<i8")})
    artifact = ArtifactIdentity("array.literal-future-unentered", "literal-transport-only", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    return raw, method.MatrixPreparedFutureArrays("arrays.literal-future-unentered", reference("source.literal-future", MatrixPreparationSource), artifact, members)


def test_prepared_future_known_nonentry_marker_retains_exact_all48_and_received_bytes():
    raw, operand = marker()
    assert len(raw) < 1024
    assert np.array_equal(decode_matrix_arrays(raw, operand)["unentered_branches"], np.arange(48))
    with pytest.raises(ValueError):
        decode_matrix_arrays(raw[:-1], operand)
    with pytest.raises(ValueError):
        decode_matrix_arrays(raw, replace(operand, array_artifact=replace(operand.array_artifact, sha256="f" * 64)))


def test_retained_future_reuses_original_archive_without_recompression_and_refuses_changed_values(monkeypatch):
    raw, operand = marker()
    arrays = decode_matrix_arrays(raw, operand)
    source = SimpleNamespace(identity=operand.source)
    monkeypatch.setattr(np, "savez_compressed", lambda *args, **kwargs:
        pytest.fail("retained native transport was needlessly recompressed"))
    retained, current = method.array_product(source, arrays, artifact_id="array.retained-direct-control", raw=raw)
    assert retained is raw and current.members == operand.members
    assert current.array_artifact.sha256 == operand.array_artifact.sha256
    changed = {"unentered_branches": np.arange(48, dtype="<i8") + 1}
    with pytest.raises(ValueError):
        method.array_product(source, changed, artifact_id="array.changed-direct-control", raw=raw)
    with pytest.raises(ValueError):
        method.array_product(source, arrays, artifact_id="array.corrupt-direct-control", raw=raw[:-1])


@pytest.mark.parametrize("recovered", (False, True))
def test_native_future_closes_verified_output_once_and_keeps_raw_parity(case, monkeypatch, recovered):  # noqa: F811
    """Disclosed store and supplied innovations; no acquired RNG or real contact."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_native_body as native
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_response_science
    from empirical_lawhood.infrastructure import matrix_array_io
    from tests.test_matrix_native_real_progress import DisclosedStore

    source, initial, preparation, preparation_raw, protocol, panels, forecast, frozen_raw, _ = case
    arrays = prepared_response_science.propagate_prepared_responses(*case)
    expected_raw, expected_members = encode_matrix_arrays(arrays)
    config = SimpleNamespace(source=source, protocol=protocol, panels=panels)
    streams = tuple(sorted((method.stream_id(config, panel, stream) for panel in panels for stream in panel.streams),
        key=lambda row: row.object_id))
    work = SimpleNamespace(definitions=(SimpleNamespace(streams=streams),), rosters=(object(),))
    store = DisclosedStore(expected_raw if recovered else None)
    monkeypatch.setattr(native, "MatrixParameterNativeHistory", lambda *_: object())
    monkeypatch.setattr(method, "acquire_future", lambda *args, **kwargs: pytest.fail("recovery acquired a future") if recovered else arrays)
    calls = []
    decode = matrix_array_io.decode_native_matrix_arrays
    def observed(*args, **kwargs):
        calls.append("decode")
        return decode(*args, **kwargs)
    monkeypatch.setattr(matrix_array_io, "decode_native_matrix_arrays", observed)
    artifact_id = "array.native-output.single-closeout"
    result = native._execute_future_native(config, SimpleNamespace(arrays=preparation),
        SimpleNamespace(disposition="AVAILABLE"), SimpleNamespace(disposition="AVAILABLE", arrays=forecast),
        initial, preparation_raw, frozen_raw, store, work, array_artifact_id=artifact_id)
    assert calls == ["decode"]
    raw, operand = native._close_future_arrays(result, source, artifact_id=artifact_id)
    assert calls == ["decode"] and raw == expected_raw and operand.members == expected_members
    assert store.entered == (0 if recovered else 1)
    assert result.disposition == "COMPLETED"
    with pytest.raises(ValueError, match="invocation-bound"):
        native._close_future_arrays(result, SimpleNamespace(identity=reference("foreign-source", MatrixPreparationSource)), artifact_id=artifact_id)
    with pytest.raises(ValueError, match="invocation-bound"):
        native._close_future_arrays(result, source, artifact_id=artifact_id + ".foreign")
    with pytest.raises(TypeError, match="current invocation"):
        pickle.dumps(result)
    damaged = replace(result, raw=raw[:-1])
    with pytest.raises(ValueError, match="invocation-bound"):
        native._close_future_arrays(damaged, source, artifact_id=artifact_id)


def test_member_metadata_retains_noncontiguous_values_and_explicit_missingness_without_archive(monkeypatch):
    from empirical_lawhood.infrastructure.matrix_array_io import matrix_array_members
    values = {"slice": np.arange(12, dtype="<f8").reshape(3, 4)[:, ::2],
        "missing": np.asarray([np.nan], dtype="<f8")}
    raw, expected = encode_matrix_arrays(values, nonfinite_members=("missing",))
    assert raw and not values["slice"].flags.c_contiguous
    monkeypatch.setattr(np, "savez_compressed", lambda *args, **kwargs:
        pytest.fail("member metadata created a transport archive"))
    assert matrix_array_members(values, nonfinite_members=("missing",)) == expected
    with pytest.raises(ValueError):
        matrix_array_members(values)
    with pytest.raises(ValueError):
        matrix_array_members({"objects": np.asarray([object()], dtype=object)})


@pytest.mark.parametrize("damage", ("oversize", "missing-members", "infinite-marker"))
def test_prepared_future_refuses_unbounded_or_incomplete_transport(damage):
    _, operand = marker()
    with pytest.raises(ValueError, match="bounded complete finite"):
        if damage == "oversize":
            replace(operand, array_artifact=replace(operand.array_artifact, size_bytes=MAXIMUM_MATRIX_ARRAY_BYTES + 1))
        elif damage == "missing-members":
            replace(operand, members=())
        else:
            replace(operand, members=(replace(operand.members[0], finite_required=False),))


def test_prepared_future_cannot_promote_known_nonentry_to_completed_native_custody():
    _, operand = marker()
    product = method.MatrixPreparedFutureHistory("history.literal-future-unentered", operand.source,
        reference("history.literal-preparation", MatrixPreparationHistory), reference("causal.literal-preparation", MatrixPreparedCausalPrefix),
        reference("point.literal-preparation", MatrixPreparedPointSeal), reference("mechanical.literal-preparation", MatrixPreparedMechanicalForecast),
        reference("protocol.literal-preparation", ScheduledResponseProtocol),
        tuple(reference("panel.literal." + str(at), MatrixPreparedResponsePanel) for at in range(2)),
        tuple("branch.literal." + str(at).zfill(2) for at in range(48)), operand, (), "NO_ORIGIN")
    with pytest.raises(ValueError, match="denominators"):
        replace(product, disposition="COMPLETED")
    with pytest.raises(ValueError, match="denominators"):
        replace(product, branch_ids=product.branch_ids[:-1])


def test_missing_full_assay_inputs_report_dependencies_without_science_or_authority(monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_assay_experiment as public
    from empirical_lawhood.planning.campaigns import CampaignSpec
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    specification = public.MatrixPreparedAssaySpecification("experiment.literal-missing-assay",
        reference("programme.literal-missing-assay", public.MatrixPreparedAssayProgramme),
        reference("campaign.literal-missing-assay", CampaignSpec), 16, 48)

    def forbidden(*args, **kwargs):
        raise AssertionError("missing-input preparation entered native work or science")

    monkeypatch.setattr(method, "acquire_future", forbidden)
    monkeypatch.setattr(method, "assess_future", forbidden)
    monkeypatch.setattr(public, "lower_prepared_assay", forbidden)
    prepared = public.prepare_assay_experiment(specification, scientific_inputs={}, execution=ExecutionSelection())
    assert not prepared.executable and prepared.draft is None
    assert {row.source_key for row in prepared.dependencies if row.code.endswith(".missing")} == {"programme", "campaign"}
    assert prepared.census.native_effect_count == 96 and dict(prepared.census.operation_counts)["responses"] == 48
    assert dict(prepared.census.output_counts) == {"array-products": 240, "canonical-products": 433}
    with pytest.raises(ValueError, match="scope"):
        replace(specification, scope="PROTECTED_CONFIRMATION_BY_LABEL")


def test_revision_future_closes_actual_record_without_shifting_package_into_protocol(monkeypatch):
    """Only post-handoff record closeout: disclosed pins, no issue or native work."""
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_future as revision
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_native_body
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionSelectedPackage
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4RevisionPoint
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.artifacts import ArtifactProfile

    raw, marker_operand = marker()
    # These metadata-only seams isolate the real post-native call and schema;
    # they supply no source, handoff, execution or scientific acceptance.
    def metadata(name, kind, **extra):
        pin = reference(name, kind)
        return SimpleNamespace(record_id=name, SCHEMA=kind.SCHEMA, VERSION=kind.VERSION,
            fingerprint=lambda: pin.object_fingerprint, **extra)
    source = SimpleNamespace(source_id=marker_operand.source.object_id, identity=marker_operand.source)
    history = metadata("history.literal-revision-closeout", MatrixPreparationHistory,
        history_id="history.literal-revision-closeout", validate_source=lambda *_: None)
    causal = metadata("causal.literal-revision-closeout", MatrixPreparedCausalPrefix, disposition="NO_ORIGIN")
    point = metadata("point.literal-revision-closeout", SelectedE4RevisionPoint)
    mechanical = metadata("mechanical.literal-revision-closeout", MatrixPreparedMechanicalForecast, disposition="NO_ORIGIN")
    protocol = metadata("protocol.literal-revision-closeout", ScheduledResponseProtocol,
        protocol_id="protocol.literal-revision-closeout")
    panels = tuple(SimpleNamespace(identity=reference("panel.literal-revision." + str(at), MatrixPreparedResponsePanel)) for at in range(2))
    branches = tuple(("branch.literal-revision." + str(at).zfill(2),) for at in range(48))
    config = SimpleNamespace(source=source, protocol=protocol, panels=panels,
        selected_package=SimpleNamespace(identity=reference("package.literal-revision-closeout", MatrixRevisionSelectedPackage)))
    context = SimpleNamespace(output_ports=(SimpleNamespace(profile=ArtifactProfile.MATRIX_ARRAY_NPZ,
        logical_artifact_id=marker_operand.array_artifact.artifact_id),))
    work = object()
    monkeypatch.setattr(revision, "initial_native_work", lambda *_: work)
    monkeypatch.setattr(revision, "check_handoff", lambda *_: None)
    monkeypatch.setattr(revision, "branch_census", lambda *_: branches)
    calls = []
    def supplied_nonentry(*args, **kwargs):
        assert args[-1] is work
        assert kwargs == {"array_artifact_id": marker_operand.array_artifact.artifact_id}
        calls.append("supplied-known-nonentry")
        return {"unentered_branches": np.arange(48, dtype="<i8")}, raw, (), "NO_ORIGIN"
    monkeypatch.setattr(prepared_native_body, "_execute_future_native", supplied_nonentry)
    retained, product = revision.execute_native_future(context, config, history, causal, point, mechanical,
        b"", b"", b"", SimpleNamespace(parent_contact=object()), allocation=object())
    assert calls == ["supplied-known-nonentry"] and retained == raw
    assert product.protocol == ObjectIdentity.from_record(protocol.protocol_id, protocol)
    assert product.panels == tuple(row.identity for row in panels)
    assert product.branch_ids == tuple(row[0] for row in branches)
    assert product.native == () and product.disposition == "NO_ORIGIN" and product.standing == revision.STANDING
    payload = product.canonical_bytes()
    assert decode_canonical_bytes(payload, revision.MatrixRevisionFutureHistory, maximum_bytes=len(payload)) == product
    with pytest.raises(ValueError, match="selected seals"):
        replace(product, protocol=config.selected_package.identity)



@pytest.mark.parametrize("precision", (28, 80))
def test_prepared_future_cold_science_reuses_exact_frozen_input_and_preserves_adverse_cells(case, monkeypatch, precision):  # noqa: F811
    """Real supplied-innovation equations; only native receipt admission is a seam."""
    from decimal import localcontext
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_response_science as science
    from empirical_lawhood.infrastructure import matrix_array_io
    source, initial, preparation, preparation_raw, protocol, panels, forecast, frozen_raw, _ = case
    actual = science.propagate_prepared_responses(*case)
    damaged = {name: value.copy() for name, value in actual.items()}
    key = next(name for name in damaged if name.startswith("branch.fine.") and name.endswith(".momenta"))
    damaged[key][1, 0, 0, 0, 0] += .01
    config = SimpleNamespace(source=source, protocol=protocol, panels=panels)
    history, mechanical = SimpleNamespace(arrays=preparation), SimpleNamespace(arrays=forecast)
    # This test has no native completion receipt; it does not claim custody acceptance.
    monkeypatch.setattr(method, "validate_future_history", lambda *_: None)
    products = []
    for arrays in (actual, damaged):
        raw, operand = method.array_product(source, arrays, artifact_id="array.literal-prepared-future-reuse")
        products.append((SimpleNamespace(disposition="COMPLETED", arrays=operand), raw))
    args = (config, history, object(), object(), mechanical)
    with localcontext() as context:
        context.prec = precision
        expected = tuple(method.assess_future(*args, product, initial, preparation_raw, frozen_raw, raw,
            record_id="readout.literal-prepared-future-reuse") for product, raw in products)
        calls, decode = [], matrix_array_io._decode_matrix_arrays

        def observed(raw, operand):
            if raw is frozen_raw:
                calls.append(operand)
            return decode(raw, operand)

        monkeypatch.setattr(matrix_array_io, "_decode_matrix_arrays", observed)
        selected = matrix_array_io.DecodedMatrixArrayInput(frozen_raw, forecast)
        original = science.decode_matrix_arrays

        def no_repeat(raw, operand):
            if raw is frozen_raw:
                pytest.fail("prepared future cold assessment expanded the frozen operand again")
            return original(raw, operand)

        monkeypatch.setattr(science, "decode_matrix_arrays", no_repeat)
        monkeypatch.setattr(science, "native_scheduled_branch", lambda *_args, **_kwargs:
            pytest.fail("cold score entered a native producer"))
        actual_readouts = tuple(method.assess_future(*args, product, initial, preparation_raw, frozen_raw, raw,
            record_id="readout.literal-prepared-future-reuse", frozen_input=selected) for product, raw in products)
    assert calls == [forecast] and actual_readouts == expected
    assert tuple(row.canonical_bytes() for row in actual_readouts) == tuple(row.canonical_bytes() for row in expected)
    assert actual_readouts[0].numerical_pass and not actual_readouts[1].numerical_pass
    assert all(len(row.controls) == 48 and len(row.cells) == 240 and len(row.cumulative_log_errors) == 15 for row in actual_readouts)
    assert actual_readouts[1].cumulative_log_errors == (None,) * 15
    copied = bytes(bytearray(frozen_raw))
    with pytest.raises(ValueError, match="exact original operand"):
        method.assess_future(*args, products[0][0], initial, preparation_raw, copied, products[0][1],
            record_id="readout.forbidden-copied-frozen", frozen_input=selected)
    with pytest.raises(ValueError):
        method.assess_future(*args, products[0][0], initial, preparation_raw, frozen_raw, products[0][1][:-1],
            record_id="readout.forbidden-truncated-future", frozen_input=selected)


def test_prepared_future_nonentry_keeps_all48_and_validation_precedes_decoding(case, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_response_science as science
    source, initial, preparation, preparation_raw, protocol, panels, forecast, frozen_raw, _ = case
    config = SimpleNamespace(source=source, protocol=protocol, panels=panels)
    history, mechanical = SimpleNamespace(arrays=preparation), SimpleNamespace(arrays=forecast)
    raw, operand = method.array_product(source, {"unentered_branches": np.arange(48, dtype="<i8")},
        artifact_id="array.literal-prepared-future-nonentry-reuse")
    product = SimpleNamespace(disposition="NO_ORIGIN", arrays=operand)
    calls = []
    monkeypatch.setattr(method, "validate_future_history", lambda *_: calls.append("original-custody-admission"))
    poison = SimpleNamespace(for_operand=lambda *_: pytest.fail("nonentry consumed an unneeded frozen input"))
    readout = method.assess_future(config, history, object(), object(), mechanical, product, initial, preparation_raw,
        frozen_raw, raw, record_id="readout.literal-prepared-future-nonentry-reuse", frozen_input=poison)
    expected = science.unentered_prepared_responses(source, preparation, protocol, panels,
        record_id=readout.record_id, disposition="NO_ORIGIN")
    assert calls == ["original-custody-admission"] and readout.canonical_bytes() == expected.canonical_bytes()
    assert len(readout.unentered_branch_ids) == 48 and len(readout.cells) == 240 and not readout.controls
    assert readout.cumulative_log_errors == (None,) * 15 and not readout.numerical_pass
    changed_raw, changed = method.array_product(source, {"unentered_branches": np.arange(48, dtype="<i8") + 1},
        artifact_id="array.forbidden-prepared-future-nonentry")
    with pytest.raises(ValueError, match="complete unentered branch marker"):
        method.assess_future(config, history, object(), object(), mechanical, SimpleNamespace(disposition="NO_ORIGIN", arrays=changed),
            initial, preparation_raw, frozen_raw, changed_raw, record_id="readout.forbidden-nonentry", frozen_input=poison)

    def refused(*_):
        raise ValueError("literal original handoff refusal")

    monkeypatch.setattr(method, "validate_future_history", refused)
    monkeypatch.setattr(method, "decode_matrix_arrays", lambda *_: pytest.fail("custody refusal reached array decoding"))
    with pytest.raises(ValueError, match="original handoff refusal"):
        method.assess_future(config, history, object(), object(), mechanical, product, initial, preparation_raw,
            frozen_raw, raw, record_id="readout.forbidden-before-decode", frozen_input=poison)


@pytest.mark.parametrize("nonentry", (False, True))
def test_installed_prepared_assessor_reuses_one_frozen_decode_and_keeps_actual_cold_reproof(tmp_path, monkeypatch, nonentry):
    """Actual score worker/physical equations; ordinary input/native-custody admission are explicit seams."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_future_bindings as worker
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science, prepared_forecast, prepared_response_science as science
    from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
    from empirical_lawhood.infrastructure import matrix_array_io
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from tests import test_matrix_prepared_forecast as physical_fixture
    source, protocol, causal, causal_raw, template_raw = physical_fixture.case.__wrapped__(tmp_path)
    if nonentry:
        causal = replace(causal, disposition="NO_ORIGIN", frame_sha256=None, reason="DISCLOSED_CONTROL_NO_ORIGIN")
    frozen_raw, mechanical = prepared_forecast.forecast(source, protocol, causal, causal_raw, template_raw,
        artifact_id="array.literal-prepared-score-worker-reuse")
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype="<c16")
    factor = np.asarray([np.kron(row, np.eye(2)) / 2 for row in pauli], dtype="<c16")
    positions = np.stack((factor, factor)).astype("<c16")
    initial, _ = encode_matrix_arrays({"positions": positions, "momenta": np.zeros_like(positions)})
    assert sha256(initial).hexdigest() == source.initial.array_artifact.sha256
    zeros = np.zeros((source.total_ticks, 2, 3, 4, 4), dtype="<c16")
    prepared = preparation_science.propagate_preparation(source, initial, coarse_innovations=zeros, bridge_innovations=zeros)
    preparation_raw, preparation = preparation_science.preparation_array_product(source, initial, prepared,
        artifact_id="array.literal-pauli-preparation")
    assert method.preparation_identity(preparation) == mechanical.arrays.preparation
    group = source.root.root.independent_group_id
    panels = (science.MatrixPreparedResponsePanel("panel.reuse.common", group, "COMMON_NOISE_PANEL", source.root.streams),
        science.MatrixPreparedResponsePanel("panel.reuse.independent", group, "INDEPENDENT_FUTURE",
            tuple(MatrixHistorySeed(purpose, sha256(("prepared-score-reuse." + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
    if nonentry:
        values = {"unentered_branches": np.arange(48, dtype="<i8")}
        disposition = "NO_ORIGIN"
    else:
        innovations = {panel.panel_id: {"primary": np.zeros((3, 2, 3, 4, 4), dtype="<c16"),
            "fine": np.zeros((6, 2, 3, 4, 4), dtype="<c16"), "bridge": np.zeros((3, 2, 3, 4, 4), dtype="<c16")} for panel in panels}
        values = science.propagate_prepared_responses(source, initial, preparation, preparation_raw,
            protocol, panels, mechanical.arrays, frozen_raw, innovations)
        disposition = "COMPLETED"
    future_raw, future = method.array_product(source, values, artifact_id="array.literal-prepared-score-worker-future")
    product = SimpleNamespace(disposition=disposition, arrays=future)
    config = SimpleNamespace(source=source, protocol=protocol, panels=panels)
    records = {"history": SimpleNamespace(arrays=preparation), "causal": causal, "point": object(),
        "mechanical": mechanical, "responses": product}
    # No receipt is fabricated: this is an ordinary decoded-input/cold-science control.
    monkeypatch.setattr(method, "validate_future_history", lambda *_: None)
    expected = method.assess_future(config, *(records[name] for name in ("history", "causal", "point", "mechanical", "responses")),
        initial, preparation_raw, frozen_raw, future_raw, record_id="score." + source.source_id)

    class Port:
        def __init__(self, raw):
            self.raw, self.closed = raw, False
        def read(self):
            assert not self.closed
            return self.raw
        def close(self):
            self.closed = True

    raw_ports = {"initial-state": initial, "history-arrays": preparation_raw, "mechanical-arrays": frozen_raw,
        "response-arrays": future_raw, "causal-arrays": causal_raw, "templates": template_raw}
    ports = {key: Port(raw) for key, raw in raw_ports.items()}
    context = SimpleNamespace(task_id="worker.literal-prepared-score-reuse", input_ports=tuple(ports.values()),
        output_ports=(SimpleNamespace(output_id="worker.literal-prepared-score-reuse.product"),))
    monkeypatch.setattr(worker, "_decode", lambda received, phase: (config, records, ports))
    calls, decode = [], matrix_array_io._decode_matrix_arrays

    def observed(raw, operand):
        if raw is frozen_raw:
            calls.append(operand)
        return decode(raw, operand)

    monkeypatch.setattr(matrix_array_io, "_decode_matrix_arrays", observed)
    for owner in (science, prepared_forecast):
        original = owner.decode_matrix_arrays
        def no_repeat(raw, operand, original=original):
            if raw is frozen_raw:
                pytest.fail("installed prepared score worker expanded its frozen input twice")
            return original(raw, operand)
        monkeypatch.setattr(owner, "decode_matrix_arrays", no_repeat)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
    monkeypatch.setattr(response_forecast, "_hessian", lambda *_: pytest.fail("cold reproof entered Hessian producer"))
    monkeypatch.setattr(np.linalg, "eigh", lambda *_: pytest.fail("cold reproof entered eigensolver"))
    monkeypatch.setattr(np.random, "Generator", lambda *_: pytest.fail("cold score created RNG"))
    score = next(row for row in worker.operation_declarations()
        if row.capability_key == method.NAMESPACE + ".response-score")
    factory = score.provider_factory()
    assessor = factory.runner_factory()
    assert type(assessor) is worker.MatrixPreparedFutureAssessor
    assert assessor.manifest == factory.manifest == score.manifest()
    result = assessor.execute(context)
    assert calls == [mechanical.arrays] and all(port.closed for port in ports.values())
    actual = decode_canonical_bytes(result.outputs[0].payload, science.MatrixPreparedResponseReadout, maximum_bytes=None)
    assert actual == expected and actual.canonical_bytes() == expected.canonical_bytes()
    assert len(actual.cells) == 240 and len(actual.cumulative_log_errors) == 15
    assert len(actual.controls) == (0 if nonentry else 48)
    assert len(actual.unentered_branch_ids) == (48 if nonentry else 0)

    # A later actual received input is authenticated anew; the first holder is not reused.
    ports = {key: Port(raw) for key, raw in raw_ports.items()}
    ports["mechanical-arrays"].raw = frozen_raw[:-1]
    refused_context = SimpleNamespace(task_id=context.task_id, input_ports=tuple(ports.values()), output_ports=context.output_ports)
    with pytest.raises(ValueError):
        factory.runner_factory().execute(refused_context)
    assert all(port.closed for port in ports.values())
