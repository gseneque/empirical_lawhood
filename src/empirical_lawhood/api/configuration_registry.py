"""Closed configuration consumers; no registry entry grants execution or authority.

Module/class locators below are implementation-owned constants, never input values.
Consumer byte limits mirror their existing loaders; the exposed helper has a new
shape-check ceiling and the unsupported human template has no consuming limit.
Inputs are documentary inventory, not an installed-wheel checkout requirement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import import_module
from collections.abc import Sequence

from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration
from empirical_lawhood.adapters.composition.generated_public_facets import CONFIGURATION_DECLARATIONS


@dataclass(frozen=True, slots=True)
class ConfigurationConsumer(ConfigurationDeclaration):
    configuration_capabilities: tuple = ()

    @property
    def authoring_maximum_bytes(self) -> int | None:
        if self.maximum_bytes is None:
            return None
        return min(4 * self.maximum_bytes, 128 * 1024**2)

    @property
    def preparation_allowed(self) -> bool:
        return self.disposition == "editable"

    @property
    def loader(self) -> str:
        if self.consumer == "prepared-prior-census":
            return "adapters.composition.prepared_response.native_authoring._prior_census"
        if self.consumer == "finite-prior-census":
            return "adapters.composition.finite_response_law.native_input._census"
        if self.disposition == "helper":
            return "documentary helper; no runner loader"
        if self.requires_canonical:
            return "kernel.decoding.decode_canonical_bytes"
        return "api.codecs.load_registered_authoring"

    def record_type(self) -> type[CanonicalRecord]:
        if self.record_module is None or self.record_name is None:
            raise ValueError("this consumer has no canonical record constructor")
        record = getattr(import_module(self.record_module), self.record_name)
        if not isinstance(record, type) or not issubclass(record, CanonicalRecord):
            raise TypeError("configuration registry contains a non-record owner")
        if record.SCHEMA != self.schema_id:
            raise ValueError("configuration registry schema differs from its owner")
        return record


_BASE_CONSUMERS = tuple(ConfigurationConsumer(**asdict(row)) for row in CONFIGURATION_DECLARATIONS)

def _configuration_consumers() -> tuple[ConfigurationConsumer, ...]:
    from empirical_lawhood.api.experiment_preparation import experiment_protocols

    extra = tuple(ConfigurationConsumer(
        declaration.consumer_id, declaration.specification_type.SCHEMA,
        declaration.specification_type.__module__, declaration.specification_type.__name__,
        "editable", declaration.maximum_config_bytes, True, "campaign experiment-prepare",
        declaration.specification_type.__name__, declaration.example_paths, declaration.configuration_capabilities)
        for declaration in experiment_protocols())
    inputs = tuple(ConfigurationConsumer(
        value.consumer_id, value.record_type.SCHEMA,
        value.record_type.__module__, value.record_type.__name__,
        "editable", value.maximum_config_bytes, False, "campaign experiment-prepare --sources",
        value.record_type.__name__, value.example_paths)
        for declaration in experiment_protocols() for value in declaration.configuration_inputs)
    result = (*_BASE_CONSUMERS, *extra)
    names = {consumer.consumer for consumer in result}
    if len(names) != len(result):
        raise ValueError("configuration consumers conflict with installed experiment declarations")
    shared = {}
    for consumer in inputs:
        previous = shared.setdefault(consumer.consumer, consumer)
        if consumer.consumer in names or previous != consumer:
            raise ValueError("configuration input consumers conflict with installed owning declarations")
    return (*result, *shared.values())


class _ConfigurationConsumers(Sequence):
    """Keep static imports cold while deriving domain consumers when requested."""

    def __len__(self):
        return len(_configuration_consumers())

    def __getitem__(self, index):
        return _configuration_consumers()[index]

    def __iter__(self):
        return iter(_configuration_consumers())


CONSUMERS = _ConfigurationConsumers()


def consumers_for_schema(schema_id: str) -> tuple[ConfigurationConsumer, ...]:
    return tuple(item for item in CONSUMERS if item.schema_id == schema_id)


def consumer_by_id(consumer: str) -> ConfigurationConsumer:
    for item in CONSUMERS:
        if item.consumer == consumer:
            return item
    raise ValueError(f"unknown configuration consumer: {consumer}")
