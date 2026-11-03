# SPDX-License-Identifier: MPL-2.0
"""Only explicitly declared editable roles enter configuration discovery."""
from dataclasses import dataclass, replace
from typing import ClassVar

import pytest

from empirical_lawhood.api import configuration_registry
from empirical_lawhood.api.configuration import validate_configuration
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.experiment_preparation import (
    ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration, PreparedExperimentInputs,
)


@dataclass(frozen=True, slots=True)
class EditableOperationalInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/explicit-operational-input"
    workers: int


@dataclass(frozen=True, slots=True)
class EditableOperationalInputV2(EditableOperationalInput):
    VERSION: ClassVar[str] = "2.0.0"
    numerical_threads: int


@dataclass(frozen=True, slots=True)
class OriginalEvidenceInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/original-evidence-input"
    original_id: str


@dataclass(frozen=True, slots=True)
class QuestionSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/question-specification"
    question: str


def declaration():
    selected = ExperimentInputConfigurationDeclaration("test-explicit-operational-input",
        EditableOperationalInput, maximum_config_bytes=65536)
    return ExperimentProtocolDeclaration("test.input-config-projection", QuestionSpecification,
        lambda *_args, **_kw: None, "test-original-specification",
        input_record_types=(EditableOperationalInput, OriginalEvidenceInput),
        bind_inputs=lambda *_args, **_kw: PreparedExperimentInputs({}),
        configuration_inputs=(selected,))


def test_only_explicit_role_is_editable_and_config_validation_has_no_prerequisite_contact(tmp_path, monkeypatch):
    from empirical_lawhood.api import experiment_preparation

    owner = declaration()
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", lambda: (owner,))
    values = configuration_registry._configuration_consumers()
    assert [row.consumer for row in values if row.schema_id == EditableOperationalInput.SCHEMA] == [
        "test-explicit-operational-input"]
    # Evidence is permitted only as a protocol source operand. Merely listing
    # its decoder does not create an editable evidence configuration consumer.
    assert not any(row.schema_id == OriginalEvidenceInput.SCHEMA for row in values)
    path = tmp_path / "operational.json"
    record = EditableOperationalInput(4)
    path.write_bytes(record.canonical_bytes())
    result = validate_configuration(path, consumer="test-explicit-operational-input")
    assert result["status"] == "VALIDATED" and result["consumer_byte_ready"]
    assert result["authority_granted"] is False and result["external_prerequisites_checked"] is False


@pytest.mark.parametrize("damage", ("foreign", "duplicate", "specification", "untyped"))
def test_configuration_role_requires_exact_declared_input_and_unique_consumer(damage):
    owner = declaration()
    role, = owner.configuration_inputs
    with pytest.raises((ValueError, TypeError)):
        if damage == "foreign":
            replace(owner, input_record_types=(OriginalEvidenceInput,))
        elif damage == "duplicate":
            replace(owner, configuration_inputs=(role, role))
        elif damage == "specification":
            replace(owner, configuration_inputs=(replace(role, consumer_id=owner.consumer_id),))
        else:
            replace(owner, configuration_inputs=(object(),))


@pytest.mark.parametrize("bound", (None, 0, -1, True, 1.5))
def test_configuration_parser_bounds_remain_explicit_positive_integers(bound):
    with pytest.raises(ValueError):
        ExperimentInputConfigurationDeclaration("test.input-config", EditableOperationalInput, bound)


@pytest.mark.parametrize("reverse", (False, True))
def test_public_inputs_keep_exact_same_schema_editions_without_roster_order_dependence(tmp_path, monkeypatch, reverse):
    from empirical_lawhood.api import experiment_preparation
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection

    kinds = (EditableOperationalInput, EditableOperationalInputV2)
    owner = replace(declaration(), input_record_types=kinds[::-1] if reverse else kinds,
        bind_inputs=lambda _specification, records: PreparedExperimentInputs({}, records))
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", lambda: (owner,))
    records = {"current": EditableOperationalInputV2(4, 1), "legacy": EditableOperationalInput(4)}
    bindings = []
    for key, record in records.items():
        payload = record.canonical_bytes()
        (tmp_path / (key + ".json")).write_bytes(payload)
        bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record(key, record), key + ".json", len(payload)))
    selection = ExperimentInputSelection("selection.editions", owner.protocol_id, tuple(bindings))
    selected = tmp_path / "sources.json"
    selected.write_bytes(selection.canonical_bytes())
    loaded = experiment_preparation.load_experiment_inputs(QuestionSpecification("Selected editions"), selected)
    for key, record in records.items():
        assert type(loaded.method_inputs[key]) is type(record)
        assert loaded.method_inputs[key].canonical_bytes() == record.canonical_bytes()
    changed = replace(selection, bindings=(replace(bindings[0],
        identity=replace(bindings[0].identity, object_version="3.0.0")), bindings[1]))
    selected.write_bytes(changed.canonical_bytes())
    with pytest.raises(ValueError, match="exact codec/revision"):
        experiment_preparation.load_experiment_inputs(QuestionSpecification("Unknown edition"), selected)
    with pytest.raises(TypeError, match="closed code-owned"):
        replace(owner, input_record_types=(EditableOperationalInput, EditableOperationalInput))
