# SPDX-License-Identifier: MPL-2.0
"""Unpublished incomplete E3 assessment from ordinary current custody.

The public configured reader owns issue/plan authentication and current reveal
before this helper and again at return. This helper never launches work, repairs
a parent, publishes a receipt or claims a retained adjudication.
"""

from hashlib import sha256
from collections import Counter
from contextlib import contextmanager

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as methods
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_preparation import (
    decode_response_inputs, response_native_work,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import ConfiguredProtectedE3ResponseConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import ConfiguredE3ContinuedResponseConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_source_records import NAMESPACE
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import statistical_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_unknown_response import (
    ConfiguredProtectedE3UnknownResponseAvailability, score_unknown_response,
)
from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader, authenticate_task_dispatch_authority
from empirical_lawhood.api.protected_e3_read_custody import product
from empirical_lawhood.api.recursive_qualified_parents import _collect_receipt_closure
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.execution import LocalScheduler, validate_resolved_external_inputs
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.retained_input_read import RetainedInputRead
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_value
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactManifest, most_restrictive_outcome_access
from empirical_lawhood.runtime.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.experimental_statistics import binomial_upper_tail, split_upper_calibration
from empirical_lawhood.runtime.native_subwork import NativeSubworkState


def _external_inputs(writer, task, run_id):
    result = []
    for spec in task.external_inputs:
        relative, _, _ = provider_input_location(writer, run_id, spec.logical_artifact_id)
        manifest = writer.read_manifest(relative)
        logical, physical = manifest.logical, manifest.materialization
        if (manifest.publication is None or physical.relative_path != relative
                or physical.storage_root_id != writer.root.contract.storage_root_id
                or logical.logical_artifact_id != spec.logical_artifact_id
                or physical.compression != 'none' or physical.partition_selector is not None):
            raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_EXTERNAL_INPUT_REQUIRED')
        writer.verify_manifest(manifest)
        result.append(VerifiedArtifactInput(logical, physical))
    return validate_resolved_external_inputs(task, tuple(sorted(result, key=lambda value: value.artifact_id)))


def _configuration(writer, task, external):
    matches = tuple(value for value in external if value.logical.logical_artifact_id == task.capability.config.artifact_id)
    if len(matches) != 1:
        raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_CONFIGURATION_REQUIRED')
    value, = matches
    raw = read_bounded_bytes(writer.root.resolve(value.materialization.relative_path, for_write=False),
        maximum_bytes=value.materialization.size_bytes)
    kind = {kind.SCHEMA: kind for kind in (ConfiguredProtectedE3ResponseConfig, ConfiguredE3ContinuedResponseConfig)}.get(
        task.capability.config.config_schema)
    if kind is None:
        raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_CONFIGURATION_REQUIRED')
    config = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    if (not config.canonical_equals(raw) or config.fingerprint() != task.capability.config.content_sha256
            or sha256(raw).hexdigest() != value.materialization.physical_sha256
            or config.operation != 'responses'):
        raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_CONFIGURATION_REQUIRED')
    return config


@contextmanager
def _input_ports(writer, values, bindings, maximum_bytes, input_read):
    if input_read is not None:
        with input_read.open_many(values, bindings=bindings, maximum_bytes=maximum_bytes) as ports:
            yield ports
        return
    ports = writer.open_many(values, bindings=bindings, maximum_bytes=maximum_bytes)
    try:
        yield ports
    finally:
        for port in ports:
            port.close()


def _operands(writer, package, task, contact, receipts, external, *, input_read=None, control_reader=None):
    if input_read is not None and (type(input_read) is not RetainedInputRead or input_read.writer is not writer
            or type(control_reader) is not CurrentResultPlanReader or control_reader.writer is not writer):
        raise PermissionError('incomplete response input reuse changes its owning custody scope')
    if any(parent not in receipts for parent in task.dependency_task_ids):
        return None
    dependencies = {}
    for task_id in task.dependency_task_ids:
        receipt = receipts[task_id]
        physical = {row.logical_artifact_id: row for row in receipt.output_materializations}
        dependencies[task_id] = tuple(VerifiedArtifactInput(row, physical[row.logical_artifact_id])
            for row in receipt.output_logical_artifacts)
    dependency_outputs = LocalScheduler._dependency_outputs(task, dependencies)
    selected = tuple(sorted((
        *((value, WorkerInputBinding.from_verified(value, kind=WorkerInputKind.DEPENDENCY)) for value in dependency_outputs),
        *((value, WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL)) for value in external)),
        key=lambda row: row[1].artifact_id))
    if any(not LocalScheduler._input_is_authorized(task, value) for value, _ in selected):
        raise PermissionError('INCOMPLETE_E3_ORIGINAL_INPUT_ACCESS_REQUIRED')
    bindings = tuple(binding for _, binding in selected)
    with _input_ports(writer, tuple(value for value, _ in selected), bindings,
            task.capability.requested_resources.source_scan_bytes, input_read) as ports:
        context = TaskContext(contact.run_id, task.task_id, contact.attempt_id, task.capability.config, bindings, ports,
            tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile, row.media_type, row.logical_artifact_id)
                for row in task.outputs), task.capability.required_permissions, task.capability.requested_outcome_access,
            task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL,
            dependency_receipts=LocalScheduler._dependency_receipt_bindings(task,
                dependency_outputs=dependency_outputs, receipts=receipts))
        if (contact.execution_task != ObjectIdentity.from_record(task.task_id, task)
                or contact.implementation_commit != package.issued_study.source_closure.implementation_commit
                or contact.input_materialization_ids != context.input_materialization_ids
                or contact.dependency_receipt_ids != context.dependency_receipt_ids):
            raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_CONTACT_INPUTS_REQUIRED')
        manifest = package.registry.resolve(task.capability.capability_key, task.capability.capability_version)
        if manifest.implementation_sha256 != task.capability_implementation_sha256:
            raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_RESPONSE_METHOD_REQUIRED')
        def read_record(port, prepared, kind):
            from empirical_lawhood.adapters.methods.matrix_factor_response.protected_input_custody import read_protected_e3_response_input
            retained = input_read.retained_manifest(port)
            if retained is None:
                return read_protected_e3_response_input(port, prepared, kind)
            if prepared is not None:
                raise PermissionError('incomplete response read cannot replace worker input delivery')
            return control_reader.read_control(retained, kind, port.size_bytes)

        operands = decode_response_inputs(context, capability=manifest, operation='responses', statistical_task_id=statistical_task_id,
            **({} if input_read is None else {'record_reader': read_record}))
        work = response_native_work(operands, context=context, expected_parent=contact)
        return operands, work, tuple(ArtifactManifest(value.logical, value.materialization) for value, _ in selected)


