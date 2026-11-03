# SPDX-License-Identifier: MPL-2.0
"""Standard public candidate authoring over exposed metadata, without grants."""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.formal_gaps import FormalDomain, FormalGapRegister, FormalGapSpec, FormalGapEvidenceWorld
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole
from empirical_lawhood.runtime.candidate_compiler import AuthoringMaterializationIdentity, CandidateCompilationDisposition, compile_study_candidate
from empirical_lawhood.adapters.physical.virtual_cell.authoring import build_virtual_cell_authoring_bundle
from empirical_lawhood.adapters.physical.virtual_cell.authoring_v2 import project_authoring_bundle_v2
from empirical_lawhood.adapters.physical.virtual_cell.materialization import TargetFeatureMaterializationReceipt
from tests.test_virtual_cell_ports_v2 import _metadata


def _original():
    values = _metadata()
    provenance = ObjectIdentity("formal-source.exposed", "empirical-lawhood/testing/formal-source", "1.0.0", "1" * 64)
    gaps = tuple(FormalGapSpec("gap." + domain.value.lower() + ".exposed", domain, "Exposed software authoring only",
        ("operand.exposed",), (FormalGapEvidenceWorld.RETROSPECTIVE_DATASET,), 1, 0,
        ("estimator." + domain.value.lower(),), ("control." + domain.value.lower(),),
        ("falsifier." + domain.value.lower(),), ("prerequisite." + domain.value.lower(),),
        "multiplicity." + domain.value.lower(), EvidenceCeiling.LOCAL_LAW, (provenance.object_id,)) for domain in sorted(FormalDomain))
    register = FormalGapRegister("register.exposed", "1.0.0", (provenance,), gaps)
    receipt = TargetFeatureMaterializationReceipt("receipt.features.exposed", values.manifest.fingerprint(),
        ("roster.test", "roster.train", "roster.validation"), ("1" * 64, "2" * 64, "3" * 64),
        values.original.target_feature_build_receipt_sha256, sha256(values.features).hexdigest(), len(values.features), 1, 1,
        values.original.target_feature_provenance_sha256, OutcomeAccess.OUTCOME_BLIND, False, False)
    bundle = build_virtual_cell_authoring_bundle(source_manifest=values.manifest, target_feature_payload=values.features,
        test_roster_payload=values.roster, leaderboard_snapshot=values.leaderboard,
        feature_materialization_receipt=receipt, register=register, implementation_sha256="1" * 64,
        pipeline_config=values.original)
    return bundle, values.selection


@pytest.mark.parametrize("development", [False, True])
def test_projected_authoring_compiles_through_standard_service_preserving_original_and_authority(development):
    original, selection = _original()
    historical = (original.config.canonical_bytes(), original.package.canonical_bytes(), original.development_package.canonical_bytes())
    # Explicit software fixture provenance on the endpoint-stage causal clock;
    # this asserts no calendar-time historical provenance for the current code.
    selection_input = DesignInputRecord("design-input.exposed-current-v2", selection.identity, selection.fingerprint(),
        original.draft.design_inputs[0].information_cutoff, DesignInputRole.DEVELOPMENT_TUNING,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, "human.exposed-software-fixture")
    bundle = project_authoring_bundle_v2(original, selection=selection, selection_design_input=selection_input)
    package = bundle.development_package if development else bundle.package
    payload = package.canonical_bytes()
    report = compile_study_candidate(authoring_package=package,
        authoring_materialization=AuthoringMaterializationIdentity("application/json", len(payload), sha256(payload).hexdigest()),
        context=bundle.standard_context)
    assert report.disposition is CandidateCompilationDisposition.COMPILED_AUTHORITY_PENDING
    assert report.candidate is not None
    assert (original.config.canonical_bytes(), original.package.canonical_bytes(), original.development_package.canonical_bytes()) == historical
    assert selection.canonical_bytes() in bundle.candidate_input_payloads
    assert original.config.canonical_bytes() in bundle.candidate_input_payloads
    assert package.entry_package.checklist.bindings == (original.development_package if development else original.package).entry_package.checklist.bindings
    assert all(value.capability_version == "2.0.0" for value in package.draft.capability_selections)
    assert len((bundle.development_template if development else bundle.template).protocol.steps) == (7 if development else 9)


@pytest.mark.parametrize("damage", ["absent", "exposed", "changed-cutoff"])
def test_current_selection_cannot_inherit_historical_provenance_or_hide_exposure(damage):
    from decimal import Decimal
    from empirical_lawhood.adapters.physical.virtual_cell.contracts import VirtualCellContractError

    original, selection = _original()
    if damage == "absent":
        with pytest.raises(VirtualCellContractError, match="explicit current selection design input"):
            project_authoring_bundle_v2(original, selection=selection)
        return
    prior = original.draft.design_inputs[0].information_cutoff
    cutoff = replace(prior, cutoff_id="cutoff.current-selection", coordinate=Decimal(1)) if damage == "changed-cutoff" else prior
    selection_input = DesignInputRecord("design-input.current-exposed-v2", selection.identity, selection.fingerprint(), cutoff,
        DesignInputRole.DEVELOPMENT_TUNING,
        OutcomeAccess.EVALUATION_REVEALED if damage == "exposed" else OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.OUTCOME_VISIBLE if damage == "exposed" else VisibilityCeiling.PROSPECTIVE,
        "human.exposed-software-fixture")
    bundle = project_authoring_bundle_v2(original, selection=selection, selection_design_input=selection_input)
    assert next(value for value in bundle.draft.design_inputs if value.input_id == selection_input.input_id) is selection_input
    payload = bundle.package.canonical_bytes()
    report = compile_study_candidate(authoring_package=bundle.package,
        authoring_materialization=AuthoringMaterializationIdentity("application/json", len(payload), sha256(payload).hexdigest()),
        context=bundle.standard_context)
    assert report.disposition is CandidateCompilationDisposition.INVALID_DRAFT
    assert report.candidate is None
