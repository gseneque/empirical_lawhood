# SPDX-License-Identifier: MPL-2.0
"""Exposed binding/custody conformance; every native receiver is a software fixture."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import subprocess
import sys
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_thermal_inquiry import native, science
from empirical_lawhood.adapters.methods.battery_thermal_inquiry import operation_bindings as owner, recursive_translation as drafts
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySource, BatteryInquirySupply
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, AssessmentPhase, ContributionRole
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.recursive_compiler import project_recursive_assessments
from tests.test_battery_thermal_inquiry import _exposed_trace
from tests.test_inquiry_successor_compilation import compile_complete_draft


@pytest.fixture
def episode(monkeypatch):
    calls = []
    def exposed(config):
        calls.append(config)
        return _exposed_trace(config, cpu=D(1) if config.model_view == 'chen-spme' else D(2))
    monkeypatch.setattr(native, 'acquire', exposed)
    supplier = science.supply(BatteryInquirySource())
    later = owner.BatteryInquiryAssessedInstance('product.battery-thermal-inquiry.use', supplier,
        science.assess(supplier, science.compatible_instance(supplier)))
    instance = science.compatible_instance(supplier, 'reuse', prior_use=later.assessment)
    reused = owner.BatteryInquiryAssessedInstance('product.battery-thermal-inquiry.reuse', supplier,
        science.assess(supplier, instance, prior_use=later.assessment), later.assessment)
    return supplier, later, reused, calls


def _products(draft, record):
    """Authenticated metadata seam fixture; no actual scientific/issue authority."""
    node = draft.operations[0].node_id
    phase = node.rsplit('.', 1)[-1]
    census = owner.native_census(record, phase)
    records = {node+'.product': record, node+'.native-census': census}
    logicals, outputs = [], {}
    for key, value in sorted(records.items()):
        logical = N(logical_artifact_id='artifact.exposed.'+key, payload_schema=value.SCHEMA,
            content_sha256=value.fingerprint(), media_type='application/json', outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        logicals.append(logical)
        outputs[logical.logical_artifact_id] = N(logical=logical, materialization=N(size_bytes=len(value.canonical_bytes())))
    receipt = N(receipt_id='receipt.exposed.'+node, SCHEMA='empirical-lawhood/testing/battery-inquiry-receipt', VERSION='1.0.0',
                fingerprint=lambda: 'a'*64, operational_status=OperationalStatus.SUCCEEDED, output_logical_artifacts=tuple(logicals))
    return {'records': {node: records}, 'receipts': {node: receipt}, 'outputs': outputs}


def _payloads(draft, records):
    by_hash = {record.fingerprint(): record.canonical_bytes() for record in records}
    return {'external-'+sha256(row.input_id.encode()).hexdigest()[:24]+'.json': by_hash[row.expected_content_sha256]
            for row in draft.external_inputs}


def test_cold_discovery_never_imports_native_library_or_executes_provider():
    subprocess.run([sys.executable, '-c', "import sys; from empirical_lawhood.adapters.methods.battery_thermal_inquiry import native; native.acquire=lambda *a,**k: (_ for _ in ()).throw(AssertionError('native contact')); from empirical_lawhood.adapters.methods.battery_thermal_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES; assert len(EXECUTABLE_BINDING_FACTORIES)==3; assert 'pybamm' not in sys.modules"], check=True)


def test_all_three_singleton_scientific_graphs_and_native_slots_compile(episode):
    supplier, later, reused, calls = episode
    first = drafts.supply_draft(supplier.source)
    first_products = _products(first, supplier)
    first_parent = drafts.describe_contributions(first, first_products)[0]
    second = drafts.next_wave_builder(first, first_parent, first_products)
    second_products = _products(second, later)
    second_parent = drafts.describe_contributions(second, second_products)[0]
    third = drafts.next_wave_builder(second, second_parent, second_products)
    for draft in (first, second, third):
        compile_complete_draft(draft, owner)
        config = decode_canonical_bytes(draft.operations[0].config_payload.encode(), owner.BatteryInquiryOperationConfig, maximum_bytes=None)
        slots = owner.native_effect_slot_ids(config)
        assert len(slots) == (36 if config.operation == 'supply' else 12) and len(set(slots)) == len(slots)
        assert len(owner.operation_registrations()[0].outputs) == 2
    assert first_parent.products[0].role is ContributionRole.DESIGN_OPERAND
    assert second_parent.products[0].role is ContributionRole.INSTANCE_PRODUCT
    assert next(row for row in third.external_inputs if row.input_id.endswith('.supplier')).scientific_role == 'OUTCOME'
    assert drafts.next_wave_builder(third, drafts.describe_contributions(third, _products(third, reused))[0], _products(third, reused)) is None
    assert len(calls) == 60  # exposed mocked backend only, not actual native contacts


def test_wrapper_preserves_original_supplier_and_actual_prior_use_without_native(episode, monkeypatch):
    supplier, later, reused, _ = episode
    def forbidden(*args, **kwargs):
        raise AssertionError('constructors/readers cannot execute native science')
    monkeypatch.setattr(native, 'acquire', forbidden)
    monkeypatch.setattr(science, 'assess', forbidden)
    assert decode_canonical_bytes(reused.canonical_bytes(), owner.BatteryInquiryAssessedInstance, maximum_bytes=None) == reused
    assert reused.supplier == later.supplier == supplier
    assert reused.prior_use == later.assessment
    assert reused.assessment.instance.prior_use == science.identity(later.assessment)
    with pytest.raises(ValueError, match='prior use'):
        replace(reused, prior_use=None)
    with pytest.raises(ValueError, match='prior instance'):
        replace(later, prior_use=later.assessment)
    with pytest.raises(ValueError, match='prior use'):
        drafts.reuse_draft(reused)


def test_actual_current_census_excludes_ancestor_attempts_and_refuses_tampering(episode):
    supplier, later, reused, _ = episode
    censuses = (owner.native_census(supplier, 'supply'), owner.native_census(later, 'use'), owner.native_census(reused, 'reuse'))
    assert [row.native_provider_attempts for row in censuses] == [36, 12, 12]
    assert [row.backend_solve_calls for row in censuses] == [36, 12, 12]
    assert [row.initializer_solver_attempts for row in censuses] == [36, 12, 12]
    assert tuple(row.initializer_attempts for row in censuses[1].traces) == tuple(
        row.initializer_attempts for row in sorted(later.assessment.traces, key=lambda row: row.trace_id))
    assert tuple(row.charging_attempts for row in censuses[1].traces) == tuple(
        row.charging_attempts for row in sorted(later.assessment.traces, key=lambda row: row.trace_id))
    assert tuple(row.transitions for row in censuses[1].traces) == tuple(
        row.transitions for row in sorted(later.assessment.traces, key=lambda row: row.trace_id))
    assert len({row.trace for census in censuses for row in census.traces}) == 60
    assert all(row.source == science.identity(supplier.source) for row in censuses)
    with pytest.raises(ValueError, match='denominator'):
        replace(censuses[0], traces=censuses[0].traces[:-1])
    with pytest.raises(ValueError, match='totals'):
        replace(censuses[1], backend_solve_calls=36)
    with pytest.raises(ValueError, match='totals'):
        replace(censuses[1], initializer_solver_attempts=0)
    with pytest.raises(ValueError, match='charging scope'):
        replace(censuses[1].traces[0], backend_solve_scope='ALL_NATIVE_SOLVES')
    with pytest.raises(ValueError, match='trace/config types'):
        replace(censuses[1].traces[0], trace=replace(censuses[1].traces[0].trace, object_version='1.0.0'))
    assert decode_canonical_bytes(censuses[2].canonical_bytes(), owner.BatteryInquiryNativeCensus, maximum_bytes=None) == censuses[2]


def test_census_retains_failed_subsolve_and_counts_multiple_calls_per_forecast(episode):
    supplier, _, _, _ = episode
    census = owner.native_census(supplier, 'supply')
    row = census.traces[0]
    first = row.charging_attempts[0]
    failed = replace(first, attempt_index=2, requested_start_clock_s=first.native_times_s[-1],
        requested_differential_state=first.end_differential_state, disposition='TECHNICAL_FAILURE',
        termination='ExposedSolverError', error_type='ExposedSolverError', error_message='Exposed software-only failure',
        native_times_s=(), start_differential_state=(), end_differential_state=(), start_receivers=(), end_receivers=(),
        requested_state_sha256='', realized_start_state_sha256='', realized_end_state_sha256='')
    multiple = replace(row, backend_solve_calls=2, charging_attempts=(first, failed))
    changed = replace(census, traces=(multiple, *census.traces[1:]), backend_solve_calls=census.backend_solve_calls+1)
    assert changed.native_provider_attempts == 36 and changed.backend_solve_calls == 37
    assert changed.traces[0].charging_attempts[-1].disposition == 'TECHNICAL_FAILURE'
    with pytest.raises(ValueError, match='native attempts'):
        replace(multiple, charging_attempts=(first,))
    assert decode_canonical_bytes(changed.canonical_bytes(), owner.BatteryInquiryNativeCensus, maximum_bytes=None) == changed


def test_repaired_binding_versions_refuse_relabelled_exact_guard_source_without_native(monkeypatch):
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    source = BatteryInquirySource()
    original = source.to_document()
    original['version'] = '1.0.0'
    with pytest.raises(ValueError):
        decode_canonical_bytes(canonical_json_bytes(original), BatteryInquirySource, maximum_bytes=None)
    assert owner.BatteryInquiryAssessedInstance.VERSION == owner.BatteryInquiryOperationConfig.VERSION == '1.1.0'
    assert owner.BatteryInquiryNativeCensus.VERSION == owner.BatteryInquiryNativeTraceBinding.VERSION == '1.1.0'
    assert {row.capability_version for row in owner.operation_manifests()} == {'1.1.0'}
    def forbidden(*args, **kwargs):
        raise AssertionError('counterfeit source refusal cannot execute native science')
    monkeypatch.setattr(native, 'acquire', forbidden)
    counterfeit = source.to_document()
    counterfeit['value']['protocol_sha256'] = '0'*64
    with pytest.raises(ValueError):
        decode_canonical_bytes(canonical_json_bytes(counterfeit), BatteryInquirySource, maximum_bytes=None)


def test_four_phase_projection_uses_actual_product_and_current_census(episode):
    supplier, later, reused, _ = episode
    first = drafts.supply_draft(supplier.source)
    parent = drafts.describe_contributions(first, _products(first, supplier))[0]
    use = drafts.use_draft(supplier, parent=parent)
    use_parent = drafts.describe_contributions(use, _products(use, later))[0]
    reuse = drafts.reuse_draft(later, parent=use_parent)
    for draft, record in ((use, later), (reuse, reused)):
        actual = _products(draft, record)
        outputs = {(task, output.removeprefix(task+'.')): value for task, records in actual['records'].items() for output, value in records.items()}
        projected = project_recursive_assessments(draft=draft, registrations=owner.operation_registrations(), outputs=outputs)
        assert {row.phase for row in projected} == set(AssessmentPhase)
        assert all(row.disposition is AssessmentDisposition.SATISFIED for row in projected)
        assert all(row.evidence == (science.identity(record),) for row in projected)
        with pytest.raises(ValueError, match='scientific condition'):
            owner.project_battery_assessments(record, replace(draft.requirements[0], condition='Physical safety'), draft.connections[0])


def test_scientific_false_admission_does_not_erase_successful_joined_delivery(monkeypatch):
    def exposed(config):
        magnitude = D('.8') if config.phase == 'use' and config.model_view == 'chen-spme' and config.recipe == 'original-ambient' else None
        return _exposed_trace(config, magnitude=magnitude, cpu=D(1) if config.model_view == 'chen-spme' else D(2))
    monkeypatch.setattr(native, 'acquire', exposed)
    supplier = science.supply(BatteryInquirySource())
    record = owner.BatteryInquiryAssessedInstance('product.battery-thermal-inquiry.use', supplier, science.assess(supplier, science.compatible_instance(supplier)))
    first = drafts.supply_draft(supplier.source)
    parent = drafts.describe_contributions(first, _products(first, supplier))[0]
    use = drafts.use_draft(supplier, parent=parent)
    projected = owner.project_battery_assessments(record, use.requirements[0], use.connections[0])
    phases = {row.phase: row.disposition for row in projected}
    assert phases[AssessmentPhase.ADMISSION] is AssessmentDisposition.FALSIFIED
    assert phases[AssessmentPhase.JOINED] is AssessmentDisposition.SATISFIED
    spec = N(endpoint=supplier.scope, distinguishing_assessment=use.operations[0].config_identity)
    assert drafts.inquiry_outcome_projector(use, spec, _products(use, record)) == 'scoped-failure'


def test_source_only_inquiry_has_no_native_or_supplier_evaluation(monkeypatch):
    source = BatteryInquirySource()
    initial = drafts.supply_draft(source)
    def forbidden(*args, **kwargs):
        raise AssertionError('source-only inquiry cannot contact selected science')
    monkeypatch.setattr(science, 'supply', forbidden)
    monkeypatch.setattr(native, 'acquire', forbidden)
    bindings = drafts.inquiry_evidence_projector(initial, _payloads(initial, (source,)), {'records': {}})
    assert len(bindings) == 1 and bindings[0].independent_unit_ids == ()
    spec = N(endpoint=scope_for_source(source), distinguishing_assessment=initial.operations[0].config_identity)
    assert drafts.inquiry_outcome_projector(initial, spec, {'records': {}}) == 'unresolved'


def scope_for_source(source):
    return science.source_scope(science.identity(source))


def test_projection_retains_original_parent_scope_all_native_outputs_and_exact_prior(episode):
    supplier, later, reused, _ = episode
    use = drafts.use_draft(supplier)
    use_products = _products(use, later)
    use_parent = drafts.describe_contributions(use, use_products)[0]
    reuse = drafts.reuse_draft(later, parent=use_parent)
    actual = _products(reuse, reused)
    bindings = drafts.inquiry_evidence_projector(reuse, _payloads(reuse, (later, reused.assessment.instance)), actual)
    assert len(bindings) == 4 and all(row.independent_unit_ids == () for row in bindings)
    parent_binding = next(row for row in bindings if row.binding_id.endswith('.supplier'))
    assert parent_binding.role is ContributionRole.INSTANCE_PRODUCT and parent_binding.scope == later.scope
    assert any(row.binding_id.endswith('.native-census') for row in bindings)
    spec = N(endpoint=supplier.scope, distinguishing_assessment=reuse.operations[0].config_identity)
    assert drafts.inquiry_outcome_projector(reuse, spec, actual) == 'useful-supply'
    actual['receipts'][reuse.operations[0].node_id].output_logical_artifacts[0].content_sha256 = 'f'*64
    with pytest.raises(ValueError, match='producing receipt'):
        drafts.describe_contributions(reuse, actual)


def test_native_runner_checks_all_contracts_before_any_contact(episode, monkeypatch):
    supplier, _, _, _ = episode
    source = supplier.source
    initial = drafts.supply_draft(source)
    config = decode_canonical_bytes(initial.operations[0].config_payload.encode(), owner.BatteryInquiryOperationConfig, maximum_bytes=None)
    node = initial.operations[0].node_id
    contact = []
    monkeypatch.setattr(science, 'supply', lambda raw: contact.append(raw) or supplier)
    def context():
        inputs = tuple(N(payload_schema=row.SCHEMA, size_bytes=len(row.canonical_bytes()), media_type='application/json',
            kind=WorkerInputKind.EXTERNAL, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, read=row.canonical_bytes,
            close=lambda: None) for row in (config, source))
        return N(task_id=node, permissions=owner.BatteryInquiryRunner('supply').manifest.permissions,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, resource_budget=owner.BUDGET, input_ports=inputs,
            config=N(config_id=config.config_id, content_sha256=config.fingerprint()),
            output_ports=(N(output_id=node+'.native-census', payload_schema=owner.BatteryInquiryNativeCensus.SCHEMA,
                            profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json'),
                          N(output_id=node+'.product', payload_schema=BatteryInquirySupply.SCHEMA,
                            profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json')))
    wrong = context(); wrong.output_ports = wrong.output_ports[:-1]
    with pytest.raises(ValueError, match='outputs'):
        owner.BatteryInquiryRunner('supply').execute(wrong)
    assert not contact
    result = owner.BatteryInquiryRunner('supply').execute(context())
    assert len(contact) == 1 and len(result.outputs) == 2
    assert decode_canonical_bytes(result.outputs[1].payload, BatteryInquirySupply, maximum_bytes=None) == supplier


def test_reuse_contribution_refuses_substituted_prior_product_even_without_evidence_projection(episode):
    _, later, reused, _ = episode
    original = drafts.reuse_draft(later)
    operation = original.operations[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), owner.BatteryInquiryOperationConfig, maximum_bytes=None)
    config = replace(config, operands=tuple(replace(row, object_fingerprint='f'*64)
        if row.object_schema == owner.BatteryInquiryAssessedInstance.SCHEMA else row for row in config.operands))
    changed = replace(original, operations=(replace(operation, config_payload=config.canonical_bytes().decode()),),
        development_study=owner.development_root(config, study_id=original.development_study.study_id))
    with pytest.raises(ValueError, match='configured actual prior use product'):
        drafts.describe_contributions(changed, _products(changed, reused))


def test_missing_reference_refusal_preserves_zero_new_native_census(monkeypatch):
    monkeypatch.setattr(native, 'acquire', lambda config: _exposed_trace(config, technical=config.model_view == 'oregan-dfn-refined'))
    supplier = science.supply(BatteryInquirySource())
    assert supplier.disposition is AssessmentDisposition.UNEVALUABLE
    instance = science.compatible_instance(supplier)
    record = owner.BatteryInquiryAssessedInstance('product.battery-thermal-inquiry.use', supplier, science.assess(supplier, instance))
    census = owner.native_census(record, 'use')
    assert census.native_provider_attempts == census.backend_solve_calls == 0
    assert record.assessment.disposition is AssessmentDisposition.REFUSED
    use = drafts.use_draft(supplier)
    products = _products(use, record)
    parent = drafts.describe_contributions(use, products)[0]
    assert drafts.next_wave_builder(use, parent, products) is None


def test_contribution_origins_keep_instance_product_outcome_role(episode):
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    supplier, later, _, _ = episode
    use = drafts.use_draft(supplier)
    parent = drafts.describe_contributions(use, _products(use, later))[0]
    reuse = drafts.reuse_draft(later, parent=parent)
    product = parent.products[0]
    origins = RecursiveInputOrigins(tuple(sorted((RecursiveInputOrigin(row.input_id, RecursiveInputOriginKind.CONTRIBUTION,
        row.expected_content_sha256, product.role.value, ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id, product.producing_receipt)
        if row.input_id.endswith('.supplier') else RecursiveInputOrigin(row.input_id, RecursiveInputOriginKind.SOURCE,
            row.expected_content_sha256, row.scientific_role) for row in reuse.external_inputs), key=lambda row: row.input_id)))
    origins.validate_draft(reuse)
    with pytest.raises(ValueError, match='digest or role'):
        origins.validate_draft(replace(reuse, external_inputs=tuple(replace(row, scientific_role='MODEL')
            if row.input_id.endswith('.supplier') else row for row in reuse.external_inputs)))
