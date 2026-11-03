# SPDX-License-Identifier: MPL-2.0
"""Original DEV to revision composition over existing component lifecycle owners."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as acquisition_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_revision_transition as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_revision_preparation as component
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
from empirical_lawhood.api.composite_experiment_programme import write_experiment_programme_descriptor
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import _retained_plans
from empirical_lawhood.api.selected_e4_method_runtime import export_selected_e4_revision_inputs_from_acquisition, read_selected_e4_revision
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, artifact_custody_limits
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.experiment_programme import ExperimentProgrammeDescriptor
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input


PARENT_FILENAME = "revision-acquisition-programme.json"
COMPONENT_DIRECTORY = "revision-component"


def _location(writer, directory, filename, *, for_write):
    path = Path(directory)
    if not path.is_absolute() or any(value.is_symlink() for value in (path, *path.parents)):
        raise ValueError("selected DEV revision programme requires its guarded absolute real directory")
    root = Path(writer.root.contract.canonical_path)
    relative = (path / filename).relative_to(root).as_posix()
    return relative, writer.root.resolve(relative, for_write=for_write)


class SelectedE4RevisionAcquisitionService:
    def __init__(self, *, service, descriptor=None):
        if descriptor is not None and type(descriptor) is not ExperimentProgrammeDescriptor:
            raise TypeError("selected DEV revision programme requires its registered descriptor")
        self.service, self.descriptor = service, descriptor

    def author(self, *, preparation, output_dir):
        from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
        programme = preparation.programme
        if (type(programme) is not domain.SelectedE4RevisionAcquisitionProgramme or not preparation.executable
                or programme.resolved_source is not None or preparation.specification_record != programme.specification
                or preparation.specification != programme.specification.identity
                or preparation.allocation != programme.allocation or preparation.execution != programme.execution):
            raise ValueError("selected DEV transition authoring changes its exact declared preparation")
        programme.__post_init__()
        writer = self.service.artifact_writer
        _location(writer, output_dir, PARENT_FILENAME, for_write=True)
        original = writer.root.resolve(programme.source.authored_directory, for_write=False)
        exported = export_selected_e4_revision_inputs_from_acquisition(directory=original, artifact_writer=writer,
            output_directory=Path(output_dir) / "derived-inputs", campaign=programme.campaign,
            resources=programme.resources, allow_partial=programme.source.allow_partial,
            expected_specification=programme.specification.revision, expected_allocation=programme.allocation)
        records = exported["records"]
        if (records["programme"].identity != programme.specification.revision.programme
                or acquisition_owner.allocation(records["programme"]) != programme.allocation):
            raise PermissionError("selected DEV transition substitutes the original authenticated allocation")
        bound = load_experiment_inputs(programme.specification.revision, Path(exported["sources_path"]), artifact_writer=writer)
        child = prepare_experiment(programme.specification.revision, scientific_inputs=bound.scientific_inputs,
            method_inputs=bound.method_inputs, execution=programme.execution)
        # This delegates authoring only. Actual fitting still requires the
        # direct component's fresh original DEV parent-custody preparation.
        authored = self.service.author(preparation=child, output_dir=Path(output_dir) / COMPONENT_DIRECTORY)
        packet, draft, _, payloads = load_authored_wave(directory=Path(output_dir) / COMPONENT_DIRECTORY,
            artifact_writer=writer, lazy_payloads=True)
        _, plan, _ = _retained_plans(payloads, draft)
        instance = decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)
        retained = replace(programme, resolved_source=records["acquisition"],
            child_packet=ObjectIdentity.from_record(packet.packet_id, packet),
            child_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            child_instance=ObjectIdentity.from_record("recursive-member.experiment-instance", instance))
        relative, _ = _location(writer, output_dir, PARENT_FILENAME, for_write=True)
        parent_relative = str(Path(relative).parent)
        writer.write(ArtifactWriteRequest(retained.record_id, relative, retained.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", retained.record_id, parent_relative, retained.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        descriptor = ExperimentProgrammeDescriptor("descriptor." + retained.fingerprint(), domain.PROTOCOL_ID,
            retained.specification.identity, retained.identity)
        write_experiment_programme_descriptor(service=self.service, directory=output_dir, descriptor=descriptor)
        return {**authored, "authoring_dir": str(output_dir), "component_dir": str(Path(output_dir) / COMPONENT_DIRECTORY),
            "programme": retained.identity.to_document(), "sources_path": exported["sources_path"],
            "native_contact": "none", "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}

    def _retained(self, directory):
        if self.descriptor is None:
            raise ValueError("selected DEV transition requires its authenticated retained programme descriptor")
        writer = self.service.artifact_writer
        relative, path = _location(writer, directory, PARENT_FILENAME, for_write=False)
        limit = artifact_custody_limits(writer).manifest_bytes
        manifest = decode_artifact_manifest(read_bounded_bytes(writer.root.resolve(relative + ".manifest.json", for_write=False),
            maximum_bytes=limit), maximum_bytes=limit)
        if (manifest.materialization.relative_path != relative or manifest.materialization.storage_root_id != writer.root.contract.storage_root_id
                or manifest.logical.payload_schema != domain.SelectedE4RevisionAcquisitionProgramme.SCHEMA
                or manifest.logical.media_type != "application/json"
                or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise PermissionError("selected DEV transition substitutes original programme publication custody")
        writer.verify_manifest(manifest)
        raw = read_bounded_bytes(path, maximum_bytes=manifest.materialization.size_bytes)
        programme = decode_canonical_bytes(raw, domain.SelectedE4RevisionAcquisitionProgramme,
            maximum_bytes=manifest.materialization.size_bytes)
        if (programme.canonical_bytes() != raw or sha256(raw).hexdigest() != manifest.logical.content_sha256
                or programme.identity != self.descriptor.programme or programme.specification.identity != self.descriptor.specification
                or programme.resolved_source is None):
            raise PermissionError("selected DEV transition changes actual original declared programme bytes or complete child closure")
        packet, draft, source, payloads = load_authored_wave(directory=Path(directory) / COMPONENT_DIRECTORY,
            artifact_writer=writer, lazy_payloads=True)
        _, plan, _ = _retained_plans(payloads, draft)
        instance = decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)
        if ((ObjectIdentity.from_record(packet.packet_id, packet), ObjectIdentity.from_record(plan.execution_plan_id, plan),
                ObjectIdentity.from_record("recursive-member.experiment-instance", instance)) !=
                (programme.child_packet, programme.child_plan, programme.child_instance)
                or instance.specification != programme.specification.revision.identity
                or ObjectIdentity.from_record("recursive-member.implementation", source) != programme.source_snapshot):
            raise PermissionError("selected DEV transition substitutes its original exact child packet/plan/instance/source")
        companions = {}
        kinds = {kind.SCHEMA: (name, kind) for name, kind in component.INPUT_TYPES.items() if name != "resources"}
        for reference in instance.sources:
            name, kind = kinds[reference.object_schema]
            member = "experiment-source-" + sha256(reference.object_id.encode()).hexdigest() + ".json"
            companions[name] = decode_canonical_bytes(payloads[member], kind, maximum_bytes=None)
        if (companions["acquisition"] != programme.resolved_source or companions["campaign"] != programme.campaign
                or companions["programme"].identity != programme.specification.revision.programme
                or acquisition_owner.allocation(companions["programme"]) != programme.allocation):
            raise PermissionError("selected DEV transition changes original native acquisition or complete scientific choices")
        budgets = dict(programme.resources.phase_budgets)
        declarations = {row.capability_key: row for row in methods.operation_declarations()}
        for operation in draft.operations:
            declaration = declarations[operation.selection.capability_key]
            config = decode_recursive_config_input(operation, declaration.registration()).record
            if operation.resource_budget != budgets[config.operation] or config.operational_budget != budgets[config.operation]:
                raise PermissionError("selected DEV transition changes its frozen explicit operational reservations")
        return programme

    def _workers(self, programme, maximum_parallel_tasks):
        if maximum_parallel_tasks != programme.workers:
            raise ValueError("selected DEV transition execution changes its retained explicit worker selection")

    def run(self, *, directory, maximum_parallel_tasks, programme_request_path=None, confirmed=False, result_read_scope='FULL'):
        if programme_request_path is not None or confirmed:
            raise ValueError("selected DEV transition uses genuine development custody and accepts no issued request/confirmation")
        programme = self._retained(directory)
        self._workers(programme, maximum_parallel_tasks)
        return self.service.run(directory=Path(directory) / COMPONENT_DIRECTORY,
            maximum_parallel_tasks=maximum_parallel_tasks, result_read_scope=result_read_scope)

    def recover(self, *, directory, maximum_parallel_tasks, programme_request_path=None, confirmed=False, result_read_scope='FULL'):
        if programme_request_path is not None or confirmed:
            raise ValueError("selected DEV transition recovery accepts no issued request/confirmation")
        programme = self._retained(directory)
        self._workers(programme, maximum_parallel_tasks)
        return self.service.recover(directory=Path(directory) / COMPONENT_DIRECTORY,
            maximum_parallel_tasks=maximum_parallel_tasks, result_read_scope=result_read_scope)

    def read_execution(self, *, directory, programme_request_path=None):
        if programme_request_path is not None:
            raise ValueError('selected DEV revision inspection accepts no issued request')
        programme = self._retained(directory)
        report = self.service.read_execution(directory=Path(directory) / COMPONENT_DIRECTORY,
            expected_specification_bytes=programme.specification.revision.canonical_bytes())
        if report.get('execution_plan') != programme.child_plan.to_document():
            raise PermissionError('selected DEV revision inspection changes its retained child plan')
        return {**report, 'programme': programme.identity.to_document()}

    def read(self, *, directory, allow_partial=False, programme_request_path=None):
        if programme_request_path is not None:
            raise ValueError("selected DEV transition inspection accepts no issued request selection")
        programme = self._retained(directory)
        report = read_selected_e4_revision(directory=Path(directory) / COMPONENT_DIRECTORY,
            artifact_writer=self.service.artifact_writer, allow_partial=allow_partial)
        return {**report, "programme": programme.identity.to_document(),
            "native_acquisition": programme.resolved_source.to_document(), "new_native_contact_count": 0}


def programme_service_factory(*, service, descriptor=None):
    return SelectedE4RevisionAcquisitionService(service=service, descriptor=descriptor)
