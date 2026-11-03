# SPDX-License-Identifier: MPL-2.0
"""Exposed method nomination and fresh public lifecycle software conformance.

The numerical coefficient, adjudication outcomes and signers are synthetic.
The development construction uses the actual selected worker. These tests do
not qualify any real scientific method.
"""

from dataclasses import dataclass, replace
from pathlib import Path
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.authority import AuthorityAction
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.exploration import (
    Hypothesis, HypothesisDisposition, HypothesisSet, OutcomeInterpretation,
    OutcomeInterpretationKind, ProspectiveNomination,
)
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole, DesignOrigin, DesignOriginKind
from empirical_lawhood.runtime.execution import RunnerRegistry, RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import Config, fixture as development_fixture
from tests.runtime_platform import test_recursive_prospective_workflow as public


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class _ExposedMethod(CanonicalRecord):
    """An inspected development product with its unchanged producing receipt."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/recursive-exposed-method'
    method_id: str
    method: ObjectIdentity
    producing_receipt: ObjectIdentity
    coefficient: int
    assigned_unit_ids: tuple[str, ...]
    evidence_ceiling: EvidenceCeiling = EvidenceCeiling.NON_PROMOTABLE
    outcome_access: OutcomeAccess = OutcomeAccess.DEVELOPMENT_VISIBLE
    visibility_ceiling: VisibilityCeiling = VisibilityCeiling.OUTCOME_VISIBLE


class _MethodRunner:
    """A reviewed synthetic operation; constructor captures no study records."""

    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, context):
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from tests.runtime_platform.test_recursive_compiler import SourceConfig, UseConfig

        config_type = SourceConfig if context.task_id == 'source' else UseConfig
        config_port = next(port for port in context.input_ports if port.payload_schema == config_type.SCHEMA)
        config = decode_canonical_bytes(config_port.read(), config_type, maximum_bytes=10_000)
        if context.task_id == 'use':
            operand_port = next(port for port in context.input_ports if port.payload_schema == Config.SCHEMA)
            operand = decode_canonical_bytes(operand_port.read(), Config, maximum_bytes=10_000)
            assert operand.scalar == config.scalar
        product = Config('method.' + context.task_id, config.scalar)
        return RunnerResult(tuple(TaskOutputPayload(port.output_id, product.canonical_bytes())
                                  for port in context.output_ports),
                            (ReceiptCheck('synthetic-developed-method', True, ()),))


def _develop_method(tmp_path, monkeypatch):
    """Acquire the old exposed product through actual generic DEV custody."""
    from empirical_lawhood.api import recursive_authoring as author
    from empirical_lawhood.api import recursive_execution as execute
    from tests.test_recursive_public_service import _plane

    draft, registrations, registry = development_fixture()
    # The constructor fixture's1MB ceiling cannot run a spawned CPython worker.
    # Select a feasible exposed worker budget and retain actual enforcement.
    budget = replace(registrations[0].resource_ceiling, memory_bytes=2 * 1024**3,
                     wall_time_seconds=120)
    registrations = tuple(replace(row, resource_ceiling=budget) for row in registrations)
    registry = replace(registry, capabilities=tuple(replace(row, resource_ceiling=budget)
        for row in registry.capabilities))
    draft = replace(draft, operations=tuple(replace(row, resource_budget=budget) for row in draft.operations))
    # The method construction has no scientific assessment requirement. Its
    # exact source-to-method port remains in the scientific and task graphs.
    draft = replace(draft, requirements=(), connections=(), suppliers=(),
                    links=tuple(replace(link, requirement_id=None, connection_id=None) for link in draft.links))
    from threadpoolctl import threadpool_limits
    # Load the selected numerical libraries before observing their actual pool
    # configuration. The synthetic method itself never calls a native solver.
    __import__('scipy.linalg')
    with threadpool_limits(limits=1):
        from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
        capture_numerical_provenance(project_root=ROOT)
    plane = _plane(tmp_path / 'exposed-development')
    directory = Path(plane.root.contract.canonical_path) / 'authored-method'
    runners = RunnerRegistry(tuple(_MethodRunner(manifest) for manifest in registry.capabilities),
                             registry_sha256=registry.fingerprint())
    with monkeypatch.context() as patch:
        composition = (registrations, registry, {Config.SCHEMA: Config})
        patch.setattr(author, 'operation_catalog', lambda: composition)
        patch.setattr(execute, 'operation_catalog', lambda: composition)
        patch.setattr(execute, 'operation_runners', lambda **kwargs: runners)
        authored = author.author_recursive_wave(draft=draft, project_root=ROOT,
                                                artifact_writer=plane, output_dir=directory)
        result = execute.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
        retained, products, _, _ = execute.read_recursive_wave(directory=directory,
                                                   artifact_writer=plane, include_products=True)
    assert authored['task_count'] == result['task_count'] == 2
    assert result['status'] == 'SUCCEEDED', result['task_census']
    assert result['scientific_authority'] == 'NONE' and result['qualification'] == 'NOT_ESTABLISHED'
    assert result['native_contact'] == 'none' and result == retained
    assert all(claim.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE for claim in draft.development_study.claims)
    method = products['records']['use']['use.result']
    receipt = products['receipts']['use']
    logical = receipt.output_logical_artifacts[0]
    assert logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    method_view = _ExposedMethod('method.inspected-development', ObjectIdentity.from_record(method.config_id, method),
                   ObjectIdentity.from_record(receipt.receipt_id, receipt), method.scalar,
                   draft.development_study.assigned_unit_ids)
    # Retain the inspection view separately; do not overwrite the old product or
    # increase the evidential role of its completion receipt.
    (directory / 'inspected-method.json').write_bytes(method_view.canonical_bytes())
    preserved = (method.canonical_bytes(), receipt.canonical_bytes(), draft.development_study.canonical_bytes())
    return method_view, directory, products, preserved


def _nominate(compilation, method, destination):
    """Build the existing advisory nomination with exact developed-method bytes."""
    study = compilation.candidate_draft
    experiment = study.experiment
    hypotheses = HypothesisSet('hypotheses.exposed-method', (method.method.object_id,), (
        Hypothesis('hypothesis.method', 'The frozen coefficient can work on separate assigned units.',
                   HypothesisDisposition.PREFERRED, (method.method.object_id,),
                   'Fresh held-out evaluation opposes the procedure.', 'Independent protected evidence.'),
        Hypothesis('hypothesis.overfit', 'The inspected coefficient reflects the exposed development unit.',
                   HypothesisDisposition.UNRESOLVED, (method.method.object_id,),
                   'Independent evaluation supports the frozen procedure.', 'Independent protected evidence.'),
    ), OutcomeAccess.DEVELOPMENT_VISIBLE, (VisibilityCeiling.OUTCOME_VISIBLE,), VisibilityCeiling.OUTCOME_VISIBLE)
    nomination = ProspectiveNomination('nomination.exposed-method', ObjectIdentity.from_record(hypotheses.hypothesis_set_id, hypotheses),
        experiment.relation, 'Can the frozen exposed method qualify on independently assigned protected evidence?',
        tuple(hypothesis.hypothesis_id for hypothesis in hypotheses.hypotheses), experiment.assignment,
        experiment.measurement_quantity_ids, tuple(item.falsifier_id for item in experiment.obligations.falsifiers),
        study.system.authority_policy.required_gate_ids, experiment.precision_goals,
        tuple(sorted((OutcomeInterpretation('interpretation.' + kind.value.lower(), kind,
                         'Apply the frozen synthetic evaluator criterion for ' + kind.value.lower() + '.')
                      for kind in OutcomeInterpretationKind), key=lambda item: item.interpretation_id)),
        AuthorityAction.REFERENCE_WORLD_EXECUTION, True, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.OUTCOME_VISIBLE, VisibilityCeiling.OUTCOME_VISIBLE,
        ('Stop if the original exposed unit enters the evaluation roster.',))
    for name, record in (('hypotheses', hypotheses), ('nomination', nomination)):
        (destination / (name + '.json')).write_bytes(record.canonical_bytes())
    cutoff = study.design_inputs[0].information_cutoff
    motivation = DesignInputRecord('input.exposed-method', ObjectIdentity.from_record(method.method_id, method),
           method.fingerprint(), cutoff, DesignInputRole.MOTIVATION, method.outcome_access,
           method.visibility_ceiling, 'human.owner', method.assigned_unit_ids)
    hypothesis_input = DesignInputRecord('input.exposed-hypotheses', nomination.source_hypothesis_set,
           hypotheses.fingerprint(), cutoff, DesignInputRole.MOTIVATION, hypotheses.outcome_access,
           hypotheses.visibility_ceiling, 'human.owner', parent_input_ids=(motivation.input_id,))
    nomination_input = DesignInputRecord('input.nomination', ObjectIdentity.from_record(nomination.nomination_id, nomination),
           nomination.fingerprint(), cutoff, DesignInputRole.MOTIVATION, nomination.outcome_access,
           nomination.visibility_ceiling, 'human.owner', parent_input_ids=(hypothesis_input.input_id,))
    inputs = tuple(sorted((*study.design_inputs, motivation, hypothesis_input, nomination_input), key=lambda item: item.input_id))
    origin = DesignOrigin('origin.exposed-method-nomination', DesignOriginKind.PROSPECTIVE_NOMINATION,
             tuple(item.input_id for item in inputs), VisibilityCeiling.OUTCOME_VISIBLE,
             ObjectIdentity.from_record(nomination.nomination_id, nomination), True)
    from tests.runtime_platform.test_candidate_compiler import _replace_candidate_experiment
    study = _replace_candidate_experiment(study, replace(experiment, design_visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE))
    study = replace(study, design_origin=origin, design_inputs=inputs,
                    development_unit_ids=tuple(sorted({*study.development_unit_ids, *method.assigned_unit_ids})))
    return study, nomination, inputs


def _install_nomination(monkeypatch, method, destination, *, change=None):
    original = public._actual_source
    captured = {}
    def nominated(compilation):
        compilation, _, _, raw, source_config = original(compilation)
        study, nomination, inputs = _nominate(compilation, method, destination)
        if change is not None:
            study = change(study)
            inputs = study.design_inputs
        draft = replace(compilation.draft, prospective_draft=study, campaign=study.campaign)
        compiled = compile_recursive_wave(draft=draft, registrations=public._registrations(compilation),
             registry=compilation.registry, implementation_commit='a' * 40,
             qualifications=compilation.candidate_context.qualifications,
             known_design_inputs=inputs, output_codecs=compilation.output_codecs)
        captured.update(compilation=compiled, nomination=nomination, method=method)
        assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
        from tests.experiment_entry_support import standard_authoring_for_draft
        standard, formal = standard_authoring_for_draft(compiled.candidate_draft, compiled.candidate_context,
                                       formal_method_capability_key='recursive-fixture.evaluate')
        return compiled, standard, formal, raw, source_config
    monkeypatch.setattr(public, '_actual_source', nominated)
    return captured


def _nominated_public_run(tmp_path, monkeypatch, *, sealed_fixture=None, reveal_terminal=True):
    """Return the actual nomination-derived public run for later parent reuse."""
    from empirical_lawhood.adapters.reference_worlds.runtime import ReferenceAdjudicationFixture
    from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
    from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability

    method, original_directory, products, preserved = _develop_method(tmp_path, monkeypatch)
    fresh = tmp_path / 'fresh'
    fresh.mkdir()
    accepted = sealed_fixture or ReferenceAdjudicationFixture('fixture.fresh-synthetic-supported', AdjudicationEvaluability.EVALUABLE,
                           ScientificStatus.SUPPORTED, AdmissionStatus.ADMITTED, ('SYNTHETIC_PARENT_SUPPORTED',))
    # Restore the fixture's source constructor after this earlier study. A later
    # consumer must author its own independent source/unit/evaluator cohort.
    with monkeypatch.context() as patch:
        captured = _install_nomination(patch, method, tmp_path)
        run = public._public_run_handoff_fixture(fresh, patch, sealed_fixture=accepted,
                    exercise_reveal_stop=True, reveal_terminal=reveal_terminal)
    return run, method, original_directory, products, preserved, captured


def test_exposed_development_method_nomination_qualifies_only_distinct_protected_test_world_evidence(tmp_path, monkeypatch):
    from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus

    run, method, original_directory, products, preserved, captured = _nominated_public_run(tmp_path, monkeypatch)
    candidate = run.handoff.compilation.candidate_report.candidate
    origin = candidate.design_origin
    assert origin.kind is DesignOriginKind.PROSPECTIVE_NOMINATION and origin.requests_fresh_child
    assert origin.nomination == ObjectIdentity.from_record(captured['nomination'].nomination_id, captured['nomination'])
    assert candidate.experiment.design_visibility_ceiling is VisibilityCeiling.OUTCOME_VISIBLE
    assert all(claim.visibility_ceiling is VisibilityCeiling.PROSPECTIVE for claim in candidate.experiment.claims)
    assert all(method.coefficient == config.record.scalar for config in run.handoff.compilation.config_inputs)
    draft = run.handoff.compilation.candidate_draft
    assert set(method.assigned_unit_ids).isdisjoint(draft.evaluation_unit_ids)
    assert set(draft.development_seed_ids).isdisjoint(draft.evaluation_seed_ids)
    assert run.executor.invocations == 5
    assert run.adjudication.scientific_status is ScientificStatus.SUPPORTED
    assert run.adjudication.admission_status is AdmissionStatus.ADMITTED
    assert run.adjudication.outcome_access is OutcomeAccess.EVALUATION_REVEALED
    assert run.adjudication.visibility_ceiling is VisibilityCeiling.OUTCOME_VISIBLE
    assert run.qualification_receipt.receipt_id != method.producing_receipt.object_id
    assert run.raw != products['records']['use']['use.result'].canonical_bytes()
    assert method.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
    assert method.visibility_ceiling is VisibilityCeiling.OUTCOME_VISIBLE
    assert (original_directory / 'inspected-method.json').read_bytes() == method.canonical_bytes()
    assert products['records']['use']['use.result'].canonical_bytes() == preserved[0]
    assert products['receipts']['use'].canonical_bytes() == preserved[1]
    assert captured['compilation'].candidate_report.candidate is not None


@pytest.mark.parametrize('case', ['no-fresh-child', 'exposed-unit', 'tuning-seed', 'claim-from-exposed-outcomes'])
def test_nomination_cannot_make_exposed_evidence_fresh_before_publication(tmp_path, monkeypatch, case):
    from empirical_lawhood.runtime.candidate_compiler import CandidateDiagnosticCode

    method, _, _, _ = _develop_method(tmp_path, monkeypatch)
    def change(study):
        if case == 'no-fresh-child':
            return replace(study, design_origin=replace(study.design_origin, requests_fresh_child=False))
        if case == 'exposed-unit':
            return replace(study, evaluation_unit_ids=method.assigned_unit_ids)
        if case == 'tuning-seed':
            return replace(study, evaluation_seed_ids=study.development_seed_ids)
        return replace(study, design_inputs=tuple(replace(item, role=DesignInputRole.CLAIM_DERIVATION)
                        if item.input_id == 'input.exposed-method' else item for item in study.design_inputs))
    captured = _install_nomination(monkeypatch, method, tmp_path, change=change)
    destination = tmp_path / 'refused'
    destination.mkdir()
    with pytest.raises(AssertionError):
        public._authored_handoff_fixture(destination, monkeypatch)
    report = captured['compilation'].candidate_report
    assert report.candidate is None
    assert CandidateDiagnosticCode.OUTCOME_SEPARATION_REQUIRED in {item.code for item in report.diagnostics}
    assert not tuple(destination.rglob('authoring/authored-wave.json'))
    assert not tuple(destination.rglob('runs/*/tasks/*'))
    assert method.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
