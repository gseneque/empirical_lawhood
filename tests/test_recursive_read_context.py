# SPDX-License-Identifier: MPL-2.0
"""One real PURE read per internal consumer; no native or scientific acceptance."""
from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api import recursive_execution as owner
from empirical_lawhood.infrastructure import recursive_custody as custody
from tests.test_recursive_report_projection import wave as wave  # noqa: F401
from tests.test_recursive_contribution_custody import portable_a as portable_a  # noqa: F401


def counts(monkeypatch):
    observed = {"loads": 0, "plans": 0, "products": 0}
    load, plans, products = owner.load_authored_wave, owner._retained_plans, custody.read_recursive_products
    def actual_load(**kwargs):
        observed["loads"] += 1
        return load(**kwargs)
    def actual_plans(*args):
        observed["plans"] += 1
        return plans(*args)
    def actual_products(**kwargs):
        observed["products"] += 1
        return products(**kwargs)
    monkeypatch.setattr(owner, "load_authored_wave", actual_load)
    monkeypatch.setattr(owner, "_retained_plans", actual_plans)
    monkeypatch.setattr(custody, "read_recursive_products", actual_products)
    return observed


@pytest.mark.parametrize("mode", ("documents", "references", "compact"))
@pytest.mark.parametrize("scoped", (False, True))
def test_actual_pure_read_reuses_only_own_roots_and_keeps_exact_public_result(wave, monkeypatch, mode, scoped):
    baseline = owner.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
        include_products=True, terminal_product_format=mode)
    observed = counts(monkeypatch)
    def preflight(**roots):
        assert observed == {"loads": 1, "plans": 1, "products": 0}
        assert roots["draft"] == baseline[2] and roots["plan"] == baseline[3]
        assert roots["packet"].fingerprint() == baseline[0]["packet_sha256"]
        # Return only decoded identities, never the callback's live payload map.
        return roots["packet"].fingerprint(), roots["run"].run_plan_id
    with (wave.plane.verification_scope() if scoped else nullcontext(wave.plane)) as writer:
        result, roots, selected = owner._read_recursive_wave_with_roots(directory=wave.directory,
            artifact_writer=writer, include_products=True, terminal_product_format=mode,
            validate_authored=preflight)
    assert result == baseline
    assert len(roots) == 6 and all(not isinstance(value, Mapping) for value in roots)
    assert selected == (baseline[0]["packet_sha256"], baseline[0]["run_id"])
    assert observed == {"loads": 1, "plans": 1, "products": 1}


def test_preflight_refusal_precedes_every_actual_product_read(wave, monkeypatch):
    observed = counts(monkeypatch)
    def refuse(**roots):
        assert roots["plan"].tasks and observed["loads"] == observed["plans"] == 1
        raise PermissionError("actual selected consumer refuses this scope")
    with pytest.raises(PermissionError, match="consumer refuses"):
        owner._read_recursive_wave_with_roots(directory=wave.directory, artifact_writer=wave.plane,
            include_products=True, validate_authored=refuse)
    assert observed == {"loads": 1, "plans": 1, "products": 0}


@pytest.mark.parametrize("name", ("authored-wave.json", "draft.json", "execution-plan.json"))
@pytest.mark.parametrize("scoped", (False, True))
def test_preflight_metadata_mutation_is_refused_with_or_without_outer_scope(wave, monkeypatch, name, scoped):
    observed = counts(monkeypatch)
    path = wave.directory / name
    original = path.read_bytes()
    def change(**roots):
        assert observed["products"] == 0
        path.write_bytes(b"x" + original[1:])
        return roots["packet"].fingerprint()
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            with (wave.plane.verification_scope() if scoped else nullcontext(wave.plane)) as writer:
                owner._read_recursive_wave_with_roots(directory=wave.directory, artifact_writer=writer,
                    include_products=True, validate_authored=change)
    finally:
        # This is an explicit mutation of a reusable PURE software fixture.
        path.write_bytes(original)
    assert observed == {"loads": 1, "plans": 1, "products": 0}


@pytest.mark.parametrize("fallback", ("policy", "request-bound"))
def test_custom_policy_or_request_bound_keeps_fresh_second_metadata_admission(wave, monkeypatch, fallback):
    baseline = owner.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane, include_products=True)
    if fallback == "policy":
        original = wave.plane.verify_manifest
        monkeypatch.setattr(wave.plane, "verify_manifest", lambda value: original(value))
    else:
        packet, _, _, _ = owner.load_authored_wave(directory=wave.directory,
            artifact_writer=wave.plane, lazy_payloads=True)
        # The real request ceiling admits each publication and the constructor
        # batch, while the additional packet exceeds this helper's one batch.
        monkeypatch.setattr(wave.plane, "custody_limits",
            replace(wave.plane.custody_limits, publication_members=len(packet.members)))
    observed = counts(monkeypatch)
    def preflight(**roots):
        assert observed == {"loads": 1, "plans": 1, "products": 0}
        return roots["packet"].fingerprint()
    result, roots, selected = owner._read_recursive_wave_with_roots(directory=wave.directory,
        artifact_writer=wave.plane, include_products=True, validate_authored=preflight)
    assert result == baseline and selected == roots[0].fingerprint()
    assert observed == {"loads": 2, "plans": 2, "products": 1}


