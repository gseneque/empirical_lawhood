# SPDX-License-Identifier: MPL-2.0
"""Standalone owning-API composition for the protected E4 prepared selection.

Registration and public service integration remain separate work. This binder
reads blind original metadata and replays existing authorities; it issues no
study, reads no confirmation outcomes and grants no worker or reveal access.
The original StudyDefinition entry is an exact design-source carrier, not an
inferred original human act or publication. Current candidate entry and issue
retain their existing generic owners.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition import ScheduledProgrammeAcquisitionAdmissionConfig
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import ScheduledProgrammeAuthenticatedParent
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import ScheduledFactorialConfirmationConfig
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_inputs import (
    ProtectedFactorialOriginalSource, ProtectedFactorialPreparationRequest, ProtectedFactorialPreparationSelection,
    bind_protected_factorial_preparation_request, validate_protected_factorial_request_binding,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import (
    PAIRED_TYPES, ProtectedFactorialExperimentInputs, derive_protected_factorial_design_inputs,
    prepare_protected_factorial_experiment, validate_protected_experiment_handoff_selection,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_specification import ProtectedFactorialExperimentSpecification
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.candidate_sources import ExternalContentAddressedInputResolver
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.planning.experiment_entry import validate_experiment_entry
from empirical_lawhood.planning.study_authoring import DesignInputRole
from empirical_lawhood.runtime.source_resolution import (
    CandidateSourceResolutionService, ContentAddressedInputKind, ContentAddressedInputRequirement, ResolvedContent,
)
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentPreparation

from . import matrix_scheduled_factorial_runtime as factorial
from . import matrix_scheduled_programme as programme
from .current_result_custody import CurrentResultPlanReader
from .matrix_scheduled_programme_runtime import authenticate_programme_qualified_parent, bind_programme_runtime_handoff


def prepare_protected_factorial_experiment_authoring(preparation, *, project_root, artifact_writer, output_dir):
    """Bind exact operational intent using the real, nonauthorizing candidate owner.

    All original entry/custody/current calibration authority remains mandatory at
    the owning handoff and each worker. This step neither issues nor reveals.
    """
    from .experiment_preparation import _protocol
    from .experiment_runtime_bindings import experiment_runtime_binding
    from .prospective_experiment import preview_prepared_prospective_experiment_candidate

    if (type(preparation) is not ExperimentPreparation
            or type(preparation.specification_record) is not ProtectedFactorialExperimentSpecification
            or preparation.execution is None or preparation.allocation is None or preparation.draft is None):
        raise ValueError("protected authoring needs its complete original typed preparation before resource binding")
    preparation.__post_init__()
    resolvable_codes = {"matrix.protected-factorial.owning-api-composition", "matrix.protected-factorial.resource-projection"}
    if any(row.kind is not DependencyKind.SOFTWARE or row.code not in resolvable_codes for row in preparation.dependencies):
        raise ValueError("protected authoring retains unresolved entry dependencies before candidate resource binding")
    binding = experiment_runtime_binding(_protocol(preparation.specification_record))
    if (binding is None or binding.bind_handoff is not bind_protected_factorial_experiment_handoff
            or binding.prepare_authoring is not prepare_protected_factorial_experiment_authoring):
        raise ValueError("SOFTWARE: protected authoring requires its exact installed owning API composition")
    selected = {}
    for key, record in preparation.design_records:
        if type(record) not in (ProtectedFactorialOriginalSource, ProtectedFactorialPreparationRequest,
                ProtectedFactorialPreparationSelection) or type(record) in selected:
            raise ValueError("protected authoring changes its original source/request role census")
        if key != (record.source_id if type(record) is ProtectedFactorialOriginalSource else
                record.request_id if type(record) is ProtectedFactorialPreparationRequest else record.selection_id):
            raise ValueError("protected authoring aliases an original source or operational request")
        selected[type(record)] = record
    original = selected.get(ProtectedFactorialOriginalSource)
    request = selected.get(ProtectedFactorialPreparationRequest)
    bound = selected.get(ProtectedFactorialPreparationSelection)
    selection = request if request is not None else bound
    if original is None or selection is None:
        raise ValueError("protected authoring omits its actual original source or operational request")
    if request is not None and bound is not None:
        validate_protected_factorial_request_binding(request, bound)
    files = []
    for _, value in preparation.input_files:
        role = "bank" if value.identity.artifact_id == selection.bank.artifact_id else next(
            (name for name, kind in PAIRED_TYPES.items() if value.identity.payload_schema == kind.SCHEMA), None)
        if role is None:
            raise ValueError("protected authoring adds an unselected physical source")
        files.append((role, value))
    inputs = ProtectedFactorialExperimentInputs(original, bound if request is None else None,
        tuple(sorted(files)), request)
    baseline = prepare_protected_factorial_experiment(preparation.specification_record,
        scientific_inputs={"confirmation": preparation.allocation}, execution=preparation.execution, method_inputs=inputs)
    resolved = tuple(row for row in baseline.dependencies if row.kind is DependencyKind.SOFTWARE and row.code in resolvable_codes)
    if (len(resolved) != 2 or any(row not in resolved for row in baseline.dependencies)
            or any(row not in resolved for row in preparation.dependencies)):
        raise ValueError("protected authoring retains unresolved entry dependencies before candidate resource binding")
    for name in ("specification", "census", "allocation", "draft", "input_records", "input_files", "assessment_limitations"):
        if getattr(baseline, name) != getattr(preparation, name):
            raise ValueError("protected authoring changes its original scientific preparation or input bindings")
    _, _, _, design = derive_protected_factorial_design_inputs(preparation.specification_record, original, selection)
    from .authoring_handoff import preflight_authoring_output_directory

    preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root), artifact_writer=artifact_writer)
    preview = preview_prepared_prospective_experiment_candidate(preparation=preparation, design_inputs=design,
        source_configs=selection.source_configs, project_root=project_root, artifact_writer=artifact_writer)
    if request is not None:
        bound = bind_protected_factorial_preparation_request(request, issued_extensions=preview.issued_extensions)
    elif bound.resources.issued_study_extensions != ObjectIdentity.from_record(
            preview.issued_extensions.issued_extension_set_id, preview.issued_extensions):
        raise ValueError("protected bound resources differ from the actual candidate extension projection")
    result = prepare_protected_factorial_experiment(preparation.specification_record,
        scientific_inputs={"confirmation": preparation.allocation}, execution=preparation.execution,
        method_inputs=ProtectedFactorialExperimentInputs(original, bound, tuple(sorted(files))))
    if any(getattr(result, name) != getattr(preparation, name) for name in (
            "specification", "census", "allocation", "draft", "input_records", "input_files", "assessment_limitations")):
        raise ValueError("protected resource binding changed its unchanged original scientific preparation")
    records = dict(preparation.design_records)
    if bound.selection_id in records and records[bound.selection_id] != bound:
        raise ValueError("protected bound preparation collides with an unchanged original design record")
    records[bound.selection_id] = bound
    return replace(result, dependencies=tuple(row for row in result.dependencies if row not in resolved),
        design_records=tuple(sorted(records.items())), prospective_candidate_preview=preview)


def _original_bank(handoff, selection, writer):
    """Use the existing guarded exact content address, with no caller path.

    Canonical decoding validates the complete shared bank and its bounded
    source references. Actual source and access joins remain with their owners.
    """
    service = handoff.context.source_resolution_service
    if (type(service) is not CandidateSourceResolutionService
            or type(service.resolver) is not ExternalContentAddressedInputResolver
            or service.resolver.root.contract != writer.root.contract):
        raise PermissionError("protected experiment bank resolver changes its existing guarded custody root")
    artifact = selection.bank
    requirement = ContentAddressedInputRequirement("protected-factorial-bank." + artifact.artifact_id,
        ContentAddressedInputKind.SOURCE_MATERIALIZATION, artifact.sha256, artifact.payload_schema,
        artifact.media_type, artifact.size_bytes, artifact.size_bytes,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    resolved = service.resolver.resolve(requirement, materialize=True)
    if (type(resolved) is not ResolvedContent or type(resolved.payload) is not bytes
            or resolved.receipt.requirement != ObjectIdentity.from_record(requirement.requirement_id, requirement)
            or not resolved.receipt.payload_materialized
            or (resolved.receipt.observed_sha256, resolved.receipt.observed_size_bytes) != (artifact.sha256, artifact.size_bytes)
            or len(resolved.payload) != artifact.size_bytes or sha256(resolved.payload).hexdigest() != artifact.sha256):
        raise PermissionError("protected experiment bank differs from its exact resolved physical bytes")
    bank = decode_canonical_bytes(resolved.payload, ScheduledCompactBank, maximum_bytes=artifact.size_bytes)
    if (bank.canonical_bytes() != resolved.payload
            or ObjectIdentity.from_record(bank.bank_id, bank) != ObjectIdentity(
                artifact.artifact_id, artifact.payload_schema, ScheduledCompactBank.VERSION, artifact.sha256)):
        raise PermissionError("protected experiment bank changes its original canonical subject or revision")
    return bank


def _original_global_root(original, package, plan, writer, wave):
    """Join the full original opening scope and its original issued root pin."""
    opening, = (row for row in plan.tasks if row.task_id == wave.wave_id + ".open")
    opening_config, _ = factorial._original_config(writer, package.run_plan_id, opening,
        ScheduledProgrammeAcquisitionAdmissionConfig)
    root = original.study.draft
    actual = opening_config.scope.global_root
    expected = ObjectIdentity.from_record(root.draft_id, root)
    if (actual != root or ObjectIdentity.from_record(actual.draft_id, actual) != expected
            or actual.canonical_bytes() != root.canonical_bytes()):
        raise PermissionError("protected experiment opening changes the exact unchanged original global scientific root")
    issued_root = package.issued_study.candidate.authoring_package.base.draft
    pins = tuple(row for row in issued_root.design_inputs if row.object_identity == expected)
    if (len(pins) != 1 or pins[0].materialization_sha256 != expected.object_fingerprint
            or pins[0].role is not DesignInputRole.READINESS_METADATA
            or pins[0].outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or pins[0].visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or pins[0].physical_unit_ids or pins[0].seed_ids):
        raise PermissionError("protected experiment acquisition omits its exact original global readiness pin")


def bind_protected_factorial_experiment_handoff(handoff, *, specification, allocation, source_records,
        artifact_writer, reveal_authority_id=None):
    """Authenticate original blind custody, then attach the existing supplier.

    Every worker still replays original criteria/acquisition/current calibrated
    parent authority through prepare_factorial_task. The seal worker remains
    outcome-blind; historical calibration replay retains its original scope.
    """
    from .recursive_prospective_authoring import RecursiveProspectiveApplicationHandoff

    if type(handoff) is not RecursiveProspectiveApplicationHandoff or not isinstance(artifact_writer, ExternalArtifactPlane):
        raise TypeError("protected experiment binding requires the actual owning prospective handoff and artifact custody")
    if reveal_authority_id is not None:
        validate_stable_id(reveal_authority_id)
    original, selection, _ = validate_protected_experiment_handoff_selection(handoff,
        specification=specification, allocation=allocation, source_records=source_records)
    validate_experiment_entry(original.study.draft, original.study.entry_package, for_issue=False)
    bank = _original_bank(handoff, selection, artifact_writer)
    configuration = original.criteria.record.configuration
    declaration = configuration.qualified_parent
    programme._assert_actual_declaration(handoff.compilation.draft, configuration.programme, bank, None,
        qualified_parent=declaration)
    parent = programme._actual_programme_entry(configuration.programme, bank, artifact_writer, None, qualified_parent=declaration)
    if (type(parent) is not ScheduledProgrammeAuthenticatedParent or parent.declaration != declaration.identity
            or parent.bank != configuration.bank or parent.evidence != declaration.evidence):
        raise PermissionError("protected experiment entry lacks its freshly authenticated original qualified parent")
    assessment, = (row.record for row in handoff.compilation.config_inputs
        if type(row.record) is ScheduledFactorialConfirmationConfig)
    originals = []
    with artifact_writer.verification_scope() as parent_writer:
        reader = CurrentResultPlanReader(parent_writer)
        originals.append(factorial._ordinary_product(parent_writer, original.criteria, reader))
        for locator in assessment.acquisitions:
            package, plan, wave, _, _, _, global_parent = factorial._wave_metadata(artifact_writer, locator,
                assessment, bank, original.study.draft, parent_writer=parent_writer, parent_plan_reader=reader)
            _original_global_root(original, package, plan, artifact_writer, wave)
            originals.extend((package, global_parent))
    by_run = {}
    for package in originals:
        if by_run.setdefault(package.run_plan_id, package) != package:
            raise PermissionError("protected experiment original run changes its actual immutable issued package")
    for package in by_run.values():
        if factorial._live_package(artifact_writer, package.run_plan_id) != package:
            raise PermissionError("protected experiment original authority or source changed during metadata authentication")
    if authenticate_programme_qualified_parent(artifact_writer, bank, declaration, programme._programme_codecs()) != parent:
        raise PermissionError("protected experiment qualified parent changed during original metadata authentication")
    return bind_programme_runtime_handoff(handoff, writer=artifact_writer, reveal_authority_id=reveal_authority_id)
