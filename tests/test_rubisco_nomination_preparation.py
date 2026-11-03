# SPDX-License-Identifier: MPL-2.0
"""Exposed pure conformance only; no biological assay or actual qualification."""

from dataclasses import replace
from hashlib import sha256
import json
from types import SimpleNamespace as N
import pytest
from empirical_lawhood.adapters.methods.rubisco_nomination_preparation import (
    contracts as c,
    science,
    operation_bindings as owner,
    recursive_translation as drafts,
)
from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import (
    assessment,
    recursive_translation as cycle_drafts,
)
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import (
    science as portfolio,
)
from empirical_lawhood.kernel.decoding import (
    decode_canonical_bytes,
)
from empirical_lawhood.kernel.evidence import (
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition,
    AssessmentPhase,
    ContributionRole,
)
from empirical_lawhood.kernel.scientific_contributions import (
    ContributionManifest,
    ContributionProduct,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import WorkerInputKind
from tests.test_inquiry_successor_compilation import compile_complete_draft
from tests.rubisco_nomination_fixture import proposal, sources


@pytest.fixture(scope="module")
def stock():
    mechanism, macro = sources()
    model = assessment.supply(mechanism)
    query = cycle_drafts.instance_from_source(
        macro,
        instance_id="instance.exposed-nomination.first",
        candidate_ids=("gp.wt", "wilson2017-row17"),
    )
    return macro, assessment.assess_use(model, macro, query)


@pytest.fixture(scope="module")
def preparation(stock):
    macro, outcome = stock
    candidate = next(
        r
        for r in portfolio.complete_candidate_roster(macro)
        if r.candidate_id == c.CANDIDATE_ID
    )
    selected_members, assay = proposal()
    members = list(selected_members)
    # Rebind only the proposed material ID in this exposed software copy; original files are never edited.
    material = next(m for m in members if m.filename == "construct-options.json")
    doc = json.loads(material.raw_utf8)
    doc["proposed_material_id"] = "material.exposed.gp-i95m-proposed-m1"
    raw = json.dumps(doc, sort_keys=True)
    members[members.index(material)] = replace(
        material, raw_utf8=raw, source_sha256=sha256(raw.encode()).hexdigest()
    )
    return science.preparation_from_source(
        macro,
        outcome,
        proposed_material_id="material.exposed.gp-i95m-proposed-m1",
        source_ssu_view=candidate.ssu_sequence_views[0][0],
        source_members=members,
        assay=assay,
        conditional_rationale="Conditional source-bound hypothesis only, no measured mutant/microrate relation.",
        adverse_rationale="Unknown mutant endpoints, processing/assembly and model transport.",
        decision_provenance="Exposed software fixture selects exploratory test, no assay or submission.",
    )


def test_exposed_operands_relocate_without_session_or_producer_access(
    tmp_path, monkeypatch
):
    import importlib.util
    from pathlib import Path
    import shutil
    from tests import rubisco_nomination_fixture as fixture

    selected = tmp_path / "selected-source-fixture"
    selected.mkdir()
    helper = selected / "rubisco_nomination_fixture.py"
    shutil.copyfile(fixture.__file__, helper)
    shutil.copytree(
        Path(fixture.__file__).parent / "fixtures/rubisco/nomination",
        selected / "fixtures/rubisco/nomination",
    )
    spec = importlib.util.spec_from_file_location("relocated_nomination_fixture", helper)
    relocated = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(relocated)
    read_bytes = Path.read_bytes

    def selected_read(path):
        if not path.is_relative_to(selected):
            raise AssertionError("portable fixture reads outside its selected source")
        return read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", selected_read)
    mechanism, macro = relocated.sources()
    members, assay = relocated.proposal()
    assert len(mechanism.sources) == 2 and len(macro.sources) == 34
    assert tuple((m.role, m.filename) for m in members) == c.SOURCE_CENSUS
    assert assay.status == "PROPOSED_NOT_ENTERED"
    assert assay.physical_independent_units == 0 and not assay.actual_assay_ids


def parent(outcome):
    product = ContributionProduct(
        "product.exposed-nomination.prior-outcome",
        c.identity(outcome),
        ArtifactIdentity(
            "artifact.exposed-nomination.prior",
            "scientific-product",
            outcome.SCHEMA,
            outcome.fingerprint(),
            "application/json",
            len(outcome.canonical_bytes()),
        ),
        ObjectIdentity(
            "receipt.exposed-nomination",
            "empirical-lawhood/testing/exposed-receipt",
            "1.0.0",
            "a" * 64,
        ),
        ContributionRole.INSTANCE_PRODUCT,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
    )
    return ContributionManifest(
        "contribution.exposed-nomination",
        "Exposed conditional outcome",
        "Metadata fixture only.",
        outcome.scope,
        (product,),
        (c.identity(outcome),),
        (),
    )


def test_cold_installed_factories_and_nomination_runner_have_exact_manifests_without_native_imports():
    import subprocess
    import sys

    probe = """
import importlib.abc
import json
import sys
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'pybamm':
            raise AssertionError('cold recursive discovery imports PyBaMM')
sys.meta_path.insert(0, RefuseNative())
from empirical_lawhood.api.recursive_operations import operation_catalog, operation_factories
from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.executable_binding import EXECUTABLE_BINDING_FACTORIES
_, registry, _ = operation_catalog()
assert tuple(sorted((f.manifest for f in operation_factories()), key=lambda m: m.registry_id)) == registry.capabilities
factory, = EXECUTABLE_BINDING_FACTORIES
runner = factory.runner_factory()
assert runner.manifest == factory.manifest == registry.resolve(factory.manifest.capability_key, factory.manifest.capability_version)
assert callable(runner.execute)
print(json.dumps({'count': len(registry.capabilities), 'keys': [r.capability_key for r in registry.capabilities], 'native_imported': 'pybamm' in sys.modules}))
"""
    result = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    census = json.loads(result.stdout)
    assert census["count"] == len(census["keys"])
    assert owner.NODE in census["keys"]
    assert not census["native_imported"]


@pytest.mark.parametrize("executor_kind", ("direct", "process"))
def test_real_registered_pure_runner_shared_scheduler_receipt_and_no_effect_recovery(
    tmp_path, stock, preparation, monkeypatch, executor_kind
):
    """Exposed parent metadata fixture; real compiler, factory, runner and custody.

    This exercises software conformance, not receipt admission of a real parent
    or biological qualification. No worker or registry is replaced by a mock.
    """
    from empirical_lawhood.api.recursive_execution import _external_inputs
    from empirical_lawhood.api.recursive_operations import (
        operation_catalog,
        operation_runners,
    )
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
    from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
    from tests.test_recursive_public_service import _plane

    macro, outcome = stock
    draft = drafts.preparation_draft(
        preparation, macro, outcome, parent=parent(outcome)
    )
    registrations, registry, codecs = operation_catalog()
    compiled = compile_recursive_wave(
        draft=draft,
        registrations=registrations,
        registry=registry,
        implementation_commit="1" * 40,
        output_codecs=codecs,
    )
    plan, run = compiled.execution_plan, compiled.run_plan
    runners = operation_runners(registry=registry, plan=plan)
    selected = runners.resolve(plan.tasks[0])
    assert type(selected) is owner.NominationRunner
    assert selected.manifest == tuple(declaration.manifest() for declaration in owner.operation_declarations())[0]
    assert selected.manifest == registry.resolve(
        owner.NODE, selected.manifest.capability_version
    )
    plane = _plane(tmp_path / "exposed-pure-nomination-custody")
    payloads = {value.config_id: value.payload for value in compiled.config_inputs}
    payloads.update({
        "preparation": preparation.canonical_bytes(),
        "macro": macro.canonical_bytes(),
        "outcome": outcome.canonical_bytes(),
    })
    inputs = _external_inputs(
        plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=False
    )
    index = DevelopmentRunRecoveryIndex.from_execution_plan(
        plan, run_id=run.run_plan_id,
        wave_id="wave.exposed-pure-nomination", authority_identities=(),
    )
    recovery, receipts = ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane)
    engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
    upgrade_catalog(engine)
    repository = SQLiteOperationalRepository(engine)
    scheduler = LocalScheduler(
        operational_repository=repository, artifact_writer=plane,
        receipt_store=receipts, recovery_index=index, recovery_store=recovery,
        runner_registry=runners, implementation_commit="1" * 40,
        external_input_resolver=StaticExternalInputResolver(inputs),
        executor=(DirectTaskExecutor() if executor_kind == "direct" else
                  LocalProcessExecutor(scratch_root=plane.root)), input_port_factory=plane,
        lane=PlanLane.DEVELOPMENT, authorized_barriers=(),
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
        dossier = decode_canonical_bytes(raw, c.NominationDossier, maximum_bytes=None)
        science.validate_dossier(dossier, macro, outcome)
        assert dossier.biological_disposition is AssessmentDisposition.UNEVALUABLE
        assert len(dossier.target_findings) == 12
        assert set(receipt.input_materialization_ids) == {
            r.materialization.materialization_id for r in inputs
        }
        def forbidden(*args, **kwargs):
            raise AssertionError("completed pure operation entered again")
        monkeypatch.setattr(selected, "execute", forbidden)
        assert scheduler.execute(run.run_plan_id, plan).receipts == result.receipts
    finally:
        engine.dispose()


def test_concrete_dossier_keeps_exact_material_complete_unknowns_and_negative_targets(
    stock, preparation
):
    macro, outcome = stock
    dossier = science.prepare(preparation, macro, outcome)
    assert dossier.preparation.source_ssu_view == "m1"
    assert (
        len(dossier.preparation.proposed_m1_ssu_sequence)
        == len(dossier.preparation.reported_ssu_sequence)
        == 138
    )
    assert (
        dossier.preparation.proposed_m1_ssu_sequence
        == dossier.preparation.reported_ssu_sequence
    )
    assert dossier.disposition is AssessmentDisposition.SATISFIED
    assert dossier.biological_disposition is AssessmentDisposition.UNEVALUABLE
    assert (
        dossier.conditional_mechanism_denominator == 864
        and len(dossier.target_findings) == 12
    )
    unknown = [r for r in dossier.target_findings if r.candidate_id == "gp.i95m"]
    assert len(unknown) == 2 and all(
        r.turnover_s_inv is None
        and r.specificity is None
        and r.historical_point_joint_pass is None
        for r in unknown
    )
    assert any(r.historical_point_joint_pass is False for r in dossier.target_findings)
    assert (
        dossier.preparation.assay.status == "PROPOSED_NOT_ENTERED"
        and not dossier.preparation.assay.actual_assay_ids
    )
    assert (
        decode_canonical_bytes(
            dossier.canonical_bytes(), c.NominationDossier, maximum_bytes=None
        )
        == dossier
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"measured_mutant_turnover_s_inv": __import__("decimal").Decimal("9")},
        {"measured_mutant_specificity": __import__("decimal").Decimal("300")},
        {"target_biology": "QUALIFIED"},
        {"biological_qualification": True},
        {"submitted": True},
    ],
)
def test_unsupported_measured_qualified_and_submission_claims_refuse(
    preparation, changes
):
    with pytest.raises(ValueError, match="promotes"):
        replace(preparation, **changes)


