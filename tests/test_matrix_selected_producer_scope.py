# SPDX-License-Identifier: MPL-2.0
"""Pure producer-scope controls, with no real issue, source or custody claims."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_selected_producer_scope as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_composition as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import ProtectedE3FitConfig, ProtectedE3StatisticalConfig, statistical_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_original_publications import ProtectedE3OriginalPublications
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3NativeSourceManifest
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.study_authoring import DesignOrigin, DesignOriginKind, StudyDraft, StudyDraftLifecycle
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry, CapabilityRequirement
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec
from tests.test_matrix_selected_package import package as exposed_package, reference
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_sampling_follow_on import prior_product
from tests.runtime_platform.test_candidate_compiler import _fixture as candidate_fixture


def unpublished_reference(pin, *, artifact_id=None, materialization_id=None, size=1):
    """Only immutable locator shapes, without any bytes or publication act."""
    name = pin.object_id if artifact_id is None else artifact_id
    generic = ArtifactGenericValidation("validator.exposed.producer", "1.0.0", "a"*64, pin.object_schema, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity(name, pin.object_fingerprint, pin.object_schema, ArtifactProfile.CANONICAL_JSON,
        "application/json", Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND, generic)
    physical = ArtifactMaterialization(materialization_id or "materialization." + name, name, "storage.exposed", "exposed/" + name + ".json",
        pin.object_fingerprint, size, "none")
    sidecar = replace(physical, materialization_id=physical.materialization_id + ".manifest", relative_path=physical.relative_path + ".manifest.json")
    return ArtifactWriteResult(logical, physical, sidecar, False)


def case_for(phase, *, frozen=None, training_coordinates=None):
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
    frozen = exposed_package() if frozen is None else frozen
    family = selected_e3_product_family(frozen.specification)
    if family.configured:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import (
            ConfiguredProtectedE3FitConfig as FitConfig, ConfiguredProtectedE3StatisticalConfig as StatisticalConfig, fit_capability_key)
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import ConfiguredProtectedE3OriginalPublications as OriginalPublications
    else:
        FitConfig, StatisticalConfig, OriginalPublications = ProtectedE3FitConfig, ProtectedE3StatisticalConfig, ProtectedE3OriginalPublications
    operation, mode = {"fit": ("fit", ""), "model-freeze": ("freeze", "model"),
        "calibrate": ("calibrate", ""), "calibration-freeze": ("freeze", "calibration")}[phase]
    task_id = family.statistical_task_id(frozen.specification.identity, frozen.allocation.identity, operation, mode=mode)
    census = tuple((role, len(frozen.allocation.unit_ids(role))) for role in ("calibration", "evaluation"))
    if phase == "fit":
        manifest_pin = reference("manifest.exposed.producer", ProtectedE3NativeSourceManifest)
        manifest_pub = unpublished_reference(manifest_pin)
        originals = OriginalPublications(
            record_id="originals.exposed.producer",
            specification=frozen.specification.identity,
            source_manifest=manifest_pin,
            training_allocation=frozen.prefit.training_allocation,
            manifest_publication=manifest_pub,
            training_allocation_publication=unpublished_reference(frozen.prefit.training_allocation),
            exposure_census_publication=unpublished_reference(reference("census.exposed.producer", MatrixFactorExposureCensus)))
        pubs = tuple((key, unpublished_reference(ObjectIdentity(artifact.artifact_id, artifact.payload_schema, "1.0.0", artifact.sha256),
            artifact_id=artifact.artifact_id, materialization_id=materialization, size=artifact.size_bytes), availability)
            for key, artifact, materialization, availability in frozen.prefit.publications)
        arguments = ("config." + task_id, frozen.specification.identity, frozen.allocation.identity,
            census, manifest_pin, frozen.prefit.training_allocation, frozen.prefit.fit_cutoff, pubs)
        if family.configured:
            if training_coordinates is None:
                raise ValueError("configured producer control requires its actual TRAIN coordinate census")
            config = FitConfig(*arguments, training_coordinates, originals)
        else:
            config = FitConfig(*arguments, originals)
    else:
        config = StatisticalConfig("config." + task_id, operation,
            frozen.specification.identity, frozen.allocation.identity, census, mode)
    product = {"fit": frozen.models, "model-freeze": frozen.model_freeze,
        "calibrate": frozen.calibration, "calibration-freeze": frozen.calibrated_freeze}[phase]
    capability_key = (fit_capability_key(frozen.models.training_features.object_schema, frozen.models.training_outcomes.object_schema)
        if family.configured and phase == "fit" else family.namespace + "." + phase)
    declaration, = (value for value in family.operation_declarations() if value.capability_key == capability_key)
    manifest = declaration.manifest()
    binding = replace(prior_product(owner._reference(product)).prior_execution, task_id=task_id)
    config_ref = CapabilityConfigRef(config.record_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), "input.config.exposed.producer")
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        config_ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        declaration.evidence_ceiling, declaration.outcome_access, declaration.resources)
    output_access, output_ceiling = declaration.outcome_access, declaration.visibility_ceiling
    external = (ExternalInputSpec("config", config_ref.artifact_id, config.fingerprint(), config.SCHEMA,
        "application/json", len(config.canonical_bytes()), output_ceiling, output_access, None),)
    outputs = tuple(ArtifactOutputSpec(task_id + "." + row.output_id,
        binding.logical_artifact_id if row.output_id == "product" else "output.exposed.prefit",
        "exposed/" + row.output_id + ".json", row.payload_schema, row.profile, row.media_type,
        output_ceiling, (), output_access) for row in declaration.outputs)
    task = ExecutionTask(task_id, declaration.stage, requirement, manifest.implementation_sha256, (), external, outputs,
        (), BarrierKind.FREEZE if phase.endswith("freeze") else BarrierKind.NONE, 1, ("obligation.exposed.producer",), scientific_inputs=())
    generic = ArtifactGenericValidation("validation.exposed.original-output", "1.0.0", "b"*64, product.SCHEMA, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity(binding.logical_artifact_id, product.fingerprint(), product.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", output_ceiling, (), output_access, generic)
    units = tuple(sorted((*frozen.allocation.unit_ids("calibration"), *frozen.allocation.unit_ids("evaluation"))))
    original_root, _ = candidate_fixture()
    system = replace(original_root.system, world=replace(original_root.system.world,
        kind=owner.WorldKind.NUMERICAL_SIMULATOR, unrepresented_physics=("physical-transfer",)))
    root = StudyDraft("draft.exposed.producer", StudyDraftLifecycle.DRAFT, "Software scope control", ("alternative.exposed",),
        DesignOrigin("origin.exposed", DesignOriginKind.ORDINARY_THEORY_PREDECLARED, ("input.exposed",), Visibility.PROSPECTIVE),
        (), (), units, (), (), (), system, None, None, "template.exposed", (), (), declaration.resources)
    package = SimpleNamespace(registry=CapabilityRegistry("registry.exposed.producer", (manifest,)),
        issued_study=SimpleNamespace(candidate=SimpleNamespace(authoring_package=SimpleNamespace(base=SimpleNamespace(draft=root)))))
    programme = SimpleNamespace(point_design=SimpleNamespace(package=frozen), nomination=None, assay=None)
    arguments = dict(programme=programme, binding=binding, package=package,
        execution_plan=SimpleNamespace(tasks=(task,)),
        receipt=SimpleNamespace(run_id=binding.run_id, task_id=task_id), logical=logical, writer=None, read_scope=None)
    return SimpleNamespace(arguments=arguments, config=config, task=task, declaration=declaration, root=root)


@pytest.mark.parametrize("phase", ("fit", "model-freeze", "calibrate", "calibration-freeze"))
def test_exact_installed_e3_scopes_accept_actual_typed_original_configurations(phase, monkeypatch):
    case = case_for(phase)
    reads = []
    def read_config(*args):
        reads.append(args)
        return case.config
    monkeypatch.setattr(owner, "_read_config", read_config)
    owner.validate_selected_original_producer(**case.arguments)
    assert len(reads) == 1


@pytest.mark.parametrize("damage", ("key", "version", "implementation", "access", "config-schema"))
def test_foreign_installed_method_or_lane_refuses_before_original_config_read(damage, monkeypatch):
    case = case_for("calibrate")
    task = case.task
    if damage == "implementation":
        task = replace(task, capability_implementation_sha256="f"*64)
    else:
        changes = {"key": {"capability_key": "foreign.same-output-schema"}, "version": {"capability_version": "2.0.0"},
            "access": {"requested_outcome_access": Access.DEVELOPMENT_VISIBLE},
            "config-schema": {"config": replace(task.capability.config, config_schema="empirical-lawhood/testing/foreign-config")}}[damage]
        task = replace(task, capability=replace(task.capability, **changes))
    case.arguments["execution_plan"].tasks = (task,)
    monkeypatch.setattr(owner, "_read_config", lambda *_: pytest.fail("foreign producer reached original config read"))
    with pytest.raises(PermissionError, match="exact installed"):
        owner.validate_selected_original_producer(**case.arguments)


def test_complete_original_root_includes_calibration_and_confirmation_units(monkeypatch):
    case = case_for("calibrate")
    bad = replace(case.root, evaluation_unit_ids=case.arguments["programme"].point_design.package.allocation.unit_ids("evaluation"))
    case.arguments["package"].issued_study.candidate.authoring_package.base.draft = bad
    monkeypatch.setattr(owner, "_read_config", lambda *_: pytest.fail("thinned root reached original config read"))
    with pytest.raises(PermissionError, match="complete genuine"):
        owner.validate_selected_original_producer(**case.arguments)


@pytest.mark.parametrize("missing_system", (True, False))
def test_original_scientific_world_comes_from_actual_root_not_execution_plan(missing_system, monkeypatch):
    case = case_for("calibrate")
    wrong = None if missing_system else replace(case.root.system,
        world=replace(case.root.system.world, kind=owner.WorldKind.ANALYTIC_REFERENCE))
    case.arguments["package"].issued_study.candidate.authoring_package.base.draft = replace(case.root, system=wrong)
    monkeypatch.setattr(owner, "_read_config", lambda *_: pytest.fail("invalid scientific world reached configuration read"))
    with pytest.raises(PermissionError, match="complete genuine"):
        owner.validate_selected_original_producer(**case.arguments)


def test_actual_original_output_keeps_inherited_development_visibility_without_relabelling_access(monkeypatch):
    case = case_for("calibrate")
    parent = ExternalInputSpec("model", "model.exposed", "d"*64, case.arguments["programme"].point_design.package.models.SCHEMA,
        "application/json", 1, Visibility.DEVELOPMENT_ONLY, Access.DEVELOPMENT_VISIBLE, None)
    task = replace(case.task, external_inputs=(*case.task.external_inputs, parent),
        outputs=tuple(replace(value, visibility_ceiling=Visibility.DEVELOPMENT_ONLY,
            parent_visibility_ceilings=(Visibility.DEVELOPMENT_ONLY,)) for value in case.task.outputs))
    case.arguments["execution_plan"].tasks = (task,)
    case.arguments["logical"] = replace(case.arguments["logical"], visibility_ceiling=Visibility.DEVELOPMENT_ONLY,
        parent_visibility_ceilings=(Visibility.DEVELOPMENT_ONLY,))
    monkeypatch.setattr(owner, "_read_config", lambda *_: case.config)
    owner.validate_selected_original_producer(**case.arguments)
    case.arguments["logical"] = replace(case.arguments["logical"], outcome_access=Access.DEVELOPMENT_VISIBLE)
    with pytest.raises(PermissionError, match="output lane"):
        owner.validate_selected_original_producer(**case.arguments)


def test_config_that_names_another_original_spec_or_count_refuses(monkeypatch):
    case = case_for("calibrate")
    for changed in (replace(case.config, specification=replace(case.config.specification, object_fingerprint="f"*64),
            record_id="config." + statistical_task_id(replace(case.config.specification, object_fingerprint="f"*64), case.config.allocation, "calibrate")),
            replace(case.config, query_census=(("calibration", 1), ("evaluation", 1)))):
        monkeypatch.setattr(owner, "_read_config", lambda *_, changed=changed: changed)
        with pytest.raises(PermissionError, match="specification/allocation/phase"):
            owner.validate_selected_original_producer(**case.arguments)


def test_missing_real_selected_opportunity_owner_refuses_instead_of_schema_admission(monkeypatch):
    case = case_for("calibrate")
    nomination = SimpleNamespace(result_id="nomination.exposed", SCHEMA="empirical-lawhood/matrix-experimental-programme/preparation-nomination")
    pin = ObjectIdentity(nomination.result_id, nomination.SCHEMA, "1.0.0", "f"*64)
    case.arguments["programme"].nomination = pin
    case.arguments["binding"] = replace(case.arguments["binding"], record=pin)
    monkeypatch.setattr(owner, "_read_config", lambda *_: pytest.fail("unsupported producer reached a legacy decoder"))
    with pytest.raises(PermissionError, match=owner.UNAVAILABLE_OPPORTUNITY):
        owner.validate_selected_original_producer(**case.arguments)
    case.arguments["receipt"].task_id = "unselected-task"
    with pytest.raises(PermissionError, match="actual task/receipt"):
        owner.validate_selected_original_producer(**case.arguments)


@pytest.mark.parametrize("phase", ("fit", "model-freeze", "calibrate", "calibration-freeze"))
def test_original_batch_checks_assay_only_at_fit_and_reuses_authenticated_config(phase, monkeypatch):
    from empirical_lawhood.api import matrix_selected_e3_e4_runtime as projection
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    from tests.test_matrix_prepared_assay_method import literal_protocol

    case, reads, checks = case_for(phase), [], []
    assay = MatrixPreparedAssayMethod.from_protocol("assay.exposed.batch-forwarding", literal_protocol()[0])
    case.arguments["programme"].assay = assay
    def read_config(*args):
        reads.append(args)
        return case.config
    monkeypatch.setattr(owner, "_read_config", read_config)
    monkeypatch.setattr(projection, "_authenticate_selected_projection", lambda **kwargs: checks.append(kwargs))
    owner.validate_selected_original_producer(**case.arguments)
    assert len(reads) == 1
    assert len(checks) == (1 if phase == "fit" else 0)
    if checks:
        assert checks[0] == dict(frozen=case.arguments["programme"].point_design.package,
            criterion=None, policies=None, preparation=None, binding=case.arguments["binding"],
            package=case.arguments["package"], execution_plan=case.arguments["execution_plan"],
            writer=case.arguments["writer"], assay=assay, fit_config=case.config)


def _disclosed_original_projection(f):
    """Actual typed lowerer operands; only bounded original control I/O is replaced."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import ProtectedE3PhysicalForecastConfig
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes

    case, records = f.case, {}
    protocol = case.protocols[0]
    profile, = (value for value in case.numerical_profiles if value.original_protocol ==
        ObjectIdentity.from_record(protocol.protocol_id, protocol))
    node, = (value for value in case.lowered.draft.operations
        if value.selection.capability_key == "matrix-e3-protected.physical-forecast"
        and value.config_id == "config.matrix-e3-protected." + protocol.public_source.root.root_id + ".physical-forecast")
    physical_config = decode_canonical_bytes(node.config_payload.encode(), ProtectedE3PhysicalForecastConfig, maximum_bytes=None)
    declarations = {value.capability_key: value for value in e3.operation_declarations()}
    def task(config, capability, inputs):
        declaration = declarations[capability]
        manifest = declaration.manifest()
        identifier = config.record_id if type(config) is ProtectedE3FitConfig else config.config_id
        config_ref = CapabilityConfigRef(identifier, config.SCHEMA, manifest.config_schema_sha256,
            config.fingerprint(), "input." + identifier)
        requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
            config_ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
            declaration.evidence_ceiling, declaration.outcome_access, declaration.resources)
        external = []
        for index, record in enumerate((config, *inputs)):
            artifact_id = config_ref.artifact_id if index == 0 else "input." + identifier + "." + str(index)
            records[artifact_id] = record
            external.append(ExternalInputSpec("control." + str(index), artifact_id,
                record.fingerprint(), record.SCHEMA, "application/json", len(record.canonical_bytes()),
                declaration.visibility_ceiling, declaration.outcome_access, None))
        return SimpleNamespace(task_id=identifier.removeprefix("config."), capability=requirement,
            capability_implementation_sha256=manifest.implementation_sha256, stage=declaration.stage,
            external_inputs=tuple(external)), manifest
    fit, fit_manifest = task(case.fit_config, "matrix-e3-protected.fit", (case.manifest,))
    physical, physical_manifest = task(physical_config, "matrix-e3-protected.physical-forecast",
        (case.projections[0], case.mathematical_protocol, protocol, profile))
    binding = replace(prior_product(owner._reference(f.inputs.original_public_package.models)).prior_execution,
        task_id=fit.task_id)
    registry = CapabilityRegistry("registry.exposed.assay-projection",
        tuple(sorted((fit_manifest, physical_manifest), key=lambda value: value.registry_id)))
    return dict(frozen=f.inputs.original_public_package, criterion=None, policies=None, preparation=None,
        binding=binding, package=SimpleNamespace(registry=registry),
        execution_plan=SimpleNamespace(tasks=(fit, physical)), writer=object()), records, protocol


