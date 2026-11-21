# SPDX-License-Identifier: MPL-2.0
"""One guarded source read for the consumers of an inquiry projection.

The owner retains packets, drafts, plans and products only while its current
access and complete byte guards are live. No admission token crosses calls.
"""
from collections import OrderedDict
from contextlib import ExitStack, contextmanager, nullcontext
from contextvars import ContextVar
from dataclasses import dataclass, fields
import os
from pathlib import Path
import sys
from threading import get_ident

from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from empirical_lawhood.execution.recursive_inquiry import InquiryWaveSource

_AUTHORING_READ = ContextVar('inquiry_authoring_read', default=None)


def _factory_read_policy(value):
    """Snapshot mutable callback bindings, without copying immutable records."""
    from functools import partial
    from types import MappingProxyType
    if type(value) in (dict, MappingProxyType):
        return (type(value), tuple((key, _factory_read_policy(item)) for key, item in value.items()))
    if type(value) in (tuple, list):
        return (type(value), tuple(_factory_read_policy(item) for item in value))
    if type(value) is partial:
        return (partial, value.func, _factory_read_policy(value.args),
            _factory_read_policy(value.keywords), _factory_read_policy(vars(value)))
    return value


def _authored_reuse_key(value):
    """Bind immutable roots to their current codecs, validators and numerics."""
    from empirical_lawhood.api import recursive_operations as operations
    from empirical_lawhood.api import recursive_authoring as authoring
    from empirical_lawhood.science.records.decoded_record_store import record_store_key
    from empirical_lawhood.execution.local.worker_bootstrap import NUMERICAL_THREAD_ENV_VARS
    if (operations.operation_factories is not operations._INSTALLED_OPERATION_FACTORIES
            or authoring.operation_catalog is not operations._INSTALLED_OPERATION_CATALOG):
        return None
    factories = operations.selected_operation_factories(
        operation.selection.selection_id for operation in value.draft.operations)
    kinds = tuple(dict.fromkeys((*(type(record) for record in
        (value.packet, value.draft, value.implementation, value.run, value.plan)),
        *(kind for factory in factories for kind in
            (factory.registration.config_record_type, *factory.registration.input_record_types,
                *factory.output_codecs.values())))))
    keys = tuple(record_store_key(kind, '', 0) for kind in kinds)
    if any(key is None for key in keys):
        return None
    # Registrations also own source/publication validators and binary codecs.
    try:
        callbacks = tuple(tuple(_factory_read_policy(getattr(factory, field.name)) for field in fields(factory))
            for factory in factories)
    except RecursionError:
        return None
    controller = sys.modules.get('threadpoolctl')
    pools = () if controller is None else tuple(sorted(
        (pool['filepath'], pool['num_threads']) for pool in controller.threadpool_info()))
    return (keys, callbacks, tuple(os.environ.get(name) for name in
        (*NUMERICAL_THREAD_ENV_VARS, 'NUMBA_NUM_THREADS', 'BLIS_NUM_THREADS')), pools)