def _unknown_response(writer, package, plan, task, config, external, receipts, attempt_ids, *, input_read=None, control_reader=None):
    contacts = ExternalNativeEffectContactStore(plane=writer,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.most_restrictive(*(row.visibility_ceiling for row in task.outputs)),
        outcome_access=most_restrictive_outcome_access(task.capability.requested_outcome_access,
            *(row.outcome_access for row in task.outputs)))
    contact = contacts.read(package.run_plan_id, task.task_id)
    if contact is None:
        return 'UNENTERED', None
    if contact.attempt_id not in attempt_ids:
        raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_ATTEMPT_REQUIRED')
    evidence = {'contact': contact}
    authenticate_task_dispatch_authority(package=package, execution_plan=plan, run_id=contact.run_id,
        task_id=contact.task_id, attempt_id=contact.attempt_id, writer=writer)
    prepared = _operands(writer, package, task, contact, receipts, external,
        **({} if input_read is None else {'input_read': input_read, 'control_reader': control_reader}))
    if prepared is None:
        return 'CONTACTED_OPERANDS_UNAVAILABLE', evidence
    operands, work, selected_inputs = prepared
    if operands.config != config:
        raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_RESPONSE_CONFIGURATION_REQUIRED')
    store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts, parent_contact=contact,
        parent_inputs=selected_inputs)
    roster = store.read_roster(contact)
    if roster is None:
        return 'PARENT_CONTACT_WITHOUT_NESTED_ENTRY', evidence
    if roster != work.rosters[0] or tuple(store.iter_roster_definitions(contact)) != work.definitions:
        raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_NATIVE_ROSTER_REQUIRED')
    definition, = work.definitions
    inspection = store.inspect(definition)
    evidence.update({'roster': roster, 'native_state': inspection.state.value,
        'definition': definition, 'completion': inspection.completion,
        'call_entry': inspection.call_entry, 'call_return': inspection.call_return})
    if inspection.native_return_status is not None:
        return ('KNOWN_FAILED_NATIVE_RETURN' if inspection.native_return_status is OperationalStatus.FAILED
            else 'KNOWN_NATIVE_RETURN_WITHOUT_PARENT_RESULT'), evidence
    if inspection.state is NativeSubworkState.UNKNOWN_COMPLETION:
        availability = ConfiguredProtectedE3UnknownResponseAvailability.from_inspection(
            'read-availability.' + task.task_id, parent_contact=contact, roster=roster, inspection=inspection,
            contact_identity=ObjectIdentity.from_record(store._id(definition, 'contact'), inspection.contact))
        score, outcome = score_unknown_response(availability, operands,
            score_id='read-score.' + task.task_id, outcome_id='read-outcome.' + task.task_id)
        evidence.update({'availability': availability, 'score': score, 'outcome': outcome,
            'forecast': operands.records['error']})
        return 'UNKNOWN_CONTACT', evidence
    return 'NESTED_NOT_CONTACTED', evidence


