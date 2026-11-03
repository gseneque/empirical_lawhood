# SPDX-License-Identifier: MPL-2.0
"""Exposed lifecycle seams only; no actual signer, prior or native qualification."""
from dataclasses import replace
from types import SimpleNamespace as N
import weakref

import pytest

from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import science, native, operation_bindings as owner
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticSource, DiagnosticResult
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySupply
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from tests.test_battery_dfn_precision_diagnostic import config_rows, exposed


class ExposedPriorPayload:
    """Weak-referenceable decoded-history stand-in, not real scientific evidence."""
    SCHEMA = BatteryInquirySupply.SCHEMA
    VERSION = BatteryInquirySupply.VERSION
    product_id = "product.battery-thermal-inquiry.supply"

    def fingerprint(self):
        return DiagnosticSource().prior_supply_sha256


class ExposedPort:
    kind = WorkerInputKind.EXTERNAL
    media_type = "application/json"
    outcome_access = OutcomeAccess.DEVELOPMENT_VISIBLE
    size_bytes = 1

    def __init__(self, schema, raw):
        self.payload_schema, self.raw = schema, raw
        self.closed = False

    def read(self):
        assert not self.closed
        return self.raw

    def close(self):
        self.closed = True


def test_exposed_runner_releases_validated_decoded_history_before_native(monkeypatch):
    source = DiagnosticSource()
    prior_identity = config_rows()[0].prior_supply
    config = owner.DiagnosticOperationConfig("config." + owner.NAMESPACE, source,
        tuple(sorted((science.identity(source), prior_identity), key=lambda row: row.object_id)))
    references, validations, calls = [], [], []
    ports = tuple(ExposedPort(schema, raw) for schema, raw in
                  ((BatteryInquirySupply.SCHEMA, b"p"), (config.SCHEMA, b"c"), (source.SCHEMA, b"s")))

    def decode(raw, record_type, **kwargs):
        if raw == b"p":
            prior = ExposedPriorPayload()
            references.append(weakref.ref(prior))
            return prior
        return config if raw == b"c" else source

    def validate(actual_source, prior):
        assert actual_source == source and science.identity(prior) == prior_identity
        validations.append(weakref.ref(prior))

    def acquire(row):
        assert len(validations) == 1
        assert references[0]() is None and validations[0]() is None
        assert all(port.closed for port in ports)
        calls.append(row)
        return exposed(row)

    monkeypatch.setattr(owner, "decode_canonical_bytes", decode)
    monkeypatch.setattr(science, "validate_prior", validate)
    monkeypatch.setattr(native, "acquire", acquire)
    runner = owner.DiagnosticRunner()
    node = owner.NAMESPACE + ".diagnose"
    context = N(task_id=node, permissions=runner.manifest.permissions, resource_budget=owner.BUDGET,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, input_ports=ports,
        config=N(config_id=config.config_id, content_sha256=config.fingerprint()),
        output_ports=(N(output_id=node + ".product", payload_schema=DiagnosticResult.SCHEMA,
                        profile=ArtifactProfile.CANONICAL_JSON, media_type="application/json"),))
    result = runner.execute(context)
    assert tuple(calls) == config_rows()
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    record = decode_canonical_bytes(result.outputs[0].payload, DiagnosticResult, maximum_bytes=None)
    assert record.prior_supply == prior_identity
    assert len(record.traces) == len(record.checks) == 12 and len(record.comparisons) == 9
    science.validate_result(record)


def test_exposed_public_wrapper_keeps_validation_and_exact_core_result(monkeypatch):
    source, prior = DiagnosticSource(), ExposedPriorPayload()
    validated = []
    monkeypatch.setattr(science, "validate_prior", lambda s, p: validated.append((s, p)))
    monkeypatch.setattr(native, "acquire", exposed)
    public = science.run(source, prior)
    private = science._run_validated_prior(source, science.identity(prior))
    assert validated == [(source, prior)]
    assert public.canonical_bytes() == private.canonical_bytes()
    assert tuple(row.config for row in public.traces) == config_rows()


@pytest.mark.parametrize("change", [
    {"object_id": "product.exposed-other-history"},
    {"object_schema": "empirical-lawhood/testing/exposed-other-schema"},
    {"object_version": "1.0.0"},
    {"object_fingerprint": "0" * 64},
])
def test_exposed_private_core_refuses_substituted_prior_before_native(monkeypatch, change):
    def unexpected_native(config):
        raise AssertionError("forged historical identity entered native acquisition")

    monkeypatch.setattr(native, "acquire", unexpected_native)
    with pytest.raises(ValueError, match="exact validated prior identity"):
        science._run_validated_prior(DiagnosticSource(), replace(config_rows()[0].prior_supply, **change))


def test_exposed_private_core_refuses_untyped_identity(monkeypatch):
    monkeypatch.setattr(native, "acquire", lambda config: pytest.fail("untyped history entered native"))
    identity = config_rows()[0].prior_supply
    forged = N(**{field: getattr(identity, field) for field in
                  ("object_id", "object_schema", "object_version", "object_fingerprint")})
    assert not isinstance(forged, ObjectIdentity)
    with pytest.raises(ValueError, match="exact validated prior identity"):
        science._run_validated_prior(DiagnosticSource(), forged)
