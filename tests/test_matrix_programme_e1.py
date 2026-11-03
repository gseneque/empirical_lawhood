# SPDX-License-Identifier: MPL-2.0
"""Exposed current C-to-E1 metadata controls; no acquisition or qualification."""
from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_bindings, compact_preparation
from empirical_lawhood.adapters.methods.matrix_researcher_programme import e1_assembly as domain
from empirical_lawhood.api import matrix_programme_e1 as owner
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, EvidenceRung, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experiments import AssignmentKind, AssignmentSpec, ControlKind, ControlSpec, PrecisionGoal
from empirical_lawhood.kernel.obligations import (
    ClosureSpec, ComputabilityEvidence, FalsifierKind, FalsifierSpec, ObligationStatus,
    ScientificObligations, StructuralConvergenceSpec, SupportSpec, UncertaintySpec, ValiditySpec,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.quantities import QuantityKind, QuantitySpec, ResponseDirection
from empirical_lawhood.kernel.status import LifecycleStatus, ReadinessStatus
from empirical_lawhood.kernel.systems import IndependentUnitSpec, RelationalIdentity, SystemBoundaryKind, SystemSpec
from empirical_lawhood.kernel.time import (
    AvailabilitySpec, CausalPhase, ClockLabelSemantics, ClockSpec, HoldSemantics, HorizonSpec, SamplingSemantics,
)
from empirical_lawhood.kernel.worlds import (
    ComputabilityEnvelope, NumericalCoordinateKind, NumericalCoordinateSpec, NumericalViewSpec,
    RandomnessSemantics, WorldKind, WorldSpec,
)
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.runtime.execution_envelope import ChildResourceTokenLimit, NonTimeResourceBudget, ProgressHeartbeat, ProgressLivenessContract
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from tests.test_matrix_programme_allocations import census as census  # noqa: F401

ROOT = Path(__file__).parents[1]


def scientific_context(design, namespace):
    """Direct current mathematical authoring; no old root/template is loaded."""
    prefix = 'disclosed.current-e1'
    coordinate = design.e1_coordinates[0]
    clock, dt = coordinate.clock_id, coordinate.primary_view.timestep
    world = WorldSpec(prefix + '.world', 'Exposed E1 numerical metadata control', WorldKind.NUMERICAL_SIMULATOR,
        ('six-matrix-native-dynamics',), ('physical-material-realization',), (), EvidenceCeiling.RESPONSE,
        frozenset(OutcomeAccess))
    policy = AuthorityPolicy(prefix + '.policy', 'human.disclosed', 'service.disclosed', (namespace,),
        frozenset((WorldKind.NUMERICAL_SIMULATOR,)), frozenset((AuthorityAction.SIMULATION_EXECUTION,
            AuthorityAction.NONACTUATING_PROSPECTIVE_FREEZE, AuthorityAction.EVALUATOR_REVEAL)),
        frozenset((SourceAccessClass.NONE,)), ('actual-current-entry-required',), frozenset(),
        ResourceBudget(4, 16 * 1024**3, 0, None, None, None), OutcomeAccess.EVALUATOR_REVEAL)
    quantities = tuple(sorted((QuantitySpec(prefix + '.' + name, name, kind, unit, unit, 'matrix-frame', clock,
        AvailabilitySpec(clock, phase, access, time), direction) for name, kind, unit, phase, access, time, direction in (
            ('bath', QuantityKind.BOUNDARY, 'temperature', CausalPhase.PRE_ACTION, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('denominator', QuantityKind.DENOMINATOR, 'physical-root', CausalPhase.PRE_ACTION, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('history', QuantityKind.HISTORY, 'native-history', CausalPhase.PRE_ACTION, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('schedule', QuantityKind.ACTION, 'coupling', CausalPhase.ACTION_REQUESTED, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('factor', QuantityKind.RECEIVER, 'event', CausalPhase.RECEIVER, OutcomeAccess.EVALUATION_SEALED, dt * 1152, ResponseDirection.HIGHER_IS_BETTER))),
        key=lambda value: value.quantity_id))
    unit = IndependentUnitSpec(prefix + '.unit', 'One original root; both views are nested', 'matrix-original-independent-group-id')
    relation = RelationalIdentity(prefix + '.relation', (prefix + '.denominator',), (prefix + '.history',), False,
        (prefix + '.schedule',), (prefix + '.factor',), HorizonSpec(prefix + '.horizon', clock,
            dt * design.e1_criterion.survival_duration_ticks, coordinate.primary_view.time_unit))
    envelope = ComputabilityEnvelope(prefix + '.envelope', ('full-native-history',), (), ('whole-root-census',),
        ('whole-root-census',), 4, 16 * 1024**3, 0, 3600, 1024**3, D(3600))
    views = tuple(sorted((NumericalViewSpec(view.view_id, world.world_id, unit.unit_id, 'equations.six-matrix',
        ('closure.six-matrix',), ('boundary.six-matrix',), (NumericalCoordinateSpec(prefix + '.' + label + '.dt',
            NumericalCoordinateKind.TIMESTEP, view.timestep, view.time_unit, index),), 'solver.baoab', '1.0.0',
        view.precision.value, 'cpu', prefix + '.runtime', RandomnessSemantics.GENERATIVE_PREPARATION,
        prefix + '.observation', envelope.envelope_id)
        for index, (label, view) in enumerate((('primary', coordinate.primary_view), ('fine', coordinate.fine_view)))),
        key=lambda value: value.view_id))
    clocks = tuple(ClockSpec(name, 'Declared physical history clock', coordinate.primary_view.time_unit, 'matrix-frame',
        SamplingSemantics.REGULAR, HoldSemantics.NONE, ClockLabelSemantics.INSTANT, dt, D(0))
        for name in sorted({value.clock_id for value in design.e1_coordinates}))
    system = SystemSpec(prefix + '.system', 'Explicit current E1 system', SystemBoundaryKind.OPEN_DRIVEN_DISSIPATIVE,
        world, relation, clocks, quantities, unit, policy, (), computability_envelopes=(envelope,), numerical_views=views)
    required = ObligationStatus.REQUIRED
    obligations = ScientificObligations(prefix + '.obligations',
        SupportSpec(prefix + '.support', relation.relation_id, unit.unit_id, 999, 2, 'cutoff.unadopted',
            ('factor-chart',), ('all-assigned-roots',), (), required),
        ValiditySpec(prefix + '.validity', ('declared-numerical-world',), ('sampling-not-established',), ('NONUSE',), required),
        UncertaintySpec(prefix + '.uncertainty', 'exact-rational-whole-root-binomial', unit.unit_id,
            D('.99'), (prefix + '.factor',), ('SAMPLING_NOT_ESTABLISHED',), required),
        (FalsifierSpec(prefix + '.falsifier', FalsifierKind.BASELINE_COMPARATOR, compact_bindings.KEY,
            'Whole-root recurrence and persistence', 'Retain all assigned roots and both views', required),),
        ClosureSpec(prefix + '.closure', ('complete-32-cell-menu',), ('fixed-factor-rule',), (prefix + '.history',), required),
        StructuralConvergenceSpec(prefix + '.convergence', ('independent-full-native-and-factor-witness',),
            tuple(value.view_id for value in views), (), required),
        ComputabilityEvidence(prefix + '.computability', envelope.envelope_id, tuple(value.view_id for value in views),
            ReadinessStatus.READY, (), ('disclosed-unadopted-capacity-link',)))
    claim = ClaimSpec(prefix + '.claim', world.world_id, relation.relation_id, 'Selected E1 recurrence and BOTH survival?',
        'Complete assigned root probabilities', unit.unit_id, EvidenceRung.RESPONSE, EvidenceCeiling.RESPONSE,
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE, 'No qualification or favorable-result promise',
        ('complete-assigned-denominator',), numerical_view_ids=tuple(value.view_id for value in views))
    control = ControlSpec(prefix + '.control', ControlKind.BASELINE_COMPARATOR, compact_bindings.NAMESPACE + '.check',
        (prefix + '.factor',), 'Independent complete native/factor witnesses in both views')
    return domain.MatrixProgrammeE1ScientificContext(prefix + '.context', claim.proposition, ('selected-four-family-design',),
        system, (claim,), AssignmentSpec(prefix + '.assignment', AssignmentKind.SIMULATOR_INTERVENTION, unit.unit_id,
            relation.action_quantity_ids, 'Acquire every C-assigned history exactly once', ('all-assigned-roots',)),
        (prefix + '.factor',), (control,), (PrecisionGoal(prefix + '.precision', 'exact-cell-probability', D('.25'),
            'probability', 1, 'No outcome-dependent top-up'),), obligations, ObjectIdentity.from_record(control.control_id, control))


@pytest.fixture
def assembled_case(tmp_path, census):  # noqa: F811
    from empirical_lawhood.api.matrix_programme_allocations import publish_matrix_programme_allocations
    from tests.test_matrix_programme_allocations import NAMESPACE, _publisher_case
    from tests.test_matrix_programme_scientific_design import build_scientific_design

    design = build_scientific_design()
    context = scientific_context(design, NAMESPACE)
    system = context.system
    design = replace(design, e1_criterion=replace(design.e1_criterion, system_id=system.system_id,
        world_id=system.world.world_id, relation=ObjectIdentity.from_record(system.relation.relation_id, system.relation),
        independent_unit_id=system.independent_unit.unit_id))
    writer, kwargs = _publisher_case(tmp_path, design, census)
    actual = publish_matrix_programme_allocations(**kwargs)
    node = CampaignNode('node.disclosed.current-e1-claim', CampaignNodeKind.CLAIM, CampaignLane.PROSPECTIVE,
        ObjectIdentity.from_record(context.claims[0].claim_id, context.claims[0]), (), LifecycleStatus.ACTIVE)
    policy = system.authority_policy
    campaign = CampaignSpec('campaign.disclosed.current-e1', context.question, (system.system_id,), (system.world.world_id,),
        (context.claims[0].claim_id,), policy.budget_ceiling, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('right.disclosed.current-e1', AuthorityAction.SIMULATION_EXECUTION,
            policy.delegate_id, policy.policy_id, True),), (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    resources = ExecutionResourceSelection('resources.disclosed.current-e1', (),
        (ChildResourceTokenLimit('child.disclosed.current-e1', 4, 0),), (), (), (), None, None, 4,
        16 * 1024**3, (), (), 'f' * 64, True, True, True, True)
    selected = domain.MatrixProgrammeE1AssemblySelection('selection.disclosed.current-e1-assembly',
        context, campaign, tuple((phase, NonTimeResourceBudget('budget.disclosed.e1.' + phase,
            1, 1024**3, 64 * 1024**2, 100, 256 * 1024**2)) for phase in domain.RESOURCE_PHASES), resources,
        ProgressLivenessContract('progress.disclosed.current-e1', ProgressHeartbeat.SCHEMA, 'disclosed-native-work', D(10), True, True),
        None, None, ())
    specification = domain.MatrixProgrammeE1AssemblySpecification('assembly.disclosed.current-e1', selected.identity, actual.commitment)
    target = Path(writer.root.contract.canonical_path) / 'e1-assembled'
    return dict(specification=specification, selection=selected, project_root=ROOT, artifact_writer=writer,
        metadata_directory=target, output_selection_path=target / 'sources.json', execution=kwargs['execution'],
        maximum_source_bytes=kwargs['metadata_budget'].source_scan_bytes), actual


def test_current_context_and_request_have_no_earlier_root_or_receipt_input(assembled_case):
    kwargs, _ = assembled_case
    selected, specification = kwargs['selection'], kwargs['specification']
    assert {field.name for field in fields(selected.scientific_context)} == {'context_id', 'question', 'alternative_ids',
        'system', 'claims', 'assignment', 'measurement_quantity_ids', 'controls', 'precision_goals', 'obligations', 'observation_operator'}
    assert not hasattr(selected, 'root') and not hasattr(selected, 'qualifications')
    assert not hasattr(selected, 'input_commitments')
    assert specification.input_commitments == assembled_case[1].commitment
    for value in (selected, specification):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
        with pytest.raises(ValueError):
            decode_canonical_record({**value.to_document(), 'version': '1.0.0'}, type(value))
    with pytest.raises(TypeError, match='actual programme commitment'):
        replace(specification, input_commitments=None)
    assert domain.bind_inputs(kwargs['specification'], {'selection': selected}).method_inputs is selected
    with pytest.raises(ValueError, match='only its current explicit'):
        domain.bind_inputs(kwargs['specification'], {'selection': selected, 'historical-root': object()})


def test_real_c_assembly_rebuilds_current_e1_and_replays_without_native_or_old_ready(assembled_case, monkeypatch):
    import numpy as np
    from empirical_lawhood.adapters.simulators.six_matrix_response import simulation
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
    from empirical_lawhood.kernel.serialization import canonical_json_bytes

    kwargs, actual = assembled_case
    monkeypatch.setattr(simulation, 'baoab_step_with_hermitian_noise', lambda *a, **kw: pytest.fail('metadata assembly acquired native history'))
    monkeypatch.setattr(np.random, 'default_rng', lambda *a, **kw: pytest.fail('metadata assembly generated random values'))
    monkeypatch.setattr(np.linalg, 'eigh', lambda *a, **kw: pytest.fail('metadata assembly measured a native outcome'))
    result = owner.assemble_programme_e1(**kwargs)
    selected = load_experiment_inputs(result.target_specification, result.source_selection_path).method_inputs
    root = selected.root
    original = actual.resolved.phase('e1').reservation
    assert selected.manifest.reservation == original
    assert selected.manifest.specification.selection.criterion == actual.resolved.scientific_design.e1_criterion
    assert selected.manifest.provenance == actual.provenance
    assert len(root.evaluation_unit_ids) == len(result.target_specification.root_ids) == 4
    assert all(co.observation_ticks[-1] == 1152 for co in original.allocation.coordinates)
    assert root.experiment.information_cutoffs == compact_bindings.cutoffs(compact_bindings.E1CompactAdjudicationConfig(
        'config.' + compact_bindings.KEY, selected.manifest.identity, actual.resolved.scientific_design.e1_criterion,
        owner.records.sources_for_manifest(selected.manifest)))
    assert {cutoff.phase for cutoff in root.experiment.information_cutoffs} == {CausalPhase.PRE_ACTION}
    # The amended occurrence map includes initial presence at tick zero.
    assert {cutoff.coordinate for cutoff in root.experiment.information_cutoffs} == {D(0)}
    assert root.capability_selections and root.dag_template_key.startswith('recursive.')
    assert root.experiment.reveal_barrier.evaluation_manifest_sha256 == sha256(canonical_json_bytes(root.evaluation_unit_ids)).hexdigest()
    assert root.experiment.authorization_record_id is None and root.experiment.readiness is ReadinessStatus.AUTHORITY_REQUIRED
    assert root.experiment.obligations.computability.readiness is ReadinessStatus.PREREQUISITE_NOT_MET
    assert root.experiment.obligations.computability.evidence_link_ids == ()
    assert root.experiment.obligations.support.physical_unit_count == 4
    assert root.experiment.obligations.support.status is ObligationStatus.REQUIRED
    assert actual.commitment.record in {value.object_identity for value in root.design_inputs}
    draft, _, operands = compact_preparation._derive(result.target_specification, selected)
    assert len(draft.operations) == 18 and len(operands) == len(selected.qualifications) == len(selected.source_configs) == 27
    assert all(value.receipt_id.startswith('qualification.derived-metadata.') for value in selected.qualifications)
    assert {'e1.entry', 'e1.formal-methods', 'e1.formal-sources'} <= {value.code for value in result.preparation.dependencies}
    before = {path.relative_to(kwargs['metadata_directory']).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in kwargs['metadata_directory'].rglob('*') if path.is_file()}
    replay = owner.assemble_programme_e1(**kwargs)
    assert replay.target_specification == result.target_specification
    assert before == {path.relative_to(kwargs['metadata_directory']).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in kwargs['metadata_directory'].rglob('*') if path.is_file()}


def test_public_copied_configuration_derives_the_existing_compact_protocol(assembled_case):
    from empirical_lawhood.api.configuration import validate_configuration
    from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs, load_experiment_inputs
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    kwargs, _ = assembled_case
    copied = Path(kwargs['artifact_writer'].root.contract.canonical_path) / 'copied-e1-assembly'
    copied.mkdir()
    selection, specification = kwargs['selection'], kwargs['specification']
    (copied / 'selection.json').write_bytes(selection.canonical_bytes())
    (copied / 'specification.json').write_bytes(specification.canonical_bytes())
    sources = ExperimentFileInputSelection('inputs.disclosed.current-e1-assembly', domain.PROTOCOL_ID,
        (ExperimentInputBinding('selection', selection.identity, 'selection.json', len(selection.canonical_bytes())),), ())
    (copied / 'sources.json').write_bytes(sources.canonical_bytes())
    assert validate_configuration(copied / 'specification.json', consumer='matrix-programme-e1-assembly')['status'] == 'VALIDATED'
    result = derive_experiment_inputs(specification_path=copied / 'specification.json', source_selection_path=copied / 'sources.json',
        project_root=ROOT, artifact_writer=kwargs['artifact_writer'], metadata_directory=kwargs['metadata_directory'],
        output_selection_path=kwargs['output_selection_path'], execution=kwargs['execution'])
    assert result.source_selection.protocol_id == compact_preparation.PROTOCOL_ID
    inputs = load_experiment_inputs(result.target_specification, result.source_selection_path)
    assert type(inputs.method_inputs) is compact_preparation.E1CompactExperimentSelectionV2
    assert len(inputs.method_inputs.manifest.reservation.allocation.roots) == 4


def test_original_c_mutation_during_new_metadata_publication_refuses_final_return(assembled_case, monkeypatch):
    kwargs, actual = assembled_case
    writer = kwargs['artifact_writer']
    path = writer.root.resolve(actual.commitment.publication.materialization.relative_path, for_write=False)
    original_write, observed = writer.write, []

    def mutate_after_authentication(request):
        result = original_write(request)
        if request.logical_artifact_id.startswith('science.'):
            raw = path.read_bytes()
            path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
            observed.append(request.logical_artifact_id)
        return result

    monkeypatch.setattr(writer, 'write', mutate_after_authentication)
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        owner.assemble_programme_e1(**kwargs)
    assert len(observed) == 1


def test_review_selector_stays_canonical_and_inside_selected_metadata(assembled_case, monkeypatch):
    kwargs, _ = assembled_case
    directory = kwargs['metadata_directory']
    monkeypatch.setattr(kwargs['artifact_writer'], 'write',
        lambda *a, **kw: pytest.fail('invalid review destination published metadata'))
    for output in (directory.parent / 'other-review/sources.json', directory / 'entry-review/selector.json',
            directory / 'entry-review/../sources.json'):
        with pytest.raises(ValueError, match='explicit canonical guarded external directory'):
            owner.assemble_programme_e1(**{**kwargs, 'output_selection_path': output})
    assert not directory.exists()


@pytest.mark.parametrize('damage', ('relation', 'policy-scope', 'census-bytes'))
def test_wrong_context_or_original_c_bytes_refuse_before_derived_publications(assembled_case, monkeypatch, damage):
    kwargs, actual = assembled_case
    selected = kwargs['selection']
    if damage == 'census-bytes':
        path = kwargs['artifact_writer'].root.resolve(actual.resolved.commitments.exposure_census.publication.materialization.relative_path,
            for_write=False)
        raw = path.read_bytes()
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    else:
        context = selected.scientific_context
        if damage == 'relation':
            system = replace(context.system, relation=replace(context.system.relation,
                horizon=replace(context.system.relation.horizon, duration=D('.129'))))
            selected = replace(selected, scientific_context=replace(context, system=system))
        else:
            policy = replace(context.system.authority_policy, scope_ids=('old.foreign-programme',))
            selected = replace(selected, scientific_context=replace(context, system=replace(context.system, authority_policy=policy)),
                campaign=replace(selected.campaign, authority_policy=ObjectIdentity.from_record(policy.policy_id, policy)))
        kwargs['selection'] = selected
        kwargs['specification'] = replace(kwargs['specification'], selection=selected.identity)
    monkeypatch.setattr(kwargs['artifact_writer'], 'write', lambda *a, **kw: pytest.fail('refused C/context published derived metadata'))
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        owner.assemble_programme_e1(**kwargs)
    assert not kwargs['metadata_directory'].exists()
