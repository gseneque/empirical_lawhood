# SPDX-License-Identifier: MPL-2.0
"""Exposed metadata scaffolding for actual installed source-owner conformance.

No fitting, native acquisition, production trust registration or qualification
is created. The caller supplies the real completed TRAIN request/certificate
and an explicitly disclosed retained public point package. Checks requiring
that historical package are optional held checks, outside release acceptance.
"""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_experiment as domain
from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as r
from empirical_lawhood.adapters.methods import matrix_finite_dt_source_pipeline as rows_owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as bridge
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as phase
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion, ScheduledResponseSelection
from empirical_lawhood.adapters.methods.backbone_structural_transport import source_free_property_transport_source_input_parts as template
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.api.matrix_finite_dt_source_pipeline import (
    MatrixFiniteDtDatasetClock, materialize_finite_dt_source, publish_finite_dt_source_metadata)
from empirical_lawhood.kernel.authority import AuthorityAction, ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.source_pipelines import SourcePipelineArtifactProfile
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests import matrix_selected_source_predecessor as existing
from tests.matrix_selected_e4_public_fixture import _source_admissions, publication
from tests.runtime_platform.test_candidate_compiler import _fixture

ROOT = Path(__file__).resolve().parents[1]
DISCLOSURE = "EXPOSED_PUBLIC_INSTRUMENT_SOURCE_SOFTWARE_CONFORMANCE_NO_QUALIFICATION"


