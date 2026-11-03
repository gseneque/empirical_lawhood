# SPDX-License-Identifier: MPL-2.0
"""Pure current target/record contracts; no API, source admission or authority."""
from dataclasses import fields, replace
from decimal import Decimal
from pathlib import Path
import json

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation as preparation
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_secondary_readout as target_owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment/secondary-response-target.example.json"


def target():
    return decode_canonical_bytes(EXAMPLE.read_bytes(), target_owner.MatrixE3SecondaryTarget, maximum_bytes=None)


def test_direct_scientific_target_has_only_mathematics_and_explicit_tolerance():
    current = target()
    assert tuple(field.name for field in fields(current)) == (
        "record_id", "mathematical_protocol", "normalized_adequacy_tolerance")
    mathematical = json.loads((EXAMPLE.parent / "native-training-scientific-protocol.example.json").read_bytes())["value"]["mathematical_protocol"]
    assert current.mathematical_protocol.to_document() == mathematical
    assert current.normalized_adequacy_tolerance == Decimal(".01")
    assert decode_canonical_bytes(current.canonical_bytes(), type(current), maximum_bytes=None) == current


@pytest.mark.parametrize("value", (Decimal(0), Decimal("-.01"), Decimal("NaN"),
    Decimal("Infinity"), Decimal("-Infinity"), .01, None))
def test_secondary_target_requires_an_explicit_exact_positive_finite_decimal(value):
    with pytest.raises((ValueError, TypeError)):
        replace(target(), normalized_adequacy_tolerance=value)


def test_secondary_target_requires_the_scientific_body_without_original_scaffolds():
    current = target()
    with pytest.raises(TypeError, match="exact response-task mathematical protocol"):
        replace(current, mathematical_protocol=current.mathematical_protocol.identity)
    assert not hasattr(target_owner, "capture_secondary_target")
    assert not hasattr(target_owner, "MatrixE3SecondaryTargetDocument")


@pytest.mark.parametrize("schema", (
    "empirical-lawhood/matrix-response-experiment/secondary-target-document",
    "empirical-lawhood/matrix-response-experiment/secondary-readout-selection"))
def test_old_scaffold_schemas_refuse_without_translation(schema):
    value = target().to_document()
    value["schema"] = schema
    with pytest.raises(ValueError):
        decode_canonical_bytes(canonical_json_document_bytes(value), target_owner.MatrixE3SecondaryTarget, maximum_bytes=None)


def test_current_preparation_keeps_v4_fields_without_original_request_decoder():
    current = preparation.ConfiguredProtectedE3PreparationSelection
    assert current.VERSION == "4.0.0"
    assert tuple(field.name for field in fields(current)) == (
        "selection_id", "root", "entry_package", "fit_config", "manifest", "training_allocation",
        "sources", "projections", "mathematical_protocol", "response_selection", "protocols", "panels",
        "numerical_profiles", "training_features", "training_outcomes", "formal_methods", "formal_source_inventories",
        "resource_selection", "qualifications", "source_configs", "numerical_qualifications", "numerical_containers",
        "secondary_readout", "primary_amendment")
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import (
        ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection,
        ConfiguredE3ClosedPreparationSelection,
    )
    assert preparation.configured_preparation_types() == (current, ConfiguredE3ContinuedPreparationSelection,
        ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection)
    assert not hasattr(preparation, "ConfiguredProtectedE3PreparationSelectionV2")
    assert not hasattr(preparation, "ConfiguredProtectedE3PreparationSelectionV3")
    assert tuple(field.name for field in fields(preparation.ConfiguredProtectedE3ExperimentInputs)) == (
        "selection", "files", "secondary_target")


@pytest.mark.parametrize("version", ("1.0.0", "2.0.0", "3.0.0"))
def test_old_preparation_revisions_refuse_before_any_nested_decode(version):
    raw = canonical_json_document_bytes({"schema": preparation.ConfiguredProtectedE3PreparationSelection.SCHEMA,
        "version": version, "value": {}})
    with pytest.raises(ValueError):
        decode_canonical_bytes(raw, preparation.ConfiguredProtectedE3PreparationSelection, maximum_bytes=None)


# E4's new convention is separate from the exact retained E3 target bytes.
def _e4_target():
    return target_owner.MatrixE4SecondaryTarget('target.e4.convention.disclosed', target().mathematical_protocol,
        Decimal('.01'), (Decimal('.005'), Decimal('.02'), Decimal('.05')),
        tuple(range(16, 129, 4)), Decimal('.001'))


def test_e4_target_declares_accuracy_grid_and_followup_without_selecting_tau():
    original = target().canonical_bytes()
    current = _e4_target()
    assert current.observation_horizons == tuple(range(16, 129, 4))
    assert tuple(current.primary_timestep * tick for tick in current.observation_horizons) == tuple(
        Decimal(tick) / 1000 for tick in range(16, 129, 4))
    assert current.normalized_adequacy_tolerance == Decimal('.01')
    assert current.sensitivity_tolerances == (Decimal('.005'), Decimal('.02'), Decimal('.05'))
    assert not hasattr(current, 'tau') and not hasattr(current, 'selected_horizon')
    assert decode_canonical_bytes(current.canonical_bytes(), type(current), maximum_bytes=None) == current
    assert target().canonical_bytes() == original


@pytest.mark.parametrize('field,value', (
    ('normalized_adequacy_tolerance', Decimal('.02')),
    ('normalized_adequacy_tolerance', .01),
    ('sensitivity_tolerances', (Decimal('.005'), Decimal('.05'), Decimal('.02'))),
    ('observation_horizons', (16, 64, 128)),
    ('observation_horizons', tuple(range(16, 257, 4))),
    ('primary_timestep', Decimal('.002')),
))
def test_e4_convention_refuses_retrospective_threshold_grid_and_clock_changes(field, value):
    with pytest.raises((ValueError, TypeError)):
        replace(_e4_target(), **{field: value})


def test_e4_target_refuses_old_three_point_carrier_without_relabelling_e3():
    original = target()
    with pytest.raises(ValueError):
        decode_canonical_bytes(original.canonical_bytes(), target_owner.MatrixE4SecondaryTarget, maximum_bytes=None)
    forged = original.to_document()
    forged['schema'] = target_owner.MatrixE4SecondaryTarget.SCHEMA
    with pytest.raises(ValueError):
        decode_canonical_bytes(canonical_json_document_bytes(forged), target_owner.MatrixE4SecondaryTarget, maximum_bytes=None)
    assert original.VERSION == target_owner.MatrixE3SecondaryTarget.VERSION