def test_fake_assay_entry_and_omitted_endpoint_refuse(preparation):
    for changes in (
        {"actual_assay_ids": ("assay.fake",)},
        {"physical_independent_units": 1},
        {"status": "ENTERED"},
        {"endpoints": ("turnover",)},
    ):
        with pytest.raises(ValueError, match="fabricate"):
            replace(preparation.assay, **changes)


def test_scientific_source_census_and_full_material_views_cannot_be_pruned(preparation):
    for changes in (
        {
            "source_members": tuple(
                m
                for m in preparation.source_members
                if m.filename != "gp-expression-patent.html"
            )
        },
        {"source_ssu_view": "invented-processing-view"},
        {"reported_ssu_sequence": preparation.reported_ssu_sequence[:-1]},
    ):
        with pytest.raises(ValueError, match="source census|substitutes material view"):
            replace(preparation, **changes)


def test_material_and_prior_outcome_substitution_refuse(stock, preparation):
    macro, outcome = stock
    swapped = replace(outcome, product_id="product.exposed.changed-prior")
    with pytest.raises(ValueError, match="swaps exact"):
        science.prepare(preparation, macro, swapped)
    changed = replace(preparation, lsu_sequence="A" + preparation.lsu_sequence[1:])
    with pytest.raises(ValueError, match="material mismatches"):
        science.prepare(changed, macro, outcome)