@pytest.mark.parametrize("reuse_fit", (False, True))
@pytest.mark.parametrize("damage", (None, "criterion", "force", "template", "tolerance", "fit-pin"))
def test_complete_selected_assay_matches_actual_original_projection_and_authenticates_supplied_fit(
        literal_recipe_source_inputs, monkeypatch, reuse_fit, damage):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    from empirical_lawhood.api import matrix_selected_e3_e4_runtime as projection, matrix_selected_runtime

    f = literal_recipe_source_inputs
    kwargs, records, protocol = _disclosed_original_projection(f)
    assay = MatrixPreparedAssayMethod.from_protocol("assay.exposed.actual-original", protocol)
    if damage == "criterion":
        assay = replace(assay, criterion=replace(assay.criterion, object_fingerprint="f" * 64))
    elif damage == "force":
        assay = replace(assay, actions=tuple(replace(row, force_norm=row.force_norm * 2) for row in assay.actions))
    elif damage == "template":
        assay = replace(assay, template_artifact=replace(assay.template_artifact, sha256="f" * 64))
    elif damage == "tolerance":
        assay = replace(assay, weak_response_minimum=assay.weak_response_minimum * 2)
    reads = []
    def read_input(writer, run_id, spec, kind):
        assert writer is kwargs["writer"] and run_id == kwargs["binding"].run_id
        value = records[spec.logical_artifact_id]
        assert type(value) is kind and (value.SCHEMA, value.fingerprint()) == (
            spec.expected_payload_schema, spec.expected_content_sha256)
        reads.append(type(value))
        return value
    monkeypatch.setattr(matrix_selected_runtime, "_published_input", read_input)
    if reuse_fit:
        kwargs["fit_config"] = f.case.fit_config
    if damage == "fit-pin":
        # A supplied configuration must retain the actual compiled fit pin.
        kwargs["fit_config"] = replace(f.case.fit_config,
            fit_cutoff=replace(f.case.fit_config.fit_cutoff, coordinate=f.case.fit_config.fit_cutoff.coordinate + 1))
    if damage is None:
        projection._authenticate_selected_projection(**kwargs, assay=assay)
    else:
        message = "already authenticated fit configuration" if damage == "fit-pin" else "producer-pinned complete method"
        with pytest.raises(PermissionError, match=message):
            projection._authenticate_selected_projection(**kwargs, assay=assay)
    assert reads.count(ProtectedE3FitConfig) == 1
    if damage == "fit-pin":
        assert reads == [ProtectedE3FitConfig]
    else:
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import ProtectedE3PhysicalForecastConfig
        assert reads.count(ProtectedE3PhysicalForecastConfig) == 1


