# SPDX-License-Identifier: MPL-2.0
"""Additive development-locator shape controls, never source qualification."""

from dataclasses import fields, replace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_entry_v2 as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as binding
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedEntryEvidence, validate_selected_entry_evidence
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
from tests.test_matrix_selected_entry_scope import entry_shape, source_case  # noqa: F401
from tests.test_matrix_selected_package import reference
from tests.test_matrix_selected_protected import confirmation, transfer  # noqa: F401


def v2_shape(programme, pipeline):
    old = entry_shape(programme, pipeline)
    receipt, nomination = programme.nomination_receipt, programme.nomination
    prior = MatrixSelectedDevelopmentProduct("development.nomination.exposed", "unpublished/selected-opportunity",
        reference("packet.opportunity.exposed", AuthoredRecursiveWave), reference(receipt.run_id, DevelopmentRunPlan),
        reference("plan.opportunity.exposed", DevelopmentExecutionPlan), receipt.run_id, receipt.task_id,
        ObjectIdentity.from_record(receipt.receipt_id, receipt), programme.nomination_publication.logical.logical_artifact_id,
        nomination.identity, programme.nomination_publication)
    values = {field.name: getattr(old, field.name) for field in fields(old)}
    values["upstream_products"] = tuple(value for value in old.upstream_products if value.record != nomination.identity)
    return owner.MatrixSelectedEntryEvidenceV2(**values, development_nomination=prior)


def test_v2_entry_retains_four_issued_originals_and_separate_actual_development_locators(confirmation, source_case):  # noqa: F811
    evidence = v2_shape(confirmation, source_case[0])
    public_programme = MatrixSelectedPublicProgramme.from_programme(confirmation)
    owner.validate_selected_entry_evidence_v2(evidence, confirmation)
    owner.validate_selected_entry_evidence_v2(evidence, public_programme)
    assert len(evidence.upstream_products) == 4
    assert evidence.development_nomination.record == confirmation.nomination.identity
    assert not hasattr(evidence.development_nomination, "issued_study")
    assert not hasattr(evidence.development_nomination, "execution_authority")
    assert decode_canonical_bytes(evidence.canonical_bytes(), type(evidence), maximum_bytes=None) == evidence
    with pytest.raises(TypeError, match="exact supplied"):
        validate_selected_entry_evidence(evidence, confirmation)
    assert MatrixSelectedEntryEvidence.SCHEMA != evidence.SCHEMA


@pytest.mark.parametrize("damage", ("receipt", "nomination", "source-gate"))
def test_v2_entry_refuses_substitution_without_changing_original_source_obligations(confirmation, source_case, damage):  # noqa: F811
    evidence = v2_shape(confirmation, source_case[0])
    if damage == "source-gate":
        changed = replace(evidence, qualification_executions=evidence.qualification_executions[:-1])
    else:
        development = evidence.development_nomination
        pin = development.receipt if damage == "receipt" else development.record
        if damage == "nomination":
            # Keep the publication and record metadata internally consistent;
            # the independently selected original nomination must still refuse.
            publication = replace(development.publication, logical=replace(development.publication.logical, content_sha256="f" * 64),
                materialization=replace(development.publication.materialization, physical_sha256="f" * 64))
            development = replace(development, record=replace(pin, object_fingerprint="f" * 64), publication=publication)
        else:
            development = replace(development, receipt=replace(pin, object_fingerprint="f" * 64))
        changed = replace(evidence, development_nomination=development)
    with pytest.raises(ValueError, match="nomination|upstream"):
        owner.validate_selected_entry_evidence_v2(changed, confirmation)


