# SPDX-License-Identifier: MPL-2.0
"""Bounded independent mathematical reproof; custody stays in the controller."""

from contextlib import contextmanager

from empirical_lawhood.infrastructure.matrix_array_io import decoded_matrix_array_scope
from empirical_lawhood.kernel.decoded_record_store import decoded_record_scope
from empirical_lawhood.kernel.decoding import record_validation_scope


# Additional concurrent operands, including conservative expansion/workspace
# and Python-record allowances. Oversized single cases retain the serial path.
MAXIMUM_PENDING_REPLAY_BYTES = 512 * 1024**2


def bounded_e4_replay_source(source):
    """Use the existing local carrier, never pickle the full source index."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import (
        SelectedE3E4NativeSource, SelectedE3E4NativeSourceReference,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import (
        SelectedE4ProtectedNativeSource, SelectedE4ProtectedNativeSourceReference,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source

    kinds = {SelectedE3E4NativeSource: SelectedE3E4NativeSourceReference,
        SelectedE4ProtectedNativeSource: SelectedE4ProtectedNativeSourceReference}
    if type(source) not in kinds:
        raise TypeError('E4 replay requires its authenticated local native source')
    transport = kinds[type(source)](*(getattr(source, name) for name in (
        'record_id', 'programme', 'bank', 'descriptor', 'public', 'policy', 'numerical_design')),
        source.provenance.identity, source.provenance.canonical_size_bytes())
    return bind_selected_native_source(transport, source.provenance)


def replay_weight(*, records, archives):
    return (16 * 1024**2 + 8 * sum(record.canonical_size_bytes() for record in records if record is not None)
        + sum(2 * len(raw) + 4 * sum(member.size_bytes for member in manifest.members)
            for raw, manifest in archives if raw is not None))


def map_reconstructions(writer, function, inputs):
    """Keep original order and all outcomes; transfer no paths or access state."""
    pool = getattr(getattr(writer, '_read_verification', None), 'canonical_pool', None)
    if pool is None:
        return tuple(function(value) for value in inputs)
    return pool.project_ordered(function, inputs, weight=lambda value: value[0],
        maximum_pending_bytes=MAXIMUM_PENDING_REPLAY_BYTES)


@contextmanager
def _replay_scope():
    with decoded_record_scope(), record_validation_scope(), decoded_matrix_array_scope():
        yield


def replay_e1(value):
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_science
    _, (source, history, numerical, product, assessment, native, diagnostics, receipts) = value
    with _replay_scope():
        compact_science.read_retained(source, history, numerical, product, assessment, native, diagnostics,
            receipts=receipts)
    return source.root_id


def replay_full_factor(value):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_science
    _, (source, product, assessment, native, diagnostics) = value
    with _replay_scope():
        full_factor_science.read_retained(source, product, assessment, native, diagnostics)
    return source.root_id


def replay_e4_functional(value):
    """Reprove one case's unchanged forecast, score and sealed account."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
        response_forecast, response_science, selected_e3_e4_science, selected_e4_native_science,
    )
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    from .matrix_mechanism_read import bound_mechanism
    _, data = value
    case, protocol, panels = (data[name] for name in ('case', 'protocol', 'panels'))
    score, account, causal, physical = (data[name] for name in ('score', 'account', 'causal', 'physical'))
    mechanism = None
    with _replay_scope():
        if score is not None:
            dense, responses = data['dense'], data['responses']
            causal_arrays = decode_matrix_arrays(data['causal_raw'], causal.arrays)
            original_arrays = decode_matrix_arrays(data['original_raw'], physical.arrays)
            templates = decode_matrix_arrays(data['template_raw'], protocol.templates)
            method = selected_e4_native_science if data['is_protected'] else selected_e3_e4_science
            _, checked = method.mechanical(protocol, causal, causal_arrays, templates,
                artifact_id=physical.arrays.array_artifact.artifact_id,
                retained=original_arrays, raw=data['original_raw'])
            if checked != physical:
                raise PermissionError('dense E4 cold replay changes the original sealed mechanical forecast')
            _, checked_dense = response_forecast.forecast_e4_dense(protocol, causal, causal_arrays, templates,
                target=data['target'], secondary=data['secondary'], original_physical=physical,
                original_forecast_raw=data['original_raw'], artifact_id=dense.arrays.array_artifact.artifact_id,
                forecast_id=dense.forecast_id, retained=decode_matrix_arrays(data['dense_raw'], dense.arrays),
                raw=data['dense_raw'])
            if checked_dense != dense:
                raise PermissionError('dense E4 cold replay changes the sealed supplementary forecast')
            checked_score = response_science.score_e4_dense(data['source'], protocol, panels,
                target=data['target'], secondary=data['secondary'], original_score=score,
                original_physical=physical, dense_physical=dense, responses=responses,
                original_forecast_raw=data['original_raw'], dense_forecast_raw=data['dense_raw'],
                response_raw=data['response_raw'], score_id=data['dense_score'].score_id)
            if checked_score != data['dense_score']:
                raise PermissionError('dense E4 cold replay differs from the actual scored archive')
        if account is not None and account.feature.physical_forecast is not None:
            if score is None:
                causal_arrays = decode_matrix_arrays(data['causal_raw'], causal.arrays)
                original_arrays = decode_matrix_arrays(data['original_raw'], physical.arrays)
            diagnostics = decode_matrix_arrays(data['diagnostic_raw'], data['witness'].arrays)
            selected_e3_e4_science.validate_selected_account(account, data['design'], protocol.public_source,
                causal, data['witness'], causal_arrays, diagnostics, protocol=protocol,
                physical=physical, frozen_arrays=original_arrays, physical_kind=type(physical))
        if data['include_mechanism']:
            if score is None or account is None:
                mechanism = {'subject_id': case.root_id, 'group_id': case.group_id,
                    'status': 'MISSING_ORIGINAL_SCORE_OR_SEALED_ACCOUNT'}
            else:
                mechanism = bound_mechanism(protocol=protocol, source=case.source, causal_record=causal,
                    physical_record=physical, response_record=data['responses'], causal_arrays=causal_arrays,
                    frozen_arrays=original_arrays,
                    response_arrays=decode_matrix_arrays(data['response_raw'], data['responses'].arrays),
                    panels=panels, numerical_status='SATISFIED' if score.numerical_pass else 'UNEVALUABLE',
                    feature=account.feature, score=score, subject_id=case.root_id, group_id=case.group_id)
    return data['row'], mechanism
