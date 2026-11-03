# SPDX-License-Identifier: MPL-2.0
"""Closed TEST source controls and opt-in issued PURE-worker acceptance."""

from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.metatheory import MetatheoryAggregateDisposition, MetatheoryApplicability
from tests import matrix_selected_source_predecessor as release
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401
from tests.test_matrix_source_evidence import source_case  # noqa: F401


@pytest.fixture
def closed_scope(selected_e4_populations, source_case):  # noqa: F811
    population, bank = selected_e4_populations.calibration, selected_e4_populations.calibration_bank
    pipeline, _ = source_case
    cutoff = InformationCutoff("cutoff.disclosed-release-source", population.cases[0].information_cutoff.clock_id,
        CausalPhase.PREPARATION, Decimal(0))
    numerical = bank.source(bank.sources[0].root_id, index=bank.source_index()).numerical_design
    common = release.ReleaseGateScope("scope.disclosed-release-source", population.identity, bank.identity,
        old.identity(bank.reservation), bank.response_selection.identity, old.identity(numerical), cutoff,
        population.group_ids, pipeline.pipeline_config.profile, pipeline.receipt, pipeline.evidence_profile,
        pipeline.receipt.publication, pipeline.receipt.recovery, pipeline.receipt.validator_receipts[0])
    records = {"programme": population, "bank": bank, "reservation": bank.reservation,
        "assay": bank.response_selection, "numerical": numerical, "cutoff": cutoff}
    return common, records


def test_six_independent_closed_gate_products_replay_complete_source_scope(closed_scope):
    common, records = closed_scope
    configs = release.gate_configs(common)
    assert len(configs) == 6
    products = tuple(release.validate_gate_inputs(config, records) for config in configs)
    assert all(value.observed_physical_unit_ids == common.group_ids for value in products)
    assert all(value.eligible_physical_unit_ids == common.group_ids and not value.invalid_physical_unit_ids for value in products)
    specification = release.gate_specification(common)
    assert len(specification.gates) == 7
    assert sum(value.applicability is MetatheoryApplicability.NOT_APPLICABLE for value in specification.gates) == 1
    declarations = tuple(release.gate_declaration(kind) for kind in release.GATES)
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourceQualificationConfig
    qualifier = MatrixSourceQualificationConfig("config.disclosed-release-source", specification, common.pipeline_receipt,
        CapabilityRegistry("registry.disclosed-release-source",
            tuple(sorted((value.manifest() for value in declarations), key=lambda value: value.registry_id))),
        tuple(sorted(products, key=lambda value: value.evidence_id)))
    result = qualifier.assess()
    assert result.disposition is MetatheoryAggregateDisposition.SUPPORTED
    assert result.complete_physical_unit_count == len(common.group_ids) == 64
    # Arithmetic/record conformance only. This has no issued producer or source
    # publication and therefore cannot pass the production custody owner.
    assert all(value.registration().native_effect is False for value in declarations)


@pytest.mark.parametrize("field", ("programme", "bank", "reservation", "assay", "numerical", "cutoff"))
def test_gate_refuses_substituted_actual_operand_pin(closed_scope, field):
    common, records = closed_scope
    original = getattr(common, field)
    if field == "cutoff":
        changed = replace(original, coordinate=Decimal(1))
    else:
        changed = replace(original, object_fingerprint="f" * 64)
    config = replace(release.gate_configs(common)[0], common=replace(common, **{field: changed}))
    with pytest.raises(ValueError, match="causally different|operand census"):
        release.validate_gate_inputs(config, records)


def test_gate_refuses_dropped_group_and_future_cutoff(closed_scope):
    common, records = closed_scope
    config = release.gate_configs(common)[0]
    with pytest.raises(ValueError, match="whole-source"):
        release.validate_gate_inputs(replace(config, common=replace(common, group_ids=common.group_ids[:-1])), records)
    future = replace(common.cutoff, phase=CausalPhase.POST_OUTCOME, coordinate=Decimal(10**9))
    with pytest.raises(ValueError, match="whole-source"):
        release.validate_gate_inputs(replace(config, common=replace(common, cutoff=future)), {**records, "cutoff": future})