def test_complete_ledger_and_unknown_model_reasons_cannot_be_pruned(stock, preparation):
    dossier = science.prepare(preparation, *stock)
    with pytest.raises(ValueError, match="denominator"):
        replace(dossier, target_findings=dossier.target_findings[:-1])
    with pytest.raises(ValueError, match="model unknowns"):
        replace(dossier, prior_model_reason_codes=())
    with pytest.raises(ValueError, match="denominator"):
        replace(dossier, conditional_mechanism_denominator=1)
    row = dossier.target_findings[2]
    altered = replace(row, turnover_ratio=row.turnover_ratio + 1)
    tampered = replace(
        dossier,
        target_findings=tuple(
            altered if r is row else r for r in dossier.target_findings
        ),
    )
    with pytest.raises(ValueError, match="changes source/model"):
        science.validate_dossier(tampered, *stock)


def changed_document(preparation, filename, change):
    """A coherently rehashed source still must satisfy independent science checks."""
    member = next(m for m in preparation.source_members if m.filename == filename)
    document = json.loads(member.raw_utf8)
    change(document)
    raw = json.dumps(document, sort_keys=True)
    replacement = replace(
        member, raw_utf8=raw, source_sha256=sha256(raw.encode()).hexdigest()
    )
    return replace(
        preparation,
        source_members=tuple(
            replacement if m == member else m for m in preparation.source_members
        ),
    )


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        (lambda d: d["adverse_witnesses"].pop(), "case denominator"),
        (
            lambda d: d["donor_nominal_witness"].update(
                turnover_multiplier={"fraction": "2", "decimal": "2"}
            ),
            "independently derived response",
        ),
        (
            lambda d: d["donor_nominal_witness"]["stationary_oracle_checks"][0].update(
                exact_flux={"fraction": "1", "decimal": "1"}
            ),
            "independent exact state balance",
        ),
        (
            lambda d: d.update(implementation_source_sha256="f" * 64),
            "reproduction script identity",
        ),
        (
            lambda d: d["donor_source"].update(panel_sha256="f" * 64),
            "original contrast substitution",
        ),
    ],
)
def test_rehashed_conditional_source_cannot_replace_or_prune_evidence(
    stock, preparation, change, refusal
):
    altered = changed_document(preparation, "exact-conditional-rationale.json", change)
    with pytest.raises(ValueError, match=refusal):
        science.prepare(altered, *stock)