def test_declarative_original_batch_forwards_complete_selected_assay_before_publication(monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
    from empirical_lawhood.api import matrix_sampling_runtime
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import original_e3_package
    from tests.test_matrix_prepared_assay_method import literal_protocol
    from tests.test_matrix_selected_e4_bank_recipe import original_locators

    frozen = exposed_package()
    public = MatrixSelectedPublicPackage.from_package(frozen)
    assay = MatrixPreparedAssayMethod.from_protocol("assay.exposed.declarative-forwarding", literal_protocol()[0])
    request = SimpleNamespace(original_e3=public, original_e3_products=original_locators(public), assay=assay)
    records = {owner._reference(value): value for value in
        (frozen.models, frozen.model_freeze, frozen.calibration, frozen.calibrated_freeze)}
    calls = []
    def read_originals(writer, pairs, codecs, *, scope_validator):
        assert scope_validator.func is owner.validate_selected_e3_original_product
        assert scope_validator.keywords == {"frozen": public, "assay": assay}
        calls.append(pairs)
        return tuple(records[pin].canonical_bytes() for _, pin in pairs)
    monkeypatch.setattr(matrix_sampling_runtime, "_original_products", read_originals)
    assert original_e3_package(object(), request, {}) == frozen
    assert len(calls) == 1 and len(calls[0]) == 4