def test_source_gate_declarations_use_actual_record_ports_and_keep_test_scope_out_of_global_catalog():
    from empirical_lawhood.api.recursive_operations import operation_catalog
    installed = {value.selection.capability_key for value in operation_catalog()[0]}
    for kind in release.GATES:
        declaration = release.gate_declaration(kind)
        assert declaration.capability_key not in installed
        assert declaration.config_record_type is release.ReleaseGateConfig
        assert {value.port_id for value in declaration.input_ports} == set(release.input_kinds())
        assert all(value.media_type == "application/json" for value in declaration.input_ports)


@pytest.mark.held
@pytest.mark.parametrize("population_label", ("CAL", "CONF"))
def test_held_actual_eight_source_producers_read_completed_recovery(
        tmp_path, monkeypatch, population_label):
    """Independent held SDK acceptance; no DEV fit or native future is entered."""
    import os
    from pathlib import Path

    from empirical_lawhood.api.recursive_operations import operation_catalog
    from tests.matrix_selected_e4_public_fixture import (
        ROOT, DISCLOSURE, authenticate_originals, held_selection, retained_census,
        selected_populations, selected_settings_census,
    )
    from tests.matrix_workflow_measurements import WorkflowMeasurements, matrix_observation_callbacks
    from tests.test_matrix_selected_e4_public_programme import observer_proof, retain

    selection_path = os.environ.get("EL_E4_SOURCE_SELECTION")
    if selection_path is None:
        pytest.skip("held eight-worker source acceptance requires explicit EL_E4_SOURCE_SELECTION")
    selected = held_selection(selection_path)
    assert selected.workers >= 4 and selected.numerical_threads == 1
    assert tmp_path.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    settings_before = selected_settings_census(selected)
    measurements = WorkflowMeasurements(tmp_path / "source-predecessor-measurements.json", monkeypatch,
        selection=selected.record_id, callbacks=matrix_observation_callbacks())
    originals = measurements.call("original-e3-current-custody", authenticate_originals, selected)
    original_run = originals.issued_package.run_plan_id
    original_before = measurements.call("original-e3-primary-census-before", retained_census,
        originals.writer, (original_run,))
    assert originals.package.calibration.radius is None
    populations = measurements.call("declared-populations-and-original-source-joins",
        selected_populations, originals, selected)
    programme, bank = populations.programmes[population_label], populations.banks[population_label]
    assert len(programme.group_ids) == 64 and len(programme.cases) == 64 * 9
    output = originals.writer.root.resolve(
        selected.output_relative_path + ".source-predecessor-only." + population_label.lower(), for_write=True)
    assert not output.exists(), "select a fresh explicit release-validation output namespace"
    predecessor = measurements.call("actual-eight-source-producers", release.selected_e4_source_predecessor,
        project_root=ROOT, originals=originals, programme=programme, bank=bank, selected=selected,
        directory=output, monkeypatch=monkeypatch, measurements=measurements)
    control, recovery = predecessor.controls
    plan = control.service._load_status_execution_plan(control.package.run_plan_id)
    assert len(plan.tasks) == 9
    expected_keys = {value.capability_key for value in release.shared.source_declarations()[:2]}
    expected_keys.update(release.gate_declaration(kind).capability_key for kind in release.GATES)
    expected_keys.add(release.source_closeout_declaration().capability_key)
    assert {value.capability.capability_key for value in plan.tasks} == expected_keys
    assert all(value.capability.requested_resources.memory_bytes == selected.memory_bytes_per_task
        and value.capability.requested_resources.wall_time_seconds is None for value in plan.tasks)
    assert control.service.maximum_parallel_tasks == selected.workers
    assert control.package.execution_resource_envelope_spec.maximum_parallel_tasks == selected.workers
    proof = observer_proof(control.executor, (value.task_id for value in plan.tasks))
    assert predecessor.run.succeeded and predecessor.status.succeeded and predecessor.recovered.succeeded
    assert not recovery.executor.calls
    assert len(predecessor.source.executions) == 8
    assert predecessor.source.specification.physical_unit_ids == programme.group_ids
    assert predecessor.source.result.complete_physical_unit_count == 64
    installed = {value.selection.capability_key for value in operation_catalog()[0]}
    assert not {release.gate_declaration(kind).capability_key for kind in release.GATES} & installed
    assert retained_census(originals.writer, (original_run,)) == original_before
    assert selected_settings_census(selected) == settings_before
    retain(output / "independent-source-predecessor-public-proof.json", {
        "scope": DISCLOSURE, "population": population_label, "workers": selected.workers,
        "numerical_threads": selected.numerical_threads, "assigned_source_groups": len(programme.group_ids),
        "assigned_source_cases": len(programme.cases), "actual_producer_count": len(plan.tasks),
        "public_sdk_lifecycle": "ACTUAL_EIGHT_PRODUCERS_STATUS_READ_ZERO_ENTRY_COMPLETED_RECOVERY",
        "sdk_composition": predecessor.sdk_composition_claim, "default_cli_authority_composition": "NOT_TESTED",
        "scientific_qualification": "NOT_ESTABLISHED", "DEV_acquisition_entered": False,
        "native_futures_entered": False, "original_E3_reexecuted": False,
        "original_E3_primary_custody_unchanged": True, "proof": proof,
        "original_E3_calibration_radius": None,
        "source_specification": predecessor.source.specification.to_document(),
        "source_result": predecessor.source.result.to_document(),
        "actual_producer_bindings": tuple(value.to_document() for value in predecessor.source.executions),
    })
    measurements.finish()