class _AuthoredInquiryReads:
    """Bounded immutable metadata for one source-reading authoring invocation.

    Execution products and decision/access/spending verdicts are never shared
    between projections. The ordinary read plane owns the complete final guard.
    """

    def __init__(self, original, writer):
        from empirical_lawhood.api.recursive_contributions import _read_policy_key
        self.original, self.writer = original, writer
        self.policy = _read_policy_key(writer)
        self.active, self.process, self.thread = True, os.getpid(), get_ident()
        self.entries, self.bytes = OrderedDict(), 0
        self.payload_guards = {}
        self.unentered = set()

    def require_current(self):
        from empirical_lawhood.api.recursive_contributions import _read_policy_key
        if not self.active or (self.process, self.thread) != (os.getpid(), get_ident()):
            raise ValueError('inquiry authoring read escaped its owning invocation')
        if (self.policy != _read_policy_key(self.original)
                or self.policy != _read_policy_key(self.writer)):
            raise ValueError('inquiry authoring changes its original read policy')
        self.writer.require_verification_context()
        for guard in self.payload_guards.values():
            guard()
        for path in self.unentered:
            if path.exists() or path.is_symlink():
                raise ValueError('prospective inquiry supplier acquired execution custody during authoring')

    def get(self, relative):
        self.require_current()
        entry = self.entries.get(relative)
        if entry is None:
            return None
        value, key, size = entry
        if key != _authored_reuse_key(value):
            del self.entries[relative]
            self.bytes -= size
            return None
        self.entries.move_to_end(relative)
        return value

    def retain(self, relative, value):
        from empirical_lawhood.science.records.decoded_record_store import MAX_SHARED_RECORD_BYTES, MAX_SHARED_RECORDS
        from empirical_lawhood.api.retained_read_metadata import retained_metadata_bytes
        self.require_current()
        # Access lifetime is not optional cache state. A large/unsupported
        # metadata graph or an eviction must still keep its final access guard.
        guard = value.payloads.retained_access_guard()
        if guard is not None:
            owner = getattr(guard, 'access', getattr(guard, '__self__', guard))
            self.payload_guards[id(owner)] = guard
        value.payloads.require_current()
        records = (value.packet, value.draft, value.implementation, value.run, value.plan)
        if not all(record._is_cacheable() for record in records):
            return
        key = _authored_reuse_key(value)
        # Charge the actual metadata graph, including lazy member indexes and
        # canonical buffers. External payload byte lengths are not heap usage.
        # The payload's live read plane/access guard has a separate owner.
        payloads = value.payloads
        size = retained_metadata_bytes((value.source, records, key,
            payloads._members, payloads._manifests, payloads._json_headers,
            payloads._selected_manifests,
            None if payloads._access_guard is None else payloads._access_guard.selected),
            maximum_bytes=MAX_SHARED_RECORD_BYTES)
        if key is None or size is None:
            return
        old = self.entries.pop(relative, None)
        if old is not None:
            self.bytes -= old[2]
        while self.entries and (len(self.entries) >= MAX_SHARED_RECORDS
                or self.bytes + size > MAX_SHARED_RECORD_BYTES):
            _, (_, _, removed) = self.entries.popitem(last=False)
            self.bytes -= removed
        self.entries[relative] = value, key, size
        self.bytes += size

    def close(self):
        self.active = False
        self.entries.clear()
        self.payload_guards.clear()
        self.unentered.clear()
        self.bytes = 0


def _current_authored_reads(writer):
    from empirical_lawhood.api.recursive_contributions import _read_policy_key
    current = _AUTHORING_READ.get()
    if (current is None or not current.active
            or (current.process, current.thread) != (os.getpid(), get_ident())
            or not (writer is current.original or writer is current.writer)
            or _read_policy_key(writer) is None):
        return None
    current.require_current()
    return current


def require_inquiry_execution_boundary(artifact_writer):
    """Execution cannot extend a source-only authoring verification lifetime."""
    current = _AUTHORING_READ.get()
    # A policy change or a copied context must not turn off the effect barrier.
    # They can disable metadata reuse, but cannot finish the original read.
    if current is not None and current.active:
        raise ValueError('end the inquiry authoring read before execution')


@contextmanager
def inquiry_authoring_read(artifact_writer):
    """Share unchanged source metadata through projection and new publication.

    Use the yielded reader for reads and the ordinary writer for new, disjoint
    decision/successor packages. End this scope before execution or transport.
    Complete byte guards, including refusal paths, remain active until return.
    Custom policies and explicit traversal limits keep their fresh route.
    """
    from empirical_lawhood.api.recursive_contributions import _read_policy_key, recursive_contribution_read_context
    current = _current_authored_reads(artifact_writer)
    if current is not None:
        yield current.writer
        return
    if _read_policy_key(artifact_writer) is None:
        yield artifact_writer
        return
    # Retained parent readers borrow this read's CPU pool. Finish their complete
    # guards before the main artifact reader shuts that pool down.
    with artifact_writer.read_context() as writer, recursive_contribution_read_context():
        current = _AuthoredInquiryReads(artifact_writer, writer)
        token = _AUTHORING_READ.set(current)
        try:
            yield writer
        finally:
            try:
                current.require_current()
            finally:
                current.close()
                _AUTHORING_READ.reset(token)


