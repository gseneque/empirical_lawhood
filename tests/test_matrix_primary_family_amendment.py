# SPDX-License-Identifier: MPL-2.0
"""Alpha-only configuration proof; actual source bytes and contacts stay exact."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import pytest
from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_primary_amendment import MatrixE3PrimaryFamilyAmendment
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_configured_protected_assembly import _case


def test_original_native_candidate_is_preserved_and_only_declared_primary_allowance_amended(tmp_path):
    _,predecessor,request,_,_,_=_case(tmp_path)
    candidate=request.candidate_specification
    before=request.canonical_bytes()
    reservation_bytes=request.future_manifest.reservation.canonical_bytes()
    reservation_identity=scheduled_identity(request.future_manifest.reservation)
    assert reservation_identity==predecessor.target_specification.future_reservation
    family=tuple(sorted(set(AMENDED_PRIMARY_FAMILY) | set(candidate.assessment.comparison_ids)))
    assessment=replace(candidate.assessment,alpha_denominator=20*len(family),comparison_ids=family)
    amendment=MatrixE3PrimaryFamilyAmendment('amendment.disclosed-primary',candidate,assessment,
        request.identity,predecessor.target_specification.identity)
    amendment.validate_native(predecessor.target_specification,request)
    assert amendment.candidate==replace(candidate,assessment=assessment)
    assert amendment.candidate.identity!=candidate.identity
    assert amendment.candidate.calibration_alpha==candidate.calibration_alpha
    assert amendment.candidate.measurement==candidate.measurement
    assert amendment.candidate.methods==candidate.methods
    assert amendment.assessment.alpha*len(family)==Fraction(1,20)
    assert decode_canonical_bytes(amendment.canonical_bytes(),type(amendment),maximum_bytes=None)==amendment
    assert request.canonical_bytes()==before
    with pytest.raises(ValueError,match='non-alpha assessment'):
        replace(amendment,assessment=replace(assessment,improvement_margin=assessment.improvement_margin+Decimal('.0001')))
    with pytest.raises(ValueError,match='exact family budget'):
        replace(amendment,assessment=replace(assessment,alpha_denominator=20*len(family)+1))
    for changed in (replace(candidate,calibration_alpha=Decimal('.1')),
            replace(candidate,methods=tuple(replace(row,ridge_lambda=row.ridge_lambda+1) if row.ridge_lambda is not None else row for row in candidate.methods)),
            replace(candidate,protocol=replace(candidate.protocol,measurement=replace(candidate.measurement,target_discrepancy_tolerance=Decimal('.001'))))):
        bad=replace(amendment,original_candidate=changed)
        with pytest.raises(ValueError,match='exact original native candidate'):
            bad.validate_native(predecessor.target_specification,request)
    with pytest.raises(ValueError,match='exact original native candidate'):
        replace(amendment,original_native_request=replace(amendment.original_native_request,object_fingerprint='f'*64)).validate_native(predecessor.target_specification,request)
    assert request.future_manifest.reservation.canonical_bytes()==reservation_bytes
    assert scheduled_identity(request.future_manifest.reservation)==reservation_identity
    assert reservation_identity==predecessor.target_specification.future_reservation
