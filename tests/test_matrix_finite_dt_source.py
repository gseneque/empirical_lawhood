# SPDX-License-Identifier: MPL-2.0
"""Disclosed pure certificate controls; fabricated pins confer no real custody."""
from dataclasses import replace
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as r
from empirical_lawhood.adapters.methods import matrix_finite_dt_source_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseBank
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, ExecutionPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case


def _unexecuted(name, kind):
    return ObjectIdentity("unexecuted.disclosed." + name, kind.SCHEMA, kind.VERSION, "a" * 64)


def _control(case, index, *, available):
    source = train.source_for(case.request, case.specification.root_ids[index], index=case.source.index)
    protocol, = (value for value in case.request.protocols if value.public_source.root.root_id == source.root_id)
    branch_count = len(branch_census(protocol, train.panels_for(case.request, source)))
    return r.MatrixFiniteDtRootControl(source.root_id, source.root.root.independent_group_id, scheduled.identity(source),
        _unexecuted(str(index) + ".prefix", train.NativeTrainingPrefixHistory),
        _unexecuted(str(index) + ".numerical", train.NativeTrainingNumericalAssessment),
        _unexecuted(str(index) + ".causal", train.NativeTrainingCausalPrefix),
        _unexecuted(str(index) + ".frames", train.NativeTrainingFrameAssessment),
        _unexecuted(str(index) + ".physical", train.NativeTrainingPhysicalForecast),
        _unexecuted(str(index) + ".responses", train.NativeTrainingResponse),
        _unexecuted(str(index) + ".score", train.NativeTrainingScore),
        (_unexecuted(str(index) + ".receipt", CanonicalTaskReceipt),), True, available, False, available,
        branch_count if available else 0, "AVAILABLE" if available else "NO_ORIGIN", "COMPLETED" if available else "NO_ORIGIN")


def _certificate(case, controls):
    source = train.source_for(case.request, case.specification.root_ids[0], index=case.source.index)
    locator = r.MatrixFiniteDtTrainingLocator("unexecuted.disclosed", "run.unexecuted.disclosed",
        _unexecuted("packet", AuthoredRecursiveWave), _unexecuted("plan", DevelopmentExecutionPlan))
    return r.MatrixFiniteDtInstrumentCertificate(
        record_id="certificate.unexecuted.disclosed", locator=locator,
        specification=case.specification.identity, request=case.request.identity,
        acquisition=train.acquisition_seal(case.specification, case.request).identity,
        original_future_reservation=scheduled.identity(case.request.future_manifest.reservation),
        measurement=case.specification.measurement, numerical=scheduled.identity(source.numerical_design),
        factor_numerical=scheduled.identity(source.policy.factor_numerical_design),
        instrument_sha256=r.instrument_signature(case.request.protocols[0]), criterion=case.request.mathematical_protocol.identity,
        provenances=(source.provenance.identity,), templates=tuple(sorted({value.templates.array_artifact for value in case.request.protocols},
            key=lambda value: value.artifact_id)), training_effective_seeds=tuple(sorted({stream.effective_seed for root in
                case.request.train_manifest.reservation.allocation.roots for stream in root.streams})), controls=controls,
        reserved_future_effective_seeds=tuple(sorted({stream.effective_seed for root in
            case.request.future_manifest.reservation.allocation.roots for stream in root.streams})),
        future_bank=_unexecuted("future-bank", SelectedE4PhaseBank), future_group_ids=("future.group.disclosed",),
        cutoff=InformationCutoff("cutoff.disclosed", source.root.root.clock_id, CausalPhase.PREPARATION, None))


