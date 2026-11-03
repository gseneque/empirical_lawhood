# SPDX-License-Identifier: MPL-2.0
"""Eight-process projection over exposed records; no scientific authority."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal as D, getcontext, localcontext
from hashlib import sha256
import os
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.selected_e4_case_projection import _project_score, original_score_projections
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.infrastructure.parallel_verification import CanonicalValidationPool, canonical_validation_scope
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_dense_response_measurements import assay, impulse, measure  # noqa: F401


def _overlap(value):
    """Disk barrier proves all eight processes exist before any completes."""
    index, directory = value
    path = Path(directory)
    (path / str(index)).write_text(str(os.getpid()))
    deadline = time.monotonic() + 20
    while len(tuple(path.iterdir())) < 8:
        if time.monotonic() > deadline:
            raise AssertionError('eight projection processes did not overlap')
        time.sleep(.01)
    time.sleep((8 - index) * .01)
    return index, os.getpid(), getcontext().prec


def _fail(value):
    if value == 0:
        raise ValueError('exposed projection refusal')
    return value


def test_eight_processes_return_fixed_order_and_preserve_decimal_context(tmp_path):
    pool = CanonicalValidationPool(8)
    try:
        with localcontext() as context:
            context.prec = 73
            result = pool.project_ordered(_overlap, ((index, str(tmp_path)) for index in range(8)))
        assert tuple(row[0] for row in result) == tuple(range(8))
        assert len({row[1] for row in result}) == 8
        assert all(row[1] != os.getpid() and row[2] == 73 for row in result)
        assert len(pool.worker_pids) == pool.projected_records == 8
    finally:
        pool.close()
    with pytest.raises(RuntimeError, match='ended'):
        pool.project_ordered(_fail, (1,))


def test_projection_refusal_stops_input_consumption_and_releases_pool():
    consumed = []
    def values():
        for value in range(100):
            consumed.append(value)
            yield value
    pool = CanonicalValidationPool(8)
    try:
        with pytest.raises(ValueError, match='refusal'):
            pool.project_ordered(_fail, values())
        assert consumed == list(range(8))
        assert pool.project_ordered(_fail, (1, 2)) == (1, 2)
    finally:
        pool.close()


def test_scheduler_scope_shares_existing_capacity_without_owning_its_shutdown():
    with canonical_validation_scope(8) as original:
        def task():
            with canonical_validation_scope(8, shared_pool=original) as borrowed:
                with canonical_validation_scope(1) as independent_custody:
                    assert borrowed is independent_custody is original
                    return independent_custody.project_ordered(_fail, (1,))
        with ThreadPoolExecutor(max_workers=2) as threads:
            assert tuple(threads.map(lambda _: task(), range(2))) == ((1,), (1,))
        assert original.project_ordered(_fail, (2,)) == (2,)
        assert len(original.worker_pids) <= 8


def _matched_record(operands, *, available):
    protocol, panels, *_ = operands
    for panel, role in zip(panels, ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE'), strict=True):
        panel.role = role
    source = ObjectIdentity('exposed.source', 'empirical-lawhood/testing/source', '1.0.0', 'a' * 64)
    protocol.criterion = source
    protocol.native_reference_tolerance = D('.01')
    protocol.public_source = SimpleNamespace(source=source,
        root=SimpleNamespace(root_id='exposed.root', independent_group_id='exposed.group'),
        coordinate=SimpleNamespace(primary_view=SimpleNamespace(timestep=D('.001'))))
    impulse(operands, tick=16, magnitude=1e-6)
    cells, dense = measure(operands, available=available, numerical_usable=available)
    controls = []
    for branch, view, *_ in r.branch_census(protocol, panels):
        steps = (1 if view == 'PRIMARY' else 2) * 128
        controls.append(ScheduledResponseTransitionControl('control.scheduled.exposed.root.' + branch,
            'SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS', D(0), D('.01'),
            'SATISFIED', steps, 192, (D(0),) * steps, ()))
    score = r.ScheduledResponseScore('score.exposed.root', source, source, source, source, source,
        'exposed.root', 'exposed.group', 'DEVELOPMENT', source, tuple(controls) if available else (),
        available, 'FINITE' if available else 'NO_ORIGIN', cells, dense.factor_log_targets, (), dense)
    raw = score.canonical_bytes()
    return (raw, sha256(raw).hexdigest()), protocol, panels, score.root_id


@pytest.mark.parametrize('available', (True, False))
def test_actual_matched_case_projection_is_byte_identical_and_compact(assay, available, record_property):  # noqa: F811
    value = _matched_record(assay, available=available)
    serial = _project_score(value)
    pool = CanonicalValidationPool(8)
    try:
        values = tuple(value if index != 3 else (None, *value[1:]) for index in range(10))
        results = pool.project_ordered(_project_score, values)
        assert results[3] is None
        assert all(result is None or result.canonical_bytes() == serial.canonical_bytes() for result in results)
        assert len(pool.worker_pids) == 8
        assert serial.target_contract == 'MATCHED_FACTOR58' and len(serial.paired_log_targets) == 58
        assert serial.disposition == ('FINITE' if available else 'NO_ORIGIN')
        assert len(serial.canonical_bytes()) < len(value[0][0]) // 10
        for raw, digest in ((value[0][0] + b' ', value[0][1]), (value[0][0], 'f' * 64)):
            with pytest.raises(ValueError):
                pool.project_ordered(_project_score, (((raw, digest), *value[1:]),))
        record_property('projection', dict(input_bytes=len(value[0][0]), output_bytes=len(serial.canonical_bytes()),
            processes=len(pool.worker_pids), disposition=serial.disposition, original_cells=3248))
    finally:
        pool.close()


def test_controller_retains_current_access_before_returning_projection(monkeypatch):
    """Disclosed payload seam isolates the parent-side final access check."""
    import empirical_lawhood.api.selected_e4_case_projection as owner
    reads = []
    access = SimpleNamespace(require_current=lambda: reads.append('current'))
    monkeypatch.setattr(owner, '_record_bytes', lambda *args, **kwargs: None)
    case = SimpleNamespace(root_id='exposed.case')
    bank = SimpleNamespace(source_index=lambda: {}, source=lambda *args, **kwargs: None,
        response_selection=SimpleNamespace(validate_source=lambda source: (None, None)))
    assert original_score_projections(writer=None, products={'product_index':()}, programme=SimpleNamespace(cases=(case,)),
        bank=bank, original_input_access=access) == (None,)
    assert reads == ['current']
    def revoked():
        raise PermissionError('original access revoked')
    access.require_current = revoked
    with pytest.raises(PermissionError, match='revoked'):
        original_score_projections(writer=None, products={'product_index':()}, programme=SimpleNamespace(cases=(case,)),
            bank=bank, original_input_access=access)
