# SPDX-License-Identifier: MPL-2.0
"""Tiny declaration/missing-input controls, with no worker or native entry."""

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_functional_bindings as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_functional_experiment as public
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection


def reference(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, "a" * 64)


def test_functional_declarations_reuse_actual_native_owners_and_add_one_pure_consumer():
    declarations = method.operation_declarations()
    assert len(declarations) == 11 and len({row.capability_key for row in declarations}) == 11
    assert sum(row.registration().native_effect for row in declarations) == 2
    history = next(row for row in declarations if row.capability_key.endswith(".history"))
    history_runner = history.provider_factory().runner_factory()
    assert type(history_runner) is method.prediction.source_owner.MatrixPreparationNativeRunner
    assert history_runner.manifest == history.manifest()
    assert history_runner.manifest.capability_key == method.NAMESPACE + ".history"
    assert callable(history_runner.execute_with_native_subwork)
    assert history.registration().native_work_preparer is method.prediction.source_owner.prepare_native_work
    final = next(row for row in declarations if row.capability_key.endswith(".nominate"))
    assert not final.registration().native_effect
    final_runner = final.provider_factory().runner_factory()
    assert type(final_runner) is method.MatrixPreparedFunctionalRunner
    assert final_runner.manifest == final.manifest()
    assert final_runner.manifest.capability_key == method.NAMESPACE + ".nominate"
    assert not callable(getattr(final_runner, "execute_with_native_subwork", None))
    assert {row.output_id for row in final.outputs} == {"manifest", "product"}
    assert all(row.scientific_hooks.scientific_root_validator is method.scientific_root_validator for row in declarations)


def test_functional_public_missing_inputs_keep_complete16x3_plan_census(monkeypatch):
    specification = public.MatrixPreparedFunctionalExperimentSpecification("experiment.literal-functional-missing",
        reference("selection.literal-functional-missing", method.MatrixPreparedFunctionalSelection),
        reference("assay.literal-functional-missing", public.MatrixPreparedAssayProgramme),
        reference("campaign.literal-functional-missing", CampaignSpec), 16, 48)

    def forbidden(*args, **kwargs):
        raise AssertionError("missing-input preparation entered an outcome reduction or graph lowering")

    monkeypatch.setattr(method.functional, "nominate_prepared_opportunity", forbidden)
    monkeypatch.setattr(method, "lower_prepared_functional", forbidden)
    prepared = public.prepare_functional_experiment(specification, scientific_inputs={}, execution=ExecutionSelection())
    assert not prepared.executable and prepared.draft is None
    assert prepared.census.native_effect_count == 96
    assert dict(prepared.census.operation_counts)["nominate"] == 1
    assert sum(value for _, value in prepared.census.operation_counts) == 434
    assert dict(prepared.census.output_counts) == {"array-products": 240, "canonical-products": 435}
    assert {row.source_key for row in prepared.dependencies if row.code.endswith(".missing")} == {"selection", "assay", "campaign"}
    with pytest.raises(ValueError, match="scope"):
        replace(specification, scope="LABELLED_FRESH_OR_QUALIFIED")


def test_functional_public_binder_refuses_unknown_roles_or_owners():
    with pytest.raises(TypeError, match="exact declared"):
        public.bind_functional_inputs(object(), {}, files={})
