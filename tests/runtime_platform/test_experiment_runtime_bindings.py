# SPDX-License-Identifier: MPL-2.0
"""Declared API composition selection, without constructing a runtime or source."""

from dataclasses import replace

import pytest

from empirical_lawhood.api import generated_experiment_runtime_bindings as generated
from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration, ExperimentRuntimeBinding
from tests.runtime_platform.test_recursive_compiler import Config


def protocol(*, required=False):
    return ExperimentProtocolDeclaration("protocol.synthetic-runtime", Config, lambda *_args: None,
        "consumer.synthetic-runtime", requires_prospective_runtime_binding=required)


def forbidden(*_args, **_kwargs):
    pytest.fail("static discovery constructed or entered a runtime")


def test_static_binding_selection_never_enters_handler_and_requires_exact_protocol(monkeypatch):
    selected = protocol(required=True)
    binding = ExperimentRuntimeBinding(selected.protocol_id, forbidden)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    assert experiment_runtime_binding(selected) is binding
    other = replace(selected, protocol_id="protocol.uninstalled-runtime")
    with pytest.raises(ValueError, match="SOFTWARE"):
        experiment_runtime_binding(other)


@pytest.mark.parametrize("damage", ("missing", "duplicate", "wrong-type", "unrequested"))
def test_missing_conflicting_or_unrequested_api_composition_refuses_before_handler(monkeypatch, damage):
    selected = protocol(required=damage != "unrequested")
    binding = ExperimentRuntimeBinding(selected.protocol_id, forbidden)
    rows = {"missing": (), "duplicate": (binding, binding), "wrong-type": (object(),), "unrequested": (binding,)}[damage]
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", rows)
    with pytest.raises(ValueError):
        experiment_runtime_binding(selected)


def test_ordinary_protocol_needs_no_api_runtime_binding(monkeypatch):
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", ())
    assert experiment_runtime_binding(protocol()) is None


@pytest.mark.parametrize("value", (0, 1, None, "required"))
def test_requirement_is_a_strict_code_owned_boolean(value):
    with pytest.raises(TypeError, match="must be explicit"):
        replace(protocol(), requires_prospective_runtime_binding=value)


def test_installed_protected_protocol_joins_only_its_own_api_and_file_owners():
    from empirical_lawhood.api.experiment_preparation import _file_byte_limit, experiment_protocols
    from empirical_lawhood.api.matrix_protected_experiment import bind_protected_factorial_experiment_handoff
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactBank
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_reduction import ScheduledProgrammeReduction
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionDataBank
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_specification import PROTOCOL_ID
    from empirical_lawhood.kernel.references import ArtifactIdentity

    declared = experiment_protocols()
    from empirical_lawhood.api.experiment_runtime_bindings import validate_experiment_runtime_binding
    required = {row.protocol_id for row in declared if row.requires_prospective_runtime_binding
        or row.requires_development_runtime_binding or row.programme_record_type is not None}
    installed = {row.protocol_id for row in generated.EXPERIMENT_RUNTIME_BINDINGS}
    assert required <= installed <= {row.protocol_id for row in declared}
    owners = {row.protocol_id: row for row in declared}
    assert len(installed) == len(generated.EXPERIMENT_RUNTIME_BINDINGS)
    for row in generated.EXPERIMENT_RUNTIME_BINDINGS:
        assert validate_experiment_runtime_binding(owners[row.protocol_id], row) is row
    selected, = (row for row in declared if row.protocol_id == PROTOCOL_ID)
    binding = experiment_runtime_binding(selected)
    assert binding.bind_handoff is bind_protected_factorial_experiment_handoff
    expected = (ScheduledCompactBank, ScheduledProgrammeReduction, ScheduledRevisionDataBank)
    assert set(selected.input_file_record_types) == set(expected)
    assert not set(expected) & set(selected.input_record_types)
    for kind in expected:
        identity = ArtifactIdentity("file.metadata-only", "contract-check", kind.SCHEMA, "a" * 64, "application/json", 123)
        assert _file_byte_limit(selected, identity, kind.VERSION, operation_storage_codecs()) is None
        with pytest.raises(ValueError, match="exact declared schema/revision"):
            _file_byte_limit(selected, identity, "99.0.0", operation_storage_codecs())


def test_development_runtime_binding_remains_a_separate_explicit_lifecycle(monkeypatch):
    selected = replace(protocol(), requires_development_runtime_binding=True)
    binding = ExperimentRuntimeBinding(selected.protocol_id, None, bind_development_runtime=forbidden)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    assert experiment_runtime_binding(selected) is binding
    with pytest.raises(TypeError, match="explicit lifecycle"):
        replace(selected, requires_prospective_runtime_binding=True)
    incompatible = ExperimentRuntimeBinding(selected.protocol_id, forbidden)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (incompatible,))
    with pytest.raises(ValueError, match="declared lifecycle"):
        experiment_runtime_binding(selected)


def test_retained_development_specification_selects_its_installed_api_binder(monkeypatch):
    from empirical_lawhood.api import experiment_preparation
    from empirical_lawhood.api.recursive_execution import _development_runtime_supplier

    selected = replace(protocol(), requires_development_runtime_binding=True)
    calls, wrapped = [], object()
    def bind(**values):
        calls.append(values)
        return wrapped
    binding = ExperimentRuntimeBinding(selected.protocol_id, None, bind_development_runtime=bind)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", lambda: (selected,))
    config = Config("configuration.development-runtime", 1)
    operands = {"experiment-instance.json": b"original authenticated instance",
                "experiment-specification.json": config.canonical_bytes()}
    result = _development_runtime_supplier(directory="selected-directory", writer="selected-writer", plan="frozen-plan",
        payloads=operands, supplier="original-inputs", output_codecs={})
    assert result is wrapped
    assert calls == [dict(directory="selected-directory", writer="selected-writer", plan="frozen-plan",
                          supplier="original-inputs", output_codecs={})]
    selected = replace(selected, requires_development_runtime_binding=False,
        requires_prospective_runtime_binding=True)
    binding = replace(binding, bind_handoff=forbidden)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    assert _development_runtime_supplier(directory="selected-directory", writer="selected-writer", plan="frozen-plan",
        payloads=operands, supplier="original-inputs", output_codecs={}) is wrapped
    assert calls[-1]['specification'] == config
    from empirical_lawhood.api.domain_composition.matrix_protected_response.experiment_binding import bind_exposed_development
    from tests.test_matrix_experiment_specification import selected as prospective_specification
    with pytest.raises(PermissionError, match='prospective E3 inputs'):
        bind_exposed_development(specification=prospective_specification(), supplier=wrapped)



def test_prospective_design_owner_is_cold_and_cannot_widen_the_declared_lifecycle(monkeypatch):
    selected = protocol(required=True)
    binding = ExperimentRuntimeBinding(selected.protocol_id, forbidden,
        prepare_authoring=forbidden, bind_development_runtime=forbidden,
        derive_prospective_design_inputs=forbidden)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    assert experiment_runtime_binding(selected) is binding
    with pytest.raises(TypeError, match="ordinary authoring and handoff"):
        replace(binding, prepare_authoring=None)
    with pytest.raises(TypeError, match="ordinary authoring and handoff"):
        replace(binding, derive_prospective_design_inputs=object())
    with pytest.raises(ValueError, match="prospective lifecycle"):
        experiment_runtime_binding(replace(selected, requires_prospective_runtime_binding=False,
            requires_development_runtime_binding=True))
