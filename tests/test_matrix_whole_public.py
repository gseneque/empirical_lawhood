# SPDX-License-Identifier: MPL-2.0
"""Disclosed copied-input controls through the actual whole-programme CLI.

All populations and credentials are software controls, never fresh science.
Only input construction uses fixture seams; programme progression and public
storage selection use their production owners.
"""
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import NativeTrainingAssemblyRequest
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import PROTOCOL_ID, MatrixResearchProgrammeSpecification
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.cli.app import app
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
from tests.test_matrix_c25_protected_development_lifecycle import ROOT, _exposed_inputs, _profile, _profile_for_path
from tests.test_matrix_programme_e1 import scientific_context

def copied_whole_inputs(tmp_path):
    from tests import test_matrix_programme_scientific_design as mathematical
    from empirical_lawhood.kernel.authority import AuthorityAction, ResourceBudget
    from empirical_lawhood.kernel.status import LifecycleStatus
    from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
    original = mathematical.build_scientific_design

    def selected_design():
        design = original()
        context = scientific_context(design, 'native-training.disclosed-whole')
        system = context.system
        return replace(design, e1_criterion=replace(design.e1_criterion,
            system_id=system.system_id, world_id=system.world.world_id,
            relation=ObjectIdentity.from_record(system.relation.relation_id, system.relation),
            independent_unit_id=system.independent_unit.unit_id))

    def operator_contract(path):
        from empirical_lawhood.runtime.operator_profile import resolve_external_root_contract
        return resolve_external_root_contract(_profile_for_path(path), repo_root=ROOT, home_root=Path.home())

    # End construction seams before invoking any public programme operation.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(mathematical, 'build_scientific_design', selected_design)
        case = _exposed_inputs(tmp_path / 'original-inputs', root_contract_factory=operator_contract)
    root = Path(case.plane.root.contract.canonical_path)
    design = case.committed.scientific_design
    context = scientific_context(design, case.committed.commitments.namespace)
    system, policy = context.system, context.system.authority_policy
    prototype = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json').read_bytes(),
        MatrixResearchProgrammeSpecification, maximum_bytes=None)
    operations = prototype.operations
    resources = operations.e1.resources
    campaign_budget = ResourceBudget(resources.maximum_parallel_tasks,
        resources.aggregate_memory_ceiling_bytes, 0, None, None, None)
    node = CampaignNode('node.disclosed.whole.e1', CampaignNodeKind.CLAIM,
        CampaignLane.PROSPECTIVE, ObjectIdentity.from_record(context.claims[0].claim_id, context.claims[0]),
        (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.disclosed.whole.e1', context.question,
        (system.system_id,), (system.world.world_id,), (context.claims[0].claim_id,),
        campaign_budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('right.disclosed.whole.e1', AuthorityAction.SIMULATION_EXECUTION,
            policy.delegate_id, policy.policy_id, True),), (node,), (node.node_id,),
        (node.node_id,), (), LifecycleStatus.ACTIVE)
    training = NativeTrainingAssemblyRequest('request.disclosed.whole.train',
        case.training.request.resources, case.training.request.campaign)
    cutoff = case.preparation.fit_config.fit_cutoff
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity
    nominal_pin = dict(design.e3.role_coordinates)['CALIBRATION']
    nominal, = (coordinate for coordinate in design.training_protocol.coordinates
        if coordinate_identity(coordinate) == nominal_pin)
    e3 = replace(operations.e3, computability_evidence=replace(operations.e3.computability_evidence,
        numerical_view_ids=tuple(sorted((nominal.primary_view.view_id, nominal.fine_view.view_id)))))
    operations = replace(operations, e3=e3,
        e1=replace(operations.e1, scientific_context=context, campaign=campaign),
        e2=replace(operations.e2, resources=training.resources, campaign=training.campaign),
        training=training,
        source_metadata=replace(operations.source_metadata, physical_cutoff=cutoff,
            source_computability_evidence=case.preparation.root.experiment.obligations.computability,
            metadata_private_key_relative_path='programme/metadata-keys/source.ed25519',
            allow_metadata_key_creation=True, metadata_valid_from_utc=None),
        prepared=replace(operations.prepared, campaign=case.preparation.root.campaign, cutoff=cutoff))
    specification = MatrixResearchProgrammeSpecification('programme.disclosed.whole',
        'programme', case.commitment, operations)
    profile = _profile(case.plane)
    scratch = Path(profile.external_root_locator) / profile.scientific_scratch_namespace
    scratch.mkdir(mode=0o700)
    directory = root / 'copied-programme'
    directory.mkdir()
    source = implementation_binding(ROOT)
    selector = ExperimentFileInputSelection('inputs.disclosed.whole',
        PROTOCOL_ID, (), ())
    for name, value in (('specification', specification), ('sources', selector),
            ('source-snapshot', source), ('operator-profile', profile), ('artifact-root', case.plane.root.contract)):
        (directory / (name + '.json')).write_bytes(value.canonical_bytes())
    return case, directory, specification


