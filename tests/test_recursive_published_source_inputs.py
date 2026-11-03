# SPDX-License-Identifier: MPL-2.0
"""Real publication/authoring controls with disclosed software callbacks only.

No E3 products, real permission, native execution or qualification are created.
The strict authored-member callback intentionally refuses intrinsic blind source
members; exact selected source metadata must justify those reads separately.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import os
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring as owner, recursive_operations
from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_recursive_compiler import Config, BUDGET, fixture
from tests.runtime_platform.test_recursive_storage_codec_registration import SCHEMA, MEDIA, _codec, _declaration, _framed, _request
from tests.test_recursive_public_service import _plane


ROOT = Path(__file__).resolve().parents[1]


class _DisclosedScope:
    parents = ()

    def __init__(self):
        self.current = True
        self.samples = 0
        self.authored_member_calls = 0
        self.protected_record = None

    def require_current(self):
        self.samples += 1
        if not self.current:
            raise PermissionError('disclosed original permission expired before source read')

    def record_parents(self, record):
        return self.parents if record is self.protected_record else ()

    def require_member(self, manifest):
        self.authored_member_calls += 1
        self.require_current()
        logical = manifest.logical
        if (logical.outcome_access, logical.visibility_ceiling) != (
                OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY):
            raise PermissionError('disclosed authored owner refuses an unowned source/sibling')
        if logical.lineage_parents != self.parents:
            raise PermissionError('disclosed authored owner refuses foreign ancestry')


def _external(name, logical, payload, schema=SCHEMA, media=MEDIA):
    return RecursiveExternalInput('input.' + name, logical, schema, media, max(1, len(payload)),
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, sha256(payload).hexdigest())


def _source_case(tmp_path, *, sibling=False):
    codec = _codec()
    base = _plane(tmp_path / 'guarded')
    plane = ExternalArtifactPlane(base.root, validators=ArtifactProfileValidatorRegistry(binary_codecs=(codec,)))
    payload = _framed()
    requests = [_request(payload, logical_artifact_id='artifact.source', relative_path='source/source.blob',
        publication_scope_id='publication.disclosed-source', publication_scope_relative_root='source',
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)]
    record = Config('config.selected-metadata', 7)
    requests.append(ArtifactWriteRequest('artifact.metadata', 'source/metadata.json', record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.disclosed-source', 'source',
        record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    if sibling:
        requests.append(replace(requests[0], logical_artifact_id='artifact.foreign-sibling',
            relative_path='source/foreign.blob'))
    publications = plane.write_batch(tuple(requests))
    binary = _external('binary', 'artifact.source', payload)
    metadata = _external('metadata', 'artifact.metadata', record.canonical_bytes(), record.SCHEMA, 'application/json')
    root = Path(plane.root.contract.canonical_path)
    return SimpleNamespace(plane=plane, codec=codec, payload=payload, record=record, external=binary,
        metadata=metadata, scope=_DisclosedScope(), source_path=root/'source/source.blob',
        bindings={binary.input_id:root/'source/source.blob', metadata.input_id:root/'source/metadata.json'},
        publications=publications)


def _guard(case, *, selected=None, records=None):
    return owner._published_source_manifest_preflight(
        selected_inputs=(case.external, case.metadata) if selected is None else selected,
        bindings=case.bindings, artifact_writer=case.plane, storage_codecs=(case.codec,),
        source_records=(case.record,) if records is None else records,
        original_input_access=case.scope, check_access=case.scope.require_current)


def test_exact_selected_intrinsic_source_and_metadata_sibling_retain_original_labels(tmp_path):
    case = _source_case(tmp_path)
    before = case.source_path.read_bytes()
    guard = _guard(case)
    manifest = case.plane.read_manifest('source/source.blob')
    case.plane.verify_manifest(manifest, before_member=guard)
    assert case.scope.samples > 2 and case.scope.authored_member_calls == 0
    assert manifest.logical.outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert manifest.logical.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
    assert manifest.logical.lineage_parents == ()
    assert case.source_path.read_bytes() == before


def test_unknown_blind_publication_sibling_refuses_before_its_first_body_open(tmp_path, monkeypatch):
    case = _source_case(tmp_path, sibling=True)
    original_open = os.open
    def no_foreign(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path).name == 'foreign.blob':
            pytest.fail('unknown sibling body opened before exact selected-source refusal')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', no_foreign)
    with pytest.raises(PermissionError, match='outside its exact selected source census'):
        guard = _guard(case)
        case.plane.verify_manifest(case.plane.read_manifest('source/source.blob'), before_member=guard)


def test_model_bearing_selected_record_cannot_omit_actual_parents_even_when_published_blind(tmp_path, monkeypatch):
    case = _source_case(tmp_path)
    case.scope.protected_record = case.record
    case.scope.parents = (ArtifactLineageParent(ObjectIdentity('original.disclosed', Config.SCHEMA,
        Config.VERSION, 'a'*64), VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.EVALUATION_SEALED),)
    monkeypatch.setattr(case.plane, 'verify_manifest', lambda *args, **kwargs: pytest.fail('body verification preceded ancestry'))
    with pytest.raises(PermissionError, match='complete actual original-parent census'):
        _guard(case)


@pytest.mark.parametrize('damage', ('id', 'schema', 'media', 'hash', 'path', 'root', 'size'))
def test_selected_source_metadata_substitution_refuses_before_any_body(tmp_path, monkeypatch, damage):
    case = _source_case(tmp_path)
    read = case.plane.read_manifest
    manifest = read('source/source.blob')
    if damage in ('id', 'schema', 'media', 'hash'):
        changes = {'id':{'logical_artifact_id':'artifact.foreign'}, 'schema':{'payload_schema':Config.SCHEMA},
            'media':{'media_type':'application/x-foreign'}, 'hash':{'content_sha256':'f'*64}}[damage]
        construct = lambda: replace(manifest, logical=replace(manifest.logical, **changes))
    else:
        changes = {'path':{'relative_path':'source/foreign.blob'}, 'root':{'storage_root_id':'root.foreign'},
            'size':{'size_bytes':manifest.materialization.size_bytes+1}}[damage]
        construct = lambda: replace(manifest, materialization=replace(manifest.materialization, **changes))
    monkeypatch.setattr(case.plane, 'verify_manifest', lambda *args, **kwargs: pytest.fail('substituted source body opened'))
    with pytest.raises((PermissionError, ValueError)):
        changed = construct()
        monkeypatch.setattr(case.plane, 'read_manifest', lambda path, **kwargs:
            changed if path == 'source/source.blob' else read(path, **kwargs))
        _guard(case)


def _author_case(case, monkeypatch):
    declaration = _declaration('use', case.codec)
    factory = declaration.provider_factory()
    monkeypatch.setattr(recursive_operations, 'operation_factories', lambda: (factory,))
    original, _, _ = fixture()
    operation = replace(original.operations[1], selection=factory.registration.selection,
        resource_budget=replace(BUDGET, output_bytes=None))
    draft = replace(original, draft_id='draft.disclosed-published-source', requirements=(), connections=(), suppliers=(),
        operations=(operation,), external_inputs=(case.external,), links=(RecursiveInputLink(
            'edge.disclosed-source', 'use', 'operand', external_input_id=case.external.input_id,
            scientific_role='SOURCE'),), selected_operation_ids=('use',))
    observed = owner.implementation_binding(ROOT)
    monkeypatch.setattr(owner, 'implementation_binding', lambda _root: observed)
    destination = Path(case.plane.root.contract.canonical_path) / 'authored'
    return draft, destination


def test_public_author_uses_exact_blind_source_guard_then_keeps_new_alias_development(tmp_path, monkeypatch):
    # This positive uses a singleton source publication; the closed sibling
    # controls above separately exercise complete selected metadata membership.
    case = _source_case(tmp_path)
    # Select both source members in the preflight without inventing an unused
    # scientific graph edge by publishing a separate singleton binary original.
    singleton = case.plane.write(_request(case.payload, logical_artifact_id='artifact.singleton',
        relative_path='singleton/source.blob', publication_scope_id='publication.disclosed-singleton',
        publication_scope_relative_root='singleton', visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        outcome_access=OutcomeAccess.OUTCOME_BLIND))
    case.external = _external('singleton', 'artifact.singleton', case.payload)
    case.source_path = case.plane.root.resolve(singleton.materialization.relative_path, for_write=False)
    draft, destination = _author_case(case, monkeypatch)
    report = owner.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=case.plane,
        output_dir=destination, input_bindings=((case.external.input_id, case.source_path),),
        _original_input_access=case.scope, _source_custody_records=(('metadata', case.record),))
    assert report['task_count'] == 1 and report['native_contact'] == 'none'
    assert report['scientific_authority'] == 'NONE' and report['qualification'] == 'NOT_ESTABLISHED'
    name = 'external-' + sha256(case.external.input_id.encode()).hexdigest()[:24] + case.codec.filename_suffix
    alias = case.plane.read_manifest((destination/name).relative_to(case.plane.root.contract.canonical_path).as_posix())
    assert (alias.logical.outcome_access, alias.logical.visibility_ceiling, alias.logical.lineage_parents) == (
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, ())
    assert (destination/name).read_bytes() == case.payload == case.source_path.read_bytes()
    original = case.plane.read_manifest(singleton.materialization.relative_path)
    assert original.logical == singleton.logical and original.materialization == singleton.materialization


def test_expiry_after_metadata_preflight_refuses_before_source_hash_and_author_output(tmp_path, monkeypatch):
    case = _source_case(tmp_path)
    draft, destination = _author_case(case, monkeypatch)
    verify = case.plane.verify_manifest
    def expired(manifest, **kwargs):
        case.scope.current = False
        return verify(manifest, **kwargs)
    monkeypatch.setattr(case.plane, 'verify_manifest', expired)
    original_open = os.open
    def no_late_body(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path) == case.source_path:
            pytest.fail('expired original permission reached a source body hash')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', no_late_body)
    with pytest.raises(PermissionError, match='expired before source read'):
        owner.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=case.plane,
            output_dir=destination, input_bindings=((case.external.input_id, case.source_path),),
            _original_input_access=case.scope,
            _source_custody_records=(('metadata', case.record),))
    assert not destination.exists()


def test_unknown_canonical_source_does_not_gain_intrinsic_blind_permission(tmp_path, monkeypatch):
    case = _source_case(tmp_path)
    monkeypatch.setattr(case.plane, 'verify_manifest', lambda *args, **kwargs:
        pytest.fail('unknown canonical body reached verification'))
    with pytest.raises(PermissionError, match='unowned source/sibling'):
        _guard(case, selected=(case.metadata,), records=())