def _denominator_math(specification, allocation, rows, freezes):
    """Use every assigned unit; missing observations never shrink n or rank."""
    calibration, decisions = [], []
    matched = specification.measurement.is_matched
    model_scores = {method: [] for method in ('B0', 'S0')}
    primary = None if matched else methods.exposed.ENDPOINTS.index((specification.measurement.primary_description, specification.measurement.primary_horizon))
    for role in ('calibration', 'evaluation'):
        for unit in allocation.unit_ids(role):
            row = rows[unit]
            forecast, outcome = row.get('forecast'), row.get('outcome')
            if forecast is None or outcome is None:
                if role == 'calibration':
                    if matched:
                        for scores in model_scores.values():
                            scores.append((unit, None, (row['state'],)))
                    else:
                        calibration.append((unit, None, (row['state'],)))
                else:
                    if specification.is_curve_primary:
                        decisions.append(methods.MatchedCurveDecision(unit, 'S0', 1, False, False,
                            tuple((method, (None,)) for method in methods.matched.MATCHED_METHODS),
                            tuple((method, None) for method in methods.matched.MATCHED_METHODS), (row['state'],), (unit,)))
                    else:
                        decisions.append(methods.matched.MatchedRootDecision(unit, False, False,
                        tuple((method, None) for method in methods.matched.MATCHED_METHODS), (row['state'],)) if matched else
                        methods.exposed.MatrixE3RootDecision(unit, False, False,
                        tuple((method, view, None) for method in ('ALL_ORIGIN_RIDGE', 'RAW_TRAIN_MEDIAN')
                            for view in ('fine', 'primary')), (row['state'],)))
                continue
            frozen = freezes.get(forecast.frozen_products)
            allocated = allocation.unit(unit)
            if (frozen is None or frozen.specification != specification.identity or frozen.allocation != allocation.identity
                    or forecast.role != role or forecast.models != frozen.models
                    or forecast.specification != specification.identity or forecast.allocation != allocation.identity
                    or outcome.forecast != methods.identity(forecast) or outcome.feature != forecast.feature
                    or allocated is None or allocated.exposed or forecast.feature.source_manifest.object_id != allocated.source_id
                    or forecast.feature.source_manifest not in allocation.sources
                    or forecast.feature.public_source.reservation not in allocation.sources
                    or forecast.feature.public_source.root.role.value != ('CALIBRATION' if role == 'calibration' else 'CONFIRMATION')
                    or forecast.feature.cutoff != specification.measurement.origin_tick * specification.measurement.primary_timestep
                    or role == 'evaluation' and frozen.calibration is None):
                raise PermissionError('INCOMPLETE_E3_ORIGINAL_FROZEN_FORECAST_AND_PAIRED_OUTCOME_REQUIRED')
            reasons = list(methods.numerical.outcome_reasons(specification, outcome))
            if forecast.feature.disposition != 'AVAILABLE':
                reasons.append(forecast.feature.disposition)
            if role == 'calibration':
                if matched:
                    for method in ('B0', 'S0'):
                        score, tags = methods.numerical.matched_calibration_value(dict(forecast.log_points)[method], outcome, reasons)
                        model_scores[method].append((unit, score, tags))
                else:
                    score, tags = methods.numerical.calibration_score(specification, forecast.log_points, outcome, reasons)
                    calibration.append((unit, score, tags))
            elif matched:
                decision = methods.curve_root_decision if specification.is_curve_primary else methods.matched.matched_root_decision
                decisions.append(decision(unit, dict(forecast.log_points), outcome, reasons))
            else:
                usable, success, comparisons, tags = methods.numerical.paired_root_decision(
                    specification, dict(forecast.log_points), outcome, primary, reasons)
                decisions.append(methods.exposed.MatrixE3RootDecision(unit, usable, success, comparisons, tags))
    calibrations = tuple(methods.matched.matched_model_calibration(method, tuple(scores)) for method, scores in model_scores.items()) if matched else ()
    if matched:
        calibration = list(calibrations[1].scores)
    ranked = split_upper_calibration(tuple(row[1] for row in calibration), specification.calibration_alpha)
    successes, usable = sum(row.success for row in decisions), sum(row.usable for row in decisions)
    tail = binomial_upper_tail(len(decisions), successes, specification.assessment.null_probability)
    return {'calibration': {'scores': tuple(calibration), 'rank': ranked.rank,
                'radius': None if ranked.radius.is_infinite() else ranked.radius,
                'radius_kind': 'INFINITE' if ranked.radius.is_infinite() else 'FINITE',
                **({'admission_owner': 'S0', 'separate_model_calibrations': calibrations} if matched else {})},
        'assessment': {'decisions': tuple(decisions), 'assigned_units': len(decisions), 'successes': successes,
            'usable_units': usable, 'binomial_tail_numerator': tail.numerator, 'binomial_tail_denominator': tail.denominator,
            'criterion_met': tail <= specification.assessment.alpha and usable >= specification.assessment.minimum_usable_units,
            **({'amended_inference': methods.matched.matched_primary_inference(tuple(decisions))} if matched else {})}}


