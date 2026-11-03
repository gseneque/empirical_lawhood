# SPDX-License-Identifier: MPL-2.0
"""Pure prospective preparation joins; fixtures confer no scientific authority."""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, ExperimentCensus, ExperimentPreparation
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig
from tests.runtime_platform.test_recursive_prospective_workflow import _authored_handoff_fixture


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    handoff, _, _, plane, _, _, _, _ = _authored_handoff_fixture(tmp_path, monkeypatch)
    spec = decode_canonical_bytes((handoff.directory / 'recursive-prospective.json').read_bytes(),
        RecursiveProspectiveAuthoringSpec, maximum_bytes=16 * 1024**2)
    configurations = []
    for digest in sorted({row.source_config_sha256 for row in spec.draft.prospective_draft.source_materializations}):
        path = plane.root.resolve('candidate-inputs/sha256/' + digest[:2] + '/' + digest, for_write=False)
        configurations.append(decode_canonical_bytes(path.read_bytes(), SourceMaterializationConfig, maximum_bytes=1024**2))
    identity = ObjectIdentity('specification.synthetic-prospective',
        'empirical-lawhood/testing/prospective-specification', '1.0.0', 'a' * 64)
    allocation = UnitAllocation('allocation.synthetic-prospective', (identity,),
        (IndependentUnit('unit.synthetic-prospective', identity.object_id, 'stratum.synthetic',
            ('view.synthetic',), False),), (UnitRoleAssignment('unit.synthetic-prospective', 'synthetic-role'),))
    census = ExperimentCensus((('synthetic-role', 1),), (('synthetic-role', 1),), (), (), 0)
    return ExperimentPreparation(identity, census, (), allocation=allocation, draft=spec.draft,
        prospective_spec=spec, source_configs=tuple(configurations), execution=ExecutionSelection(workers=1))


def test_preparation_retains_exact_typed_prospective_owner_and_separate_configurations(prepared):
    assert prepared.executable
    assert prepared.prospective_spec.draft == prepared.draft
    assert tuple(record.fingerprint() for record in prepared.source_configs) == tuple(sorted({
        row.source_config_sha256 for row in prepared.draft.prospective_draft.source_materializations}))


@pytest.mark.parametrize('changed', ('missing-config', 'duplicate-config', 'wrong-config', 'wrong-draft',
    'wrong-owner-type', 'unowned-config', 'config-list'))
def test_prospective_owner_and_exact_source_configuration_roster_refuse_changes(prepared, changed):
    with pytest.raises((TypeError, ValueError)):
        if changed == 'missing-config':
            replace(prepared, source_configs=())
        elif changed == 'duplicate-config':
            replace(prepared, source_configs=prepared.source_configs * 2)
        elif changed == 'wrong-config':
            original, = prepared.source_configs
            replace(prepared, source_configs=(replace(original, config_id='configuration.unselected'),))
        elif changed == 'wrong-draft':
            replace(prepared, prospective_spec=replace(prepared.prospective_spec,
                draft=replace(prepared.draft, draft_id='draft.unselected')))
        elif changed == 'wrong-owner-type':
            replace(prepared, prospective_spec=prepared.draft)
        elif changed == 'unowned-config':
            replace(prepared, prospective_spec=None)
        else:
            replace(prepared, source_configs=list(prepared.source_configs))
