# SPDX-License-Identifier: MPL-2.0
"""Retained inspection does not repeat science; optional reconstruction is explicit."""

import numpy as np
import pytest

from empirical_lawhood.api import numerical_provenance, recursive_authoring
from empirical_lawhood.api.domain_composition.rubisco_response import paired_forecast as public
from empirical_lawhood.api.domain_composition.rubisco_response import native_analysis_export as owner
from empirical_lawhood.execution.operational_configuration import (
    ScientificReconstructionMode, scientific_reconstruction_operation,
)
from tests.test_recursive_public_service import _plane
from tests import test_rubisco_paired_forecast as forecast

fixture = forecast.fixture


def _publication(fixture, monkeypatch, *, originals=False):
    if originals:
        selection, sources, _ = forecast.electronic_forecast(fixture, monkeypatch)
    else:
        selection, sources = forecast.prepared_empty(), ()
    writer = _plane(fixture.tmp_path / "retained-inspection")
    monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda _: fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, "capture_numerical_provenance", lambda **k: fixture.config.provenance)
    exported = public.export_paired_forecast(selection=selection, sources=sources, project_root=fixture.tmp_path,
        artifact_writer=writer, output_relative_path="paired")
    return writer, sources, exported


def test_default_read_keeps_original_results_without_running_analysis(fixture, monkeypatch):
    writer, sources, exported = _publication(fixture, monkeypatch)
    calculate = public.read_paired_forecast
    calls = []
    def counted(**kwargs):
        calls.append(kwargs)
        return calculate(**kwargs)
    monkeypatch.setattr(public, "read_paired_forecast", counted)
    retained = public.read_paired_forecast_export(directory_relative_path="paired", sources=sources, artifact_writer=writer)
    assert calls == []
    assert retained["report"] == exported["report"]
    assert retained["report"]["joint"]["point_criteria"] == "UNEVALUABLE"
    assert retained["evidence"] == exported["evidence"]
    assert retained["scientific_reconstruction_performed"] is False
    assert retained["verification"] == "ORIGINAL_RECEIPTS_AND_RETAINED_RESULTS"
    with scientific_reconstruction_operation(ScientificReconstructionMode.FULL):
        reconstructed = public.read_paired_forecast_export(directory_relative_path="paired", sources=sources, artifact_writer=writer)
    assert len(calls) == 1
    assert reconstructed["scientific_reconstruction_performed"] is True
    assert reconstructed["report"] == retained["report"]
    assert reconstructed["evidence"] == retained["evidence"]
    assert reconstructed["arrays"].keys() == retained["arrays"].keys()
    assert all(np.array_equal(reconstructed["arrays"][key], value) for key, value in retained["arrays"].items())
    assert reconstructed["new_native_calls"] == retained["new_native_calls"] == 0


def test_explicit_reconstruction_compares_original_without_replacing_it(fixture, monkeypatch):
    writer, sources, exported = _publication(fixture, monkeypatch)
    calculate = public.read_paired_forecast
    def disagree(**kwargs):
        report, arrays = calculate(**kwargs)
        report["joint"]["point_criteria"] = "SATISFIED"
        return report, arrays
    monkeypatch.setattr(public, "read_paired_forecast", disagree)
    with scientific_reconstruction_operation(ScientificReconstructionMode.FULL):
        with pytest.raises(ValueError, match="independently reread"):
            public.read_paired_forecast_export(directory_relative_path="paired", sources=sources, artifact_writer=writer)
    retained = public.read_paired_forecast_export(directory_relative_path="paired", sources=sources, artifact_writer=writer)
    assert retained["report"] == exported["report"]
    assert retained["report"]["joint"]["point_criteria"] == "UNEVALUABLE"


def test_original_bytes_are_checked_after_publication_closing_checks(fixture, monkeypatch):
    writer, sources, _ = _publication(fixture, monkeypatch, originals=True)
    original = next(source for source in sources if source.original_result is not None)
    stream = original.native_subwork.iter_completed_output
    def changed(definition, output_id, **kwargs):
        for index, block in enumerate(stream(definition, output_id, **kwargs)):
            yield (bytes((block[0] ^ 1,)) + block[1:]) if index == 0 and block else block
    verify = type(writer).verify_manifest_members
    def mutate_after_close(self, *args, **kwargs):
        result = verify(self, *args, **kwargs)
        if self is writer:
            monkeypatch.setattr(original.native_subwork, "iter_completed_output", changed)
        return result
    monkeypatch.setattr(type(writer), "verify_manifest_members", mutate_after_close)
    def no_analysis(**kwargs):
        raise AssertionError("default inspection attempted a new calculation")
    monkeypatch.setattr(public, "read_paired_forecast", no_analysis)
    with pytest.raises(ValueError, match="original output changed"):
        public.read_paired_forecast_export(directory_relative_path="paired", sources=sources, artifact_writer=writer)


def test_failed_reconstruction_still_closes_original_source_lifetime(fixture, monkeypatch):
    writer, sources, _ = _publication(fixture, monkeypatch)
    checks = []
    original_check = owner.recheck_original_native_outputs
    def checked(selected, *, description):
        checks.append(description)
        return original_check(selected, description=description)
    monkeypatch.setattr(owner, "recheck_original_native_outputs", checked)
    def failed(**kwargs):
        raise ArithmeticError("independent reconstruction failed")
    monkeypatch.setattr(public, "read_paired_forecast", failed)
    with scientific_reconstruction_operation(ScientificReconstructionMode.FULL):
        with pytest.raises(ArithmeticError, match="independent reconstruction failed"):
            public.read_paired_forecast_export(directory_relative_path="paired", sources=sources, artifact_writer=writer)
    assert checks == ["retained analysis entry", "retained analysis closing"]
