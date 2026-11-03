# SPDX-License-Identifier: MPL-2.0
"""Bind one compact selected source to its exact standalone provenance.

This noncanonical local view carries no authority. Current parent custody and
worker input contracts authenticate the original record before construction.
The original numerical owners receive the complete producing record unchanged.
"""
from dataclasses import dataclass

from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance


@dataclass(frozen=True, slots=True)
class BoundSelectedNativeSource:
    transport: object
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        from .selected_e3_e4_records import SelectedE3E4NativeSourceReference
        from .selected_e4_native_records import SelectedE4ProtectedNativeSourceReference

        if type(self.transport) not in (SelectedE3E4NativeSourceReference, SelectedE4ProtectedNativeSourceReference):
            raise TypeError("selected source binding requires its exact installed compact transport")
        self.transport.__post_init__()
        from .records import ScheduledSource
        if type(self.reference) is not ScheduledSource:
            raise TypeError("selected source view requires its actual current bounded reference")
        self.reference.__post_init__()
        if type(self.provenance) is not NumericalProducingProvenance:
            raise TypeError("selected source binding requires its exact original full provenance")
        self.provenance.__post_init__()
        if (self.provenance.identity != self.transport.provenance
                or len(self.provenance.canonical_bytes()) != self.transport.provenance_size_bytes):
            raise ValueError("selected source binding substitutes original provenance identity or exact size")

    @property
    def reference(self):
        return self.transport.reference

    @property
    def source_id(self):
        return self.reference.source_id

    @property
    def identity(self):
        return self.transport.identity

    @property
    def programme(self):
        return self.transport.programme

    @property
    def bank(self):
        return self.transport.bank

    @property
    def descriptor(self):
        return self.transport.descriptor

    @property
    def public(self):
        return self.transport.public

    @property
    def root(self):
        return self.reference.root

    @property
    def root_id(self):
        return self.reference.root_id

    @property
    def coordinate(self):
        return self.transport.coordinate

    @property
    def policy(self):
        return self.transport.policy

    @property
    def numerical_design(self):
        return self.transport.numerical_design

    @property
    def evidence_role(self):
        return self.transport.evidence_role


def bind_selected_native_source(transport, provenance):
    return BoundSelectedNativeSource(transport, provenance)


def source_transport(source):
    return source.transport if type(source) is BoundSelectedNativeSource else source


def selected_native_operation(namespace, phase, *, recorded_operation=None):
    """Accept only the current direct scientific operand contract."""
    stem = {"prefix": "prefix-before-continuation", "continue": "exact-checkpoint-continuation",
        "responses": "scheduled-paired-pulse-responses"}[phase]
    current = namespace + "." + stem + ".direct-operands.v2"
    operation = current if recorded_operation is None else recorded_operation
    if operation != current:
        raise ValueError("selected native evidence has an unsupported exact operation revision")
    return operation, True


def selected_native_source_operands(source):
    """Name authenticated carriers; their typed binding retains the full subject."""
    if type(source) is not BoundSelectedNativeSource:
        raise TypeError("current selected native operands require the exact bound source carrier")
    # Frozen BoundSelectedNativeSource already authenticated this join in its
    # constructor; reserializing the full provenance cannot strengthen it.
    return source.transport.identity, source.transport.provenance


def selected_stream_operands(source, panels, *, include_future=False):
    """Retain every declared root/panel stream, including truthful nonuse."""
    selected = tuple((source.root.stream_identity(value), value) for value in source.root.streams)
    if include_future:
        selected += tuple((panel.stream_identity(value), value) for panel in panels
            if panel.role == "INDEPENDENT_FUTURE" for value in panel.streams)
    if len({pin.object_id for pin, _ in selected}) != len(selected):
        raise ValueError("selected native stream carriers alias an original root/panel stream")
    return selected