def test_instrument_certificate_preserves_nonuse_without_equating_it_to_violated_controls(tmp_path):
    case = fresh_training_metadata_case(tmp_path, training_count=2)
    available, nonuse = _control(case, 0, available=True), _control(case, 1, available=False)
    certificate = _certificate(case, (available, nonuse))
    assert certificate.instrument_checks_pass
    assert tuple(value.causal_disposition for value in certificate.controls) == ("AVAILABLE", "NO_ORIGIN")
    assert not replace(certificate, controls=(replace(available, frame_controls_pass=False), nonuse)).instrument_checks_pass
    assert not replace(certificate, controls=(available, replace(nonuse, frame_controls_violated=True))).instrument_checks_pass
    assert not replace(certificate, controls=(replace(available, prefix_controls_pass=False), nonuse)).instrument_checks_pass
    assert not replace(certificate, controls=(replace(available, response_controls_pass=False), nonuse)).instrument_checks_pass
    assert not _certificate(case, (_control(case, 0, available=False), nonuse)).instrument_checks_pass
    assert all(value in certificate.original_evidence_links for value in (available.score, nonuse.score, *available.receipts, *nonuse.receipts))


def test_certificate_cannot_relabel_raw_train_or_claim_continuum_and_requires_development_plan(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    certificate = _certificate(case, (_control(case, 0, available=True),))
    with pytest.raises(ValueError, match="instrument-only"):
        replace(certificate, standing="CONTINUUM_BOUND_OR_SAMPLING_QUALIFIED")
    with pytest.raises(ValueError, match="exposure"):
        replace(certificate, prerequisite_outcome_access=OutcomeAccess.OUTCOME_BLIND)
    with pytest.raises(ValueError, match="typed scientific"):
        replace(certificate.locator, execution_plan=_unexecuted("issued-plan", ExecutionPlan))
    with pytest.raises(PermissionError, match="current API custody"):
        bindings.prepare_for_invocation(object(), bindings.MatrixFiniteDtGateWorker(r.GATES[0]))


@pytest.mark.parametrize("changed", ("source", "lock", "runtime", "commit"))
def test_instrument_certificate_requires_exact_current_producing_provenance(changed):
    # Literal disclosed provenance exercises equality only. It is no observed
    # implementation, real TRAIN receipt or scientific qualification.
    observation = dict(python="TEST", numpy="TEST", scipy="TEST",
        system="TEST", machine="TEST", threadpools=[])
    sources = (("__init__.py", sha256(b"# disclosed ordinary source\n").hexdigest()),)
    current = NumericalProducingProvenance(json.dumps(observation, sort_keys=True), "a" * 64, sources,
        sha256(canonical_json_bytes(sources)).hexdigest(), "b" * 40, False)
    certificate = SimpleNamespace(provenances=(current.identity,))
    r.require_checked_implementation(certificate, SimpleNamespace(provenances=(current,)))
    if changed == "source":
        other_sources = (("__init__.py", sha256(b"# changed ordinary source\n").hexdigest()),)
        other = replace(current, package_sources=other_sources,
            code_sources_sha256=sha256(canonical_json_bytes(other_sources)).hexdigest())
    elif changed == "lock":
        other = replace(current, dependency_lock_sha256="c" * 64)
    elif changed == "runtime":
        other = replace(current, runtime_observation_json=json.dumps(dict(observation, numpy="CHANGED"), sort_keys=True))
    else:
        other = replace(current, observed_git_head="d" * 40)
    with pytest.raises(ValueError, match="actually checked numerical implementation"):
        r.require_checked_implementation(certificate, SimpleNamespace(provenances=(other,)))


def test_installed_source_gate_methods_keep_stage_contract_and_existing_replay_owners():
    from empirical_lawhood.adapters.methods.matrix_source_bindings import source_declarations, PIPELINE_KEY, QUALIFICATION_KEY
    from empirical_lawhood.runtime.candidate_compiler import _ALLOWED_STAGE_KINDS
    declarations = source_declarations()
    assert tuple(value.capability_key for value in declarations[:2]) == (PIPELINE_KEY, QUALIFICATION_KEY)
    assert {value.capability_key for value in declarations[2:]} == {
        *(r.NAMESPACE + "." + kind.value.lower() for kind in r.GATES), r.NAMESPACE + ".adjudicate",
        *("matrix-source.prepared-finite-dt." + phase + "." + kind.value.lower()
            for phase in ("e5_confirmation", "e6_transfer") for kind in r.GATES)}
    for declaration in declarations:
        assert declaration.manifest().kind in _ALLOWED_STAGE_KINDS[declaration.stage]
    assert all(value.execution_properties.runner_preparation_factory is not None for value in declarations[2:-1])


def test_public_finite_dt_specification_stops_at_actual_source_selection_dependency(tmp_path):
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_experiment as domain
    from empirical_lawhood.api.experiment_preparation import load_experiment_specification, prepare_experiment
    from empirical_lawhood.api.domain_composition.matrix_finite_dt_source.experiment_binding import EXPERIMENT_RUNTIME_BINDING
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection
    specification = domain.MatrixFiniteDtSourceQualificationSpecification("spec.disclosed.source-first-stop",
        _unexecuted("source-selection", domain.MatrixFiniteDtSourceQualificationSelection), 4)
    path = tmp_path / "copied-source-specification.json"
    path.write_bytes(specification.canonical_bytes())
    actual = load_experiment_specification(path)
    assert actual == specification
    report = prepare_experiment(actual, execution=ExecutionSelection(workers=4))
    assert report.draft is None and report.census.native_effect_count == 0
    assert report.census.role_counts == ()  # Unselected future-group census is unknown.
    assert tuple((value.code, value.kind, value.source_key) for value in report.dependencies) == (
        ("matrix.finite-dt.source-selection", DependencyKind.EXTERNAL_INPUT, "selection"),)
    assert EXPERIMENT_RUNTIME_BINDING.protocol_id == domain.PROTOCOL_ID
    assert EXPERIMENT_RUNTIME_BINDING.prepare_authoring is not None
    assert EXPERIMENT_RUNTIME_BINDING.read_result is not None


def test_pending_source_metadata_cannot_predict_future_validity_or_erase_nonuse():
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_pipeline import MatrixFiniteDtPendingSourceRow
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
    row = MatrixFiniteDtPendingSourceRow("root.disclosed.pending", "group.disclosed.pending", _unexecuted("pending-source", ScheduledSource))
    assert row.invalid_disposition == "ASSIGNED_NATIVE_ACQUISITION_NOT_YET_OBSERVED"
    for changes in ({"invalid_disposition": "ALL_FUTURE_TRAJECTORIES_VALID"},
            {"requested_action_status": "ALL_ACTIONS_SUCCEEDED"}, {"receiver_status": "TARGET_OBSERVED"}):
        with pytest.raises(ValueError, match="future outcome|nonuse"):
            replace(row, **changes)



def test_instrument_signature_preserves_labels_but_detects_declared_tolerance_changes(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    protocol = case.request.protocols[0]
    actual = r.instrument_signature(protocol)
    assert r.instrument_signature(replace(protocol, protocol_id=protocol.protocol_id + ".alias")) == actual
    assert r.instrument_signature(replace(protocol,
        native_reference_tolerance=protocol.native_reference_tolerance * 2)) != actual
    assert r.instrument_signature(replace(protocol,
        hessian_reference_tolerance=protocol.hessian_reference_tolerance * 2)) != actual



@pytest.mark.parametrize("replacement", ((), (True,), (2, 1), (1, 1), (-1,)))
def test_instrument_certificate_requires_exact_separate_reserved_future_stream_keys(tmp_path, replacement):
    case = fresh_training_metadata_case(tmp_path)
    certificate = _certificate(case, (_control(case, 0, available=True),))
    with pytest.raises(ValueError, match="original exposure|instrument-only"):
        replace(certificate, reserved_future_effective_seeds=replacement)
    with pytest.raises(ValueError, match="original exposure|instrument-only"):
        replace(certificate, reserved_future_effective_seeds=(certificate.training_effective_seeds[0],))
