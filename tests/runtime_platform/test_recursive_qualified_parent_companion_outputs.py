# SPDX-License-Identifier: MPL-2.0
"""Actual companion publications under exposed test custody; no qualification."""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

import pytest

from empirical_lawhood.api import recursive_qualified_parents as owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.recursive_qualified_parents import QualifiedParentEvidence
from tests.test_recursive_public_service import _plane


@dataclass(frozen=True, slots=True)
class Companion(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/qualified-parent-companion'
    record_id: str
    value: Decimal


@pytest.fixture
def actual(tmp_path):
    plane = _plane(tmp_path/'selected')
    record = Companion('companion.synthetic', Decimal('1.0'))

    def write(name, payload=None, access=OutcomeAccess.EVALUATION_SEALED):
        return plane.write(ArtifactWriteRequest(name, 'outputs/'+name+'.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.'+name, 'outputs',
            record.canonical_bytes() if payload is None else payload, VisibilityCeiling.PROSPECTIVE, (), access))

    publication = write('artifact.synthetic.companion')
    receipt = CanonicalTaskReceipt('receipt.synthetic.companion', 'run.synthetic.companion', 'synthetic.producer',
        'attempt.synthetic.companion', '1'*40, (), (publication.materialization,), (publication.logical,),
        (ReceiptCheck('synthetic-ordinary-completion', True, ()),), OperationalStatus.SUCCEEDED, ())
    ExternalTaskReceiptStore(plane).commit(receipt, visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        outcome_access=OutcomeAccess.EVALUATION_SEALED)
    return plane, record, publication, receipt, write


def test_default_empty_evidence_preserves_existing_route_without_extra_io(monkeypatch):
    monkeypatch.setattr(owner, '_output_payload', lambda *args: pytest.fail('undeclared companion read'))
    assert owner._additional_products(None, None, (), {}) == ()
    assert QualifiedParentEvidence(None, None, None, None, None, None, b'primary').additional_products == ()


def test_actual_successful_companion_publication_retains_exact_bytes_and_metadata(actual):
    plane, record, publication, receipt, _ = actual
    products = owner._additional_products(plane, receipt, (record.SCHEMA,), {record.SCHEMA: Companion})
    assert len(products) == 1
    assert (products[0].logical, products[0].materialization, products[0].payload) == (
        publication.logical, publication.materialization, record.canonical_bytes())


@pytest.mark.parametrize('damage', ['bytes', 'sidecar', 'publication'])
def test_actual_companion_custody_tamper_refuses(actual, damage):
    plane, record, publication, receipt, _ = actual
    path = plane.root.resolve(publication.materialization.relative_path, for_write=False)
    target = path if damage == 'bytes' else path.with_name(path.name+'.manifest.json')
    if damage == 'publication':
        target.unlink()
    else:
        target.write_bytes(target.read_bytes()[:-1]+b' ')
    with pytest.raises((PermissionError, ValueError, RuntimeError, OSError)):
        owner._additional_products(plane, receipt, (record.SCHEMA,), {record.SCHEMA: Companion})


@pytest.mark.parametrize('damage', ['missing', 'duplicate', 'foreign-codec', 'oversize', 'wrong-access', 'unsuccessful'])
def test_companion_declarations_refuse_before_any_payload_read(actual, monkeypatch, damage):
    plane, record, publication, receipt, write = actual
    codecs = {record.SCHEMA: Companion}
    if damage == 'missing':
        receipt = replace(receipt, output_logical_artifacts=(), output_materializations=())
    elif damage == 'duplicate':
        second = write('artifact.synthetic.companion2')
        receipt = replace(receipt, output_logical_artifacts=(publication.logical, second.logical),
            output_materializations=(publication.materialization, second.materialization))
    elif damage == 'foreign-codec':
        codecs = {}
    elif damage == 'oversize':
        receipt = replace(receipt, output_materializations=(replace(publication.materialization, size_bytes=16*1024**2+1),))
    elif damage == 'wrong-access':
        changed = write('artifact.synthetic.development', access=OutcomeAccess.OUTCOME_BLIND)
        receipt = replace(receipt, output_logical_artifacts=(changed.logical,), output_materializations=(changed.materialization,))
    elif damage == 'unsuccessful':
        receipt = replace(receipt, operational_status=OperationalStatus.FAILED, reason_codes=('synthetic-failure',))
    monkeypatch.setattr(owner, '_output_payload', lambda *args: pytest.fail('companion read before declaration refusal'))
    with pytest.raises(PermissionError):
        owner._additional_products(plane, receipt, (record.SCHEMA,), codecs)


@pytest.mark.parametrize('damage', ['version', 'decimal-spelling'])
def test_companion_installed_version_and_exact_canonical_decimal_bytes_refuse(actual, damage):
    plane, record, _, receipt, write = actual
    raw = record.canonical_bytes()
    changed = raw.replace(b'"version":"1.0.0"', b'"version":"9.0.0"') if damage == 'version' else raw.replace(b'"decimal":"1"', b'"decimal":"1.00"')
    assert changed != raw
    published = write('artifact.synthetic.changed', changed)
    receipt = replace(receipt, output_logical_artifacts=(published.logical,), output_materializations=(published.materialization,))
    # Even authenticated equal-value decimal spellings must match the exact
    # installed canonical re-encoding before reaching a domain assessor.
    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        owner._additional_products(plane, receipt, (record.SCHEMA,), {record.SCHEMA: Companion})