def future_case(tmp_path, *, plane, request, public_package):
    """Pure four-group typed future bank; no original record is rewritten."""
    namespace = "finite-dt.disclosed." + sha256(str(tmp_path).encode()).hexdigest()[:12]
    index = ScheduledSourceIndex.from_shared(reservation=request.train_manifest.reservation,
        specification=request.train_manifest.native_specification, provenances=request.train_manifest.provenances)
    original = train.source_for(request, request.sources[0].root_id, index=index)
    prototype = original.coordinate
    coordinates = []
    corners = (*product((Decimal(".5"), Decimal(2)), repeat=3), (Decimal(1),) * 3)
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    for fi, family in enumerate(families):
        for ci, (temperature, friction, coupling) in enumerate(corners):
            suffix = namespace + "." + str(fi) + "." + str(ci)
            coordinates.append(replace(prototype, coordinate_id="coordinate." + suffix, family_id=family,
                member=replace(prototype.member, member_id="member." + suffix, cross_coupling_gamma=coupling),
                primary_view=replace(prototype.primary_view, view_id="view.primary." + suffix,
                    bath_temperature=temperature, friction_gamma=friction),
                fine_view=replace(prototype.fine_view, view_id="view.fine." + suffix,
                    bath_temperature=temperature, friction_gamma=friction)))
    coordinates = tuple(sorted(coordinates, key=lambda value: value.coordinate_id))
    roots, scopes = [], []
    for fi, family in enumerate(families):
        group = "group." + namespace + "." + str(fi)
        local = tuple(value for value in coordinates if value.family_id == family)
        streams = tuple(MatrixHistorySeed(purpose, sha256((DISCLOSURE + group + purpose).encode()).hexdigest())
            for purpose in HISTORY_PURPOSES)
        for ci, coordinate in enumerate(local):
            root = old.MatrixProgrammeRoot("root." + group + "." + str(ci), group, "regime." + coordinate.coordinate_id,
                coordinate.coordinate_id, old.MatrixProgrammeRole.CALIBRATION, coordinate.clock_id)
            roots.append(old.ScheduledRoot(root, old.coordinate_identity(coordinate), streams))
        scopes.append(old.ScheduledMatchedScope("scope." + group, old.MatrixProgrammeRole.CALIBRATION,
            (group,), tuple(old.coordinate_identity(value) for value in local),
            "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU"))
    allocation = replace(request.future_manifest.reservation.allocation, allocation_id="allocation." + namespace,
        coordinates=coordinates, roots=tuple(sorted(roots, key=lambda value: value.root.root_id)), matched_scopes=tuple(scopes))
    reservation = old.ScheduledReservation("reservation." + namespace, allocation,
        publication(plane, allocation, "allocation." + namespace))
    policy = original.policy
    selected = old.ScheduledSelection("selection." + namespace, old.identity(reservation), original.numerical_design,
        (policy,), tuple((old.coordinate_identity(value), old.identity(policy)) for value in coordinates))
    specification = old.ScheduledSpecification("specification." + namespace, selected,
        publication(plane, selected, "selection." + namespace))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=(original.provenance,))
    sources = tuple(index.resolve(index.reference(source_id="source." + value.root.root_id,
        root_id=value.root.root_id, provenance=original.provenance.identity)) for value in allocation.roots)
    prototype_protocol = request.protocols[0]
    protocols = tuple(replace(prototype_protocol, protocol_id="protocol." + source.root_id,
        public_source=ScheduledPublicSource.from_source(source),
        templates=replace(prototype_protocol.templates, operand_id="templates." + source.root_id,
            source=old.identity(source), producers=(old.identity(source),))) for source in sources)
    panels = []
    for source in sources:
        group = source.root.root.independent_group_id
        if any(group == key for key, _ in panels):
            continue
        future = tuple(MatrixHistorySeed(purpose, sha256((DISCLOSURE + ".future." + group + purpose).encode()).hexdigest())
            for purpose in HISTORY_PURPOSES)
        panels.append((group, (
            ScheduledResponsePanel("panel." + group + ".0", group, "COMMON_NOISE_PANEL",
                "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", source.root.streams),
            ScheduledResponsePanel("panel." + group + ".1", group, "INDEPENDENT_FUTURE",
                "FRESH_DECLARED_FUTURE_START_AT_CUTOFF", future))))
    criterion = ScheduledCalibrationCriterion("criterion." + namespace, "unit.disclosed-whole-group", len(families),
        Decimal(0), families, "COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY")
    responses = ScheduledResponseSelection("responses." + namespace, ObjectIdentity.from_record(allocation.allocation_id, allocation), protocols, tuple(panels),
        request.template_publications, criterion)
    responses.validate_allocation(allocation)
    forecast = bridge.SelectedE3E4ForecastDesign("forecast-design." + namespace, public_package, old.identity(allocation),
        request.mathematical_protocol, publication(plane, request.mathematical_protocol, "criterion-record." + namespace))
    design = bridge.SelectedE3E4Design("design." + namespace, len(families), Decimal(".95"),
        tuple(ScheduledProgrammeFactor(name, "LOG", Decimal(".5"), Decimal(1), Decimal(2))
            for name in ("temperature", "friction", "coupling")), len(families))
    bank = phase.SelectedE4PhaseBank("bank." + namespace, reservation, specification, (original.provenance,),
        tuple(value.reference for value in sources), request.future_manifest.audit,
        request.future_manifest.audit_publication, forecast, responses,
        publication(plane, responses, "responses." + namespace), design, "CALIBRATION")
    programme = phase.SelectedE4PhaseProgramme.from_bank(bank, programme_id="programme." + namespace)
    cutoff = InformationCutoff("cutoff." + namespace, prototype.clock_id, CausalPhase.PREPARATION, Decimal(0))
    return SimpleNamespace(namespace=namespace, writer=plane, request=request, bank=bank, programme=programme,
        original_future_reservation=request.future_manifest.reservation, cutoff=cutoff)