@pytest.mark.parametrize("role", ("runtime", "environment"))
def test_actual_raw_source_publication_uses_existing_contract_and_exact_supporting_identity(tmp_path, role):
    """Exercise actual raw custody before any original E3 or source workflow."""
    from hashlib import sha256
    from pathlib import Path
    from empirical_lawhood.planning.dataset_manifests import DatasetCapabilityBinding, DatasetCapabilityKind
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.datasets import DatasetSupportingIdentityRegistry
    from tests.test_recursive_public_service import _plane
    writer = _plane(tmp_path / "plane")
    source = Path(release.__file__) if role == "runtime" else release.ROOT / "uv.lock"
    raw = source.read_bytes()
    relative = "sources/disclosed-raw-contract/" + source.name
    identity, publication = release._raw_artifact(writer, name="raw.disclosed." + role,
        raw=raw, relative=relative)
    manifest = writer.read_manifest(relative)
    writer.verify_manifest(manifest)
    assert (manifest.logical.payload_schema, manifest.logical.media_type, manifest.logical.profile) == (
        "empirical-lawhood/source/checksummed-uninterpreted-public-bytes", "text/plain", ArtifactProfile.RAW_SOURCE_BYTES)
    assert (identity.payload_schema, identity.media_type, identity.sha256, identity.size_bytes) == (
        manifest.logical.payload_schema, manifest.logical.media_type, sha256(raw).hexdigest(), len(raw))
    assert writer.root.resolve(relative, for_write=False).read_bytes() == raw
    assert (publication.logical, publication.materialization) == (manifest.logical, manifest.materialization)
    pin = release.pin(identity, "artifact_id")
    kind = DatasetCapabilityKind.RUNTIME if role == "runtime" else DatasetCapabilityKind.ENVIRONMENT
    binding = DatasetCapabilityBinding("binding.disclosed." + role, kind, identity.artifact_id, pin)
    supporting = DatasetSupportingIdentityRegistry("supporting.disclosed." + role, (),
        (pin,) if role == "runtime" else (), (pin,) if role == "environment" else ())
    assert supporting.resolve(binding.kind, binding.registry_key) == binding.implementation == pin


