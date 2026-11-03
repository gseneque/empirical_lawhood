# SPDX-License-Identifier: MPL-2.0
"""Exposed software conformance; no native/biological execution or qualification."""

from dataclasses import replace
from fractions import Fraction as F
import pytest
from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism import (
    contracts as c,
    science,
    operation_bindings as owner,
    recursive_translation as drafts,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from tests.test_rubisco_nomination_preparation import parent
from tests.rubisco_nomination_fixture import mechanistic_source, nominee


@pytest.fixture(scope="module")
def stock():
    macro, dossier = nominee()
    return mechanistic_source(macro, dossier), macro, dossier


def test_full_source_balances_negative_cases_and_unknowns(stock):
    source, macro, nominee = stock
    result = science.assess(source, macro, nominee)
    assert tuple(r.case_id for r in result.cases) == c.CASE_IDS
    assert sum(r.original_matrix_checks for r in result.cases) == 70
    assert all(
        r.irreversible_specificity_invariant
        and r.expanded_specificity_shared_pregas_invariant
        for r in result.cases
    )
    assert result.biological_disposition is AssessmentDisposition.UNEVALUABLE
    assert result.source_partition_specificity_gain_upper_bound.fraction == F(100, 93)
    favourable = result.cases[-1]
    assert not favourable.source_conditional_partition_compatible
    assert not favourable.carbon_state_equilibrium_favours_putative_product
    assert result.targets[0].minimum_removable_waiting_fraction.fraction == F(21, 37)
    assert result.targets[1].minimum_removable_waiting_fraction.fraction == F(193, 273)
    assert len(result.unknown_reasons) == 6 and len(result.check4_prerequisites) == 6
    assert (
        decode_canonical_bytes(
            result.canonical_bytes(), c.MechanismAssessment, maximum_bytes=None
        )
        == result
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"physical_units": 1},
        {"biological_units": 1},
        {"mathematical_rates_are_estimates": True},
        {"case_ids": c.CASE_IDS[:-1]},
        {"primary_forward_partition": c.Exact(1, 2)},
    ],
)
def test_selection_never_prunes_or_invents_measurements(changes):
    with pytest.raises(ValueError):
        replace(c.MechanismSelection("selection.exposed-mechanism"), **changes)


def test_original_source_and_outcome_substitution_refuse(stock):
    source, macro, nominee = stock
    with pytest.raises(ValueError):
        replace(
            source.primary_sources[0], raw_utf8=source.primary_sources[0].raw_utf8 + " "
        )
    with pytest.raises(ValueError):
        replace(source, primary_sources=source.primary_sources[:-1])
    wrong = replace(nominee, product_id="product.exposed.substitution")
    with pytest.raises(ValueError, match="substitutes"):
        science.validate_inputs(source, macro, wrong)
    with pytest.raises(ValueError):
        replace(
            science.assess(source, macro, nominee),
            biological_disposition=AssessmentDisposition.SATISFIED,
        )


def test_paired_uncertainty_keeps_native_tokens_and_unknown_covariance(stock):
    result = science.assess(*stock)
    row = result.donor_uncertainty[1]
    assert row.before_native_error_token == "6.9 ± 0.2*"
    assert row.after_native_error_token == "9.5 ± 0.3**"
    assert row.mean_ratio.fraction == F(95, 69)
    assert (
        row.delta_log_ratio_variance_bounds[0].fraction
        < row.delta_log_ratio_variance_bounds[1].fraction
    )
    assert "NO_CI_OR_SIGNIFICANCE" in row.scope


@pytest.mark.parametrize(
    "rates", [(2, 3, 5, 7, 11), (1, 1, 1, 1, 1), (11, 5, 2, 1, 17)]
)
def test_first_passage_independent_exact_oracle(rates):
    k, off, a, b, r = map(F, rates)
    assert science.capture_probability(rates) == a * r / (off * (b + r) + a * r)