def _materialization(future, *, rows_module=rows_owner):
    """Execute the actual installed source materializer under TEST dataset authority."""
    rows_owner = rows_module
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.planning.dataset_authority import (
        DatasetStorageScope, DatasetWorkEnvelope, DatasetFileLimits, DatasetControlLimits,
        DatasetAuthorizationIssuerRegistration, issue_dataset_operation_authorization)
    from empirical_lawhood.planning.datasets import DatasetEvidenceClass, DatasetMaterializationClass
    from empirical_lawhood.api import matrix_finite_dt_dataset_metadata as metadata_owner
    namespace, writer, programme, bank = future.namespace, future.writer, future.programme, future.bank
    budget = ResourceBudget(1, 2 * 1024**3, 0, 60, 128 * 1024**2, 64 * 1024**2)
    rows = getattr(rows_owner, 'ROW_KIND', rows_module.MatrixFiniteDtPendingSourceRows if hasattr(rows_module, 'MatrixFiniteDtPendingSourceRows') else rows_module.MatrixPreparedPendingSourceRows).from_bank(programme, bank, record_id="rows." + namespace)
    rule = getattr(rows_owner, 'RULE_KIND', rows_module.MatrixFiniteDtSourceValidationRule if hasattr(rows_module, 'MatrixFiniteDtSourceValidationRule') else rows_module.MatrixPreparedSourceValidationRule)("rule." + namespace, programme.identity, bank.identity, rows.identity)
    source = writer.write(ArtifactWriteRequest("source." + namespace, "sources/" + namespace + "/rows.json",
        rows.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "source." + namespace,
        "sources/" + namespace, rows.canonical_bytes(), r.PROSPECTIVE, (), r.BLIND))
    output_relative = "derived/" + namespace + "/rows.json"
    profile, _, _, _ = template._profile(label=namespace)
    transform = rows_owner.transform_capability(budget)
    adapter = rows_owner.source_capability(budget)
    registry, datasets = metadata_owner.dataset_registries(budget, maximum_rows=len(rows.rows), row_kind=type(rows))
    edge = replace(profile.transform_edges[0], edge_id="edge." + namespace,
        dataset_transform_registry_id=transform.registry_id,
        selection=replace(profile.transform_edges[0].selection, capability_key=transform.capability_key,
            implementation_sha256=transform.implementation_sha256), config=rule.identity,
        domain_schema=rows.SCHEMA, codomain_schema=rows.SCHEMA, source_media_type="application/json",
        destination_media_type="application/json", source_format_profile_id=rows_owner.FORMAT_ID,
        destination_format_profile_id=rows_owner.FORMAT_ID, semantic_validator=rule.identity, resource_budget=budget)
    coordinates = tuple(replace(value, coordinate_id="coordinate." + namespace + "." + str(index),
        field_id=("physical-unit", "invalid-disposition", "root")[index], clock_id=future.cutoff.clock_id)
        for index, value in enumerate(profile.input_coordinates))
    edge = replace(edge, input_coordinates=coordinates, output_coordinates=coordinates)
    contract = ObjectIdentity.from_record(writer.root.contract.storage_root_id, writer.root.contract)
    source_scope = DatasetStorageScope("scope." + namespace + ".source", contract, "sources/" + namespace)
    destination_scope = DatasetStorageScope("scope." + namespace + ".destination", contract, "derived/" + namespace)
    control_scope = DatasetStorageScope("scope." + namespace + ".control", contract, "dataset-operations/" + namespace)
    envelope = DatasetWorkEnvelope(budget, DatasetFileLimits(2, 2, 0, len(rows.canonical_bytes())),
        DatasetControlLimits(1024**2, len(rows.rows), 1024**2, 32))
    runtime, _ = existing._raw_artifact(writer=writer, name="runtime." + namespace,
        raw=Path(metadata_owner.__file__).read_bytes(), relative="sources/" + namespace + "/metadata-runtime.py")
    environment, _ = existing._raw_artifact(writer=writer, name="environment." + namespace,
        raw=(ROOT / "uv.lock").read_bytes(), relative="sources/" + namespace + "/uv.lock")
    manifest, _ = metadata_owner.make_dataset_manifest(namespace=namespace, source_publication=source,
        output_relative_path=output_relative, rows=rows, rule=rule, cutoff=future.cutoff,
        source_scope=source_scope, destination_scope=destination_scope, control_scope=control_scope,
        envelope=envelope, runtime=runtime, environment=environment)
    writer.write(ArtifactWriteRequest(manifest.manifest_id, control_scope.relative_prefix + "/" + metadata_owner.MANIFEST_FILENAME,
        manifest.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "dataset-manifest." + namespace,
        control_scope.relative_prefix, manifest.canonical_bytes(), r.PROSPECTIVE, (), r.BLIND))
    numerical = old.identity(bank.specification.selection.numerical_design)
    profile = replace(profile, profile_id="profile." + namespace, source_id="source." + namespace,
        source_selection=replace(profile.source_selection, capability_key=adapter.capability_key,
            implementation_sha256=adapter.implementation_sha256), source_config=rule.identity,
        source_materialization=ObjectIdentity.from_record(source.materialization.materialization_id, source.materialization),
        expected_source_sha256=rows.fingerprint(), expected_source_size_bytes=len(rows.canonical_bytes()),
        licence_id=DISCLOSURE, operator_storage_root_id=writer.root.contract.storage_root_id,
        source_relative_locator=source.materialization.relative_path, source_schema=rows.SCHEMA, source_media_type="application/json",
        source_format_profile_id=rows_owner.FORMAT_ID, input_coordinates=coordinates, transform_edges=(edge,),
        output_schema=rows.SCHEMA, output_media_type="application/json", output_filename_suffix=".json",
        output_artifact_profile=SourcePipelineArtifactProfile.CANONICAL_JSON, output_coordinates=coordinates,
        semantic_validators=(rule.identity,), causal_cutoff=r.pin(future.cutoff, "cutoff_id"),
        dataset_transformation_manifest=r.pin(manifest, "manifest_id"), resource_ceiling=budget,
        maximum_row_count=len(rows.rows), maximum_physical_unit_count=len(programme.group_ids),
        scratch_namespace="scratch/" + namespace, output_relative_locator=output_relative, evidence_world_id="deterministic-simulator",
        observation_operator=(bank.response_selection.identity if hasattr(bank, "response_selection") else bank.assay.identity), numerical_view_ids=(numerical.object_id,),
        receiver_semantics_id="receiver." + namespace, validity_contract_id="validity." + namespace,
        uncertainty_contract_id="uncertainty." + namespace)
    request = template._dataset_request(profile)
    now = datetime.now(UTC).replace(microsecond=0)
    at, until = now.strftime("%Y-%m-%dT%H:%M:%SZ"), (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    commit = implementation_binding(ROOT).observed_git_head
    policy = replace(template._dataset_policy(profile, request), policy_id="policy." + namespace,
        source_scopes=(source_scope,), destination_scope=destination_scope, control_write_scope=control_scope,
        work_envelope_ceiling=envelope, implementation_commit=commit, evidence_class=DatasetEvidenceClass.METADATA_ONLY,
        materialization_class=DatasetMaterializationClass.METADATA_OBSERVATION, issued_by="issuer." + namespace,
        authorized_approver_id="approver." + namespace, valid_from_utc=at, valid_until_utc=until, reason_codes=(DISCLOSURE,))
    request = replace(request, request_id="request." + namespace, policy=r.pin(policy, "policy_id"), implementation_commit=commit,
        evidence_class=DatasetEvidenceClass.METADATA_ONLY, materialization_class=DatasetMaterializationClass.METADATA_OBSERVATION,
        valid_from_utc=at, valid_until_utc=until, requested_by="operator." + namespace, reason_codes=(DISCLOSURE,),
        source_scopes=(source_scope,), destination_scope=destination_scope, control_write_scope=control_scope, work_envelope=envelope)
    signer = template._Signer()  # Explicit TEST signer, never a production trust registration.
    issuer = DatasetAuthorizationIssuerRegistration("issuer-registration." + namespace, "issuer." + namespace,
        frozenset((AuthorityAction.DATASET_TRANSFORMATION,)), transform.implementation_sha256, "1.0.0",
        signer.signature_algorithm, signer.signature_version, signer.verification_key_hex, r.BLIND)
    clock = MatrixFiniteDtDatasetClock("clock." + namespace)
    authorization = issue_dataset_operation_authorization(policy=policy, request=request,
        authorization_id="authorization." + namespace, approved_by=policy.authorized_approver_id,
        issuer_registration=issuer, signer=signer, clock=clock)
    materialization = materialize_finite_dt_source(writer=writer, programme=programme, bank=bank, rows=rows, rule=rule,
        source_publication=source, profile=profile, source_manifest=adapter, capability_registry=registry,
        dataset_registry=datasets, dataset_operation_request=request, policy=policy, authorization=authorization,
        issuer_registration=issuer, decision_clock=clock, verification_relative_path="dataset-operations/" + namespace + "/verification.json",
        record_id=namespace)
    return materialization, rule


def _source_test_template():
    """Numerical TEST framing; no continuum, transport or sampling warrant."""
    root, _ = _fixture()
    world = replace(root.system.world, label="Exposed TEST numerical reference framing",
        kind=WorldKind.NUMERICAL_SIMULATOR,
        unrepresented_physics=("continuum-limit", "physical-transfer", "population-sampling"),
        maximum_evidence=EvidenceCeiling.NON_PROMOTABLE)
    # Retain the exact world/unit/view/envelope IDs so all fixture joins remain
    # explicit. The source owner replaces the old claims with TEST-only claims.
    return replace(root, system=replace(root.system, world=world))


def source_case(tmp_path, *, future, certificate, project_root=ROOT):
    """Compose installed public source protocol, actual transform and exact inputs."""
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.recursive_prospective_authoring import preview_recursive_prospective_candidate
    from empirical_lawhood.kernel.experimental_design import UnitAllocation, UnitRoleAssignment, IndependentUnit
    from empirical_lawhood.planning.evidence_profiles import (
        EvidenceWorldKind, bind_profile_selection, build_observation_evidence_world_registry)
    from empirical_lawhood.runtime.experiment_resources import bind_execution_resources
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
    from tests.experiment_entry_support import standard_authoring_for_draft
    namespace, writer, bank, programme = future.namespace, future.writer, future.bank, future.programme
    materialized, rule = _materialization(future)
    profile_registry = build_observation_evidence_world_registry()
    world, = (value for value in profile_registry.world_profiles if value.world_kind is EvidenceWorldKind.DETERMINISTIC_SIMULATOR)
    evidence_profile = bind_profile_selection(selection_id="selection.source." + namespace, draft_id="draft." + namespace,
        registry=profile_registry, world_profile_id=world.profile_id, objective_profile_id="objective.observation-order", requested_rungs=())
    budget = ResourceBudget(1, 2 * 1024**3, 0, None, 128 * 1024**2, 64 * 1024**2)
    scope = r.MatrixFiniteDtSourceScope("scope." + namespace, programme.identity, bank.identity, old.identity(bank.reservation),
        old.identity(future.original_future_reservation), bank.response_selection.identity,
        old.identity(bank.specification.selection.numerical_design), certificate.identity, future.cutoff, programme.group_ids,
        materialized.config.profile, materialized.config.assess(), evidence_profile, materialized.verification.identity,
        materialized.verification.identity, budget)
    metadata = publish_finite_dt_source_metadata(writer=writer, scope=scope, materialization=materialized,
        output_directory=Path(writer.root.contract.canonical_path) / "finite-dt-controls" / namespace / "metadata")
    operands = {"scope": scope, "programme": programme, "bank": bank, "reservation": bank.reservation,
        "original-reservation": future.original_future_reservation, "assay": bank.response_selection,
        "numerical": bank.specification.selection.numerical_design, "cutoff": future.cutoff, "certificate": certificate}
    template_root = _source_test_template()
    training_units = tuple(IndependentUnit(value.group_id, certificate.request.object_id, "family.disclosed-control",
        ("fine", "primary"), True) for value in certificate.controls)
    training = UnitAllocation("allocation.source-contract." + namespace, (certificate.request,), training_units,
        tuple(UnitRoleAssignment(value.unit_id, "development") for value in training_units))
    # This selects only TEST scientific framing. Real gate/byte/receipt/custody
    # implementations and all original TRAIN bytes remain unchanged.
    with patch.object(existing, "original_preparation", return_value=SimpleNamespace(root=template_root, training_allocation=training)), patch.object(existing, "KEY", r.NAMESPACE):
        root = existing._source_root(object(), programme, scope, namespace=namespace,
            budget=ResourceBudget.aggregate((budget,) * (len(r.GATES) + 3)))
    terminals = tuple((name, budget) for name in ("adjudicate", "pipeline", "qualification"))
    draft, records, _, _ = domain.compose_source_draft(scope=scope, scientific_operands=operands,
        pipeline=materialized.config, root=root, campaign=root.campaign, draft_id="draft." + namespace, terminal_budgets=terminals,
        operand_access={name: (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
            if name in ("bank", "programme") else (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
            for name in operands})
    source_configs, qualifications = _source_admissions(draft, records, (), root=root, prefix=namespace,
        observation_operator=bank.response_selection.identity)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    draft = _source_projection(draft, SimpleNamespace(source_configs=source_configs, qualifications=qualifications),
        {value.logical_artifact_id: dict(records)[value.input_id].VERSION for value in draft.external_inputs})
    registrations, registry, codecs = operation_catalog()
    implementation = implementation_binding(project_root)
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit=implementation.observed_git_head, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs=codecs,
        implementation_sha256=implementation.code_sources_sha256)
    standard, formal = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
        formal_method_capability_key=r.NAMESPACE + ".source_identity")
    input_dir = tmp_path / "source-inputs"
    input_dir.mkdir(parents=True, exist_ok=False)
    bindings = []
    for external_id, record in records:
        external, = (value for value in draft.external_inputs if value.input_id == external_id)
        path = input_dir / (sha256(external.logical_artifact_id.encode()).hexdigest() + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append((external.logical_artifact_id, path))
    source_configs = tuple(sorted(source_configs, key=lambda value: value.fingerprint()))
    for config in source_configs:
        path = input_dir / (config.fingerprint() + ".json")
        path.write_bytes(config.canonical_bytes())
        bindings.append((config.fingerprint(), path))
    scientific_operands = tuple(sorted((RecursiveProspectiveOperand(value.logical_artifact_id, value.expected_content_sha256,
        value.maximum_size_bytes, value.payload_schema, value.media_type, value.outcome_access, value.visibility_ceiling)
        for value in draft.external_inputs), key=lambda value: value.logical_artifact_id))
    specification_id = "specification." + namespace
    design = RecursiveProspectiveDesignInputs("prospective." + specification_id, draft, standard.entry_package,
        formal.formal_methods, formal.source_inventories, qualifications, draft.prospective_draft.design_inputs, scientific_operands)
    preview = preview_recursive_prospective_candidate(design_inputs=design, project_root=project_root,
        artifact_writer=writer, input_bindings=tuple(bindings))
    selected = SimpleNamespace(workers=4, memory_bytes_per_task=budget.memory_bytes,
        source_bytes_per_task=budget.source_scan_bytes, output_bytes_per_task=budget.output_bytes)
    resources = bind_execution_resources(existing._resources(draft, selected, namespace), issued_extensions=preview.issued_extensions)
    authoring = design.bind_resources(resources)
    selection = domain.MatrixFiniteDtSourceQualificationSelection("selection." + namespace, scope, programme, bank,
        future.original_future_reservation, certificate, materialized.rows, rule, materialized.source_publication,
        materialized.output_publication, materialized.verification, materialized.verification_publication,
        materialized.config, authoring, source_configs, future.request.exposure_support, metadata, terminals)
    specification = domain.MatrixFiniteDtSourceQualificationSpecification(specification_id, selection.identity, 4)
    execution = ExecutionSelection(4, "main-locked", ObjectIdentity.from_record("recursive-member.implementation", preview.implementation),
        writer.root.contract.canonical_path)
    preparation = domain.prepare(specification, scientific_inputs={"source": domain.source_allocation(selection)},
        method_inputs=selection, execution=execution)
    return SimpleNamespace(selection=selection, specification=specification, preparation=preparation,
        materialization=materialized, future=future, preview=preview, input_bindings=tuple(bindings), operational=selected)



@pytest.mark.held
def test_real_future_bank_refuses_reserved_independent_panel_alias_before_materialization(tmp_path):
    """Actual typed stream alias; names/groups differ and no native work begins."""
    import os
    import pytest
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import selected_public_package_types
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from tests.test_matrix_finite_dt_source import _certificate, _control
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    selected_path = os.environ.get("EL_FINITE_DT_DISCLOSED_PUBLIC_PACKAGE")
    if selected_path is None:
        pytest.skip("select the already retained disclosed TEST point package; never fit a new fixture")
    raw = Path(selected_path).read_bytes()
    import json
    document = json.loads(raw)
    kind, = (value for value in selected_public_package_types()
        if (value.SCHEMA, value.VERSION) == (document["schema"], document["version"]))
    public = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    assert public.canonical_bytes() == raw
    (tmp_path / "metadata").mkdir()
    training = fresh_training_metadata_case(tmp_path / "metadata")
    future = future_case(tmp_path, plane=training.plane, request=training.request, public_package=public)
    certificate = replace(_certificate(training, (_control(training, 0, available=True),)),
        future_bank=future.bank.identity, future_group_ids=future.programme.group_ids, cutoff=future.cutoff)
    r.require_source_stream_separation(certificate, future.bank, future.original_future_reservation, future.programme.group_ids)
    _, panels = future.bank.response_selection.panels[0]
    independent, = (value for value in panels if value.role == "INDEPENDENT_FUTURE")
    reserved_group = future.original_future_reservation.allocation.roots[0].root.independent_group_id
    reserved_panel = replace(independent, panel_id="panel.disclosed.original-reserved", independent_group_id=reserved_group)
    assert reserved_panel.panel_id != independent.panel_id and reserved_panel.independent_group_id != independent.independent_group_id
    copied = replace(certificate, reserved_future_effective_seeds=tuple(sorted({
        *certificate.reserved_future_effective_seeds, *(stream.effective_seed for stream in reserved_panel.streams)})))
    with pytest.raises(ValueError, match="reserved original future.*effective stream"):
        r.require_source_stream_separation(copied, future.bank, future.original_future_reservation, future.programme.group_ids)


def test_source_projection_preserves_actual_compiler_role_contract_and_rejects_substitution():
    """Actual canonical bytes and compiler source owner; no bank, fit or I/O."""
    import pytest
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveStudyDraft
    from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
    from empirical_lawhood.runtime.candidate_compiler import ScientificInputRole, _source_diagnostics

    root, context = _fixture()
    template = context.template(root.dag_template_key)
    original, = template.graph.external_inputs
    record = root.system
    for role in ("SOURCE", "HISTORY", "QUALIFICATION"):
        external = RecursiveExternalInput(original.input_id, original.logical_artifact_id,
            record.SCHEMA, "application/json", len(record.canonical_bytes()), r.BLIND, r.PROSPECTIVE,
            record.fingerprint(), role)
        draft = RecursiveStudyDraft("draft.disclosed-role-contract", root.question, root.campaign,
            (), (), (), (), (external,), (), (), prospective_draft=root)
        configs, qualifications = _source_admissions(draft, ((external.input_id, record),), (),
            root=root, prefix="disclosed-role-contract", observation_operator=context.qualifications[0].observation_operator)
        selection = SimpleNamespace(source_configs=configs, qualifications=qualifications)
        projected = _source_projection(draft, selection, {external.logical_artifact_id: record.VERSION})
        scientific_role = ScientificInputRole(role)
        fields = dict(scientific_role=scientific_role, payload_schema=record.SCHEMA,
            maximum_size_bytes=external.maximum_size_bytes, outcome_access=external.outcome_access,
            visibility_ceiling=external.visibility_ceiling)
        graph = replace(template.graph, external_inputs=(replace(original, **fields,
            expected_content_sha256=record.fingerprint()),), edges=tuple(replace(edge, **fields)
                if edge.external_input_id == original.input_id else edge for edge in template.graph.edges))
        diagnostics, accepted = _source_diagnostics(projected.prospective_draft,
            replace(context, qualifications=qualifications), replace(template, graph=graph))
        assert not diagnostics, diagnostics
        assert accepted == (ObjectIdentity.from_record(qualifications[0].receipt_id, qualifications[0]),)
        wrong = (SourceMaterializationRole.OBSERVATION_STREAM
            if configs[0].role is SourceMaterializationRole.CALIBRATION else SourceMaterializationRole.CALIBRATION)
        with pytest.raises(ValueError, match="projection substitutes.*role"):
            _source_projection(draft, SimpleNamespace(source_configs=(replace(configs[0], role=wrong),),
                qualifications=qualifications), {external.logical_artifact_id: record.VERSION})


def _disclosed_metadata_future(tmp_path):
    """Metadata-only TEST operands; no authentic acquisition or qualification."""
    import os
    import pytest
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import selected_public_package_types
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    selected_path = os.environ.get("EL_FINITE_DT_DISCLOSED_PUBLIC_PACKAGE")
    if selected_path is None:
        pytest.skip("select retained disclosed point-package bytes; never fit or acquire a fixture")
    raw = Path(selected_path).read_bytes()
    import json
    document = json.loads(raw)
    kind, = (value for value in selected_public_package_types()
        if (value.SCHEMA, value.VERSION) == (document["schema"], document["version"]))
    package = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    assert package.canonical_bytes() == raw
    (tmp_path / "metadata").mkdir()
    training = fresh_training_metadata_case(tmp_path / "metadata")
    return future_case(tmp_path, plane=training.plane, request=training.request, public_package=package)


@pytest.mark.held
def test_actual_pending_inspector_and_closed_canonical_verifier_precede_materialization(tmp_path):
    from empirical_lawhood.api import matrix_finite_dt_dataset_metadata as metadata
    from empirical_lawhood.infrastructure.dataset_evidence import ExternalDatasetEvidenceVerifier, EXTERNAL_DATASET_EVIDENCE_SCHEMA_IDS
    future = _disclosed_metadata_future(tmp_path)
    invoked = []
    original_inspect = metadata.inspect_pending_source
    original_verify = ExternalDatasetEvidenceVerifier.verify
    def inspect(**kwargs):
        assert not future.writer.root.resolve("derived/" + future.namespace + "/rows.json", for_write=False).exists()
        invoked.append("actual-inspector")
        return original_inspect(**kwargs)
    def verify(self, request, *, maximum_bytes):
        assert self.registration.supported_evidence_schema_ids == EXTERNAL_DATASET_EVIDENCE_SCHEMA_IDS
        assert not future.writer.root.resolve("derived/" + future.namespace + "/rows.json", for_write=False).exists()
        invoked.append("actual-canonical-verifier")
        return original_verify(self, request, maximum_bytes=maximum_bytes)
    with patch.object(metadata, "inspect_pending_source", side_effect=inspect), patch.object(
            ExternalDatasetEvidenceVerifier, "verify", new=verify):
        materialized, _ = _materialization(future)
    assert invoked == ["actual-canonical-verifier", "actual-inspector"]
    assert materialized.config.profile.source_format_profile_id == rows_owner.FORMAT_ID
    assert materialized.rows == rows_owner.MatrixFiniteDtPendingSourceRows.from_bank(
        future.programme, future.bank, record_id=materialized.rows.record_id)


@pytest.mark.held
def test_pending_source_consumer_replays_real_manifest_and_rejects_registry_lookalike(tmp_path):
    import pytest
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import authenticate_finite_dt_source_materialization
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    future = _disclosed_metadata_future(tmp_path)
    materialized, rule = _materialization(future)
    def replay(config):
        authenticate_finite_dt_source_materialization(writer=future.writer, programme=future.programme,
            bank=future.bank, rows=materialized.rows, rule=rule,
            pipeline=SimpleNamespace(pipeline_config=config, receipt=materialized.config.assess()),
            source_publication=materialized.source_publication, output_publication=materialized.output_publication,
            verification=materialized.verification, verification_publication=materialized.verification_publication)
    replay(materialized.config)
    registry = materialized.config.dataset_registry
    original, = registry.inspectors
    wrong = replace(original, capability=replace(original.capability, implementation_sha256="0" * 64))
    with pytest.raises(PermissionError, match="actual installed pending inspector"):
        replay(replace(materialized.config, dataset_registry=replace(registry, inspectors=(wrong,))))
    profile = materialized.config.profile
    unsupported = "unsupported-pending-source-format"
    edge = replace(profile.transform_edges[0], source_format_profile_id=unsupported,
        destination_format_profile_id=unsupported)
    with pytest.raises(PermissionError, match="actual installed pending inspector"):
        replay(replace(materialized.config,
            profile=replace(profile, source_format_profile_id=unsupported, transform_edges=(edge,)),
            dataset_registry=replace(registry, inspectors=(), evidence_verifiers=())))
    manifest_path = future.writer.root.resolve(
        materialized.config.dataset_operation_request.control_write_scope.relative_prefix + "/dataset-transformation.json",
        for_write=False)
    original_raw = manifest_path.read_bytes()
    manifest_path.write_bytes(original_raw + b" ")
    with pytest.raises((ValueError, PermissionError, ArtifactIdentityConflict)):
        replay(materialized.config)