def test_rehashed_material_or_assay_document_cannot_replace_selected_design(
    stock, preparation
):
    altered = changed_document(
        preparation,
        "construct-options.json",
        lambda d: d.update(proposed_material_id="material.other.proposed"),
    )
    with pytest.raises(ValueError, match="material document mismatches"):
        science.prepare(altered, *stock)
    altered = changed_document(
        preparation,
        "paired-assay-proposal.json",
        lambda d: d["value"].update(actual_assay_ids=["assay.fabricated"]),
    )
    with pytest.raises(ValueError, match="fabricate"):
        science.prepare(altered, *stock)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["designs"][0]["full_circular_plasmid"].update(
            sequence_ascii="A" * 4992
        ),
        lambda d: d["designs"][0]["coding_features"][2].update(
            translation_ascii="M" * 138
        ),
        lambda d: d["designs"][0]["coding_features"].pop(),
        lambda d: d["designs"][0].update(expression_qualified=True),
        lambda d: d["helper_original_CDS"].update(
            coding_DNA_ascii="ATG" + "AAA" * 133 + "TAA"
        ),
    ],
)
def test_independent_complete_construct_guard_refuses_rehashed_design(
    stock, preparation, change
):
    altered = changed_document(
        preparation, "sequence-defined-construction.json", change
    )
    document = json.loads(
        next(
            m.raw_utf8
            for m in altered.source_members
            if m.filename == "sequence-defined-construction.json"
        )
    )
    altered = changed_document(
        altered,
        "construct-options.json",
        lambda d: d.update(complete_construction=document),
    )
    with pytest.raises(ValueError, match="construction"):
        science.prepare(altered, *stock)