@pytest.mark.parametrize("release", [F(1, 100), F(1), F(100)])
def test_expanded_activation_enolization_invariance_independently(release):
    carbon = (F(2), F(3), F(5), F(0), release)
    oxygen = (F(7), F(11), F(13), F(0), release * 17)
    fc, fo = science.expanded_balance(carbon, oxygen)
    assert fc / fo * 10 == (F(2) * 5 / (3 + 5)) / (F(7) * 13 / (11 + 13))


@pytest.mark.parametrize("executor_kind", ("direct", "process"))
def test_real_registered_pure_runner_shared_scheduler_receipt_and_no_effect_recovery(
    tmp_path, stock, monkeypatch, executor_kind
):
    """Exposed parent metadata fixture; real compiler, factory, runner and custody.

    This exercises software conformance, not receipt admission of a real parent
    or biological qualification. No worker or registry is replaced by a mock.
    """
    from empirical_lawhood.api.recursive_execution import _external_inputs
    from empirical_lawhood.infrastructure.execution import (
        DirectTaskExecutor,
        LocalProcessExecutor,
        LocalScheduler,
    )
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.sql import (
        SQLiteOperationalRepository,
        create_catalog_engine,
        upgrade_catalog,
    )
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from tests.runtime_platform.test_execution_scheduler import (
        StaticExternalInputResolver,
    )
    from tests.test_recursive_public_service import _plane

    source, macro, outcome = stock
    draft = drafts.challenge_draft(source, macro, outcome, parent=parent(outcome))
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.execution import RunnerRegistry

    registrations, registry, codecs = (
        tuple(declaration.registration() for declaration in owner.operation_declarations()),
        CapabilityRegistry("registry.exposed-mechanism", tuple(declaration.manifest() for declaration in owner.operation_declarations())),
        owner.output_codecs(),
    )
    compiled = compile_recursive_wave(
        draft=draft,
        registrations=registrations,
        registry=registry,
        implementation_commit="1" * 40,
        output_codecs=codecs,
    )
    plan, run = compiled.execution_plan, compiled.run_plan
    runners = RunnerRegistry(
        (owner.MechanismRunner(),), registry_sha256=registry.fingerprint()
    )
    selected = runners.resolve(plan.tasks[0])
    assert type(selected) is owner.MechanismRunner
    assert selected.manifest == tuple(declaration.manifest() for declaration in owner.operation_declarations())[0]
    assert selected.manifest == registry.resolve(
        owner.NODE, selected.manifest.capability_version
    )
    plane = _plane(tmp_path / "exposed-pure-nomination-custody")
    payloads = {value.config_id: value.payload for value in compiled.config_inputs}
    payloads.update(
        {
            "source": source.canonical_bytes(),
            "macro": macro.canonical_bytes(),
            "outcome": outcome.canonical_bytes(),
        }
    )
    inputs = _external_inputs(
        plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=False
    )
    index = DevelopmentRunRecoveryIndex.from_execution_plan(
        plan,
        run_id=run.run_plan_id,
        wave_id="wave.exposed-pure-nomination",
        authority_identities=(),
    )
    recovery, receipts = (
        ExternalRunRecoveryStore(plane),
        ExternalTaskReceiptStore(plane),
    )
    engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    scheduler = LocalScheduler(
        operational_repository=repository,
        artifact_writer=plane,
        receipt_store=receipts,
        recovery_index=index,
        recovery_store=recovery,
        runner_registry=runners,
        implementation_commit="1" * 40,
        external_input_resolver=StaticExternalInputResolver(inputs),
        executor=(
            DirectTaskExecutor()
            if executor_kind == "direct"
            else LocalProcessExecutor(scratch_root=plane.root)
        ),
        input_port_factory=plane,
        lane=PlanLane.DEVELOPMENT,
        authorized_barriers=(),
        assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,
    )
    try:
        result = scheduler.execute(run.run_plan_id, plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert result.completed_task_ids == (owner.NODE,)
        assert len(result.receipts) == 1
        receipt = result.receipts[0]
        raw = plane.root.resolve(
            receipt.output_materializations[0].relative_path, for_write=False
        ).read_bytes()
        dossier = decode_canonical_bytes(raw, c.MechanismAssessment, maximum_bytes=None)
        science.validate_assessment(dossier, macro, outcome)
        assert dossier.biological_disposition is AssessmentDisposition.UNEVALUABLE
        assert (
            len(dossier.cases) == 5
            and sum(r.original_matrix_checks for r in dossier.cases) == 70
        )
        assert set(receipt.input_materialization_ids) == {
            r.materialization.materialization_id for r in inputs
        }

        from copy import deepcopy
        from hashlib import sha256
        from empirical_lawhood.infrastructure.recursive_custody import (
            read_recursive_products,
        )
        from empirical_lawhood.kernel.recursive_requirements import ContributionRole

        products = read_recursive_products(
            plane=plane,
            plan=plan,
            index=index,
            external_inputs=inputs,
            output_codecs=owner.output_codecs(),
        )
        contribution = drafts.describe_contributions(draft, products)[0]
        assert contribution.products[0].role is ContributionRole.RETAINED_ANALYSIS_INPUT
        records = (source, macro, outcome)
        by_schema = {r.SCHEMA: r for r in records}
        meaning = {
            "external-"
            + sha256(r.input_id.encode()).hexdigest()[:24]
            + ".json": by_schema[r.payload_schema].canonical_bytes()
            for r in draft.external_inputs
        }
        assert len(drafts.inquiry_evidence_projector(draft, meaning, products)) == 4
        assert drafts.next_wave_builder(draft, contribution, products) is None
        logical = receipt.output_logical_artifacts[0].logical_artifact_id
        for damage in (
            "missing-receipt",
            "changed-path",
            "changed-storage",
            "changed-digest",
            "changed-record",
        ):
            changed = deepcopy(products)
            if damage == "missing-receipt":
                del changed["receipts"][owner.NODE]
            elif damage == "changed-record":
                changed["records"][owner.NODE][owner.NODE + ".product"] = replace(
                    dossier, source_partition_specificity_gain_upper_bound=c.Exact(2, 1)
                )
            else:
                manifest = changed["outputs"][logical]
                values = {
                    "changed-path": {"relative_path": "unattested/elsewhere.json"},
                    "changed-storage": {"storage_root_id": "storage.unattested"},
                    "changed-digest": {"physical_sha256": "d" * 64},
                }[damage]
                changed["outputs"][logical] = replace(
                    manifest,
                    materialization=replace(manifest.materialization, **values),
                )
            with pytest.raises((ValueError, KeyError)):
                drafts.describe_contributions(draft, changed)
        for damage in ("cases", "unknown_reasons"):
            with pytest.raises(ValueError):
                replace(dossier, **{damage: getattr(dossier, damage)[:-1]})

        def forbidden(*args, **kwargs):
            raise AssertionError("completed pure operation entered again")

        monkeypatch.setattr(selected, "execute", forbidden)
        assert scheduler.execute(run.run_plan_id, plan).receipts == result.receipts
    finally:
        engine.dispose()


def test_cold_registered_factory_and_all_existing_runners_without_native_imports():
    import subprocess
    import sys

    probe = """
import importlib.abc
import sys
class NoNative(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0]=='pybamm':
            raise AssertionError('cold mechanism discovery imports native battery')
sys.meta_path.insert(0,NoNative())
from empirical_lawhood.api.recursive_operations import operation_factories
from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism.executable_binding import EXECUTABLE_BINDING_FACTORIES
from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism.extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import RunnerRegistry
factories={f.manifest.registry_id:f for f in (*operation_factories(),*EXECUTABLE_BINDING_FACTORIES)}
registry=CapabilityRegistry('registry.exposed-cold-mechanism',tuple(sorted((f.manifest for f in factories.values()),key=lambda m:m.registry_id)))
runners=RunnerRegistry(tuple(f.runner_factory() for f in sorted(factories.values(),key=lambda f:f.manifest.registry_id)),registry_sha256=registry.fingerprint())
assert tuple(r.manifest for r in runners._runners)==registry.capabilities
assert tuple(f.manifest for f in EXECUTABLE_BINDING_FACTORIES)==EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests
assert all(callable(r.execute) for r in runners._runners)
assert 'pybamm' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", probe], check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