def test_copied_whole_programme_cli_derives_actual_initial_frontier_without_native_entry(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    case, copied, specification = copied_whole_inputs(tmp_path)
    root = Path(case.plane.root.contract.canonical_path)

    def forbidden(*_args, **_kwargs):
        pytest.fail('whole-programme metadata derivation entered native execution')

    monkeypatch.setattr(LocalProcessExecutor, 'execute', forbidden)
    monkeypatch.setattr(LocalProcessExecutor, 'execute_deadline_free', forbidden)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', forbidden)
    arguments = ['--project-root', str(ROOT), '--operator-profile', str(copied / 'operator-profile.json'),
        '--artifact-root-contract', str(copied / 'artifact-root.json'),
        '--catalog-relative-path', 'whole-programme.sqlite3', 'campaign', 'experiment-derive-inputs',
        '--input', str(copied / 'specification.json'), '--sources', str(copied / 'sources.json'),
        '--metadata-directory', str(root / specification.directory),
        '--output-selection', str(root / specification.directory / 'sources.json'),
        '--source-snapshot', str(copied / 'source-snapshot.json'), '--environment-id', 'main-locked', '--workers', '4']
    result = CliRunner().invoke(app, arguments)
    assert result.exit_code == 0, result.output
    bindings = root / specification.directory / 'bindings'
    assert {path.name for path in bindings.glob('*.json') if not path.name.endswith('.manifest.json')} == {
        'e1.json', 'e2.json', 'train.json'}
    assert not (root / 'runs').exists()
    assert not (Path(_profile(case.plane).external_root_locator) / 'c25-scratch' / 'whole-programme.sqlite3').exists()


def test_wrong_e3_view_scope_refuses_outer_derivation_before_any_child_or_native_entry(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService

    case, copied, specification = copied_whole_inputs(tmp_path)
    root = Path(case.plane.root.contract.canonical_path)
    e3 = specification.operations.e3
    assert e3.computability_evidence.numerical_view_ids != ('fine-view', 'primary-view')
    changed = replace(specification, operations=replace(specification.operations,
        e3=replace(e3, computability_evidence=replace(e3.computability_evidence,
            numerical_view_ids=('fine-view', 'primary-view')))))
    (copied / 'specification.json').write_bytes(changed.canonical_bytes())

    def forbidden(*_args, **_kwargs):
        pytest.fail('wrong E3 scope reached child projection or native execution')

    monkeypatch.setattr(MatrixResearchProgrammeService, '_project', forbidden)
    monkeypatch.setattr(LocalProcessExecutor, 'execute', forbidden)
    monkeypatch.setattr(LocalProcessExecutor, 'execute_deadline_free', forbidden)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', forbidden)
    result = CliRunner().invoke(app, ['--project-root', str(ROOT),
        '--operator-profile', str(copied / 'operator-profile.json'),
        '--artifact-root-contract', str(copied / 'artifact-root.json'),
        '--catalog-relative-path', 'whole-programme.sqlite3', 'campaign', 'experiment-derive-inputs',
        '--input', str(copied / 'specification.json'), '--sources', str(copied / 'sources.json'),
        '--metadata-directory', str(root / specification.directory),
        '--output-selection', str(root / specification.directory / 'sources.json'),
        '--source-snapshot', str(copied / 'source-snapshot.json'), '--environment-id', 'main-locked', '--workers', '4'])
    assert result.exit_code == 2, result.output
    assert 'Actual scoped computability evidence' in result.output
    assert not (root / specification.directory).exists()
    assert not (root / 'runs').exists()
