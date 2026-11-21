# SPDX-License-Identifier: MPL-2.0
"""Export and analyse closed E4/SCI01 evidence with current original access.

This route reuses the original custody consumer and the existing bounded array
transport. It has no source provider, native execution or basis-construction path.
"""

from hashlib import sha256
from pathlib import Path
from time import perf_counter, process_time
import csv
import io
import json

import numpy as np

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_matched import census, matched_reversal_rows, representation_summary, join_native_errors
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_matched_records import ANALYSES, MATCHED_PROTOCOL_ID, MatrixMatchedArrays, MatrixMatchedProtocol
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import MatrixRefreshArrays, MatrixRefreshDecision, MatrixRefreshProtocol
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_representation import case_representation, paired_representation_rows
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_summary import _finite_pairs, finite_pair_operands
from empirical_lawhood.api.configuration import _write_new_file
from empirical_lawhood.api.matrix_numerical_provenance import authenticate_recorded_matrix_provenance, capture_matrix_provenance, numerical_package_code_sha256, preflight_matrix_output_directory
from empirical_lawhood.api.matrix_retained_refresh import _json, _original_read, _protocol, _retained_record, _select_original
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays, decoded_matrix_array_scope, encode_matrix_arrays
from empirical_lawhood.storage.retained_analysis import publish_retained_analysis, read_retained_analysis, read_retained_analysis_member
from empirical_lawhood.domains.matrix.input_contracts import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.execution.retained_analysis import RetainedAnalysisMember


SPECIFICATION_PATH = 'programmes/foundations/emergent-structure/records/matrix-sci01-matched-accounting-v1.md'


def _identity(record):
    return ObjectIdentity.from_record(record.completion_id, record)


def _member(output, name, raw, schema='empirical-lawhood/matrix-sci01/matched-export', media='application/json'):
    _write_new_file(output / name, raw)
    return RetainedAnalysisMember(name, ArtifactIdentity(MATCHED_PROTOCOL_ID + '.' + name.replace('/', '.'),
        'sci01-matched-member', schema, sha256(raw).hexdigest(), media, len(raw)))


def _csv(rows):
    # Complete signed vectors live in JSON; CSV retains each scalar and exact cell key.
    columns = sorted({k for row in rows for k, v in row.items() if not isinstance(v, (list, tuple, dict))})
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows({k: v for k, v in row.items() if k in columns} for row in rows)
    return stream.getvalue().encode()


def _inputs(arrays):
    """Exact retained operators, bases, instruments, states and raw native endpoints."""
    names = {'forces', 'receivers', 'scales'}
    for name in arrays:
        if (name.endswith(('.h0', '.h32', '.state_ticks', '.native.phase.endpoints',
                           '.checkpoint.position', '.checkpoint.alpha'))
                or '.basis.' in name or '.state.' in name):
            names.add(name)
    return {'input.' + name: arrays[name] for name in sorted(names)}