@dataclass(frozen=True)
class _InquiryWaveRead:
    source: InquiryWaveSource
    packet: object
    draft: object
    implementation: object
    payloads: object
    report: object
    products: object
    run: object
    plan: object


class _InquiryRead:
    def __init__(self, writer, lifetime, stock, shared=None):
        from empirical_lawhood.api.recursive_contributions import _read_policy_key
        self.writer, self.lifetime, self.stock = writer, lifetime, stock
        self.policy = _read_policy_key(writer) if stock else None
        self.shared = shared
        self.waves, self.accesses, self.unentered = OrderedDict(), {}, set()
        self.wave_bytes = 0
        self.active, self.process, self.thread = True, os.getpid(), get_ident()

    def require_current(self):
        if not self.active or (self.process, self.thread) != (os.getpid(), get_ident()):
            raise ValueError('inquiry source read escaped its owning projection')
        if self.policy is not None:
            from empirical_lawhood.api.recursive_contributions import _read_policy_key
            if _read_policy_key(self.writer) != self.policy:
                raise ValueError('inquiry source changes its original read policy')
        for access in self.accesses.values():
            access.require_current(artifact_writer=self.writer)
        if self.shared is not None:
            # The enclosing source read owns its final complete union check.
            # Do not rehash unrelated history at every consumer of one wave.
            self.shared.require_current()
        elif self.stock:
            self.writer.require_verification_snapshot()
        for path in self.unentered:
            if path.exists() or path.is_symlink():
                raise ValueError('prospective inquiry supplier acquired execution custody during projection')

    def _retain_wave(self, key, value):
        """Bound projection reuse too; mandatory guards have separate owners."""
        from empirical_lawhood.science.records.decoded_record_store import MAX_SHARED_RECORD_BYTES, MAX_SHARED_RECORDS
        from empirical_lawhood.api.retained_read_metadata import retained_metadata_bytes

        payloads = value.payloads
        size = retained_metadata_bytes((value.source, value.packet, value.draft,
            value.implementation, value.report, value.products, value.run, value.plan,
            payloads._members, payloads._manifests, payloads._json_headers,
            payloads._selected_manifests,
            None if payloads._access_guard is None else payloads._access_guard.selected),
            maximum_bytes=MAX_SHARED_RECORD_BYTES)
        if size is None:
            return
        old = self.waves.pop(key, None)
        if old is not None:
            self.wave_bytes -= old[1]
        while self.waves and (len(self.waves) >= MAX_SHARED_RECORDS
                or self.wave_bytes + size > MAX_SHARED_RECORD_BYTES):
            _, (_, removed) = self.waves.popitem(last=False)
            self.wave_bytes -= removed
        self.waves[key] = value, size
        self.wave_bytes += size

    def wave(self, *, directory, include_products, expected=None, require_unentered=False,
             validate_authored=None):
        from empirical_lawhood.api.recursive_authoring import load_authored_wave
        from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots, _retained_plans
        from empirical_lawhood.api.recursive_operations import inquiry_selection_scope
        if validate_authored is not None and not callable(validate_authored):
            raise TypeError('authored source preflight requires a callable')
        self.require_current()
        root = Path(self.writer.root.contract.canonical_path)
        path = Path(directory)
        if (not path.is_absolute() or '..' in path.parts
                or any(value.is_symlink() for value in (path, *path.parents))):
            raise ValueError('inquiry requires exact original guarded custody paths')
        relative = path.resolve(strict=True).relative_to(root).as_posix()
        key = relative, include_products
        retained = self.waves.get(key) if self.policy is not None else None
        value = None if retained is None else retained[0]
        if retained is not None:
            self.waves.move_to_end(key)
        if value is None and not include_products and self.shared is not None:
            value = self.shared.get(relative)
            if value is not None:
                from empirical_lawhood.api.recursive_authoring import _authenticate_authored_wave_roots
                # Original access, parents, direct operands and registered
                # publication requirements remain current at every boundary.
                _authenticate_authored_wave_roots(packet=value.packet, draft=value.draft,
                    source=value.implementation, payloads=value.payloads,
                    artifact_writer=self.writer, lazy_payloads=True)
                self.lifetime.enter_context(inquiry_selection_scope(value.draft))
                access = getattr(value.payloads, 'original_input_access', None)
                if access is not None:
                    self.accesses[id(access)] = access
                self._retain_wave(key, value)
        if value is None:
            retained = []
            def preflight(**roots):
                if expected is not None and identity(roots['packet'], roots['packet'].packet_id) != expected:
                    raise ValueError('inquiry source changes its exact authored packet')
                self.lifetime.enter_context(inquiry_selection_scope(roots['draft']))
                access = getattr(roots['payloads'], 'original_input_access', None)
                if access is not None:
                    self.accesses[id(access)] = access
                if validate_authored is not None:
                    validate_authored(packet=roots['packet'], draft=roots['draft'], source=roots['source'])
                retained.append(roots)
            if include_products:
                result, _ = _read_recursive_wave_with_retained_roots(directory=path,
                    artifact_writer=self.writer, include_products=True, _validate_authored=preflight)
                report, products, draft, plan = result
                roots, = retained
                packet, implementation, payloads = roots['packet'], roots['source'], roots['payloads']
                run = roots['run']
            else:
                packet, draft, implementation, payloads = load_authored_wave(directory=path,
                    artifact_writer=self.writer, lazy_payloads=True)
                run, plan, index = _retained_plans(payloads, draft)
                preflight(packet=packet, draft=draft, source=implementation, payloads=payloads,
                    run=run, plan=plan, index=index)
                report = products = None
            value = _InquiryWaveRead(InquiryWaveSource(relative, identity(packet, packet.packet_id), include_products),
                packet, draft, implementation, payloads, report, products, run, plan)
            if self.policy is not None:
                self._retain_wave(key, value)
                if not include_products and self.shared is not None:
                    self.shared.retain(relative, value)
        elif validate_authored is not None:
            # A consumer's current preflight is never an inherited verdict.
            validate_authored(packet=value.packet, draft=value.draft, source=value.implementation)
        if expected is not None and value.source.packet != expected:
            raise ValueError('inquiry source changes its exact authored packet')
        if require_unentered:
            if include_products:
                raise ValueError('a prospective inquiry cannot consume completed products')
            # Use the same owning load's run identity, without a second loader.
            path = self.writer.root.resolve('runs/' + value.run.run_plan_id, for_write=False)
            self.unentered.add(path)
            if self.shared is not None:
                self.shared.unentered.add(path)
        self.require_current()
        return value

    def project_state(self, **kwargs):
        from empirical_lawhood.api.recursive_inquiry import _project_inquiry_state
        self.require_current()
        result = _project_inquiry_state(**kwargs, artifact_writer=self.writer, reading=self)
        self.require_current()
        return result


@contextmanager
def inquiry_projection_read(artifact_writer):
    """Compose registered projections inside the existing finite custody scope."""
    from empirical_lawhood.api.recursive_contributions import recursive_contribution_read_context
    from empirical_lawhood.api.recursive_execution import _read_only_custody_policy
    from empirical_lawhood.storage.artifacts import _has_stock_manifest_reads
    stock = _read_only_custody_policy(artifact_writer) is not None and _has_stock_manifest_reads(artifact_writer)
    shared = _current_authored_reads(artifact_writer) if stock else None
    with ExitStack() as lifetime:
        writer = lifetime.enter_context((shared.writer if shared is not None else artifact_writer).read_context()
            if stock else nullcontext(artifact_writer))
        lifetime.enter_context(recursive_contribution_read_context())
        reading = _InquiryRead(writer, lifetime, stock, shared)
        try:
            yield reading
        finally:
            try:
                reading.require_current()
            finally:
                reading.active = False
                reading.waves.clear()
                reading.wave_bytes = 0
                reading.accesses.clear()
                reading.unentered.clear()
