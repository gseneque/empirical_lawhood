# SPDX-License-Identifier: MPL-2.0
"""Programme orchestration over retained waves and the existing inquiry services.

Progress lives in authored specifications, task receipts, recovery records and
committed inquiry packets. This service derives a current readout from those
owners; it stores no authority verdict, replacement journal or scheduler state.
"""

from collections import defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity

from .experiment_runtime_bindings import experiment_runtime_binding


def _phase_progress(report, plan):
    rows = {row["task_id"]: row for row in report["task_census"]}
    if len(rows) != len(report["task_census"]) or set(rows) != {task.task_id for task in plan.tasks}:
        raise ValueError("programme progress changes its complete selected task census")
    phases = defaultdict(list)
    for task in plan.tasks:
        phases[task.stage.value].append(dict(rows[task.task_id]))
    return tuple({"phase": phase, "assigned_tasks": len(tasks),
                  "completed_tasks": sum(row["operational_status"] == "SUCCEEDED" for row in tasks),
                  "tasks": tuple(sorted(tasks, key=lambda row: row["task_id"]))}
                 for phase, tasks in sorted(phases.items()))


@dataclass(frozen=True, slots=True)
class ExperimentProgrammeService:
    project_root: Path
    artifact_writer: object
    storage_profile: object | None = None
    prospective_experiment_loader: object | None = None
    prospective_api_factory: object | None = None
    catalog_relative_path: str | None = field(default=None, kw_only=True)
    approval_checker_trust_path: Path | None = field(default=None, kw_only=True)


    def __post_init__(self):

        if self.catalog_relative_path is not None and self.prospective_api_factory is not None:
            raise ValueError("catalog_relative_path cannot replace an injected prospective_api_factory catalog")
        if self.approval_checker_trust_path is not None and self.prospective_api_factory is not None:
            raise ValueError("approval_checker_trust_path cannot replace an injected prospective_api_factory trust root")

    operator_artifact_root_contract: object | None = field(default=None, kw_only=True)

    def _composite_programme(self, *, directory=None, preparation=None):
        from .composite_experiment_programme import selected_composite_programme_service

        return selected_composite_programme_service(service=self, directory=directory, preparation=preparation)

    def _selected_workers(self, requested):
        from empirical_lawhood.runtime.experiment_preparation import select_experiment_workers

        return select_experiment_workers(requested,
            profile_maximum=getattr(self.storage_profile, "maximum_parallel_tasks", None))

    def _prospective_context(self, directory, *, maximum_parallel_tasks=None, reveal_authority_id=None,
            lifecycle="run", recovery_run_id=None, read_access=None):
        from .prospective_experiment import RetainedProspectiveExperiment, load_prepared_prospective_experiment, load_retained_prospective_experiment
        from empirical_lawhood.api.composition import create_api
        from empirical_lawhood.runtime.prospective_experiment import PreparedProspectiveExperimentHandoff

        if self.operator_artifact_root_contract is not None and self.prospective_api_factory is not None:
            raise ValueError("selected external root cannot replace an injected programme API")
        maximum_parallel_tasks = self._selected_workers(maximum_parallel_tasks)
        from .recursive_execution import validate_recursive_worker_controls
        validate_recursive_worker_controls(maximum_parallel_tasks, None)
        if self.storage_profile is None:
            raise ValueError("prospective programme requires its selected operator storage profile")
        api_options = {}
        if self.catalog_relative_path is not None:
            api_options["catalog_relative_path"] = self.catalog_relative_path
        if self.approval_checker_trust_path is not None:
            api_options["approval_checker_trust_path"] = self.approval_checker_trust_path
        if hasattr(self.artifact_writer, 'artifact_verification'):
            api_options['artifact_verification'] = self.artifact_writer.artifact_verification

        def compose(selected):
            if type(selected) not in (PreparedProspectiveExperimentHandoff, RetainedProspectiveExperiment):
                raise TypeError("prospective programme requires its authenticated experiment companion")
            if self.prospective_api_factory is not None:
                return self.prospective_api_factory(handoff=getattr(selected, "handoff", None), project_root=self.project_root,
                    storage_profile=self.storage_profile, maximum_parallel_tasks=maximum_parallel_tasks)
            if type(selected) is RetainedProspectiveExperiment:
                return create_api(repo_root=self.project_root, operator_storage_profile=self.storage_profile,
                    operator_artifact_root_contract=self.operator_artifact_root_contract,
                    artifact_profile_validators=getattr(self.artifact_writer, "validators", None),
                    maximum_parallel_tasks=maximum_parallel_tasks, **api_options)
            handoff = selected.handoff
            return create_api(repo_root=self.project_root, operator_storage_profile=self.storage_profile,
                operator_artifact_root_contract=self.operator_artifact_root_contract,
                artifact_profile_validators=getattr(self.artifact_writer, "validators", None),
                candidate_context_provider=handoff.context, candidate_capability_catalog=handoff.context.catalog,
                study_bundle_registry=handoff.compilation.registry, executable_platform_ports=handoff.platform_ports,
                maximum_parallel_tasks=maximum_parallel_tasks, **api_options)

        if lifecycle == "recover" and recovery_run_id is None:
            raise ValueError("default recovery requires its exact requested run identity")
        default_loader = load_retained_prospective_experiment if lifecycle == "read" else load_prepared_prospective_experiment
        loader = self.prospective_experiment_loader or default_loader
        options = {} if lifecycle == "read" else {"reveal_authority_id": reveal_authority_id}
        if read_access is not None:
            options["read_access"] = read_access
        if lifecycle == "recover":
            options["require_current_source"] = False
        selected = loader(directory=directory, project_root=self.project_root,
            storage_profile=self.storage_profile, artifact_writer=self.artifact_writer, **options)
        return selected, compose(selected)

    @staticmethod
    def _prospective_report(result, selected):
        from .prospective_experiment import RetainedProspectiveExperiment

        projection = selected.projection if type(selected) is RetainedProspectiveExperiment else selected.handoff.projection
        return {**result.to_mapping(), "programme": {
            "lifecycle": "PROSPECTIVE", "specification": selected.instance.specification.to_document(),
            "experiment_association": selected.association.identity.to_document(),
            "candidate": selected.association.candidate.to_document(),
            "assigned_tasks": len(projection.tasks)}}

    @staticmethod
    def _is_prospective(directory):
        return (Path(directory) / "experiment" / "experiment-association.json").exists()

    def prepare(self, specification, *, scientific_inputs=None, execution=None,
                protocol_bytes=None, method_inputs=None):
        """Derive the installed design; execution selections remain explicit."""
        from .experiment_preparation import prepare_experiment

        from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

        if execution is not None and type(execution) is not ExecutionSelection:
            raise TypeError("experiment execution requires its typed operational selection")
        execution = ExecutionSelection() if execution is None else execution
        execution = replace(execution, workers=self._selected_workers(execution.workers))
        preparation = prepare_experiment(specification, scientific_inputs=scientific_inputs,
            execution=execution, protocol_bytes=protocol_bytes, method_inputs=method_inputs)
        from .experiment_preparation import _protocol
        binding = experiment_runtime_binding(_protocol(specification))
        if binding is not None and binding.programme_service_factory is not None:
            composite = binding.programme_service_factory(service=self, descriptor=None)
            preparation = self._refine_preparation(preparation, composite)
        return preparation

    def _refine_preparation(self, preparation, composite):
        """Reuse the same installed owner projection before prepare/author."""
        from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation
        from dataclasses import fields
        refine = getattr(composite, "refine_preparation", None)
        if not callable(refine):
            return preparation
        refined = refine(preparation)
        if type(refined) is not ExperimentPreparation:
            raise TypeError("Programme preparation refinement requires its exact typed preparation")
        refined.__post_init__()
        if any(getattr(refined, value.name) != getattr(preparation, value.name)
                for value in fields(ExperimentPreparation)
                if value.name not in ("census", "dependencies", "assessment_limitations")):
            raise ValueError("Programme preparation refinement changes its original selection, inputs or execution")
        return refined

    def continue_matrix(self, *, predecessor_directory, output_dir, confirmed=False, maximum_parallel_tasks=None,
            pure_output_bytes=None):
        """Prepare, derive, author and execute a repaired Matrix continuation."""
        from .matrix_programme_continue import continue_matrix_programme
        return continue_matrix_programme(self, predecessor_directory=predecessor_directory,
            output_dir=output_dir, confirmed=confirmed, maximum_parallel_tasks=maximum_parallel_tasks,
            **({} if pure_output_bytes is None else {'pure_output_bytes': pure_output_bytes}))

    def derive_inputs(self, *, specification_path, source_selection_path, metadata_directory,
            output_selection_path, execution, read_access=None):
        """Publish selected current metadata through its installed domain owner."""
        from .experiment_preparation import derive_experiment_inputs
        from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
        if type(execution) is not ExecutionSelection:
            raise TypeError("input derivation requires its explicit execution selection")
        execution = replace(execution, workers=self._selected_workers(execution.workers))
        from .experiment_preparation import (
            _protocol, _validate_experiment_input_derivation_result, load_experiment_specification,
        )
        specification = load_experiment_specification(Path(specification_path))
        protocol = _protocol(specification)
        binding = experiment_runtime_binding(protocol)
        if binding is not None and binding.derive_inputs_with_service is not None:
            result = binding.derive_inputs_with_service(service=self, specification=specification,
                source_selection_path=Path(source_selection_path), metadata_directory=Path(metadata_directory),
                output_selection_path=Path(output_selection_path), execution=execution,
                **({} if read_access is None else {'read_access': read_access}))
            return _validate_experiment_input_derivation_result(specification=specification, protocol=protocol,
                binding=binding, result=result, artifact_writer=self.artifact_writer,
                output_selection_path=output_selection_path, execution=execution, read_access=read_access)
        if binding is not None and binding.programme_service_factory is not None:
            composite = binding.programme_service_factory(service=self, descriptor=None)
            derive = getattr(composite, "derive_inputs", None)
            if callable(derive):
                result = derive(specification=specification, source_selection_path=Path(source_selection_path),
                    metadata_directory=Path(metadata_directory), output_selection_path=Path(output_selection_path),
                    execution=execution, **({} if read_access is None else {'read_access': read_access}))
                # Same-protocol selector transitions still require all ordinary original-publication checks.
                result = _validate_experiment_input_derivation_result(specification=specification, protocol=protocol,
                    binding=binding, result=result, artifact_writer=self.artifact_writer,
                    output_selection_path=output_selection_path, execution=execution, read_access=read_access)
                return replace(result, preparation=self._refine_preparation(result.preparation, composite))
        return derive_experiment_inputs(specification_path=specification_path,
            source_selection_path=source_selection_path, project_root=self.project_root,
            artifact_writer=self.artifact_writer, metadata_directory=metadata_directory,
            output_selection_path=output_selection_path, execution=execution,
            **({} if read_access is None else {'read_access': read_access}))

    def export_products(self, *, directory, selection_path, read_access=None, programme_request_path=None):
        """Invoke the retained protocol's declared postprocessing, never native work."""
        composite = self._composite_programme(directory=directory)
        if composite is not None:
            if read_access is not None:
                raise ValueError('Composite product export requires its own component authority selections')
            export = getattr(composite, "export_products", None)
            if not callable(export):
                raise ValueError("selected programme has no installed component product export transition")
            options = {} if programme_request_path is None else {'programme_request_path': programme_request_path}
            return export(directory=directory, selection_path=selection_path, **options)
        if programme_request_path is not None:
            raise ValueError('Composite product export selection requires a registered retained programme')
        from empirical_lawhood.api.recursive_authoring import load_authored_wave
        from .experiment_preparation import experiment_protocols
        if self._is_prospective(directory):
            if read_access is not None:
                raise ValueError('Prospective product export requires its own typed authority selection')
            from .prospective_experiment import RetainedProspectiveExperiment, load_retained_prospective_experiment

            loader = self.prospective_experiment_loader or load_retained_prospective_experiment
            selected = loader(directory=directory, project_root=self.project_root,
                storage_profile=self.storage_profile, artifact_writer=self.artifact_writer)
            if type(selected) is not RetainedProspectiveExperiment:
                raise TypeError("prospective product export requires its authenticated retained companion")
            pin = selected.instance.specification
            declarations = tuple(value for value in experiment_protocols()
                if (value.specification_type.SCHEMA, value.specification_type.VERSION) ==
                    (pin.object_schema, pin.object_version))
            if len(declarations) != 1:
                raise ValueError("prospective product export lacks one installed exact original protocol")
            binding = experiment_runtime_binding(declarations[0])
            if binding is None or not callable(binding.export_products):
                raise ValueError("selected protocol has no installed product export transition")
            return binding.export_products(directory=directory, selected=selected, project_root=self.project_root,
                artifact_writer=self.artifact_writer, selection_path=selection_path)
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
        import json
        _, _, _, payloads = load_authored_wave(directory=directory,artifact_writer=self.artifact_writer,lazy_payloads=True,
            **({} if read_access is None else {'read_access': read_access}))
        if 'experiment-specification.json' not in payloads or 'experiment-instance.json' not in payloads:
            raise PermissionError('product export needs its exact retained public experiment instance')
        raw=payloads['experiment-specification.json'];document=json.loads(raw)
        declarations=tuple(value for value in experiment_protocols() if
            (value.specification_type.SCHEMA,value.specification_type.VERSION)==(document.get('schema'),document.get('version')))
        if len(declarations)!=1:
            raise ValueError('product export lacks one installed exact original protocol')
        declaration,=declarations
        specification=decode_canonical_bytes(raw,declaration.specification_type,maximum_bytes=len(raw))
        raw_instance=payloads['experiment-instance.json']
        instance=decode_canonical_bytes(raw_instance,ExperimentInstanceBinding,maximum_bytes=len(raw_instance))
        if specification.canonical_bytes()!=raw or instance.specification!=specification.identity:
            raise PermissionError('product export substitutes its original selected scientific specification')
        binding=experiment_runtime_binding(declaration)
        if binding is None or not callable(binding.export_products):
            raise ValueError('selected protocol has no installed product export transition')
        original_access = getattr(payloads, 'original_input_access', None)
        if original_access is not None:
            original_access.require_current()
        report = binding.export_products(directory=directory, artifact_writer=self.artifact_writer,
            selection_path=selection_path, **({} if read_access is None else {'read_access': read_access}))
        if original_access is not None:
            original_access.require_current()
        return report

    def explain(self, preparation):
        from .experiment_preparation import experiment_preparation_report

        return experiment_preparation_report(preparation)

    def author(self, *, preparation, output_dir, read_access=None):
        from .experiment_preparation import author_prepared_experiment

        if preparation.execution is None or preparation.execution.workers is None:
            raise ValueError("experiment authoring requires explicitly selected worker concurrency")
        self._selected_workers(preparation.execution.workers)
        composite = self._composite_programme(preparation=preparation)
        if composite is not None:
            if read_access is not None:
                raise ValueError("Composite authoring cannot select development read access")
            scoped_author = getattr(composite, "author_with_preparation", None)
            if callable(scoped_author):
                # The owner keeps its actual prerequisite context alive through
                # publication, rather than decoding it again after refinement.
                return scoped_author(preparation=preparation, output_dir=output_dir)
            preparation = self._refine_preparation(preparation, composite)
            if not preparation.executable:
                retain = getattr(composite, "retain_unentered", None)
                if not callable(retain):
                    raise ValueError("Programme authoring requires all declared preparation dependencies")
                return retain(preparation=preparation, output_dir=output_dir)
            return composite.author(preparation=preparation, output_dir=output_dir)
        return author_prepared_experiment(preparation=preparation, project_root=self.project_root,
            artifact_writer=self.artifact_writer, output_dir=output_dir,
            **({} if read_access is None else {'read_access': read_access}))

    def run(self, *, directory, maximum_parallel_tasks=None, inquiry_successor=False, request=None,
            programme_request_path=None, confirmed=False, read_access=None, result_read_scope="FULL"):
        """Execute the retained wave, replaying any original inquiry admission."""
        from .recursive_execution import run_recursive_wave, validate_recursive_worker_controls
        from empirical_lawhood.api.recursive_inquiry import run_inquiry_successor

        if type(confirmed) is not bool:
            raise TypeError("Programme confirmation must be an explicit boolean")
        if result_read_scope not in ("FULL", "EXECUTION_RECORDS"):
            raise ValueError("programme operation requires an explicit full or execution-record result scope")
        composite = self._composite_programme(directory=directory)
        if result_read_scope != "FULL" and (inquiry_successor
                or composite is not None and not callable(getattr(composite, 'read_execution', None))):
            raise ValueError("execution-only result scope requires an owning execution-record reader")
        if composite is not None:
            if request is not None or inquiry_successor is not False or read_access is not None:
                raise ValueError("Composite programme refuses single-campaign or inquiry options")
            workers = self._selected_workers(maximum_parallel_tasks)
            from .recursive_execution import validate_recursive_worker_controls

            validate_recursive_worker_controls(workers, None)
            return composite.run(directory=directory, maximum_parallel_tasks=workers,
                programme_request_path=programme_request_path, confirmed=confirmed,
                **({} if result_read_scope == 'FULL' else {'result_read_scope': result_read_scope}))
        if programme_request_path is not None or confirmed:
            raise ValueError("Composite programme options require a registered retained programme")
        if type(inquiry_successor) is not bool:
            raise TypeError("programme execution requires its explicit lifecycle selection")
        maximum_parallel_tasks = self._selected_workers(maximum_parallel_tasks)
        validate_recursive_worker_controls(maximum_parallel_tasks, None)
        if request is not None or self._is_prospective(directory):
            from empirical_lawhood.api.results import RunCampaignRequest

            if type(request) is not RunCampaignRequest or inquiry_successor:
                raise TypeError("prospective programme run requires its existing typed campaign request")
            selected, api = self._prospective_context(directory, maximum_parallel_tasks=maximum_parallel_tasks,
                reveal_authority_id=request.reveal_authority_id, read_access=read_access)
            from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
            with current_issued_task_control_scope(api):
                result = api.run_campaign(request, expected_candidate=selected.association.candidate)
            return self._prospective_report(result, selected)
        owner_options = {}
        if inquiry_successor:
            if read_access is not None:
                raise ValueError("inquiry execution cannot select development read access")
            owner = run_inquiry_successor
        else:
            owner = run_recursive_wave
            owner_options["require_initial_experiment"] = True
            if result_read_scope != "FULL":
                owner_options["result_read_scope"] = result_read_scope
            if read_access is not None:
                owner_options["read_access"] = read_access

        return owner(directory=directory, project_root=self.project_root,
                     artifact_writer=self.artifact_writer, maximum_parallel_tasks=maximum_parallel_tasks,
                     **owner_options)

    def repair_development_structure(self, *, directory, repair_instruction_path,
            maximum_parallel_tasks=None, confirmed=False, read_access=None):
        """Execute one separate PURE child with the complete failed original retained."""
        from hashlib import sha256
        from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
        from .development_structure_repair import repair_development_structure
        from .recursive_execution import validate_recursive_worker_controls
        if confirmed is not True:
            raise ValueError('structural repair requires the explicit --yes selection')
        instruction = read_bounded_bytes(Path(repair_instruction_path), maximum_bytes=1024 * 1024)
        if not instruction.strip():
            raise ValueError('structural repair instruction is empty')
        workers = self._selected_workers(maximum_parallel_tasks)
        validate_recursive_worker_controls(workers, None)
        return repair_development_structure(service=self, directory=directory,
            owner_instruction_sha256=sha256(instruction).hexdigest(), maximum_parallel_tasks=workers,
            read_access=read_access)

    def prepare_native_continuation(self, *, directory, run_id, output_dir,
            preparation_instruction_path, worker_interpreter, worker_source_root,
            pure_output_bytes, read_access=None):
        """Prepare an exact incomplete-native proposal without execution authority."""
        from hashlib import sha256
        from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
        from empirical_lawhood.kernel.serialization import validate_stable_id
        from .native_continuation_preparation import prepare_native_continuation
        validate_stable_id(run_id)
        if type(pure_output_bytes) is not int or not 0 < pure_output_bytes <= 256 * 1024**2:
            raise ValueError('native continuation preparation requires its bounded PURE output proposal')
        instruction = read_bounded_bytes(Path(preparation_instruction_path), maximum_bytes=1024 * 1024)
        if not instruction.strip():
            raise ValueError('native continuation preparation instruction is empty')
        return prepare_native_continuation(service=self, directory=directory, run_id=run_id,
            output_dir=output_dir, preparation_instruction_sha256=sha256(instruction).hexdigest(),
            worker_interpreter=worker_interpreter, worker_source_root=worker_source_root,
            pure_output_bytes=pure_output_bytes, read_access=read_access)

    def continue_native(self, *, directory, run_id, proposal_path, execution_instruction_path,
            maximum_parallel_tasks=None, confirmed=False, read_access=None):
        """Validate a separate native selection; dispatch only on explicit confirmation."""
        from hashlib import sha256
        from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
        from empirical_lawhood.kernel.serialization import validate_stable_id
        from .native_continuation_execution import continue_native
        from .recursive_execution import validate_recursive_worker_controls
        validate_stable_id(run_id)
        if type(confirmed) is not bool:
            raise TypeError('native continuation confirmation must be an explicit boolean')
        instruction = read_bounded_bytes(Path(execution_instruction_path), maximum_bytes=1024 * 1024)
        if not instruction.strip():
            raise ValueError('native continuation execution selection is empty')
        workers = self._selected_workers(maximum_parallel_tasks)
        validate_recursive_worker_controls(workers, None)
        return continue_native(service=self, directory=directory, run_id=run_id, proposal_path=proposal_path,
            owner_instruction_sha256=sha256(instruction).hexdigest(), maximum_parallel_tasks=workers,
            confirmed=confirmed, read_access=read_access)

    def recover(self, *, directory, maximum_parallel_tasks=None, inquiry_successor=False, request=None,
            programme_request_path=None, confirmed=False, custody_only=False, read_access=None, result_read_scope="FULL",
            repair_retained_e3=False, repair_development_output_bytes=None,
            repair_development_controller=False,
            worker_interpreter=None, worker_source_root=None, repair_instruction_path=None):
        """Reuse completed custody; the native owner still refuses UNKNOWN retry."""
        if type(repair_retained_e3) is not bool:
            raise TypeError('Retained E3 repair selection must be an explicit boolean')
        if type(repair_development_controller) is not bool:
            raise TypeError('Development controller repair selection must be an explicit boolean')
        if repair_development_controller and repair_development_output_bytes is None:
            raise ValueError('development controller repair requires its explicit PURE output allowance')
        if repair_development_output_bytes is not None:
            from .results import ResumeCampaignRequest
            if (type(repair_development_output_bytes) is not int
                    or not 0 < repair_development_output_bytes <= 256 * 1024**2
                    or repair_retained_e3 or programme_request_path is not None or confirmed
                    or custody_only or inquiry_successor or result_read_scope != 'FULL'
                    or type(request) is not ResumeCampaignRequest or request.confirmed is not True
                    or request.reconcile_only or request.reveal_authority_id is not None
                    or request.parent_record_path is not None or request.parent_input_binding_paths
                    or worker_interpreter is None or worker_source_root is None or repair_instruction_path is None):
                raise ValueError('development output repair requires one confirmed development run, a bounded output allowance, frozen worker and owner instruction')
            from hashlib import sha256
            from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
            from .development_output_repair import recover_development_output_budget
            from .development_controller_repair import recover_development_controller
            from .recursive_execution import validate_recursive_worker_controls
            instruction = read_bounded_bytes(Path(repair_instruction_path), maximum_bytes=1024 * 1024)
            if not instruction.strip():
                raise ValueError('development output repair instruction is empty')
            workers = self._selected_workers(maximum_parallel_tasks)
            validate_recursive_worker_controls(workers, None)
            owner = recover_development_controller if repair_development_controller else recover_development_output_budget
            return owner(service=self, directory=directory,
                run_id=request.run_id, output_bytes=repair_development_output_bytes,
                owner_instruction_sha256=sha256(instruction).hexdigest(),
                worker_interpreter=worker_interpreter, worker_source_root=worker_source_root,
                maximum_parallel_tasks=workers, read_access=read_access)
        if repair_retained_e3:
            if (programme_request_path is not None or confirmed or custody_only or inquiry_successor
                    or result_read_scope != 'FULL' or worker_interpreter is None
                    or worker_source_root is None or repair_instruction_path is None):
                raise ValueError('retained E3 repair requires a single run, frozen worker and owner instruction')
            from hashlib import sha256
            from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
            instruction = read_bounded_bytes(Path(repair_instruction_path), maximum_bytes=1024 * 1024)
            if not instruction.strip():
                raise ValueError('retained E3 repair instruction is empty')
            return self.repair_retained_e3(directory=directory, request=request,
                owner_instruction_sha256=sha256(instruction).hexdigest(),
                worker_interpreter=worker_interpreter, worker_source_root=worker_source_root,
                maximum_parallel_tasks=maximum_parallel_tasks, read_access=read_access)
        if any(value is not None for value in (worker_interpreter, worker_source_root, repair_instruction_path)):
            raise ValueError('frozen worker and repair instruction require an explicit selective repair')
        if type(custody_only) is not bool:
            raise TypeError("Custody-only recovery requires an explicit boolean")
        if type(confirmed) is not bool:
            raise TypeError("Programme confirmation must be an explicit boolean")
        if result_read_scope not in ("FULL", "EXECUTION_RECORDS"):
            raise ValueError("programme operation requires an explicit full or execution-record result scope")
        if result_read_scope != "FULL" and (custody_only or inquiry_successor):
            raise ValueError("execution-only result scope requires ordinary execution custody")
        if custody_only:
            if (maximum_parallel_tasks is not None or inquiry_successor is not False or request is not None
                    or programme_request_path is not None or confirmed or read_access is not None):
                raise ValueError("Custody-only recovery requires an initial development wave without execution or authority options")
            from .recursive_execution import recover_recursive_custody

            return recover_recursive_custody(directory=directory, project_root=self.project_root,
                artifact_writer=self.artifact_writer)
        composite = self._composite_programme(directory=directory)
        if composite is not None:
            if result_read_scope != 'FULL' and not callable(getattr(composite, 'read_execution', None)):
                raise ValueError('composite recovery lacks an owning execution-record reader')
            if request is not None or inquiry_successor is not False or read_access is not None:
                raise ValueError("Composite programme refuses single-campaign or inquiry options")
            workers = self._selected_workers(maximum_parallel_tasks)
            from .recursive_execution import validate_recursive_worker_controls

            validate_recursive_worker_controls(workers, None)
            return composite.recover(directory=directory, maximum_parallel_tasks=workers,
                programme_request_path=programme_request_path, confirmed=confirmed,
                **({} if result_read_scope == 'FULL' else {'result_read_scope': result_read_scope}))
        if programme_request_path is not None or confirmed:
            raise ValueError("Composite programme options require a registered retained programme")
        if request is not None or self._is_prospective(directory):
            from empirical_lawhood.api.results import ResumeCampaignRequest
            from .recursive_execution import validate_recursive_worker_controls

            maximum_parallel_tasks = self._selected_workers(maximum_parallel_tasks)
            validate_recursive_worker_controls(maximum_parallel_tasks, None)
            if type(request) is not ResumeCampaignRequest or inquiry_successor is not False:
                raise TypeError("prospective programme recovery requires its existing typed campaign request")
            selected, api = self._prospective_context(directory, maximum_parallel_tasks=maximum_parallel_tasks,
                reveal_authority_id=request.reveal_authority_id,
                lifecycle="read" if request.reconcile_only else "recover",
                recovery_run_id=request.run_id, read_access=read_access)
            from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
            from contextlib import nullcontext
            from copy import copy
            from .execution import CampaignExecutionService

            execution = getattr(api, "_execution_service", None)
            scope = (execution._reconciliation_package_read_scope(request.run_id)
                if (request.reconcile_only and request.confirmed is True
                    and self.prospective_api_factory is None
                    and type(execution) is CampaignExecutionService)
                else nullcontext(execution))
            with scope as current_execution:
                current_api = api
                if current_execution is not execution:
                    current_api = copy(api)
                    current_api._execution_service = current_execution
                with current_issued_task_control_scope(current_api):
                    result = current_api.resume_campaign(request,
                        expected_candidate=selected.association.candidate)
            return self._prospective_report(result, selected)
        return self.run(directory=directory, maximum_parallel_tasks=maximum_parallel_tasks,
                        inquiry_successor=inquiry_successor,
                        **({} if result_read_scope == "FULL" else {"result_read_scope": result_read_scope}),
                        **({} if read_access is None else {"read_access": read_access}))

    def repair_retained_e3(self, *, directory, request, owner_instruction_sha256,
            worker_interpreter, worker_source_root, maximum_parallel_tasks=None, execute=True,
            repair_id=None, read_access=None):
        """Explicit selective recovery, preserving the frozen scientific worker.

        This is the owner behind ``experiment-recover --repair-retained-e3``.
        A new controller can repair only a known failed PURE retained adoption.
        Existing successful receipts and never-entered dependencies are derived
        from primary custody. A matching controller resumes its existing wave;
        it does not obtain another attempt by repeating the command.
        """
        from .results import ResumeCampaignRequest
        from .current_task_custody import current_issued_task_control_scope
        from .recursive_authoring import implementation_binding
        from .retained_e3_control_repair import (
            derive_retained_e3_control_repair, publish_retained_e3_control_repair,
            retained_e3_control_repair,
        )
        from .retained_e3_repair_continuation import (
            derive_repair_continuation, publish_repair_continuation, selected_controller,
        )
        from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
        from empirical_lawhood.runtime.retained_e3_repair import (
            RetainedE3RepairRecoveryIndex, RetainedE3ContinuedRepairRecoveryIndex,
        )
        if (type(request) is not ResumeCampaignRequest or request.confirmed is not True
                or request.reconcile_only or type(execute) is not bool):
            raise ValueError('retained E3 repair requires an explicit run and --yes')
        workers = self._selected_workers(maximum_parallel_tasks)
        selected, api = self._prospective_context(directory, maximum_parallel_tasks=workers,
            reveal_authority_id=request.reveal_authority_id, lifecycle='recover',
            recovery_run_id=request.run_id, read_access=read_access)
        execution = api._execution_service
        with current_issued_task_control_scope(api):
            plan = execution._load_status_execution_plan(request.run_id)
            contacts = ExternalNativeEffectContactStore(plane=execution.artifact_plane,
                execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)
            with contacts.execution_lock(request.run_id):
                package = execution._load_package(request.run_id)
                _, index, _ = execution._load_status_index(request.run_id, package=package)
                controller = implementation_binding(execution.repo_root)
                selected_id = repair_id or ('repair.retained-e3.' + controller.fingerprint()[:20]
                    + '.' + index.fingerprint()[:20])
                if not isinstance(index, RetainedE3RepairRecoveryIndex):
                    proof, index, envelope = derive_retained_e3_control_repair(service=execution,
                        run_id=request.run_id, repair_id=selected_id,
                        owner_instruction_sha256=owner_instruction_sha256,
                        worker_interpreter=worker_interpreter, worker_source_root=worker_source_root,
                        reveal_authority_id=request.reveal_authority_id)
                    publish_retained_e3_control_repair(service=execution, repair=proof, index=index,
                        original_envelope=envelope)
                else:
                    original = index.repair
                    if (original.owner_instruction_sha256 != owner_instruction_sha256
                            or original.worker_environment.interpreter_path != str(worker_interpreter)
                            or original.worker_source_root != str(worker_source_root)):
                        raise PermissionError('retained E3 repair substitutes its frozen worker or owner instruction')
                    if selected_controller(execution.artifact_plane, index) != controller:
                        proof, index = derive_repair_continuation(service=execution, run_id=request.run_id,
                            repair_id=selected_id, owner_instruction_sha256=owner_instruction_sha256,
                            reveal_authority_id=request.reveal_authority_id)
                        publish_repair_continuation(service=execution, proof=proof, index=index)
            with retained_e3_control_repair(execution, run_id=request.run_id) as index:
                original = index.repair
                proof = (index.repair_continuation
                    if type(index) is RetainedE3ContinuedRepairRecoveryIndex else original)
                if repair_id is not None and proof.repair_id != repair_id:
                    raise PermissionError('retained E3 repair substitutes its explicit recovery identity')
                if not execute:
                    return {'repair': proof.identity.to_document(), 'recovery_index':
                        ObjectIdentity.from_record(index.recovery_index_id, index).to_document(),
                        'reused_task_count': len(index.completed_receipts), 'pure_retry_count': 1,
                        'first_execution_task_count': len(index.unstarted_task_ids), 'new_native_contact_count': 0}
                result = api.resume_campaign(request, expected_candidate=selected.association.candidate)
                return self._prospective_report(result, selected)

    def read_execution(self, *, directory, request=None, reveal_authority_id=None, read_access=None,
            expected_specification_bytes=None, programme_request_path=None):
        """Inspect authenticated execution records without a scientific report."""
        from .experiment_execution_read import read_development_execution, read_prospective_execution
        composite = self._composite_programme(directory=directory)
        if composite is not None:
            if request is not None or reveal_authority_id is not None or read_access is not None or expected_specification_bytes is not None:
                raise ValueError('composite execution inspection requires its owning programme selection')
            owner = getattr(composite, 'read_execution', None)
            if not callable(owner):
                raise ValueError('selected composite has no execution-record reader')
            return owner(directory=directory, programme_request_path=programme_request_path)
        if programme_request_path is not None:
            raise ValueError('programme request requires a retained composite')
        if request is not None or self._is_prospective(directory):
            from .results import CampaignStatusRequest
            if type(request) is not CampaignStatusRequest or expected_specification_bytes is not None:
                raise TypeError('issued execution inspection requires its actual campaign status request')
            selected, _ = self._prospective_context(directory, lifecycle='read', read_access=read_access)
            return read_prospective_execution(selected=selected, artifact_writer=self.artifact_writer,
                run_id=request.run_id, reveal_authority_id=reveal_authority_id)
        if reveal_authority_id is not None:
            raise ValueError('development execution inspection cannot select an issued reveal')
        return read_development_execution(directory=directory, artifact_writer=self.artifact_writer,
            expected_specification_bytes=expected_specification_bytes, read_access=read_access)

    def read(self, *, directory, allow_partial=False, decision_directories=(), request=None, reveal_authority_id=None,
            programme_request_path=None, assess_incomplete=False, read_access=None,
            expected_specification_bytes=None, allow_unexecuted=False):
        """Read complete phases and products through the current custody owners.

        Partial reads keep typed scientific assessment explicitly deferred. A
        committed decision must name this exact retained wave before its next
        step can appear in the programme readout. A selected ACT remains subject
        to the successor's execution, input, issue and reveal requirements.
        Each owning reader retains its targeted verification lifetime; unrelated
        publication batches do not accumulate in one mutable snapshot here.
        """
        from .recursive_execution import read_recursive_wave
        from empirical_lawhood.api.recursive_inquiry import read_inquiry_decision

        if type(allow_partial) is not bool:
            raise TypeError("programme inspection requires an explicit partial-custody selection")
        if type(allow_unexecuted) is not bool:
            raise TypeError("authored-only inspection requires an explicit unexecuted selection")
        if expected_specification_bytes is not None and type(expected_specification_bytes) is not bytes:
            raise TypeError("selected development specification must have exact canonical bytes")
        if type(assess_incomplete) is not bool or allow_partial and assess_incomplete:
            raise ValueError("incomplete scientific assessment requires an explicit selection distinct from partial inspection")
        composite = self._composite_programme(directory=directory)
        if ((allow_unexecuted or expected_specification_bytes is not None)
                and (composite is not None or request is not None or self._is_prospective(directory))):
            raise ValueError("development read constraints require an ordinary development package")
        if composite is not None:
            if assess_incomplete:
                raise ValueError("incomplete scientific assessment requires one supported issued campaign")
            if request is not None or decision_directories or reveal_authority_id is not None or read_access is not None:
                raise ValueError("Composite programme read refuses single-campaign and inquiry options")
            return composite.read(directory=directory, allow_partial=allow_partial,
                programme_request_path=programme_request_path)
        if programme_request_path is not None:
            raise ValueError("Composite read selection requires a registered retained programme")
        if request is not None or self._is_prospective(directory):
            from empirical_lawhood.api.results import CampaignStatusRequest

            if type(request) is not CampaignStatusRequest or decision_directories:
                raise TypeError("prospective programme read requires its existing typed campaign status request")
            from .experiment_scientific_read import read_prepared_experiment_science

            selected, api = self._prospective_context(directory, lifecycle="read", read_access=read_access)
            result = api.campaign_status(request, expected_candidate=selected.association.candidate)
            report = self._prospective_report(result, selected)
            if result.succeeded or assess_incomplete:
                report["scientific_result"] = read_prepared_experiment_science(selected=selected,
                    artifact_writer=self.artifact_writer, run_id=request.run_id,
                    reveal_authority_id=reveal_authority_id, allow_partial=allow_partial, assess_incomplete=assess_incomplete,
                    **({} if read_access is None else {"read_access": read_access}))
            return report
        if assess_incomplete:
            raise ValueError("incomplete scientific assessment requires one supported issued campaign")
        if reveal_authority_id is not None:
            raise ValueError("development programme read does not accept issued reveal authority")
        writer = self.artifact_writer
        report, _, draft, plan = read_recursive_wave(directory=directory, artifact_writer=writer,
            include_products=True, allow_partial=allow_partial,
            terminal_product_format="compact" if allow_partial else "documents",
            expected_specification_bytes=expected_specification_bytes, allow_unexecuted=allow_unexecuted,
            **({} if read_access is None else {"read_access": read_access}))
        partial_read = allow_partial or (allow_unexecuted and report.get("terminal_product_format") == "compact")
        root = Path(writer.root.contract.canonical_path)
        relative = Path(directory).resolve(strict=True).relative_to(root).as_posix()
        decisions = []
        seen = set()
        for selected in decision_directories:
            packet, records = read_inquiry_decision(directory=selected, artifact_writer=writer)
            if packet.fingerprint() in seen:
                raise ValueError("programme readout repeats one committed decision")
            seen.add(packet.fingerprint())
            if not any(source.relative_path == relative and source.include_products
                       and source.packet.object_fingerprint == report["packet_sha256"]
                       for source in records["sources.json"].waves):
                raise ValueError("programme decision does not bind this exact completed retained wave")
            decision = records["decision.json"]
            alternative = next(row for row in records["menu.json"].alternatives
                               if row.alternative_id == decision.selected_alternative_id)
            decisions.append({"packet": ObjectIdentity.from_record(packet.packet_id, packet).to_document(),
                              "decision": decision.to_document(), "selected_action": alternative.action.value,
                              "intent": records["intent.json"].to_document() if "intent.json" in records else None})
        scientific_root = draft.development_study
        if scientific_root is None:
            raise ValueError("development programme readout lacks its actual scientific root")
        return {**report, "programme": {
            "scientific_root": ObjectIdentity.from_record(scientific_root.study_id, scientific_root).to_document(),
            "campaign": ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign).to_document(),
            "phases": _phase_progress(report, plan),
            "decisions": tuple(decisions),
            "next_step": "INSPECT_RETAINED_CONTACT_AND_RECOVERY" if partial_read
                         else "COMMITTED_INQUIRY_DECISION" if decisions else "ASSESS_PRODUCTS_AND_DECLARE_NEXT_INQUIRY",
        }}

    def decide(self, *, request, output_dir):
        """Commit the declared current policy through its existing authority owner."""
        from empirical_lawhood.api.recursive_inquiry import commit_inquiry_decision
        from empirical_lawhood.runtime.recursive_inquiry import InquiryDecisionRequest, WorkBoundInquiryDecisionRequest

        if type(request) not in (InquiryDecisionRequest, WorkBoundInquiryDecisionRequest):
            raise TypeError("programme decision requires its current typed inquiry request")
        request.__post_init__()
        arguments = {name: getattr(request, name) for name in
                     ("specification", "state", "sources", "menu", "policy", "campaign", "right", "actor_id", "human_choice")}
        if hasattr(request, "human_reason"):
            arguments["human_reason"] = request.human_reason
        return commit_inquiry_decision(**arguments, project_root=self.project_root,
                                       artifact_writer=self.artifact_writer, output_dir=output_dir)

    def advance(self, *, decision_directory, supplier_directory, origins, output_dir, input_bindings=()):
        """Derive a successor through its installed domain builder and admission."""
        from empirical_lawhood.api.recursive_inquiry import author_inquiry_successor

        return author_inquiry_successor(decision_directory=decision_directory, origins=origins,
            supplier_directory=supplier_directory, project_root=self.project_root,
            artifact_writer=self.artifact_writer, output_dir=output_dir, input_bindings=input_bindings)
