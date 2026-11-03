# SPDX-License-Identifier: MPL-2.0
"""Public E3 custody composition; no API authority callback enters a worker."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import authenticate_configured_protected_e3_fit_config
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalRunner
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody, CurrentIssuedTaskCustodySupplier
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentPreparation
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort


def _fit(compilation):
    return _fit_from_draft(compilation.draft)


def _selection(records):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import configured_preparation_types

    values = tuple(record for _, record in records if type(record) in configured_preparation_types())
    if len(values) != 1:
        raise ValueError("protected E3 omits or repeats its actual preissue preparation selection")
    return values[0]


def authenticate_protected_e3_numerical_originals(writer, selection):
    """Authenticate each original qualified container once, including its bytes.

    One existing qualified selection may cover every selected protocol. This
    current authentication creates no earlier publication or numerical warrant.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import _object

    containers = {_object(row): row for row in (selection.response_selection, *selection.protocols, *selection.numerical_containers)}
    checked = set()
    for profile in selection.numerical_profiles:
        pin = profile.provenance_container
        publication = profile.provenance_publication
        key = (pin, publication.fingerprint())
        if key not in checked:
            authenticate_publication(writer, publication, containers[pin])
            checked.add(key)


class ProtectedE3RuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    """Parent-only custody; the existing supplier still owns exact input bytes."""

    def __init__(self, supplier, *, writer, root, fit_config, qualifications, selection,
            reveal_authority_id=None, custody=None, retained_e3_scope=None):
        self.supplier = supplier
        self.writer = writer
        self.root = root
        self.fit_config = fit_config
        self.qualifications = qualifications
        self.selection = selection
        self.retained_e3_scope = retained_e3_scope
        self.reveal_authority_id = reveal_authority_id
        if custody is not None and (type(custody) is not CurrentIssuedTaskCustody
                or custody.writer is not writer or custody.reveal_authority_id != reveal_authority_id):
            raise TypeError("configured E3 shared custody changes its exact writer or reveal selection")
        self.custody = (CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id)
            if custody is None else custody)

    def resolve_input(self, spec):
        return self.supplier.resolve_input(spec)

    def prepare_matrix_sampling(self, context, runner):
        from empirical_lawhood.api.matrix_sampling_runtime import prepare_matrix_sampling
        with self.custody.preparation_scope():
            return prepare_matrix_sampling(self, context, runner)

    def prepare_selected_matrix(self, context, runner):
        from empirical_lawhood.api.matrix_selected_runtime import prepare_selected_matrix
        with self.custody.preparation_scope():
            return prepare_selected_matrix(self, context, runner)

    def prepare_configured_protected_e3_fit(self, context, runner):
        if self.retained_e3_scope is not None:
            raise PermissionError('continued E3 cannot execute a replacement fit')
        with self.custody.preparation_scope():
            return self._prepare_configured_protected_e3_fit(context, runner)

    def prepare_configured_e3_retained_task(self, context, runner):
        from empirical_lawhood.api.configured_e3_retained_runtime import prepare_retained_task
        return prepare_retained_task(self, context, runner)

    def _prepare_configured_protected_e3_fit(self, context, runner):
        """Recheck the actual issued entry and originals before any TRAIN decode."""
        if type(runner) is not ConfiguredProtectedE3StatisticalRunner or runner.phase != "fit":
            raise PermissionError("protected E3 parent preparation refuses a foreign fit implementation")
        custody = self.custody
        package, plan, task = custody.current_task(context, runner)
        _, controls = custody.task_inputs(context, task)
        actual_root = package.issued_study.candidate.authoring_package.base.draft
        if actual_root != self.root:
            raise PermissionError("protected E3 fit changes its actual current issued scientific root")
        actual_qualifications = {ObjectIdentity.from_record(row.receipt_id, row): row
            for row in package.issued_study.materialization_qualifications}
        expected_qualifications = {ObjectIdentity.from_record(row.receipt_id, row): row for row in self.qualifications}
        for source in actual_root.source_materializations:
            pin = source.qualification_receipt
            if (pin is None or pin not in expected_qualifications
                    or actual_qualifications.get(pin) != expected_qualifications[pin]):
                raise PermissionError("protected E3 fit loses an actual issued scientific-source qualification")
        manifest = controls.get(context.config.artifact_id)
        if manifest is None:
            raise PermissionError("protected E3 fit has no exact persisted current configuration")
        # CurrentIssuedTaskCustody has already joined this manifest to the
        # actual task/config input binding. Read only its control record here.
        self.writer.verify_manifest(manifest)
        raw = read_bounded_bytes(self.writer.root.resolve(manifest.materialization.relative_path, for_write=False),
            maximum_bytes=manifest.materialization.size_bytes)
        config = decode_canonical_bytes(raw, ConfiguredProtectedE3FitConfig, maximum_bytes=manifest.materialization.size_bytes)
        if (config != self.fit_config or raw != config.canonical_bytes()
                or len(raw) != manifest.materialization.size_bytes
                or sha256(raw).hexdigest() != manifest.logical.content_sha256
                or sha256(raw).hexdigest() != manifest.materialization.physical_sha256
                or context.config.content_sha256 != config.fingerprint()):
            raise PermissionError("protected E3 fit substitutes its exact issued original-publication bindings")
        from empirical_lawhood.api.configured_e3_secondary_target import authenticate_secondary_target
        authenticate_secondary_target(writer=self.writer, selection=self.selection)
        from empirical_lawhood.api.configured_e3_primary_amendment import authenticate_primary_amendment
        authenticate_primary_amendment(writer=self.writer, selection=self.selection)
        authenticate_configured_protected_e3_fit_config(self.writer, config)
        authenticate_protected_e3_numerical_originals(self.writer, self.selection)
        if custody.current_task(context, runner) != (package, plan, task):
            raise PermissionError("protected E3 current grant or issued source changed during preparation")
        return runner