def test_custom_policy_fresh_second_admission_rejects_changed_packet(wave, monkeypatch):
    original_policy = wave.plane.verify_manifest
    monkeypatch.setattr(wave.plane, "verify_manifest", lambda value: original_policy(value))
    path = wave.directory / "authored-wave.json"
    original = path.read_bytes()
    observed = counts(monkeypatch)
    def change(**roots):
        path.write_bytes(b"x" + original[1:])
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            owner._read_recursive_wave_with_roots(directory=wave.directory, artifact_writer=wave.plane,
                include_products=True, validate_authored=change)
    finally:
        path.write_bytes(original)
    assert observed["loads"] == 2 and observed["products"] == 0


def test_real_native_export_owner_refuses_wrong_actual_protocol_before_products(wave, monkeypatch):
    from empirical_lawhood.api.native_training_banks import export_native_training_banks
    observed = counts(monkeypatch)
    destination = wave.directory.parent / "wrong-protocol-native-export"
    with pytest.raises((ValueError, PermissionError)):
        export_native_training_banks(directory=wave.directory, artifact_writer=wave.plane,
            output_directory=destination, record_id="bank.actual-pure-is-not-native-train")
    assert observed == {"loads": 1, "plans": 1, "products": 0}
    assert not destination.exists()


@pytest.mark.parametrize("custody_kind", ("PUBLICATION", "FILE"))
@pytest.mark.parametrize("scoped", (False, True))
def test_actual_committed_train_support_mutation_after_preflight_refuses_before_products(
        tmp_path, monkeypatch, custody_kind, scoped):
    from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
    from empirical_lawhood.api.native_training_banks import _read_instance
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as records
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_request
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    from tests.test_matrix_native_training_public_lifecycle import _copied_preparation, ROOT
    # Existing metadata constructors publish actual support commitments only;
    # no trajectory, native worker, fitting or producing completion is executed.
    case = fresh_training_metadata_case(tmp_path)
    if custody_kind == "FILE":
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
        census_artifacts = {artifact for manifest in (case.request.train_manifest, case.request.future_manifest)
            for artifact, _ in exposure_support(manifest.audit)}
        mandatory = records.future_response_support(case.request)
        supports = []
        for artifact, publication in case.request.exposure_support:
            if artifact not in census_artifacts:
                supports.append((artifact, publication))
                continue
            # Future/C commitments remain their actual canonical publications.
            # Only the census receives a byte-identical unpublished FILE copy.
            relative = "unpublished-support/" + artifact.sha256 + ".json"
            target = case.plane.root.resolve(relative, for_write=True)
            target.parent.mkdir(exist_ok=True)
            original_path = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
            raw = original_path.read_bytes()
            target.write_bytes(raw)
            assert len(raw) == artifact.size_bytes
            assert not Path(str(target) + ".manifest.json").exists()
            supports.append((artifact, ExperimentFileInputBinding("file." + artifact.artifact_id,
                artifact, "1.0.0", relative, artifact.size_bytes)))
        supports = tuple(supports)
        case.request = replace(case.request, exposure_support=supports)
        assert records.future_response_support(case.request) == mandatory
        case.acquisition = records.acquisition_seal(case.specification, case.request)
    preparation = _copied_preparation(case, tmp_path / "copied")
    directory = Path(case.plane.root.contract.canonical_path) / "authored-support"
    author_prepared_experiment(preparation=preparation, project_root=ROOT,
        artifact_writer=case.plane, output_dir=directory)
    artifact, support = (next(row for row in case.request.exposure_support
        if type(row[1]) is ExperimentFileInputBinding) if custody_kind == "FILE"
        else case.request.exposure_support[0])
    relative = support.relative_path if custody_kind == "FILE" else support.materialization.relative_path
    path = case.plane.root.resolve(relative, for_write=False)
    original = path.read_bytes()
    observed = counts(monkeypatch)
    # An author-only target would otherwise fail for missing run inputs even
    # if premise refresh were absent. Trap its FIRST read path to distinguish
    # the required freshness refusal from that unrelated later failure.
    def forbidden_inputs(**kwargs):
        pytest.fail("changed committed support reached target run inputs")
    monkeypatch.setattr(owner, "_external_inputs", forbidden_inputs)
    seen = []
    def change(**roots):
        specification, request, _ = _read_instance(roots["payloads"])
        assert specification == case.specification and request == case.request
        authenticate_request(writer, request)
        assert relative not in {roots["payloads"].manifest(name).materialization.relative_path
            for name in roots["payloads"]}
        seen.append(request.identity)
        path.write_bytes(b"x" * artifact.size_bytes)
        return request.identity
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            with (case.plane.verification_scope() if scoped else nullcontext(case.plane)) as writer:
                owner._read_recursive_wave_with_roots(directory=directory, artifact_writer=writer,
                    include_products=True, validate_authored=change)
    finally:
        path.write_bytes(original)
    assert seen == [case.request.identity]
    assert observed == {"loads": 1, "plans": 1, "products": 0}


