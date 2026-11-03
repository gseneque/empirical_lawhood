# SPDX-License-Identifier: MPL-2.0
"""Conditional Rubisco execution, source binding and retained-history falsifiers."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.rubisco_feedback.assay_binding import (
    AssayRunProduct, assay_claim, assay_declaration,
)
from empirical_lawhood.adapters.methods.rubisco_feedback.recursive_translation import assay_recursive_draft
from empirical_lawhood.adapters.simulators.rubisco_assay.fixture import historical_r1_config
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.adapters.simulators.rubisco_assay.science import run_assay
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

ROOT = Path(__file__).resolve().parents[1]


def _config():
    return historical_r1_config(plan_sha256="a" * 64)


def _compile(draft):
    registry = CapabilityRegistry("registry.rubisco.assay-test", (assay_declaration().manifest(),))
    return compile_recursive_wave(draft=draft, registrations=(assay_declaration().registration(),), registry=registry,
        implementation_commit="a" * 40, output_codecs={AssayRunProduct.SCHEMA: AssayRunProduct})


def test_recursive_assay_preserves_complete_units_queries_and_nonpromotable_claim():
    config = _config()
    draft = assay_recursive_draft(config)
    compiled = _compile(draft)
    assert len(compiled.execution_plan.tasks) == 1
    assert len(assay_declaration().registration().native_effect_slot_ids(config)) == 12
    assert draft.development_study.assigned_unit_ids == tuple(case.case_id for case in config.cases)
    assert draft.development_study.claims[0].requested_rung is None
    assert not hasattr(compiled.run_plan, "authorization")
    projections, evaluation = run_assay(config)
    product = AssayRunProduct(ObjectIdentity.from_record(config.config_id, config), projections, evaluation, 12)
    assert product.numerical_query_count == 12
    assert product.independent_biological_unit_count == 0
    assert product.biological_prediction_established is False


def test_correct_branch_rates_with_rank_deficiency_do_not_satisfy_the_rank_four_claim():
    from empirical_lawhood.kernel.status import ScientificStatus

    config = _config()
    one_probe = replace(config, initial_fixed_queries=config.initial_fixed_queries[:1], rounds_per_case=1,
                        maximum_native_calls=len(config.cases))
    projections, evaluation = run_assay(one_probe)
    assert all(p.maximum_relative_forecast_error <= one_probe.numerical_relative_tolerance for p in projections)
    assert all(p.log_sensitivity_rank == 2 for p in projections)
    assert "rank-four" in assay_claim().proposition
    assert evaluation.scientific_status is ScientificStatus.NOT_SUPPORTED
    assert "CONDITIONAL_LOCAL_INFORMATION_RANK_DEFICIENT" in evaluation.reason_codes


def test_later_feedback_does_not_redefine_the_initial_probe_rank_claim():
    import numpy as np

    from empirical_lawhood.adapters.simulators.rubisco_assay.core import log_sensitivity
    from empirical_lawhood.kernel.status import ScientificStatus

    config = _config()
    two_probes = replace(config, initial_fixed_queries=(config.initial_fixed_queries[0], config.initial_fixed_queries[2]))
    projections, evaluation = run_assay(two_probes)
    assert all(p.maximum_relative_forecast_error <= config.numerical_relative_tolerance for p in projections)
    assert all(p.log_sensitivity_rank == 3 for p in projections)
    for case, projection in zip(two_probes.cases, projections, strict=True):
        complete_queries = tuple(result.realized_query.native() for result in projection.source_results)
        assert np.linalg.matrix_rank(log_sensitivity(case.native(), complete_queries), tol=1e-10) == 4
    assert "frozen initial probe design has rank-four" in assay_claim().proposition
    assert evaluation.scientific_status is ScientificStatus.NOT_SUPPORTED


@pytest.mark.parametrize("change", ("proposition", "units", "views", "operands"))
def test_recursive_assay_refuses_changed_scientific_root_before_contact(change):
    draft = assay_recursive_draft(_config())
    study = draft.development_study
    if change == "proposition":
        study = replace(study, claims=(replace(study.claims[0], proposition="An unseen enzyme was predicted"),))
    elif change == "units":
        study = replace(study, assigned_unit_ids=study.assigned_unit_ids + ("unassigned-case",))
    elif change == "views":
        study = replace(study, numerical_view_ids=("unrelated-view",))
    else:
        study = replace(study, scientific_operands=())
    with pytest.raises(ValueError, match="scientific|census|scope"):
        _compile(replace(draft, development_study=study))


def test_assay_product_refuses_mixed_evaluation_source_or_truncated_rounds():
    config = _config()
    projections, evaluation = run_assay(config)
    identity = ObjectIdentity.from_record(config.config_id, config)
    other = ObjectIdentity.from_record("other.assay", replace(config, config_id="other.assay"))
    with pytest.raises(ValueError, match="source/configuration"):
        AssayRunProduct(identity, projections, replace(evaluation, config=other), 12)
    with pytest.raises(ValueError, match="census"):
        AssayRunProduct(identity, projections, evaluation, 11)
    with pytest.raises(ValueError, match="source/configuration|case_ids"):
        AssayRunProduct(identity, (projections[0], projections[0]), evaluation, 12)
    with pytest.raises(ValueError, match="biological"):
        AssayRunProduct(identity, projections, evaluation, 12, independent_biological_unit_count=False)
    shortened = replace(projections[0], source_results=projections[0].source_results[:-1],
        branch_rates=projections[0].branch_rates[:-1], specificity_estimates=projections[0].specificity_estimates[:-1])
    changed = (shortened, projections[1])
    changed_evaluation = replace(evaluation, source_reports=tuple(
        ObjectIdentity.from_record(value.report_id, value) for value in changed))
    with pytest.raises(ValueError, match="round census"):
        AssayRunProduct(identity, changed, changed_evaluation, 11)
    substituted = replace(projections[0].source_results[1], prior_commitment=ObjectIdentity.from_record(
        projections[1].source_results[0].result_id, projections[1].source_results[0]))
    broken = replace(projections[0], source_results=(projections[0].source_results[0], substituted,
                                                    *projections[0].source_results[2:]))
    changed = (broken, projections[1])
    changed_evaluation = replace(evaluation, source_reports=tuple(
        ObjectIdentity.from_record(value.report_id, value) for value in changed))
    with pytest.raises(ValueError, match="complete committed"):
        AssayRunProduct(identity, changed, changed_evaluation, 12)


def test_assay_product_refuses_rebased_gases_after_a_different_committed_query():
    from decimal import Decimal

    config = _config()
    projections, evaluation = run_assay(config)
    original = projections[0].source_results
    query = AssayQuery(Decimal(999), original[1].realized_query.o2_um, Decimal(1))
    changed = replace(original[1], requested_query=query, accepted_query=query, applied_query=query, realized_query=query)
    # Rebind downstream predecessor identities so this is a scientific action
    # inconsistency rather than merely a stale digest.
    results = [original[0], changed]
    for result in original[2:]:
        results.append(replace(result, prior_commitment=ObjectIdentity.from_record(results[-1].result_id, results[-1])))
    broken = replace(projections[0], source_results=tuple(results))
    changed_projections = (broken, projections[1])
    changed_evaluation = replace(evaluation, source_reports=tuple(
        ObjectIdentity.from_record(value.report_id, value) for value in changed_projections))
    with pytest.raises(ValueError, match="complete committed"):
        AssayRunProduct(ObjectIdentity.from_record(config.config_id, config), changed_projections, changed_evaluation, 12)


def test_registered_assay_executes_and_recovers_without_reacquisition(tmp_path, monkeypatch):
    from empirical_lawhood.api import matrix_numerical_provenance as provenance_owner
    from empirical_lawhood.api import recursive_authoring as author
    from empirical_lawhood.api import recursive_execution as execute
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, FilesystemState, GuardedExternalRoot
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.runtime.artifacts import ExternalRootContract

    class Inspector:
        def inspect(self, contract):
            return FilesystemState(contract.canonical_path, True, True, 2**40, False)

    source = author.implementation_binding(ROOT)
    observed = provenance_owner.capture_matrix_provenance(project_root=ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(execute, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(provenance_owner, "capture_matrix_provenance", lambda **kwargs: observed)
    selected = tmp_path / "custody"
    selected.mkdir()
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "rubisco-test-root", "Rubisco software fixture", str(selected), str(selected),
        "empirical-lawhood/testing/rubisco-custody", 1), Inspector()))
    directory = selected / "assay"
    authored = author.author_recursive_wave(draft=assay_recursive_draft(_config()), project_root=ROOT,
        artifact_writer=plane, output_dir=directory)
    assert authored["native_contact"] == "none" and authored["task_count"] == 1
    report = execute.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 1
    product = next(iter(next(iter(report["terminal_products"].values())).values()))["value"]
    assert product["numerical_query_count"] == 12 and product["independent_biological_unit_count"] == 0

    def forbidden(*args, **kwargs):
        raise AssertionError("retained conditional assay was reacquired")

    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    retained = {**report, "native_contact": "none", "new_native_contact_count": 0}
    assert execute.read_recursive_wave(directory=directory, artifact_writer=plane) == retained
    assert execute.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane) == retained
