# SPDX-License-Identifier: MPL-2.0
"""Bounded process reproof over disclosed values; no grants or native work."""

from hashlib import sha256
import os
from pathlib import Path
import time
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.api.matrix_retained_replay import replay_e4_functional
from empirical_lawhood.infrastructure.parallel_verification import CanonicalValidationPool
from empirical_lawhood.infrastructure import matrix_array_io as arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity


def _weighted(value):
    index, directory = value
    started = time.monotonic()
    if index < 2:
        path = Path(directory)
        (path / str(index)).write_text(str(os.getpid()))
        deadline = started + 20
        while len(tuple(path.iterdir())) < 2:
            if time.monotonic() > deadline:
                raise AssertionError('two admitted jobs failed to overlap')
            time.sleep(.01)
    time.sleep(.02)
    return index, os.getpid(), started, time.monotonic()


def test_weighted_pool_bounds_concurrent_work_and_runs_large_case_without_copy(tmp_path):
    pool = CanonicalValidationPool(8)
    try:
        values = [(n, str(tmp_path)) for n in range(6)]
        result = pool.project_ordered(_weighted, values,
            weight=lambda value: 21 if value[0] == 3 else 10, maximum_pending_bytes=20)
        assert [row[0] for row in result] == list(range(6))
        assert result[3][1] == os.getpid()
        assert all(row[1] != os.getpid() for row in result if row[0] != 3)
        events = sorted((at, delta) for _, _, start, stop in result for at, delta in ((start, 1), (stop, -1)))
        active = peak = 0
        for _, delta in events:
            active += delta
            peak = max(peak, active)
        assert peak == 2 and active == 0
    finally:
        pool.close()
    with pytest.raises(RuntimeError, match='ended'):
        pool.project_ordered(_weighted, values[:1], weight=lambda _: 21, maximum_pending_bytes=20)


def _operand(index):
    raw, members = arrays.encode_matrix_arrays({'values': np.arange(8, dtype='<f8') + index})
    manifest = arrays.NPZMemberSelection(ArtifactIdentity('array.replay-' + str(index), 'software-replay-control',
        MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw)), members)
    return raw, manifest


@pytest.mark.parametrize('damage', (None, 'mechanical', 'dense', 'score'))
def test_functional_worker_keeps_each_numerical_join_and_reuses_case_arrays(monkeypatch, damage):
    """Disclosed math seams isolate dispatch; physical NPZ decoding is real."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
        response_forecast, response_science, selected_e3_e4_science,
    )
    from empirical_lawhood.api import matrix_mechanism_read
    operands = [_operand(n) for n in range(6)]
    template, causal, physical, dense, response, witness = [SimpleNamespace(arrays=value[1]) for value in operands]
    physical.forecast_id = 'forecast.exposed'; dense.forecast_id = 'forecast.dense-exposed'
    protocol = SimpleNamespace(templates=template.arrays, public_source=object())
    account = SimpleNamespace(feature=SimpleNamespace(physical_forecast=object()))
    score = SimpleNamespace(numerical_pass=True); dense_score = SimpleNamespace(score_id='score.exposed')
    case = SimpleNamespace(root_id='root.exposed', group_id='group.exposed', source=object())
    row = ('complete', case.root_id)
    data = dict(case=case, protocol=protocol, panels=(), score=score, account=account, causal=causal,
        physical=physical, dense=dense, responses=response, witness=witness, is_protected=False,
        target=object(), secondary=object(), source=object(), dense_score=dense_score, design=object(),
        include_mechanism=True, row=row, **dict(zip(
            ('template_raw','causal_raw','original_raw','dense_raw','response_raw','diagnostic_raw'),
            (value[0] for value in operands), strict=True)))
    calls, decodes = [], []
    original_decode = arrays._decode_matrix_arrays
    def decode(raw, manifest):
        decodes.append(manifest.array_artifact.artifact_id)
        return original_decode(raw, manifest)
    monkeypatch.setattr(arrays, '_decode_matrix_arrays', decode)
    def mechanical(actual_protocol, actual_causal, causal_values, template_values, **kwargs):
        assert actual_protocol is protocol and actual_causal is causal
        assert kwargs['raw'] is data['original_raw']
        calls.append('mechanical')
        return None, object() if damage == 'mechanical' else physical
    def dense_forecast(*args, **kwargs):
        assert kwargs['original_physical'] is physical and kwargs['secondary'] is data['secondary']
        calls.append('dense')
        return None, object() if damage == 'dense' else dense
    def scoring(source, actual_protocol, panels, **kwargs):
        assert source is data['source'] and actual_protocol is protocol and kwargs['original_score'] is score
        for name, manifest in (('original_forecast_raw',physical.arrays),('dense_forecast_raw',dense.arrays),
                ('response_raw',response.arrays)):
            arrays.decode_matrix_arrays(kwargs[name],manifest)
        calls.append('score')
        return object() if damage == 'score' else dense_score
    def validate(*args, **kwargs):
        assert args[0] is account and kwargs['physical'] is physical
        calls.append('account')
    monkeypatch.setattr(selected_e3_e4_science, 'mechanical', mechanical)
    monkeypatch.setattr(response_forecast, 'forecast_e4_dense', dense_forecast)
    monkeypatch.setattr(response_science, 'score_e4_dense', scoring)
    monkeypatch.setattr(selected_e3_e4_science, 'validate_selected_account', validate)
    monkeypatch.setattr(matrix_mechanism_read, 'bound_mechanism', lambda **kwargs: {'root':kwargs['subject_id']})
    if damage is None:
        assert replay_e4_functional((1,data)) == (row,{'root':case.root_id})
        assert calls == ['mechanical','dense','score','account']
        assert len(decodes) == len(set(decodes)) == 6
    else:
        with pytest.raises(PermissionError, match='cold replay'):
            replay_e4_functional((1,data))
        assert 'account' not in calls


def test_missing_functional_case_is_retained_in_parallel():
    data = dict(case=SimpleNamespace(root_id='root.missing',group_id='group.missing'),
        protocol=None,panels=(),score=None,account=None,causal=None,physical=None,
        include_mechanism=True,row=('UNEVALUABLE','root.missing'))
    pool = CanonicalValidationPool(2)
    try:
        result = pool.project_ordered(replay_e4_functional, ((1,data),(1,data)))
        assert result == ((data['row'],{'subject_id':'root.missing','group_id':'group.missing',
            'status':'MISSING_ORIGINAL_SCORE_OR_SEALED_ACCOUNT'}),)*2
    finally:
        pool.close()
