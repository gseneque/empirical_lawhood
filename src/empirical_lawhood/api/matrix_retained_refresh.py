# SPDX-License-Identifier: MPL-2.0
"""SCI01 composition over the original E4 reader and retained-analysis custody.

The source consumer owns original access and the complete receipt census through
publication. This API adds no native runner, fitter, scheduler or permission.
"""

from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter, process_time

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import REFRESH_PROTOCOL_ID, MatrixRefreshArrays, MatrixRefreshCaseAssessment, MatrixRefreshCaseSource, MatrixRefreshDecision, MatrixRefreshProtocol, refresh_columns
from empirical_lawhood.api.configuration import _write_new_file
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance, numerical_package_code_sha256, preflight_matrix_output_directory
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays, decoded_matrix_array_scope, encode_matrix_arrays
from empirical_lawhood.storage.retained_analysis import publish_retained_analysis, read_retained_analysis, read_retained_analysis_member
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.domains.matrix.input_contracts import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.execution.retained_analysis import RetainedAnalysisMember

SPECIFICATION_PATH = 'programmes/foundations/emergent-structure/records/matrix-sci01-retained-refresh-v1.md'
SPECIFICATION_SCHEMA = 'empirical-lawhood/matrix-sci01/specification-markdown'


def _pin(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


def _plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _json(value):
    return (json.dumps(_plain(value), sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def _member(output, name, raw, *, schema, media='application/json'):
    _write_new_file(output / name, raw)
    return RetainedAnalysisMember(name, ArtifactIdentity(
        REFRESH_PROTOCOL_ID + '.' + name.replace('/', '.'), 'sci01-retained-member', schema,
        sha256(raw).hexdigest(), media, len(raw)))


def _select_original(context):
    """Derive, never author, the census from one actual complete original read."""
    from empirical_lawhood.api.matrix_full_factor_custody import _record
    from empirical_lawhood.domains.matrix.matrix_scheduled_history import selected_e3_e4_records as records
    from empirical_lawhood.domains.matrix.matrix_scheduled_history import selected_e3_e4_bindings as owner
    from empirical_lawhood.domains.matrix.matrix_scheduled_history.response_records import ScheduledResponseScore
    writer, products, plan, access = (context[key] for key in ('writer', 'products', 'plan', 'original_input_access'))
    access.require_current()
    if (products['terminal'] is None or products['terminal'].operational_status != 'SUCCEEDED'
            or set(products['receipts']) != {task.task_id for task in plan.tasks}):
        raise PermissionError('SCI01 requires complete original E4 execution custody')
    facts = frozenset((value.logical, value.materialization) for value in products['outputs'].values())
    tasks = {task.task_id: task for task in plan.tasks}
    protocols = {p.public_source.root.root_id: p for p in context['bank'].response_selection.protocols}
    panels = dict(context['bank'].response_selection.panels)
    selected = []
    for index, case in enumerate(context['cases']):
        protocol = protocols[case.root_id]
        actual, custody = {}, {}
        for phase, kind, field in (
                ('project', records.SelectedE3E4CausalPrefix, 'prefix_id'),
                ('mechanical', records.SelectedE3E4MechanicalForecast, 'forecast_id'),
                ('responses', records.SelectedE3E4Responses, 'response_id'),
                ('response-score', ScheduledResponseScore, 'score_id')):
            record, retained = _record(writer, products, plan, owner.local_node(case.root_id, phase), kind, field,
                original_input_access=access, publication_facts=facts, task_index=tasks)
            if record is None or retained is None:
                raise PermissionError('SCI01 requires the complete original case products')
            actual[phase], custody[phase] = record, retained
        causal, physical, response, score = (actual[key] for key in ('project', 'mechanical', 'responses', 'response-score'))
        causal_pin, physical_pin, response_pin = (_pin(causal, 'prefix_id'), _pin(physical, 'forecast_id'), _pin(response, 'response_id'))
        protocol_pin = _pin(protocol, 'protocol_id')
        if (any(record.source != case.source for record in actual.values())
                or physical.protocol != response.protocol or physical.protocol != protocol_pin
                or physical.causal_prefix != response.causal_prefix or physical.causal_prefix != causal_pin
                or response.physical_forecast != physical_pin
                or (score.causal_prefix, score.physical_forecast, score.responses) != (causal_pin, physical_pin, response_pin)
                or score.error_forecast != response.error_forecast
                or (score.root_id, score.independent_group_id) != (case.root_id, case.group_id)
                or score.disposition != case.score_disposition
                or protocol.public_source.source != case.source
                or score.disposition not in ('FINITE', 'NO_ORIGIN')
                or score.disposition == 'FINITE' and (physical.disposition != 'AVAILABLE' or response.disposition != 'COMPLETED')
                or score.disposition == 'NO_ORIGIN' and (causal.disposition, physical.disposition, response.disposition) != ('NO_ORIGIN',) * 3):
            raise PermissionError('SCI01 substitutes original source, response, score, availability or instrument joins')
        coordinate = protocol.public_source.coordinate
        binding = MatrixRefreshCaseSource(index, case.root_id, case.group_id, case.source, protocol_pin,
            causal_pin, physical_pin, response_pin, _pin(score, 'score_id'), score.disposition, score.numerical_pass,
            (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma, coordinate.member.cross_coupling_gamma),
            tuple(sorted(panel.panel_id for panel in panels[case.group_id])))
        selected.append((binding, protocol, actual, custody))
    access.require_current()
    return tuple(selected), facts, tasks


def _arrays(context, binding, phase, operand, facts, tasks):
    from empirical_lawhood.api.matrix_full_factor_custody import _output
    from empirical_lawhood.domains.matrix.matrix_scheduled_history import selected_e3_e4_bindings as owner
    writer, products, plan, access = (context[key] for key in ('writer', 'products', 'plan', 'original_input_access'))
    actual = _output(writer, products, plan, owner.local_node(binding.root_id, phase), 'arrays',
        original_input_access=access, publication_facts=facts, task_index=tasks)
    if actual is None:
        raise PermissionError('SCI01 original array output is missing')
    _, publication = actual
    artifact = operand.array_artifact
    # The typed development operand can remain inside an evaluation-sealed
    # original publication. Its label does not grant access or replace that
    # publication's restriction; the authenticated original reader owns access.
    if (publication.logical.logical_artifact_id, publication.logical.payload_schema,
            publication.logical.content_sha256, publication.materialization.size_bytes) != (
            artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.size_bytes):
        raise PermissionError('SCI01 original array producer, access or bytes differ')
    access.require_current()
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False), maximum_bytes=artifact.size_bytes)
    arrays = decode_matrix_arrays(raw, operand)
    access.require_current()
    return arrays


def _protocol(context, selected, specification_sha256):
    return MatrixRefreshProtocol(context['entry'].programme.identity,
        _pin(context['plan'], 'execution_plan_id'), context['original_evidence'].identity,
        context['run_id'], tuple(row[0] for row in selected), specification_sha256)


def _original_custody(context):
    products = context['products']
    return {'original_run_id': context['run_id'], 'terminal': products['terminal'],
        'task_count': len(context['plan'].tasks),
        'task_receipts': {key: _pin(value, 'receipt_id') for key, value in products['receipts'].items()},
        'attempt_receipts': {key: _pin(value, 'receipt_id') for key, value in products.get('attempt_receipts', {}).items()},
        'recovery_events': products.get('recovery_events', {}),
        'operational_census': products['operational_census'], 'dispositions': products['dispositions']}


def _case_custody(custody):
    return {phase: {'receipt': _pin(receipt, 'receipt_id'), 'record': publication.logical}
            for phase, (receipt, publication) in custody.items()}


def _original_read(directory, writer, consume):
    from empirical_lawhood.api.selected_e3_access import original_e3_authority_read_context
    from empirical_lawhood.api.matrix_selected_e3_e4_read import read_selected_e3_e4_development
    with original_e3_authority_read_context(writer), writer.read_context() as reading:
        report = read_selected_e3_e4_development(directory=directory, artifact_writer=reading,
            allow_partial=False, _consume_original=consume)
        reading.require_verification_snapshot()
    return report


def run_matrix_retained_refresh(*, original_directory, output_directory, project_root, artifact_writer, observe=None):
    """Publish the bound successor protocol, calculate once, and close exact members."""
    from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import evaluate_refresh_case, predict_refresh_case, refresh_case_summary, refresh_work_counts, select_refresh_observations
    from empirical_lawhood.domains.matrix.matrix_factor_response.mechanism_readout import MechanismUnavailable
    start, cpu = perf_counter(), process_time()
    output = preflight_matrix_output_directory(directory=output_directory, artifact_writer=artifact_writer, project_root=project_root)
    provenance = capture_matrix_provenance(project_root=project_root)
    specification = read_bounded_bytes(Path(project_root) / SPECIFICATION_PATH, maximum_bytes=128 * 1024)
    members, summaries, protocol_holder, timings = [], [], [], []

    def consume(**context):
        selected, facts, tasks = _select_original(context)
        protocol = _protocol(context, selected, sha256(specification).hexdigest())
        if protocol_holder:
            raise ValueError('SCI01 cannot merge two original execution consumers')
        protocol_holder.append(protocol)
        output.mkdir(parents=True, exist_ok=False)
        members.append(_member(output, 'protocol.canonical.json', protocol.canonical_bytes(), schema=protocol.SCHEMA))
        members.append(_member(output, 'specification.md', specification, schema=SPECIFICATION_SCHEMA, media='text/markdown'))
        # A durable protocol publication precedes any scientific calculation.
        publish_retained_analysis(directory=output, artifact_writer=artifact_writer,
            completion_id=REFRESH_PROTOCOL_ID + '.protocol-publication', members=tuple(members))
        # The complete calculation has its own disjoint completion namespace.
        calculated = output / 'calculation'
        calculated.mkdir()
        result_members = []
        result_members.append(_member(calculated, 'protocol.canonical.json', protocol.canonical_bytes(), schema=protocol.SCHEMA))
        result_members.append(_member(calculated, 'specification.md', specification, schema=SPECIFICATION_SCHEMA, media='text/markdown'))
        result_members.append(_member(calculated, 'provenance.canonical.json', provenance.canonical_bytes(), schema=provenance.SCHEMA))
        result_members.append(_member(calculated, 'columns.json', _json(refresh_columns()), schema='empirical-lawhood/matrix-sci01/columns'))
        result_members.append(_member(calculated, 'original-custody.json', _json(_original_custody(context)),
            schema='empirical-lawhood/matrix-sci01/original-custody'))
        for binding, response_protocol, records, custody in selected:
            access = context['original_input_access']
            access.require_current()
            case_start, case_cpu = perf_counter(), process_time()
            name = 'case-' + str(binding.case_index).zfill(3)
            case_dir = calculated / name
            case_dir.mkdir()
            summary = {'original_case': binding, 'status': 'NO_ORIGIN', 'new_native_acquisition': 0, 'new_statistical_fits': 0}
            if binding.original_availability == 'FINITE':
                with decoded_matrix_array_scope():
                    causal, frozen, received = (_arrays(context, binding, phase, records[phase].arrays, facts, tasks)
                        for phase in ('project', 'mechanical', 'responses'))
                    observations = select_refresh_observations(response_protocol, received, panel_ids=binding.panel_ids)
                    cost_rows = []
                    try:
                        predicted, constructions = predict_refresh_case(response_protocol, causal, frozen, observations,
                            panel_ids=binding.panel_ids, observe_cost=cost_rows.append)
                        arrays = evaluate_refresh_case(response_protocol, predicted, received,
                            panel_ids=binding.panel_ids, observe_cost=cost_rows.append)
                    except MechanismUnavailable as error:
                        summary = {**summary, 'status': 'CONSTRUCTION_UNAVAILABLE', 'reason': str(error)}
                    else:
                        raw, array_members = encode_matrix_arrays(arrays)
                        artifact = ArtifactIdentity(REFRESH_PROTOCOL_ID + '.' + name + '.arrays', 'sci01-retained-array',
                            MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw))
                        operand = MatrixRefreshArrays(REFRESH_PROTOCOL_ID + '.' + name, protocol.identity, binding, artifact, array_members)
                        _write_new_file(case_dir / 'arrays.npz', raw)
                        result_members.append(RetainedAnalysisMember(name + '/arrays.npz', artifact))
                        result_members.append(_member(calculated, name + '/arrays.canonical.json', operand.canonical_bytes(), schema=operand.SCHEMA))
                        summary = {**refresh_case_summary(arrays, numerical_usable=binding.numerical_usable),
                            'original_case': binding, 'construction': constructions, 'work_counts': refresh_work_counts()}
                        del arrays, predicted, raw
                    timings.extend({'case_index': binding.case_index, **row} for row in cost_rows)
            summary['source_custody'] = _case_custody(custody)
            result_members.append(_member(calculated, name + '/summary.json', _json(summary), schema='empirical-lawhood/matrix-sci01/case-summary'))
            summaries.append(summary)
            timings.append({'case_index': binding.case_index, 'phase': 'complete_case_including_custody_and_publication',
                'wall_seconds': perf_counter() - case_start, 'cpu_seconds': process_time() - case_cpu})
            access.require_current()
            if observe is not None:
                observe({'completed_cases': len(summaries), 'assigned_cases': 144, 'case_index': binding.case_index,
                         'status': summary['status']})
        result_members.append(_member(calculated, 'summary.json', _json({'protocol': protocol.identity,
            'assigned_cases': 144, 'original_usable_cases': 36, 'NO_ORIGIN': 108,
            'assigned_groups': 16, 'usable_independent_groups': 4,
            'new_native_acquisition': 0, 'new_statistical_fits': 0,
            'independent_assessment': 'REQUIRED_SEPARATELY', 'case_statuses': tuple(s['status'] for s in summaries)}),
            schema='empirical-lawhood/matrix-sci01/calculation-summary'))
        result_members.append(_member(calculated, 'costs.json', _json({'observations': timings,
            'wall_seconds_through_calculation': perf_counter() - start,
            'cpu_seconds_through_calculation': process_time() - cpu,
            'original_native_cost': 'NOT_REMEASURED_UNKNOWN_WHERE_ORIGINAL_RECEIPTS_LACK_TIMINGS',
            'prospective_information_is_not_free': True}), schema='empirical-lawhood/matrix-sci01/calculation-cost'))
        if numerical_package_code_sha256() != provenance.code_sources_sha256:
            raise ValueError('SCI01 producing source changed during calculation')
        access.require_current()
        context['writer'].require_verification_snapshot()
        completion = publish_retained_analysis(directory=calculated, artifact_writer=artifact_writer,
            completion_id=REFRESH_PROTOCOL_ID + '.calculation', members=tuple(result_members))
        access.require_current()
        members.append(completion)

    report = _original_read(Path(original_directory), artifact_writer, consume)
    if len(protocol_holder) != 1 or len(summaries) != 144:
        raise ValueError('SCI01 did not consume the complete original case census')
    # A fresh ordinary read verified every original member at the closing boundary.
    return {'output_directory': str(output), 'calculation_directory': str(output / 'calculation'),
        'protocol': _plain(protocol_holder[0].identity), 'original_read': report,
        'status': 'CALCULATION_COMPLETE_INDEPENDENT_READ_REQUIRED', 'new_native_acquisition': 0, 'new_statistical_fits': 0}