def _receipt_sources(*, writer, package, plan, receipts, retained):
    """Keep each accepted receipt with its producing plan and live read owner."""
    sources = [(writer, plan, receipts)]
    if retained is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import ConfiguredE3RetainedTaskConfig
        adopted = {task.task_id: task for task in plan.tasks
            if task.capability.config.config_schema == ConfiguredE3RetainedTaskConfig.SCHEMA}
        if retained.unfinished is None:
            if set(adopted) != set(retained.tasks):
                raise PermissionError('INCOMPLETE_E3_EXACT_RETAINED_TASK_CENSUS_REQUIRED')
            for task_id, task in adopted.items():
                retained.require_config(retained.tasks[task_id], task, package.run_plan_id)
                if task_id in receipts:
                    retained.require_receipt(retained.tasks[task_id], task, receipts[task_id])
        else:
            previous = retained.predecessor
            if (previous is None or adopted
                    or {task.task_id for task in plan.tasks} != set(retained.unfinished.unfinished_task_ids)
                    or set(previous.receipts).intersection(task.task_id for task in plan.tasks)):
                raise PermissionError('INCOMPLETE_E3_EXACT_UNFINISHED_TASK_CENSUS_REQUIRED')
            previous.require_access()
            inherited = (previous.receipt_sources() if hasattr(previous, 'receipt_sources')
                else ((previous.writer, previous.plan, previous.receipts),))
            seen = set()
            for _, producing_plan, producing_receipts in inherited:
                if (not set(producing_receipts) <= {task.task_id for task in producing_plan.tasks}
                        or seen & set(producing_receipts)):
                    raise PermissionError('INCOMPLETE_E3_EXACT_UNFINISHED_TASK_CENSUS_REQUIRED')
                seen.update(producing_receipts)
            if seen != set(previous.receipts):
                raise PermissionError('INCOMPLETE_E3_EXACT_UNFINISHED_TASK_CENSUS_REQUIRED')
            sources[:0] = inherited
    return tuple(sources)


