# SPDX-License-Identifier: MPL-2.0
"""Installed Matrix requirements and recorded-profile refusals without effects."""

from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.matrix.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.api.numerical_provenance import validate_registered_provenance
from empirical_lawhood.api.recursive_operations import operation_factories
from tests.test_rubisco_kinetic_declaration import _profile_provenance


def _matrix_factories():
    return tuple(factory for factory in operation_factories()
        if ".matrix_" in factory.registration.config_record_type.__module__
        or factory.manifest.capability_key.startswith("matrix-"))


def test_every_installed_matrix_operation_retains_its_explicit_profile_requirement():
    # These two independent study families declare per-study numerical settings.
    # The selected Matrix response programme owns the shared profile checked here.
    from empirical_lawhood.domains.matrix.classical_series.records import NAMESPACE as classical
    from empirical_lawhood.domains.matrix.model_free.records import NAMESPACE as model_free
    installed = _matrix_factories()
    for family, phases in ((classical, {"acquire", "analyse", "calibrate", "summarise", "synthesise"}),
                           (model_free, {"acquire", "analyse", "synthesise"})):
        selected = {factory.manifest.capability_key: factory.registration for factory in installed
                    if factory.manifest.capability_key.startswith(family + ".")}
        assert set(selected) == {family + "." + phase for phase in phases}
        assert all("settings_json" in item.config_record_type.__dataclass_fields__ for item in selected.values())
    factories = tuple(factory for factory in installed
        if factory.manifest.capability_key.split(".", 1)[0] not in (classical, model_free))
    assert len(factories) >= 154
    retained_or_metadata = {
        *("matrix-e3-configured-protected.retained-" + phase for phase in (
            "check", "feature", "fit", "forecast", "measure", "model-freeze", "numerical",
            "physical-forecast", "prefix", "project")),
        "matrix-prepared-functional.nominate", "matrix-scheduled-revision-future.seal",
        "matrix-scheduled-revision.calibrate",
        *("matrix-selected-e4-full-factor." + scope + "." + phase
            for scope in ("dev", "revealed") for phase in ("assess", "measure", "reduce")),
    }
    assert {factory.manifest.capability_key for factory in factories
        if not factory.registration.provenance_requirements} == retained_or_metadata
    assert all(not factory.registration.native_effect for factory in factories
        if factory.manifest.capability_key in retained_or_metadata)
    assert all(factory.registration.provenance_requirements == (MATRIX_PROVENANCE_REQUIREMENT,)
        for factory in factories if factory.manifest.capability_key not in retained_or_metadata)
    assert {factory.manifest.capability_key for factory in factories} >= {
        "matrix-response-error-v2.forecast",
        "matrix-response-error-development-v2.forecast", "matrix-scheduled-programme.global-commit",
        "matrix-scheduled-programme.confirmation-global-commit", "matrix-scheduled-programme.tail-custody-freeze",
    }


def test_shared_dispatch_checks_matrix_profile_without_observing_reader_runtime(monkeypatch):
    registrations = tuple(factory.registration for factory in _matrix_factories())
    # Only the dispatch seam is exercised: these selections create no study,
    # source custody, publication, scientific execution or authority record.
    operations = tuple(SimpleNamespace(node_id=registration.selection.capability_key,
        selection=registration.selection) for registration in registrations)
    draft = SimpleNamespace(operations=operations,
        selected_operation_ids=tuple(operation.node_id for operation in operations))
    monkeypatch.setattr("platform.python_version", lambda: "reader-runtime-is-distinct")
    assert validate_registered_provenance(provenance=_profile_provenance(), draft=draft,
        registrations=registrations) is None
    with pytest.raises(ValueError, match="Matrix runtime observation.*selected numerical profile"):
        validate_registered_provenance(provenance=_profile_provenance(numpy="0.0.0"), draft=draft,
            registrations=registrations)