def prepare_protected_e3_experiment_authoring(preparation, *, project_root, artifact_writer, output_dir):
    """Bind resources from the actual candidate without changing selected science."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import (
        RESOURCE_BINDING_DEPENDENCY, derive_protected_e3_design_inputs,
    )
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.prospective_experiment import preview_prepared_prospective_experiment_candidate
    from empirical_lawhood.runtime.experiment_resources import bind_execution_resources

    if (type(preparation) is not ExperimentPreparation
            or type(preparation.specification_record) is not MatrixResponseErrorSpecification):
        raise TypeError("protected E3 authoring requires its exact public preparation")
    if preparation.specification_record.evidence_scope == "EXPOSED_CONFORMANCE":
        return preparation
    preparation.__post_init__()
    unresolved = tuple(row for row in preparation.dependencies
        if row.kind is not DependencyKind.SOFTWARE or row.code != RESOURCE_BINDING_DEPENDENCY)
    if unresolved or preparation.allocation is None or preparation.draft is None:
        raise ValueError("protected E3 authoring retains unresolved scientific or source entry dependencies: " + "; ".join(
            row.code + " (" + row.kind.value + "): " + row.detail for row in unresolved))
    selected = _selection(preparation.design_records)
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection
    if isinstance(selected, ConfiguredE3ContinuedPreparationSelection):
        from empirical_lawhood.api.configured_e3_retained_runtime import authenticate_selection
        with authenticate_selection(writer=artifact_writer, selection=selected):
            pass
    from empirical_lawhood.api.configured_e3_secondary_target import authenticate_secondary_target
    authenticate_secondary_target(writer=artifact_writer, selection=selected)
    from empirical_lawhood.api.configured_e3_primary_amendment import authenticate_primary_amendment
    authenticate_primary_amendment(writer=artifact_writer, selection=selected)
    authenticate_protected_e3_numerical_originals(artifact_writer, selected)
    design = derive_protected_e3_design_inputs(preparation)
    fit = _fit_from_draft(preparation.draft)
    authenticate_configured_protected_e3_fit_config(artifact_writer, fit)
    preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root),
        artifact_writer=artifact_writer)
    source_configs = tuple(sorted(selected.source_configs, key=lambda row: row.fingerprint()))
    preview = preview_prepared_prospective_experiment_candidate(preparation=preparation, design_inputs=design,
        source_configs=source_configs,
        project_root=project_root, artifact_writer=artifact_writer)
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import derive_protected_e3_resource_selection

    resources = bind_execution_resources(derive_protected_e3_resource_selection(preparation),
        issued_extensions=preview.issued_extensions)
    return replace(preparation, dependencies=(), prospective_spec=design.bind_resources(resources),
        source_configs=source_configs, prospective_candidate_preview=preview)


def _fit_from_draft(draft):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_composition import operation_declarations
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input

    registered = {row.registration().selection.selection_id: row.registration() for row in operation_declarations()}
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import original_config
    records = tuple(original_config(decode_recursive_config_input(operation,
        registered[operation.selection.selection_id]).record) for operation in draft.operations)
    records = tuple(record for record in records if type(record) is ConfiguredProtectedE3FitConfig)
    if len(records) != 1 or records[0].original_publications is None:
        raise ValueError("protected E3 requires its one selected original-bound fit")
    return records[0]


def bind_configured_protected_e3_experiment_handoff(handoff, *, specification, allocation, source_records,
        artifact_writer, reveal_authority_id=None):
    """Recheck the original instance and attach only parent-side fit custody."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import validate_protected_e3_experiment_instance
    from empirical_lawhood.api.recursive_prospective_authoring import RecursiveProspectiveApplicationHandoff
    from empirical_lawhood.kernel.serialization import validate_stable_id
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort

    if type(handoff) is not RecursiveProspectiveApplicationHandoff:
        raise TypeError("protected E3 requires the actual public prospective handoff")
    if reveal_authority_id is not None:
        validate_stable_id(reveal_authority_id)
    validate_protected_e3_experiment_instance(specification=specification, allocation=allocation,
        draft=handoff.compilation.draft, source_records=source_records)
    selection = _selection(source_records)
    from empirical_lawhood.api.configured_e3_secondary_target import authenticate_secondary_target
    authenticate_secondary_target(writer=artifact_writer, selection=selection)
    from empirical_lawhood.api.configured_e3_primary_amendment import authenticate_primary_amendment
    authenticate_primary_amendment(writer=artifact_writer, selection=selection)
    authenticate_protected_e3_numerical_originals(artifact_writer, selection)
    fit = _fit(handoff.compilation)
    if selection.fit_config != fit or handoff.authoring.base.draft != handoff.compilation.candidate_draft:
        raise PermissionError("protected E3 handoff changes its actual candidate or original fit selection")
    authenticate_configured_protected_e3_fit_config(artifact_writer, fit)
    ports = []
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection
    retained_scope = None
    if isinstance(selection, ConfiguredE3ContinuedPreparationSelection):
        from empirical_lawhood.api.configured_e3_retained_runtime import RetainedE3ExecutionScope
        retained_scope = RetainedE3ExecutionScope(writer=artifact_writer, selection=selection)
        with retained_scope.open():
            pass
    custody = CurrentIssuedTaskCustody(writer=artifact_writer, reveal_authority_id=reveal_authority_id,
        original_control_scopes=() if retained_scope is None else (retained_scope.open,))
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("protected E3 handoff substitutes its installed exact-input port")
        supplier = ProtectedE3RuntimeInputSupplier(platform.port.supplier, writer=artifact_writer,
            root=handoff.authoring.base.draft, fit_config=fit, qualifications=selection.qualifications,
            selection=selection,
            reveal_authority_id=reveal_authority_id, custody=custody, retained_e3_scope=retained_scope)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))
