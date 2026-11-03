# SPDX-License-Identifier: MPL-2.0
"""Exact locator-protocol metadata, not scientific packages or permission.

Only the packet, instance and association have authenticated body custody here.
Literal unmaterialized draft/implementation pins cannot complete a lifecycle;
An unrelated metadata sibling and separate sealed specification detect premature body reads.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import ClassVar
import os

import pytest

from empirical_lawhood.adapters.composition import generated_extension_bundles as declarations
from empirical_lawhood.api import experiment_preparation as preparation
from empirical_lawhood.api import experiment_read_access as owner
from empirical_lawhood.api import generated_experiment_runtime_bindings as installed
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding, ExperimentProtocolDeclaration
from empirical_lawhood.runtime.prospective_experiment import ProspectiveExperimentAssociation, instance_identity
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_experiment_read_access import install_locator_codecs
from tests.test_rubisco_gas_contrast import _real_plane


@dataclass(frozen=True, slots=True)
class _Specification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/tests/read-access-protocol-specification'
    record_id: str

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def _forbidden(*args, **kwargs):
    raise AssertionError('protocol selection opened scientific data or discovered operations')


def _pin(name, schema, digest='a'):
    return ObjectIdentity(name, schema, '1.0.0', digest * 64)


def _metadata_case(tmp_path, monkeypatch, *, prospective, damage=None, transport_alias=False):
    plane = _real_plane(tmp_path / 'guarded')
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    specification = _Specification('specification.disclosed')
    draft = _pin('draft.disclosed', RecursiveStudyDraft.SCHEMA)
    implementation = _pin('implementation.disclosed', 'empirical-lawhood/runtime/recursive-implementation-binding')
    instance = ExperimentInstanceBinding(specification.identity,
        _pin('allocation.disclosed', UnitAllocation.SCHEMA),
        replace(draft, object_id='draft.foreign') if damage == 'foreign-draft' else draft,
        _pin('projection.disclosed', 'empirical-lawhood/planning/recursive-scientific-selection'),
        _pin('campaign.disclosed', 'empirical-lawhood/planning/campaign'))
    if damage == 'unknown-version':
        instance = replace(instance, specification=replace(instance.specification, object_version='99.0.0'))
    specification_pin = (replace(instance.specification, object_id='specification.foreign')
        if damage == 'foreign-specification' else replace(instance.specification,
            object_id='recursive-member.experiment-specification') if transport_alias else instance.specification)
    if damage == 'foreign-specification-bytes':
        specification_pin = replace(specification_pin, object_fingerprint='f' * 64)
    instance_pin = instance_identity(instance)
    instance_member_pin = (replace(instance_pin, object_fingerprint='f' * 64)
        if damage == 'foreign-instance' else instance_pin)
    common = (
        RecursiveWaveMember('experiment-instance.json', instance_member_pin, len(instance.canonical_bytes())),
        RecursiveWaveMember('experiment-specification.json', specification_pin, len(specification.canonical_bytes())),
    )
    packet_members = tuple(sorted((RecursiveWaveMember('draft.json', draft, 1),
        RecursiveWaveMember('implementation.json', implementation, 1), *common), key=lambda row: row.filename))
    packet = AuthoredRecursiveWave('packet.disclosed', draft, implementation, packet_members)
    companion_members = tuple(sorted((*common,
        RecursiveWaveMember('experiment-allocation.json', instance.allocation, 1)), key=lambda row: row.filename))
    packet_pin = ObjectIdentity.from_record(packet.packet_id, packet)
    association = ProspectiveExperimentAssociation('association.disclosed',
        replace(packet_pin, object_id='packet.foreign') if damage == 'foreign-packet' else packet_pin,
        _pin('candidate.disclosed', 'empirical-lawhood/runtime/executable-study-candidate'),
        instance_member_pin, companion_members)
    rows = [('authored/prospective/authored-wave.json' if prospective else 'authored/authored-wave.json', packet, False),
        ('authored/experiment/experiment-instance.json' if prospective else 'authored/experiment-instance.json', instance, False),
        ('authored/experiment/experiment-specification.json' if prospective else 'authored/experiment-specification.json', specification, True),
        ('authored/private.json', Config('unused.metadata.disclosed', 17), False)]
    if prospective:
        rows.append(('authored/experiment/experiment-association.json', association, False))
    blind_pair = ((OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE) if prospective else
        (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
    # Publication classes are homogeneous. The intrinsic packet batch has an
    # unrelated sibling; its separately published sealed specification is pinned
    # but must never be opened merely to choose an operational locator codec.
    for protected in (False, True):
        plane.write_batch(tuple(ArtifactWriteRequest('artifact.protocol.' + str(index), path, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json',
            'publication.protocol-metadata.' + ('sealed' if protected else 'intrinsic'), 'authored',
            record.canonical_bytes(), VisibilityCeiling.OUTCOME_VISIBLE if protected else blind_pair[1], (),
            OutcomeAccess.EVALUATION_SEALED if protected else blind_pair[0])
            for index, (path, record, is_protected) in enumerate(rows) if is_protected == protected))
    bindings = install_locator_codecs(monkeypatch)
    monkeypatch.setattr(installed, 'EXPERIMENT_SPECIFICATION_PROTOCOLS',
        ((_Specification.SCHEMA, _Specification.VERSION, bindings[0].protocol_id),))
    monkeypatch.setattr(preparation, 'experiment_protocols', _forbidden)
    return plane, directory, rows, bindings[0].protocol_id


def _no_model_body(monkeypatch):
    opened = []
    original = os.open

    def selected(path, *args, **kwargs):
        if not isinstance(path, int):
            name = Path(path).name
            if name in ('private.json', 'experiment-specification.json', 'draft.json', 'implementation.json'):
                pytest.fail('locator protocol selection opened a protected or unrelated sibling body: ' + name)
            opened.append(name)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', selected)
    return opened


@pytest.mark.parametrize('prospective', (False, True))
@pytest.mark.parametrize('transport_alias', (False, True))
def test_retained_protocol_uses_only_pinned_intrinsic_metadata_without_sibling_hashes(
        tmp_path, monkeypatch, prospective, transport_alias):
    plane, directory, rows, protocol = _metadata_case(tmp_path, monkeypatch,
        prospective=prospective, transport_alias=transport_alias)
    before = {path: (Path(plane.root.contract.canonical_path) / path).read_bytes() for path, _, _ in rows}
    monkeypatch.setattr(plane, 'verify_manifest', _forbidden)
    monkeypatch.setattr(plane, 'verify_manifests', _forbidden)
    os_open = os.open
    opened = _no_model_body(monkeypatch)
    assert owner.experiment_read_access_protocol(directory=directory, artifact_writer=plane) == protocol
    assert 'authored-wave.json' in opened and 'experiment-instance.json' in opened
    # No publication or input rewrite, including all forbidden sibling bodies.
    monkeypatch.setattr(os, 'open', os_open)
    assert {path: (Path(plane.root.contract.canonical_path) / path).read_bytes() for path, _, _ in rows} == before


@pytest.mark.parametrize('prospective', (False, True))
@pytest.mark.parametrize('damage', ('foreign-draft', 'foreign-specification',
    'foreign-specification-bytes', 'foreign-instance', 'unknown-version'))
def test_foreign_retained_join_refuses_without_scientific_or_locator_body_read(
        tmp_path, monkeypatch, prospective, damage):
    plane, directory, _, _ = _metadata_case(tmp_path, monkeypatch, prospective=prospective, damage=damage)
    _no_model_body(monkeypatch)
    with pytest.raises((PermissionError, ValueError), match='substitutes|canonical locator|packet-pinned|companion-pinned|specification owner'):
        owner.experiment_read_access_protocol(directory=directory, artifact_writer=plane)


def test_foreign_prospective_packet_refuses_before_other_body_reads(tmp_path, monkeypatch):
    plane, directory, _, _ = _metadata_case(tmp_path, monkeypatch, prospective=True, damage='foreign-packet')
    _no_model_body(monkeypatch)
    with pytest.raises(PermissionError, match='association-pinned packet'):
        owner.experiment_read_access_protocol(directory=directory, artifact_writer=plane)


def test_editable_specification_selects_exact_owner_without_operation_discovery(tmp_path, monkeypatch):
    bindings = install_locator_codecs(monkeypatch)
    declaration = ExperimentProtocolDeclaration(bindings[0].protocol_id, _Specification,
        _forbidden, 'consumer.disclosed.protocol')
    monkeypatch.setattr(declarations, 'EXPERIMENT_PROTOCOL_DECLARATIONS', (declaration,))
    path = tmp_path / 'specification.json'
    raw = _Specification('specification.disclosed').canonical_bytes()
    path.write_bytes(raw)
    assert owner.experiment_read_access_protocol(specification_path=path) == bindings[0].protocol_id
    assert path.read_bytes() == raw


@pytest.mark.parametrize('selection', ('neither', 'both', 'no-plane', 'composite'))
def test_unsupported_protocol_selection_refuses_before_locator_file_open(tmp_path, monkeypatch, selection):
    install_locator_codecs(monkeypatch)
    if selection == 'neither':
        options = {}
    elif selection == 'both':
        options = dict(specification_path=tmp_path / 'unopened.json', directory=tmp_path)
    elif selection == 'no-plane':
        options = dict(directory=tmp_path)
    else:
        plane = _real_plane(tmp_path / 'guarded')
        directory = Path(plane.root.contract.canonical_path) / 'composite'
        directory.mkdir()
        options = dict(directory=directory, artifact_writer=plane)
    with pytest.raises(ValueError, match='exactly one|actual selected artifact plane|ordinary retained lifecycle'):
        owner.experiment_read_access_protocol(**options)
