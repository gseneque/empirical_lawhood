# SPDX-License-Identifier: MPL-2.0
"""Original inquiry meanings with disclosed receipts, never scientific authority."""

from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import recursive_inquiry as service, recursive_inquiry_evidence as evidence
from empirical_lawhood.api.recursive_inquiry_evidence import project_wave_evidence_bindings as original_bindings
from empirical_lawhood.storage.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole, ScientificConditionScope
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding, InquiryStateSources
from tests.test_recursive_inquiry import episode as episode, obj
from tests.test_recursive_inquiry_projection import custody as custody
from tests.runtime_platform.test_recursive_storage_codec_registration import _codec, _declaration, _request


@dataclass(frozen=True, slots=True)
class DisclosedReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/binary-inquiry-receipt'
    receipt_id: str
    task_id: str
    operational_status: OperationalStatus
    output_logical_artifacts: tuple
    output_materializations: tuple


@dataclass(frozen=True, slots=True)
class DisclosedProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/inquiry-product-scope'
    scope: str | ScientificConditionScope


@pytest.mark.parametrize('typed_scope', (False, True))
def test_product_scope_labels_preserve_registered_meaning_and_typed_scope_refusal(episode, monkeypatch, typed_scope):
    scope = episode['specification'].endpoint
    product = DisclosedProduct(scope if typed_scope else 'EXPOSED_RETURN_WITHOUT_PHYSICAL_ADMISSION')
    binding = InquiryEvidenceBinding('source.result', product.fingerprint(), scope,
        ContributionRole.INSTANCE_PRODUCT, (), ('nested.original',))
    registration = _declaration('source', _codec()).registration()
    draft = SimpleNamespace(operations=(SimpleNamespace(node_id='source', selection=registration.selection),),
        selected_operation_ids=('source',), links=(), external_inputs=(), contribution_parents=())
    products = dict(records={'source': {'source.result': product}})
    factory = SimpleNamespace(registration=registration, inquiry_evidence_projector=lambda *args: (binding,))
    monkeypatch.setattr(evidence, 'selected_operation_factories', lambda _: (factory,))
    original = product.canonical_bytes()
    assert original_bindings(draft=draft, payloads={}, products=products) == {binding.binding_id: binding}
    assert product.canonical_bytes() == original
    if typed_scope:
        changed = replace(binding, scope=replace(scope, receiver_id='foreign.receiver'))
        factory.inquiry_evidence_projector = lambda *args: (changed,)
        with pytest.raises(ValueError, match='original declared scope'):
            original_bindings(draft=draft, payloads={}, products=products)
    changed = replace(binding, content_sha256='f' * 64)
    factory.inquiry_evidence_projector = lambda *args: (changed,)
    with pytest.raises(ValueError, match='exact code-owned product meaning'):
        original_bindings(draft=draft, payloads={}, products=products)


@pytest.fixture
def binary(custody, episode, monkeypatch):
    codec = _codec()
    declaration = _declaration('source', codec)
    registration = declaration.registration()
    plane = ExternalArtifactPlane(custody.plane.root, ArtifactProfileValidatorRegistry(binary_codecs=(codec,)))
    request = _request()
    plane.write(request)
    manifest = plane.read_manifest(request.relative_path)
    receipt = DisclosedReceipt('receipt.exposed.binary', 'source', OperationalStatus.SUCCEEDED,
        (manifest.logical,), (manifest.materialization,))
    source = custody.add_wave('first')
    _, draft, _ = custody.packets['first']
    draft.selected_operation_ids = ('source',)
    draft.operations = (SimpleNamespace(node_id='source', selection=registration.selection, config_identity=obj('binary.config')),)
    entry = dict(task_id='source', output_id='source.result', logical_artifact_id=manifest.logical.logical_artifact_id,
        schema=manifest.logical.payload_schema, sha256=manifest.logical.content_sha256,
        size_bytes=manifest.materialization.size_bytes, relative_path=manifest.materialization.relative_path,
        producing_receipt=identity(receipt, receipt.receipt_id).to_document())
    products = dict(records={'source': {}}, receipts={'source': receipt}, outputs={manifest.logical.logical_artifact_id: manifest},
        product_index=(entry,), operational_census=({'task_id': 'source', 'attempt_id': 'attempt.exposed.binary',
            'operational_status': 'SUCCEEDED', 'reason_code': None},),
        attempt_receipts={'attempt.exposed.binary': receipt}, recovery_events={})
    binding = InquiryEvidenceBinding('source.result', manifest.logical.content_sha256, episode['specification'].endpoint,
        ContributionRole.INSTANCE_PRODUCT, (), ('nested.original',))
    factory = SimpleNamespace(registration=registration, inquiry_evidence_projector=lambda *args: (binding,))
    monkeypatch.setattr(evidence, 'selected_operation_factories', lambda _: (factory,))
    monkeypatch.setattr(evidence, 'project_wave_evidence_bindings', original_bindings)
    plan = SimpleNamespace(tasks=(SimpleNamespace(task_id='source', outputs=(SimpleNamespace(
        output_id='source.result', logical_artifact_id=manifest.logical.logical_artifact_id),)),))
    monkeypatch.setattr(service, 'read_recursive_wave', lambda **kwargs: ({'run_id': 'run.first'}, products, draft, plan))
    return SimpleNamespace(custody=custody, source=source, draft=draft, products=products,
        manifest=manifest, receipt=receipt, codec=codec, factory=factory, binding=binding)


def test_original_binary_output_stays_in_complete_attempt_and_stock_without_decoding(binary):
    state = binary.custody.project(InquiryStateSources((binary.source,)))
    expected = ObjectIdentity(binary.manifest.logical.logical_artifact_id, binary.codec.payload_schema,
        binary.codec.record_version, binary.manifest.logical.content_sha256)
    assert state.operational_census[0].products == (expected,)
    assert state.stock[0].product == expected and state.stock[0].producing_receipt == identity(binary.receipt, binary.receipt.receipt_id)
    assert state.stock[0].scope == binary.binding.scope
    assert not state.stock[0].independent_unit_ids and state.stock[0].nested_view_ids == ('nested.original',)
    assert state.cost_events[0].cost.cpu_seconds is None


@pytest.mark.parametrize('damage', ('codec', 'receipt', 'material', 'index', 'duplicate', 'digest', 'meaning'))
def test_binary_inquiry_refuses_missing_meaning_or_changed_original_producer(binary, damage):
    if damage == 'codec':
        binary.factory.registration = replace(binary.factory.registration, storage_codecs=())
    elif damage == 'receipt':
        binary.products['product_index'][0]['producing_receipt'] = obj('foreign.receipt').to_document()
    elif damage == 'material':
        binary.products['receipts']['source'] = replace(binary.receipt, output_materializations=())
    elif damage == 'index':
        binary.products['product_index'] = ()
    elif damage == 'duplicate':
        binary.products['product_index'] *= 2
    elif damage == 'digest':
        binary.products['product_index'][0]['sha256'] = 'f' * 64
    else:
        binary.factory.inquiry_evidence_projector = lambda *args: ()
    with pytest.raises(ValueError):
        binary.custody.project(InquiryStateSources((binary.source,)))
