"""Closed adapter compositions; static discovery leaves scientific owners cold."""

from importlib import import_module

__all__ = [
    "BOUNDED_ACQUISITION_CAPABILITY_KEY",
    'AcquisitionRecurrenceMarginContractRegistry',
    "GATE_MARGIN_CAPABILITY_KEY",
    "MAXIMIN_CONTINUATION_CAPABILITY_KEY",
    "RECURRENCE_CAPABILITY_KEY",
    "ACQUISITION_RECURRENCE_MARGIN_CAPABILITY_KEYS",
    'build_acquisition_recurrence_margin_contract_registry',
    'acquisition_recurrence_margin_capability_manifests',
]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    owner = import_module(".acquisition_recurrence_margin_contracts", __name__)
    value = getattr(owner, name)
    globals()[name] = value
    return value