@pytest.mark.parametrize("boundary", (
    "preview",
    pytest.param("before_issue", marks=pytest.mark.held),
    pytest.param("complete", marks=pytest.mark.held),
))
def test_actual_source_pipeline_public_lifecycle_boundaries(tmp_path_factory, monkeypatch, boundary):
    """Four-group TEST source lifecycle; no E3 replay or native acquisition."""
    import os
    from pathlib import Path
    from types import SimpleNamespace

    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as recipe
    from empirical_lawhood.api import recursive_prospective_authoring as author
    from tests.runtime_platform import test_study_issue as issue_owner
    from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs

    f = literal_recipe_source_inputs.__wrapped__(tmp_path_factory)
    inputs, writer = f.inputs, f.case.plane
    prefix = "disclosed-source-preview"
    profile = None
    if boundary != "preview":
        from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile, resolve_external_root_contract

        profile_path = Path(os.environ.get("EL_TEST_OPERATOR_PROFILE",
            "/media/chevre/EL/empirical-lawhood/operator-profiles/el-four-core-default.json"))
        if not profile_path.is_file():
            pytest.skip("select an existing EL operator profile for held source lifecycle acceptance")
        raw = profile_path.read_bytes()
        selected_profile = decode_canonical_bytes(raw, OperatorStorageProfile, maximum_bytes=len(raw))
        plane_path = Path(writer.root.contract.canonical_path)
        assert plane_path.is_relative_to(Path(selected_profile.external_root_locator))
        assert selected_profile.maximum_parallel_tasks >= 4
        profile = replace(selected_profile, profile_id="operator.disclosed-source-lifecycle",
            external_root_locator=str(plane_path.parent), artifact_namespace=plane_path.name)
        arguments = dict(repo_root=release.ROOT, home_root=Path.home())
        contract = resolve_external_root_contract(profile, **arguments)
        contract = replace(contract, storage_root_id=writer.root.contract.storage_root_id,
            logical_name=writer.root.contract.logical_name)
        contract = resolve_external_root_contract(profile, selected_contract=contract, **arguments)
        writer = ExternalArtifactPlane(GuardedExternalRoot(contract), validators=writer.validators,
            semantic_validations=writer.semantic_validations, custody_limits=writer.custody_limits)
        writer.root.verify(for_write=True)

    allocation = recipe.recipe_allocation(inputs)
    reservation = old.ScheduledReservation("reservation." + prefix, allocation,
        f.publish(writer, allocation, prefix + ".allocation"))
    selection = recipe.recipe_selection(inputs, reservation)
    specification = old.ScheduledSpecification("specification." + prefix, selection,
        f.publish(writer, selection, prefix + ".selection"))
    _, responses = recipe.recipe_responses(inputs, reservation, specification, f.case.provenance, "CALIBRATION")
    bank = recipe.recipe_bank(inputs, reservation=reservation, specification=specification,
        provenance=f.case.provenance,
        criterion_publication=f.publish(writer, inputs.original_preparation.mathematical_protocol, prefix + ".criterion"),
        response_publication=f.publish(writer, responses, prefix + ".responses"), phase="CALIBRATION")
    programme = recipe.recipe_programme(bank, "CALIBRATION")
    assert len(programme.group_ids) == 4 and len(programme.cases) == 36
    selected = SimpleNamespace(namespace=prefix, workers=4, numerical_threads=1,
        memory_bytes_per_task=2 * 1024**3, source_bytes_per_task=128 * 1024**2,
        output_bytes_per_task=64 * 1024**2)
    originals = SimpleNamespace(writer=writer, profile=profile)

    def disclosed_preparation(value):
        assert value is originals
        return inputs.original_preparation

    # Reuse the actual typed fixture preparation/root/campaign. Held paths bind
    # actual EL profile policy and the real filesystem inspector before effects.
    monkeypatch.setattr(release, "original_preparation", disclosed_preparation)
    observed = {}

    def call(label, operation, *args, **kwargs):
        result = operation(*args, **kwargs)
        observed[label.rsplit(".", 1)[-1]] = result
        return result

    class BeforeBoundary(RuntimeError):
        pass

    actual_author = author.author_recursive_prospective

    def author_boundary(**kwargs):
        from empirical_lawhood.kernel.evidence import EvidenceCeiling
        from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids

        preview, spec = kwargs["expected_preview"], kwargs["spec"]
        assert preview is observed["preview"]
        assert len(spec.draft.operations) == len(spec.resources.task_cells) == 9
        assert spec.resources.maximum_parallel_tasks == selected.workers
        assert spec.resources.aggregate_memory_ceiling_bytes == selected.workers * selected.memory_bytes_per_task
        source_root = spec.draft.prospective_draft
        assert not set(_required_obligation_ids(source_root.experiment)) & set(
            _required_obligation_ids(inputs.original_preparation.root.experiment))
        assert all(claim.requested_rung is None and claim.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
            for claim in source_root.experiment.claims)
        assert source_root.experiment.obligations.support.physical_unit_count == len(programme.group_ids)
        assert set(source_root.experiment.obligations.support.denominator_cell_ids) == {
            case.root_id for case in programme.cases}
        assert not kwargs["output_dir"].exists()
        observed["author_boundary"] = True
        if boundary == "preview":
            raise BeforeBoundary
        return actual_author(**kwargs)

    actual_prove = author.prove_recursive_prospective_handoff

    def prove(*args, **kwargs):
        result = actual_prove(*args, **kwargs)
        observed["proved"] = True
        return result

    def stop_before_issue(*_args, **_kwargs):
        assert boundary == "before_issue" and observed["proved"]
        observed["issue_boundary"] = True
        raise BeforeBoundary

    def forbidden(*_args, **_kwargs):
        raise AssertionError("source preview crossed its selected author/issue/worker boundary")

    monkeypatch.setattr(author, "author_recursive_prospective", author_boundary)
    monkeypatch.setattr(author, "prove_recursive_prospective_handoff", prove)
    if boundary == "preview":
        monkeypatch.setattr(author, "load_recursive_prospective_handoff", forbidden)
    if boundary != "complete":
        monkeypatch.setattr(issue_owner, "_issue_api_fixture", stop_before_issue)
        monkeypatch.setattr(release, "_sdk_execution", forbidden)
    directory = writer.root.resolve(prefix + "/source-predecessor", for_write=True)
    arguments = dict(project_root=release.ROOT, originals=originals, programme=programme, bank=bank,
        selected=selected, directory=directory, monkeypatch=monkeypatch, measurements=SimpleNamespace(call=call))
    if boundary == "complete":
        result = release.selected_e4_source_predecessor(**arguments)
        control, recovery = result.controls
        assert result.run.succeeded and result.status.succeeded and result.recovered.succeeded
        assert len(result.source.executions) == 8
        assert len(control.executor.completed) == len(control.executor.ready) == 9
        assert not any(contract.native_effect for contract in control.executor.contracts.values())
        assert control.service.maximum_parallel_tasks == selected.workers
        assert control.package.execution_resource_envelope_spec.maximum_parallel_tasks == selected.workers
        assert not recovery.executor.calls
    else:
        with pytest.raises(BeforeBoundary):
            release.selected_e4_source_predecessor(**arguments)
    assert observed["pipeline"].config.assess() == observed["pipeline"].receipt
    assert observed["preview"].design_inputs.draft.prospective_draft.evaluation_unit_ids == programme.group_ids
    assert observed["author_boundary"] is True
    if boundary == "preview":
        assert not (directory / "authoring").exists() and not (directory / "issue").exists()
    else:
        assert observed["proved"] and (directory / "authoring/authored-wave.json").is_file()
        if boundary == "before_issue":
            assert observed["issue_boundary"] and not any((directory / "issue").iterdir())
