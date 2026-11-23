# SPDX-License-Identifier: MPL-2.0
from dataclasses import replace
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.finite_response_law.instruments import (
    REFERENCE_INSTRUMENT,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_forecast import (
    WaveformFeatures,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_population import (
    SAMPLE_TICKS,
    allocate_waveform,
    observe_waveform_history,
)
from empirical_lawhood.domains.matrix.prepared_response.instruments import (
    PreparedPortFrame,
    prepared_receiver,
)
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import (
    _encode,
)
from empirical_lawhood.domains.matrix.waveform_preparation.experiment import (
    population_seeds,
)
from empirical_lawhood.domains.matrix.classical_series.arrays import (
    encode_acquisition,
    iter_encoded_bytes,
)
from empirical_lawhood.domains.matrix.finite_response_law.authoring.rerun_input import (
    FiniteResponseLawCurrentExposure,
)
from empirical_lawhood.domains.matrix.finite_response_law.original_f import (
    OriginalFiniteResponseLaw,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_population import (
    WaveformNativePhase,
    WaveformPrefix,
)
from empirical_lawhood.domains.matrix.waveform_preparation.bindings import (
    FLOAT_FIELDS,
    read_operand,
)
from empirical_lawhood.domains.matrix.waveform_preparation.records import (
    WaveformOperation,
    WaveformProduct,
    WaveformSpecification,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def test_waveform_assignment_pairs_views_but_separates_sources_and_roles():
    draw = allocate_waveform(master_seed=250002, role="development", index=0)
    independent = allocate_waveform(master_seed=250002, role="evaluation", index=0)
    assert not (set(population_seeds((draw,))) & set(population_seeds((independent,))))
    assert draw.stream("prefix").innovation_fraction == Decimal(".002")
    assert draw.stream("future-1").nominal_seed_sha256 is None
    assert draw.stream("future-1").innovation_fraction == 1
    with pytest.raises(ValueError, match="collide"):
        population_seeds((draw, draw))


def test_prefix_observes_the_same_physical_clock_and_measured_x_port_in_both_views():
    ticks = tuple(range(4096 - 480, 4097, 16))
    modes = np.zeros((2, 3, 4, 4), dtype="<c16")
    modes[0, 0, 0, 0] = modes[1, 1, 1, 1] = 1
    frame = PreparedPortFrame(4096, modes)
    positions = np.zeros((31, 2, 3, 4, 4), dtype="<c16")
    for i, tick in enumerate(ticks):
        positions[i, 0] = (tick / 16) * modes[1]
        positions[i, 1] = -1000 * modes[1]
    features = [Decimal(0)] * 24
    features[REFERENCE_INSTRUMENT.feature_ids.index("x-port-2")] = Decimal(
        str(prepared_receiver(frame, positions[-1, 0])[1])
    )
    phases = []
    for r in (1, 2):
        trace = np.zeros((4096 * r, 9))
        trace[:, 3] = np.arange(1, 4096 * r + 1) / r
        trace[:, 4] = -trace[:, 3]
        phases.append(
            SimpleNamespace(
                disposition="COMPLETE",
                history_ticks=ticks,
                history_positions_base64=_encode(positions),
                completed_intervals=len(trace),
                trace_base64=_encode(trace),
            )
        )
    prefix = SimpleNamespace(
        frame_base64=_encode(modes), phases=phases, features=(features, features)
    )
    first = observe_waveform_history(prefix, refinement=1)
    assert first == observe_waveform_history(prefix, refinement=2)
    assert tuple(float(x) for x in first["earlier_port_two"]) == tuple(
        t / 16 for t in SAMPLE_TICKS[:-1]
    )
    assert tuple(first["drive"][::2]) == SAMPLE_TICKS
    for suffix in ("later path A", "different later path B"):
        trajectory = SimpleNamespace(prefix=prefix, future=suffix)
        assert observe_waveform_history(trajectory.prefix) == first
    phases[0].disposition = "OBSERVATION_FAILURE"
    assert observe_waveform_history(prefix) is None


def test_history_and_margin_comparisons_use_identical_shared_inputs():
    features = WaveformFeatures(
        "unit.test",
        "a" * 64,
        "b" * 64,
        1,
        tuple(map(Decimal, range(24))),
        tuple(map(Decimal, range(18))),
        tuple(map(Decimal, range(8))),
        Decimal("-1.25"),
    )
    assert (
        features.row("drive-history")
        == features.row("drive") + features.earlier_port_two
    )
    for k in ("drive", "drive-history", "snapshot"):
        assert features.row(k + "-margin") == features.row(k) + (features.margin,)
    assert (
        replace(
            features, margin=None, full_prefix=(), drive=(), earlier_port_two=()
        ).row("drive")
        is None
    )


def test_binary_native_companion_restores_canonical_measurement_and_refuses_damage(
    monkeypatch,
):
    from empirical_lawhood.domains.matrix.waveform_preparation import bindings, design
    from empirical_lawhood.execution.execution import WorkerOutputPort
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile

    lower = ObjectIdentity(
        "original.f", OriginalFiniteResponseLaw.SCHEMA, "1.0.0", "a" * 64
    )
    prior = ObjectIdentity(
        "known.exposure", FiniteResponseLawCurrentExposure.SCHEMA, "1.0.0", "b" * 64
    )
    spec = WaveformSpecification(
        "specification.codec",
        "development",
        251,
        901,
        lower,
        "c" * 64,
        "d" * 64,
        "e" * 64,
        prior,
    )
    config = WaveformOperation(spec, "prefix", 0)
    draw = spec.draw(0)
    phases = tuple(
        WaveformNativePhase(
            draw.unit_id,
            "prefix",
            None,
            None,
            None,
            v,
            spec.producing_code_sha256,
            None,
            0,
            4096,
            0,
            0,
            (Decimal(0), Decimal(0)),
            Decimal(0),
            Decimal(0),
            Decimal(0),
            "NUMERICAL_FAILURE",
            "fixture",
            "f" * 64,
            (draw.stream("prefix"), draw.stream("prefix-bridge")),
            "",
            (),
            "",
            "",
            "",
            (),
            None,
            (),
            "",
            "",
            waveform=draw,
            allocation=draw.allocation,
        )
        for v in (1, 2)
    )
    frame = _encode(np.arange(192, dtype="<f8").view("<c16").reshape((2, 3, 4, 4)))
    operand = WaveformPrefix(
        draw.unit_id, phases, frame, ((Decimal(".125"),) * 24,) * 2
    )
    plain = WaveformProduct.from_operand(config, (), operand)
    encoded, chunks = encode_acquisition(
        plain, artifact_id=config.node_id + ".arrays", base64_float_fields=FLOAT_FIELDS
    )
    raw = b"".join(iter_encoded_bytes(encoded, chunks))
    assert (
        read_operand(encoded, BytesIO(raw)).canonical_bytes()
        == operand.canonical_bytes()
    )
    with pytest.raises(ValueError):
        read_operand(encoded, BytesIO(raw[:-1]))
    with pytest.raises(ValueError, match="canonical bytes"):
        read_operand(replace(encoded, operand_sha256="2" * 64), BytesIO(raw))

    run_id = "recursive." + "3" * 24
    array_id = config.node_id + ".arrays"
    product_id = config.node_id + ".product"
    array_port = WorkerOutputPort(
        array_id,
        encoded.array_artifact.payload_schema,
        ArtifactProfile.RAW_SOURCE_BYTES,
        "application/octet-stream",
        f"artifact.{run_id}.{array_id}",
    )
    product_port = WorkerOutputPort(
        product_id,
        WaveformProduct.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,
        "application/json",
        f"artifact.{run_id}.{product_id}",
    )
    port = SimpleNamespace(
        payload_schema=config.SCHEMA,
        media_type="application/json",
        size_bytes=len(config.canonical_bytes()),
        decode_canonical_record=lambda *args, **kwargs: config,
        close=lambda: None,
    )
    context = SimpleNamespace(
        run_id=run_id,
        task_id=config.node_id,
        input_ports=(port,),
        output_ports=(array_port, product_port),
        permissions=design.PERMISSIONS,
        resource_budget=design.BUDGET,
        outcome_access=design.ACCESS,
        config=SimpleNamespace(
            config_id=config.config_id, content_sha256=config.fingerprint()
        ),
    )
    monkeypatch.setattr(bindings, "acquire_prefix", lambda *args, **kwargs: operand)
    runner = next(
        d for d in bindings.declarations() if d.capability_key.endswith(".prefix")
    ).runner_factory()
    binary, document = runner.execute(context).outputs
    published = decode_canonical_bytes(
        document.payload, WaveformProduct, maximum_bytes=len(document.payload)
    )
    assert published.array_artifact.artifact_id == array_port.logical_artifact_id
    assert read_operand(published, BytesIO(binary.payload)) == operand
    context.run_id = "recursive." + "4" * 24
    with pytest.raises(ValueError, match="another run"):
        runner.execute(context)


def test_waveform_worker_streams_large_assay_metadata_without_changing_bytes(
    monkeypatch,
):
    from empirical_lawhood.domains.matrix.waveform_preparation.bindings import Runner
    from empirical_lawhood.execution.local.execution import _PipeOutputEmitter
    from empirical_lawhood.storage.artifact_stream_primitives import STREAM_CHUNK_BYTES

    runner = Runner(manifest=None)
    payload = b"x" * (2 * STREAM_CHUNK_BYTES) + b"\n"
    binary = b"waveform"
    outputs = (("assay.arrays", (binary,)), ("assay.product", (payload,)))
    monkeypatch.setattr(runner, "_outputs", lambda context: outputs)
    context = SimpleNamespace(
        input_ports=(),
        output_ports=tuple(SimpleNamespace(output_id=key) for key, _ in outputs),
        resource_budget=SimpleNamespace(output_bytes=len(payload) + len(binary)),
    )
    messages = []
    emitter = _PipeOutputEmitter(SimpleNamespace(send=messages.append), context)
    runner.execute_streaming(context, emitter)
    assert [(m.output_id, len(m.payload)) for m in messages] == [
        ("assay.arrays", len(binary)),
        ("assay.product", STREAM_CHUNK_BYTES),
        ("assay.product", STREAM_CHUNK_BYTES),
        ("assay.product", 1),
    ]
    assert messages[0].payload == binary
    assert b"".join(m.payload for m in messages[1:]) == payload


def test_partial_panel_preserves_every_independently_measurable_signed_response(
    monkeypatch,
):
    from empirical_lawhood.domains.matrix.preparation_applicability import (
        measurement,
        waveform_trial,
    )
    from tests.test_preparation_applicability_reducers import _synthetic_panel

    prefix, panel = _synthetic_panel(monkeypatch)
    monkeypatch.setattr(
        waveform_trial, "_frame", lambda p: SimpleNamespace(cutoff_tick=4096)
    )
    _, full, _ = measurement.reduce_panel(prefix, panel)
    target = next(
        p
        for p in panel.phases
        if (p.schedule_index, p.refinement, p.future_index, p.word_index)
        == (1, 2, 0, waveform_trial.PORT_TWO_WORDS[0])
    )
    target.disposition = "OBSERVATION_FAILURE"
    assert measurement.reduce_panel(prefix, panel) is None
    partial = waveform_trial._available_port_two(prefix, panel)
    assert [i for i, v in enumerate(partial) if v is None] == [5]
    expected = full[:, waveform_trial.PORT_TWO_PAIR, 1].ravel()
    assert all(
        val is None or float(val) == expected[i] for i, val in enumerate(partial)
    )
    from empirical_lawhood.api.waveform_preparation import _root_readout
    record = SimpleNamespace(
        draw=SimpleNamespace(unit_id="test.waveform"), fingerprint=lambda: "1" * 64,
        complete=False, measured=SimpleNamespace(covered_counts=(), false_admissions=(), conjuncts=()),
        native_intervals=12, primary=SimpleNamespace(margin=None),
        signed_port_two=partial, failures=("OBSERVATION_FAILURE",),
    )
    displayed = _root_readout(record)["signed_port_two"]
    assert displayed[5] is None
    assert [Decimal(v) for v in displayed if v is not None] == [v for v in partial if v is not None]
