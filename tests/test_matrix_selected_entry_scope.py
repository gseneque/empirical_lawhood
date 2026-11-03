# SPDX-License-Identifier: MPL-2.0
"""Pure selected-entry joins with exposed assertions, never real qualification."""

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_entry as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
from empirical_lawhood.api.matrix_selected_runtime import _reconstruct_entry_programme
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.metatheory import MetatheoryAggregateDisposition, MetatheoryApplicability
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateKind
from tests.test_matrix_selected_protected import confirmation, transfer, unpublished  # noqa: F401
from tests.test_matrix_source_evidence import source_case  # noqa: F401
from tests.test_matrix_sampling_follow_on import prior_product


def entry_shape(programme, pipeline):
    """Self-consistent record shapes only; every original locator is synthetic."""
    closure, package = programme.sources.closure, programme.point_design.package
    old_spec = pipeline.qualification_config.specification
    method = pipeline.qualification_config.gate_evidence[0].method
    operands = tuple(sorted((closure.identity, programme.sources.identity, programme.assay.identity,
        closure.numerical_scope), key=lambda pin: pin.object_id))
    gates = tuple(replace(gate, applicability=MetatheoryApplicability.REQUIRED, evaluator=method,
        required_operands=operands, applicability_reason_codes=(), falsifier_ids=('exposed-shape-control',))
        if gate.gate_kind is not ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE else replace(gate,
            applicability=MetatheoryApplicability.NOT_APPLICABLE, evaluator=None, required_operands=(), falsifier_ids=(),
            applicability_reason_codes=('EXPOSED_NO_SAMPLING_WARRANT',)) for gate in old_spec.gates)
    groups = tuple(sorted({source.root.root.independent_group_id for _, source in programme.sources.source_arms()}))
    spec = replace(old_spec, source_identity=closure.identity, preparation=programme.sources.identity,
        observation_operator=programme.assay.identity, numerical_view=closure.numerical_scope,
        physical_unit_ids=groups, expected_physical_unit_count=len(groups), gates=gates)
    original = pipeline.qualification_config.gate_evidence[0]
    rows = tuple(replace(original, evidence_id='evidence.exposed.' + gate.gate_id, qualification_spec=owner.reference(spec, 'spec_id'),
        gate_spec=owner.reference(gate, 'gate_id'), input_operands=gate.required_operands,
        observed_physical_unit_ids=groups, eligible_physical_unit_ids=groups) for gate in gates
        if gate.applicability is MetatheoryApplicability.REQUIRED)
    qualification = replace(pipeline.qualification_config, specification=spec, gate_evidence=rows)
    pipeline = replace(pipeline, qualification_config=qualification)
    result = qualification.assess()
    originals = tuple((record, 'record_id') for record in
        (package.models, package.model_freeze, package.calibration, package.calibrated_freeze))
    if programme.nomination is not None:
        originals += ((programme.nomination, 'result_id'),)
    upstream = tuple(sorted((owner.MatrixSelectedOriginalProduct(
        replace(prior_product(owner.reference(record, field)).prior_execution, record_id_field=field),
        prior_product(owner.reference(record, field)).reveal_authority) for record, field in originals),
        key=lambda value: value.record.object_id))
    products = ((pipeline.receipt, 'receipt_id'), (result, 'result_id'), *((gate, 'evidence_id') for gate in rows))
    executions = tuple(sorted((replace(prior_product(owner.reference(record, field)).prior_execution, record_id_field=field)
        for record, field in products), key=lambda value: value.record.object_id))
    return owner.MatrixSelectedEntryEvidence('entry-evidence.exposed-shape', programme.identity,
        unpublished(closure.reservation, 'reservation.exposed-shape'), spec, pipeline, result, upstream, executions, ())


def test_entry_shape_retains_complete_original_scopes_and_canonical_bytes(transfer, source_case):  # noqa: F811
    evidence = entry_shape(transfer, source_case[0])
    owner.validate_selected_entry_evidence(evidence, transfer)
    assert decode_canonical_bytes(evidence.canonical_bytes(), type(evidence), maximum_bytes=None) == evidence
    with pytest.raises(TypeError, match='immutable original'):
        replace(evidence, qualification_executions=list(evidence.qualification_executions))


