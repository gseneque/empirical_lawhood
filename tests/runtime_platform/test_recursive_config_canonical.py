# SPDX-License-Identifier: MPL-2.0
"""Exact configuration grammar controls, without execution or source grants."""
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
from empirical_lawhood.planning.study_authoring import CapabilitySelection


@dataclass(frozen=True)
class LiteralConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/literal-recursive-config'
    config_id: str
    rows: tuple[tuple[str, int, Decimal], ...]


def _operation(count=1):
    config = LiteralConfig('config.literal', tuple(('exact-row', index, Decimal('0.0125')) for index in range(count)))
    return config, RecursiveOperationSpec.from_config(node_id='node.literal',
        selection=CapabilitySelection('literal.recursive', '1.0.0', 'a' * 64), config_id=config.config_id,
        config=config, obligation_ids=('obligation.literal',), resource_budget=ResourceBudget(1, 1024**2, 0, 1, 1024**2, 1024**2))


def test_many_nested_configurations_keep_every_exact_decimal_and_original_identity():
    config, operation = _operation(4096)
    assert operation.config_payload.encode() == config.canonical_bytes()
    assert operation.config_identity == ObjectIdentity.from_record(config.config_id, config)
    assert replace(operation).canonical_bytes() == operation.canonical_bytes()


@pytest.mark.parametrize('value', (
    '{"x":1,"x":1}', '{"nested":{"x":0,"x":1}}',
    '{"decimal":{"decimal":"1.00","decimal":"1.00"}}',
    '{"x":1.0}', '{"x":NaN}', '{"x":Infinity}', '{"x":-0}',
    '{"text":"\\u0061"}', '{"x":1, "y":2}',
))
def test_full_byte_comparison_rejects_duplicate_keys_and_every_noncanonical_number_or_escape(value):
    config, operation = _operation()
    text = '{"schema":"' + config.SCHEMA + '","value":' + value + ',"version":"1.0.0"}\n'
    with pytest.raises(ValueError):
        replace(operation, config_payload=text)


def test_duplicate_envelope_key_is_refused_even_when_both_values_agree():
    _, operation = _operation()
    text = operation.config_payload.replace('"version":"1.0.0"', '"version":"1.0.0","version":"1.0.0"')
    with pytest.raises(ValueError):
        replace(operation, config_payload=text)
