# SPDX-License-Identifier: MPL-2.0
"""Scientific scopes for original products consumed by selected Matrix entry.

This predicate runs after original issue/reveal/plan/receipt authentication and
before the target payload is returned for scientific use. Receipt validation
may already inspect protected bytes under those genuine grants. This predicate
is not an authority token or reader.
"""

from functools import partial

from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import ProtectedE3FitConfig
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme
from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, derived_outcome_access


UNAVAILABLE_OPPORTUNITY = "SELECTED_OPPORTUNITY_PRODUCER_UNAVAILABLE"


def _reference(value, field="record_id"):
    return value if type(value) is ObjectIdentity else ObjectIdentity.from_record(getattr(value, field), value)


def selected_original_producer_scope(programme):
    """Select a consumer predicate; actual original custody remains external."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity import (
        MatrixSelectedOpportunityProgramme, MatrixSelectedOpportunityPublicProgramme,
    )

    if type(programme) not in (MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme,
            MatrixSelectedOpportunityProgramme, MatrixSelectedOpportunityPublicProgramme):
        raise TypeError("selected producer scope requires the actual complete programme or exact public projection")
    programme.__post_init__()
    return partial(validate_selected_original_producer, programme=programme)


def _read_config(writer, binding, task, kind):
    from empirical_lawhood.api.matrix_selected_runtime import _published_input

    matches = tuple(value for value in task.external_inputs if value.logical_artifact_id == task.capability.config.artifact_id)
    if len(matches) != 1:
        raise PermissionError("selected original producer lacks its one actual configured input")
    config = _published_input(writer, binding.run_id, matches[0], kind)
    identifier = config.record_id if type(config) is ProtectedE3FitConfig or hasattr(config, "record_id") else config.config_id
    if (identifier, config.SCHEMA, config.fingerprint()) != (task.capability.config.config_id,
            task.capability.config.config_schema, task.capability.config.content_sha256):
        raise PermissionError("selected original producer substitutes actual canonical configured science")
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import ConfiguredE3RetainedTaskConfig
    if type(config) is ConfiguredE3RetainedTaskConfig:
        from .configured_e3_retained_read import authenticated_original_config
        return authenticated_original_config(writer=writer, run_id=binding.run_id, task=task, config=config)
    return config


def _installed_task(task, package, declaration):
    manifest = declaration.manifest()
    try:
        installed = package.registry.resolve(manifest.capability_key, manifest.capability_version)
    except KeyError as error:
        raise PermissionError("selected original scientific producer is not independently installed") from error
    if (installed != manifest or task.capability.capability_key != manifest.capability_key
            or task.capability.capability_version != manifest.capability_version
            or task.capability_implementation_sha256 != manifest.implementation_sha256
            or task.stage is not declaration.stage
            or (task.capability.config.config_schema, task.capability.config.config_schema_sha256)
                != (manifest.config_schema, manifest.config_schema_sha256)
            or task.capability.requested_outcome_access is not declaration.outcome_access
            or task.capability.required_permissions != manifest.permissions):
        raise PermissionError("selected original producer changes its exact installed method/version/implementation/stage/config or access")


def _original_output(task, logical, binding, declaration):
    declared = tuple(sorted(((task.task_id + "." + value.output_id, value.payload_schema, value.profile, value.media_type)
        for value in declaration.outputs), key=lambda value: value[0]))
    actual = tuple((value.output_id, value.payload_schema, value.profile, value.media_type) for value in task.outputs)
    outputs = tuple(value for value in task.outputs if value.output_id == task.task_id + ".product"
        and value.logical_artifact_id == binding.logical_artifact_id)
    if (actual != declared or len(outputs) != 1 or logical.logical_artifact_id != binding.logical_artifact_id
            or logical.payload_schema != binding.record.object_schema or logical.content_sha256 != binding.record.object_fingerprint
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != "application/json"):
        raise PermissionError("selected original producer substitutes its exact declared scientific output")
    inputs = tuple((value.expected_outcome_access, value.expected_visibility_ceiling) for value in task.external_inputs)
    inputs += tuple((value.outcome_access, value.visibility_ceiling) for value in task.scientific_inputs if value.producer_task_id is not None)
    if any(access not in (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.EVALUATION_SEALED)
            or ceiling not in (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.DEVELOPMENT_ONLY) for access, ceiling in inputs):
        raise PermissionError("selected original scientific inputs were already revealed or relabelled")
    access = derived_outcome_access(declaration.outcome_access, *(value[0] for value in inputs))
    ceiling = inherited_visibility(tuple(value[1] for value in inputs), access)
    if ((logical.outcome_access, logical.visibility_ceiling) != (access, ceiling)
            or any((value.outcome_access, value.visibility_ceiling) != (access, ceiling) for value in task.outputs)):
        raise PermissionError("selected original product changes the actual inherited scientific output lane")


def validate_selected_original_producer(*, programme, binding, package, execution_plan, receipt, logical, writer, read_scope):
    frozen = programme.point_design.package
    choices = ((_reference(frozen.models), "fit"), (_reference(frozen.model_freeze), "model-freeze"),
        (_reference(frozen.calibration), "calibrate"), (_reference(frozen.calibrated_freeze), "calibration-freeze"))
    if len({value.object_id for value, _ in choices}) != 4:
        raise PermissionError("selected original science aliases its four independent E3 products")
    nomination = getattr(programme, "nomination", None)
    nomination_pin = (None if nomination is None else nomination.original_nomination
        if type(programme) is MatrixSelectedPublicProgramme else _reference(nomination, "result_id"))
    tasks = tuple(value for value in execution_plan.tasks if value.task_id == binding.task_id)
    if len(tasks) != 1 or (receipt.run_id, receipt.task_id) != (binding.run_id, binding.task_id):
        raise PermissionError("selected original producer changes its actual task/receipt")
    if binding.record == nomination_pin:
        raise PermissionError(UNAVAILABLE_OPPORTUNITY + ": no installed selected opportunity scientific producer")
    return validate_selected_e3_original_product(frozen=frozen, binding=binding, package=package,
        execution_plan=execution_plan, receipt=receipt, logical=logical, writer=writer, read_scope=read_scope,
        assay=programme.assay)


def validate_selected_e3_original_product(*, frozen, binding, package, execution_plan, receipt, logical, writer, read_scope, assay=None):
    """Exact four original E3 producers after genuine issue/reveal authentication."""
    choices = ((_reference(frozen.models), "fit"), (_reference(frozen.model_freeze), "model-freeze"),
        (_reference(frozen.calibration), "calibrate"), (_reference(frozen.calibrated_freeze), "calibration-freeze"))
    if len({value.object_id for value, _ in choices}) != 4:
        raise PermissionError("selected original science aliases its four independent E3 products")
    tasks = tuple(value for value in execution_plan.tasks if value.task_id == binding.task_id)
    if len(tasks) != 1 or (receipt.run_id, receipt.task_id) != (binding.run_id, binding.task_id):
        raise PermissionError("selected original producer changes its actual task/receipt")
    task, = tasks
    phases = tuple(phase for reference, phase in choices if reference == binding.record)
    if len(phases) != 1 or binding.record_id_field != "record_id":
        raise PermissionError("selected original producer is not one of its exact original E3 scientific records")
    phase, = phases
    family = selected_e3_product_family(frozen.specification)
    keys = (family.namespace + "." + phase,)
    if family.configured and phase == "fit":
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import fit_capability_key
        keys = (fit_capability_key(frozen.models.training_features.object_schema,
            frozen.models.training_outcomes.object_schema),)
    if family.configured and phase in ('fit', 'model-freeze'):
        keys += (family.namespace + '.retained-' + phase,)
    if task.capability.capability_key not in keys:
        raise PermissionError("selected original producer changes its exact installed E3 scientific edition")
    declaration, = (value for value in family.operation_declarations()
        if value.capability_key == task.capability.capability_key)
    _installed_task(task, package, declaration)
    _original_output(task, logical, binding, declaration)
    root = package.issued_study.candidate.authoring_package.base.draft
    if (type(root) is not StudyDraft or root.system is None or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.evaluation_unit_ids != tuple(sorted((*frozen.allocation.unit_ids("calibration"),
                *frozen.allocation.unit_ids("evaluation"))))):
        raise PermissionError("selected original E3 producer changes its complete genuine numerical scientific root")
    config = _read_config(writer, binding, task, declaration.config_record_type)
    operation, mode = {"fit": ("fit", ""), "model-freeze": ("freeze", "model"),
        "calibrate": ("calibrate", ""), "calibration-freeze": ("freeze", "calibration")}[phase]
    if (config.specification != frozen.specification.identity or config.allocation != frozen.allocation.identity
            or config.operation != operation or config.mode != mode or config.root is not None
            or config.query_census != tuple((role, len(frozen.allocation.unit_ids(role))) for role in ("calibration", "evaluation"))
            or task.task_id != family.statistical_task_id(config.specification, config.allocation, operation, mode=mode)):
        raise PermissionError("selected original E3 producer changes original specification/allocation/phase or complete CAL/CONF census")
    if phase == "fit":
        if (config.training_allocation != frozen.prefit.training_allocation or config.fit_cutoff != frozen.prefit.fit_cutoff
                or config.original_publications is None):
            raise PermissionError("selected original fit changes original pre-fit publication or cutoff custody")
        observed = tuple((key, publication.logical.payload_schema, publication.logical.content_sha256,
            publication.logical.media_type, publication.materialization.size_bytes, publication.materialization.materialization_id, availability)
            for key, publication, availability in config.publications)
        expected = tuple((key, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes, materialization, availability)
            for key, artifact, materialization, availability in frozen.prefit.publications)
        if observed != expected:
            raise PermissionError("selected original fit substitutes its actual pre-fit reservation/role/selection publications")
        if assay is not None:
            from empirical_lawhood.api.matrix_selected_e3_e4_runtime import _authenticate_selected_projection
            _authenticate_selected_projection(frozen=frozen, criterion=None, policies=None, preparation=None,
                binding=binding, package=package, execution_plan=execution_plan, writer=writer,
                assay=assay, fit_config=config)
