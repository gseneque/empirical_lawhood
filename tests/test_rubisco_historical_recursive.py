# SPDX-License-Identifier: MPL-2.0
"""Historical graph joins and all-fold evaluation custody through the public route."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.rubisco_historical.operation_bindings import (
    operation_declarations, output_codecs,
)
from empirical_lawhood.adapters.methods.rubisco_historical.recursive_translation import historical_recursive_draft
from empirical_lawhood.adapters.methods.rubisco_historical.records import HistoricalFoldV1, HistoricalScienceV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalLabelSliceV1, HistoricalTrainingSliceV1,
    ReportedEndpointsV1, ReportedSubstitutionV1,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

ROOT = Path(__file__).resolve().parents[1]


def _inputs():
    source = ObjectIdentity("exposed-software-fixture", "empirical-lawhood/testing/reported-source", "1.0.0", "a" * 64)
    features = tuple(ReportedSubstitutionV1(sample, edit) for sample, edit in
                     (("d206e", "D206E"), ("m100t", "M100T"), ("wt", "WT")))
    endpoints = tuple(ReportedEndpointsV1(sample, Decimal(turnover), Decimal(specificity))
                      for sample, turnover, specificity in
                      (("d206e", "14.1", "12.1"), ("m100t", "10.6", "11.7"), ("wt", "13.1", "12.3")))
    folds = (HistoricalFoldV1("site100", ("d206e", "wt"), ("m100t",), "wt"),
             HistoricalFoldV1("site206", ("m100t", "wt"), ("d206e",), "wt"))
    science = HistoricalScienceV1("science.exposed-software-fixture", source, folds, features)
    slices = []
    for fold in folds:
        slices.extend((HistoricalTrainingSliceV1(f"training.{fold.fold_id}", fold.fold_id, source,
            tuple(f for f in features if f.sample_id in fold.training_sample_ids),
            tuple(e for e in endpoints if e.sample_id in fold.training_sample_ids)),
            HistoricalFeatureSliceV1(f"features.{fold.fold_id}", fold.fold_id, source,
                tuple(f for f in features if f.sample_id in fold.target_sample_ids)),
            HistoricalLabelSliceV1(f"labels.{fold.fold_id}", fold.fold_id, source,
                tuple(e for e in endpoints if e.sample_id in fold.target_sample_ids))))
    return science, tuple(sorted(slices, key=lambda value: value.slice_id))


def _compile(draft):
    return compile_recursive_wave(draft=draft, registrations=tuple(declaration.registration() for declaration in operation_declarations()),
        registry=CapabilityRegistry("registry.rubisco.historical-fixture", tuple(sorted(tuple(declaration.manifest() for declaration in operation_declarations()), key=lambda v: v.registry_id))),
        implementation_commit="a" * 40, output_codecs=output_codecs())


def test_all_folds_feed_global_commitment_and_no_labels_feed_predictors():
    draft = historical_recursive_draft(*_inputs())
    compiled = _compile(draft)
    assert len(compiled.execution_plan.tasks) == 6 and len(draft.external_inputs) == 6
    assert len([edge for edge in draft.links if edge.consumer_node_id.endswith("commit")]) == 2
    assert all(edge.scientific_role != "OUTCOME" for edge in draft.links if edge.consumer_node_id.endswith("predict"))
    assert all(registration.native_effect is False for registration in tuple(declaration.registration() for declaration in operation_declarations()))
    assert not hasattr(compiled.run_plan, "authorization")


def test_changed_root_or_removed_global_forecast_refuses_before_execution():
    draft = historical_recursive_draft(*_inputs())
    changed = replace(draft.development_study, question="A different claim about unseen enzymes")
    with pytest.raises(ValueError, match="exact analysis root"):
        _compile(replace(draft, development_study=changed))
    links = tuple(edge for edge in draft.links if not (edge.consumer_node_id.endswith("commit")
                                                    and edge.consumer_input_id.endswith("site206")))
    with pytest.raises(ValueError, match="barrier|census"):
        _compile(replace(draft, links=links))


def test_crossfold_role_swap_or_duplicate_slice_cannot_enter_frozen_draft():
    science, slices = _inputs()
    with pytest.raises(ValueError, match="repeats"):
        historical_recursive_draft(science, slices + (slices[0],))
    replacement = replace(slices[0], source=ObjectIdentity("other-source", science.source.object_schema, "1.0.0", "b" * 64))
    with pytest.raises(ValueError, match="source"):
        historical_recursive_draft(science, (replacement, *slices[1:]))


def test_historical_public_service_retains_negative_census_and_recovers_without_execution(tmp_path, monkeypatch):
    from empirical_lawhood.api import matrix_numerical_provenance as provenance_owner
    from empirical_lawhood.api import recursive_authoring as author
    from empirical_lawhood.api import recursive_execution as execute
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, FilesystemState, GuardedExternalRoot
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.runtime.artifacts import ExternalRootContract

    class Inspector:
        def inspect(self, contract):
            return FilesystemState(contract.canonical_path, True, True, 2**40, False)

    # Freeze only this software test's provenance while other developers edit.
    source = author.implementation_binding(ROOT)
    observed = provenance_owner.capture_matrix_provenance(project_root=ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(execute, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(provenance_owner, "capture_matrix_provenance", lambda **kwargs: observed)
    selected = tmp_path / "custody"
    selected.mkdir()
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "rubisco-history-test-root", "Rubisco historical software fixture", str(selected), str(selected),
        "empirical-lawhood/testing/rubisco-history-custody", 1), Inspector()))
    science, slices = _inputs()
    bindings = []
    for value in slices:
        path = selected / (value.slice_id + ".json")
        path.write_bytes(value.canonical_bytes())
        bindings.append((f"external.{value.slice_id}", path))
    directory = selected / "history"
    authored = author.author_recursive_wave(draft=historical_recursive_draft(science, slices), project_root=ROOT,
        artifact_writer=plane, output_dir=directory, input_bindings=tuple(bindings))
    assert authored["native_contact"] == "none" and authored["task_count"] == 6
    report = execute.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    product = next(iter(next(iter(report["terminal_products"].values())).values()))["value"]
    assert len(product["errors"]) == 6 and product["paired_table_contrasts"] == 2
    assert product["all_methods_identical"] is True
    assert product["independent_biological_units"] == 0
    outcomes = {error["value"]["observed"]["value"]["sample_id"]: error["value"]["jointly_within_point_tolerance"]
                for error in product["errors"]}
    assert outcomes == {"m100t": False, "d206e": True}

    def forbidden(*args, **kwargs):
        raise AssertionError("completed historical stage was executed again")

    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    retained = {**report, "native_contact": "none", "new_native_contact_count": 0}
    assert execute.read_recursive_wave(directory=directory, artifact_writer=plane) == retained
    assert execute.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane) == retained
