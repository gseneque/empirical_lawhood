# SPDX-License-Identifier: MPL-2.0
"""Bounded concurrent byte checks within one live custody operation."""
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from decimal import getcontext, localcontext
from multiprocessing import get_context
import os
from threading import BoundedSemaphore, Lock
from time import process_time
from types import SimpleNamespace

in_parallel_verification = ContextVar('in_parallel_artifact_verification', default=False)
canonical_validation_pool = ContextVar('canonical_validation_pool', default=None)
_canonical_scope_pool = ContextVar('canonical_scope_pool', default=None)


def _initialize_metadata_worker():
    # Set this before the worker imports the validator's numerical dependencies.
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
                 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'


def _descriptor_identity(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _validate_canonical_descriptor(parent_pid, descriptor, identity, schema, semantics, limits):
    """Inspect only a caller-opened descriptor. No paths, grants or providers."""
    from .artifact_validation import _inspect_canonical_json_file
    started = process_time()
    # The controller holds this FD open until the result returns. Opening its
    # proc descriptor avoids filesystem socket-name limits in selected deep
    # temporary directories, without reopening any caller-selected pathname.
    descriptor = os.open(f'/proc/{parent_pid}/fd/{descriptor}', os.O_RDONLY | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as handle:
        if _descriptor_identity(os.fstat(handle.fileno())) != identity:
            raise ValueError('canonical validation descriptor changed before inspection')
        request = SimpleNamespace(payload_schema=schema, semantic_validation=semantics)
        header = _inspect_canonical_json_file(handle, request, size=identity[2], custody_limits=limits)
        if _descriptor_identity(os.fstat(handle.fileno())) != identity:
            raise ValueError('canonical validation descriptor changed during inspection')
    return header, os.getpid(), process_time() - started


def _project_value(function, value, decimal_context):
    started = process_time()
    with localcontext(decimal_context):
        result = function(value)
    return result, os.getpid(), process_time() - started


class CanonicalValidationPool:
    """One bounded CPU pool for a finite read; no retained scientific objects."""

    def __init__(self, workers):
        if workers <= 0:
            raise ValueError('maximum workers must be positive')
        self._workers = workers
        self._pool = None
        self._closed = False
        self._lock = Lock()
        self._slots = BoundedSemaphore(workers)
        self.worker_pids = set()
        self.validated_files = 0
        self.projected_records = 0
        self.cpu_seconds = 0.0

    def _submit(self, function, *args):
        self._slots.acquire()
        try:
            with self._lock:
                if self._closed:
                    raise RuntimeError('canonical validation scope has ended')
                if self._pool is None:
                    self._pool = ProcessPoolExecutor(max_workers=self._workers, mp_context=get_context('spawn'),
                        initializer=_initialize_metadata_worker)
                future = self._pool.submit(function, *args)
            future.add_done_callback(lambda _: self._slots.release())
            return future
        except BaseException:
            self._slots.release()
            raise

    def validate(self, handle, request, limits):
        # The artifact owner retains hashing, current access and replacement
        # checks. The FD remains open until this synchronous call returns.
        with self._lock:
            if self._closed:
                raise RuntimeError('canonical validation scope has ended')
        future = self._submit(_validate_canonical_descriptor,
            os.getpid(), handle.fileno(), _descriptor_identity(os.fstat(handle.fileno())),
            request.payload_schema, request.semantic_validation, limits)
        header, pid, elapsed = future.result()
        with self._lock:
            self.worker_pids.add(pid)
            self.validated_files += 1
            self.cpu_seconds += elapsed
        return header

    def project_ordered(self, function, values, *, weight=None, maximum_pending_bytes=None):
        """Decode bounded caller-owned inputs; retain only compact results.

        At most eight inputs are pending, sharing this read's CPU capacity
        with format validation. No path, custody owner or access verdict is
        transferred. The caller authenticates input bytes and final access.
        An optional conservative working-set estimate also bounds concurrent
        bytes. A single larger operand runs in the caller after pending jobs
        drain, preserving the existing serial capacity without copying it.
        """
        if (weight is None) != (maximum_pending_bytes is None):
            raise ValueError('weighted projections require both a size function and byte allowance')
        if weight is not None and (not callable(weight) or type(maximum_pending_bytes) is not int
                or maximum_pending_bytes <= 0):
            raise ValueError('weighted projections require a positive bounded byte allowance')
        with self._lock:
            if self._closed:
                raise RuntimeError('canonical validation scope has ended')
        iterator = iter(values)
        pending, results = deque(), []
        context = getcontext().copy()
        buffered, exhausted, pending_bytes = None, False, 0
        try:
            while pending or buffered is not None or not exhausted:
                while not exhausted and len(pending) < min(8, self._workers):
                    if buffered is None:
                        try:
                            value = next(iterator)
                        except StopIteration:
                            exhausted = True
                            break
                        size = 0 if weight is None else weight(value)
                        if type(size) is not int or size < 0:
                            raise ValueError('projection working-set estimate must be nonnegative bytes')
                        buffered = value, size
                    value, size = buffered
                    if maximum_pending_bytes is not None and pending_bytes + size > maximum_pending_bytes:
                        if pending:
                            break
                        # No second copy or concurrent expansion of an operand
                        # larger than the additional process-memory allowance.
                        result, _, elapsed = _project_value(function, value, context)
                        results.append(result)
                        with self._lock:
                            self.projected_records += 1
                            self.cpu_seconds += elapsed
                        buffered = None
                        continue
                    pending.append((self._submit(_project_value, function, value, context), size))
                    pending_bytes += size
                    buffered = None
                if not pending:
                    continue
                future, size = pending.popleft()
                result, pid, elapsed = future.result()
                pending_bytes -= size
                results.append(result)
                with self._lock:
                    self.worker_pids.add(pid)
                    self.projected_records += 1
                    self.cpu_seconds += elapsed
            return tuple(results)
        finally:
            for future, _ in pending:
                future.cancel()
            if pending:
                wait(tuple(future for future, _ in pending))

    def close(self):
        with self._lock:
            self._closed = True
            pool = self._pool
        if pool is not None:
            pool.shutdown(wait=True)


@contextmanager
def canonical_validation_scope(workers, *, shared_pool=None):
    """Share CPU capacity across nested scopes, never their custody state.

    The outer finite read owns shutdown. Nested readers can have independent
    byte censuses and access callbacks without retaining another W processes.
    The executor starts processes only when an actual format batch needs them.
    """
    inherited = shared_pool or _canonical_scope_pool.get()
    if inherited is not None:
        token = _canonical_scope_pool.set(inherited)
        try:
            yield inherited
        finally:
            _canonical_scope_pool.reset(token)
        return
    pool = CanonicalValidationPool(workers)
    token = _canonical_scope_pool.set(pool)
    try:
        yield pool
    finally:
        _canonical_scope_pool.reset(token)
        pool.close()


class ParallelValidationBatch:
    """Pipeline at most W descriptor reads into W process validators.

    Access callbacks stay in the controller. Every active read joins before
    return or refusal; the caller performs its complete final byte guard.
    """

    def __init__(self, check, *, workers, canonical_pool=None):
        self.check = check
        self.workers = workers
        self.canonical_pool = canonical_pool
        self._own_pool = canonical_pool is None
        self._pending = set()

    def __enter__(self):
        if self.canonical_pool is None:
            self.canonical_pool = CanonicalValidationPool(self.workers)
        self._threads = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix='artifact-format')
        return self

    def submit(self, value):
        if len(self._pending) >= self.workers:
            self._drain_completed()
        context = copy_context()
        self._pending.add(self._threads.submit(context.run, self._check, value))

    def _drain_completed(self):
        completed, _ = wait(self._pending, return_when=FIRST_COMPLETED)
        for future in completed:
            future.result()
        self._pending.difference_update(completed)

    def _check(self, value):
        parallel_token = in_parallel_verification.set(True)
        pool_token = canonical_validation_pool.set(self.canonical_pool)
        try:
            return self.check(value)
        finally:
            canonical_validation_pool.reset(pool_token)
            in_parallel_verification.reset(parallel_token)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                while self._pending:
                    self._drain_completed()
        finally:
            for future in self._pending:
                future.cancel()
            self._threads.shutdown(wait=True)
            if self._own_pool:
                self.canonical_pool.close()


def verify_in_parallel(check, values, *, workers):
    """Run at most the selected number of checks, inheriting current scopes.

    There is no persistent cache, publication or authority decision here.
    Nested verification stays serial to avoid pools waiting on their own
    serialized access callbacks. Exceptions escape only after active reads join.
    """
    def run(value):
        token = in_parallel_verification.set(True)
        try:
            return check(value)
        finally:
            in_parallel_verification.reset(token)

    iterator = iter(values)
    pending = set()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix='artifact-verification') as pool:
        def submit(value):
            context = copy_context()
            return pool.submit(context.run, run, value)
        try:
            for _ in range(workers):
                try:
                    value = next(iterator)
                except StopIteration:
                    break
                pending.add(submit(value))
            while pending:
                completed, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in completed:
                    future.result()
                pending.difference_update(completed)
                for _ in completed:
                    try:
                        value = next(iterator)
                    except StopIteration:
                        break
                    pending.add(submit(value))
        finally:
            for future in pending:
                future.cancel()
