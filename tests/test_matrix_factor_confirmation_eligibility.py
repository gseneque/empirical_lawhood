# SPDX-License-Identifier: MPL-2.0
"""Current allocation and anonymous-array software controls, never qualification."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import eligibility as p
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import (
    MatrixHistoryAllocation, PUBLIC_HISTORY_MASTER_SEED, matrix_history_numeric_roots,
    matrix_known_exposed_effective_seeds,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.exposure import (
    MANDATORY_EFFECTIVE_SEEDS, MANDATORY_FLOOR_IDENTITY, MANDATORY_FLOOR_SHA256,
    MatrixConstantPhysicalExclusion,
)
from empirical_lawhood.adapters.methods.matrix_prospective.example import example_source
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole as Role
from empirical_lawhood.api import matrix_history_analysis as history_api
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.test_recursive_public_service import _plane


ROOT = Path(__file__).resolve().parents[1]


def _matrix_plane(path, *, storage_codecs=MATRIX_STORAGE_CODECS):
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    plane = _plane(path)
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=storage_codecs)
    return plane

def artifact(name, raw=b"exposed software audit", schema="empirical-lawhood/testing/exposure-audit"):
    return ArtifactIdentity(name, "exposed-software-fixture", schema, sha256(raw).hexdigest(), "application/json", len(raw))

def operand(name, digest="a" * 64):
    return ObjectIdentity(name, "empirical-lawhood/testing/frozen-method", "1.0.0", digest)

def publish(plane, record, name):
    return plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "publication." + name,
        "inputs", record.canonical_bytes(), Visibility.PROSPECTIVE,
        (), Access.OUTCOME_BLIND))

@pytest.fixture(scope="module")
def provenance():
    return capture_matrix_provenance(project_root=ROOT)

@pytest.fixture
def stock(tmp_path, provenance, *, storage_codecs=MATRIX_STORAGE_CODECS):
    plane = _matrix_plane(tmp_path / "selected", storage_codecs=storage_codecs)
    original = example_source()
    facts = (artifact("audit.exposure"), artifact("bank.historical"))
    prior_regime = p.MatrixFactorRegime(original.protocol.root.regime_id,
        original.protocol.member, original.protocol.view, original.protocol.alpha_x, original.protocol.alpha_y)
    seeds = MANDATORY_EFFECTIVE_SEEDS | {9321, *(stream.effective_seed
        for root in original.allocation.streams.roots for stream in root.scientific_seeds)}
    exposure = p.MatrixFactorExposureCensus("exposure.software.matrix", MANDATORY_FLOOR_IDENTITY,
        tuple(sorted(seeds)), (original.protocol.root.independent_group_id,),
        (original.protocol.root.regime_id,), (MatrixConstantPhysicalExclusion(*prior_regime.physical_parameters),), (),
        tuple(sorted({"f" * 64, MANDATORY_FLOOR_SHA256, *(value.sha256 for value in facts)})), facts)
    roots = []
    for number, role in enumerate((Role.CALIBRATION, Role.CONFIRMATION, Role.DEVELOPMENT, Role.WITHHELD_TRANSFER)):
        streams = tuple(p.MatrixFactorStream(name, name + ".panel", 50000 + number * 10 + index, stream_role)
            for index, (name, stream_role) in enumerate((
                ("independent", "INDEPENDENT_FUTURE"), ("paired", "COMMON_NOISE_PANEL"), ("prefix", "PREFIX"))))
        roots.append(p.MatrixFactorRootAllocation("root." + role.value.lower(), "independent." + role.value.lower(),
            "regime." + role.value.lower(), "coordinate." + role.value.lower(), "clock." + role.value.lower(), role, streams))
    regimes = tuple(p.MatrixFactorRegime(r.regime_id, original.protocol.member,
        replace(original.protocol.view, bath_temperature=Decimal(2))
            if r.role is Role.WITHHELD_TRANSFER else original.protocol.view,
        Decimal(1), Decimal(1)) for r in roots)
    allocation = p.MatrixFactorAllocation("allocation.software.matrix", tuple(roots), exposure, regimes=regimes)
    reservation = p.MatrixAllocationReservation("reservation.software.matrix", allocation,
        publish(plane, allocation, "allocation"))
    fits = tuple(p.MatrixFactorFitScope("fit." + role.value.lower(), p.identity(reservation),
        ("root." + role.value.lower(),), ("regime." + role.value.lower(),), role.value)
        for role in (Role.CALIBRATION, Role.DEVELOPMENT))
    selection = p.MatrixFactorScientificSelection("selection.software.matrix", p.identity(reservation), fits,
        operand("rule.fixed"), ObjectIdentity.from_record(original.protocol.member.member_id, original.protocol.member),
        operand("predictor.fixed"), operand("evaluator.fixed"), operand("response-design.fixed"),
        operand("statistics.fixed"),
        *(operand(name) for name in ("chart.fixed", "receiver.fixed", "initial.fixed", "preparation.fixed")),
        ("hold", "negative", "positive"), (1, 2))
    frozen = p.MatrixFactorFrozenSpecification("freeze.software.matrix", selection, publish(plane, selection, "selection"))
    source = p.MatrixFactorSource("source.software.matrix", reservation, frozen,
        original.protocol.member, original.protocol.view, provenance)
    return plane, source

def test_public_numeric_seed_lift_preserves_exact_historical_bytes_and_exclusions():
    raw = (ROOT / "programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json").read_bytes()
    original = decode_canonical_bytes(raw, MatrixHistoryAllocation, maximum_bytes=None)
    assert original.roots == matrix_history_numeric_roots("public.matrix-history", PUBLIC_HISTORY_MASTER_SEED)
    assert original.canonical_bytes() == raw
    assert history_api._numeric_roots("renamed", 123) == matrix_history_numeric_roots("renamed", 123)
    known = matrix_known_exposed_effective_seeds((9843,))
    assert 9843 in known
    assert {s.effective_seed for r in original.roots for s in r.seeds} <= known
    with pytest.raises(ValueError, match="overlap"):
        history_api.prepare_matrix_history_allocation(allocation_id="renamed", namespace="renamed",
            master_seed=PUBLIC_HISTORY_MASTER_SEED, exposure="PROPOSED_UNRUN")

def test_complete_reservation_freeze_source_roundtrip_and_no_qualification(stock):
    _, source = stock
    assert decode_canonical_bytes(source.canonical_bytes(), p.MatrixFactorSource, maximum_bytes=None) == source
    source.specification.validate_reservation(source.reservation)
    assert source.evidence_role == p.CANDIDATE

def test_actual_fit_input_requires_prior_retained_role_publication(stock):
    plane, source = stock
    published = source.reservation.publication
    port = plane.open(VerifiedArtifactInput(published.logical, published.materialization),
                      maximum_bytes=len(source.allocation.canonical_bytes()))
    try:
        p.require_reserved_fit_input(source.specification.selection.fits[0], source.reservation, port)
    finally:
        port.close()
    changed = replace(source.reservation, reservation_id="late.renamed.reserve")
    port = plane.open(VerifiedArtifactInput(published.logical, published.materialization),
                      maximum_bytes=len(source.allocation.canonical_bytes()))
    try:
        with pytest.raises(ValueError, match="prior whole-programme"):
            p.require_reserved_fit_input(source.specification.selection.fits[0], changed, port)
    finally:
        port.close()

def test_timestep_or_semantic_regime_rename_cannot_create_transfer_holdout(stock):
    _, source = stock
    regimes = list(source.allocation.regimes)
    regimes[3] = replace(regimes[3], member=replace(regimes[1].member, member_id="member.renamed"),
        view=replace(regimes[1].view, view_id="view.fine", timestep=Decimal("0.0005")))
    with pytest.raises(ValueError, match="physical regime"):
        replace(source.allocation, regimes=tuple(regimes))

@pytest.mark.parametrize("defect", ("public-stream", "old-stream", "declared-stream", "collision", "exposed-parent", "regime", "root-role"))
def test_labels_and_new_source_do_not_supply_independence_or_protect_visited_regimes(stock, defect):
    _, source = stock
    allocation = source.allocation
    roots = list(allocation.roots)
    root = roots[1]
    if defect in {"public-stream", "old-stream", "declared-stream", "collision"}:
        seed = {
            # Exact previously exposed public-history and original-example
            # seeds remain excluded without reconstructing those allocations.
            "public-stream": int("c08aaf69a529e7428ffc717ae7b1924d", 16),
            "old-stream": example_source().allocation.streams.roots[0].scientific_seeds[0].effective_seed,
            "declared-stream": 9321,
            "collision": roots[0].streams[0].seed,
        }[defect]
        roots[1] = replace(root, streams=(replace(root.streams[0], seed=seed), *root.streams[1:]))
    elif defect == "exposed-parent":
        roots[1] = replace(root, independent_group_id=allocation.exposure.exposed_independent_groups[0])
    elif defect == "regime":
        roots[3] = replace(roots[3], regime_id=roots[2].regime_id)
    else:
        roots[1] = replace(root, independent_group_id=roots[2].independent_group_id)
    with pytest.raises(ValueError):
        replace(allocation, allocation_id="renamed.allocation", roots=tuple(roots))

@pytest.mark.parametrize("defect", ("confirmation-fit", "withheld-fit", "wrong-reserve", "changed-model", "changed-menu", "changed-freeze-publication"))
def test_late_or_changed_scientific_choices_refuse_before_fit_or_confirmation(stock, defect):
    _, source = stock
    selection = source.specification.selection
    with pytest.raises(ValueError):
        if defect.endswith("fit"):
            role = Role.CONFIRMATION if defect == "confirmation-fit" else Role.WITHHELD_TRANSFER
            fit = replace(selection.fits[0], root_ids=("root." + role.value.lower(),),
                regime_ids=("regime." + role.value.lower(),))
            fit.validate_reservation(source.reservation)
        elif defect == "wrong-reserve":
            changed = replace(selection, reservation=replace(selection.reservation, object_fingerprint="b" * 64), fits=())
            changed.validate_reservation(source.reservation)
        else:
            if defect == "changed-model":
                changed = replace(selection, model=replace(selection.model, object_fingerprint="b" * 64))
            elif defect == "changed-menu":
                changed = replace(selection, action_ids=("hold",))
            else:
                changed = replace(selection, receiver=operand("receiver.changed"))
            replace(source.specification, selection=changed)

def test_strict_anonymous_eligible_array_reader_and_relocation_with_future_free_scope(stock, tmp_path):
    plane, source = stock
    arrays = {"momenta": np.zeros((3, 2, 3, 4, 4), dtype="<c16"),
              "positions": np.ones((3, 2, 3, 4, 4), dtype="<c16")}
    raw, members = encode_matrix_arrays(arrays)
    saved = p.EligibleMatrixArrays("arrays.software.origin", source.allocation.identity, p.identity(source),
        "root.confirmation", "ORIGIN", ArtifactIdentity("array.origin", "matrix-arrays", MATRIX_ARRAY_SCHEMA,
            sha256(raw).hexdigest(), "application/x-npz", len(raw)), members,
        (p.identity(source),), Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
    published = plane.write(ArtifactWriteRequest(saved.array_artifact.artifact_id, "arrays/origin.npz", MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "publication.origin", "arrays",
        raw, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    expected = tuple((m.name, m.dtype, m.shape) for m in members)
    value = VerifiedArtifactInput(published.logical, published.materialization)
    relocated = _matrix_plane(tmp_path / "relocated")
    shutil.copytree(plane.root.contract.canonical_path, relocated.root.contract.canonical_path, dirs_exist_ok=True)
    shutil.rmtree(plane.root.contract.canonical_path)
    for scope in (source, p.identity(source)):
        port = relocated.open(value, maximum_bytes=len(raw))
        try:
            observed = p.consume_eligible_arrays(port, saved, scope, expected_members=expected,
                expected_producers=saved.producers, allocation=source.allocation.identity, root_id="root.confirmation")
            for name in arrays:
                np.testing.assert_array_equal(observed[name], arrays[name])
        finally:
            port.close()
    for damaged in (replace(saved, source=replace(saved.source, object_fingerprint="b" * 64)),
                    replace(saved, members=(replace(members[0], sha256="b" * 64), members[1]))):
        port = relocated.open(value, maximum_bytes=len(raw))
        try:
            with pytest.raises(ValueError):
                p.consume_eligible_arrays(port, damaged, source, expected_members=expected, expected_producers=saved.producers)
        finally:
            port.close()

def test_confirmation_clock_and_existing_authority_refusals(stock):
    _, source = stock
    cutoff = InformationCutoff("cutoff.origin", "clock.confirmation", CausalPhase.PRE_ACTION, Decimal("0.002"))
    p.validate_origin_cutoff(source, "root.confirmation", cutoff, native_step=2, timestep=source.view.timestep)
    with pytest.raises(ValueError):
        p.validate_origin_cutoff(source, "root.confirmation", replace(cutoff, coordinate=Decimal("0.003")),
            native_step=2, timestep=source.view.timestep)
    policy = AuthorityPolicy("policy.software", "owner", "approver", ("study.confirmation",),
        frozenset((WorldKind.NUMERICAL_SIMULATOR,)), frozenset((AuthorityAction.READ_ONLY_EXPLORATION,)),
        frozenset((SourceAccessClass.NONE,)), ("gate.confirmation",), frozenset(), p.BUDGET, Access.OUTCOME_BLIND)
    reasons = p.confirmation_authority_reasons(source, policy, scope_id="study.confirmation", budget=p.BUDGET,
        passed_gate_ids=frozenset(), proposer_id="proposer", approver_id="approver", at_utc="2026-10-13T00:00:00Z")
    assert {"ACTION_NOT_ALLOWED", "REQUIRED_GATES_MISSING"} <= set(reasons)

@pytest.mark.parametrize("state", ("UNKNOWN_COMPLETION", "COMPLETED", "BEGUN"))
def test_retained_or_uncertain_native_branch_cannot_be_reacquired(state):
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    selected = NativeSubworkState(state)
    store = SimpleNamespace(inspect=lambda definition: SimpleNamespace(state=selected))
    with pytest.raises(ValueError, match="receipt recovery"):
        p.refuse_completed_or_uncertain_branch(store, object())
