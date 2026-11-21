# SPDX-License-Identifier: MPL-2.0
"""Prepared operand lifetimes over an exposed PURE draft, never authority."""

from dataclasses import replace
from contextvars import copy_context
from decimal import localcontext
from pathlib import Path
from types import SimpleNamespace
import gc
import weakref

import pytest

from empirical_lawhood.domains.materials.analytic_material_inquiry.operation_bindings import InquiryOperationConfig
from empirical_lawhood.domains.materials.analytic_material_inquiry.recursive_translation import supply_draft
from empirical_lawhood.domains.materials.electron_gas.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.execution.recursive_inquiry_selection import InquirySelectionPreparation


@pytest.fixture
def selection():
    root = Path(__file__).resolve().parents[1]
    source = decode_canonical_bytes((root / 'programmes/materials/superconductivity/workflows/electron-gas-response/config.json').read_bytes(),
        UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
    draft = supply_draft(source)
    calls = []
    def prepare(candidate):
        calls.append(candidate.draft_id)
        if candidate != draft:
            raise ValueError('changed complete source draft')
        return tuple(decode_canonical_bytes(row.config_payload.encode(), InquiryOperationConfig, maximum_bytes=None)
            for row in candidate.operations)
    owner = InquirySelectionPreparation(prepare, (InquiryOperationConfig,), (supply_draft,))
    return SimpleNamespace(draft=draft, owner=owner, calls=calls)


def test_selection_is_once_per_live_draft_and_releases_records(selection):
    case = selection
    with case.owner.scope(case.draft) as records:
        record_ref = weakref.ref(records[0])
        with case.owner.scope(case.draft) as nested:
            assert nested is records
        assert case.owner.read(case.draft) is records
        assert len(case.calls) == 1
    del records, nested
    gc.collect()
    assert record_ref() is None
    with case.owner.scope(case.draft):
        assert len(case.calls) == 2
    case.owner.read(case.draft)
    case.owner.read(case.draft)
    assert len(case.calls) == 4


def test_copied_context_cannot_keep_a_closed_selection_alive(selection):
    with selection.owner.scope(selection.draft) as records:
        record_ref = weakref.ref(records[0])
        copied = copy_context()
    del records
    gc.collect()
    assert record_ref() is None
    copied.run(selection.owner.read, selection.draft)
    assert len(selection.calls) == 2


def test_changed_draft_does_not_inherit_validated_selection(selection):
    with selection.owner.scope(selection.draft):
        with pytest.raises(ValueError, match='changed complete source draft'):
            selection.owner.read(replace(selection.draft, question='A different scientific question'))
    assert len(selection.calls) == 2


def test_decimal_context_and_validation_owner_changes_start_fresh(selection):
    with selection.owner.scope(selection.draft) as original:
        with localcontext() as context:
            context.prec += 1
            assert selection.owner.read(selection.draft) == original
            assert len(selection.calls) == 2
        changed = replace(selection.owner, validators=(lambda: None,))
        assert changed.read(selection.draft) == original
        assert len(selection.calls) == 3
        assert selection.owner.read(selection.draft) is original
        assert len(selection.calls) == 3


def test_replaced_record_validator_refuses_inside_existing_scope(selection, monkeypatch):
    with selection.owner.scope(selection.draft):
        def refuse(self):
            raise ValueError('current configuration validator refuses')
        monkeypatch.setattr(InquiryOperationConfig, '__post_init__', refuse)
        with pytest.raises(ValueError, match='current configuration validator refuses'):
            selection.owner.read(selection.draft)
    assert len(selection.calls) == 2


def test_custom_record_encoding_keeps_eager_validation(selection, monkeypatch):
    original = InquiryOperationConfig.canonical_bytes
    monkeypatch.setattr(InquiryOperationConfig, 'canonical_bytes', lambda self: original(self))
    with selection.owner.scope(selection.draft):
        selection.owner.read(selection.draft)
        selection.owner.read(selection.draft)
    assert len(selection.calls) == 3