@pytest.fixture
def authored_parent_origins(portable_a, monkeypatch):
    from empirical_lawhood.api import recursive_authoring as author
    from empirical_lawhood.api import recursive_contributions as parents
    from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import (
        BatteryFurtherProduct, BatteryProcedureContribution,
    )
    from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import battery_wave_b_draft
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from tests.test_recursive_contribution_custody import _publish_fixture_wave, ROOT
    from tests.test_recursive_multiple_parents import pair_draft, PairConfig, PairRead
    # Reuse disclosed precomputed synthetic software custody, real owner
    # receipts and portable closure. No battery/native numerical work is run.
    _, _, _, _, plane, first_dir, _ = portable_a
    _, _, first, _, first_products, _ = parents.authenticate_recursive_contribution(
        directory=first_dir, artifact_writer=plane)
    procedure = next(row for values in first_products["records"].values() for row in values.values()
        if type(row) is BatteryProcedureContribution)
    second_authored = Path(plane.root.contract.canonical_path) / "parent-origin-wave-b"
    _publish_fixture_wave(monkeypatch, plane, second_authored, battery_wave_b_draft(first, procedure),
        manifest=first, procedure=procedure, parent=first_dir)
    second_dir = second_authored.parent / "parent-origin-export-b"
    parents.export_recursive_contribution(directory=second_authored, output_dir=second_dir,
        project_root=ROOT, artifact_writer=plane)
    _, _, second, _, second_products, _ = parents.authenticate_recursive_contribution(
        directory=second_dir, artifact_writer=plane)
    outcome = next(row for values in second_products["records"].values() for row in values.values()
        if type(row) is BatteryFurtherProduct)
    draft, origins, manifest, registration = pair_draft(first, second, procedure, outcome)
    old_registrations, old_registry, old_codecs = author.operation_catalog()
    codecs = {**old_codecs, **{kind.SCHEMA: kind for kind in
        (PairConfig, PairRead, BatteryProcedureContribution, BatteryFurtherProduct)}}
    registry = CapabilityRegistry("registry.read-context.parent-origins", tuple(sorted(
        (*old_registry.capabilities, manifest), key=lambda row: row.registry_id)))
    catalog = lambda: ((*old_registrations, registration), registry, codecs)
    monkeypatch.setattr(author, "operation_catalog", catalog)
    monkeypatch.setattr(owner, "operation_catalog", catalog)
    directories = (first_dir, second_dir)
    inputs = dict(parents.contribution_input_bindings(directories=directories, draft=draft,
        artifact_writer=plane, origins=origins))
    selected_origin = origins.inputs[0]
    target = Path(plane.root.contract.canonical_path) / "authored-origin-consumer"
    authored = author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=target, contribution_dirs=directories, origins=origins)
    return plane, target, authored["run_id"], first_dir / "contribution.json", inputs[selected_origin.input_id]


@pytest.mark.parametrize("kind", ("parent", "origin-product"))
@pytest.mark.parametrize("scoped", (False, True))
def test_real_external_parent_and_origin_product_mutations_refresh_before_target_products(
        authored_parent_origins, monkeypatch, kind, scoped):
    plane, directory, run_id, parent_file, origin_file = authored_parent_origins
    path = parent_file if kind == "parent" else origin_file
    original = path.read_bytes()
    actual_products = custody.read_recursive_products
    target_products = []
    actual_inputs = owner._external_inputs
    def read_parent_inputs_only(**kwargs):
        if kwargs["plan"].source_plan.object_id == run_id:
            pytest.fail("changed parent/origin reached target run inputs")
        return actual_inputs(**kwargs)
    monkeypatch.setattr(owner, "_external_inputs", read_parent_inputs_only)
    def read_parent_only(**kwargs):
        if kwargs["plan"].source_plan.object_id == run_id:
            target_products.append(run_id)
            pytest.fail("changed parent/origin reached target products")
        return actual_products(**kwargs)
    monkeypatch.setattr(custody, "read_recursive_products", read_parent_only)
    preflights = []
    def change(**roots):
        assert roots["run"].run_plan_id == run_id and not target_products
        preflights.append(roots["packet"].fingerprint())
        path.write_bytes(b"x" + original[1:])
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            with (plane.verification_scope() if scoped else nullcontext(plane)) as writer:
                owner._read_recursive_wave_with_roots(directory=directory, artifact_writer=writer,
                    include_products=True, validate_authored=change)
    finally:
        path.write_bytes(original)
    assert len(preflights) == 1 and target_products == []
