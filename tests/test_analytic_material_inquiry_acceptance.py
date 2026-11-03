# SPDX-License-Identifier: MPL-2.0
"""Independent scalar SI/slab checks and exact source/clock controls."""
from dataclasses import replace
from decimal import Decimal
from math import acosh, cosh
from pathlib import Path

import pytest
from scipy.constants import mu_0

from empirical_lawhood.adapters.methods.analytic_material_inquiry import science
from empirical_lawhood.adapters.methods.analytic_material_inquiry.operation_bindings import operation_registrations
from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import supply_draft, use_draft
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as Verdict

D = Decimal


@pytest.fixture(scope='module')
def source():
    return decode_canonical_bytes(Path('programmes/materials/superconductivity/workflows/electron-gas-response/config.json').read_bytes(), UniformElectronGasAnalyticReferenceConfig, maximum_bytes=4*1024**2)


@pytest.fixture(scope='module')
def supplier(source):
    return science.supply(source)


def test_compatible_response_independent_si_and_slab_oracle(supplier):
    instance = science.compatible_instance(supplier)
    result = science.assess(supplier, instance)
    assert result.disposition is Verdict.SATISFIED
    assert len(instance.panel.rows) == 20
    kernel0 = 1 / (mu_0 * 1e-7**2)
    for row in instance.panel.rows:
        expected = -kernel0 * (1 + 4 * float(row.q_over_kf)**2) * float(row.realized_A_T[1])
        assert abs(float(row.current_density[1]) - expected) <= max(abs(expected) * 1e-12, 1e-100)
    centre = float(instance.panel.slab_profile[50][1])
    assert abs(centre - 1 / cosh(5)) / centre < 1e-12
    inferred = 1e-6 / (2 * acosh(1 / centre))
    assert abs(inferred - 1e-7) / 1e-7 < 1e-12
    assert decode_canonical_bytes(result.canonical_bytes(), science.MaterialAssessment, maximum_bytes=4*1024**2) == result


def test_exact_three_selected_changes(source):
    later = science.later_config(source)
    from dataclasses import fields
    assert {f.name for f in fields(source) if getattr(source, f.name) != getattr(later, f.name)} == {
        'config_id', 'independent_unit_id', 'slab_thickness_m'}
    assert later.deterministic_kernel_relative_error == D('0.0001')
    assert later.thresholds == source.thresholds


def test_clock_drift_retained_adverse(supplier):
    instance = science.compatible_instance(supplier)
    rows = (replace(instance.panel.rows[0], receiver_clock=4), *instance.panel.rows[1:])
    changed = replace(instance, panel=replace(instance.panel, rows=rows))
    result = science.assess(supplier, changed)
    assert result.disposition is Verdict.FALSIFIED
    assert 'ACTION_RECEIVER_CLOCK_DRIFT' in result.reason_codes


def test_source_and_later_config_substitution_refuse(source, supplier):
    with pytest.raises(ValueError, match='substitution'):
        science.supply(replace(source, receiver_clock=4))
    instance = science.compatible_instance(supplier)
    with pytest.raises(ValueError, match='config diff'):
        science.assess(supplier, replace(instance, config=replace(instance.config, field_ceiling_T=D('0.002'))))
    with pytest.raises(ValueError, match='another frozen'):
        science.assess(supplier, replace(instance, panel=replace(instance.panel, config_sha256='1'*64)))


def test_separate_drafts_have_zero_native_effects(source, supplier):
    assert len(supply_draft(source).operations) == len(use_draft(supplier).operations) == 1
    assert all(not r.native_effect for r in operation_registrations())


def test_registered_assessment_projection_retains_clock_failure(supplier):
    from types import SimpleNamespace as N
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import inquiry_outcome_projector
    from empirical_lawhood.kernel.status import OperationalStatus
    instance = science.compatible_instance(supplier)
    instance = replace(instance, panel=replace(instance.panel, rows=(replace(instance.panel.rows[0], receiver_clock=4), *instance.panel.rows[1:])))
    draft = use_draft(supplier, instance)
    record = science.assess(supplier, instance)
    node = draft.operations[0].node_id
    specification = N(distinguishing_assessment=draft.operations[0].config_identity, endpoint=supplier.scope)
    logical = N(payload_schema=record.SCHEMA, content_sha256=record.fingerprint())
    products = {'records': {node: {'product': record}}, 'receipts': {node: N(
        operational_status=OperationalStatus.SUCCEEDED, output_logical_artifacts=(logical,))}}
    assert inquiry_outcome_projector(draft, specification, products) == 'scoped-failure'
    with pytest.raises(ValueError, match='endpoint'):
        inquiry_outcome_projector(draft, N(distinguishing_assessment=specification.distinguishing_assessment,
            endpoint=replace(supplier.scope, receiver_id='wrong.receiver')), products)


