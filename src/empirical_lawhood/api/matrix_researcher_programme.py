# SPDX-License-Identifier: MPL-2.0
"""One current Matrix runner over C, actual products and ordinary lifecycles."""
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import (
    METADATA_PHASES, PHASES, MatrixProgrammeObservation, programme_frontier,
)
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    PREPARATION_CONTEXT, MatrixProgrammeOperationSelection, MatrixProgrammePhaseBinding,
    MatrixProgrammeRunBinding, MatrixResearchProgrammePlan, MatrixResearchProgrammeSpecification,
    MatrixContinuedProgrammeSpecification, MatrixCurveAmendedProgrammeSpecification, programme_protocol,
)
from empirical_lawhood.api.experiment_preparation import (
    _protocol, load_experiment_inputs, prepare_experiment,
)
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite, MatrixProgrammeProjectionContext
from empirical_lawhood.api.matrix_researcher_programme_lineage import read_published_record, run_binding_relative
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult
from empirical_lawhood.runtime.experiment_programme import PROGRAMME_DESCRIPTOR_FILENAME, ExperimentProgrammeDescriptor
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled

PLAN_FILENAME = 'matrix-programme.json'
MAX_SELECTION_BYTES = 64 * 1024**2


def _relative(writer, path, *, writing=False):
    path = Path(path)
    if (not path.is_absolute() or path != path.resolve(strict=False)
            or any(value.is_symlink() for value in (path, *path.parents))):
        raise ValueError('Matrix programme requires its actual guarded canonical path')
    relative = path.relative_to(writer.root.contract.canonical_path).as_posix()
    writer.root.resolve(relative, for_write=writing)
    return relative


def _publish(writer, path, record):
    relative = _relative(writer, path, writing=True)
    pin = getattr(record, 'identity', None)
    logical = pin.object_id if pin is not None else record.selection_id
    return writer.write(ArtifactWriteRequest(logical, relative, record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'matrix-programme',
        Path(relative).parent.as_posix(), record.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))


def _phase_complete(phase, report):
    """Owner completion is independent of a favourable scientific outcome."""
    if report.get('read_scope') == 'EXECUTION_RECORDS':
        return False
    if report.get('state') in ('UNENTERED_REVISION_NOT_TRIGGERED', 'UNENTERED_REVISION_UNEVALUABLE',
            'UNENTERED_REVISION_FIT_UNAVAILABLE', 'UNENTERED_REQUIRED_SR_BR_FIT_UNAVAILABLE'):
        return False  # Conditional nonentry comes from the original DEV decision.
    science = report.get('scientific_result')
    if phase in METADATA_PHASES:
        return report.get('state') == 'INPUTS_DERIVED'
    if phase in ('e4.calibration', 'e4.confirmation'):
        assessment = report.get('assessment')
        return (report.get('scientific_completion') == 'ASSESSMENT_RETAINED'
            and report.get('all_wave_terminals_present') is True and isinstance(assessment, dict)
            and assessment.get('status') == 'SUCCEEDED' and assessment.get('scientific_result') is not None
            and isinstance(report.get('structure'), dict)
            and report['structure'].get('scientific_completion') == 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS')
    if report.get('status') != 'SUCCEEDED':
        return False
    if phase == 'e4.development':
        structure = (science if isinstance(science, dict) else report).get('structure')
        return isinstance(structure, dict) and structure.get('scientific_completion') == 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS'
    expected = {'e2': 'COMPLETE_NATIVE_UTILITY_ASSESSMENT', 'train': 'COMPLETE_NATIVE_TRAIN_ARRAY_REPLAY',
        'e3': 'RETAINED_ADJUDICATION', 'e5.development': 'COMPLETE_ASSIGNED_E5_DEVELOPMENT_CENSUS',
        'e4.source-cal': 'COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT',
        'e4.source-conf': 'COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT', 'e5.source': 'COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT',
        'e6.source': 'COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT', 'e5.confirmation': 'RETAINED_ADJUDICATION',
        'e6': 'RETAINED_ADJUDICATION'}.get(phase)
    return expected is None or isinstance(science, dict) and science.get('scientific_completion') == expected

def _reported_count(value):
    """Only owner-reported counts or explicit memberships establish a count."""
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, (tuple, list)) and all(isinstance(item, str) for item in value):
        return len(value)
    return None


def _disposition_denominators(report):
    """Keep independent scopes separate; resolved inputs are not usable outcomes."""
    rows = []
    science = report.get("scientific_result")
    if isinstance(science, dict) and isinstance(science.get("denominators"), dict):
        for scope, values in science["denominators"].items():
            if not isinstance(values, dict):
                continue
            assigned = _reported_count(values.get("assigned_units"))
            successful = _reported_count(values.get("successes"))
            rows.append({"scope": scope, "source": "scientific_result.denominators." + scope,
                "assigned": assigned, "usable": _reported_count(values.get("usable_units")),
                "successful": successful, "adverse": _reported_count(values.get("adverse_units")),
                "unsuccessful": (assigned - successful if assigned is not None
                    and successful is not None and successful <= assigned else None),
                "unevaluable": _reported_count(values.get("unevaluable_units")),
                "unentered": _reported_count(values.get("unentered_units"))})
    result = report.get("result")
    if isinstance(result, dict) and "requested_histories" in result:
        rows.append({"scope": "descriptive-histories", "source": "result",
            "assigned": _reported_count(result.get("requested_histories")),
            "completed": _reported_count(result.get("completed_histories")),
            "usable": None, "successful": None, "adverse": None, "unsuccessful": None,
            "unevaluable": _reported_count(result.get("unevaluable_histories")),
            "unentered": _reported_count(result.get("unentered_histories"))})
    containers = [("", report)]
    if isinstance(science, dict):
        containers.append(("scientific_result.", science))
        if isinstance(science.get("structure"), dict):
            containers.append(("scientific_result.structure.", science["structure"]))
    for prefix, container in containers:
        for scope, keys in (("independent-groups", ("assigned_group_count", "assigned_groups")),
                ("cases", ("assigned_case_count", "assigned_cases")),
                ("independent-units", ("assigned_unit_ids", "assigned_roots"))):
            key = next((value for value in keys if value in container), None)
            if key is not None:
                rows.append({"scope": scope, "source": prefix + key, "assigned": _reported_count(container[key]),
                    "usable": None, "successful": None, "adverse": None, "unsuccessful": None,
                    "unevaluable": None, "unentered": None})
    return tuple(rows)


