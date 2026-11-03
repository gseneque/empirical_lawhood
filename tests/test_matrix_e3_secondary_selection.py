# SPDX-License-Identifier: MPL-2.0
"""Direct scientific target publications and cold selectors; no acquisition."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation as preparation
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_secondary_readout as domain
from empirical_lawhood.api import configured_e3_secondary_target as owner
from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs, load_experiment_inputs, load_experiment_specification
from empirical_lawhood.infrastructure import source_closure
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding, ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_configured_protected_public_preparation import prepared_case

ROOT = Path(__file__).parents[1]
PROTOCOL = "matrix.response-error.configured-protected-v2"


@pytest.fixture(scope="module")
def originals(tmp_path_factory):
    """Complete disclosed current inputs; no original/request conversion."""
    return prepared_case(tmp_path_factory.mktemp("current-secondary-controls"))


def published(writer, record, name):
    target = type(record) is domain.MatrixE3SecondaryTarget
    return writer.write(ArtifactWriteRequest(name, "secondary-controls/" + name + ".json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", name, "secondary-controls", record.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY if target else VisibilityCeiling.PROSPECTIVE, (),
        OutcomeAccess.DEVELOPMENT_VISIBLE if target else OutcomeAccess.OUTCOME_BLIND))


def current_selection(case):
    return case.specification, case.selection


def target_for(case, name):
    return domain.MatrixE3SecondaryTarget("target.secondary." + name, case.mathematical_protocol, Decimal(".01"))


def test_direct_target_preserves_primary_and_actual_source_inputs(originals):
    case = originals
    specification, current = current_selection(case)
    before = current.canonical_bytes()
    target = target_for(case, "capture")
    assert target.values() == Decimal(".01") != specification.measurement.target_discrepancy_tolerance
    assert decode_canonical_bytes(target.canonical_bytes(), type(target), maximum_bytes=None) == target
    publication = published(case.plane, target, "target.secondary.capture")
    output = domain.bind_secondary_selection(current, target, publication)
    assert type(output) is preparation.ConfiguredProtectedE3PreparationSelection
    assert output.VERSION == "4.0.0" and output.SCHEMA == current.SCHEMA
    assert decode_canonical_bytes(output.canonical_bytes(), type(output), maximum_bytes=None) == output
    assert current.canonical_bytes() == before
    for name in ("fit_config", "manifest", "training_allocation", "sources", "projections", "mathematical_protocol", "response_selection",
            "protocols", "panels", "numerical_profiles", "training_features", "training_outcomes", "primary_amendment"):
        assert getattr(output, name) == getattr(current, name), name
    assert output.root.system == current.root.system and output.root.experiment == current.root.experiment
    assert owner.authenticate_secondary_target(writer=case.plane, selection=output) == (Decimal(".01"), target.identity)
    assert domain.bind_secondary_selection(output, target, publication) == output
    assert output.secondary_readout.publication.logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert output.secondary_readout.publication.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert b"normalized_adequacy_tolerance" not in output.canonical_bytes()
    with pytest.raises(ValueError, match="actual frozen scientific root"):
        replace(output, root=current.root, entry_package=current.entry_package)
    with pytest.raises(ValueError, match="actual complete DEV target publication"):
        replace(output.secondary_readout, publication=replace(publication,
            logical=replace(publication.logical, outcome_access=OutcomeAccess.OUTCOME_BLIND,
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE)))
    changed = replace(target, normalized_adequacy_tolerance=Decimal(".02"))
    with pytest.raises(ValueError, match="already frozen"):
        domain.bind_secondary_selection(output, changed, published(case.plane, changed, "target.secondary.changed"))


def test_foreign_mathematics_refuses_before_target_publication(originals):
    case = originals
    _, current = current_selection(case)
    target = target_for(case, "foreign")
    changed = replace(target, mathematical_protocol=replace(target.mathematical_protocol, protocol_id="protocol.foreign-target"))
    with pytest.raises(ValueError, match="response-task mathematics"):
        changed.validate_selection(current)
    before = case.plane.root.resolve("secondary-controls/foreign.json", for_write=False)
    assert not before.exists()


def test_corrupt_actual_published_target_refuses_before_any_point_science(originals):
    case = originals
    _, current = current_selection(case)
    target = target_for(case, "corrupt")
    publication = published(case.plane, target, "target.secondary.corrupt")
    selected = domain.bind_secondary_selection(current, target, publication)
    path = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        path.write_bytes(b"corrupt")
        with pytest.raises((ValueError, RuntimeError)):
            owner.selected_secondary_target(selected=SimpleNamespace(design_records=((selected.selection_id, selected),)), writer=case.plane)
    finally:
        path.write_bytes(raw)


def test_missing_secondary_selection_has_no_inferred_tolerance(originals):
    _, current = current_selection(originals)
    class Forbidden:
        def __getattr__(self, name):
            pytest.fail("missing secondary target contacted publication or science: " + name)
    assert current.secondary_readout is None
    assert owner.authenticate_secondary_target(writer=Forbidden(), selection=current) is None


def test_foreign_preparation_refuses_without_target_access():
    class Forbidden:
        def __getattr__(self, name):
            pytest.fail("foreign preparation contacted publication or science: " + name)
    with pytest.raises(TypeError, match="exact current configured preparation"):
        owner.authenticate_secondary_target(writer=Forbidden(), selection=object())


def test_public_loader_derive_and_replay_freeze_direct_target_before_authoring(originals, monkeypatch):
    case = originals
    specification, current = current_selection(case)
    target = target_for(case, "public")
    plane = Path(case.plane.root.contract.canonical_path)
    bindings = []
    for key, record, field in (("protected-selection", current, "selection_id"), ("secondary-target", target, "record_id")):
        path = plane / ("secondary-public-" + key + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record(getattr(record, field), record), path.name, len(record.canonical_bytes())))
    files = tuple(ExperimentFileInputBinding(key, value.identity, value.record_version, value.path.relative_to(plane).as_posix(), value.maximum_bytes)
        for key, value in sorted(case.files.items()))
    selector = ExperimentFileInputSelection("sources.secondary.public", PROTOCOL, tuple(sorted(bindings, key=lambda row: row.key)), files)
    source = plane / "secondary-public-sources.json"
    source.write_bytes(selector.canonical_bytes())
    specification_path = plane / "secondary-public-specification.json"
    specification_path.write_bytes(specification.canonical_bytes())
    specification = load_experiment_specification(specification_path)
    pending = load_experiment_inputs(specification, source)
    assert pending.method_inputs.secondary_target == target
    captures, capture = [], source_closure.capture_admitted_target_source
    def observe_source(root):
        observed = capture(root)
        captures.append(observed)
        return observed
    monkeypatch.setattr(source_closure, "capture_admitted_target_source", observe_source)
    selected_execution = ExecutionSelection(workers=4)
    output = plane / "secondary-public-derived.json"
    def derive_once():
        return derive_experiment_inputs(specification_path=specification_path, source_selection_path=source,
            project_root=ROOT, artifact_writer=case.plane, metadata_directory=plane / "secondary-public-metadata",
            output_selection_path=output, execution=selected_execution)
    result = derive_once()
    assert len(captures) == 1
    reopened = load_experiment_inputs(specification, result.source_selection_path)
    successor = reopened.method_inputs.selection
    assert type(successor) is preparation.ConfiguredProtectedE3PreparationSelection
    assert successor.secondary_readout.target == target.identity
    assert successor.training_features == current.training_features and successor.training_outcomes == current.training_outcomes
    assert successor.fit_config == current.fit_config and successor.manifest == current.manifest
    assert reopened.method_inputs.secondary_target is None
    assert tuple(row.key for row in result.source_selection.bindings) == ("protected-selection",)
    before = output.read_bytes()
    replay = derive_once()
    assert len(captures) == 2 and captures[0] is not captures[1]
    assert output.read_bytes() == before and replay.source_selection == result.source_selection
    assert load_experiment_inputs(specification, replay.source_selection_path) == reopened
    assert owner.authenticate_secondary_target(writer=case.plane, selection=successor) == (Decimal(".01"), target.identity)


def test_existing_e4_recipe_accepts_current_pin_and_preserves_family_refusals(originals):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_bank_recipe import SelectedE4BankRecipe
    from tests.test_matrix_selected_e4_bank_recipe import recipe, reference
    _, current = current_selection(originals)
    target = target_for(originals, "e4-join")
    successor = domain.bind_secondary_selection(current, target, published(originals.plane, target, "target.secondary.e4-join"))
    selected_recipe = replace(recipe(), original_preparation=ObjectIdentity.from_record(successor.selection_id, successor),
        original_public_package=reference("original.configured-public-package", ConfiguredMatrixSelectedPublicPackage))
    assert decode_canonical_bytes(selected_recipe.canonical_bytes(), SelectedE4BankRecipe, maximum_bytes=None) == selected_recipe
    with pytest.raises(ValueError, match="mixes original preparation/predictor families"):
        replace(selected_recipe, original_public_package=recipe().original_public_package)