def test_public_entry_preserves_original_scope_while_calibration_bank_stays_in_parent(transfer, source_case):  # noqa: F811
    evidence = entry_shape(transfer, source_case[0])
    public = MatrixSelectedPublicProgramme.from_programme(transfer)
    owner.validate_selected_entry_evidence(evidence, public)
    assert _reconstruct_entry_programme(public, transfer.point_design.package.calibration) == transfer
    assert b'"scores"' not in public.canonical_bytes()
    assert public.identity != public.original_programme
    assert public.point_design.identity != public.point_design.original_design
    assert public.point_design.package.identity != public.point_design.package.original_package


def test_confirmation_requires_actual_original_nomination_and_projects_only_its_selection(confirmation, source_case):  # noqa: F811
    evidence = entry_shape(confirmation, source_case[0])
    public = MatrixSelectedPublicProgramme.from_programme(confirmation)
    owner.validate_selected_entry_evidence(evidence, confirmation)
    owner.validate_selected_entry_evidence(evidence, public)
    assert len(evidence.upstream_products) == 5
    assert _reconstruct_entry_programme(public, confirmation.point_design.package.calibration,
        confirmation.nomination) == confirmation
    assert public.nomination.original_nomination == owner.reference(confirmation.nomination, 'result_id')
    assert all(name not in public.nomination.canonical_bytes() for name in (b'"cases"', b'"candidate_results"'))
    with pytest.raises((ValueError, TypeError), match='nomination'):
        _reconstruct_entry_programme(public, confirmation.point_design.package.calibration)
    original_pin = public.nomination.original_nomination
    changed = replace(evidence, upstream_products=tuple(value for value in evidence.upstream_products if value.record != original_pin))
    with pytest.raises(ValueError, match='actual upstream freeze'):
        owner.validate_selected_entry_evidence(changed, public)


@pytest.mark.parametrize('pin', ('package', 'design', 'programme'))
def test_parent_reconstruction_rejects_substituted_original_identity(transfer, pin):  # noqa: F811
    public = MatrixSelectedPublicProgramme.from_programme(transfer)
    design = public.point_design
    if pin == 'package':
        package = replace(design.package, original_package=replace(design.package.original_package, object_fingerprint='f'*64))
        public = replace(public, point_design=replace(design, package=package))
    elif pin == 'design':
        public = replace(public, point_design=replace(design, original_design=replace(design.original_design, object_fingerprint='f'*64)))
    else:
        public = replace(public, original_programme=replace(public.original_programme, object_fingerprint='f'*64))
    with pytest.raises(PermissionError, match='exact original scientific'):
        _reconstruct_entry_programme(public, transfer.point_design.package.calibration)


@pytest.mark.parametrize('damage', ('source', 'preparation', 'numerical', 'negative', 'upstream', 'gate'))
def test_entry_refuses_substituted_or_negative_source_premises_before_native_admission(transfer, source_case, damage):  # noqa: F811
    evidence = entry_shape(transfer, source_case[0])
    if damage in ('source', 'preparation', 'numerical'):
        field = {'source': 'source_identity', 'preparation': 'preparation', 'numerical': 'numerical_view'}[damage]
        spec = replace(evidence.source_specification, **{field: replace(getattr(evidence.source_specification, field), object_fingerprint='f'*64)})
        changed = replace(evidence, source_specification=spec)
    elif damage == 'negative':
        changed = replace(evidence, source_result=replace(evidence.source_result, disposition=MetatheoryAggregateDisposition.OPPOSED))
    elif damage == 'upstream':
        changed = replace(evidence, upstream_products=evidence.upstream_products[:-1])
    else:
        changed = replace(evidence, qualification_executions=evidence.qualification_executions[:-1])
    with pytest.raises(ValueError, match='qualification scope|supported complete|actual upstream freeze'):
        owner.validate_selected_entry_evidence(changed, transfer)
