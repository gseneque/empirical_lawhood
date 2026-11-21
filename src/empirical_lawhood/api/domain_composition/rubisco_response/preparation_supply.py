# SPDX-License-Identifier: MPL-2.0
"""Prepare and independently read the original local destination consumer."""

from hashlib import sha256

from empirical_lawhood.api.recursive_inquiry_read import inquiry_projection_read
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import PreparationSupplySelection, assess_supply, external_id
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_translation import selected_configs, supply_draft


def prepare_preparation_supply(*, design, original_prefixes, parents, original_response=None):
    """Select already independently read originals; custody imports their bytes."""
    selection = PreparationSupplySelection(design, original_prefixes, original_response,
        tuple(sorted(parents, key=lambda p: p.contribution_id)))
    config = PreparationSupplyConfig(selection)
    return dict(config=config, draft=supply_draft(config))


def read_preparation_supply(*, directory, artifact_writer):
    with artifact_writer.read_context() as writer, inquiry_projection_read(writer) as reading:
        return _read_preparation_supply(directory=directory, reading=reading)


def _read_preparation_supply(*, directory, reading):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_inquiry import actual_products
    original = reading.wave(directory=directory, include_products=True)
    packet, draft, source, payloads = original.packet, original.draft, original.implementation, original.payloads
    config, = selected_configs(draft)
    report, products = original.report, original.products
    for record in config.selection.records:
        if payloads['external-' + sha256(external_id(record).encode()).hexdigest()[:24] + '.json'] != record.canonical_bytes():
            raise ValueError('local destination changes original complete contribution bytes')
    rows = actual_products(draft, products)
    if len(rows) != 1 or rows[0][2] != assess_supply(config.selection):
        raise ValueError('local destination lacks its independent original complete assessment')
    return dict(packet=packet, draft=draft, source=source, config=config, report=report, products=products,
        assessment=rows[0][2], connection_assessments=products['connection_assessments'])