def _disposition_facts(report):
    """Copy exact owner dispositions without interpreting operational success."""
    fields = ("state", "status", "operational_status", "scientific_status", "admission_status",
        "scientific_completion", "scientific_disposition", "scientific_standing", "uncertainty_status",
        "scientific_qualification", "qualification", "evaluability", "disposition", "nomination_disposition", "evidence_role",
        "conditional_criterion_met", "source_premise", "sampling", "transport", "reason_codes",
        "calibration_radius_kind", "observation_status", "all_wave_terminals_present",
        "status_source", "recovery_terminal_event_relative_path")
    owners = [("report", report)]
    for name in ("scientific_result", "result", "payload", "assessment"):
        value = report.get(name)
        if isinstance(value, dict):
            owners.append((name, value))
            if isinstance(value.get("scientific_result"), dict):
                owners.append((name + ".scientific_result", value["scientific_result"]))
    for name in ("reduction", "qualification_result"):
        record = report.get(name)
        if isinstance(record, dict) and isinstance(record.get("value"), dict):
            owners.append((name + ".value", record["value"]))
    science = report.get("scientific_result")
    if isinstance(science, dict):
        record = science.get("qualification_result")
        if isinstance(record, dict) and isinstance(record.get("value"), dict):
            owners.append(("scientific_result.qualification_result.value", record["value"]))
    return tuple({"source": source, "values": {key: value[key] for key in fields if key in value}}
        for source, value in owners if any(key in value for key in fields))