def read_incomplete_assessment(*, writer, package, plan, specification, allocation, retained=None):
    """Consume the current complete assigned census with explicit missingness."""
    closure = _collect_receipt_closure(package, plan, writer, None, (NAMESPACE + '.',), allow_partial=True)
    receipts = closure.by_task
    sources = _receipt_sources(writer=writer, package=package, plan=plan, receipts=receipts, retained=retained)
    rows, freezes = {}, {}
    tasks = tuple(task for task in plan.tasks if task.capability.capability_key ==
        NAMESPACE + ('.responses' if retained is None else '.continued-responses'))
    frequencies = Counter(spec.logical_artifact_id for task in tasks for spec in task.external_inputs)
    with RetainedInputRead(writer, shared_artifact_ids=(key for key, count in frequencies.items() if count > 1)) as input_read:
        control_reader = CurrentResultPlanReader(writer)
        for task in tasks:
            external = _external_inputs(writer, task, package.run_plan_id)
            config = _configuration(writer, task, external)
            if config.specification != specification.identity:
                raise PermissionError('INCOMPLETE_E3_EXACT_ORIGINAL_SPECIFICATION_REQUIRED')
            root = config.source.root.root
            role = 'calibration' if root.role.value == 'CALIBRATION' else 'evaluation' if root.role.value == 'CONFIRMATION' else None
            if role is None or root.independent_group_id not in allocation.unit_ids(role):
                raise PermissionError('INCOMPLETE_E3_EXACT_ASSIGNED_PROTECTED_ROOT_REQUIRED')
            unit = root.independent_group_id
            if unit in rows:
                raise PermissionError('INCOMPLETE_E3_ASSIGNED_ROOT_CENSUS_REPEATED')
            summary = closure.operational_summaries.get(task.task_id)
            state = 'UNENTERED' if summary is None else summary.disposition.value
            row = {'unit_id': unit, 'root_id': root.root_id, 'role': role, 'task_id': task.task_id,
                'state': 'OPERATIONAL_SUCCEEDED_WITHOUT_OUTCOME' if state == 'SUCCEEDED' else state,
                'operational_status': state, 'reason_code': None if summary is None else summary.reason_code,
                'forecast': None, 'outcome': None, 'score': None, 'availability': None, 'contact': None}
            if task.task_id not in receipts:
                observed, values = _unknown_response(writer, package, plan, task, config, external, receipts,
                    tuple(candidate.attempt_id for candidate in closure.recovery_index.task(task.task_id).attempts),
                    input_read=input_read, control_reader=control_reader)
                row['state'] = state if observed == 'UNENTERED' and summary is not None else observed
                if values is not None:
                    row.update(values)
            rows[unit] = row
    del control_reader
    if retained is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution
        if type(retained.unfinished) is ConfiguredE3ClosedExecution:
            previous = retained.predecessor
            previous.require_access()
            missing = previous.missing_products(retained.retention.response_provenance)
            for root in retained.unfinished.calibration_roots:
                if root.unit_id in rows:
                    raise PermissionError('INCOMPLETE_E3_CLOSED_CAL_NATIVE_REENTRY')
                row = {'unit_id': root.unit_id, 'root_id': root.root_id, 'role': 'calibration',
                    'task_id': root.native_task_id, 'state': 'OPERATIONAL_SUCCEEDED_WITHOUT_OUTCOME',
                    'operational_status': 'SUCCEEDED', 'reason_code': None,
                    'forecast': None, 'outcome': None, 'score': None, 'availability': None,
                    'contact': previous.contacts[root.native_task_id]}
                if root.missing_products is not None:
                    products = missing[root.native_task_id]
                    row.update(state='UNKNOWN_CONTACT', operational_status='UNKNOWN_COMPLETION',
                        reason_code='UNKNOWN_CONTACT', forecast=previous.unknown[root.native_task_id]['forecast'],
                        outcome=products.outcome, score=products.score, availability=products.availability)
                rows[root.unit_id] = row
    expected = set(allocation.unit_ids('calibration')) | set(allocation.unit_ids('evaluation'))
    if set(rows) != expected:
        raise PermissionError('INCOMPLETE_E3_COMPLETE_ASSIGNED_UNIT_CENSUS_REQUIRED')
    for source_writer, source_plan, source_receipts in sources:
        for task_id, receipt in source_receipts.items():
            if any(row.payload_schema == methods.ConfiguredProtectedE3FrozenProducts.SCHEMA for row in receipt.output_logical_artifacts):
                frozen, _ = product(source_writer, source_plan, source_receipts, task_id, methods.ConfiguredProtectedE3FrozenProducts)
                freezes[methods.identity(frozen)] = frozen
            for kind, key in ((methods.ConfiguredProtectedE3Forecast, 'forecast'), (methods.ConfiguredProtectedE3PairedOutcome, 'outcome')):
                if any(row.payload_schema == kind.SCHEMA for row in receipt.output_logical_artifacts):
                    record, _ = product(source_writer, source_plan, source_receipts, task_id, kind)
                    unit = record.feature.unit_id
                    if unit in rows:
                        existing = rows[unit][key]
                        if existing is not None and existing != record:
                            raise PermissionError('INCOMPLETE_E3_ORIGINAL_ROOT_OBSERVATION_CONFLICT')
                        rows[unit][key] = record
                        if key == 'outcome' and rows[unit]['state'] != 'UNKNOWN_CONTACT':
                            rows[unit]['state'] = 'RETAINED_OUTCOME'
    math = _denominator_math(specification, allocation, rows, freezes)
    return canonical_value({'scientific_status': 'UNEVALUABLE', 'admission_status': 'UNEVALUABLE',
        'evaluability': 'UNEVALUABLE', 'qualification': 'NOT_ESTABLISHED',
        'reason_codes': ('UNPUBLISHED_INCOMPLETE_ASSESSMENT',), 'adjudication': None,
        'scientific_completion': 'UNPUBLISHED_INCOMPLETE_ASSESSMENT', 'typed_product_validation': 'COMPLETE_FOR_RETAINED_RECEIPTS',
        'assigned_tasks': len(plan.tasks), 'completed_tasks': len(receipts), 'native_contact': 'none',
        'denominators': {public: {'assigned_units': len(allocation.unit_ids(role)), 'units': allocation.unit_ids(role)}
            for public, role in (('calibration', 'calibration'), ('confirmation', 'evaluation'))},
        'roots': tuple(rows[unit] for unit in sorted(rows)), **math})