def test_native_backbone_source_cannot_be_coherently_rehashed(preparation):
    member = next(
        m
        for m in preparation.source_members
        if m.filename == "pUC19-M77789.2-original.embl"
    )
    raw = member.raw_utf8 + "\n"
    counterfeit = replace(
        member, raw_utf8=raw, source_sha256=sha256(raw.encode()).hexdigest()
    )
    with pytest.raises(ValueError, match="original construction source bytes"):
        replace(
            preparation,
            source_members=tuple(
                counterfeit if m == member else m for m in preparation.source_members
            ),
        )


def test_pure_registered_singleton_compiles_and_retains_real_parent_role(
    stock, preparation
):
    macro, outcome = stock
    draft = drafts.preparation_draft(
        preparation, macro, outcome, parent=parent(outcome)
    )
    result = compile_complete_draft(draft, owner)
    assert not tuple(declaration.registration() for declaration in owner.operation_declarations())[0].native_effect
    assert (
        next(
            r for r in draft.external_inputs if r.input_id.endswith("cycle-outcome")
        ).scientific_role
        == "OUTCOME"
    )
    assert draft.requirements[0].scope == outcome.scope
    assert result.execution_plan.tasks[0].capability.capability_key == owner.NODE
    bad = replace(
        draft,
        external_inputs=tuple(
            replace(r, scientific_role="SOURCE")
            if r.input_id.endswith("cycle-outcome")
            else r
            for r in draft.external_inputs
        ),
    )
    with pytest.raises(ValueError):
        compile_complete_draft(bad, owner)


def test_pure_worker_exact_inputs_no_path_side_effect_and_fake_prior_refusal(
    stock, preparation
):
    macro, outcome = stock
    draft = drafts.preparation_draft(
        preparation, macro, outcome, parent=parent(outcome)
    )
    config = decode_canonical_bytes(
        draft.operations[0].config_payload.encode(),
        c.NominationOperationConfig,
        maximum_bytes=None,
    )

    def ctx(prior):
        inputs = tuple(
            N(
                payload_schema=r.SCHEMA,
                size_bytes=len(r.canonical_bytes()),
                media_type="application/json",
                kind=WorkerInputKind.EXTERNAL,
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                read=r.canonical_bytes,
                close=lambda: None,
            )
            for r in (config, preparation, macro, prior)
        )
        return N(
            task_id=owner.NODE,
            permissions=tuple(declaration.manifest() for declaration in owner.operation_declarations())[0].permissions,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            resource_budget=owner.BUDGET,
            input_ports=inputs,
            config=N(config_id=config.config_id, content_sha256=config.fingerprint()),
            output_ports=(
                N(
                    output_id=owner.NODE + ".product",
                    payload_schema=c.NominationDossier.SCHEMA,
                    profile=ArtifactProfile.CANONICAL_JSON,
                    media_type="application/json",
                ),
            ),
        )

    result = owner.NominationRunner().execute(ctx(outcome))
    assert decode_canonical_bytes(
        result.outputs[0].payload, c.NominationDossier, maximum_bytes=None
    ) == science.prepare(preparation, macro, outcome)
    with pytest.raises(ValueError, match="exact source or prior"):
        owner.NominationRunner().execute(
            ctx(replace(outcome, product_id="product.exposed.wrong"))
        )


def test_four_phases_assess_proposal_compatibility_without_biological_promotion(
    stock, preparation
):
    macro, outcome = stock
    draft = drafts.preparation_draft(
        preparation, macro, outcome, parent=parent(outcome)
    )
    dossier = science.prepare(preparation, macro, outcome)
    rows = owner.project_assessments(
        dossier, draft.requirements[0], draft.connections[0]
    )
    assert tuple(r.phase for r in rows) == tuple(AssessmentPhase) and all(
        r.disposition is AssessmentDisposition.SATISFIED for r in rows
    )
    assert dossier.biological_disposition is AssessmentDisposition.UNEVALUABLE