class MatrixResearchProgrammeService:
    def __init__(self, *, service, descriptor=None):
        self.service, self.writer, self.descriptor = service, service.artifact_writer, descriptor

    def _home(self, plan):
        return self.writer.root.resolve(plan.specification.directory, for_write=False)

    def _plan(self, directory):
        relative = _relative(self.writer, Path(directory) / PLAN_FILENAME)
        plan = read_published_record(self.writer, relative, MatrixResearchProgrammePlan, MAX_SELECTION_BYTES)
        expected = ExperimentProgrammeDescriptor('descriptor.' + plan.fingerprint(), programme_protocol(plan.specification),
            plan.specification.identity, plan.identity)
        if (self.descriptor != expected or Path(directory) != self._home(plan)
                or plan.output_root != self.writer.root.contract.canonical_path):
            raise PermissionError('Matrix programme changes its original descriptor/home/output root')
        return plan

    @contextmanager
    def _read_context(self, plan, *, operation=None):
        """Keep predecessor custody shared through the complete read chain.

        Each predecessor still authenticates its own selected records and live
        access. Propagate the scoped service so nested owners reuse the same
        byte proof. The outer scope owns the complete final snapshot check.
        Execution continues to use its separate ordinary context.
        """
        from .selected_e3_access import original_e3_authority_read_context
        from .retained_e3_evidence import retained_e3_reader
        with original_e3_authority_read_context(self.writer), retained_e3_reader(self.writer).read_context() as writer:
            service = replace(self.service, artifact_writer=writer)
            owner = type(self)(service=service, descriptor=self.descriptor)
            with owner._context(plan, operation=operation) as context:
                yield context

    @contextmanager
    def _context(self, plan, *, operation=None):
        if plan.output_root != self.writer.root.contract.canonical_path:
            raise PermissionError('Matrix programme substitutes its selected artifact root')
        from .retained_e3_evidence import retained_e3_evidence_context, retained_e3_reader
        evidence = nullcontext() if scientific_reconstruction_enabled() else retained_e3_evidence_context(self.writer)
        input_reader = authenticated_programme_inputs
        if not scientific_reconstruction_enabled():
            from empirical_lawhood.infrastructure.matrix_recorded_inputs import recorded_programme_inputs
            input_reader = recorded_programme_inputs
        with evidence, input_reader(writer=retained_e3_reader(self.writer), commitment=plan.specification.input_commitments,
                maximum_source_bytes=plan.specification.operations.metadata_budget.source_scan_bytes) as inputs, ExitStack() as lifetime:
            from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import require_computability_scope
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity
            nominal_pin = dict(inputs.scientific_design.e3.role_coordinates)['CALIBRATION']
            nominal, = (coordinate for coordinate in inputs.scientific_design.training_protocol.coordinates
                if coordinate_identity(coordinate) == nominal_pin)
            e3 = plan.specification.operations.e3
            require_computability_scope(e3.computability_envelope, e3.computability_evidence, nominal)
            context = MatrixProgrammeProjectionContext(self.service, plan, inputs, self._home(plan), {}, {}, operation,
                _read_lifetime=lifetime)
            self._load_bindings(context)
            from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import (
                CONTINUATION_FILENAME,
            )
            continuation_path = context.directory / CONTINUATION_FILENAME
            present = continuation_path.exists() or continuation_path.is_symlink()
            from empirical_lawhood.adapters.methods.matrix_researcher_programme import retained_training_continuation as retained_domain
            retained_path = context.directory / retained_domain.CONTINUATION_FILENAME
            retained_present = retained_path.exists() or retained_path.is_symlink()
            retained_selected = (type(plan.specification) is MatrixContinuedProgrammeSpecification
                and plan.specification.continuation_request.object_schema
                    == retained_domain.MatrixProgrammeRetainedTrainingContinuationSpecification.SCHEMA)
            from empirical_lawhood.adapters.methods.matrix_researcher_programme import retained_e3_continuation as e3_domain
            from empirical_lawhood.adapters.methods.matrix_researcher_programme import e3_closeout as e3_closeout_domain
            e3_path = context.directory / e3_domain.CONTINUATION_FILENAME
            e3_present = e3_path.exists() or e3_path.is_symlink()
            e3_selected = (type(plan.specification) is MatrixContinuedProgrammeSpecification
                and plan.specification.continuation_request.object_schema
                    in (e3_domain.MatrixProgrammeRetainedE3ContinuationSpecification.SCHEMA,
                        e3_closeout_domain.MatrixProgrammeE3CloseoutSpecification.SCHEMA))
            if type(plan.specification) is MatrixContinuedProgrammeSpecification:
                if e3_selected:
                    if not e3_present or present or retained_present:
                        raise PermissionError('continued programme requires its exact retained E3 continuation publication')
                    relative = _relative(self.writer, e3_path)
                    schema = self.writer.read_manifest(relative).logical.payload_schema
                    kinds = {kind.SCHEMA: kind for kind in (e3_domain.MatrixProgrammeRetainedE3Continuation,
                        e3_domain.MatrixProgrammeUnfinishedE3Continuation, e3_closeout_domain.MatrixProgrammeClosedE3Continuation)}
                    if schema not in kinds:
                        raise PermissionError('continued programme changes its retained E3 record contract')
                    record = read_published_record(self.writer, relative, kinds[schema], MAX_SELECTION_BYTES)
                    from .matrix_programme_retained_e3_continuation import continued_context
                elif retained_selected:
                    if not retained_present or present:
                        raise PermissionError('continued programme requires its exact retained TRAIN continuation publication')
                    record = read_published_record(self.writer, _relative(self.writer, retained_path),
                        retained_domain.MatrixProgrammeRetainedTrainingContinuation, MAX_SELECTION_BYTES)
                    from .matrix_programme_retained_training_continuation import continued_context
                else:
                    if not present:
                        raise PermissionError('continued programme requires its exact original source-continuation publication')
                    from .matrix_programme_completed_continuation import read_source_continuation
                    record = read_source_continuation(self.writer, _relative(self.writer, continuation_path),
                        MAX_SELECTION_BYTES)
                    from .matrix_programme_source_continuation import continued_context
                if (not scientific_reconstruction_enabled()
                        and (not e3_selected or 'e3' in context.bindings)):
                    from .matrix_programme_recorded_lineage import recorded_continuation_context
                    continued_context = recorded_continuation_context
                lifetime.enter_context(continued_context(self, context, record))
            elif present:
                raise PermissionError('original programme cannot acquire an unselected source-continuation file')
            if retained_present and not retained_selected:
                raise PermissionError('programme cannot acquire an unselected retained TRAIN continuation file')
            if e3_present and not e3_selected:
                raise PermissionError('programme cannot acquire an unselected retained E3 continuation file')
            from empirical_lawhood.adapters.methods.matrix_researcher_programme.curve_amendment import (
                AMENDMENT_FILENAME, MatrixProgrammeCurveAmendment,
            )
            amendment_path = context.directory / AMENDMENT_FILENAME
            present = amendment_path.exists() or amendment_path.is_symlink()
            if type(plan.specification) is MatrixCurveAmendedProgrammeSpecification:
                if not present:
                    raise PermissionError('amended programme requires its exact prospective curve-amendment publication')
                record = read_published_record(self.writer, _relative(self.writer, amendment_path),
                    MatrixProgrammeCurveAmendment, MAX_SELECTION_BYTES)
                from .matrix_programme_curve_amendment import amended_context
                if not scientific_reconstruction_enabled():
                    from .matrix_programme_recorded_lineage import recorded_continuation_context
                    amended_context = recorded_continuation_context
                lifetime.enter_context(amended_context(self, context, record))
            elif present:
                raise PermissionError('programme cannot acquire an unselected prospective amendment file')
            yield context

    @staticmethod
    def _require_preparation(preparation):
        from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation
        if type(preparation) is not ExperimentPreparation:
            raise TypeError('Matrix preparation requires its exact typed preparation')
        preparation.__post_init__()
        if (type(preparation.specification_record) not in (MatrixResearchProgrammeSpecification, MatrixContinuedProgrammeSpecification,
                MatrixCurveAmendedProgrammeSpecification)
                or preparation.specification != preparation.specification_record.identity):
            raise TypeError('Matrix preparation requires its exact current C-pinned specification')

    @staticmethod
    def _refine_context(preparation, context):
        workers = context.plan.workers
        if (context.plan != preparation.programme
                or context.plan.specification.operations.e1.resources.maximum_parallel_tasks != workers
                or context.plan.specification.operations.e2.resources.maximum_parallel_tasks != workers
                or context.plan.specification.operations.training.resources.maximum_parallel_tasks != workers):
            raise ValueError('Matrix programme changes explicit child concurrency selections')
        return replace(preparation, dependencies=tuple(row for row in preparation.dependencies if row.code != PREPARATION_CONTEXT))

    def refine_preparation(self, preparation):
        self._require_preparation(preparation)
        if self.service.storage_profile is None or self.writer is None or preparation.programme is None:
            return preparation
        with self._context(preparation.programme) as context:
            return self._refine_context(preparation, context)

    def _load_bindings(self, context):
        from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
        for phase in PHASES:
            relative = (context.directory / 'bindings' / (phase + '.json')).relative_to(
                self.writer.root.contract.canonical_path).as_posix()
            path = self.writer.root.resolve(relative, for_write=False)
            if path.exists() or path.is_symlink():
                # Uncommitted bytes cannot establish a phase binding. A normal
                # advancing call independently rederives the expected record;
                # the writer alone may complete its exact original intent.
                # Read-only inspection reports this obstruction without repair.
                try:
                    self.writer.read_manifest(relative)
                except (FileNotFoundError, ArtifactIdentityConflict) as error:
                    context.pending_bindings[phase] = str(error)
                    continue
                binding = read_published_record(self.writer, relative, MatrixProgrammePhaseBinding, MAX_SELECTION_BYTES)
                if binding.phase != phase or binding.programme != context.plan.identity:
                    raise PermissionError('Matrix phase binding changes its exact original programme/phase')
                context.bindings[phase] = binding

    def _retain_binding(self, context, phase, result):
        if type(result) is not ExperimentInputDerivationResult or result.target_specification is None:
            raise TypeError('Matrix projector must return the actual ordinary typed target derivation')
        result.__post_init__()
        target = result.target_specification
        specification = ExperimentInputBinding('specification', target.identity,
            _relative(self.writer, result.target_specification_path), len(target.canonical_bytes()))
        selector = result.source_selection
        sources = ExperimentInputBinding('sources', ObjectIdentity.from_record(selector.selection_id, selector),
            _relative(self.writer, result.source_selection_path), len(selector.canonical_bytes()))
        from empirical_lawhood.infrastructure.publication_metadata import consume_published_materializations
        with self._phase_scope(context, phase):
            def reconstruct(members):
                # The closed-roster owner checks every exact handle, sidecar,
                # complete sibling set and commit before this callback. Reuse
                # those immutable handles; `created` is only a call result.
                publications = []
                for actual in result.publications:
                    manifest = members[actual.materialization.relative_path]
                    if (manifest.logical, manifest.materialization) != (actual.logical, actual.materialization):
                        raise PermissionError('Matrix derivation changes its actual published custody')
                    publications.append(replace(actual, created=False))
                requirements, = (row for row in publications
                    if row.materialization.relative_path == result.requirements_publication.materialization.relative_path)
                return MatrixProgrammePhaseBinding('binding.' + context.plan.fingerprint() + '.' + phase,
                    context.plan.identity, phase, _protocol(target).protocol_id, specification, sources,
                    requirements, tuple(publications))

            # The final complete byte/access guard surrounds reconstruction
            # and finishes before the binding's immutable publication effect.
            binding = consume_published_materializations(self.writer, result.publications, consume=reconstruct)
            _publish(self.writer, context.directory / 'bindings' / (phase + '.json'), binding)
        context.bindings[phase] = binding
        context.pending_bindings.pop(phase, None)
        if phase in ('e2', 'train', 'e3') and hasattr(context, 'prepared_inputs'):
            context.prepared_inputs[phase] = binding.identity, result.preparation
        return binding

    def _request(self, plan, path):
        if path is None:
            return None
        raw = read_bounded_bytes(Path(path), maximum_bytes=MAX_SELECTION_BYTES)
        request = decode_canonical_bytes(raw, MatrixProgrammeOperationSelection, maximum_bytes=MAX_SELECTION_BYTES)
        if request.canonical_bytes() != raw or request.programme != plan.identity:
            raise PermissionError('Matrix operation changes its exact original programme')
        return request

    @contextmanager
    def _phase_scope(self, context, phase):
        # Protected model-bearing derived records are decoded only while the
        # actual original reader holds current reveal and complete custody.
        if phase.startswith(('e4.', 'e5.', 'e6')) and phase in context.bindings and not scientific_reconstruction_enabled():
            from .selected_e3_access import original_e3_authority_read_context
            # Authored/input readers own fresh original access before protected
            # bytes. Scheduling does not reopen the E3 numerical read.
            scope = original_e3_authority_read_context(self.writer)
        else:
            scope = context.e3_originals() if phase.startswith(('e4.', 'e5.', 'e6')) else nullcontext()
        with scope:
            yield

    def _authored(self, context, phase, specification):
        directory = context.child_directory(phase)
        descriptor = directory / PROGRAMME_DESCRIPTOR_FILENAME
        if descriptor.exists() or descriptor.is_symlink():
            _relative(self.writer, descriptor)
            raw = read_bounded_bytes(descriptor, maximum_bytes=64 * 1024)
            value = decode_canonical_bytes(raw, ExperimentProgrammeDescriptor, maximum_bytes=64 * 1024)
            expected_specification, expected_protocol = specification.identity, _protocol(specification).protocol_id
            if phase in ('e4.calibration', 'e4.confirmation'):
                # The ordinary declarative author authenticates copied intent
                # and hands off once to the existing native E4 lifecycle.
                from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_declarative as declarative
                from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_preparation import PROGRAMME_PROTOCOL_ID
                if type(specification) is not declarative.SelectedE4DeclarativeSpecification:
                    raise TypeError('programme protected E4 requires its exact current declarative specification')
                actual = context.method_inputs(phase)
                declarative.validate_plan(specification, actual)
                expected_specification, expected_protocol = actual.plan.specification.identity, PROGRAMME_PROTOCOL_ID
            if (raw != value.canonical_bytes() or value.specification != expected_specification
                    or value.protocol_id != expected_protocol):
                raise PermissionError('Matrix child changes its actual original selected programme')
            return True
        if self.service._is_prospective(directory):
            from empirical_lawhood.api.prospective_experiment import load_retained_prospective_experiment
            selected = load_retained_prospective_experiment(directory=directory, project_root=self.service.project_root,
                storage_profile=self.service.storage_profile, artifact_writer=self.writer)
            if selected.instance.specification != specification.identity:
                raise PermissionError('Matrix child changes its actual original prospective specification')
            return True
        packet = directory / 'authored-wave.json'
        if packet.exists() or packet.is_symlink():
            from empirical_lawhood.api.recursive_authoring import load_authored_wave
            _, _, _, payloads = load_authored_wave(directory=directory, artifact_writer=self.writer, lazy_payloads=True)
            if payloads.get('experiment-specification.json') != specification.canonical_bytes():
                raise PermissionError('Matrix child changes its actual original development specification')
            return True
        return False

    def _read_phase(self, context, phase, *, allow_partial=False, execution_only=False, observe_controls=None):
        if execution_only:
            from .matrix_programme_recorded_lineage import phase_execution
            return phase_execution(context, phase, observe_controls=observe_controls)
        with self._phase_scope(context, phase):
            _, specification = context.bound_specification(context.binding(phase))
            inputs = load_experiment_inputs(specification, self.writer.root.resolve(
                context.binding(phase).sources.relative_path, for_write=False), artifact_writer=self.writer)
            from empirical_lawhood.api.matrix_researcher_programme_prepared_lineage import require_current_account
            require_current_account(context, phase, specification, inputs.method_inputs)
            if phase in METADATA_PHASES:
                preparation = self.service.prepare(specification, scientific_inputs=inputs.scientific_inputs,
                    method_inputs=inputs.method_inputs, execution=context.execution)
                return {'state': 'INPUTS_DERIVED' if not preparation.dependencies else 'DEPENDENCIES_REQUIRED',
                    'dependencies': tuple({'code': row.code, 'detail': row.detail} for row in preparation.dependencies),
                    'scientific_completion': 'NOT_APPLICABLE', 'new_native_contact_count': 0}
            declaration = _protocol(specification)
            if phase not in ('e4.calibration', 'e4.confirmation') and not declaration.requires_prospective_runtime_binding:
                child = self.service._composite_programme(directory=context.child_directory(phase))
                if child is not None:
                    if child.descriptor.specification != specification.identity:
                        raise PermissionError('programme read changes its actual composite specification')
                    return child.read(directory=context.child_directory(phase), allow_partial=allow_partial)
                packet = context.child_directory(phase) / 'authored-wave.json'
                if not packet.exists() and not packet.is_symlink():
                    return {'state': 'AUTHORING_REQUIRED', 'new_native_contact_count': 0}
                # The ordinary reader authenticates the expected specification,
                # retained plan and pending/full custody in its one packet load.
                return self.service.read(directory=context.child_directory(phase), allow_partial=allow_partial,
                    expected_specification_bytes=specification.canonical_bytes(), allow_unexecuted=True)
            if not self._authored(context, phase, specification):
                return {'state': 'AUTHORING_REQUIRED', 'new_native_contact_count': 0}
            if phase in ('e4.calibration', 'e4.confirmation'):
                from empirical_lawhood.api.matrix_programme_e4_phases import programme_e4_request
                directory = context.child_directory(phase)
                child = self.service._composite_programme(directory=directory)
                request = programme_e4_request(context, phase)
                plan = inputs.method_inputs.plan
                selected = {value.component_id for value in request.components}
                missing = tuple(value for value in plan.component_ids if value not in selected)
                analysis = self.writer.root.resolve(_relative(self.writer, directory / 'structure' / 'analysis'),
                    for_write=False)
                # Authored/issued waves have no future result to read yet.
                # Existing structure custody still reaches the full reader;
                # malformed bytes or a revoked current reveal are not absence.
                unfinished = (any(wave.wave_id not in selected for wave in plan.declaration.programme.waves)
                    or not analysis.exists())
                report = child.read(directory=directory, allow_partial=allow_partial or unfinished, request=request)
                return {**report, 'missing_components': missing} if unfinished else report
            if declaration.requires_prospective_runtime_binding:
                from empirical_lawhood.api.results import CampaignStatusRequest
                selected, api, authority, package, run, _ = context.authority(phase)
                if phase == 'e3' and not allow_partial:
                    # Preserve the ordinary status envelope, but keep its full
                    # scientific read alive for the downstream original-product
                    # consumers in this same operation. A pending/failed status
                    # must not open a complete original-product reader.
                    status = api.campaign_status(CampaignStatusRequest(run.run_plan_id),
                        expected_candidate=selected.association.candidate)
                    report = self.service._prospective_report(status, selected)
                    if status.succeeded:
                        reading = context.original_e3_products(selected=selected, package=package,
                            run_id=run.run_plan_id, reveal_authority_id=authority.reveal_authority_id)
                        del selected, package
                        with reading as original:
                            report['scientific_result'] = dict(original.report)
                    return report
                return self.service.read(directory=context.child_directory(phase), allow_partial=allow_partial,
                    request=CampaignStatusRequest(run.run_plan_id), reveal_authority_id=authority.reveal_authority_id)

    def _observe(self, context, *, allow_partial=False, phases=PHASES, operational=False, reports=None):
        for phase in phases:
            if phase not in context.bindings:
                continue
            try:
                if reports is not None and phase in reports:
                    report = reports[phase]
                elif (operational and not scientific_reconstruction_enabled()
                        and phase in getattr(context, 'retained_execution_reports', {})):
                    report = context.retained_execution_reports[phase]
                else:
                    options = ({'execution_only': True}
                        if operational and not scientific_reconstruction_enabled() and phase not in METADATA_PHASES else {})
                    report = self._read_phase(context, phase, allow_partial=allow_partial, **options)
            except MatrixProgrammePrerequisite as error:
                report = {'state': 'DEPENDENCIES_REQUIRED', 'dependencies': ({'code': error.code, 'detail': error.detail},),
                    'new_native_contact_count': 0}
            complete = not allow_partial and _phase_complete(phase, report)
            execution_complete = (operational
                and report.get('read_scope') == 'EXECUTION_RECORDS' and report.get('execution_complete') is True)
            context.observations[phase] = MatrixProgrammeObservation(phase, report, complete,
                execution_complete=execution_complete)
            if phase == 'e4.revision' and (complete or execution_complete):
                from empirical_lawhood.api.matrix_researcher_programme_e4_lineage import programme_revision_products
                with self._phase_scope(context, phase):
                    _, _, decision = programme_revision_products(context)
                context.observations[phase] = replace(context.observations[phase], revision_trigger=decision.trigger_disposition)
            elif phase == 'e4.confirmation' and (complete or execution_complete) and context.design.downstream_account == 'REVISION':
                from empirical_lawhood.api.matrix_researcher_programme_e4_lineage import programme_downstream_choice
                with self._phase_scope(context, phase):
                    choice = programme_downstream_choice(context)
                context.observations[phase] = replace(context.observations[phase], downstream_choice=choice)
            elif phase == 'e5.development' and (complete or execution_complete):
                from empirical_lawhood.api.matrix_researcher_programme_prepared_lineage import programme_development_nomination
                with self._phase_scope(context, phase):
                    disposition = programme_development_nomination(context)
                context.observations[phase] = replace(context.observations[phase], nomination_disposition=disposition)

    def _project(self, context, phase):
        if phase in getattr(context, 'phase_origins', {}):
            raise PermissionError('continued E1/E2 phases retain their original producers and cannot be rederived')
        if phase in ('e1', 'e2', 'train', 'e3'):
            from empirical_lawhood.api.matrix_programme_initial_phases import project_initial_phase
            return project_initial_phase(context, phase)
        if phase.startswith('e4.'):
            from empirical_lawhood.api.matrix_programme_e4_phases import project_e4_phase
            return project_e4_phase(context, phase)
        from empirical_lawhood.api.matrix_programme_prepared_phases import project_prepared_phase
        return project_prepared_phase(context, phase)

    def _author_phase(self, context, phase, *, observe_authoring=False):
        if phase in getattr(context, 'phase_origins', {}):
            raise MatrixProgrammePrerequisite(phase, 'ORIGINAL_EXECUTION_CUSTODY_REQUIRED',
                'Continued E1/E2 phases must retain complete original execution; replacement authoring is forbidden.')
        with self._phase_scope(context, phase):
            observed = context.observations.get(phase)
            if (observed is not None and observed.report.get('read_scope') == 'EXECUTION_RECORDS'
                    and observed.report.get('status') in ('UNENTERED', 'INPUTS_PARTIAL', 'INCOMPLETE', 'SUCCEEDED', 'FAILED', 'BLOCKED')):
                # The live observation authenticated the actual frozen child.
                # Its execution owner loads that child once before dispatch.
                return False
            _, specification = context.bound_specification(context.binding(phase))
            if self._authored(context, phase, specification):
                return False
            previous = getattr(context, 'prepared_inputs', {}).get(phase)
            if previous is None:
                inputs = load_experiment_inputs(specification, self.writer.root.resolve(
                    context.binding(phase).sources.relative_path, for_write=False), artifact_writer=self.writer)
                preparation = self.service.prepare(specification, scientific_inputs=inputs.scientific_inputs,
                    method_inputs=inputs.method_inputs, execution=context.execution)
            else:
                binding_identity, preparation = previous
                if (binding_identity != context.binding(phase).identity
                        or preparation.specification_record != specification
                        or preparation.execution != context.execution):
                    raise PermissionError('Matrix authoring changes its live derived input preparation')
            from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
            from empirical_lawhood.runtime.experiment_preparation import DependencyKind
            binding = experiment_runtime_binding(_protocol(specification))
            deferred = (preparation.programme is None and binding is not None
                and callable(binding.prepare_authoring) and bool(preparation.dependencies)
                and all(row.kind is DependencyKind.SOFTWARE for row in preparation.dependencies))
            if not preparation.executable and not deferred:
                raise MatrixProgrammePrerequisite(phase, 'ORDINARY_AUTHORING_PREREQUISITES_REQUIRED',
                    '; '.join(row.code + ': ' + row.detail for row in preparation.dependencies))
            if _protocol(specification).requires_prospective_runtime_binding:
                from .composite_experiment_programme import prepared_component_source_snapshot
                snapshot = prepared_component_source_snapshot(self.service.project_root, preparation)
                preparation = replace(preparation, execution=replace(preparation.execution, source_snapshot=snapshot))
            report = self.service.author(preparation=preparation, output_dir=context.child_directory(phase))
            if observe_authoring and phase in ('e2', 'train'):
                from .experiment_execution_read import observed_development_authoring
                context.authored_reports[phase] = context._read_lifetime.enter_context(
                    observed_development_authoring(directory=context.child_directory(phase),
                        artifact_writer=self.writer, authoring_report=report,
                        expected_specification_bytes=specification.canonical_bytes()))
            return True

    def _retain_run(self, context, phase, selected, authority, package, run, component_id=None):
        from empirical_lawhood.api.matrix_researcher_programme_lineage import retained_run_binding
        original = retained_run_binding(context, phase, component_id)
        if original is not None:
            if (original.specification != selected.instance.specification
                    or original.package != ObjectIdentity.from_record(package.package_id, package)
                    or original.run_id != run.run_plan_id):
                raise PermissionError('Matrix operation changes its actual immutable original run locator')
            # Replacement reveal is a current operation selection. It never
            # rewrites the original binding or becomes a new execution attempt.
            return original
        binding = MatrixProgrammeRunBinding('run.' + context.plan.fingerprint() + '.' + phase + '.' + (component_id or 'main'),
            context.plan.identity, phase, component_id or 'main', selected.instance.specification,
            ObjectIdentity.from_record(package.package_id, package), run.run_plan_id, authority)
        _publish(self.writer, self.writer.root.resolve(run_binding_relative(context, phase, component_id), for_write=True), binding)

    def _operate_phase(self, context, phase, *, recover, confirmed):
        if phase in getattr(context, 'phase_origins', {}):
            raise PermissionError('continued E1/E2 phases are read-only; replacement acquisition is forbidden')
        if not confirmed:
            raise MatrixProgrammePrerequisite(phase, 'WRITE_CONFIRMATION_REQUIRED',
                'Select --yes to execute or recover a Matrix programme phase. '
                'Unconfirmed advancement only derives and authors metadata.')
        with self._phase_scope(context, phase):
            _, specification = context.bound_specification(context.binding(phase))
            if phase in ('e4.calibration', 'e4.confirmation'):
                from empirical_lawhood.api.matrix_programme_e4_phases import programme_e4_request
                request = programme_e4_request(context, phase)
                for component in request.components:
                    selected, _, authority, package, run, _ = context.authority(phase, component.component_id)
                    self._retain_run(context, phase, selected, authority, package, run, component.component_id)
                child = self.service._composite_programme(directory=context.child_directory(phase))
                return (child.recover if recover else child.run)(directory=context.child_directory(phase),
                    maximum_parallel_tasks=context.plan.workers, confirmed=confirmed, request=request,
                    **({} if scientific_reconstruction_enabled() else {'result_read_scope':'EXECUTION_RECORDS'}))
            declaration = _protocol(specification)
            options = {'maximum_parallel_tasks': context.plan.workers}
            if declaration.requires_prospective_runtime_binding:
                from empirical_lawhood.api.results import ResumeCampaignRequest, RunCampaignRequest
                from empirical_lawhood.api.current_result_custody import current_result_package_present
                selected, _, authority, package, run, _ = context.authority(phase)
                self._retain_run(context, phase, selected, authority, package, run)
                paths = lambda path: None if path is None else self.writer.root.resolve(path, for_write=False)
                common = {'confirmed': confirmed, 'reveal_authority_id': authority.reveal_authority_id,
                    'parent_record_path': paths(authority.parent_record_path),
                    'parent_input_binding_paths': tuple(paths(path) for path in authority.parent_input_binding_paths)}
                retained = current_result_package_present(writer=self.writer, run_id=run.run_plan_id)
                ordinary = (ResumeCampaignRequest(run.run_plan_id, **common) if retained
                    else RunCampaignRequest(paths(authority.package_path), **common))
                options['request'] = ordinary
                operation = self.service.recover if retained else self.service.run
            else:
                operation = self.service.recover if recover else self.service.run
                if phase in ('e2', 'train') or not scientific_reconstruction_enabled():
                    options['result_read_scope'] = 'EXECUTION_RECORDS'
            return operation(directory=context.child_directory(phase), **options)

    def _report(self, context, *, dependencies=(), allow_partial=False, operational=False, structural_prediction=None):
        from .matrix_programme_structural_prediction import programme_structural_prediction
        frontier = programme_frontier(context.observations, downstream_account=context.design.downstream_account,
            operational=operational)
        from .matrix_programme_recorded_lineage import operational_report
        exhaustive = scientific_reconstruction_enabled()
        phases = tuple({'phase': phase, 'binding': context.bindings[phase].identity.to_document(),
            'producing_programme': context.phase_origins.get(phase, context).plan.identity.to_document(),
            'report': (dict(context.observations[phase].report) if exhaustive
                else operational_report(context.observations[phase].report)),
            'operational_completion': context.observations[phase].complete or context.observations[phase].execution_complete,
            'scientific_read_completed': context.observations[phase].complete,
            'denominators': _disposition_denominators(context.observations[phase].report),
            'scientific_dispositions': _disposition_facts(context.observations[phase].report)}
            for phase in PHASES if phase in context.observations)
        return {'programme': context.plan.identity.to_document(),
            'input_commitments': context.plan.specification.input_commitments.record.to_document(),
            'source_continuations': tuple((record.to_document() if exhaustive else record.identity.to_document())
                for record in context.continuation_records),
            'prospective_amendments': tuple((record.to_document() if exhaustive else record.identity.to_document())
                for record in context.amendment_records),
            'scientific_design': context.design.identity.to_document(), 'downstream_account': context.design.downstream_account,
            'state': ('OPERATIONS_COMPLETE' if operational else 'COMPLETE') if frontier.complete
                else 'DEPENDENCIES_REQUIRED' if dependencies else 'IN_PROGRESS',
            'frontier': {'eligible': frontier.eligible, 'unentered': frontier.unentered, 'waiting': frontier.waiting},
            'phases': phases, 'dependencies': tuple(dependencies),
            'read_scope': 'OPERATIONAL_ADVANCE' if operational else 'PARTIAL' if allow_partial else 'FULL',
            'observation_scope': 'OWNER_READS_DURING_THIS_OPERATION',
            'binding_publication_pending': dict(context.pending_bindings),
            'structural_prediction_comparison': (structural_prediction if structural_prediction is not None
                else programme_structural_prediction(context)
                if scientific_reconstruction_enabled() else {'status': 'DEFERRED_EXPLICIT_RECONSTRUCTION'}),
            'scientific_reconstruction': 'full' if scientific_reconstruction_enabled() else 'off',
            'denominator_aggregation': 'SEPARATE_SCOPES_NO_CROSS_PHASE_SUM',
            'scientific_qualification': 'NOT_ESTABLISHED'}

    def _advance_report(self, context, dependencies):
        # An operation report describes its owning reads, not a new full read
        # of all science. Current permission still bounds returned outcomes.
        from .matrix_programme_products import _current_grants
        with self.writer.read_context() as authorities:
            current = _current_grants(context, authorities)
            report = self._report(context, dependencies=dependencies, operational=True)
            current()
        return report

    def _advance(self, context, *, mode, confirmed=False):
        blocked, dependencies = set(), []
        # Every successful step either retains a new binding, authors one exact
        # child or completes an ordinary owner observation. No polling loop or
        # native retry is introduced by orchestration.
        # Initial acquisitions need execution records to prevent redispatch.
        # E3 assembly owns TRAIN's full read and bank export. Each later
        # outcome-dependent projector keeps its complete original science and
        # current authority checks. This advance report is not a full read.
        self._observe(context, operational=True)
        for _ in range(4 * len(PHASES) + 1):
            frontier = programme_frontier(context.observations, downstream_account=context.design.downstream_account,
                operational=True)
            choices = tuple(phase for phase in frontier.eligible if phase not in blocked)
            if not choices:
                # Refresh access to any scientific bodies returned by this
                # operation. Do not replay every completed phase a second time.
                return self._advance_report(context, dependencies)
            phase = choices[0]
            try:
                if phase not in context.bindings:
                    self._retain_binding(context, phase, self._project(context, phase))
                    self._observe(context, phases=(phase,), operational=True)
                    continue
                if phase in METADATA_PHASES:
                    blocked.add(phase)
                    continue
                author_options = {'observe_authoring': True} if mode == 'author' and phase in ('e2', 'train') else {}
                if mode != 'derive' and self._author_phase(context, phase, **author_options):
                    if mode == 'author':
                        authored = getattr(context, 'authored_reports', {}).get(phase)
                        self._observe(context, phases=(phase,), operational=True,
                            reports=None if authored is None else {phase: authored})
                        blocked.add(phase)
                        continue
                    # This invocation just authored the exact selected child.
                    # Its ordinary execution owner now authenticates that child
                    # before dispatch. A status read here would decode the same
                    # graph solely to tell this controller that it authored it.
                if mode in ('derive', 'author'):
                    blocked.add(phase)
                    continue
                report = self._operate_phase(context, phase, recover=mode == 'recover', confirmed=confirmed)
                if report.get('schema') == 'empirical-lawhood/api/result' and report.get('status') != 'SUCCEEDED':
                    # A refused issued operation has no completed scientific
                    # read. Preserve its actual cause before any such read can
                    # replace it with a missing-terminal error.
                    dependencies.append({'phase': phase, 'code': 'PHASE_OPERATION_NOT_COMPLETED',
                        'detail': 'The issued child operation did not complete.', 'operation_result': report})
                    blocked.add(phase)
                    continue
                # A development runner already returns its owning full read.
                # Reuse that immediate result; issued run summaries still need
                # the scientific reader. No report persists between calls.
                returned_read = (report.get('read_scope') == 'EXECUTION_RECORDS'
                    or _phase_complete(phase, report) and (isinstance(report.get('scientific_result'), dict)
                        or phase in ('e4.calibration', 'e4.confirmation')))
                self._observe(context, phases=(phase,), operational=True,
                    reports={phase: report} if returned_read else None)
                observation = context.observations[phase]
                if not (observation.complete or observation.execution_complete):
                    blocked.add(phase)
            except MatrixProgrammePrerequisite as error:
                dependencies.append({'phase': error.phase, 'code': error.code, 'detail': error.detail})
                blocked.add(phase)
        raise RuntimeError('Matrix programme failed to make bounded phase progress')

    def author(self, *, preparation, output_dir):
        return self.author_with_preparation(preparation=preparation, output_dir=output_dir)

    def author_with_preparation(self, *, preparation, output_dir):
        """Authenticate current prerequisites once, retaining them through authoring."""
        return self._start_prepared(preparation=preparation, output_dir=output_dir, mode='author')

    def continue_prepared(self, *, preparation, output_dir, maximum_parallel_tasks, confirmed):
        """Author and execute one prepared continuation in its owning context."""
        if (type(confirmed) is not bool or not confirmed
                or maximum_parallel_tasks != preparation.execution.workers):
            raise ValueError('Matrix continuation requires its exact workers and explicit confirmation')
        return self._start_prepared(preparation=preparation, output_dir=output_dir, mode='run', confirmed=True)

    def _start_prepared(self, *, preparation, output_dir, mode, confirmed=False):
        from empirical_lawhood.api.composite_experiment_programme import write_experiment_programme_descriptor
        self._require_preparation(preparation)
        if self.service.storage_profile is None or self.writer is None:
            raise ValueError('Matrix authoring requires its selected storage profile and guarded artifact writer')
        plan = preparation.programme
        if type(plan) is not MatrixResearchProgrammePlan or Path(output_dir) != self._home(plan):
            raise ValueError('Matrix authoring requires the one selected programme home')
        from .selected_e3_access import original_e3_authority_read_context
        with original_e3_authority_read_context(self.writer), self._context(plan) as context:
            preparation = self._refine_context(preparation, context)
            if not preparation.executable:
                raise ValueError('Matrix authoring requires its ordinary prepared original C and execution settings')
            _publish(self.writer, context.directory / PLAN_FILENAME, plan)
            descriptor = ExperimentProgrammeDescriptor('descriptor.' + plan.fingerprint(), programme_protocol(plan.specification),
                plan.specification.identity, plan.identity)
            path = context.directory / PROGRAMME_DESCRIPTOR_FILENAME
            if path.exists() or path.is_symlink():
                if read_bounded_bytes(path, maximum_bytes=64 * 1024) != descriptor.canonical_bytes():
                    raise PermissionError('Matrix authoring changes its original programme descriptor')
            else:
                write_experiment_programme_descriptor(service=self.service, directory=context.directory, descriptor=descriptor)
            report = self._advance(context, mode=mode, confirmed=confirmed)
        return {**report, 'authoring_dir': str(output_dir), 'programme_descriptor': descriptor.to_document()}

    def run(self, *, directory, maximum_parallel_tasks, programme_request_path=None, confirmed=False):
        return self._operate(directory, maximum_parallel_tasks, programme_request_path, confirmed, 'run')

    def recover(self, *, directory, maximum_parallel_tasks, programme_request_path=None, confirmed=False):
        return self._operate(directory, maximum_parallel_tasks, programme_request_path, confirmed, 'recover')

    def _operate(self, directory, workers, request_path, confirmed, mode):
        plan = self._plan(directory)
        if type(confirmed) is not bool or workers != plan.workers:
            raise ValueError('Matrix operation requires its exact selected concurrency and explicit confirmation value')
        operation = self._request(plan, request_path)
        from .selected_e3_access import original_e3_authority_read_context
        with original_e3_authority_read_context(self.writer), self._context(plan, operation=operation) as context:
            return self._advance(context, mode=mode, confirmed=confirmed)

    def read(self, *, directory, allow_partial=False, programme_request_path=None):
        if type(allow_partial) is not bool:
            raise TypeError('Matrix read requires explicit partial/full inspection')
        plan = self._plan(directory)
        with self._read_context(plan, operation=self._request(plan, programme_request_path)) as context:
            operational = not scientific_reconstruction_enabled()
            self._observe(context, allow_partial=allow_partial, operational=operational)
            return self._report(context, allow_partial=allow_partial, operational=operational)

    def export_products(self, *, directory, selection_path, programme_request_path=None):
        from .matrix_programme_products import export_programme_products
        return export_programme_products(self, directory=directory, selection_path=selection_path,
            programme_request_path=programme_request_path)

    def derive_inputs(self, *, specification, source_selection_path, metadata_directory, output_selection_path, execution):
        preparation = prepare_experiment(specification, execution=execution)
        # Authenticate the selected operational context before publication.
        # The ordinary target validator reopens the static preparation first;
        # the public programme service then applies this same current refinement.
        self.refine_preparation(preparation)
        plan = preparation.programme
        if plan is None or Path(metadata_directory) != self._home(plan):
            raise ValueError('Matrix input derivation requires the one selected programme home and actual execution settings')
        with self._context(plan) as context:
            self._advance(context, mode='derive')
            selector = ExperimentFileInputSelection('sources.' + specification.fingerprint(), programme_protocol(specification), (), ())
            target_path = context.directory / 'specification.json'
            target = _publish(self.writer, target_path, specification)
            source = _publish(self.writer, output_selection_path, selector)
            raw = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
                'version': '1.0.0', 'value': {'specification': specification.identity,
                    'original_commitments': specification.input_commitments.record,
                    'scientific_authority': 'NONE', 'native_contact': 'NONE'}})
            relative = _relative(self.writer, context.directory / ('requirements.' + sha256(raw).hexdigest() + '.json'), writing=True)
            requirements = self.writer.write(ArtifactWriteRequest('requirements.' + sha256(raw).hexdigest(), relative,
                'empirical-lawhood/operational/experiment-input-requirements', ArtifactProfile.CANONICAL_JSON,
                'application/json', 'matrix-programme', specification.directory, raw,
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
            return ExperimentInputDerivationResult(specification.identity, selector, Path(output_selection_path),
                preparation, (target, source, requirements), requirements, specification, target_path)