def test_current_entry_consumes_development_evidence_and_refuses_uncommitted_execution(confirmation, source_case):  # noqa: F811
    from tests.matrix_selected_commitment_fixture import unpublished_committed_evidence
    from tests.test_matrix_selected_declarative_preparation import disclosed_produced_parents
    original = v2_shape(confirmation, source_case[0])
    evidence = unpublished_committed_evidence(original)
    parents = disclosed_produced_parents(evidence.upstream_products, (evidence.development_nomination,))
    configs, external, _, _, _ = binding.contracts(confirmation, evidence.identity, len(evidence.canonical_bytes()),
        produced_input_parents=parents)
    entry = next(config for _, config in configs if config.phase == "entry")
    assert type(entry) is binding.MatrixSelectedProtectedRootConfigV3
    assert evidence.development_nomination == original.development_nomination
    assert evidence.upstream_products == original.upstream_products
    declarations = binding.operation_declarations()
    current, = (row for row in declarations if (row.capability_key, row.capability_version, row.config_record_type) ==
        (binding.ENTRY_ORIGINAL_COMMITMENTS_KEY, "3.0.0", binding.MatrixSelectedProtectedRootConfigV3))
    assert not current.registration().native_effect
    assert current.runner_factory().manifest == current.manifest()
    assert current.runner_factory().phase == "entry"
    for version in ("1.0.0", "2.0.0"):
        with pytest.raises(ValueError, match="installed phase/version"):
            binding.capability_key("entry", version)
    with pytest.raises(ValueError, match="commitment-bearing entry"):
        binding.contracts(confirmation, original.identity, len(original.canonical_bytes()), produced_input_parents=parents)
    for _, config in configs:
        phase, version = binding.phase_of(config), binding.config_capability_version(config)
        selected, = (row for row in declarations if (row.capability_key, row.capability_version) ==
            (binding.capability_key(phase, version), version))
        assert selected.config_record_type is type(config)
        assert selected.capability_version == ("3.0.0" if phase == "entry" else "2.0.0" if phase in binding.NATIVE else "1.0.0")
    point, = (row for row in external if row.input_id.startswith("external.selected-point-design."))
    assert (point.outcome_access, point.visibility_ceiling) == (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)
    entry_evidence, = (row for row in external if row.input_id.startswith("external.selected-entry-evidence."))
    assert (entry_evidence.outcome_access, entry_evidence.visibility_ceiling) == (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)
    assert all(row.outcome_access is OutcomeAccess.OUTCOME_BLIND and row.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
        for row in external if row not in (point, entry_evidence))
    assert all(b'"scores"' not in record.canonical_bytes() for _, record in configs)


@pytest.mark.parametrize("route", ("transfer", "legacy-confirmation", "development-confirmation"))
def test_protected_entry_batches_only_original_e3_and_keeps_nomination_lanes_separate(
        transfer, confirmation, source_case, monkeypatch, route):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment
    from empirical_lawhood.api import matrix_sampling_runtime, matrix_selected_runtime, matrix_selected_producer_scope
    from empirical_lawhood.api import matrix_selected_opportunity_runtime
    full = transfer if route == "transfer" else confirmation
    programme = MatrixSelectedPublicProgramme.from_programme(full)
    evidence = (v2_shape(full, source_case[0]) if route == "development-confirmation" else entry_shape(full, source_case[0]))
    package, writer, codecs = full.point_design.package, object(), {}
    records = {ObjectIdentity.from_record(value.record_id, value): value for value in
        (package.models, package.model_freeze, package.calibration, package.calibrated_freeze)}
    calls = []
    class OriginalJoinObserved(Exception):
        pass
    def batch(actual_writer, originals, actual_codecs, *, scope_validator):
        assert actual_writer is writer and actual_codecs is codecs
        assert {pin for _, pin in originals} == set(records) and len(originals) == 4
        assert originals == tuple((value, value.record) for value in evidence.upstream_products if value.record in records)
        assert scope_validator.func is matrix_selected_producer_scope.validate_selected_original_producer
        assert scope_validator.keywords == {"programme": programme}
        calls.append("original-e3-batch")
        return tuple(records[pin].canonical_bytes() for _, pin in originals)
    def legacy_nomination(actual_writer, original, expected, actual_codecs, read_scope, *, scope_validator):
        assert route == "legacy-confirmation" and actual_writer is writer and actual_codecs is codecs and read_scope is None
        assert expected == original.record == programme.nomination.original_nomination
        assert scope_validator.keywords == {"programme": programme}
        calls.append("separate-issued-nomination")
        raise OriginalJoinObserved
    def development_nomination(actual_writer, binding, *, package, criterion, nomination_pin, read_access):
        assert route == "development-confirmation" and actual_writer is writer and read_access is None
        assert binding == evidence.development_nomination and package == full.point_design.package
        assert criterion == programme.criterion and nomination_pin == programme.nomination.original_nomination
        calls.append("separate-development-nomination")
        raise OriginalJoinObserved
    def reconstruct(actual_programme, calibration, nomination):
        assert route == "transfer" and actual_programme == programme
        assert calibration == package.calibration and nomination is None
        calls.append("exact-parent-calibration")
        raise OriginalJoinObserved
    # These disclosed I/O seams exercise grouping only; no source qualification,
    # original custody, issue or reveal authority is supplied by this fixture.
    monkeypatch.setattr(commitment, "authenticate_publication", lambda *args: None)
    monkeypatch.setattr(matrix_sampling_runtime, "_original_products", batch)
    monkeypatch.setattr(matrix_sampling_runtime, "_original_product", legacy_nomination)
    monkeypatch.setattr(matrix_selected_opportunity_runtime, "authenticate_selected_development_nomination", development_nomination)
    monkeypatch.setattr(matrix_selected_runtime, "_reconstruct_entry_programme", reconstruct)
    with pytest.raises(OriginalJoinObserved):
        matrix_selected_runtime.authenticate_selected_original_products(writer, programme, evidence, codecs)
    expected = {"transfer": "exact-parent-calibration", "legacy-confirmation": "separate-issued-nomination",
        "development-confirmation": "separate-development-nomination"}[route]
    assert calls == ["original-e3-batch", expected]