def run_matrix_refresh_matched(*, original_directory, calculation_directory, assessment_directory,
                               output_directory, project_root, artifact_writer, observe=None):
    """Publish the separate protocol, export retained arrays, verify and close three analyses."""
    start, cpu = perf_counter(), process_time()
    output = preflight_matrix_output_directory(directory=output_directory, artifact_writer=artifact_writer, project_root=project_root)
    calculation, assessment = Path(calculation_directory), Path(assessment_directory)
    specification = read_bounded_bytes(Path(project_root) / SPECIFICATION_PATH, maximum_bytes=128 * 1024)
    result_holder = []
    with artifact_writer.read_context() as reading:
        calc = read_retained_analysis(directory=calculation, artifact_writer=reading)
        assessed = read_retained_analysis(directory=assessment, artifact_writer=reading)
        original_protocol = _retained_record(calc, 'protocol.canonical.json', MatrixRefreshProtocol, calculation, reading)
        decision = _retained_record(assessed, 'decision.canonical.json', MatrixRefreshDecision, assessment, reading)
        if decision.protocol != original_protocol or decision.calculation_completion != _identity(calc):
            raise ValueError('Matched SCI01 requires the assessment of this exact calculation')
        for directory, completion in ((calculation, calc), (assessment, assessed)):
            authenticate_recorded_matrix_provenance(_retained_record(completion, 'provenance.canonical.json',
                NumericalProducingProvenance, directory, reading))
        original_spec = read_retained_analysis_member(calc, 'specification.md', directory=calculation,
            artifact_writer=reading, maximum_bytes=128 * 1024)
        if sha256(original_spec).hexdigest() != original_protocol.public_specification_sha256:
            raise ValueError('Matched SCI01 changes the original scientific specification')
        declaration = read_retained_analysis(directory=calculation.parent, artifact_writer=reading)
        if _retained_record(declaration, 'protocol.canonical.json', MatrixRefreshProtocol, calculation.parent, reading) != original_protocol:
            raise ValueError('Matched SCI01 loses the original prior protocol publication')
        prior_pairs_raw = read_retained_analysis_member(assessed, 'finite-pairs.json', directory=assessment,
            artifact_writer=reading, maximum_bytes=None)
        prior_pairs = json.loads(prior_pairs_raw)
        protocol = MatrixMatchedProtocol(original_protocol, _identity(calc), _identity(assessed), sha256(specification).hexdigest())
        provenance = capture_matrix_provenance(project_root=project_root)

        def consume(**context):
            selected, _, _ = _select_original(context)
            if _protocol(context, selected, original_protocol.public_specification_sha256) != original_protocol:
                raise PermissionError('Matched SCI01 changes actual original source, access or complete census')
            access = context['original_input_access']
            access.require_current()
            output.mkdir(parents=True, exist_ok=False)
            declared_members = (
                _member(output, 'protocol.canonical.json', protocol.canonical_bytes(), protocol.SCHEMA),
                _member(output, 'specification.md', specification, media='text/markdown'))
            publish_retained_analysis(directory=output, artifact_writer=artifact_writer,
                completion_id=MATCHED_PROTOCOL_ID + '.protocol-publication', members=declared_members)
            destination = output / 'analysis'
            destination.mkdir()
            members = [_member(destination, 'protocol.canonical.json', protocol.canonical_bytes(), protocol.SCHEMA),
                       _member(destination, 'specification.md', specification, media='text/markdown'),
                       _member(destination, 'provenance.canonical.json', provenance.canonical_bytes(), provenance.SCHEMA),
                       _member(destination, 'source-finite-pairs.json', prior_pairs_raw)]
            operands, representations, checks, export_index = [], {}, [], []
            assessments = {r.original_case.case_index: r for r in decision.cases}
            for binding, response_protocol, _, _ in selected:
                access.require_current()
                if not assessments[binding.case_index].methods:
                    continue
                name = 'case-' + str(binding.case_index).zfill(3)
                operand = _retained_record(calc, name + '/arrays.canonical.json', MatrixRefreshArrays, calculation, reading)
                if operand.original_case != binding or operand.protocol != original_protocol.identity:
                    raise ValueError('Matched SCI01 substitutes its retained array operands')
                body = read_retained_analysis_member(calc, name + '/arrays.npz', directory=calculation,
                    artifact_writer=reading, maximum_bytes=MAXIMUM_MATRIX_ARRAY_BYTES)
                with decoded_matrix_array_scope():
                    arrays = decode_matrix_arrays(body, operand)
                    operands.append(finite_pair_operands(response_protocol, binding, arrays))
                    represented, exported, case_checks = case_representation(response_protocol, binding, arrays)
                    # These compact arrays survive the decoded scope as owned copies.
                    represented['scales'] = represented['scales'].copy()
                    represented['receivers'] = represented['receivers'].copy()
                    representations[binding.case_index] = represented
                    checks.extend(case_checks)
                    raw, array_members = encode_matrix_arrays({**_inputs(arrays), **exported})
                    (destination / name).mkdir()
                    array_member = _member(destination, name + '/arrays.npz', raw, MATRIX_ARRAY_SCHEMA, 'application/x-npz')
                    typed = MatrixMatchedArrays(MATCHED_PROTOCOL_ID + '.' + name, protocol.identity, binding,
                        ObjectIdentity.from_record(operand.operand_id, operand), array_member.artifact, array_members)
                    # Decode our export through the same bounded contracts before committing it.
                    reopened = decode_matrix_arrays(raw, typed)
                    for key, value in _inputs(arrays).items():
                        if not np.array_equal(reopened[key], value):
                            raise ValueError('Matched SCI01 export changes retained input bytes')
                    members.extend((array_member, _member(destination, name + '/arrays.canonical.json', typed.canonical_bytes(), typed.SCHEMA)))
                    export_index.append({'case_index': binding.case_index, 'source_arrays': typed.source_arrays,
                        'array_record': name + '/arrays.canonical.json', 'arrays': name + '/arrays.npz',
                        'action_order': tuple({'index': i, 'action_id': action.action_id, 'role': action.role}
                                              for i, action in enumerate(response_protocol.actions)),
                        'panel_order': binding.panel_ids,
                        'views': {view: {'timestep': getattr(response_protocol.public_source.coordinate, view + '_view').timestep,
                                        'friction': getattr(response_protocol.public_source.coordinate, view + '_view').friction_gamma}
                                  for view in ('primary', 'fine')}})
                access.require_current()
                if observe:
                    observe({'exported_cases': len(operands), 'case_index': binding.case_index})
            regenerated_pairs = _finite_pairs(decision, operands)
            if _json(regenerated_pairs) != _json(prior_pairs):
                raise ValueError('Matched SCI01 does not reproduce the originally assessed common-receiver vectors')
            matched, unavailable = matched_reversal_rows(regenerated_pairs, decision.cases)
            represented_rows = paired_representation_rows(matched, representations)
            native_join = join_native_errors(matched, represented_rows)
            summary = {
                'analyses': ANALYSES, 'protocol': protocol.identity, 'assigned_cases': len(decision.cases),
                'original_usable_cases': len(operands), 'NO_ORIGIN': sum(r.original_case.original_availability == 'NO_ORIGIN' for r in decision.cases),
                'assigned_pairs': len({(r['low_case'], r['high_case']) for r in regenerated_pairs}),
                'usable_pairs': len({(r['low_case'], r['high_case']) for r in matched}),
                'unavailable_pairs': len({(r['low_case'], r['high_case']) for r in unavailable}),
                'assigned_groups': len({r.original_case.group_id for r in decision.cases}),
                'usable_independent_groups': len({r['group_id'] for r in matched}),
                'matched_cells': len(matched), 'representation_rows': len(represented_rows),
                'by_method_horizon': census(matched, ('horizon', 'comparison')),
                'by_group': census(matched, ('horizon', 'comparison', 'group_id')),
                'by_channel': census(matched, ('horizon', 'comparison', 'action', 'block')),
                'by_group_channel': census(matched, ('horizon', 'comparison', 'group_id', 'action', 'block')),
                'by_view_panel': census(matched, ('horizon', 'comparison', 'group_id', 'view', 'panel_id')),
                'representation_by_group': representation_summary(represented_rows, ('horizon', 'regime', 'group_id')),
                'representation_by_channel': representation_summary(represented_rows, ('horizon', 'regime', 'action', 'block')),
                'maximum_native_representation_join_residual': native_join,
                'maximum_normalized_state_reconstruction_residual': max((r['maximum_normalized_residual'] for r in checks), default=None),
                'maximum_alignment_identity_residual': max((abs(r['alignment_change_residual']) for r in matched), default=None),
                'new_native_acquisition': 0, 'new_statistical_fits': 0, 'new_bases': 0, 'additional_updates': 0,
                'independence': 'FOUR_GROUPS_COORDINATES_PANELS_ACTIONS_VIEWS_AND_TIMES_ARE_NESTED',
                'scope': 'DESCRIPTIVE_RETAINED_EVIDENCE_NO_MOLECULAR_ADMISSION'}
            source_bindings = {'calculation_directory': str(calculation), 'assessment_directory': str(assessment),
                'original_directory': str(original_directory), 'calculation_completion': _identity(calc),
                'assessment_completion': _identity(assessed), 'decision': decision.identity,
                'array_exports': export_index,
                'array_axes': {'saved_states': ('action', 'origin_checkpoint32_H64_H128', 'q_then_p_in_retained_basis'),
                    'native_endpoints': ('action', 'H64_H128', 'native_q96_then_p96'),
                    'representation_terms': ('action', 'native_q96_then_p96'),
                    'receivers': 'Original complex receiver tensors; common receiver is the nominal case in each group',
                    'scales': ('action', 'PRIMARY_tick_1_to_128', 'q_p'),
                    'maps': {'m': 'full BAOAB', 'r': 'BAOAB composed after Hessian projection', 'l': 'diag(U,U)',
                             'defect': 'M L - L R', 'd_checkpoint': 'full minus lifted reduced at the checkpoint'},
                    'input_prefix': 'Exact copies of the named retained calculation arrays'},
                'original_costs': 'Exact original cost files copied; no cost is remeasured or assigned zero.'}
            for name, data in (('matched-cells.json', matched), ('representation.json', represented_rows),
                    ('unavailable-pairs.json', unavailable), ('summary.json', summary),
                    ('source-bindings.json', source_bindings), ('independent-checks.json', checks)):
                members.append(_member(destination, name, _json(data)))
            for name, rows in (('matched-cells.csv', matched), ('representation.csv', represented_rows)):
                members.append(_member(destination, name, _csv(rows), media='text/csv'))
            for label, directory, completion in (('calculation', calculation, calc), ('assessment', assessment, assessed)):
                raw = read_retained_analysis_member(completion, 'costs.json', directory=directory,
                    artifact_writer=reading, maximum_bytes=None)
                members.append(_member(destination, 'original-' + label + '-costs.json', raw))
            from empirical_lawhood.api.matrix_refresh_matched_report import render_report
            members.append(_member(destination, 'report.html', render_report(summary, matched, represented_rows), media='text/html'))
            members.append(_member(destination, 'costs.json', _json({'wall_seconds_through_analysis': perf_counter() - start,
                'cpu_seconds_through_analysis': process_time() - cpu, 'new_native_acquisition': 0, 'new_statistical_fits': 0,
                'scope': 'EXPORT_AND_THREE_RETAINED_ANALYSES_WITH_ORIGINAL_CUSTODY_NOT_PROSPECTIVE_METHOD_COST'})))
            if numerical_package_code_sha256() != provenance.code_sources_sha256:
                raise ValueError('Matched SCI01 source changed during the analysis')
            access.require_current()
            context['writer'].require_verification_snapshot()
            for directory in (calculation, assessment):
                read_retained_analysis(directory=directory, artifact_writer=reading)
            publish_retained_analysis(directory=destination, artifact_writer=artifact_writer,
                completion_id=MATCHED_PROTOCOL_ID + '.analysis', members=tuple(members))
            access.require_current()
            result_holder.append({'status': 'THREE_RETAINED_ANALYSES_COMPLETE', 'analysis_directory': str(destination),
                'matched_cells': len(matched), 'unavailable_pairs': len(unavailable), 'new_native_acquisition': 0})

        _original_read(Path(original_directory), reading, consume)
        reading.require_verification_snapshot()
    if len(result_holder) != 1:
        raise ValueError('Matched SCI01 requires exactly one complete original source')
    return result_holder[0]
