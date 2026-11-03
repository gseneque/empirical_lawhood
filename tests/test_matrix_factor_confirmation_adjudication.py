# SPDX-License-Identifier: MPL-2.0
"""E1 population/authority falsifiers using explicitly hypothetical controls."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import records as r, science
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import (
    BUDGET, KEY, NAMESPACE, E1AdjudicationConfig, E1Adjudicator, confirmation_draft,
    cutoffs, operation_factories, source_operands,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorObservation
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import lifetime
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS, MatrixParameterFactorControl, expected_members
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.status import OperationalStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole, SourceAccessDisposition, SourceMaterializationRef, SourceMaterializationRole
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_factor_confirmation_history import e1 as e1
from tests.test_matrix_factor_response import Reader


def products(sources, *, flags=None, numerical=True):
    """Compact pure reducer fixture; these are not qualified spectral products."""
    products, assessments = [], []
    for source in sources:
        rule = source.rule
        arrays = {name: np.zeros(shape, dtype=dtype) for name, (dtype, shape) in expected_members(rule).items()}
        raw, members = encode_matrix_arrays(arrays)
        artifact = ArtifactIdentity('synthetic.diagnostic.'+source.root_id, 'hypothetical-e1-reduction-control',
            'empirical-lawhood/matrix-array/npz', sha256(raw).hexdigest(), 'application/x-npz', len(raw))
        # Use the actual matrix codec schema, independent of fixture labels.
        from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
        artifact = replace(artifact, payload_schema=MATRIX_ARRAY_SCHEMA)
        history = ObjectIdentity('history.'+source.root_id, r.E1NativeHistory.SCHEMA, '1.0.0', '1'*64)
        native = ArtifactIdentity('native.'+source.root_id, 'hypothetical-software-control', MATRIX_ARRAY_SCHEMA, '2'*64, 'application/x-npz', 1)
        root = r.E1FactorRootRole(source.root_id, source.root.root.independent_group_id, source.coordinate.family_id,
            r.identity(source), native, history)
        traces = []
        for view in r.VIEWS:
            for sector in rule.sectors:
                selected = (True,)*len(rule.lattice) if flags is None else flags.get((source.root_id, view, sector), (True,)*len(rule.lattice))
                origin = next((tick for tick, flag in zip(rule.lattice, selected, strict=True) if tick >= rule.risk_start_tick and flag is True), None)
                obs = tuple(FactorObservation(tick, 'UNAVAILABLE', None, None, None, None, None, None, None, None, None,
                    False, 'UNAVAILABLE') if flag is None else FactorObservation(tick, 'AVAILABLE', True, flag, flag, None,
                    D(0) if flag else D(1), D(0), D(0), None,
                    D(0) if origin is not None and tick >= origin else None, False, None)
                    for tick, flag in zip(rule.lattice, selected, strict=True))
                traces.append(r.E1FactorTrace(root, r.identity(rule), view, sector, obs, lifetime(obs, rule),
                    lifetime(obs, rule, origin_fixed=True), artifact, members))
        numerical_id = ObjectIdentity('numerical.'+source.root_id, r.E1NumericalAssessment.SCHEMA, '1.0.0', '3'*64)
        operand = r.E1Arrays('synthetic.arrays.'+source.root_id, r.identity(source), 'FACTOR_DIAGNOSTICS', artifact, members,
            tuple(sorted((r.identity(source), history, numerical_id), key=lambda x: x.object_id)), Access.EVALUATION_SEALED, Visibility.PROSPECTIVE)
        product = r.E1FactorProduct('synthetic.product.'+source.root_id, r.identity(source), history,
            numerical_id, numerical, tuple(traces), operand)
        n = len(rule.lattice)*len(rule.sectors)*2
        controls = tuple(MatrixParameterFactorControl(method, (D(0),)*(15*n if method == 'all-eigenpairs' else n),
            D('1e-9'), dimension, 'SATISFIED', (True,)*(15*n if method == 'all-eigenpairs' else n))
            for method, dimension in zip(METHODS, (225, 15, 225, 225, 48, 1), strict=True))
        assessment = r.E1FactorAssessment('synthetic.assessment.'+source.root_id, r.identity(source), r.identity(product),
            r.identity(source.specification.selection.factor_numerical_design), controls, True)
        products.append(product)
        assessments.append(assessment)
    return tuple(products), tuple(assessments)


def test_complete_family_presence_and_separate_survival_with_nested_denominators(e1):
    _, sources, _ = e1
    p, a = products(sources)
    result = science.reduce_population(sources, p, a)
    assert result.scientific_status is ScientificStatus.SUPPORTED
    assert len(result.findings) == 4*2*2*3
    assert len(result.risk_rows) == 4*2*2*9
    assert {f.requested_roots for f in result.findings} == {1}
    assert {f.independent_units for f in result.findings} == {1}
    assert {f.endpoint for f in result.findings} == {'RECURRENCE', 'MOVING', 'ORIGIN_FIXED'}
    assert all(f.left_present_roots == 1 and f.observed_new_admissions == 0 for f in result.findings)
    with pytest.raises(ValueError, match='complete selected root'):
        science.reduce_population(sources, p[:-1], a[:-1])


@pytest.mark.parametrize('state', ('no-origin', 'exit', 'missing', 'late-admission', 'numerical-failure'))
def test_adverse_no_origin_unknown_and_right_censoring_retained(e1, state):
    _, sources, _ = e1
    flag = ((False,)*9 if state == 'no-origin' else (True,)*5+(False,)*4 if state == 'exit'
        else (True,)*5+(None,)+(True,)*3 if state == 'missing'
        else (False,)*8+(True,) if state == 'late-admission' else (True,)*9)
    key = sources[0].root_id, 'PRIMARY', 'X'
    p, a = products(sources, flags={key: flag}, numerical=state != 'numerical-failure')
    result = science.reduce_population(sources, p, a)
    findings = tuple(f for f in result.findings if (f.family_id, f.view, f.sector) == (sources[0].coordinate.family_id, 'PRIMARY', 'X'))
    assert result.scientific_status is (ScientificStatus.NOT_SUPPORTED if state == 'exit' else ScientificStatus.UNEVALUABLE)
    if state == 'no-origin':
        assert all(f.never_admitted_roots == 1 for f in findings)
        assert findings[1].risk_roots == 0
    if state == 'missing':
        assert all(f.failures == 0 for f in findings)
        assert all(f.unresolved_roots == 1 for f in findings[1:])
    if state == 'late-admission':
        assert all(f.censored_before_horizon == 1 and f.failures == 0 for f in findings[1:])
        assert all(f.observed_new_admissions == 1 for f in findings)


def test_retained_non_success_root_has_explicit_full_denominator_no_fake_assessment(e1):
    _, sources, _ = e1
    p, a = products(sources)
    source = sources[0]
    task = NAMESPACE+'.'+source.root_id+'.history'
    receipt = CanonicalTaskReceipt('receipt.unavailable.e1', 'run.software.e1', task, 'attempt.'+task,
        source.provenance.observed_git_head, (), (), (), (), OperationalStatus.FAILED, ('matrix-e1-native-failure',))
    unavailable = r.E1UnavailableRoot(r.identity(source), receipt)
    result = science.reduce_population(sources, p[1:], a[1:], unavailable=(unavailable,))
    assert result.scientific_status is ScientificStatus.UNEVALUABLE
    assert result.root_ids == tuple(s.root_id for s in sources)
    assert result.unavailable == (unavailable,)
    rows = tuple(f for f in result.findings if f.family_id == source.coordinate.family_id)
    assert all(f.requested_roots == 1 and f.unknown_admission_roots == 1 for f in rows)
    assert all(f.failures == 0 for f in rows)


def test_actual_contact_without_completion_stays_unknown_and_never_failed_model(e1):
    _, sources, _ = e1
    p, a = products(sources)
    source = sources[0]
    task = NAMESPACE+'.'+source.root_id+'.history'
    contact = NativeEffectContact('run.unknown.e1', task, 'attempt.unknown.e1',
        ObjectIdentity('plan.unknown.e1', 'empirical-lawhood/runtime/execution-plan', '1.0.0', 'a'*64),
        ObjectIdentity(task, 'empirical-lawhood/runtime/execution-task', '1.0.0', 'b'*64),
        source.provenance.observed_git_head, ('input.unknown.e1',), ())
    unknown = r.E1UnavailableRoot(r.identity(source), contact=contact)
    result = science.reduce_population(sources, p[1:], a[1:], unavailable=(unknown,))
    assert result.scientific_status is ScientificStatus.UNEVALUABLE
    assert result.unavailable[0].availability == 'UNKNOWN_CONTACT'
    assert all(f.failures == 0 for f in result.findings if f.family_id == source.coordinate.family_id)
    with pytest.raises(ValueError, match='original'):
        r.E1UnavailableRoot(r.identity(source))


def selected_sources(e1, *, estimand=None, endpoints=None, multiplicity=None):
    plane, sources, definition = e1
    old = sources[0].specification.selection
    criterion = replace(old.criterion, recurrence_estimand=estimand or old.criterion.recurrence_estimand,
        survival_endpoints=endpoints or old.criterion.survival_endpoints, multiplicity=multiplicity or old.criterion.multiplicity)
    selected = replace(old, criterion=criterion)
    frozen = replace(sources[0].specification, selection=selected, publication=publish(plane, selected, 'selection.changed.e1'))
    return tuple(replace(s, specification=frozen) for s in sources), definition


def test_explicit_new_formation_estimand_does_not_relabel_left_present_and_joint_is_selected(e1):
    sources, _ = selected_sources(e1, estimand='OBSERVED_NEW_ADMISSION_AFTER_RISK_START', endpoints=('BOTH',))
    p, a = products(sources)
    result = science.reduce_population(sources, p, a)
    assert result.scientific_status is ScientificStatus.NOT_SUPPORTED
    recurrence = tuple(f for f in result.findings if f.endpoint == 'RECURRENCE')
    assert all(f.successes == 0 and f.left_present_roots == 1 and f.observed_new_admissions == 0 for f in recurrence)
    assert {f.endpoint for f in result.findings} == {'RECURRENCE', 'BOTH'}


def test_marginal_cells_never_make_full_study_confirmation_claim(e1):
    sources, _ = selected_sources(e1, multiplicity='MARGINAL_CELL_NO_FULL_STUDY_CLAIM')
    p, a = products(sources)
    assert science.reduce_population(sources, p, a).scientific_status is ScientificStatus.PARTIAL


def test_new_admission_recurrence_endpoint_does_not_read_later_unknown_onset(e1):
    plane, old_sources, _ = e1
    old = old_sources[0].specification.selection
    criterion = replace(old.criterion, recurrence_estimand='OBSERVED_NEW_ADMISSION_AFTER_RISK_START', recurrence_end_tick=6)
    selection = replace(old, criterion=criterion)
    frozen = replace(old_sources[0].specification, selection=selection, publication=publish(plane, selection, 'selection.endpoint.e1'))
    sources = tuple(replace(s, specification=frozen) for s in old_sources)
    key = (sources[0].root_id, 'PRIMARY', 'X')
    p, a = products(sources, flags={key: (False,)*7+(None, True)})
    result = science.reduce_population(sources, p, a)
    finding = next(f for f in result.findings if (f.family_id, f.view, f.sector, f.endpoint)
        == (sources[0].coordinate.family_id, 'PRIMARY', 'X', 'RECURRENCE'))
    assert finding.evaluable and finding.failures == 1 and finding.successes == 0 and finding.unresolved_roots == 0


@pytest.mark.parametrize('defect', ('half-view', 'eigenpair-denominator', 'tolerance'))
def test_full_population_rejects_thinned_or_changed_independent_witness_protocol(e1, defect):
    _, sources, _ = e1
    p, a = products(sources)
    if defect == 'half-view':
        p = (replace(p[0], traces=p[0].traces[:2]), *p[1:])
    else:
        c = a[0].controls[1]
        c = (replace(c, measured_errors=c.measured_errors[:-1], applicable=c.applicable[:-1])
            if defect == 'eigenpair-denominator' else replace(c, tolerance=D('1e-6')))
        a = (replace(a[0], controls=(a[0].controls[0], c, *a[0].controls[2:])), *a[1:])
    with pytest.raises(ValueError, match='complete factor products'):
        science.reduce_population(sources, p, a)


def context(config, p, a, *, plane, defect=None, selected_owner=None, manifest_record=None, resource_budget=BUDGET):
    """Real typed task/prepared metadata for disclosed, unissued reducer inputs."""
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import operation_bindings
    from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
    from empirical_lawhood.runtime.capabilities import CapabilityRequirement
    from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from tests.worker_configuration_support import freeze_worker_configuration

    selected_owner = operation_bindings if selected_owner is None else selected_owner
    declaration = next(row for row in selected_owner.operation_declarations() if row.capability_key == selected_owner.KEY)
    selected = declaration.manifest()
    ports, receipts, verified, edges, externals = [], [], [], [], []
    records = (config, *((manifest_record,) if manifest_record is not None else ()), *p, *a)
    for n, record in enumerate(records):
        raw = record.canonical_bytes()
        intrinsic = record is config or record is manifest_record
        kind = WorkerInputKind.EXTERNAL if intrinsic or defect == 'external-outcome' else WorkerInputKind.DEPENDENCY
        access = (declaration.outcome_access if record is config else Access.OUTCOME_BLIND if intrinsic
            else Access.DEVELOPMENT_VISIBLE if defect == 'exposed-outcome' else Access.EVALUATION_SEALED)
        visibility = (declaration.visibility_ceiling if record is config else Visibility.DEVELOPMENT_ONLY
            if access is Access.DEVELOPMENT_VISIBLE else Visibility.PROSPECTIVE)
        logical_id = config.config_id if record is config else f'artifact.control.{n:03}'
        write = plane.write(ArtifactWriteRequest(logical_id, f'e1-adjudication-control/{n:03}.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.e1-adjudication-control',
            'e1-adjudication-control', raw, visibility, (), access))
        actual = VerifiedArtifactInput(write.logical, write.materialization)
        verified.append(actual)
        binding = WorkerInputBinding.from_verified(actual, kind=kind)
        port = WorkerInputPort(binding, Reader(raw));ports.append(port)
        if record is config:
            name = 'config'
        elif record is manifest_record:
            name = 'manifest'
        else:
            source = next(source for source in config.sources if selected_owner.identity(source) == record.source)
            role = 'measure' if record in p else 'check'
            name = role + '.' + source.root_id
            task_id = (f'wrong.task.{n:03}' if defect == 'wrong-receipt' else
                selected_owner.NAMESPACE + '.' + source.root_id + '.' + role)
            if kind is WorkerInputKind.DEPENDENCY:
                receipts.append(DependencyReceiptBinding(f'receipt.control.{n:03}', task_id, (port.materialization_id,)))
        receipt = next((row for row in receipts if port.materialization_id in row.output_materialization_ids), None)
        if kind is WorkerInputKind.EXTERNAL:
            externals.append(ExternalInputSpec(name, logical_id, write.logical.content_sha256, record.SCHEMA,
                'application/json', len(raw), visibility, access, None))
        if record is not config:
            edges.append(ScientificInputSpec('edge.control.'+name, name,
                ScientificInputRole.SOURCE if intrinsic else ScientificInputRole.OUTCOME,
                None if receipt is None else receipt.task_id, None if receipt is None else 'product',
                'external.control.'+name if receipt is None else None, logical_id, logical_id, record.SCHEMA,
                'application/json', len(raw), access, visibility, BarrierKind.NONE))
    ports = tuple(sorted(ports, key=lambda row: row.artifact_id))
    receipts = tuple(sorted(receipts, key=lambda row: row.receipt_id))
    criterion = config.sources[0].criterion if manifest_record is None else config.criterion
    plan_pin = ObjectIdentity('plan.control.e1', 'empirical-lawhood/runtime/execution-plan', '1.0.0', 'a'*64)
    authority = ScientificAdjudicationContext(plan_pin,
        criterion.world_id, WorldKind.NUMERICAL_SIMULATOR, criterion.relation, criterion.independent_unit_id,
        tuple(ObjectIdentity.from_record(c.cutoff_id, c) for c in selected_owner.cutoffs(config)),
        Visibility.OUTCOME_VISIBLE, Access.EVALUATION_REVEALED)
    if defect == 'wrong-world':
        authority = replace(authority, evidence_world_id='wrong.world')
    if defect == 'fixture-authority':
        authority = replace(authority, fixture_scope_id='fixture.scope', plumbing_only=True, evidence_world_kind=WorldKind.ANALYTIC_REFERENCE)
    result_schema = r.E1PopulationResult.SCHEMA if manifest_record is None else selected_owner.E1CompactPopulationResult.SCHEMA
    outputs = (WorkerOutputPort(selected_owner.KEY+'.adjudication', ScientificAdjudicationRecord.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'output.adjudication.e1'),
        WorkerOutputPort(selected_owner.KEY+'.product', result_schema, ArtifactProfile.CANONICAL_JSON,
        'application/json', 'output.result.e1'))
    reference = CapabilityConfigRef(config.config_id, config.SCHEMA, selected.config_schema_sha256,
        config.fingerprint(), config.config_id)
    access = Access.EVALUATION_SEALED if defect == 'sealed-task' else Access.EVALUATOR_REVEAL
    ctx = TaskContext('run.control.e1', selected_owner.KEY, 'attempt.control.e1', reference,
        tuple(port.binding for port in ports), ports, outputs, selected.permissions, access, resource_budget,
        WorkerIsolationProfile.TRUSTED_LOCAL, receipts, None if defect == 'missing-authority' else authority)
    requirement = CapabilityRequirement(selected.capability_key, selected.capability_version, selected.kind,
        reference, selected.input_schema_ids, selected.output_schema_ids, selected.permissions,
        selected.maximum_evidence_ceiling, access, resource_budget)
    task = ExecutionTask(ctx.task_id, declaration.stage, requirement, selected.implementation_sha256,
        tuple(sorted(row.task_id for row in receipts)), tuple(sorted(externals,key=lambda row:row.input_id)),
        tuple(ArtifactOutputSpec(output.output_id, output.logical_artifact_id,
            'e1-adjudication-output/'+output.output_id+'.json', output.payload_schema, output.profile,
            output.media_type, Visibility.OUTCOME_VISIBLE, (), Access.EVALUATION_REVEALED) for output in outputs),
        (), BarrierKind.REVEAL, 1, ('obligation.disclosed.e1-adjudication',),
        scientific_inputs=tuple(sorted(edges,key=lambda row:row.edge_id)))
    task = freeze_worker_configuration(task)
    provenance = config.sources[0].provenance if manifest_record is None else manifest_record.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    runner = selected_owner.E1Adjudicator() if manifest_record is None else selected_owner.E1CompactAdjudicator()
    prepared = prepare_worker_invocation(runner, ctx, tuple(verified), implementation=implementation,
        execution_plan=plan_pin, execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task)
    assert not prepared.native_effect and prepared.native_work is None
    return replace(ctx, prepared_invocation=prepared)


@pytest.mark.parametrize('compact', (False, True))
@pytest.mark.parametrize('defect', (None, 'missing-authority', 'sealed-task', 'wrong-world', 'fixture-authority', 'external-outcome', 'exposed-outcome', 'wrong-receipt'))
def test_actual_evaluator_requires_reveal_context_and_original_dependency_receipts(e1, defect, compact):
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_bindings
    from tests.test_matrix_factor_confirmation_compact_core import compact_case, compact_products
    _, sources, _ = e1
    if compact:
        manifest, sources = compact_case(e1)
        p, a = compact_products(e1[1], sources)
        config = compact_bindings.E1CompactAdjudicationConfig('config.'+compact_bindings.KEY,
            compact_bindings.identity(manifest), manifest.specification.selection.criterion, sources)
        selected_owner, runner = compact_bindings, compact_bindings.E1CompactAdjudicator()
    else:
        manifest = None
        p, a = products(sources)
        config = E1AdjudicationConfig('config.'+KEY, sources)
        selected_owner, runner = None, E1Adjudicator()
    if defect is None:
        ctx = context(config, p, a, plane=e1[0], selected_owner=selected_owner, manifest_record=manifest)
        result = runner.execute(ctx)
        assert len(result.outputs) == 2
    else:
        with pytest.raises(ValueError):
            ctx = context(config, p, a, plane=e1[0], selected_owner=selected_owner,
                manifest_record=manifest, defect=defect)
            runner.execute(ctx)


@pytest.mark.parametrize('compact', (False, True))
@pytest.mark.parametrize('damage', ('missing', 'substituted'))
def test_adjudicator_authenticates_actual_config_edge_before_any_operand_body(e1, monkeypatch, compact, damage):
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_bindings
    from empirical_lawhood.runtime.plans import ScientificInputRole
    from tests.test_matrix_factor_confirmation_compact_core import compact_case, compact_products
    if compact:
        manifest, sources = compact_case(e1);p, a = compact_products(e1[1], sources)
        config = compact_bindings.E1CompactAdjudicationConfig('config.'+compact_bindings.KEY,
            compact_bindings.identity(manifest), manifest.specification.selection.criterion, sources)
        ctx = context(config,p,a,plane=e1[0],selected_owner=compact_bindings,manifest_record=manifest)
        runner = compact_bindings.E1CompactAdjudicator()
    else:
        sources=e1[1];p,a=products(sources);config=E1AdjudicationConfig('config.'+KEY,sources)
        ctx=context(config,p,a,plane=e1[0]);runner=E1Adjudicator()
    task=ctx.prepared_invocation.execution_task_record
    original,=(edge for edge in task.scientific_inputs if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    edges=tuple(edge for edge in task.scientific_inputs if edge is not original)
    if damage=='substituted':
        edges += (replace(original,edge_id=original.edge_id+'.foreign'),)
    task=replace(task,scientific_inputs=tuple(sorted(edges,key=lambda row:row.edge_id)))
    prepared=replace(ctx.prepared_invocation,execution_task_record=task,
        execution_task=ObjectIdentity.from_record(task.task_id,task))
    ctx=replace(ctx,prepared_invocation=prepared)
    monkeypatch.setattr(Reader,'read',lambda *_args,**_kwargs:pytest.fail('invalid CONFIG opened an operand body'))
    with pytest.raises(ValueError,match='CONFIGURATION'):
        runner.execute(ctx)


def prospective(e1):
    plane, sources, definition = e1
    root, original = _fixture()
    original_cutoffs = {c.cutoff_id for c in root.experiment.information_cutoffs}
    world = replace(root.system.world, kind=WorldKind.NUMERICAL_SIMULATOR, unrepresented_physics=('physical-transfer',))
    system = replace(root.system, world=world, authority_policy=replace(root.system.authority_policy, budget_ceiling=BUDGET))
    selection = sources[0].specification.selection
    criterion = replace(selection.criterion, system_id=system.system_id, world_id=world.world_id,
        relation=ObjectIdentity.from_record(root.experiment.relation.relation_id, root.experiment.relation),
        independent_unit_id=root.experiment.independent_unit_id)
    selection = replace(selection, criterion=criterion)
    frozen = replace(sources[0].specification, selection=selection, publication=publish(plane, selection, 'selection.prospective.e1'))
    sources = tuple(replace(s, specification=frozen) for s in sources)
    config = E1AdjudicationConfig('config.'+KEY, sources)
    clocks = tuple(replace(system.clocks[0], clock_id=s.coordinate.clock_id, time_unit=s.coordinate.primary_view.time_unit,
        nominal_period=s.coordinate.primary_view.timestep) for s in sources)
    system = replace(system, clocks=tuple(sorted((*system.clocks, *clocks), key=lambda c: c.clock_id)))
    selected_cutoffs = cutoffs(config)
    experiment = replace(root.experiment, information_cutoffs=selected_cutoffs,
        obligations=replace(root.experiment.obligations, support=replace(root.experiment.obligations.support, information_cutoff_id=selected_cutoffs[0].cutoff_id)))
    operands = tuple(sorted({o for s in sources for o in source_operands(s)}, key=lambda o: o.object_id))
    design = tuple(DesignInputRecord(f'input.e1.{n:03}', o, o.object_fingerprint, root.experiment.information_cutoffs[0],
        DesignInputRole.READINESS_METADATA, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, 'human.owner') for n, o in enumerate(operands))
    campaign = replace(root.campaign, nodes=tuple(replace(n, object_identity=ObjectIdentity.from_record(experiment.experiment_id, experiment))
        if n.object_identity.object_id == experiment.experiment_id else n for n in root.campaign.nodes))
    root = replace(root, system=system, experiment=experiment, campaign=campaign, design_inputs=design,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(i.input_id for i in design)),
        evaluation_unit_ids=tuple(sorted(s.root.root.independent_group_id for s in sources)), resource_ceiling=BUDGET)
    nodes = tuple(NAMESPACE+'.'+s.root_id+'.'+role for s in sources for role in ('history', 'numerical', 'measure', 'check'))+(KEY, NAMESPACE+'.commit')
    owners = [(f'obligation.e1.{n:03}', node) for n, node in enumerate(nodes)]
    owners.extend((b.obligation_id, KEY) for b in original.templates[0].coverage.bindings if b.obligation_id not in original_cutoffs)
    owners.extend((c.cutoff_id, NAMESPACE+'.'+c.cutoff_id.removeprefix('cutoff.')+'.history') for c in selected_cutoffs)
    draft = confirmation_draft(root=root, sources=sources, scalar_definition=definition, proof_owners=tuple(sorted(set(owners))), draft_id='draft.software.e1')
    materials, qualifications = [], []
    for n, external in enumerate(draft.external_inputs):
        material = ObjectIdentity(external.logical_artifact_id, external.payload_schema, '1.0.0', external.expected_content_sha256)
        q = replace(original.qualifications[0], receipt_id=f'qualification.e1.{n:03}', source_id=external.input_id,
            materialization=material, content_sha256=external.expected_content_sha256, clock_ids=tuple(c.clock_id for c in system.clocks))
        qualifications.append(q)
        materials.append(SourceMaterializationRef(external.input_id, SourceMaterializationRole.OBSERVATION_STREAM,
            world.world_id, material, external.expected_content_sha256, external.expected_content_sha256, q.observation_operator,
            q.numerical_view_ids, ObjectIdentity.from_record(q.receipt_id, q), SourceAccessDisposition.VERIFIED_ACCESS))
    root = replace(root, source_materializations=tuple(sorted(materials, key=lambda s: s.source_id)))
    return replace(draft, prospective_draft=root), tuple(qualifications)


def test_stock_prospective_compiler_requires_complete_source_qualification_and_phase_census(e1):
    draft, qualifications = prospective(e1)
    factories = operation_factories()
    registry = CapabilityRegistry('registry.software.e1', tuple(sorted((f.manifest for f in factories), key=lambda m: m.registry_id)))
    kwargs = dict(registrations=tuple(f.registration for f in factories), registry=registry, implementation_commit='a'*40,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs={k: v for f in factories for k, v in f.output_codecs.items()})
    compiled = compile_recursive_wave(draft=draft, qualifications=qualifications, **kwargs)
    assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
    assert len(compiled.template.protocol.steps) == 18
    unqualified = compile_recursive_wave(draft=draft, qualifications=(), **kwargs)
    assert unqualified.candidate_report.candidate is None
    missing = draft.operations[0].node_id
    thinned = replace(draft, operations=tuple(o for o in draft.operations if o.node_id != missing),
        links=tuple(l for l in draft.links if l.consumer_node_id != missing and l.producer_node_id != missing),
        selected_operation_ids=tuple(n for n in draft.selected_operation_ids if n != missing))
    with pytest.raises(ValueError, match='four-phase|thins'):
        compile_recursive_wave(draft=thinned, qualifications=qualifications, **kwargs)
