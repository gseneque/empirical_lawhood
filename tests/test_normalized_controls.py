# SPDX-License-Identifier: MPL-2.0
"""Closed operational views preserve original bytes, semantics and custody."""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from typing import ClassVar

import pytest

from empirical_lawhood.infrastructure.recursive_control_read import (
    CONTROL_VIEWS, decode_authored_control, normalized_plan_views,
)
from empirical_lawhood.kernel import decoding
from empirical_lawhood.kernel.normalized_control import NormalizedCanonicalControl, _content_tree, _document, _json
from empirical_lawhood.kernel.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class Operand(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/normalized-operand'
    label: str
    value: Decimal

    def __post_init__(self):
        if self.value < 0:
            raise ValueError('negative operand')


@dataclass(frozen=True, slots=True)
class Control(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/normalized-control'
    operands: tuple[Operand, ...]


def _case():
    operand = Operand('shared scientific operand ' * 320, Decimal('0.123456789012345678901234567890123456789'))
    return Control((operand,) * 96)


def test_closed_shared_view_restores_exact_bytes_with_one_operand_construction(monkeypatch, record_property):
    original = _case()
    raw = original.canonical_bytes()
    view = NormalizedCanonicalControl.from_record('recursive-member.run-plan', original)
    assert view.canonical_size_bytes() < len(raw) // 4
    assert NormalizedCanonicalControl.from_record('recursive-member.run-plan', original) == view
    validations = []
    validate = Operand.__post_init__
    def observed(self):
        validations.append(self.value)
        validate(self)
    monkeypatch.setattr(Operand, '__post_init__', observed)
    with localcontext() as context:
        context.prec = 8
        result = view.restore(raw, Control, maximum_bytes=len(raw))
    assert result == original and result.canonical_bytes() == raw
    assert len(validations) == 1
    assert result.operands[0] is result.operands[-1]
    record_property('normalized_control_work', dict(original_bytes=len(raw), view_bytes=view.canonical_size_bytes(),
        repeated_operands=len(original.operands), operand_constructions=len(validations), exact_bytes=True))


@pytest.mark.parametrize('damage', ('original', 'bound', 'type', 'node', 'missing', 'duplicate', 'unused', 'size', 'forward', 'binary'))
def test_view_refuses_changed_original_or_malformed_complete_graph(damage):
    original = _case()
    raw = original.canonical_bytes()
    view = NormalizedCanonicalControl.from_record('recursive-member.run-plan', original)
    with pytest.raises((ValueError, TypeError)):
        if damage == 'original':
            view.restore(raw.replace(b'shared', b'altered', 1), Control, maximum_bytes=len(raw) + 1)
        elif damage == 'bound':
            view.restore(raw, Control, maximum_bytes=len(raw) - 1)
        elif damage == 'type':
            view.restore(raw, Operand, maximum_bytes=len(raw))
        elif damage == 'size':
            replace(view, original_size_bytes=len(raw) - 1)
        else:
            graph = json.loads(view.graph_json)
            if damage == 'node':
                graph['nodes'][0][0] = '0' * 64
            elif damage == 'missing':
                graph['nodes'].pop(0)
            elif damage == 'duplicate':
                graph['nodes'].append(graph['nodes'][0])
            elif damage == 'forward':
                graph['nodes'].reverse()
            elif damage == 'unused':
                body = ['seq', [[0, 'unused']]]
                graph['nodes'].append([sha256(_json(body).encode()).hexdigest(), body])
            elif damage == 'binary':
                graph['extra'] = 1.5
            replace(view, graph_json=_json(graph))


def test_view_cannot_hide_wrong_graph_behind_correct_original_pin(monkeypatch):
    original = _case()
    wrong = Control((replace(original.operands[0], value=Decimal('0.923456789012345678901234567890123456789')), ) * 96)
    raw = original.canonical_bytes()
    view = NormalizedCanonicalControl.from_record('recursive-member.run-plan', wrong)
    view = replace(view, original=replace(view.original, object_fingerprint=original.fingerprint()))
    with pytest.raises(ValueError, match='not canonical'):
        view.restore(raw, Control, maximum_bytes=len(raw))
    correct = NormalizedCanonicalControl.from_record('recursive-member.run-plan', original)
    def reject(_self):
        raise ValueError('current operand validator refuses')
    monkeypatch.setattr(Operand, '__post_init__', reject)
    with pytest.raises(ValueError, match='current operand validator'):
        correct.restore(raw, Control, maximum_bytes=len(raw))


def test_legacy_fallback_and_new_closed_view_keep_selected_reader_contract(monkeypatch):
    record = _case()
    original = record.canonical_bytes()
    payloads = {'run-plan.json': original}
    assert decode_authored_control(payloads, 'run-plan.json', Control) == record
    views = normalized_plan_views({'run-plan.json': record, 'execution-plan.json': record})
    assert set(views) == set(CONTROL_VIEWS.values())
    payloads.update({name: value.canonical_bytes() for name, value in views.items()})
    def no_expanded_parse(*args, **kwargs):
        if args[1] is Control:
            raise AssertionError('normalised view reparsed the expanded original')
        return decode(*args, **kwargs)
    decode = decoding._decode_canonical_bytes
    monkeypatch.setattr(decoding, '_decode_canonical_bytes', no_expanded_parse)
    assert decode_authored_control(payloads, 'run-plan.json', Control) == record
    payloads['run-plan.normalized.json'] = b'{}\n'
    with pytest.raises(ValueError):
        decode_authored_control(payloads, 'run-plan.json', Control)


def test_small_controls_keep_original_only_representation():
    small = Control((Operand('small', Decimal(1)),))
    assert normalized_plan_views({'run-plan.json': small, 'execution-plan.json': small}) == {}


def test_normalized_selection_keeps_smaller_custody_policy_and_avoids_unique_graph_work(monkeypatch):
    from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits
    record = _case()
    for limits in (ArtifactCustodyLimits(control_record_bytes=1), ArtifactCustodyLimits(in_memory_payload_bytes=1),
            ArtifactCustodyLimits(canonical_json_token_bytes=1024), ArtifactCustodyLimits(canonical_json_depth=32)):
        assert normalized_plan_views({'run-plan.json': record, 'execution-plan.json': record}, custody_limits=limits) == {}
    unique = Control(tuple(replace(record.operands[0], label=f'{index:03d}' + record.operands[0].label) for index in range(96)))
    def forbidden(*args):
        raise AssertionError('unshared control should not build a normalised graph')
    monkeypatch.setattr(NormalizedCanonicalControl, 'from_record', forbidden)
    assert normalized_plan_views({'run-plan.json': unique, 'execution-plan.json': unique}) == {}


def test_reserved_literal_keys_and_exponential_expansion_are_not_ambiguous():
    # Complete auxiliary graph controls only; these are not scientific records.
    body = {'$literal': [['$ref', 'literal text']]}
    raw = _json({'$ref': 'literal text'}).encode() + b'\n'
    graph = _json({'nodes': [[sha256(_json(body).encode()).hexdigest(), body]], 'root': 0})
    assert _document(graph, len(raw)) == {'$ref': 'literal text'}
    nodes, identities = [], []
    for index in range(30):
        body = 'x' if index == 0 else [{'$ref': index - 1}, {'$ref': index - 1}]
        identity = sha256(_json(_content_tree(body, identities)).encode()).hexdigest()
        nodes.append([identity, body])
        identities.append(identity)
    with pytest.raises(ValueError, match='expansion exceeds'):
        _document(_json({'nodes': nodes, 'root': 29}), 1024)


@pytest.mark.parametrize('damage', ('original', 'view', 'revoked', 'final-view'))
def test_normalized_reader_keeps_both_publications_current_and_complete(tmp_path, damage):
    from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
    from tests.test_artifact_publication_admission import _plane, _requests
    plane = _plane(tmp_path / 'custody')
    record = _case()
    view = NormalizedCanonicalControl.from_record('recursive-member.run-plan', record)
    records = {'run-plan.json': record, 'run-plan.normalized.json': view}
    requests = tuple(replace(request, relative_path='authored/' + name, publication_scope_relative_root='authored',
        payload_schema=value.SCHEMA, payload=value.canonical_bytes())
        for request, (name, value) in zip(_requests(2), records.items(), strict=True))
    plane.write_batch(requests)
    members = tuple(RecursiveWaveMember(name, ObjectIdentity.from_record('software.' + name, value), value.canonical_size_bytes())
        for name, value in records.items())
    class Access:
        active = True
        def require_current(self):
            if not self.active:
                raise PermissionError('original access revoked')
        def require_member(self, _manifest):
            self.require_current()
    access = Access()
    with pytest.raises((ValueError, RuntimeError, OSError)):
        with plane.read_context() as writer:
            payloads = AuthenticatedRecursivePayloads(plane=writer, directory=tmp_path / 'custody/authored',
                members=members, original_input_access=access)
            assert decode_authored_control(payloads, 'run-plan.json', Control) == record
            if damage == 'revoked':
                access.active = False
            else:
                name = 'run-plan.json' if damage == 'original' else 'run-plan.normalized.json'
                path = payloads.directory / name
                path.write_bytes(b'[' + path.read_bytes()[1:])
            if damage != 'final-view':
                decode_authored_control(payloads, 'run-plan.json', Control)


def _public_draft():
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts import RCPrerequisiteChainConfig
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
    from tests.test_recursive_public_service import ROOT
    config = decoding.decode_canonical_bytes((ROOT / 'programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json').read_bytes(),
        RCPrerequisiteChainConfig, maximum_bytes=8 * 1024**2)
    return rc_recursive_draft(config, unit_ids=tuple(unit.unit_id for unit in config.units), include_summary=False)


def test_actual_compiled_plan_view_size_and_exact_reconstruction(record_property):
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    registrations, registry, codecs = operation_catalog()
    compiled = compile_recursive_wave(draft=_public_draft(), registrations=registrations, registry=registry,
        implementation_commit='a' * 40, run_plan_id='software.normalized-plan', output_codecs=codecs)
    sizes = {}
    for name, record in (('run-plan', compiled.run_plan), ('execution-plan', compiled.execution_plan)):
        raw = record.canonical_bytes()
        view = NormalizedCanonicalControl.from_record('recursive-member.' + name, record)
        restored = view.restore(raw, type(record), maximum_bytes=len(raw))
        assert restored == record and restored.canonical_bytes() == raw
        sizes[name] = {'original_bytes': len(raw), 'view_bytes': view.canonical_size_bytes()}
    record_property('actual_compiled_plan_sizes', sizes)


def test_public_author_and_control_readers_keep_exact_originals_and_normalized_members(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_authoring as author, recursive_execution as execution
    from empirical_lawhood.api import experiment_execution_read as observation
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.infrastructure import recursive_control_read as controls
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from tests.test_artifact_publication_admission import _census, _plane
    from tests.test_recursive_public_service import ROOT, _draft
    # Force optional views for this small public fixture. Production selection
    # and substantial savings have separate controls above; no task can execute.
    originals = {}
    def selected(records, **options):
        originals.update({name: records[name].canonical_bytes() for name in CONTROL_VIEWS})
        return {view_name: NormalizedCanonicalControl.from_record('recursive-member.' + name.removesuffix('.json'), records[name])
            for name, view_name in CONTROL_VIEWS.items()}
    monkeypatch.setattr(controls, 'normalized_plan_views', selected)
    def forbidden(*args, **kwargs):
        raise AssertionError('normalised metadata acceptance cannot execute tasks')
    monkeypatch.setattr(LocalProcessExecutor, 'execute', forbidden)
    plane = _plane(tmp_path / 'public')
    plane.validators = integration_artifact_profile_validators()
    directory = tmp_path / 'public/authored'
    report = author.author_recursive_wave(draft=_draft(), project_root=ROOT, artifact_writer=plane, output_dir=directory)
    packet, draft, _, payloads = author.load_authored_wave(directory=directory, artifact_writer=plane, lazy_payloads=True)
    assert set(CONTROL_VIEWS.values()) <= {member.filename for member in packet.members}
    for name, view_name in CONTROL_VIEWS.items():
        assert (directory / name).read_bytes() == originals[name]
        logical, auxiliary = payloads.manifest(name).logical, payloads.manifest(view_name).logical
        assert (logical.outcome_access, logical.visibility_ceiling, logical.lineage_parents) == (
            auxiliary.outcome_access, auxiliary.visibility_ceiling, auxiliary.lineage_parents)
    before = _census(tmp_path / 'public')
    run, plan, _ = execution._retained_plans(payloads, draft)
    observed = observation.load_development_execution_controls(directory=directory, artifact_writer=plane)
    assert observed[1] == run and observed[2] == plan
    with observation.observed_development_authoring(directory=directory, artifact_writer=plane, authoring_report=report) as result:
        assert result['status'] == 'UNENTERED' and result['new_native_contact_count'] == 0
    assert _census(tmp_path / 'public') == before
    (directory / 'execution-plan.normalized.json').write_bytes(b'{}\n')
    with pytest.raises((ValueError, RuntimeError, OSError)):
        observation.load_development_execution_controls(directory=directory, artifact_writer=plane)