def test_initial_and_later_material_stock_keep_original_config_scope(source, supplier, monkeypatch):
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import inquiry_evidence_projector
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    instance = science.compatible_instance(supplier)
    draft = use_draft(supplier, instance)
    records = {record.fingerprint(): record for record in (supplier, instance)}
    payloads = {'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json':
                records[external.expected_content_sha256].canonical_bytes() for external in draft.external_inputs}
    from empirical_lawhood.api import recursive_inquiry_evidence as api
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
    monkeypatch.setattr(api, 'operation_factories', lambda: EXECUTABLE_BINDING_FACTORIES)
    bindings = api.project_wave_evidence_bindings(draft=draft, payloads=payloads)
    retained = bindings['external.analytic-material-inquiry.use.supplier']
    original = bindings['external.analytic-material-inquiry.use.instance']
    assert retained.scope == supplier.scope and retained.role is ContributionRole.DESIGN_OPERAND
    assert original.scope.source_config_sha256 == instance.config.fingerprint() != source.fingerprint()
    assert original.role is ContributionRole.RETAINED_ANALYSIS_INPUT
    assert all(not row.independent_unit_ids for row in bindings.values())
    result = science.assess(supplier, instance)
    product_rows = inquiry_evidence_projector(draft, payloads, {'records': {'analytic-material-inquiry.use': {'analytic-material-inquiry.use.product': result}}})
    assert next(row for row in product_rows if row.binding_id == 'analytic-material-inquiry.use.product').scope == result.scope
    altered = replace(result, scope=replace(result.scope, receiver_id='wrong.endpoint'))
    with pytest.raises(ValueError, match='scope/output'):
        inquiry_evidence_projector(draft, payloads, {'records': {'analytic-material-inquiry.use': {'analytic-material-inquiry.use.product': altered}}})


def test_material_use_outcome_refuses_instance_alias_for_supplier(supplier):
    from types import SimpleNamespace as N
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import inquiry_outcome_projector
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.operation_bindings import record_identity
    from empirical_lawhood.kernel.status import OperationalStatus
    instance = science.compatible_instance(supplier)
    draft = use_draft(supplier, instance)
    record = replace(science.assess(supplier, instance), supplier=record_identity(instance))
    node = draft.operations[0].node_id
    spec = N(distinguishing_assessment=draft.operations[0].config_identity, endpoint=supplier.scope)
    products = {'records': {node: {'product': record}}, 'receipts': {node: N(operational_status=OperationalStatus.SUCCEEDED,
        output_logical_artifacts=(N(payload_schema=record.SCHEMA, content_sha256=record.fingerprint()),))}}
    with pytest.raises(ValueError, match='exact supplier'):
        inquiry_outcome_projector(draft, spec, products)


def test_material_source_only_endpoint_validation_before_missing_product(source):
    from types import SimpleNamespace as N
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import inquiry_outcome_projector
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    draft = supply_draft(source)
    original = N(distinguishing_assessment=draft.operations[0].config_identity, endpoint=science.scope(source))
    assert science.source_scope(ObjectIdentity.from_record(source.config_id, source)) == original.endpoint
    assert inquiry_outcome_projector(draft, original, {'records': {}}) == 'unresolved'
    wrong = N(distinguishing_assessment=original.distinguishing_assessment,
              endpoint=replace(original.endpoint, receiver_id='wrong.material-endpoint'))
    with pytest.raises(ValueError, match='original design endpoint'):
        inquiry_outcome_projector(draft, wrong, {'records': {}})
    with pytest.raises(ValueError, match='frozen source identity'):
        science.source_scope(replace(ObjectIdentity.from_record(source.config_id, source), object_id='wrong.source'))


def test_material_static_history_endpoint_preserves_supply_use_scope(source, supplier):
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import inquiry_endpoint_validator
    first, later = supply_draft(source), use_draft(supplier)
    assert first.operations[0].config_identity != later.operations[0].config_identity
    assert inquiry_endpoint_validator(first, supplier.scope) is None
    assert inquiry_endpoint_validator(later, supplier.scope) is None
    for draft in (first, later):
        with pytest.raises(ValueError, match='original design endpoint'):
            inquiry_endpoint_validator(draft, replace(supplier.scope, receiver_id='wrong.history-receiver'))
    changed = replace(later, operations=(replace(later.operations[0], selection=first.operations[0].selection),))
    with pytest.raises(ValueError, match='selected configuration'):
        inquiry_endpoint_validator(changed, supplier.scope)