def _retained_record(completion, name, kind, directory, writer):
    raw = read_retained_analysis_member(completion, name, directory=directory, artifact_writer=writer,
        maximum_bytes=None)
    return decode_canonical_bytes(raw, kind, maximum_bytes=None)


def read_matrix_retained_refresh(*, original_directory, calculation_directory, assessment_directory,
                                project_root, artifact_writer, observe=None):
    """Reopen original custody and independently assess a completed SCI01 calculation."""
    from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_read import assess_refresh_case, verify_refresh_case
    from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_summary import channel_endpoints, finite_pair_operands, summarize_refresh
    from empirical_lawhood.api.matrix_numerical_provenance import authenticate_recorded_matrix_provenance
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    start, cpu = perf_counter(), process_time()
    output = preflight_matrix_output_directory(directory=assessment_directory, artifact_writer=artifact_writer, project_root=project_root)
    calculation = Path(calculation_directory)
    with artifact_writer.read_context() as reading:
        completion = read_retained_analysis(directory=calculation, artifact_writer=reading)
        protocol = _retained_record(completion, 'protocol.canonical.json', MatrixRefreshProtocol, calculation, reading)
        producing = _retained_record(completion, 'provenance.canonical.json', NumericalProducingProvenance, calculation, reading)
        authenticate_recorded_matrix_provenance(producing)
        specification = read_retained_analysis_member(completion, 'specification.md', directory=calculation,
            artifact_writer=reading, maximum_bytes=128 * 1024)
        if sha256(specification).hexdigest() != protocol.public_specification_sha256:
            raise ValueError('SCI01 calculation changes its published scientific specification')
        declared = read_retained_analysis(directory=calculation.parent, artifact_writer=reading)
        if (_retained_record(declared, 'protocol.canonical.json', MatrixRefreshProtocol, calculation.parent, reading) != protocol
                or read_retained_analysis_member(declared, 'specification.md', directory=calculation.parent,
                    artifact_writer=reading, maximum_bytes=128 * 1024) != specification):
            raise ValueError('SCI01 calculation differs from its prior protocol publication')
        provenance = capture_matrix_provenance(project_root=project_root)
        assessments, metrics, pairs, checks, members = [], [], [], [], []
        output.mkdir(parents=True, exist_ok=False)

        def consume(**context):
            selected, facts, tasks = _select_original(context)
            if _protocol(context, selected, protocol.public_specification_sha256) != protocol:
                raise PermissionError('SCI01 assessment changes the actual original complete source binding')
            for name, expected in (('original-custody.json', _original_custody(context)), ('columns.json', refresh_columns())):
                raw = read_retained_analysis_member(completion, name, directory=calculation,
                    artifact_writer=reading, maximum_bytes=None)
                if json.loads(raw) != _plain(expected):
                    raise ValueError('SCI01 assessment changes its original custody or array meanings')
            required = {'protocol.canonical.json', 'specification.md', 'provenance.canonical.json',
                        'columns.json', 'summary.json', 'costs.json', 'original-custody.json'}
            for binding, response_protocol, records, custody in selected:
                access = context['original_input_access']
                access.require_current()
                name = 'case-' + str(binding.case_index).zfill(3)
                required.add(name + '/summary.json')
                raw = read_retained_analysis_member(completion, name + '/summary.json', directory=calculation,
                    artifact_writer=reading, maximum_bytes=None)
                retained = json.loads(raw)
                if retained['original_case'] != _plain(binding) or retained['source_custody'] != _plain(_case_custody(custody)):
                    raise ValueError('SCI01 case summary changes its original source')
                if binding.original_availability == 'NO_ORIGIN':
                    if retained['status'] != 'NO_ORIGIN':
                        raise ValueError('SCI01 cannot relabel a missing original response')
                    assessments.append(MatrixRefreshCaseAssessment(binding, ()))
                    continue
                if retained['status'] == 'CONSTRUCTION_UNAVAILABLE':
                    # An unavailable calculation remains an unresolved finding, never an admission.
                    # Its reason is retained as producer-reported; this reader supplies no numerical support.
                    assessments.append(MatrixRefreshCaseAssessment(binding, (), 'UNVERIFIED_PRODUCER_FAILURE:' + retained['reason']))
                    continue
                required.update((name + '/arrays.canonical.json', name + '/arrays.npz'))
                operand = _retained_record(completion, name + '/arrays.canonical.json', MatrixRefreshArrays, calculation, reading)
                if operand.protocol != protocol.identity or operand.original_case != binding:
                    raise ValueError('SCI01 calculation substitutes its actual array protocol or case')
                body = read_retained_analysis_member(completion, name + '/arrays.npz', directory=calculation,
                    artifact_writer=reading, maximum_bytes=MAXIMUM_MATRIX_ARRAY_BYTES)
                with decoded_matrix_array_scope():
                    arrays = decode_matrix_arrays(body, operand)
                    causal, frozen, received = (_arrays(context, binding, phase, records[phase].arrays, facts, tasks)
                        for phase in ('project', 'mechanical', 'responses'))
                    case_checks = verify_refresh_case(response_protocol, causal, frozen, received, arrays, binding)
                    assessment = assess_refresh_case(binding, arrays)
                    if assessment.decision != retained['H64_method_decision']:
                        raise ValueError('SCI01 independent decision differs from its reported calculation')
                    for method in assessment.methods:
                        for field in ('primary_curve', 'fine_curve'):
                            actual = tuple(Decimal(str(v)) for v in retained['methods'][method.method][field])
                            if any(abs(a - b) > Decimal('1e-10') for a, b in zip(actual, getattr(method, field), strict=True)):
                                raise ValueError('SCI01 independent error curve differs from its report')
                    assessments.append(assessment)
                    checks.append({'case_index': binding.case_index, 'residuals': case_checks})
                    metrics.extend(channel_endpoints(response_protocol, binding, arrays))
                    pairs.append(finite_pair_operands(response_protocol, binding, arrays))
                access.require_current()
                if observe is not None:
                    observe({'assessed_usable_cases': len(checks), 'usable_cases': 36, 'case_index': binding.case_index})
            if {member.relative_path for member in completion.members} != required:
                raise ValueError('SCI01 calculation changes its closed complete member census')
            decision = MatrixRefreshDecision(REFRESH_PROTOCOL_ID + '.decision', protocol,
                ObjectIdentity.from_record(completion.completion_id, completion), tuple(assessments))
            summary, finite_pairs = summarize_refresh(decision, metrics, pairs)
            members.append(_member(output, 'decision.canonical.json', decision.canonical_bytes(), schema=decision.SCHEMA))
            members.append(_member(output, 'summary.json', _json(summary), schema='empirical-lawhood/matrix-sci01/assessed-summary'))
            members.append(_member(output, 'channel-endpoints.json', _json(metrics), schema='empirical-lawhood/matrix-sci01/channel-endpoints'))
            members.append(_member(output, 'finite-pairs.json', _json(finite_pairs), schema='empirical-lawhood/matrix-sci01/finite-pairs'))
            members.append(_member(output, 'independent-checks.json', _json(checks), schema='empirical-lawhood/matrix-sci01/independent-checks'))
            members.append(_member(output, 'provenance.canonical.json', provenance.canonical_bytes(), schema=provenance.SCHEMA))
            members.append(_member(output, 'costs.json', _json({'wall_seconds_through_assessment': perf_counter() - start,
                'cpu_seconds_through_assessment': process_time() - cpu, 'original_native_calls': 0, 'new_statistical_fits': 0,
                'scope': 'INDEPENDENT_RECONSTRUCTION_CUSTODY_AND_ASSESSMENT_NOT_PROSPECTIVE_METHOD_COST'}),
                schema='empirical-lawhood/matrix-sci01/assessment-cost'))
            if numerical_package_code_sha256() != provenance.code_sources_sha256:
                raise ValueError('SCI01 assessment implementation changed during reconstruction')
            context['original_input_access'].require_current()
            context['writer'].require_verification_snapshot()
            read_retained_analysis(directory=calculation, artifact_writer=reading)
            publish_retained_analysis(directory=output, artifact_writer=artifact_writer,
                completion_id=REFRESH_PROTOCOL_ID + '.assessment', members=tuple(members))
            context['original_input_access'].require_current()

        _original_read(Path(original_directory), reading, consume)
        read_retained_analysis(directory=calculation, artifact_writer=reading)
        reading.require_verification_snapshot()
    return {'assessment_directory': str(output), 'assigned_cases': 144, 'original_usable_cases': 36,
        'NO_ORIGIN': 108, 'usable_independent_groups': 4, 'status': 'INDEPENDENT_ASSESSMENT_COMPLETE',
        'decision_counts': _plain(decision_counts(assessments)), 'new_native_acquisition': 0, 'new_statistical_fits': 0}


def decision_counts(assessments):
    from collections import Counter
    return tuple(sorted(Counter(row.decision for row in assessments).items()))
